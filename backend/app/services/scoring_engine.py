"""Composite scoring engine orchestrator."""
import logging
from datetime import date
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.score_result import ScoreResult
from app.models.stock import Stock
from app.services.hard_filter import HardFilter
from app.services.chip_scorer import ChipScorer
from app.services.fundamental_scorer import FundamentalScorer
from app.services.technical_scorer import TechnicalScorer

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Composite scoring orchestrator for multi-factor stock screening."""

    def __init__(self):
        self.hard_filter = HardFilter()
        self.chip_scorer = ChipScorer()
        self.fundamental_scorer = FundamentalScorer()
        self.technical_scorer = TechnicalScorer()

    def run_screening(
        self,
        db: Session,
        weights: dict = None,
        threshold: float = 2.5,
        candidate_ids: Optional[List[str]] = None,
        as_of_date: date = None,
    ) -> list:
        """
        Full screening pipeline.

        Args:
            db: Database session
            weights: Weight distribution dict
            threshold: Volume threshold for hard filter
            candidate_ids: Pre-filtered stock IDs (skip hard filter if given)

        Returns:
            List of score results sorted by rank
        """
        if weights is None:
            weights = {"chip": 40, "fundamental": 35, "technical": 25}

        logger.info(f"Starting screening with weights: {weights}")

        try:
            # Use provided candidates or run hard filter
            if candidate_ids:
                candidate_stocks = candidate_ids
            else:
                candidate_stocks = self.hard_filter.filter_by_volume(db, threshold, as_of_date=as_of_date)

            if not candidate_stocks:
                logger.warning("No stocks passed hard filter")
                return []

            logger.info(f"Scoring {len(candidate_stocks)} stocks")

            # Step 2 & 3: Score each candidate
            score_results = []

            for stock_id in candidate_stocks:
                try:
                    result = self.score_single_stock(db, stock_id, weights, as_of_date=as_of_date)

                    if result is not None:
                        # Skip stocks where all 3 factors have no data
                        has_data = (
                            result['chip_score'] > 0 or
                            result['fundamental_score'] > 0 or
                            result['technical_score'] > 0
                        )
                        if has_data:
                            score_results.append(result)

                except Exception as e:
                    logger.error(f"Error scoring {stock_id}: {e}")
                    continue

            if not score_results:
                logger.warning("No valid score results")
                return []

            # Step 4: Sort by total_score descending
            score_results.sort(key=lambda x: x['total_score'], reverse=True)

            # Step 5: Save to database with rank
            if as_of_date:
                score_date = as_of_date
            else:
                from sqlalchemy import func
                from app.models.daily_price import DailyPrice
                max_date = db.query(func.max(DailyPrice.trade_date)).scalar()
                score_date = max_date if max_date else date.today()

            # Clear old results for this date before saving new ones
            db.query(ScoreResult).filter(
                ScoreResult.score_date == score_date
            ).delete()

            saved_results = []

            for rank, result in enumerate(score_results, start=1):
                try:
                    score_record = ScoreResult(
                        stock_id=result['stock_id'],
                        score_date=score_date,
                        chip_score=Decimal(str(result['chip_score'])),
                        fundamental_score=Decimal(str(result['fundamental_score'])),
                        technical_score=Decimal(str(result['technical_score'])),
                        total_score=Decimal(str(result['total_score'])),
                        rank=rank,
                        chip_weight=Decimal(str(weights['chip'])),
                        fundamental_weight=Decimal(str(weights['fundamental'])),
                        technical_weight=Decimal(str(weights['technical']))
                    )
                    db.add(score_record)
                    saved_results.append(result)

                except Exception as e:
                    logger.error(f"Error saving score for {result['stock_id']}: {e}")
                    continue

            db.commit()

            logger.info(f"Screening complete: {len(saved_results)} stocks scored and saved")

            return saved_results

        except Exception as e:
            logger.error(f"Error in screening pipeline: {e}")
            db.rollback()
            return []

    def score_single_stock(
        self,
        db: Session,
        stock_id: str,
        weights: dict = None,
        as_of_date: date = None,
    ) -> dict:
        """
        Score a single stock (for detail view).

        Args:
            db: Database session
            stock_id: Stock ID to score
            weights: Weight distribution dict

        Returns:
            Dict with scores and details
        """
        if weights is None:
            weights = {"chip": 40, "fundamental": 35, "technical": 25}

        try:
            # Normalize weights to sum to 100
            total_weight = sum(weights.values())
            normalized_weights = {
                k: v / total_weight for k, v in weights.items()
            }

            # Calculate individual scores
            chip_result = self.chip_scorer.score(db, stock_id, as_of_date=as_of_date)
            fundamental_result = self.fundamental_scorer.score(db, stock_id)
            technical_result = self.technical_scorer.score(db, stock_id, as_of_date=as_of_date)

            chip_score = chip_result.get('chip_score', 0)
            fundamental_score = fundamental_result.get('fundamental_score', 0)
            technical_score = technical_result.get('technical_score', 0)

            # Weighted composite
            total_score = (
                chip_score * normalized_weights['chip'] +
                fundamental_score * normalized_weights['fundamental'] +
                technical_score * normalized_weights['technical']
            )

            return {
                'stock_id': stock_id,
                'chip_score': round(chip_score, 2),
                'chip_details': chip_result.get('details', {}),
                'fundamental_score': round(fundamental_score, 2),
                'fundamental_details': fundamental_result.get('details', {}),
                'technical_score': round(technical_score, 2),
                'technical_details': technical_result.get('details', {}),
                'total_score': round(total_score, 2)
            }

        except Exception as e:
            logger.error(f"Error scoring single stock {stock_id}: {e}")
            return None
