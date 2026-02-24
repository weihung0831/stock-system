"""Analysis and scoring steps for pipeline."""
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.services.hard_filter import HardFilter
from app.services.scoring_engine import ScoringEngine

logger = logging.getLogger(__name__)


def step_hard_filter(db: Session, date_str: str, threshold: float = 2.5) -> Dict[str, Any]:
    """
    Apply hard filter to get candidate stocks.

    Args:
        db: Database session
        date_str: Date string in YYYY-MM-DD format
        threshold: Volume threshold in hundred million TWD

    Returns:
        Result dict with success status, message, and candidate stock IDs
    """
    try:
        logger.info(f"Starting hard filter with threshold {threshold}")
        hard_filter = HardFilter()

        candidate_stocks = hard_filter.filter_by_volume(db, threshold)

        logger.info(f"Hard filter completed: {len(candidate_stocks)} candidates")

        return {
            "success": True,
            "message": f"Filtered {len(candidate_stocks)} candidate stocks",
            "candidates": candidate_stocks
        }

    except Exception as e:
        logger.error(f"Hard filter failed: {e}", exc_info=True)
        return {"success": False, "message": f"Error: {str(e)}", "candidates": []}


def step_scoring(
    db: Session,
    stock_ids: List[str],
    date_str: str,
    weights: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Calculate composite scores for candidate stocks.

    Args:
        db: Database session
        stock_ids: List of candidate stock IDs
        date_str: Date string in YYYY-MM-DD format
        weights: Weight distribution (chip, fundamental, technical)

    Returns:
        Result dict with success status and message
    """
    try:
        logger.info(f"Starting scoring for {len(stock_ids)} stocks")

        if weights is None:
            weights = {"chip": 40, "fundamental": 35, "technical": 25}

        engine = ScoringEngine()
        results = engine.run_screening(
            db, weights=weights, threshold=2.5,
            candidate_ids=stock_ids,
        )

        logger.info(f"Scoring completed: {len(results)} scored stocks")

        return {
            "success": True,
            "message": f"Scored {len(results)} stocks",
            "scored_count": len(results)
        }

    except Exception as e:
        logger.error(f"Scoring failed: {e}", exc_info=True)
        return {"success": False, "message": f"Error: {str(e)}"}


