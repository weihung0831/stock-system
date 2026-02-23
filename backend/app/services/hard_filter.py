"""Hard threshold filter for volume-based stock screening."""
import logging
from datetime import date, timedelta
from typing import List
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.daily_price import DailyPrice

logger = logging.getLogger(__name__)

# Fallback: take top N stocks by recent volume if ratio filter empty
FALLBACK_TOP_N = 500


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

            # Check if previous week has trading data; if not (e.g. holidays),
            # search backwards up to 4 weeks to find a week with data
            prev_count = db.query(func.count(DailyPrice.id)).filter(
                DailyPrice.trade_date >= prev_start,
                DailyPrice.trade_date <= prev_end
            ).scalar() or 0

            if prev_count == 0:
                logger.warning(
                    f"No trading data in prev week {prev_start}~{prev_end}, "
                    "searching earlier weeks (holiday gap)"
                )
                for shift in range(2, 5):  # try 2~4 weeks back
                    candidate_start = recent_start - timedelta(days=7 * shift)
                    candidate_end = candidate_start + timedelta(days=4)
                    cnt = db.query(func.count(DailyPrice.id)).filter(
                        DailyPrice.trade_date >= candidate_start,
                        DailyPrice.trade_date <= candidate_end
                    ).scalar() or 0
                    if cnt > 0:
                        prev_start = candidate_start
                        prev_end = candidate_end
                        logger.info(
                            f"Found prev week with data: {prev_start}~{prev_end}"
                        )
                        break

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
            # If max_date has too few records (e.g. TWSE API delay after
            # holidays), fall back to the most recent date with enough data
            fallback_date = max_date
            day_count = db.query(func.count(DailyPrice.id)).filter(
                DailyPrice.trade_date == fallback_date
            ).scalar() or 0

            if day_count < 50:
                logger.warning(
                    f"Only {day_count} stocks on {fallback_date}, "
                    "searching for a date with more data"
                )
                rich_date = (
                    db.query(DailyPrice.trade_date)
                    .group_by(DailyPrice.trade_date)
                    .having(func.count(DailyPrice.id) >= 50)
                    .order_by(desc(DailyPrice.trade_date))
                    .first()
                )
                if rich_date:
                    fallback_date = rich_date[0]
                    if isinstance(fallback_date, str):
                        fallback_date = date.fromisoformat(fallback_date)
                    logger.info(f"Using fallback date: {fallback_date}")

            latest_vol = (
                db.query(
                    DailyPrice.stock_id,
                    func.sum(DailyPrice.volume).label('volume')
                )
                .filter(DailyPrice.trade_date == fallback_date)
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

            # Cap at FALLBACK_TOP_N to keep candidate pool consistent
            merged = merged[:FALLBACK_TOP_N]

            logger.info(
                f"Final filter: {len(merged)} stocks "
                f"({len(ratio_filtered)} ratio + {len(merged) - len(ratio_filtered)} top-vol)"
            )
            return merged

        except Exception as e:
            logger.error(f"Error in volume filter: {e}")
            return []
