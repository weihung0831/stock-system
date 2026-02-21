"""Tests for require_premium dependency."""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.dependencies import require_premium


class TestRequirePremium:
    """Tests for require_premium dependency function."""

    def test_allows_premium_user(self):
        user = MagicMock()
        user.membership_tier = "premium"
        user.is_admin = False
        result = require_premium(user)
        assert result == user

    def test_allows_admin_user(self):
        user = MagicMock()
        user.membership_tier = "free"
        user.is_admin = True
        result = require_premium(user)
        assert result == user

    def test_blocks_free_user(self):
        user = MagicMock()
        user.membership_tier = "free"
        user.is_admin = False
        with pytest.raises(HTTPException) as exc_info:
            require_premium(user)
        assert exc_info.value.status_code == 403
        assert "Premium" in exc_info.value.detail
