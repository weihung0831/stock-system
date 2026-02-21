"""API routes for right-side trading signal detection."""
from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stock import Stock
from app.services.right_side_signal_detector import RightSideSignalDetector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/right-side-signals", tags=["right-side-signals"])

detector = RightSideSignalDetector()


@router.get("/screen/batch")
def screen_batch(
    min_signals: int = Query(default=2, ge=1, le=6),
    db: Session = Depends(get_db),
):
    """Batch screen: top 50 scored stocks + stocks with volume > 2000 lots."""
    from datetime import timedelta
    from sqlalchemy import func
    from app.models.daily_price import DailyPrice
    from app.models.score_result import ScoreResult

    candidate_ids: set[str] = set()

    # Source 1: Top 50 from latest ScoreResult
    latest_date = db.query(ScoreResult.score_date).order_by(
        ScoreResult.score_date.desc()
    ).first()
    if latest_date:
        top50 = (
            db.query(ScoreResult.stock_id)
            .filter(ScoreResult.score_date == latest_date[0])
            .order_by(ScoreResult.total_score.desc())
            .limit(50)
            .all()
        )
        candidate_ids.update(row[0] for row in top50)

    # Source 2: Stocks with latest volume > 2000 lots (2,000,000 shares)
    recent_cutoff = date.today() - timedelta(days=7)
    high_vol = (
        db.query(DailyPrice.stock_id)
        .filter(DailyPrice.trade_date >= recent_cutoff)
        .group_by(DailyPrice.stock_id)
        .having(func.max(DailyPrice.volume) > 2_000_000)
        .all()
    )
    candidate_ids.update(row[0] for row in high_vol)

    stock_ids = list(candidate_ids)
    if not stock_ids:
        return {"items": [], "total": 0, "min_signals": min_signals}

    # Build stock name lookup
    stocks = db.query(Stock.stock_id, Stock.stock_name).filter(
        Stock.stock_id.in_(stock_ids)
    ).all()
    name_map = {s.stock_id: s.stock_name for s in stocks}

    results = []
    for sid in stock_ids:
        try:
            result = detector.detect(db, sid)
            if result["triggered_count"] >= min_signals:
                results.append({
                    "stock_id": sid,
                    "stock_name": name_map.get(sid, sid),
                    **result,
                })
        except Exception as e:
            logger.warning(f"Signal detection failed for {sid}: {e}")

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "items": results,
        "total": len(results),
        "min_signals": min_signals,
    }


@router.get("/{stock_id}")
def get_stock_signals(stock_id: str, db: Session = Depends(get_db)):
    """Get 6 right-side signals for a single stock."""
    result = detector.detect(db, stock_id)
    return {"stock_id": stock_id, **result}
