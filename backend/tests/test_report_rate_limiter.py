"""Tests for per-user daily report rate limiter."""
from datetime import date
from unittest.mock import patch

import pytest

from app.services.report_rate_limiter import ReportRateLimiter


class TestReportRateLimiter:
    """Unit tests for ReportRateLimiter."""

    def test_first_request_allowed(self):
        limiter = ReportRateLimiter()
        allowed, reason = limiter.check("user1", tier="free")
        assert allowed is True
        assert reason == ""

    def test_free_daily_limit(self):
        limiter = ReportRateLimiter()
        for _ in range(5):
            allowed, _ = limiter.check("user1", tier="free")
            assert allowed
        allowed, reason = limiter.check("user1", tier="free")
        assert allowed is False
        assert "5" in reason

    def test_premium_effectively_unlimited(self):
        limiter = ReportRateLimiter()
        for _ in range(20):
            allowed, _ = limiter.check("user2", tier="premium")
            assert allowed

    def test_daily_reset(self):
        limiter = ReportRateLimiter()
        # Exhaust free limit
        for _ in range(5):
            limiter.check("user1", tier="free")
        # Simulate next day
        limiter._daily_log["user1"] = {"date": date(2026, 2, 20), "count": 5}
        with patch("app.services.report_rate_limiter.date") as mock_date:
            mock_date.today.return_value = date(2026, 2, 21)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            allowed, _ = limiter.check("user1", tier="free")
            assert allowed is True

    def test_users_independent(self):
        limiter = ReportRateLimiter()
        for _ in range(5):
            limiter.check("user1", tier="free")
        allowed, _ = limiter.check("user2", tier="free")
        assert allowed is True

    def test_default_tier_is_free(self):
        limiter = ReportRateLimiter()
        for _ in range(5):
            limiter.check("user1")
        allowed, _ = limiter.check("user1")
        assert allowed is False
