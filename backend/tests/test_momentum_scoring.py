"""動能評分與分類模組測試。"""
import numpy as np
import pandas as pd
import pytest

from app.services.momentum_scoring import (
    calculate_momentum_score,
    calculate_trading_plan,
    classify,
)


# ── 評分測試 ──────────────────────────────────────────────


class TestCalculateMomentumScore:
    def test_all_dimensions_80(self):
        """所有維度對應正規化值約 80 時，總分約 80。"""
        score = calculate_momentum_score(
            rs=1.6,           # 1.6 * 50 = 80
            rsi=80,           # 80
            adx=80,           # 80
            volume_ratio=1.6, # 1.6 * 50 = 80
            breakout_magnitude=0.8,  # 0.8 * 100 = 80
            accumulation_score=0.8,  # 0.8 * 100 = 80
        )
        assert score == pytest.approx(80.0)

    def test_all_zero(self):
        score = calculate_momentum_score(0, 0, 0, 0, 0, 0)
        assert score == 0.0

    def test_clamped_to_100(self):
        """超出範圍的值被截斷至 100。"""
        score = calculate_momentum_score(
            rs=5.0, rsi=120, adx=200,
            volume_ratio=10, breakout_magnitude=5, accumulation_score=3,
        )
        assert score == 100.0

    def test_negative_rs_clamped_to_zero(self):
        score = calculate_momentum_score(rs=-1, rsi=60, adx=60, volume_ratio=1.2, breakout_magnitude=0.6, accumulation_score=0.6)
        # norm_rs = 0, others positive
        assert score > 0


# ── 分類測試 ──────────────────────────────────────────────


class TestClassify:
    def test_buy(self):
        assert classify(70, breakout_passed=True, accumulation_passed=False, in_top_sector=True) == "BUY"

    def test_buy_requires_top_sector(self):
        assert classify(70, breakout_passed=True, accumulation_passed=False, in_top_sector=False) != "BUY"

    def test_watch_at_60(self):
        assert classify(60, breakout_passed=False, accumulation_passed=False, in_top_sector=False) == "WATCH"

    def test_watch_not_when_breakout(self):
        """breakout_passed 為 True 且 score=65 不符合 BUY（<70），也不符合 WATCH。"""
        result = classify(65, breakout_passed=True, accumulation_passed=False, in_top_sector=False)
        assert result != "WATCH"

    def test_early_at_50(self):
        assert classify(50, breakout_passed=False, accumulation_passed=True, in_top_sector=False) == "EARLY"

    def test_ignore_below_50(self):
        assert classify(40, breakout_passed=False, accumulation_passed=True, in_top_sector=False) == "IGNORE"

    def test_priority_buy_over_watch(self):
        """BUY 優先於 WATCH：score >= 70、breakout、top_sector。"""
        assert classify(75, breakout_passed=True, accumulation_passed=True, in_top_sector=True) == "BUY"

    def test_priority_watch_over_early(self):
        """WATCH 優先於 EARLY：score >= 60、no breakout、accumulation。"""
        assert classify(65, breakout_passed=False, accumulation_passed=True, in_top_sector=False) == "WATCH"


# ── 交易計畫測試 ──────────────────────────────────────────


def _make_ohlcv(n: int = 30, base_price: float = 100.0) -> pd.DataFrame:
    """產生 n 天的合成 OHLCV 資料。"""
    np.random.seed(42)
    closes = base_price + np.cumsum(np.random.randn(n) * 0.5)
    highs = closes + np.abs(np.random.randn(n)) * 0.5
    lows = closes - np.abs(np.random.randn(n)) * 0.5
    return pd.DataFrame({
        "Open": closes + np.random.randn(n) * 0.1,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": np.random.randint(1000, 10000, n),
    })


class TestCalculateTradingPlan:
    def test_basic(self):
        df = _make_ohlcv(30)
        plan = calculate_trading_plan(df)
        assert plan["buy_price"] is not None
        assert plan["stop_price"] is not None
        assert plan["add_price"] is not None
        assert plan["target_price"] is not None
        assert plan["buy_price"] > plan["stop_price"]
        assert plan["target_price"] > plan["buy_price"]

    def test_insufficient_data(self):
        df = _make_ohlcv(10)
        plan = calculate_trading_plan(df)
        assert all(v is None for v in plan.values())

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        plan = calculate_trading_plan(df)
        assert all(v is None for v in plan.values())

    def test_buy_price_is_max_close_times_101(self):
        df = _make_ohlcv(30)
        expected = round(float(df["Close"].iloc[-20:].max() * 1.01), 2)
        plan = calculate_trading_plan(df)
        assert plan["buy_price"] == expected

    def test_stop_price_is_min_low(self):
        df = _make_ohlcv(30)
        expected = round(float(df["Low"].iloc[-10:].min()), 2)
        plan = calculate_trading_plan(df)
        assert plan["stop_price"] == expected
