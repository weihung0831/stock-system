"""Screening router for multi-factor stock screening."""
import logging
from typing import Annotated
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.score_result import ScoreResult
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.schemas.screening import (
    ScreeningRequest,
    ScoreResultResponse,
    ScoreDetailResponse,
    ScreeningResultsResponse,
    ScreeningSettingsResponse,
    ScreeningSettingsUpdate,
)
from app.services.scoring_engine import ScoringEngine
from app.models.system_setting import SystemSetting
from app.models.institutional import Institutional
from app.models.revenue import Revenue
from app.models.financial import Financial

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screening", tags=["screening"])


@router.post("/run", response_model=ScreeningResultsResponse)
def run_screening(
    request: ScreeningRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Trigger multi-factor screening with custom weights.

    Args:
        request: Screening request with weights and threshold
        db: Database session
        current_user: Authenticated user

    Returns:
        Screening results with scores and rankings
    """
    try:
        logger.info(f"User {current_user.username} triggered screening")

        engine = ScoringEngine()
        results = engine.run_screening(
            db=db,
            weights=request.weights,
            threshold=request.threshold
        )

        # Convert to response format
        items = []
        for idx, result in enumerate(results):
            stock = db.query(Stock).filter(Stock.stock_id == result['stock_id']).first()
            stock_name = stock.stock_name if stock else None
            industry = stock.industry if stock else None

            close_price = 0.0
            change_pct = 0.0
            recent_prices = (
                db.query(DailyPrice)
                .filter(DailyPrice.stock_id == result['stock_id'])
                .order_by(DailyPrice.trade_date.desc())
                .limit(2)
                .all()
            )
            if recent_prices:
                close_price = float(recent_prices[0].close or 0)
                if len(recent_prices) >= 2 and recent_prices[1].close:
                    prev = float(recent_prices[1].close)
                    if prev > 0:
                        change_pct = round((close_price - prev) / prev * 100, 2)

            items.append(
                ScoreResultResponse(
                    stock_id=result['stock_id'],
                    stock_name=stock_name,
                    score_date=str(date.today()),
                    chip_score=result['chip_score'],
                    fundamental_score=result['fundamental_score'],
                    technical_score=result['technical_score'],
                    total_score=result['total_score'],
                    rank=idx + 1,
                    industry=industry,
                    close_price=close_price,
                    change_percent=change_pct,
                )
            )

        return ScreeningResultsResponse(
            items=items,
            total=len(items),
            threshold=request.threshold,
            weights=request.weights
        )

    except Exception as e:
        logger.error(f"Error running screening: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="篩選執行失敗，請稍後再試"
        )


@router.get("/results", response_model=ScreeningResultsResponse)
def get_results(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    score_date: str = None
):
    """
    Get latest screening results ranking.

    Args:
        score_date: Optional date filter (YYYY-MM-DD), defaults to today
        db: Database session
        current_user: Authenticated user

    Returns:
        Screening results sorted by rank
    """
    try:
        # Parse date
        if score_date:
            try:
                query_date = date.fromisoformat(score_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            # Default to latest available score date
            query_date = db.query(
                sqlfunc.max(ScoreResult.score_date)
            ).scalar()
            if not query_date:
                return ScreeningResultsResponse(
                    items=[], total=0, threshold=2.5,
                    weights={"chip": 40, "fundamental": 35, "technical": 25}
                )

        # Query score results
        results = (
            db.query(ScoreResult)
            .filter(ScoreResult.score_date == query_date)
            .order_by(ScoreResult.rank.asc())
            .all()
        )

        if not results:
            return ScreeningResultsResponse(
                items=[],
                total=0,
                threshold=2.5,
                weights={"chip": 40, "fundamental": 35, "technical": 25}
            )

        # Get weights from first result
        first_result = results[0]
        weights = {
            "chip": float(first_result.chip_weight),
            "fundamental": float(first_result.fundamental_weight),
            "technical": float(first_result.technical_weight)
        }

        # Convert to response format
        items = []
        for result in results:
            stock = db.query(Stock).filter(Stock.stock_id == result.stock_id).first()
            stock_name = stock.stock_name if stock else None
            industry = stock.industry if stock else None

            # Get latest 2 prices for close_price and change_percent
            close_price = 0.0
            change_pct = 0.0
            recent_prices = (
                db.query(DailyPrice)
                .filter(DailyPrice.stock_id == result.stock_id)
                .order_by(DailyPrice.trade_date.desc())
                .limit(2)
                .all()
            )
            if recent_prices:
                close_price = float(recent_prices[0].close or 0)
                if len(recent_prices) >= 2 and recent_prices[1].close:
                    prev = float(recent_prices[1].close)
                    if prev > 0:
                        change_pct = round((close_price - prev) / prev * 100, 2)

            items.append(
                ScoreResultResponse(
                    stock_id=result.stock_id,
                    stock_name=stock_name,
                    score_date=str(result.score_date),
                    chip_score=float(result.chip_score),
                    fundamental_score=float(result.fundamental_score),
                    technical_score=float(result.technical_score),
                    total_score=float(result.total_score),
                    rank=result.rank,
                    industry=industry,
                    close_price=close_price,
                    change_percent=change_pct,
                )
            )

        return ScreeningResultsResponse(
            items=items,
            total=len(items),
            threshold=2.5,
            weights=weights
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screening results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得篩選結果失敗，請稍後再試"
        )


@router.get("/results/{stock_id}", response_model=ScoreDetailResponse)
def get_stock_score(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get single stock score details with breakdown.

    Args:
        stock_id: Stock ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Detailed score breakdown for the stock
    """
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock {stock_id} not found"
            )

        # Calculate fresh score
        engine = ScoringEngine()
        result = engine.score_single_stock(db, stock_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate score"
            )

        result["stock_name"] = stock.stock_name
        result["industry"] = stock.industry
        return ScoreDetailResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock score for {stock_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得股票評分失敗，請稍後再試"
        )


