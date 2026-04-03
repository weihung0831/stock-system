"""Custom screening service for advanced filtering."""
import logging
from typing import List, Dict, Any, Optional
from datetime import date
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from sqlalchemy.sql import func as sqlfunc
from app.models.score_result import ScoreResult
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.sector_tag import SectorTag

logger = logging.getLogger(__name__)


def custom_screen(
    db: Session,
    filters: Dict[str, Any],
    score_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Perform custom screening with momentum strategy filters.

    Args:
        db: Database session
        filters: Filter criteria:
            - industry: str — Filter by industry
            - min_total_score: float — Minimum total score
            - min_momentum_score: float — Minimum momentum score
            - classification: str — BUY/HOLD/SELL filter
        score_date: Target date (default: latest available)

    Returns:
        Matching stocks sorted by total_score desc
    """
    logger.info(f"Custom screening with filters: {filters}")

    query = db.query(
        ScoreResult, Stock.stock_name, Stock.industry, Stock.market
    ).join(Stock, ScoreResult.stock_id == Stock.stock_id)

    # Date filter
    if score_date:
        query = query.filter(ScoreResult.score_date == score_date)
    else:
        latest = db.query(ScoreResult.score_date).order_by(
            ScoreResult.score_date.desc()
        ).first()
        if latest:
            query = query.filter(ScoreResult.score_date == latest[0])

    # Industry filter (SectorTag fuzzy matching)
    if filters.get("industry"):
        tag = db.query(SectorTag).filter(
            SectorTag.name == filters["industry"]
        ).first()
        if tag and tag.keywords:
            keywords = [k.strip() for k in tag.keywords.split(",") if k.strip()]
            if keywords:
                conditions = [Stock.industry.contains(kw) for kw in keywords]
                query = query.filter(or_(*conditions))
        else:
            query = query.filter(Stock.industry.contains(filters["industry"]))

    # Score filters
    if filters.get("min_total_score") is not None:
        query = query.filter(ScoreResult.total_score >= filters["min_total_score"])

    if filters.get("min_momentum_score") is not None:
        query = query.filter(
            ScoreResult.momentum_score >= filters["min_momentum_score"]
        )

    if filters.get("classification"):
        query = query.filter(
            ScoreResult.classification == filters["classification"]
        )

    query = query.order_by(ScoreResult.total_score.desc())
    results = query.all()
    logger.info(f"Found {len(results)} matching stocks")

    # Batch fetch latest 2 close prices
    stock_ids = [r[0].stock_id for r in results]
    price_map: Dict[str, float] = {}
    change_map: Dict[str, float] = {}
    if stock_ids:
        two_dates = (
            db.query(DailyPrice.trade_date)
            .filter(DailyPrice.stock_id.in_(stock_ids))
            .distinct()
            .order_by(desc(DailyPrice.trade_date))
            .limit(2)
            .all()
        )
        if two_dates:
            date_list = [d[0] for d in two_dates]
            prices = (
                db.query(
                    DailyPrice.stock_id, DailyPrice.trade_date, DailyPrice.close
                )
                .filter(
                    DailyPrice.stock_id.in_(stock_ids),
                    DailyPrice.trade_date.in_(date_list),
                )
                .order_by(DailyPrice.stock_id, desc(DailyPrice.trade_date))
                .all()
            )
            grouped: Dict[str, list] = defaultdict(list)
            for p in prices:
                grouped[p.stock_id].append(float(p.close or 0))
            for sid, closes in grouped.items():
                price_map[sid] = closes[0]
                if len(closes) >= 2 and closes[1] > 0:
                    change_map[sid] = round(
                        (closes[0] - closes[1]) / closes[1] * 100, 2
                    )

    # Format results
    output = []
    for score_result, stock_name, industry, market in results:
        sr = score_result
        output.append({
            "stock_id": sr.stock_id,
            "stock_name": stock_name,
            "industry": industry,
            "market": market,
            "score_date": sr.score_date.isoformat(),
            "total_score": float(sr.total_score),
            "momentum_score": float(sr.momentum_score or 0),
            "classification": sr.classification or "",
            "rank": sr.rank,
            "close_price": price_map.get(sr.stock_id, 0),
            "change_percent": change_map.get(sr.stock_id, 0.0),
            "buy_price": float(sr.buy_price) if sr.buy_price else None,
            "stop_price": float(sr.stop_price) if sr.stop_price else None,
            "add_price": float(sr.add_price) if sr.add_price else None,
            "target_price": float(sr.target_price) if sr.target_price else None,
            "sector_name": sr.sector_name,
            "sector_rank": sr.sector_rank,
            "market_status": sr.market_status,
        })

    return output
