"""API routes for right-side trading signal detection."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func as sqlfunc, desc as sqldesc
from sqlalchemy.orm import Session
import pandas as pd

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.services.right_side_signal_detector import RightSideSignalDetector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/right-side-signals", tags=["right-side-signals"])

detector = RightSideSignalDetector()

# Day-level cache: {date_str: [all_results]}
_cache: dict[str, list[dict]] = {}
_cache_date: str = ""


def _get_candidates(db: Session) -> list[str]:
    """Get candidate stock IDs by recent trading volume (top-500)."""
    from sqlalchemy import func as _func, desc as _desc
    max_date = db.query(_func.max(DailyPrice.trade_date)).scalar()
    if not max_date:
        return []
    rows = (
        db.query(DailyPrice.stock_id)
        .filter(DailyPrice.trade_date == max_date)
        .group_by(DailyPrice.stock_id)
        .order_by(_desc(_func.sum(DailyPrice.volume)))
        .limit(500)
        .all()
    )
    return [r[0] for r in rows]


def _batch_load_prices(db: Session, stock_ids: list[str]) -> dict[str, pd.DataFrame]:
    """Load 180 days of prices for all stocks in 1 SQL query, return per-stock DataFrames."""
    cutoff = date.today() - timedelta(days=180)
    rows = (
        db.query(
            DailyPrice.stock_id, DailyPrice.trade_date,
            DailyPrice.open, DailyPrice.high, DailyPrice.low,
            DailyPrice.close, DailyPrice.volume,
        )
        .filter(DailyPrice.stock_id.in_(stock_ids), DailyPrice.trade_date >= cutoff)
        .order_by(DailyPrice.stock_id, DailyPrice.trade_date.asc())
        .all()
    )

    # Group into per-stock DataFrames
    grouped: dict[str, list] = {}
    for sid, td, o, h, lo, c, v in rows:
        grouped.setdefault(sid, []).append({
            "date": td, "open": float(o), "high": float(h),
            "low": float(lo), "close": float(c), "volume": int(v),
        })

    result = {}
    for sid, records in grouped.items():
        df = pd.DataFrame(records)
        df.set_index("date", inplace=True)
        result[sid] = df
    return result


@router.get("/screen/batch")
def screen_batch(
    min_signals: int = Query(default=2, ge=1, le=6),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Batch screen right-side signals with day-level caching."""
    global _cache, _cache_date
    today = str(date.today())

    # Return cached results if available (filter by min_signals)
    if _cache_date == today and _cache:
        filtered = [r for r in _cache if r["triggered_count"] >= min_signals]
        return {"items": filtered, "total": len(filtered), "min_signals": min_signals}

    # Get candidates (same pool as Dashboard)
    stock_ids = _get_candidates(db)
    if not stock_ids:
        return {"items": [], "total": 0, "min_signals": min_signals}

    # Batch load prices in 1 SQL query (instead of 500)
    price_map = _batch_load_prices(db, stock_ids)

    # Build stock name lookup (1 SQL)
    stocks = db.query(Stock.stock_id, Stock.stock_name).filter(
        Stock.stock_id.in_(stock_ids)
    ).all()
    name_map = {s.stock_id: s.stock_name for s in stocks}

    # Detect signals using pre-loaded DataFrames
    all_results = []
    for sid in stock_ids:
        try:
            df = price_map.get(sid)
            result = detector.detect(db, sid, preloaded_df=df)
            if result["triggered_count"] > 0:
                all_results.append({
                    "stock_id": sid,
                    "stock_name": name_map.get(sid, sid),
                    **result,
                })
        except Exception as e:
            logger.warning(f"Signal detection failed for {sid}: {e}")

    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Cache all results for today
    _cache = all_results
    _cache_date = today

    filtered = [r for r in all_results if r["triggered_count"] >= min_signals]
    return {"items": filtered, "total": len(filtered), "min_signals": min_signals}


@router.get("/{stock_id}")
def get_stock_signals(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Get 6 right-side signals for a single stock."""
    result = detector.detect(db, stock_id)
    return {"stock_id": stock_id, **result}
