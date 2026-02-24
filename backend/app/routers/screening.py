"""Screening router for multi-factor stock screening."""
import logging
from typing import Annotated, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func as sqlfunc, desc as sqldesc
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


def _build_score_responses(
    db: Session,
    score_data: List[dict],
) -> List[ScoreResultResponse]:
    """Batch-build ScoreResultResponse items (3 SQL queries instead of N*2).

    Args:
        db: Database session
        score_data: List of dicts with keys: stock_id, score_date,
            chip_score, fundamental_score, technical_score, total_score, rank
    """
    if not score_data:
        return []

    stock_ids = [d['stock_id'] for d in score_data]

    # Batch query: all Stock info in 1 query
    stocks_map = {
        s.stock_id: s
        for s in db.query(Stock).filter(Stock.stock_id.in_(stock_ids)).all()
    }

    # Batch query: latest 2 prices per stock using window function
    # Subquery: rank prices by trade_date desc per stock
    price_subq = (
        db.query(
            DailyPrice.stock_id,
            DailyPrice.close,
            DailyPrice.trade_date,
            sqlfunc.row_number().over(
                partition_by=DailyPrice.stock_id,
                order_by=sqldesc(DailyPrice.trade_date),
            ).label('rn'),
        )
        .filter(DailyPrice.stock_id.in_(stock_ids))
        .subquery()
    )
    recent_prices = (
        db.query(price_subq.c.stock_id, price_subq.c.close, price_subq.c.rn)
        .filter(price_subq.c.rn <= 2)
        .all()
    )

    # Organize: {stock_id: {1: close, 2: close}}
    prices_map: dict = {}
    for sid, close, rn in recent_prices:
        prices_map.setdefault(sid, {})[rn] = float(close) if close else 0.0

    # Build response items
    items = []
    for d in score_data:
        sid = d['stock_id']
        stock = stocks_map.get(sid)
        price_info = prices_map.get(sid, {})

        close_price = price_info.get(1, 0.0)
        prev_price = price_info.get(2, 0.0)
        change_pct = 0.0
        if prev_price > 0:
            change_pct = round((close_price - prev_price) / prev_price * 100, 2)

        items.append(ScoreResultResponse(
            stock_id=sid,
            stock_name=stock.stock_name if stock else None,
            score_date=d['score_date'],
            chip_score=d['chip_score'],
            fundamental_score=d['fundamental_score'],
            technical_score=d['technical_score'],
            total_score=d['total_score'],
            rank=d['rank'],
            industry=stock.industry if stock else None,
            close_price=close_price,
            change_percent=change_pct,
        ))

    return items


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

        # Convert to batch-friendly format
        score_data = [
            {
                'stock_id': r['stock_id'],
                'score_date': str(date.today()),
                'chip_score': r['chip_score'],
                'fundamental_score': r['fundamental_score'],
                'technical_score': r['technical_score'],
                'total_score': r['total_score'],
                'rank': idx + 1,
            }
            for idx, r in enumerate(results)
        ]
        items = _build_score_responses(db, score_data)

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

        # Query score results (top 30 for dashboard)
        results = (
            db.query(ScoreResult)
            .filter(ScoreResult.score_date == query_date)
            .order_by(ScoreResult.rank.asc())
            .limit(30)
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

        # Batch-build response items (3 SQL instead of N*2)
        score_data = [
            {
                'stock_id': r.stock_id,
                'score_date': str(r.score_date),
                'chip_score': float(r.chip_score),
                'fundamental_score': float(r.fundamental_score),
                'technical_score': float(r.technical_score),
                'total_score': float(r.total_score),
                'rank': r.rank,
            }
            for r in results
        ]
        items = _build_score_responses(db, score_data)

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
    current_user: Annotated[User, Depends(get_current_user)],
    fetch_data: bool = True
):
    """
    Get single stock score details with breakdown.
    Auto-fetches missing data from FinMind if fetch_data=True.

    Args:
        stock_id: Stock ID
        db: Database session
        current_user: Authenticated user
        fetch_data: If True, fetch missing data on-demand before scoring

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

        # On-demand fetch missing data before scoring
        if fetch_data:
            from app.services.on_demand_data_fetcher import OnDemandDataFetcher
            fetcher = OnDemandDataFetcher(db)
            fetch_result = fetcher.fetch_missing_data(stock_id)
            logger.info(f"On-demand fetch for {stock_id}: {fetch_result}")

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
