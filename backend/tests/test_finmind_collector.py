"""Tests for FinMind data collector service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd

from app.services.finmind_collector import FinMindCollector, FINMIND_API


class TestFinMindCollectorInit:
    """Tests for FinMindCollector initialization."""

    def test_init_with_token(self):
        """Test collector initializes with token."""
        collector = FinMindCollector(token="test_token")
        assert collector.token == "test_token"


class TestFinMindCollectorGet:
    """Tests for _get method (HTTP API calls)."""

    @patch("app.services.finmind_collector.requests.get")
    def test_get_success(self, mock_get):
        """Test successful API response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [{"stock_id": "2330", "stock_name": "台積電"}]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector._get("TaiwanStockInfo")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["stock_id"] == "2330"

    @patch("app.services.finmind_collector.requests.get")
    def test_get_empty_response(self, mock_get):
        """Test empty API response returns empty DataFrame."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"msg": "success", "data": []}
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector._get("TaiwanStockInfo")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch("app.services.finmind_collector.requests.get")
    def test_get_api_error(self, mock_get):
        """Test API error returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector._get("TaiwanStockInfo")

        assert result is None

    @patch("app.services.finmind_collector.requests.get")
    @patch("app.services.finmind_collector.time.sleep")
    def test_get_rate_limited_retries(self, mock_sleep, mock_get):
        """Test 429 rate limit triggers retry with sleep."""
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429

        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_resp_ok.json.return_value = {
            "msg": "success",
            "data": [{"stock_id": "2330"}]
        }

        mock_get.side_effect = [mock_resp_429, mock_resp_ok]

        collector = FinMindCollector(token="test")
        result = collector._get("TaiwanStockInfo")

        assert isinstance(result, pd.DataFrame)
        mock_sleep.assert_called_once_with(60)

    @patch("app.services.finmind_collector.requests.get")
    def test_get_timeout_retries(self, mock_get):
        """Test timeout triggers retry."""
        import requests
        mock_get.side_effect = [
            requests.Timeout("timeout"),
            MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "msg": "success",
                    "data": [{"stock_id": "2330"}]
                })
            )
        ]

        collector = FinMindCollector(token="test")
        result = collector._get("TaiwanStockInfo")

        assert isinstance(result, pd.DataFrame)
        assert mock_get.call_count == 2

    @patch("app.services.finmind_collector.requests.get")
    def test_get_exception_returns_none(self, mock_get):
        """Test generic exception returns None."""
        mock_get.side_effect = ConnectionError("Connection refused")

        collector = FinMindCollector(token="test")
        result = collector._get("TaiwanStockInfo")

        assert result is None

    @patch("app.services.finmind_collector.requests.get")
    def test_get_removes_empty_params(self, mock_get):
        """Test empty params are removed from request."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"msg": "success", "data": []}
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test_token")
        collector._get("TaiwanStockInfo")

        call_kwargs = mock_get.call_args
        params = call_kwargs[1]["params"]
        assert "data_id" not in params
        assert "start_date" not in params
        assert params["token"] == "test_token"
        assert params["dataset"] == "TaiwanStockInfo"


class TestFetchStockList:
    """Tests for fetch_stock_list method with delisted stock filtering."""

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_filters_delisted(self, mock_get):
        """Test delisted stocks are filtered by date field."""
        today = pd.Timestamp.now()
        recent_date = (today - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
        old_date = (today - pd.Timedelta(days=60)).strftime("%Y-%m-%d")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [
                {"stock_id": "2330", "stock_name": "台積電", "date": recent_date},
                {"stock_id": "9999", "stock_name": "已下市公司", "date": old_date},
            ]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        assert len(result) == 1
        assert result[0]["stock_id"] == "2330"

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_all_active(self, mock_get):
        """Test all stocks pass when dates are recent."""
        today = pd.Timestamp.now()
        recent = (today - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [
                {"stock_id": "2330", "stock_name": "台積電", "date": recent},
                {"stock_id": "2454", "stock_name": "聯發科", "date": recent},
            ]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        assert len(result) == 2

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_no_date_column(self, mock_get):
        """Test graceful handling when date column missing."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [
                {"stock_id": "2330", "stock_name": "台積電"},
                {"stock_id": "2454", "stock_name": "聯發科"},
            ]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        # No date column => no filtering, all stocks returned
        assert len(result) == 2

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_empty_response(self, mock_get):
        """Test empty API response returns empty list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"msg": "success", "data": []}
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        assert result == []

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_none_response(self, mock_get):
        """Test None API response returns empty list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Error"
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        assert result == []

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_includes_optional_columns(self, mock_get):
        """Test optional columns (type, industry_category) are included."""
        today = pd.Timestamp.now().strftime("%Y-%m-%d")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [
                {
                    "stock_id": "2330",
                    "stock_name": "台積電",
                    "type": "stock",
                    "industry_category": "半導體",
                    "date": today,
                }
            ]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        assert len(result) == 1
        assert result[0]["type"] == "stock"
        assert result[0]["industry_category"] == "半導體"

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_boundary_date_29_days(self, mock_get):
        """Test stock at 29 days (within cutoff) is included."""
        safe_date = (pd.Timestamp.now() - pd.Timedelta(days=29)).strftime("%Y-%m-%d")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [
                {"stock_id": "2330", "stock_name": "台積電", "date": safe_date},
            ]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        assert len(result) == 1

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_stock_list_boundary_date_31_days(self, mock_get):
        """Test stock at 31-day (past cutoff) is excluded."""
        old_date = (pd.Timestamp.now() - pd.Timedelta(days=31)).strftime("%Y-%m-%d")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [
                {"stock_id": "9999", "stock_name": "已下市", "date": old_date},
            ]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_stock_list()

        assert len(result) == 0


class TestFetchDataMethods:
    """Tests for various fetch methods (daily prices, institutional, margin, etc.)."""

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_all_daily_prices(self, mock_get):
        """Test bulk daily price fetch."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [
                {"stock_id": "2330", "date": "2026-01-15", "close": 600}
            ]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_all_daily_prices("2026-01-01", "2026-01-31")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_daily_prices_single_stock(self, mock_get):
        """Test single stock price fetch passes data_id."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [{"date": "2026-01-15", "close": 600}]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        collector.fetch_daily_prices("2330", "2026-01-01", "2026-01-31")

        params = mock_get.call_args[1]["params"]
        assert params["data_id"] == "2330"

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_all_institutional(self, mock_get):
        """Test bulk institutional data fetch."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [{"stock_id": "2330", "buy": 1000}]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_all_institutional("2026-01-01", "2026-01-31")

        assert isinstance(result, pd.DataFrame)

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_all_margin(self, mock_get):
        """Test bulk margin trading data fetch."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [{"stock_id": "2330", "margin_buy": 500}]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_all_margin("2026-01-01", "2026-01-31")

        assert isinstance(result, pd.DataFrame)

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_revenue(self, mock_get):
        """Test revenue data fetch."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [{"stock_id": "2330", "revenue": 100000}]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_revenue("2330", "2026-01-01", "2026-01-31")

        assert isinstance(result, pd.DataFrame)

    @patch("app.services.finmind_collector.requests.get")
    def test_fetch_financial(self, mock_get):
        """Test financial statement data fetch."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "msg": "success",
            "data": [{"stock_id": "2330", "eps": 5.5}]
        }
        mock_get.return_value = mock_resp

        collector = FinMindCollector(token="test")
        result = collector.fetch_financial("2330", "2026-01-01", "2026-01-31")

        assert isinstance(result, pd.DataFrame)
