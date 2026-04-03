"""Analysis and scoring steps for pipeline."""
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.daily_price import DailyPrice
from app.services.momentum.strategy import MomentumStrategy

logger = logging.getLogger(__name__)

CANDIDATE_TOP_N = 500


def step_hard_filter(db: Session, date_str: str, threshold: float = 2.5) -> Dict[str, Any]:
    """
    Get candidate stocks by recent trading volume (top-N).

    Args:
        db: Database session
        date_str: Date string in YYYY-MM-DD format
        threshold: Kept for API compatibility (unused)

    Returns:
        Result dict with success status, message, and candidate stock IDs
    """
    try:
        logger.info("Starting candidate selection (top-%d by volume)", CANDIDATE_TOP_N)

        max_date = db.query(func.max(DailyPrice.trade_date)).scalar()
        if not max_date:
            return {"success": True, "message": "No price data", "candidates": []}

        rows = (
            db.query(DailyPrice.stock_id)
            .filter(DailyPrice.trade_date == max_date)
            .group_by(DailyPrice.stock_id)
            .order_by(desc(func.sum(DailyPrice.volume)))
            .limit(CANDIDATE_TOP_N)
            .all()
        )
        candidate_stocks = [r[0] for r in rows]

        logger.info(f"Candidate selection completed: {len(candidate_stocks)} stocks")

        return {
            "success": True,
            "message": f"Selected {len(candidate_stocks)} candidate stocks",
            "candidates": candidate_stocks,
        }

    except Exception as e:
        logger.error(f"Candidate selection failed: {e}", exc_info=True)
        return {"success": False, "message": f"Error: {str(e)}", "candidates": []}


def step_scoring(
    db: Session,
    stock_ids: List[str],
    date_str: str,
    weights: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Execute momentum strategy pipeline.

    Args:
        db: Database session
        stock_ids: List of candidate stock IDs (kept for API compatibility)
        date_str: Date string in YYYY-MM-DD format
        weights: Weight distribution (kept for API compatibility)

    Returns:
        Result dict with success status and message
    """
    try:
        as_of = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        logger.info("Starting momentum strategy scoring")

        strategy = MomentumStrategy(db)
        output = strategy.run(as_of_date=as_of)

        result_count = len(output.get("results", []))
        logger.info(
            f"Momentum strategy completed: {output['market_status']}, "
            f"{result_count} scored stocks"
        )

        return {
            "success": True,
            "message": f"Momentum strategy: {output['market_status']}, {result_count} stocks",
            "scored_count": result_count,
            "market_status": output["market_status"],
        }

    except Exception as e:
        logger.error(f"Scoring failed: {e}", exc_info=True)
        return {"success": False, "message": f"Error: {str(e)}"}


