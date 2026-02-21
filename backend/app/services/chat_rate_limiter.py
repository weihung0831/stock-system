"""Per-user rate limiter for AI chat assistant."""
import time
import logging
from datetime import date
from threading import Lock

logger = logging.getLogger(__name__)


class ChatRateLimiter:
    """In-memory per-user rate limiter with minute and daily limits."""

    def __init__(self, per_minute: int = 3, per_day: int = 20):
        self.per_minute = per_minute
        self.per_day = per_day
        self._lock = Lock()
        # {user_id: [timestamp, ...]} for minute-window tracking
        self._minute_log: dict[str, list[float]] = {}
        # {user_id: {"date": date, "count": int}} for daily tracking
        self._daily_log: dict[str, dict] = {}

    def check(self, user_id: str) -> tuple[bool, str]:
        """Check if user is allowed to send a message.

        Returns:
            (allowed, reason) — reason is empty string if allowed.
        """
        now = time.time()
        today = date.today()

        with self._lock:
            # --- Daily limit ---
            daily = self._daily_log.get(user_id)
            if daily and daily["date"] == today:
                if daily["count"] >= self.per_day:
                    return False, f"已達每日上限 {self.per_day} 則，明天再來吧！"
            else:
                # New day, reset
                self._daily_log[user_id] = {"date": today, "count": 0}

            # --- Per-minute limit ---
            timestamps = self._minute_log.get(user_id, [])
            # Remove entries older than 60 seconds
            cutoff = now - 60
            timestamps = [t for t in timestamps if t > cutoff]
            if len(timestamps) >= self.per_minute:
                wait = int(60 - (now - timestamps[0])) + 1
                return False, f"發送太頻繁，請等 {wait} 秒後再試。"

            # --- Allowed: record this request ---
            timestamps.append(now)
            self._minute_log[user_id] = timestamps
            self._daily_log[user_id]["count"] += 1

            remaining = self.per_day - self._daily_log[user_id]["count"]
            logger.info(f"Chat rate OK: user={user_id}, daily_remaining={remaining}")

            return True, ""


# Singleton instance
chat_rate_limiter = ChatRateLimiter()
