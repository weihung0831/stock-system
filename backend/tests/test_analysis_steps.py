"""Tests for pipeline analysis steps."""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from app.tasks.analysis_steps import step_hard_filter
from app.models.stock import Stock
from app.models.daily_price import DailyPrice


class TestStepHardFilter:
    """Tests for step_hard_filter function."""

    def test_hard_filter_success(self, test_db):
        """Test step_hard_filter returns candidates on success."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        today = date.today()
        price = DailyPrice(
            stock_id="2330", trade_date=today,
            open=600, high=610, low=590, close=605, volume=1000000,
        )
        test_db.add(price)
        test_db.commit()

        result = step_hard_filter(test_db, today.isoformat())

        assert result["success"] is True
        assert "2330" in result["candidates"]

    def test_hard_filter_empty_db(self, test_db):
        """Test step_hard_filter handles empty database."""
        result = step_hard_filter(test_db, "2026-02-15")

        assert result["success"] is True
        assert result["candidates"] == []

    def test_hard_filter_error_handling(self, test_db):
        """Test step_hard_filter handles exceptions gracefully."""
        with patch("app.tasks.analysis_steps.DailyPrice") as mock_dp:
            mock_dp.trade_date = None
            # Force an error by making the query fail
            result = step_hard_filter(None, "2026-02-15")

        assert result["success"] is False
        assert result["candidates"] == []
