"""Chip (institutional investor) scoring service."""
import logging
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading
from app.models.daily_price import DailyPrice

logger = logging.getLogger(__name__)


class ChipScorer:
    """Calculate chip (institutional investor) score for stocks."""

    def score(self, db: Session, stock_id: str, as_of_date: date = None) -> dict:
        """
        Calculate chip (institutional) score.

        Indicators (weighted sum, normalize to 0-100):
        A. Consecutive buy days by 3 institutional investors (30%)
           - foreign weight highest
           - 5+ consecutive days = high score, 1-2 days = medium
        B. Institutional net buy / daily volume ratio (40%)
           - Higher ratio = deeper institutional involvement
        C. Margin changes (30%)
           - Margin decrease + short increase = positive signal
           - 5-day change rate for both

        Args:
            db: Database session
            stock_id: Stock ID to score

        Returns:
            Dict with chip_score (0-100) and details
        """
        try:
            # Get last 20 trading days data relative to as_of_date
            ref_date = as_of_date or date.today()
            cutoff_date = ref_date - timedelta(days=30)

            query = db.query(Institutional).filter(
                Institutional.stock_id == stock_id,
                Institutional.trade_date >= cutoff_date,
            )
            if as_of_date:
                query = query.filter(Institutional.trade_date <= as_of_date)

            institutional_data = (
                query.order_by(Institutional.trade_date.desc())
                .limit(20)
                .all()
            )

            if not institutional_data:
                logger.warning(f"No institutional data for {stock_id}")
                return {"chip_score": 0.0, "details": {"error": "No data"}}

            # A. Consecutive buy days (30%)
            consecutive_score = self._calculate_consecutive_buy_score(institutional_data)

            # B. Net buy / volume ratio (40%)
            volume_ratio_score = self._calculate_net_buy_ratio_score(
                db, stock_id, institutional_data
            )

            # C. Margin changes (30%)
            margin_score = self._calculate_margin_score(db, stock_id, as_of_date)

            # Weighted composite
            chip_score = (
                consecutive_score * 0.3 +
                volume_ratio_score * 0.4 +
                margin_score * 0.3
            )

            details = {
                "consecutive_buy_score": round(consecutive_score, 2),
                "net_buy_ratio_score": round(volume_ratio_score, 2),
                "margin_score": round(margin_score, 2),
            }

            logger.info(f"Chip score for {stock_id}: {chip_score:.2f}")

            return {
                "chip_score": round(chip_score, 2),
                "details": details
            }

        except Exception as e:
            logger.error(f"Error calculating chip score for {stock_id}: {e}")
            return {"chip_score": 0.0, "details": {"error": str(e)}}

    def _calculate_consecutive_buy_score(self, data: list) -> float:
        """Calculate score based on consecutive institutional buy days."""
        if not data:
            return 0.0

        # Count consecutive buy days for each institution
        foreign_consecutive = 0
        trust_consecutive = 0
        dealer_consecutive = 0

        for record in data:
            if record.foreign_net > 0:
                foreign_consecutive += 1
            else:
                break

        for record in data:
            if record.trust_net > 0:
                trust_consecutive += 1
            else:
                break

        for record in data:
            if record.dealer_net > 0:
                dealer_consecutive += 1
            else:
                break

        # Weighted scoring: foreign has highest weight
        foreign_score = min(foreign_consecutive * 5, 50)  # Max 50
        trust_score = min(trust_consecutive * 3, 30)      # Max 30
        dealer_score = min(dealer_consecutive * 2, 20)    # Max 20

        return min(foreign_score + trust_score + dealer_score, 100)

    def _calculate_net_buy_ratio_score(
        self, db: Session, stock_id: str, institutional_data: list
    ) -> float:
        """Calculate institutional net buy to volume ratio score."""
        if not institutional_data:
            return 0.0

        try:
            # Get recent 5 days average
            recent_dates = [d.trade_date for d in institutional_data[:5]]

            total_net_buy = float(sum(d.total_net for d in institutional_data[:5]))

            # Get volume for same dates
            volumes = (
                db.query(func.sum(DailyPrice.volume))
                .filter(
                    DailyPrice.stock_id == stock_id,
                    DailyPrice.trade_date.in_(recent_dates)
                )
                .scalar()
            )

            if not volumes or volumes == 0:
                return 0.0

            # Net buy ratio
            ratio = (total_net_buy / float(volumes)) * 100

            # Score mapping: ratio > 5% = 100, ratio < -5% = 0
            if ratio >= 5.0:
                score = 100
            elif ratio <= -5.0:
                score = 0
            else:
                score = 50 + (ratio * 5)  # Linear mapping

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error calculating net buy ratio: {e}")
            return 0.0

    def _calculate_margin_score(self, db: Session, stock_id: str, as_of_date: date = None) -> float:
        """Calculate margin trading change score."""
        try:
            ref_date = as_of_date or date.today()
            cutoff_date = ref_date - timedelta(days=10)

            query = db.query(MarginTrading).filter(
                MarginTrading.stock_id == stock_id,
                MarginTrading.trade_date >= cutoff_date,
            )
            if as_of_date:
                query = query.filter(MarginTrading.trade_date <= as_of_date)

            margin_data = (
                query.order_by(MarginTrading.trade_date.desc())
                .limit(5)
                .all()
            )

            if len(margin_data) < 2:
                return 50.0  # Neutral score

            # 5-day change rate
            latest = margin_data[0]
            oldest = margin_data[-1]

            margin_change_rate = 0.0
            short_change_rate = 0.0

            if oldest.margin_balance > 0:
                margin_change_rate = float(
                    (latest.margin_balance - oldest.margin_balance)
                ) / float(oldest.margin_balance) * 100

            if oldest.short_balance > 0:
                short_change_rate = float(
                    (latest.short_balance - oldest.short_balance)
                ) / float(oldest.short_balance) * 100

            # Positive signal: margin decrease + short increase
            score = 50.0

            if margin_change_rate < 0:
                score += min(abs(margin_change_rate) * 2, 30)

            if short_change_rate > 0:
                score += min(short_change_rate * 2, 20)

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error calculating margin score: {e}")
            return 50.0
