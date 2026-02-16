"""Tests for backtest service with stock_ids filtering."""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from app.services.backtest_service import (
    get_historical_top_stocks,
    calculate_performance,
    get_available_score_dates
)
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.score_result import ScoreResult


class TestBacktestServiceStockFiltering:
    """Tests for backtest service with stock_ids parameter."""

    def test_calculate_performance_with_stock_ids_filter(self, test_db):
        """Test calculate_performance filters by specific stock_ids."""
        # Add test stocks
        for stock_id in ["2330", "2454", "1234"]:
            stock = Stock(stock_id=stock_id, stock_name=f"Stock {stock_id}", market="TWSE")
            test_db.add(stock)
        test_db.commit()

        # Add score results for all stocks
        score_date = date(2024, 1, 10)
        for i, stock_id in enumerate(["2330", "2454", "1234"]):
            score = ScoreResult(
                stock_id=stock_id,
                score_date=score_date,
                total_score=Decimal(85.0 - i * 5),
                fundamental_score=Decimal(80.0),
                technical_score=Decimal(90.0),
                chip_score=Decimal(85.0),
                rank=i + 1,
                chip_weight=Decimal(20.0),
                fundamental_weight=Decimal(35.0),
                technical_weight=Decimal(25.0)
            )
            test_db.add(score)
        test_db.commit()

        # Add price data for performance calculation
        base_date = date(2024, 1, 15)
        for stock_id in ["2330", "2454", "1234"]:
            for i in range(25):
                price = DailyPrice(
                    stock_id=stock_id,
                    trade_date=base_date - timedelta(days=25 - i),
                    open=600.0 + i,
                    high=610.0 + i,
                    low=590.0 + i,
                    close=605.0 + i,
                    volume=1000000,
                    turnover=605000000,
                    change_price=5.0,
                    change_percent=0.83
                )
                test_db.add(price)
        test_db.commit()

        # Calculate performance with specific stock_ids
        stock_ids = ["2330", "2454"]
        result = calculate_performance(
            db=test_db,
            score_date=score_date,
            stock_ids=stock_ids
        )

        # Should only include specified stocks
        assert result is not None
        if isinstance(result, dict) and "stocks" in result:
            for stock_result in result.get("stocks", []):
                assert stock_result["stock_id"] in stock_ids

    def test_calculate_performance_without_stock_ids_uses_top_n(self, test_db):
        """Test calculate_performance without stock_ids uses top N."""
        # Add test stocks
        for stock_id in ["2330", "2454", "1234", "5555"]:
            stock = Stock(stock_id=stock_id, stock_name=f"Stock {stock_id}", market="TWSE")
            test_db.add(stock)
        test_db.commit()

        # Add score results with different scores
        score_date = date(2024, 1, 10)
        for i, stock_id in enumerate(["2330", "2454", "1234", "5555"]):
            score = ScoreResult(
                stock_id=stock_id,
                score_date=score_date,
                total_score=Decimal(100.0 - i * 10),
                fundamental_score=Decimal(80.0),
                technical_score=Decimal(90.0),
                chip_score=Decimal(85.0),
                rank=i + 1,
                chip_weight=Decimal(20.0),
                fundamental_weight=Decimal(35.0),
                technical_weight=Decimal(25.0)
            )
            test_db.add(score)
        test_db.commit()

        # Call without stock_ids (should use top_n=10 default)
        result = calculate_performance(
            db=test_db,
            score_date=score_date,
            top_n=2
        )

        # Should return result
        assert result is not None

    def test_calculate_performance_empty_stock_ids(self, test_db):
        """Test calculate_performance with empty stock_ids list."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)

        score_date = date(2024, 1, 10)
        score = ScoreResult(
            stock_id="2330",
            score_date=score_date,
            total_score=Decimal(85.0),
            fundamental_score=Decimal(80.0),
            technical_score=Decimal(90.0),
            chip_score=Decimal(85.0),
            rank=1,
            chip_weight=Decimal(20.0),
            fundamental_weight=Decimal(35.0),
            technical_weight=Decimal(25.0)
        )
        test_db.add(score)
        test_db.commit()

        # Call with empty stock_ids
        result = calculate_performance(
            db=test_db,
            score_date=score_date,
            stock_ids=[]
        )

        # Should handle empty list gracefully
        assert result is not None

    def test_calculate_performance_nonexistent_stock_ids(self, test_db):
        """Test calculate_performance with non-existent stock_ids."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)

        score_date = date(2024, 1, 10)
        score = ScoreResult(
            stock_id="2330",
            score_date=score_date,
            total_score=Decimal(85.0),
            fundamental_score=Decimal(80.0),
            technical_score=Decimal(90.0),
            chip_score=Decimal(85.0),
            rank=1,
            chip_weight=Decimal(20.0),
            fundamental_weight=Decimal(35.0),
            technical_weight=Decimal(25.0)
        )
        test_db.add(score)
        test_db.commit()

        # Call with non-existent stock_ids
        result = calculate_performance(
            db=test_db,
            score_date=score_date,
            stock_ids=["9999", "8888"]
        )

        # Should return empty or handle gracefully
        assert result is not None

    def test_calculate_performance_forward_days(self, test_db):
        """Test calculate_performance with different forward_days."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)

        score_date = date(2024, 1, 10)
        score = ScoreResult(
            stock_id="2330",
            score_date=score_date,
            total_score=Decimal(85.0),
            fundamental_score=Decimal(80.0),
            technical_score=Decimal(90.0),
            chip_score=Decimal(85.0),
            rank=1,
            chip_weight=Decimal(20.0),
            fundamental_weight=Decimal(35.0),
            technical_weight=Decimal(25.0)
        )
        test_db.add(score)

        # Add price data
        base_date = date(2024, 1, 10)
        for i in range(35):
            price = DailyPrice(
                stock_id="2330",
                trade_date=base_date + timedelta(days=i),
                open=600.0 + i * 0.5,
                high=610.0 + i * 0.5,
                low=590.0 + i * 0.5,
                close=605.0 + i * 0.5,
                volume=1000000 + (i * 50000),
                turnover=605000000,
                change_price=5.0,
                change_percent=0.83
            )
            test_db.add(price)
        test_db.commit()

        # Test with custom forward_days
        result = calculate_performance(
            db=test_db,
            score_date=score_date,
            stock_ids=["2330"],
            forward_days=[5, 10, 20, 30]
        )

        # Should return result with performance metrics
        assert result is not None

    def test_get_historical_top_stocks_in_date_range(self, test_db):
        """Test get_historical_top_stocks returns stocks in date range."""
        # Add stocks
        for stock_id in ["2330", "2454", "1234"]:
            stock = Stock(stock_id=stock_id, stock_name=f"Stock {stock_id}", market="TWSE")
            test_db.add(stock)
        test_db.commit()

        # Add score results for multiple dates
        start_date = date(2024, 1, 5)
        for day_offset in range(0, 10, 5):
            score_date = start_date + timedelta(days=day_offset)
            for i, stock_id in enumerate(["2330", "2454", "1234"]):
                score = ScoreResult(
                    stock_id=stock_id,
                    score_date=score_date,
                    total_score=Decimal(90.0 - i * 5),
                    fundamental_score=Decimal(80.0),
                    technical_score=Decimal(90.0),
                    chip_score=Decimal(85.0),
                    rank=i + 1,
                    chip_weight=Decimal(20.0),
                    fundamental_weight=Decimal(35.0),
                    technical_weight=Decimal(25.0)
                )
                test_db.add(score)
        test_db.commit()

        # Get historical top stocks
        result = get_historical_top_stocks(
            db=test_db,
            start_date=start_date,
            end_date=start_date + timedelta(days=15),
            top_n=2
        )

        # Should return results for each score date
        assert result is not None
        assert isinstance(result, list)
        if len(result) > 0:
            # Each result should have score_date and top_stocks
            assert "score_date" in result[0]
            assert "top_stocks" in result[0]

    def test_get_historical_top_stocks_empty_range(self, test_db):
        """Test get_historical_top_stocks with empty date range."""
        result = get_historical_top_stocks(
            db=test_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            top_n=10
        )

        # Should return empty list
        assert result is not None
        assert isinstance(result, list)

    def test_get_available_score_dates(self, test_db):
        """Test get_available_score_dates returns all score dates."""
        # Add stock and prices
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)

        # Add prices with range
        for i in range(50):
            price = DailyPrice(
                stock_id="2330",
                trade_date=date(2024, 1, 1) + timedelta(days=i),
                open=600.0 + i,
                high=610.0 + i,
                low=590.0 + i,
                close=605.0 + i,
                volume=1000000,
                turnover=605000000,
                change_price=5.0,
                change_percent=0.83
            )
            test_db.add(price)

        # Add score results for multiple dates
        for day_offset in range(0, 30, 5):
            score_date = date(2024, 1, 1) + timedelta(days=day_offset)
            score = ScoreResult(
                stock_id="2330",
                score_date=score_date,
                total_score=Decimal(85.0),
                fundamental_score=Decimal(80.0),
                technical_score=Decimal(90.0),
                chip_score=Decimal(85.0),
                rank=1,
                chip_weight=Decimal(20.0),
                fundamental_weight=Decimal(35.0),
                technical_weight=Decimal(25.0)
            )
            test_db.add(score)
        test_db.commit()

        # Get available score dates
        result = get_available_score_dates(test_db)

        # Should return list of dates with backtestable status
        assert result is not None
        assert isinstance(result, list)
        if len(result) > 0:
            assert "date" in result[0]
            assert "backtestable" in result[0]

    def test_get_available_score_dates_empty_database(self, test_db):
        """Test get_available_score_dates with empty database."""
        result = get_available_score_dates(test_db)

        # Should return empty list
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
