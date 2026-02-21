"""Per-user daily rate limiter for AI report generation."""
import logging
from datetime import date
from threading import Lock

logger = logging.getLogger(__name__)

REPORT_TIER_LIMITS = {
    'free':    {'per_day': 5},
    'premium': {'per_day': 999999},
}


class ReportRateLimiter:
    """In-memory per-user daily rate limiter for report generation."""

    def __init__(self):
        self._lock = Lock()
        self._daily_log: dict[str, dict] = {}

    def check(self, user_id: str, tier: str = 'free') -> tuple[bool, str]:
        """Check if user is allowed to generate a report.

        Returns:
            (allowed, reason) — reason is empty string if allowed.
        """
        today = date.today()
        limits = REPORT_TIER_LIMITS.get(tier, REPORT_TIER_LIMITS['free'])

        with self._lock:
            daily = self._daily_log.get(user_id)
            if daily and daily["date"] == today:
                if daily["count"] >= limits['per_day']:
                    return False, f"已達每日 AI 報告上限 {limits['per_day']} 次"
            else:
                self._daily_log[user_id] = {"date": today, "count": 0}

            self._daily_log[user_id]["count"] += 1
            remaining = limits['per_day'] - self._daily_log[user_id]["count"]
            logger.info(f"Report rate OK: user={user_id}, remaining={remaining}")
            return True, ""


    def check_quota(self, user_id: str, tier: str = 'free') -> dict:
        """Read-only quota check — does not increment counters."""
        today = date.today()
        limits = REPORT_TIER_LIMITS.get(tier, REPORT_TIER_LIMITS['free'])

        with self._lock:
            daily = self._daily_log.get(user_id)
            daily_used = 0
            if daily and daily["date"] == today:
                daily_used = daily["count"]

            return {
                "daily_limit": limits['per_day'],
                "daily_used": daily_used,
                "daily_remaining": limits['per_day'] - daily_used,
            }


report_rate_limiter = ReportRateLimiter()
