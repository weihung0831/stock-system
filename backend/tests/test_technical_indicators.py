"""技術指標純函式測試。"""
import pytest
import pandas as pd
import numpy as np

from app.services.technical_indicators import (
    calculate_ma,
    calculate_rsi,
    calculate_atr,
    calculate_adx,
    calculate_rs,
    calculate_return,
)


@pytest.fixture
def sample_closes():
    """70 筆收盤價（足夠計算所有指標）。"""
    np.random.seed(42)
    base = 100 + np.cumsum(np.random.randn(70) * 0.5)
    return pd.Series(base, dtype=float)


@pytest.fixture
def short_closes():
    """不足 60 筆的短資料。"""
    return pd.Series([100.0, 101.0, 99.5, 102.0, 98.0], dtype=float)


@pytest.fixture
def ohlc_data():
    """70 筆 OHLC 資料。"""
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(70) * 0.5)
    high = close + np.abs(np.random.randn(70) * 0.3)
    low = close - np.abs(np.random.randn(70) * 0.3)
    return pd.Series(high), pd.Series(low), pd.Series(close)


class TestCalculateMA:
    def test_basic(self, sample_closes):
        ma = calculate_ma(sample_closes, 5)
        assert len(ma) == len(sample_closes)
        assert pd.isna(ma.iloc[3])
        assert not pd.isna(ma.iloc[4])
        expected = sample_closes.iloc[:5].mean()
        assert abs(ma.iloc[4] - expected) < 1e-10

    def test_short_data(self, short_closes):
        ma = calculate_ma(short_closes, 10)
        assert ma.isna().all()


class TestCalculateRSI:
    def test_range(self, sample_closes):
        rsi = calculate_rsi(sample_closes, 14)
        valid = rsi.dropna()
        assert len(valid) > 0
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_short_data(self, short_closes):
        rsi = calculate_rsi(short_closes, 14)
        assert rsi.isna().all()

    def test_monotonic_up(self):
        closes = pd.Series(range(1, 31), dtype=float)
        rsi = calculate_rsi(closes, 14)
        valid = rsi.dropna()
        assert valid.iloc[-1] == 100.0


class TestCalculateATR:
    def test_positive(self, ohlc_data):
        h, l, c = ohlc_data
        atr = calculate_atr(h, l, c, 14)
        valid = atr.dropna()
        assert len(valid) > 0
        assert (valid > 0).all()

    def test_short_data(self, short_closes):
        s = short_closes
        atr = calculate_atr(s + 1, s - 1, s, 14)
        assert atr.dropna().empty


class TestCalculateADX:
    def test_range(self, ohlc_data):
        h, l, c = ohlc_data
        adx = calculate_adx(h, l, c, 14)
        valid = adx.dropna()
        assert len(valid) > 0
        assert (valid >= 0).all()

    def test_short_data(self, short_closes):
        s = short_closes
        adx = calculate_adx(s + 1, s - 1, s, 14)
        assert adx.dropna().empty


class TestCalculateRS:
    def test_normal(self):
        assert calculate_rs(10.0, 5.0) == 2.0

    def test_market_zero(self):
        result = calculate_rs(10.0, 0.0)
        assert result == 10.0

    def test_market_negative(self):
        result = calculate_rs(5.0, -3.0)
        assert result == 8.0

    def test_both_positive(self):
        assert abs(calculate_rs(15.0, 10.0) - 1.5) < 1e-10


class TestCalculateReturn:
    def test_basic(self, sample_closes):
        ret = calculate_return(sample_closes, 20)
        assert isinstance(ret, float)

    def test_known_value(self):
        closes = pd.Series([100.0] * 20 + [110.0])
        ret = calculate_return(closes, 20)
        assert abs(ret - 10.0) < 1e-10

    def test_insufficient_data(self, short_closes):
        ret = calculate_return(short_closes, 20)
        assert ret == 0.0

    def test_zero_start(self):
        closes = pd.Series([0.0] * 21 + [10.0])
        ret = calculate_return(closes, 20)
        assert ret == 0.0
