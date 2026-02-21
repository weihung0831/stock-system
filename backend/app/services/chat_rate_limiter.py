"""Per-user rate limiter for AI chat assistant with tier-aware limits."""
import time
import logging
from datetime import date
from threading import Lock

logger = logging.getLogger(__name__)

CHAT_TIER_LIMITS = {
    'free':    {'per_minute': 3,  'per_day': 10},
    'premium': {'per_minute': 5,  'per_day': 100},
}


class ChatRateLimiter:
    """In-memory per-user rate limiter with tier-aware minute and daily limits."""

    def __init__(self):
        self._lock = Lock()
        # {user_id: [timestamp, ...]} for minute-window tracking
        self._minute_log: dict[str, list[float]] = {}
        # {user_id: {"date": date, "count": int}} for daily tracking
        self._daily_log: dict[str, dict] = {}

    def check(self, user_id: str, tier: str = 'free') -> tuple[bool, str, dict]:
        """Check if user is allowed to send a message.

        Returns:
            (allowed, reason, quota) — reason is empty string if allowed.
            quota contains daily_remaining and minute_remaining.
        """
        now = time.time()
        today = date.today()
        limits = CHAT_TIER_LIMITS.get(tier, CHAT_TIER_LIMITS['free'])

        with self._lock:
            # --- Daily limit ---
            daily = self._daily_log.get(user_id)
            if daily and daily["date"] == today:
                if daily["count"] >= limits['per_day']:
                    quota = {"daily_remaining": 0, "minute_remaining": 0}
                    return False, f"已達每日上限 {limits['per_day']} 則，明天再來吧！", quota
            else:
                # New day, reset
                self._daily_log[user_id] = {"date": today, "count": 0}

            # --- Per-minute limit ---
            timestamps = self._minute_log.get(user_id, [])
            cutoff = now - 60
            timestamps = [t for t in timestamps if t > cutoff]
            if len(timestamps) >= limits['per_minute']:
                wait = int(60 - (now - timestamps[0])) + 1
                daily_remaining = limits['per_day'] - self._daily_log[user_id]["count"]
                quota = {"daily_remaining": daily_remaining, "minute_remaining": 0}
                return False, f"發送太頻繁，請等 {wait} 秒後再試。", quota

            # --- Allowed: record this request ---
            timestamps.append(now)
            self._minute_log[user_id] = timestamps
            self._daily_log[user_id]["count"] += 1

            daily_remaining = limits['per_day'] - self._daily_log[user_id]["count"]
            minute_remaining = limits['per_minute'] - len(timestamps)
            quota = {"daily_remaining": daily_remaining, "minute_remaining": minute_remaining}

            logger.info(f"Chat rate OK: user={user_id}, daily_remaining={daily_remaining}")
            return True, "", quota

    def check_quota(self, user_id: str, tier: str = 'free') -> dict:
        """Read-only quota check — does not increment counters."""
        today = date.today()
        limits = CHAT_TIER_LIMITS.get(tier, CHAT_TIER_LIMITS['free'])

        with self._lock:
            daily = self._daily_log.get(user_id)
            daily_used = 0
            if daily and daily["date"] == today:
                daily_used = daily["count"]

            return {
                "daily_limit": limits['per_day'],
                "daily_used": daily_used,
                "daily_remaining": limits['per_day'] - daily_used,
                "minute_limit": limits['per_minute'],
            }


# Singleton instance
chat_rate_limiter = ChatRateLimiter()
