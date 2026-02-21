"""Tests for per-user chat rate limiter."""
import time
from datetime import date
from unittest.mock import patch

import pytest

from app.services.chat_rate_limiter import ChatRateLimiter


class TestChatRateLimiter:
    """Unit tests for ChatRateLimiter."""

    def test_first_request_allowed(self):
        limiter = ChatRateLimiter(per_minute=3, per_day=20)
        allowed, reason = limiter.check("user1")
        assert allowed is True
        assert reason == ""

    def test_per_minute_limit_blocks(self):
        limiter = ChatRateLimiter(per_minute=2, per_day=100)
        limiter.check("user1")
        limiter.check("user1")
        allowed, reason = limiter.check("user1")
        assert allowed is False
        assert "秒" in reason

    def test_per_minute_resets_after_window(self):
        limiter = ChatRateLimiter(per_minute=1, per_day=100)
        limiter.check("user1")
        # Manually expire the timestamp
        limiter._minute_log["user1"] = [time.time() - 61]
        allowed, _ = limiter.check("user1")
        assert allowed is True

    def test_daily_limit_blocks(self):
        limiter = ChatRateLimiter(per_minute=100, per_day=3)
        for _ in range(3):
            limiter.check("user1")
        allowed, reason = limiter.check("user1")
        assert allowed is False
        assert "每日上限" in reason

    def test_daily_resets_on_new_day(self):
        limiter = ChatRateLimiter(per_minute=100, per_day=1)
        limiter.check("user1")
        # Simulate yesterday's log
        yesterday = date(2026, 2, 20)
        limiter._daily_log["user1"] = {"date": yesterday, "count": 999}
        with patch("app.services.chat_rate_limiter.date") as mock_date:
            mock_date.today.return_value = date(2026, 2, 21)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            allowed, _ = limiter.check("user1")
            assert allowed is True

    def test_users_are_independent(self):
        limiter = ChatRateLimiter(per_minute=1, per_day=100)
        limiter.check("user1")
        allowed, _ = limiter.check("user2")
        assert allowed is True

    def test_daily_remaining_decrements(self):
        limiter = ChatRateLimiter(per_minute=100, per_day=5)
        for _ in range(4):
            limiter.check("user1")
        assert limiter._daily_log["user1"]["count"] == 4
