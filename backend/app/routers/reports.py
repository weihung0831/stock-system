"""LLM report endpoints."""
import logging
from typing import Annotated, List, Optional
from datetime import date, datetime, timedelta

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
from app.services.report_rate_limiter import report_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/quota")
def get_report_quota(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's report quota from DB (survives restart)."""
    from sqlalchemy import func
    from app.models.report_usage import ReportUsage
    from app.services.report_rate_limiter import REPORT_TIER_LIMITS

    tier = current_user.membership_tier if not current_user.is_admin else 'premium'
    limits = REPORT_TIER_LIMITS.get(tier, REPORT_TIER_LIMITS['free'])

    daily_used = db.query(func.count(ReportUsage.id)).filter(
        ReportUsage.user_id == current_user.id,
        ReportUsage.usage_date == date.today(),
    ).scalar() or 0

    return {
        "tier": tier,
        "daily_limit": limits['per_day'],
        "daily_used": daily_used,
        "daily_remaining": max(0, limits['per_day'] - daily_used),
    }


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
        from sqlalchemy import func as sa_func

        # Subquery: latest report per stock
        latest_sub = (
            db.query(
                LLMReport.stock_id,
                sa_func.max(LLMReport.id).label('max_id')
            )
            .group_by(LLMReport.stock_id)
            .subquery()
        )

        # Free users can only see reports they generated themselves
        tier = current_user.membership_tier if not current_user.is_admin else 'premium'

        base_query = (
            db.query(LLMReport, Stock.stock_name)
            .join(latest_sub, LLMReport.id == latest_sub.c.max_id)
            .outerjoin(Stock, LLMReport.stock_id == Stock.stock_id)
        )

        if tier == 'free':
            from app.models.report_usage import ReportUsage
            base_query = base_query.join(
                ReportUsage,
                (ReportUsage.stock_id == LLMReport.stock_id) & (ReportUsage.user_id == current_user.id)
            )

        rows = base_query.order_by(desc(LLMReport.report_date)).all()

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
    Returns cached report if one already exists for today (24h cooldown).
    """
    from app.config import settings
    from app.services.llm_client import LLMClient
    from app.services.llm_analyzer import LLMAnalyzer

    # Report rate limit check (DB-based, survives restart)
    from sqlalchemy import func
    from app.models.report_usage import ReportUsage
    from app.services.report_rate_limiter import REPORT_TIER_LIMITS

    tier = current_user.membership_tier if not current_user.is_admin else 'premium'
    limits = REPORT_TIER_LIMITS.get(tier, REPORT_TIER_LIMITS['free'])
    daily_used = db.query(func.count(ReportUsage.id)).filter(
        ReportUsage.user_id == current_user.id,
        ReportUsage.usage_date == date.today(),
    ).scalar() or 0
    if daily_used >= limits['per_day']:
        raise HTTPException(status_code=429, detail=f"已達每日 AI 報告上限 {limits['per_day']} 檔")

    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {stock_id} not found")

        # Cache check: return existing report if generated within 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        cached = (
            db.query(LLMReport, Stock.stock_name)
            .outerjoin(Stock, LLMReport.stock_id == Stock.stock_id)
            .filter(LLMReport.stock_id == stock_id, LLMReport.created_at >= cutoff)
            .order_by(desc(LLMReport.created_at))
            .first()
        )
        if cached:
            report, stock_name = cached
            report.stock_name = stock_name or stock_id
            # Record usage so Free user can see it after refresh
            existing = db.query(ReportUsage).filter(
                ReportUsage.user_id == current_user.id,
                ReportUsage.stock_id == stock_id,
                ReportUsage.usage_date == date.today(),
            ).first()
            if not existing:
                db.add(ReportUsage(user_id=current_user.id, stock_id=stock_id, usage_date=date.today()))
                db.commit()
            logger.info(f"Returning cached report for {stock_id} (created_at={report.created_at})")
            return report

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

        # Record usage in DB (skip if already recorded today for this stock)
        existing = db.query(ReportUsage).filter(
            ReportUsage.user_id == current_user.id,
            ReportUsage.stock_id == stock_id,
            ReportUsage.usage_date == date.today(),
        ).first()
        if not existing:
            db.add(ReportUsage(user_id=current_user.id, stock_id=stock_id, usage_date=date.today()))
            db.commit()

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report for {stock_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/{stock_id}", response_model=Optional[LLMReportResponse])
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
            return None

        # Free users can only see reports they generated themselves
        tier = current_user.membership_tier if not current_user.is_admin else 'premium'
        if tier == 'free':
            from app.models.report_usage import ReportUsage
            has_usage = db.query(ReportUsage).filter(
                ReportUsage.user_id == current_user.id,
                ReportUsage.stock_id == stock_id,
            ).first()
            if not has_usage:
                return None

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
        # Free users can only see reports they generated themselves
        tier = current_user.membership_tier if not current_user.is_admin else 'premium'
        if tier == 'free':
            from app.models.report_usage import ReportUsage
            has_usage = db.query(ReportUsage).filter(
                ReportUsage.user_id == current_user.id,
                ReportUsage.stock_id == stock_id,
            ).first()
            if not has_usage:
                return ReportsListResponse(items=[], total=0, page=page, limit=limit)

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
