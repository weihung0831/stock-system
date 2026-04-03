"""動能篩選器單元測試。"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
import pytest

from app.services.momentum.filters import (
    initial_filter,
    trend_filter,
    relative_strength_filter,
    run_all_filters,
)


def _make_df(closes: List[float], volumes: Optional[List[int]] = None) -> pd.DataFrame:
    """建立模擬 OHLCV DataFrame。"""
    n = len(closes)
    if volumes is None:
        volumes = [5000] * n
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=n),
        "Open": closes,
        "High": [c + 1 for c in closes],
        "Low": [c - 1 for c in closes],
        "Close": closes,
        "Volume": volumes,
    })


def _make_uptrend_df(n: int = 80, base: float = 50.0) -> pd.DataFrame:
    """建立穩定上升趨勢的 DataFrame，確保 MA20 > MA60。"""
    closes = [base + i * 0.5 for i in range(n)]
    return _make_df(closes)


def _make_downtrend_df(n: int = 80, base: float = 100.0) -> pd.DataFrame:
    """建立穩定下降趨勢的 DataFrame，確保 MA20 < MA60。"""
    closes = [base - i * 0.5 for i in range(n)]
    return _make_df(closes)


# ── initial_filter ──


class TestInitialFilter:
    def test_pass(self):
        data = {"2330": _make_df([25.0], [2000])}
        assert "2330" in initial_filter(data)

    def test_price_boundary_fail(self):
        """price=19.99 應被過濾。"""
        data = {"2330": _make_df([19.99], [2000])}
        assert initial_filter(data) == {}

    def test_price_exact_boundary(self):
        """price=20 不通過（條件為 > 20）。"""
        data = {"2330": _make_df([20.0], [2000])}
        assert initial_filter(data) == {}

    def test_volume_boundary_fail(self):
        """volume=999 應被過濾。"""
        data = {"2330": _make_df([25.0], [999])}
        assert initial_filter(data) == {}

    def test_volume_exact_boundary(self):
        """volume=1000 不通過（條件為 > 1000）。"""
        data = {"2330": _make_df([25.0], [1000])}
        assert initial_filter(data) == {}

    def test_empty_input(self):
        assert initial_filter({}) == {}

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        assert initial_filter({"2330": empty_df}) == {}


# ── trend_filter ──


class TestTrendFilter:
    def test_uptrend_pass(self):
        data = {"2330": _make_uptrend_df()}
        assert "2330" in trend_filter(data)

    def test_downtrend_fail(self):
        data = {"2330": _make_downtrend_df()}
        assert trend_filter(data) == {}

    def test_insufficient_data(self):
        """資料不足 60 根應被過濾。"""
        data = {"2330": _make_df([50.0] * 30)}
        assert trend_filter(data) == {}

    def test_empty_input(self):
        assert trend_filter({}) == {}


# ── relative_strength_filter ──


class TestRelativeStrengthFilter:
    def test_stronger_than_market(self):
        """個股漲幅大於大盤。"""
        stock_closes = [100.0] * 10 + [120.0]
        market_closes = [100.0] * 10 + [105.0]
        data = {"2330": _make_df(stock_closes)}
        market = _make_df(market_closes)
        assert "2330" in relative_strength_filter(data, market)

    def test_weaker_than_market(self):
        """個股漲幅小於大盤。"""
        stock_closes = [100.0] * 10 + [102.0]
        market_closes = [100.0] * 10 + [110.0]
        data = {"2330": _make_df(stock_closes)}
        market = _make_df(market_closes)
        assert relative_strength_filter(data, market) == {}

    def test_empty_input(self):
        market = _make_df([100.0] * 11)
        assert relative_strength_filter({}, market) == {}


# ── run_all_filters ──


class TestRunAllFilters:
    def test_all_pass(self):
        """符合所有條件的股票應通過。"""
        stock_closes = [50.0 + i * 0.5 for i in range(80)]
        # 最後一根改高一點確保相對強度
        stock_closes[-1] = stock_closes[-11] * 1.15
        data = {"2330": _make_df(stock_closes, [5000] * 80)}
        market_closes = [50.0 + i * 0.1 for i in range(80)]
        market = _make_df(market_closes)
        result = run_all_filters(data, market)
        assert "2330" in result

    def test_price_too_low(self):
        """收盤價太低應在第一關被過濾。"""
        closes = [10.0 + i * 0.1 for i in range(80)]
        data = {"2330": _make_df(closes, [5000] * 80)}
        market = _make_df([50.0] * 80)
        assert run_all_filters(data, market) == {}

    def test_empty_input(self):
        market = _make_df([100.0] * 11)
        assert run_all_filters({}, market) == {}