def _get_or_create_settings(db: Session) -> SystemSetting:
    """Get system settings row, create with defaults if missing."""
    row = db.query(SystemSetting).first()
    if not row:
        row = SystemSetting(
            id=1, chip_weight=40,
            fundamental_weight=35, technical_weight=25,
            screening_threshold=2.5,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/settings", response_model=ScreeningSettingsResponse)
def get_screening_settings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current screening weights and threshold."""
    row = _get_or_create_settings(db)
    return ScreeningSettingsResponse(
        weights={"chip": row.chip_weight, "fundamental": row.fundamental_weight, "technical": row.technical_weight},
        threshold=row.screening_threshold,
    )


@router.get("/settings/auto-weights", response_model=ScreeningSettingsResponse)
def auto_optimize_weights(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Auto-calculate optimal weights based on data coverage.

    Analyzes how many candidate stocks have usable data for each factor,
    then allocates weight proportionally — factors with better data coverage
    get higher weight.
    """
    from datetime import timedelta

    # Get candidate stocks (top 30 by volume)
    from app.services.hard_filter import HardFilter
    candidates = HardFilter().filter_by_volume(db, threshold=2.5)
    if not candidates:
        return ScreeningSettingsResponse(
            weights={"chip": 40, "fundamental": 35, "technical": 25},
            threshold=2.5,
        )

    total = len(candidates)
    today = date.today()

    # Chip coverage: stocks with institutional data in last 30 days
    chip_count = db.query(sqlfunc.count(sqlfunc.distinct(Institutional.stock_id))).filter(
        Institutional.stock_id.in_(candidates),
        Institutional.trade_date >= today - timedelta(days=30),
    ).scalar() or 0

    # Fundamental coverage: stocks with revenue data
    fund_count = db.query(sqlfunc.count(sqlfunc.distinct(Revenue.stock_id))).filter(
        Revenue.stock_id.in_(candidates),
    ).scalar() or 0

    # Technical coverage: stocks with >= 120 days of price data
    cutoff = today - timedelta(days=180)
    tech_subq = (
        db.query(DailyPrice.stock_id)
        .filter(DailyPrice.stock_id.in_(candidates), DailyPrice.trade_date >= cutoff)
        .group_by(DailyPrice.stock_id)
        .having(sqlfunc.count(DailyPrice.id) >= 120)
    )
    tech_count = tech_subq.count()

    # Calculate coverage ratios (min 0.1 to avoid zero weight)
    chip_ratio = max(chip_count / total, 0.1)
    fund_ratio = max(fund_count / total, 0.1)
    tech_ratio = max(tech_count / total, 0.1)

    # Normalize to 100, round to nearest 5
    raw_total = chip_ratio + fund_ratio + tech_ratio
    chip_w = round((chip_ratio / raw_total) * 100 / 5) * 5
    fund_w = round((fund_ratio / raw_total) * 100 / 5) * 5
    tech_w = 100 - chip_w - fund_w  # ensure sum = 100

    logger.info(
        f"Auto weights - coverage: chip={chip_count}/{total}, "
        f"fund={fund_count}/{total}, tech={tech_count}/{total} "
        f"→ weights: {chip_w}/{fund_w}/{tech_w}"
    )

    return ScreeningSettingsResponse(
        weights={"chip": chip_w, "fundamental": fund_w, "technical": tech_w},
        threshold=2.5,
    )


@router.put("/settings", response_model=ScreeningSettingsResponse)
def update_screening_settings(
    body: ScreeningSettingsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Update screening weights and threshold, persisted for pipeline use."""
    row = _get_or_create_settings(db)
    if body.weights:
        row.chip_weight = body.weights["chip"]
        row.fundamental_weight = body.weights["fundamental"]
        row.technical_weight = body.weights["technical"]
    if body.threshold is not None:
        row.screening_threshold = body.threshold
    db.commit()
    db.refresh(row)
    return ScreeningSettingsResponse(
        weights={"chip": row.chip_weight, "fundamental": row.fundamental_weight, "technical": row.technical_weight},
        threshold=row.screening_threshold,
    )
