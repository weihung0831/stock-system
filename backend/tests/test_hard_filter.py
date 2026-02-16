"""Tests for hard threshold filtering service."""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.services.hard_filter import HardFilter
from app.models.stock import Stock
from app.models.daily_price import DailyPrice


class TestHardFilter:
    """Tests for HardFilter class."""

    @pytest.fixture
    def hard_filter(self):
        """Create HardFilter instance."""
        return HardFilter()

    def test_filter_by_volume_empty_database(self, test_db, hard_filter):
        """Test volume filter with empty database."""
        result = hard_filter.filter_by_volume(test_db)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_filter_by_volume_no_last_week_data(self, test_db, hard_filter):
        """Test volume filter when last week has no data."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        # Add data only for this week
        today = date.today()
        current_weekday = today.weekday()
        this_week_start = today - timedelta(days=current_weekday)

        for i in range(5):
            date_val = this_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000
            )
            test_db.add(price)
        test_db.commit()

        result = hard_filter.filter_by_volume(test_db)

        # No ratio match, but included via top-N fallback
        assert stock.stock_id in result

    def test_filter_by_volume_volume_spike(self, test_db, hard_filter):
        """Test volume filter passes when this week >> last week."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        today = date.today()
        current_weekday = today.weekday()
        this_week_start = today - timedelta(days=current_weekday)
        last_week_start = this_week_start - timedelta(days=7)

        # Last week: low volume (1M per day = 5M total)
        for i in range(5):
            date_val = last_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000  # 1M
            )
            test_db.add(price)

        # This week: high volume (5M per day = 25M total)
        for i in range(5):
            date_val = this_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=5000000  # 5M
            )
            test_db.add(price)

        test_db.commit()

        # 25M / 5M = 5x > 2.5x threshold
        result = hard_filter.filter_by_volume(test_db, threshold=2.5)

        assert stock.stock_id in result

    def test_filter_by_volume_no_spike(self, test_db, hard_filter):
        """Test volume filter fails when volume is stable."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        today = date.today()
        current_weekday = today.weekday()
        this_week_start = today - timedelta(days=current_weekday)
        last_week_start = this_week_start - timedelta(days=7)

        volume = 1000000

        # Last week: consistent volume
        for i in range(5):
            date_val = last_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=volume
            )
            test_db.add(price)

        # This week: same volume
        for i in range(5):
            date_val = this_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=volume
            )
            test_db.add(price)

        test_db.commit()

        result = hard_filter.filter_by_volume(test_db, threshold=2.5)

        # Ratio 1.0 < 2.5: no ratio match, but included via top-N fallback
        assert stock.stock_id in result

    def test_filter_by_volume_custom_threshold(self, test_db, hard_filter):
        """Test volume filter with custom threshold."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        today = date.today()
        current_weekday = today.weekday()
        this_week_start = today - timedelta(days=current_weekday)
        last_week_start = this_week_start - timedelta(days=7)

        # Last week: 5M total
        for i in range(5):
            date_val = last_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000
            )
            test_db.add(price)

        # This week: 10M total
        for i in range(5):
            date_val = this_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=2000000
            )
            test_db.add(price)

        test_db.commit()

        # 10M / 5M = 2.0
        # Ratio 2.0 < 2.5: no ratio match, but included via top-N fallback
        result_high = hard_filter.filter_by_volume(test_db, threshold=2.5)
        assert stock.stock_id in result_high

        # Ratio 2.0 > 1.5: passes ratio filter directly
        result_low = hard_filter.filter_by_volume(test_db, threshold=1.5)
        assert stock.stock_id in result_low

    def test_filter_by_volume_multiple_stocks(self, test_db, hard_filter):
        """Test volume filter with multiple stocks."""
        stock1 = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        stock2 = Stock(stock_id="2454", stock_name="聯發科", market="TWSE")
        stock3 = Stock(stock_id="3008", stock_name="聯德", market="TWSE")
        test_db.add_all([stock1, stock2, stock3])
        test_db.commit()

        today = date.today()
        current_weekday = today.weekday()
        this_week_start = today - timedelta(days=current_weekday)
        last_week_start = this_week_start - timedelta(days=7)

        # Stock 1: Volume spike (5x)
        for i in range(5):
            date_val = last_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id="2330",
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000
            )
            test_db.add(price)

        for i in range(5):
            date_val = this_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id="2330",
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=5000000
            )
            test_db.add(price)

        # Stock 2: No volume spike
        for i in range(5):
            date_val = last_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id="2454",
                trade_date=date_val,
                open=100,
                high=105,
                low=95,
                close=102,
                volume=100000
            )
            test_db.add(price)

        for i in range(5):
            date_val = this_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id="2454",
                trade_date=date_val,
                open=100,
                high=105,
                low=95,
                close=102,
                volume=100000
            )
            test_db.add(price)

        test_db.commit()

        result = hard_filter.filter_by_volume(test_db, threshold=2.5)

        assert "2330" in result  # Passes ratio filter (first in list)
        assert "2454" in result  # Included via top-N fallback
        assert "3008" not in result  # No price data at all

    def test_filter_by_volume_zero_volume_handling(self, test_db, hard_filter):
        """Test volume filter handles zero volume in last week."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        today = date.today()
        current_weekday = today.weekday()
        this_week_start = today - timedelta(days=current_weekday)

        # This week: has volume
        for i in range(5):
            date_val = this_week_start + timedelta(days=i)
            price = DailyPrice(
                stock_id=stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000
            )
            test_db.add(price)

        test_db.commit()

        # No ratio match (no prev week), but included via top-N fallback
        result = hard_filter.filter_by_volume(test_db, threshold=2.5)

        assert stock.stock_id in result

    def test_filter_by_volume_error_handling(self, test_db, hard_filter):
        """Test volume filter handles errors gracefully."""
        # Simulate an error by using invalid database
        invalid_db = None

        result = hard_filter.filter_by_volume(invalid_db)

        # Should return empty list instead of raising
        assert isinstance(result, list)
        assert len(result) == 0
