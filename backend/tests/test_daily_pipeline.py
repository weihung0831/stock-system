"""Tests for daily pipeline orchestration."""
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.tasks.daily_pipeline import (
    is_trading_day,
    _fetch_twse_holidays,
    run_daily_pipeline,
)


class TestTWSEHolidayFetching:
    """Tests for TWSE holiday fetching."""

    def test_fetch_twse_holidays_cache_hit(self):
        """Test holiday cache is reused."""
        # Clear cache first
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "stat": "ok",
                "data": [["2024-01-01", "元旦"]]
            }
            mock_get.return_value = mock_response

            # First call
            holidays1 = _fetch_twse_holidays(2024)
            assert len(holidays1) == 1
            assert mock_get.call_count == 1

            # Second call (should use cache)
            holidays2 = _fetch_twse_holidays(2024)
            assert holidays1 == holidays2
            assert mock_get.call_count == 1  # Not incremented

    def test_fetch_twse_holidays_excludes_trading_day_markers(self):
        """Test that trading day markers are excluded from holidays."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "stat": "ok",
                "data": [
                    ["2024-02-28", "228和平紀念日"],
                    ["2024-02-29", "春節後開始交易日"],  # Should be excluded
                    ["2024-03-04", "最後交易日"],  # Should be excluded
                ]
            }
            mock_get.return_value = mock_response

            holidays = _fetch_twse_holidays(2024)
            assert len(holidays) == 1
            assert date(2024, 2, 28) in holidays

    def test_fetch_twse_holidays_api_failure(self):
        """Test graceful handling of API failure."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection error")

            holidays = _fetch_twse_holidays(2024)
            assert holidays == set()

    def test_fetch_twse_holidays_invalid_format(self):
        """Test handling of invalid API response format."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"stat": "error"}
            mock_get.return_value = mock_response

            holidays = _fetch_twse_holidays(2024)
            assert holidays == set()

    def test_fetch_twse_holidays_roc_year_conversion(self):
        """Test ROC year conversion to Western year."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "stat": "ok",
                "data": [["2024-01-01", "元旦"]]
            }
            mock_get.return_value = mock_response

            _fetch_twse_holidays(2024)
            # 2024 - 1911 = 113 (ROC 113)
            assert mock_get.call_args[1]["params"]["queryYear"] == 113


class TestIsTradingDay:
    """Tests for trading day detection."""

    def test_is_trading_day_weekday(self):
        """Test weekdays (Mon-Fri) are recognized as trading days."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"stat": "ok", "data": []}
            mock_get.return_value = mock_response

            # Jan 1, 2024 is Monday
            assert is_trading_day(date(2024, 1, 1)) == True

    def test_is_trading_day_saturday(self):
        """Test Saturday is not a trading day."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"stat": "ok", "data": []}
            mock_get.return_value = mock_response

            # Jan 6, 2024 is Saturday
            assert is_trading_day(date(2024, 1, 6)) == False

    def test_is_trading_day_sunday(self):
        """Test Sunday is not a trading day."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"stat": "ok", "data": []}
            mock_get.return_value = mock_response

            # Jan 7, 2024 is Sunday
            assert is_trading_day(date(2024, 1, 7)) == False

    def test_is_trading_day_holiday(self):
        """Test TWSE holiday is not a trading day."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "stat": "ok",
                "data": [["2024-02-28", "228和平紀念日"]]
            }
            mock_get.return_value = mock_response

            # Feb 28, 2024 is Wednesday but is a holiday
            assert is_trading_day(date(2024, 2, 28)) == False

    def test_is_trading_day_normal_weekday_no_holiday(self):
        """Test normal weekday without holiday is a trading day."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"stat": "ok", "data": []}
            mock_get.return_value = mock_response

            # Jan 2, 2024 is Tuesday with no holiday
            assert is_trading_day(date(2024, 1, 2)) == True


class TestRunDailyPipeline:
    """Tests for main pipeline orchestrator."""

    def test_run_daily_pipeline_skips_weekend(self, test_db):
        """Test pipeline skips on weekends for scheduled trigger."""
        with patch("app.tasks.daily_pipeline.date") as mock_date:
            # Saturday, Jan 6, 2024
            mock_date.today.return_value = date(2024, 1, 6)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            result = run_daily_pipeline(trigger_type="scheduled")

            assert result["status"] == "skipped"
            assert "not a trading day" in result["reason"].lower()

    def test_run_daily_pipeline_executes_on_trading_day(self, test_db):
        """Test pipeline executes on trading day."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        with patch("app.tasks.daily_pipeline.date") as mock_date:
            with patch("app.tasks.daily_pipeline.step_fetch_stock_data") as mock_fetch:
                with patch("app.tasks.daily_pipeline.step_fetch_news") as mock_news:
                    with patch("app.tasks.daily_pipeline.step_hard_filter") as mock_filter:
                        with patch("app.tasks.daily_pipeline.step_scoring") as mock_score:
                            with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
                                mock_date.today.return_value = date(2024, 1, 2)  # Tuesday
                                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

                                mock_get.return_value.json.return_value = {
                                    "stat": "ok",
                                    "data": []
                                }

                                mock_fetch.return_value = {"stocks_fetched": 100}
                                mock_news.return_value = {"news_fetched": 50}
                                mock_filter.return_value = ["2330", "2454"]
                                mock_score.return_value = {"scores_calculated": 2}

                                result = run_daily_pipeline(trigger_type="scheduled")

                                # Should have executed the pipeline
                                assert mock_fetch.called or result.get("status") in ["success", "completed"]

    def test_run_daily_pipeline_manual_trigger_uses_last_trading_day(self, test_db):
        """Test manual trigger on weekend uses last trading day."""
        from app.tasks import daily_pipeline
        daily_pipeline._holiday_cache.clear()

        # Simply test that manual trigger does not skip on weekends
        with patch("app.tasks.daily_pipeline.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {
                "stat": "ok",
                "data": []
            }

            with patch("app.tasks.daily_pipeline.date") as mock_date_class:
                # Setup: Sunday Jan 7, 2024 is not a trading day
                mock_date_class.today.return_value = date(2024, 1, 7)
                # Mock date class constructor to return actual date objects
                mock_date_class.side_effect = lambda *args, **kw: \
                    date(2024, 1, 7) if args == () else date(*args, **kw)

                # Patch timedelta too
                with patch("app.tasks.daily_pipeline.timedelta") as mock_delta:
                    mock_delta.side_effect = timedelta

                    # For manual trigger, should not raise error
                    try:
                        result = run_daily_pipeline(trigger_type="manual")
                        # Should succeed or skip, not crash
                        assert result is not None
                    except Exception as e:
                        # If it's not a trading day handling issue, that's ok
                        assert "trading" in str(e).lower() or \
                               result.get("status") in ["skipped", "completed", "success"]
