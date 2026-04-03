"""Screening router for momentum-based stock screening."""
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
    ScoreResultResponse,
    ScreeningResultsResponse,
    ScreeningSettingsResponse,
    ScreeningSettingsUpdate,
    SectorRankItem,
)
from app.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)


def _score_result_to_dict(r: ScoreResult) -> dict:
    """ScoreResult ORM -> dict for _build_score_responses."""
    return {
        'stock_id': r.stock_id,
        'score_date': str(r.score_date),
        'total_score': float(r.total_score),
        'momentum_score': float(r.momentum_score or 0),
        'classification': r.classification or '',
        'rank': r.rank,
        'buy_price': float(r.buy_price) if r.buy_price else None,
        'stop_price': float(r.stop_price) if r.stop_price else None,
        'add_price': float(r.add_price) if r.add_price else None,
        'target_price': float(r.target_price) if r.target_price else None,
        'sector_name': r.sector_name,
        'sector_rank': r.sector_rank,
        'market_status': r.market_status,
    }

router = APIRouter(prefix="/api/screening", tags=["screening"])



def _build_score_responses(
    db: Session,
    score_data: List[dict],
) -> List[ScoreResultResponse]:
    """Batch-build ScoreResultResponse items (3 SQL queries instead of N*2).

    Args:
        db: Database session
        score_data: List of dicts with momentum strategy fields
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
            total_score=d['total_score'],
            momentum_score=d.get('momentum_score', 0.0),
            classification=d.get('classification', ''),
            rank=d['rank'],
            industry=stock.industry if stock else None,
            close_price=close_price,
            change_percent=change_pct,
            buy_price=d.get('buy_price'),
            stop_price=d.get('stop_price'),
            add_price=d.get('add_price'),
            target_price=d.get('target_price'),
            sector_name=d.get('sector_name'),
            sector_rank=d.get('sector_rank'),
            market_status=d.get('market_status'),
        ))

    return items


@router.get("/results", response_model=ScreeningResultsResponse)
def get_results(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    score_date: str = None
):
    """Get latest screening results ranking."""
    try:
        if score_date:
            try:
                query_date = date.fromisoformat(score_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            query_date = db.query(
                sqlfunc.max(ScoreResult.score_date)
            ).scalar()
            if not query_date:
                return ScreeningResultsResponse(
                    items=[], total=0, threshold=2.5
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
                items=[], total=0, threshold=2.5
            )

        # Check market status — if DOWNTREND, return empty with marker
        first_result = results[0]
        market_status = first_result.market_status
        if market_status == "DOWNTREND":
            return ScreeningResultsResponse(
                items=[], total=0, threshold=2.5,
                market_status="DOWNTREND",
            )

        # Batch-build response items (3 SQL instead of N*2)
        score_data = [_score_result_to_dict(r) for r in results]
        items = _build_score_responses(db, score_data)

        # 讀取後端算好的族群排名（從 DB）
        top_sectors = []
        try:
            import json
            setting = db.query(SystemSetting).first()
            if setting and setting.top_sectors_json:
                top_sectors = [SectorRankItem(**s) for s in json.loads(setting.top_sectors_json)]
        except Exception:
            pass

        return ScreeningResultsResponse(
            items=items,
            total=len(items),
            threshold=2.5,
            market_status=market_status,
            top_sectors=top_sectors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screening results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得篩選結果失敗，請稍後再試"
        )


@router.get("/results/{stock_id}", response_model=ScoreResultResponse)
def get_stock_score(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get score for a single stock."""
    result = (
        db.query(ScoreResult)
        .filter(ScoreResult.stock_id == stock_id)
        .order_by(ScoreResult.score_date.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="找不到該股票的評分資料")

    items = _build_score_responses(db, [_score_result_to_dict(result)])
    if not items:
        raise HTTPException(status_code=404, detail="找不到該股票的評分資料")
    return items[0]


@router.post("/run")
def run_screening(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """手動觸發動能策略評分。"""
    try:
        from app.services.momentum.strategy import MomentumStrategy
        strategy = MomentumStrategy(db)
        result = strategy.run()
        return {
            "success": True,
            "market_status": result.get("market_status"),
            "scored_count": len(result.get("results", [])),
        }
    except Exception as e:
        logger.error(f"Scoring run failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"評分計算失敗: {str(e)}"
        )


def _get_or_create_settings(db: Session) -> SystemSetting:
    """Get system settings row, create with defaults if missing."""
    row = db.query(SystemSetting).first()
    if not row:
        row = SystemSetting(id=1, screening_threshold=2.5)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/settings", response_model=ScreeningSettingsResponse)
def get_screening_settings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current screening threshold."""
    row = _get_or_create_settings(db)
    return ScreeningSettingsResponse(threshold=row.screening_threshold)


@router.put("/settings", response_model=ScreeningSettingsResponse)
def update_screening_settings(
    body: ScreeningSettingsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Update screening threshold."""
    row = _get_or_create_settings(db)
    if body.threshold is not None:
        row.screening_threshold = body.threshold
    db.commit()
    db.refresh(row)
    return ScreeningSettingsResponse(threshold=row.screening_threshold)
