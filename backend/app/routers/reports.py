"""LLM report endpoints."""
import logging
from typing import Annotated, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.llm_report import LLMReport
from app.models.stock import Stock
from app.models.score_result import ScoreResult
from app.schemas.report import LLMReportResponse, ReportsListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/latest", response_model=List[LLMReportResponse])
def get_latest_reports(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get latest batch of LLM reports.

    Returns all reports from the most recent report_date.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of latest LLM reports
    """
    try:
        # Find most recent report_date
        latest_date_result = (
            db.query(LLMReport.report_date)
            .order_by(desc(LLMReport.report_date))
            .first()
        )

        if not latest_date_result:
            return []

        latest_date = latest_date_result[0]

        # Get all reports from that date with stock names
        rows = (
            db.query(LLMReport, Stock.stock_name)
            .outerjoin(Stock, LLMReport.stock_id == Stock.stock_id)
            .filter(LLMReport.report_date == latest_date)
            .order_by(LLMReport.stock_id)
            .all()
        )

        results = []
        for report, stock_name in rows:
            report.stock_name = stock_name or report.stock_id
            results.append(report)

        return results

    except Exception as e:
        logger.error(f"Failed to get latest reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")


@router.post("/{stock_id}/generate", response_model=LLMReportResponse)
def generate_stock_report(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Trigger LLM analysis for a single stock on-demand.

    Args:
        stock_id: Stock ticker (e.g., "2330")
        db: Database session
        current_user: Authenticated user

    Returns:
        Generated LLM report
    """
    from app.config import settings
    from app.services.llm_client import LLMClient
    from app.services.llm_analyzer import LLMAnalyzer

    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {stock_id} not found")

        # Get latest score for this stock (if any)
        score = (
            db.query(ScoreResult)
            .filter(ScoreResult.stock_id == stock_id)
            .order_by(desc(ScoreResult.score_date))
            .first()
        )
        score_data = {}
        if score:
            score_data = {
                'chip': float(score.chip_score),
                'fundamental': float(score.fundamental_score),
                'technical': float(score.technical_score),
                'total': float(score.total_score),
            }

        # Initialize LLM client and analyzer
        llm_client = LLMClient(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
        )
        analyzer = LLMAnalyzer(llm_client=llm_client)

        # Analyze single stock
        result = analyzer.analyze_stock(db, stock_id, score_data)
        if not result:
            raise HTTPException(status_code=500, detail="LLM analysis failed")

        # Fetch the saved report to return
        row = (
            db.query(LLMReport, Stock.stock_name)
            .outerjoin(Stock, LLMReport.stock_id == Stock.stock_id)
            .filter(LLMReport.id == result['id'])
            .first()
        )
        if not row:
            raise HTTPException(status_code=500, detail="Report not found after generation")

        report, stock_name = row
        report.stock_name = stock_name or stock_id
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report for {stock_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/{stock_id}", response_model=LLMReportResponse)
def get_stock_report(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get latest report for specific stock.

    Args:
        stock_id: Stock ticker (e.g., "2330")
        db: Database session
        current_user: Authenticated user

    Returns:
        Latest LLM report for the stock

    Raises:
        HTTPException: If report not found
    """
    try:
        row = (
            db.query(LLMReport, Stock.stock_name)
            .outerjoin(Stock, LLMReport.stock_id == Stock.stock_id)
            .filter(LLMReport.stock_id == stock_id)
            .order_by(desc(LLMReport.report_date))
            .first()
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No report found for stock {stock_id}"
            )

        report, stock_name = row
        report.stock_name = stock_name or stock_id
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report for {stock_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report")


@router.get("/history/{stock_id}", response_model=ReportsListResponse)
def get_report_history(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """
    Get historical reports for a stock (paginated).

    Args:
        stock_id: Stock ticker (e.g., "2330")
        page: Page number (default: 1)
        limit: Items per page (default: 10, max: 100)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of historical reports
    """
    try:
        # Calculate offset
        skip = (page - 1) * limit

        # Get total count
        total = (
            db.query(LLMReport)
            .filter(LLMReport.stock_id == stock_id)
            .count()
        )

        # Get paginated reports with stock name
        rows = (
            db.query(LLMReport, Stock.stock_name)
            .outerjoin(Stock, LLMReport.stock_id == Stock.stock_id)
            .filter(LLMReport.stock_id == stock_id)
            .order_by(desc(LLMReport.report_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

        reports = []
        for report, stock_name in rows:
            report.stock_name = stock_name or stock_id
            reports.append(report)

        return ReportsListResponse(
            items=reports,
            total=total,
            page=page,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Failed to get report history for {stock_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report history")
