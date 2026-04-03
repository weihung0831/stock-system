"""信號偵測模組測試。"""

import pandas as pd
import numpy as np
import pytest
from app.services.momentum.signals import (
    detect_accumulation,
    detect_breakout,
    detect_momentum_stock,
)


def _make_df(n: int, close=100.0, volume=1000, low_offset=2, high_offset=2):
    """建立基本測試 DataFrame。"""
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "Date": dates,
        "Open": [close] * n,
        "High": [close + high_offset] * n,
        "Low": [close - low_offset] * n,
        "Close": [close] * n,
        "Volume": [volume] * n,
    })


# === detect_accumulation ===

class TestDetectAccumulation:
    def test_all_passed(self):
        """量增 + 橫盤 + 低點墊高 → 全通過。"""
        df = _make_df(25, close=100, volume=1000)
        # 量增：最近 5 日量 > 20 日均量 × 1.3
        df.loc[df.index[-5:], "Volume"] = 2000
        # 低點墊高：前 5 日低點較低
        df.loc[df.index[-10:-5], "Low"] = 95
        df.loc[df.index[-5:], "Low"] = 98

        passed, score = detect_accumulation(df)
        assert passed is True
        assert score == pytest.approx(1.0)

    def test_partial_pass(self):
        """只有 2/3 條件通過。"""
        df = _make_df(25, close=100, volume=1000)
        # 量增
        df.loc[df.index[-5:], "Volume"] = 2000
        # 低點墊高
        df.loc[df.index[-10:-5], "Low"] = 95
        df.loc[df.index[-5:], "Low"] = 98
        # 破壞橫盤：大幅波動
        df.loc[df.index[-10], "Close"] = 80
        df.loc[df.index[-9], "Close"] = 120

        passed, score = detect_accumulation(df)
        assert passed is False
        assert score == pytest.approx(2 / 3)

    def test_all_fail(self):
        """全不通過。"""
        df = _make_df(25, close=100, volume=1000)
        # 量縮
        df.loc[df.index[-5:], "Volume"] = 500
        # 大波動
        df.loc[df.index[-10], "Close"] = 50
        df.loc[df.index[-9], "Close"] = 150
        # 低點下降
        df.loc[df.index[-10:-5], "Low"] = 99
        df.loc[df.index[-5:], "Low"] = 90

        passed, score = detect_accumulation(df)
        assert passed is False
        assert score == pytest.approx(0.0)

    def test_insufficient_data(self):
        df = _make_df(10)
        passed, score = detect_accumulation(df)
        assert passed is False
        assert score == 0.0


# === detect_breakout ===

class TestDetectBreakout:
    def test_breakout_above_threshold(self):
        """收盤突破 20 日高點 +1% 且量放大。"""
        df = _make_df(25, close=100, volume=1000)
        df.loc[df.index[-1], "Close"] = 105
        df.loc[df.index[-1], "Volume"] = 2000

        passed, mag = detect_breakout(df)
        assert passed is True
        assert mag > 1.0  # 超過 1%

    def test_exactly_at_threshold(self):
        """恰好在 1.01 × 20d high 邊界。"""
        df = _make_df(25, close=100, volume=1000, high_offset=0)
        high_20 = 100  # 前 20 日最高
        df.loc[df.index[-1], "Close"] = high_20 * 1.01 + 0.001  # 剛超過
        df.loc[df.index[-1], "Volume"] = 2000

        passed, mag = detect_breakout(df)
        assert passed is True
        assert mag > 0

    def test_below_threshold(self):
        """未達閾值。"""
        df = _make_df(25, close=100, volume=1000)
        # 收盤沒超過
        df.loc[df.index[-1], "Close"] = 100
        df.loc[df.index[-1], "Volume"] = 2000

        passed, mag = detect_breakout(df)
        assert passed is False
        assert mag == 0.0

    def test_insufficient_data(self):
        df = _make_df(15)
        passed, mag = detect_breakout(df)
        assert passed is False
        assert mag == 0.0


# === detect_momentum_stock ===

class TestDetectMomentumStock:
    def _make_momentum_pair(self, n=100):
        """建立個股與大盤 DataFrame。"""
        dates = pd.date_range("2025-01-01", periods=n, freq="B")
        stock = pd.DataFrame({
            "Date": dates,
            "Open": np.linspace(100, 150, n),
            "High": np.linspace(102, 152, n),
            "Low": np.linspace(98, 148, n),
            "Close": np.linspace(100, 150, n),
            "Volume": [1000] * n,
        })
        market = pd.DataFrame({
            "Date": dates,
            "Open": np.linspace(100, 110, n),
            "High": np.linspace(102, 112, n),
            "Low": np.linspace(98, 108, n),
            "Close": np.linspace(100, 110, n),
            "Volume": [5000] * n,
        })
        return stock, market

    def test_all_conditions_met(self):
        """RS 新高 + ATR 收縮 + 量縮 → True。"""
        stock, market = self._make_momentum_pair()
        # ATR 收縮：壓縮近期 high-low 差距
        stock.loc[stock.index[-20:], "High"] = stock.loc[stock.index[-20:], "Close"] + 0.5
        stock.loc[stock.index[-20:], "Low"] = stock.loc[stock.index[-20:], "Close"] - 0.5
        # 量縮
        stock.loc[stock.index[-5:], "Volume"] = 300

        result = detect_momentum_stock(stock, market)
        assert result is True

    def test_rs_high_but_atr_not_shrinking(self):
        """RS 高但 ATR 未收縮 → False。"""
        stock, market = self._make_momentum_pair()
        # 量縮
        stock.loc[stock.index[-5:], "Volume"] = 300
        # 保持 ATR 不收縮（放大波動）
        stock.loc[stock.index[-14:], "High"] = stock.loc[stock.index[-14:], "Close"] + 10
        stock.loc[stock.index[-14:], "Low"] = stock.loc[stock.index[-14:], "Close"] - 10

        result = detect_momentum_stock(stock, market)
        assert result is False

    def test_insufficient_data(self):
        """資料不足 → False。"""
        stock = _make_df(30)
        market = _make_df(30)
        assert detect_momentum_stock(stock, market) is False
