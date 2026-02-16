"""Analysis and scoring steps for pipeline."""
import logging
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.services.hard_filter import HardFilter
from app.services.scoring_engine import ScoringEngine
from app.services.llm_analyzer import LLMAnalyzer
from app.services.llm_client import LLMClient
from app.models.score_result import ScoreResult

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


def step_llm_analysis(db: Session, top_n: int = 10) -> Dict[str, Any]:
    """
    Generate LLM analysis for top-ranked stocks.

    Args:
        db: Database session
        top_n: Number of top stocks to analyze

    Returns:
        Result dict with success status and message
    """
    try:
        logger.info(f"Starting LLM analysis for top {top_n} stocks")

        # Get latest scored stocks from ScoreResult table
        from sqlalchemy import func as sqlfunc
        latest_score_date = db.query(
            sqlfunc.max(ScoreResult.score_date)
        ).scalar()
        if not latest_score_date:
            return {"success": True, "message": "No scores yet", "reports_count": 0}

        query = db.query(ScoreResult).filter(
            ScoreResult.score_date == latest_score_date
        ).order_by(desc(ScoreResult.total_score))
        if top_n > 0:
            query = query.limit(top_n)
        top_scores = query.all()

        if not top_scores:
            logger.warning("No score results found for LLM analysis")
            return {"success": True, "message": "No stocks to analyze", "reports_count": 0}

        # Prepare stock data for analysis
        top_stocks = []
        for score in top_scores:
            top_stocks.append({
                'stock_id': score.stock_id,
                'scores': {
                    'chip': float(score.chip_score),
                    'fundamental': float(score.fundamental_score),
                    'technical': float(score.technical_score),
                    'total': float(score.total_score)
                }
            })

        # Initialize LLM client and analyzer
        llm_client = LLMClient(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
        )
        analyzer = LLMAnalyzer(llm_client=llm_client)

        # Analyze top stocks in batch
        results = analyzer.analyze_batch(db, top_stocks)

        logger.info(f"LLM analysis completed: {len(results)} reports generated")

        return {
            "success": True,
            "message": f"Generated {len(results)} LLM reports",
            "reports_count": len(results)
        }

    except Exception as e:
        logger.error(f"LLM analysis failed: {e}", exc_info=True)
        return {"success": False, "message": f"Error: {str(e)}"}
