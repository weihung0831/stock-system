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
    """Batch screen: top 100 stocks by recent volume from DailyPrice."""
    from sqlalchemy import func, desc
    from app.models.daily_price import DailyPrice

    latest_date = db.query(func.max(DailyPrice.trade_date)).scalar()
    if not latest_date:
        return {"items": [], "total": 0, "min_signals": min_signals}

    # If latest date has too few records (e.g. API delay after holidays),
    # fall back to the most recent date with sufficient data
    day_count = db.query(func.count(DailyPrice.id)).filter(
        DailyPrice.trade_date == latest_date
    ).scalar() or 0
    if day_count < 50:
        rich_date = (
            db.query(DailyPrice.trade_date)
            .group_by(DailyPrice.trade_date)
            .having(func.count(DailyPrice.id) >= 50)
            .order_by(desc(DailyPrice.trade_date))
            .first()
        )
        if rich_date:
            latest_date = rich_date[0]

    top100_vol = (
        db.query(DailyPrice.stock_id)
        .filter(DailyPrice.trade_date == latest_date)
        .order_by(DailyPrice.volume.desc())
        .limit(100)
        .all()
    )
    stock_ids = [row[0] for row in top100_vol]
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
