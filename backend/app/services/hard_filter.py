"""Hard threshold filter for volume-based stock screening."""
import logging
from datetime import date, timedelta
from typing import List
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.daily_price import DailyPrice

logger = logging.getLogger(__name__)

# Fallback: take top N stocks by recent volume if ratio filter empty
FALLBACK_TOP_N = 100


class HardFilter:
    """Volume-based hard threshold filter for stock screening."""

    def filter_by_volume(
        self, db: Session, threshold: float = 2.5, as_of_date: date = None
    ) -> List[str]:
        """
        Filter stocks by volume ratio (recent vs previous week).

        Falls back to top-N by recent volume if ratio filter yields nothing.
        Uses as_of_date or latest trading date from DB.
        """
        try:
            if as_of_date:
                # Use the closest trading date on or before as_of_date
                max_date = db.query(func.max(DailyPrice.trade_date)).filter(
                    DailyPrice.trade_date <= as_of_date
                ).scalar()
            else:
                max_date = db.query(func.max(DailyPrice.trade_date)).scalar()
            if not max_date:
                logger.warning("No price data for volume filter")
                return []

            if isinstance(max_date, str):
                max_date = date.fromisoformat(max_date)

            weekday = max_date.weekday()
            recent_start = max_date - timedelta(days=weekday)
            recent_end = recent_start + timedelta(days=4)
            prev_start = recent_start - timedelta(days=7)
            prev_end = prev_start + timedelta(days=4)

            logger.info(
                f"Volume filter - Prev: {prev_start}~{prev_end}, "
                f"Recent: {recent_start}~{recent_end}, "
                f"Threshold: {threshold}x"
            )

            # --- Try ratio-based filter first ---
            prev_q = (
                db.query(
                    DailyPrice.stock_id,
                    func.sum(DailyPrice.volume).label('volume')
                )
                .filter(
                    DailyPrice.trade_date >= prev_start,
                    DailyPrice.trade_date <= prev_end
                )
                .group_by(DailyPrice.stock_id)
                .subquery()
            )

            recent_q = (
                db.query(
                    DailyPrice.stock_id,
                    func.sum(DailyPrice.volume).label('volume')
                )
                .filter(
                    DailyPrice.trade_date >= recent_start,
                    DailyPrice.trade_date <= recent_end
                )
                .group_by(DailyPrice.stock_id)
                .subquery()
            )

            results = (
                db.query(recent_q.c.stock_id)
                .join(prev_q, recent_q.c.stock_id == prev_q.c.stock_id)
                .filter(
                    prev_q.c.volume > 0,
                    recent_q.c.volume > threshold * prev_q.c.volume
                )
                .all()
            )

            ratio_filtered = [r[0] for r in results]
            logger.info(
                f"Volume ratio filter: {len(ratio_filtered)} stocks passed"
            )

            # Always get top N by volume as baseline
            latest_vol = (
                db.query(
                    DailyPrice.stock_id,
                    func.sum(DailyPrice.volume).label('volume')
                )
                .filter(DailyPrice.trade_date == max_date)
                .group_by(DailyPrice.stock_id)
                .order_by(desc('volume'))
                .limit(FALLBACK_TOP_N)
                .all()
            )
            top_n = [r[0] for r in latest_vol]

            # Merge: ratio-filtered first, then fill with top-N
            seen = set(ratio_filtered)
            merged = list(ratio_filtered)
            for sid in top_n:
                if sid not in seen:
                    merged.append(sid)
                    seen.add(sid)

            logger.info(
                f"Final filter: {len(merged)} stocks "
                f"({len(ratio_filtered)} ratio + {len(merged) - len(ratio_filtered)} top-vol)"
            )
            return merged

        except Exception as e:
            logger.error(f"Error in volume filter: {e}")
            return []
