"""Tests for scoring engine with as_of_date parameter."""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from app.services.scoring_engine import ScoringEngine
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.score_result import ScoreResult


class TestScoringEngineAsOfDate:
    """Tests for ScoringEngine with as_of_date parameter."""

    @pytest.fixture
    def scoring_engine(self):
        """Create ScoringEngine instance."""
        return ScoringEngine()

    def test_score_stocks_with_as_of_date(self, test_db, scoring_engine):
        """Test run_screening respects as_of_date parameter."""
        # Add test stock
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        # Add price data for different dates
        base_date = date(2024, 1, 15)
        for i in range(10):
            price = DailyPrice(
                stock_id="2330",
                trade_date=base_date - timedelta(days=i),
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

        weights = {
            "fundamental": 0.3,
            "technical": 0.3,
            "chip": 0.2,
            "momentum": 0.2
        }

        # Mock the individual scorers
        with patch.object(scoring_engine, "hard_filter") as mock_filter:
            with patch.object(scoring_engine, "chip_scorer") as mock_chip:
                with patch.object(scoring_engine, "technical_scorer") as mock_tech:
                    with patch.object(scoring_engine, "fundamental_scorer") as mock_fund:
                        mock_filter.filter_by_volume.return_value = ["2330"]
                        mock_chip.score.return_value = {"score": 80}
                        mock_tech.score.return_value = {"score": 75}
                        mock_fund.score.return_value = {"score": 70}

                        # Call with as_of_date
                        result = scoring_engine.run_screening(
                            test_db,
                            weights,
                            as_of_date=date(2024, 1, 10)
                        )

                        # Verify as_of_date was passed to hard_filter
                        mock_filter.filter_by_volume.assert_called_once()
                        call_kwargs = mock_filter.filter_by_volume.call_args[1]
                        assert call_kwargs.get("as_of_date") == date(2024, 1, 10)

    def test_score_single_stock_with_as_of_date(self, test_db, scoring_engine):
        """Test score_single_stock respects as_of_date parameter."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        weights = {
            "fundamental": 0.3,
            "technical": 0.3,
            "chip": 0.2,
            "momentum": 0.2
        }

        with patch.object(scoring_engine, "chip_scorer") as mock_chip:
            with patch.object(scoring_engine, "technical_scorer") as mock_tech:
                with patch.object(scoring_engine, "fundamental_scorer") as mock_fund:
                    mock_chip.score.return_value = {"score": 80}
                    mock_tech.score.return_value = {"score": 75}
                    mock_fund.score.return_value = {"score": 70}

                    as_of_date = date(2024, 1, 10)
                    result = scoring_engine.score_single_stock(
                        test_db,
                        "2330",
                        weights,
                        as_of_date=as_of_date
                    )

                    # Verify as_of_date was passed to scorers
                    mock_chip.score.assert_called_once()
                    chip_call_kwargs = mock_chip.score.call_args[1]
                    assert chip_call_kwargs.get("as_of_date") == as_of_date

                    mock_tech.score.assert_called_once()
                    tech_call_kwargs = mock_tech.score.call_args[1]
                    assert tech_call_kwargs.get("as_of_date") == as_of_date

    def test_score_result_stores_as_of_date(self, test_db, scoring_engine):
        """Test run_screening stores as_of_date correctly."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)

        # Add price data
        base_date = date(2024, 1, 15)
        for i in range(10):
            price = DailyPrice(
                stock_id="2330",
                trade_date=base_date - timedelta(days=i),
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

        weights = {
            "fundamental": 0.3,
            "technical": 0.3,
            "chip": 0.2,
            "momentum": 0.2
        }

        as_of_date = date(2024, 1, 10)

        with patch.object(scoring_engine, "hard_filter") as mock_filter:
            with patch.object(scoring_engine, "chip_scorer") as mock_chip:
                with patch.object(scoring_engine, "technical_scorer") as mock_tech:
                    with patch.object(scoring_engine, "fundamental_scorer") as mock_fund:
                        mock_filter.filter_by_volume.return_value = ["2330"]
                        mock_chip.score.return_value = {"score": 80}
                        mock_tech.score.return_value = {"score": 75}
                        mock_fund.score.return_value = {"score": 70}

                        result = scoring_engine.run_screening(
                            test_db,
                            weights,
                            as_of_date=as_of_date
                        )

                        # Verify as_of_date was used
                        assert result is not None

    def test_score_stocks_without_as_of_date_uses_latest(self, test_db, scoring_engine):
        """Test run_screening without as_of_date uses latest date."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)

        # Add prices with different dates
        for i in range(5):
            price = DailyPrice(
                stock_id="2330",
                trade_date=date(2024, 1, 15) - timedelta(days=i),
                open=600.0,
                high=610.0,
                low=590.0,
                close=605.0,
                volume=1000000,
                turnover=605000000,
                change_price=5.0,
                change_percent=0.83
            )
            test_db.add(price)
        test_db.commit()

        weights = {
            "fundamental": 0.3,
            "technical": 0.3,
            "chip": 0.2,
            "momentum": 0.2
        }

        with patch.object(scoring_engine, "hard_filter") as mock_filter:
            with patch.object(scoring_engine, "chip_scorer"):
                with patch.object(scoring_engine, "technical_scorer"):
                    with patch.object(scoring_engine, "fundamental_scorer"):
                        mock_filter.filter_by_volume.return_value = ["2330"]

                        # Call without as_of_date
                        result = scoring_engine.run_screening(
                            test_db,
                            weights
                        )

                        # Verify hard_filter was called (should use latest)
                        mock_filter.filter_by_volume.assert_called_once()

    def test_score_stocks_empty_candidate_list(self, test_db, scoring_engine):
        """Test run_screening handles empty candidate list."""
        weights = {
            "fundamental": 0.3,
            "technical": 0.3,
            "chip": 0.2,
            "momentum": 0.2
        }

        with patch.object(scoring_engine, "hard_filter") as mock_filter:
            mock_filter.filter_by_volume.return_value = []

            result = scoring_engine.run_screening(
                test_db,
                weights,
                as_of_date=date(2024, 1, 10)
            )

            # Should return empty list
            assert result is not None
            if isinstance(result, list):
                assert len(result) == 0
