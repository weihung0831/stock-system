"""Custom screening service for advanced filtering."""
import logging
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
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
    """
    Perform custom screening with multiple filter criteria.

    Args:
        db: Database session
        filters: Dictionary containing filter criteria:
            - industry: str (optional) - Filter by industry
            - min_total_score: float (optional) - Minimum total score
            - min_chip_score: float (optional) - Minimum chip score
            - min_fundamental_score: float (optional) - Minimum fundamental score
            - min_technical_score: float (optional) - Minimum technical score
            - min_close_price: float (optional) - Minimum stock price
            - max_close_price: float (optional) - Maximum stock price
        score_date: Target date for screening (default: latest available)

    Returns:
        List of matching score results with stock info, sorted by total_score desc
    """
    logger.info(f"Custom screening with filters: {filters}")

    # Build query joining ScoreResult and Stock
    query = db.query(
        ScoreResult,
        Stock.stock_name,
        Stock.industry,
        Stock.market
    ).join(
        Stock,
        ScoreResult.stock_id == Stock.stock_id
    )

    # Apply date filter
    if score_date:
        query = query.filter(ScoreResult.score_date == score_date)
    else:
        # Get latest date
        latest_date = db.query(ScoreResult.score_date).order_by(
            ScoreResult.score_date.desc()
        ).first()
        if latest_date:
            query = query.filter(ScoreResult.score_date == latest_date[0])

    # Apply industry filter using SectorTag keywords for fuzzy matching
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

    # Apply score filters
    if filters.get("min_total_score") is not None:
        query = query.filter(ScoreResult.total_score >= filters["min_total_score"])

    if filters.get("min_chip_score") is not None:
        query = query.filter(ScoreResult.chip_score >= filters["min_chip_score"])

    if filters.get("min_fundamental_score") is not None:
        query = query.filter(
            ScoreResult.fundamental_score >= filters["min_fundamental_score"]
        )

    if filters.get("min_technical_score") is not None:
        query = query.filter(
            ScoreResult.technical_score >= filters["min_technical_score"]
        )

    # Sort by total score descending
    query = query.order_by(ScoreResult.total_score.desc())

    # Execute query
    results = query.all()

    logger.info(f"Found {len(results)} matching stocks")

    # Batch fetch latest 2 close prices per stock (for close_price & change_percent)
    stock_ids = [r[0].stock_id for r in results]
    price_map: Dict[str, float] = {}
    change_map: Dict[str, float] = {}
    if stock_ids:
        from sqlalchemy import desc
        from sqlalchemy.sql import func as sqlfunc
        # Get the 2 most recent trade dates across all stocks
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
                db.query(DailyPrice.stock_id, DailyPrice.trade_date, DailyPrice.close)
                .filter(
                    DailyPrice.stock_id.in_(stock_ids),
                    DailyPrice.trade_date.in_(date_list),
                )
                .order_by(DailyPrice.stock_id, desc(DailyPrice.trade_date))
                .all()
            )
            # Group by stock_id
            from collections import defaultdict
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
        output.append({
            "stock_id": score_result.stock_id,
            "stock_name": stock_name,
            "industry": industry,
            "market": market,
            "score_date": score_result.score_date.isoformat(),
            "chip_score": float(score_result.chip_score),
            "fundamental_score": float(score_result.fundamental_score),
            "technical_score": float(score_result.technical_score),
            "total_score": float(score_result.total_score),
            "rank": score_result.rank,
            "close_price": price_map.get(score_result.stock_id, 0),
            "change_percent": change_map.get(score_result.stock_id, 0.0),
        })

    return output
