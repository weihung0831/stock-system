"""Tests for per-user tier-aware chat rate limiter."""
import time
from datetime import date
from unittest.mock import patch

import pytest

from app.services.chat_rate_limiter import ChatRateLimiter, CHAT_TIER_LIMITS


class TestChatRateLimiter:
    """Unit tests for ChatRateLimiter with tier awareness."""

    def test_first_request_allowed(self):
        limiter = ChatRateLimiter()
        allowed, reason, quota = limiter.check("user1")
        assert allowed is True
        assert reason == ""
        assert "daily_remaining" in quota

    def test_free_per_minute_limit_blocks(self):
        limiter = ChatRateLimiter()
        for _ in range(3):
            limiter.check("user1", tier="free")
        allowed, reason, _ = limiter.check("user1", tier="free")
        assert allowed is False
        assert "秒" in reason

    def test_per_minute_resets_after_window(self):
        limiter = ChatRateLimiter()
        limiter.check("user1", tier="free")
        limiter.check("user1", tier="free")
        limiter.check("user1", tier="free")
        # Manually expire timestamps
        limiter._minute_log["user1"] = [time.time() - 61]
        allowed, _, _ = limiter.check("user1", tier="free")
        assert allowed is True

    def test_free_daily_limit_blocks(self):
        limiter = ChatRateLimiter()
        # Bypass minute limit by spacing requests across time windows
        for i in range(10):
            limiter._minute_log["user1"] = []  # reset minute window
            limiter.check("user1", tier="free")
        limiter._minute_log["user1"] = []  # reset for final check
        allowed, reason, quota = limiter.check("user1", tier="free")
        assert allowed is False
        assert "每日上限" in reason
        assert "10" in reason
        assert quota["daily_remaining"] == 0

    def test_premium_daily_limit_higher(self):
        limiter = ChatRateLimiter()
        # After 10 requests, premium should still be allowed
        for _ in range(10):
            limiter._minute_log["user2"] = []  # reset minute window
            allowed, _, _ = limiter.check("user2", tier="premium")
            assert allowed
        limiter._minute_log["user2"] = []
        allowed, _, _ = limiter.check("user2", tier="premium")
        assert allowed is True

    def test_premium_per_minute_limit(self):
        limiter = ChatRateLimiter()
        for _ in range(5):
            limiter.check("user3", tier="premium")
        allowed, reason, _ = limiter.check("user3", tier="premium")
        assert allowed is False
        assert "秒" in reason

    def test_daily_resets_on_new_day(self):
        limiter = ChatRateLimiter()
        limiter.check("user1", tier="free")
        yesterday = date(2026, 2, 20)
        limiter._daily_log["user1"] = {"date": yesterday, "count": 999}
        with patch("app.services.chat_rate_limiter.date") as mock_date:
            mock_date.today.return_value = date(2026, 2, 21)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            allowed, _, _ = limiter.check("user1", tier="free")
            assert allowed is True

    def test_users_are_independent(self):
        limiter = ChatRateLimiter()
        for _ in range(3):
            limiter.check("user1", tier="free")
        # user1 minute-limited, but user2 should be fine
        allowed, _, _ = limiter.check("user2", tier="free")
        assert allowed is True

    def test_daily_remaining_decrements(self):
        limiter = ChatRateLimiter()
        _, _, quota = limiter.check("user4", tier="free")
        assert quota["daily_remaining"] == 9  # 10 - 1

    def test_quota_info_returned(self):
        limiter = ChatRateLimiter()
        _, _, quota = limiter.check("user5", tier="free")
        assert "daily_remaining" in quota
        assert "minute_remaining" in quota
        assert quota["daily_remaining"] == 9

    def test_default_tier_is_free(self):
        limiter = ChatRateLimiter()
        # No tier param should default to free limits
        for _ in range(3):
            limiter.check("user6")
        allowed, _, _ = limiter.check("user6")
        assert allowed is False  # free minute limit is 3

    def test_unknown_tier_falls_back_to_free(self):
        limiter = ChatRateLimiter()
        for _ in range(3):
            limiter.check("user7", tier="gold")
        allowed, _, _ = limiter.check("user7", tier="gold")
        assert allowed is False


class TestChatRateLimiterQuota:
    """Tests for read-only quota check."""

    def test_check_quota_no_usage(self):
        limiter = ChatRateLimiter()
        quota = limiter.check_quota("new_user", tier="free")
        assert quota["daily_limit"] == 10
        assert quota["daily_used"] == 0
        assert quota["daily_remaining"] == 10
        assert quota["minute_limit"] == 3

    def test_check_quota_after_usage(self):
        limiter = ChatRateLimiter()
        limiter.check("user1", tier="free")
        limiter.check("user1", tier="free")
        quota = limiter.check_quota("user1", tier="free")
        assert quota["daily_used"] == 2
        assert quota["daily_remaining"] == 8

    def test_check_quota_premium(self):
        limiter = ChatRateLimiter()
        quota = limiter.check_quota("user1", tier="premium")
        assert quota["daily_limit"] == 100
        assert quota["minute_limit"] == 5

    def test_check_quota_does_not_increment(self):
        limiter = ChatRateLimiter()
        limiter.check_quota("user1", tier="free")
        limiter.check_quota("user1", tier="free")
        quota = limiter.check_quota("user1", tier="free")
        assert quota["daily_used"] == 0
