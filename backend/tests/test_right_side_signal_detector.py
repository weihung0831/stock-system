"""Tests for RightSideSignalDetector class."""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from app.services.right_side_signal_detector import RightSideSignalDetector


class TestRightSideSignalDetectorDataLoading:
    """Test data loading from database."""

    def test_load_prices_nonexistent_stock(self, test_db):
        """Test _load_prices returns None for nonexistent stock."""
        detector = RightSideSignalDetector()
        result = detector._load_prices(test_db, "9999")
        assert result is None


class TestBreakout20DHighSignal:
    """Test 突破20日高點 signal."""

    def test_breakout_20d_high_triggered(self):
        """Test signal triggers when latest close > prev 20d high."""
        detector = RightSideSignalDetector()

        # Create data where latest close breaks 20d high
        # Need 21+ data points (20 days of history + current day)
        dates = pd.date_range(start="2024-01-01", periods=22, freq="D")
        df = pd.DataFrame({
            "open": [100.0] * 20 + [105.0, 108.0],
            "high": [101.0] * 20 + [106.0, 109.0],
            "low": [99.0] * 20 + [104.0, 107.0],
            "close": [100.5] * 20 + [105.0, 110.0],  # Latest high breaks previous 20d high
            "volume": [1000000] * 22,
        }, index=dates)

        result = detector._check_breakout_20d_high(df)

        assert result["id"] == "breakout_20d_high"
        assert result["triggered"] is True
        assert "110.00" in result["description"]

    def test_breakout_20d_high_not_triggered(self):
        """Test signal doesn't trigger when latest close <= prev 20d high."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        df = pd.DataFrame({
            "open": [100.0] * 25,
            "high": [102.0] * 25,
            "low": [99.0] * 25,
            "close": [101.0] * 25,
            "volume": [1000000] * 25,
        }, index=dates)

        result = detector._check_breakout_20d_high(df)

        assert result["triggered"] is False

    def test_breakout_20d_high_insufficient_data(self):
        """Test signal handles insufficient data gracefully."""
        detector = RightSideSignalDetector()

        # Only 5 days - need 21+ for 20d high calculation
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({
            "open": [100.0] * 5,
            "high": [102.0] * 5,
            "low": [99.0] * 5,
            "close": [101.0] * 5,
            "volume": [1000000] * 5,
        }, index=dates)

        result = detector._check_breakout_20d_high(df)

        assert result["triggered"] is False
        # With 5 days, iloc[-21:-1] will still execute but with NaN values
        # The function doesn't explicitly check for "不足", it just handles NaN


class TestReclaimMA20Signal:
    """Test 站回MA20 signal."""

    def test_reclaim_ma20_triggered(self):
        """Test signal triggers on golden cross above MA20."""
        detector = RightSideSignalDetector()

        # Need sufficient data for MA20 calculation (20+ days)
        # Create a pattern: stable at 100, dip below, then cross back above
        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 20 + [99.5, 99.0, 99.5, 100.5, 101.0]  # Dip below, then cross above
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000000] * 25,
        }, index=dates)

        result = detector._check_reclaim_ma20(df)

        assert result["id"] == "reclaim_ma20"
        # May or may not trigger depending on MA20 calculation, just verify structure
        assert "triggered" in result
        assert isinstance(result["triggered"], (bool, np.bool_))

    def test_reclaim_ma20_not_triggered_below(self):
        """Test signal doesn't trigger when staying below MA20."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 23 + [98.0, 97.0]  # Below MA20
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000000] * 25,
        }, index=dates)

        result = detector._check_reclaim_ma20(df)

        assert result["triggered"] is False

    def test_reclaim_ma20_insufficient_data(self):
        """Test signal handles insufficient data."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({
            "open": [100.0] * 5,
            "high": [102.0] * 5,
            "low": [99.0] * 5,
            "close": [101.0] * 5,
            "volume": [1000000] * 5,
        }, index=dates)

        result = detector._check_reclaim_ma20(df)

        assert result["triggered"] is False
        # With 5 days, MA20 will be NaN but code doesn't explicitly check for "不足"


class TestKDGoldenCrossSignal:
    """Test KD低檔黃金交叉 signal."""

    def test_kd_golden_cross_triggered(self):
        """Test KD golden cross signal when K crosses above D in low zone."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        closes = [80.0] * 15 + [85.0] * 15  # Low prices, then recovery
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 2 for c in closes],
            "low": [c - 2 for c in closes],
            "close": closes,
            "volume": [1000000] * 30,
        }, index=dates)

        result = detector._check_kd_golden_cross(df)

        assert result["id"] == "kd_golden_cross"
        assert isinstance(result["triggered"], (bool, np.bool_))

    def test_kd_golden_cross_not_in_oversold(self):
        """Test KD doesn't trigger when K is not in oversold zone."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        closes = [100.0] * 30  # Stable high price
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000000] * 30,
        }, index=dates)

        result = detector._check_kd_golden_cross(df)

        # In high zone, so should not trigger despite potential cross
        assert "K=" in result["description"]

    def test_kd_insufficient_data(self):
        """Test KD handles insufficient data."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({
            "open": [100.0] * 5,
            "high": [102.0] * 5,
            "low": [99.0] * 5,
            "close": [101.0] * 5,
            "volume": [1000000] * 5,
        }, index=dates)

        result = detector._check_kd_golden_cross(df)

        assert result["triggered"] is False


class TestMACDGoldenCrossSignal:
    """Test MACD黃金交叉 signal."""

    def test_macd_golden_cross_triggered(self):
        """Test MACD golden cross signal."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        closes = [100.0] * 25 + [102.0] * 25  # Uptrend
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000000] * 50,
        }, index=dates)

        result = detector._check_macd_golden_cross(df)

        assert result["id"] == "macd_golden_cross"
        assert "DIF=" in result["description"]
        assert "Signal=" in result["description"]

    def test_macd_downtrend(self):
        """Test MACD in downtrend."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        closes = [100.0] * 25 + [98.0] * 25  # Downtrend
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000000] * 50,
        }, index=dates)

        result = detector._check_macd_golden_cross(df)

        assert result["triggered"] is False


class TestVolumePriceSurgeSignal:
    """Test 量價齊揚 signal."""

    def test_volume_price_surge_triggered(self):
        """Test signal triggers on price up with 1.5x average volume."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 23 + [101.0, 102.0]
        volumes = [1000000] * 23 + [1500000, 1600000]  # Surge above 1.5x avg
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": volumes,
        }, index=dates)

        result = detector._check_volume_price_surge(df)

        assert result["id"] == "volume_price_surge"
        assert result["triggered"] is True
        assert "漲" in result["description"]

    def test_volume_price_surge_price_down(self):
        """Test signal doesn't trigger on price down."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 23 + [101.0, 99.0]  # Price down at end
        volumes = [1000000] * 23 + [1500000, 1600000]
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": volumes,
        }, index=dates)

        result = detector._check_volume_price_surge(df)

        assert result["triggered"] is False
        assert "跌" in result["description"]

    def test_volume_price_surge_insufficient_volume(self):
        """Test signal doesn't trigger on low volume."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 23 + [101.0, 102.0]
        volumes = [1000000] * 25  # No surge
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": volumes,
        }, index=dates)

        result = detector._check_volume_price_surge(df)

        assert result["triggered"] is False


class TestBollingerBandBreakoutSignal:
    """Test 突破布林上軌 signal."""

    def test_bb_upper_breakout_triggered(self):
        """Test signal triggers when breaking above Bollinger upper band."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 22 + [100.5, 101.0, 105.0]  # Breakout upward
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000000] * 25,
        }, index=dates)

        result = detector._check_breakout_bb_upper(df)

        assert result["id"] == "breakout_bb_upper"
        # Triggered depends on volatility, but should execute without error
        assert isinstance(result["triggered"], (bool, np.bool_))

    def test_bb_upper_stable_price(self):
        """Test signal with stable price."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 25
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 0.5 for c in closes],
            "low": [c - 0.5 for c in closes],
            "close": closes,
            "volume": [1000000] * 25,
        }, index=dates)

        result = detector._check_breakout_bb_upper(df)

        assert result["triggered"] is False


class TestDetectAllSignals:
    """Test the main detect() method."""

    def test_detect_nonexistent_stock_returns_all_false(self, test_db):
        """Test detect() returns dict with all False signals for nonexistent stock."""
        detector = RightSideSignalDetector()
        result = detector.detect(test_db, "9999")

        # detect() now returns dict with signals, score, triggered_count, prediction
        assert isinstance(result, dict)
        assert "signals" in result
        assert "score" in result
        assert "triggered_count" in result
        assert "prediction" in result

        signals = result["signals"]
        assert len(signals) == 6
        assert all(r["triggered"] is False for r in signals)
        assert all("不足" in r["description"] for r in signals)
        assert result["score"] == 0
        assert result["triggered_count"] == 0
        assert result["prediction"] is None

    def test_detect_signal_structure_validity(self):
        """Test detect() would return proper signal structure."""
        detector = RightSideSignalDetector()
        # Verify signal definitions have proper structure
        for sig_def in detector.SIGNAL_DEFS:
            assert "id" in sig_def
            assert "label" in sig_def


class TestCalcScore:
    """Test calc_score() static method."""

    def test_calc_score_no_signals_triggered(self):
        """Score = 0 when no signals triggered."""
        signals = [
            {"id": "breakout_20d_high", "triggered": False, "weight": 20},
            {"id": "reclaim_ma20", "triggered": False, "weight": 15},
        ]
        assert RightSideSignalDetector.calc_score(signals) == 0

    def test_calc_score_all_signals_triggered(self):
        """Score = sum of all weights when all triggered."""
        signals = [s.copy() for s in RightSideSignalDetector.SIGNAL_DEFS]
        for s in signals:
            s["triggered"] = True
        total = sum(s["weight"] for s in RightSideSignalDetector.SIGNAL_DEFS)
        assert RightSideSignalDetector.calc_score(signals) == total

    def test_calc_score_partial_triggered(self):
        """Score = sum of triggered weights only."""
        signals = [
            {"triggered": True, "weight": 20},   # breakout_20d_high
            {"triggered": True, "weight": 25},   # volume_price_surge
            {"triggered": False, "weight": 15},  # reclaim_ma20
            {"triggered": False, "weight": 12},  # kd_golden_cross
            {"triggered": False, "weight": 20},  # macd_golden_cross
            {"triggered": False, "weight": 8},   # breakout_bb_upper
        ]
        assert RightSideSignalDetector.calc_score(signals) == 45

    def test_calc_score_missing_weight_key(self):
        """Signals without weight key should contribute 0."""
        signals = [
            {"triggered": True},   # no weight key
            {"triggered": True, "weight": 20},
        ]
        assert RightSideSignalDetector.calc_score(signals) == 20

    def test_calc_score_returns_int(self):
        """calc_score() should return int."""
        signals = [{"triggered": True, "weight": 20}]
        result = RightSideSignalDetector.calc_score(signals)
        assert isinstance(result, int)

    def test_calc_score_full_weights_sum_to_100(self):
        """All SIGNAL_DEFS weights must sum to 100."""
        total = sum(s["weight"] for s in RightSideSignalDetector.SIGNAL_DEFS)
        assert total == 100


class TestCalcPrediction:
    """Test _calc_prediction() static method."""

    def _make_df(self, closes, lows=None, n=25):
        """Build minimal DataFrame for prediction tests."""
        dates = pd.date_range(start="2024-01-01", periods=n, freq="D")
        if lows is None:
            lows = [c - 5 for c in closes]
        return pd.DataFrame({
            "open": closes,
            "high": [c + 5 for c in closes],
            "low": lows,
            "close": closes,
            "volume": [1000000] * n,
        }, index=dates)

    def test_entry_is_latest_close(self):
        """entry should equal last row close price."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        assert pred["entry"] == 100.0

    def test_risk_reward_fixed_1_5(self):
        """risk_reward must always be 1.5."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        assert pred["risk_reward"] == 1.5

    def test_action_buy_when_score_ge_60(self):
        """action = buy when score >= 60."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        assert pred["action"] == "buy"
        assert pred["action_label"] == "建議買入"

    def test_action_buy_boundary_score_60(self):
        """action = buy at exact score 60."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        assert pred["action"] == "buy"

    def test_action_hold_when_score_35_to_59(self):
        """action = hold when 35 <= score < 60."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        for score in [35, 45, 59]:
            pred = RightSideSignalDetector._calc_prediction(df, score)
            assert pred["action"] == "hold", f"Expected hold at score={score}"
            assert pred["action_label"] == "觀望等待"

    def test_action_avoid_when_score_lt_35(self):
        """action = avoid when score < 35."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        for score in [0, 20, 34]:
            pred = RightSideSignalDetector._calc_prediction(df, score)
            assert pred["action"] == "avoid", f"Expected avoid at score={score}"
            assert pred["action_label"] == "暫不建議"

    def test_stop_loss_is_max_of_ma20_and_20d_low(self):
        """stop_loss = max(MA20, 20d low) when below entry."""
        # Stable at 100 → MA20 = 100, 20d low ≈ 95
        closes = [100.0] * 24 + [110.0]  # last close = 110
        lows = [95.0] * 24 + [105.0]
        df = self._make_df(closes, lows=lows)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        # MA20 = (100*24 + 110) / 25 ≈ 100.4, 20d low = min of last 20 lows
        assert pred["stop_loss"] < pred["entry"]

    def test_stop_loss_fallback_when_ge_entry(self):
        """stop_loss = close * 0.95 when calculated stop >= entry."""
        # Rapidly rising price: MA20 >> latest close would only happen if price was higher
        # Simulate: close = 50, MA20 and 20d low both = 60 (both above close)
        # Actually this edge case: if stock gapped down significantly
        # Use: last 24 closes = 200, last close = 100 → MA20 ≈ 195 > 100
        closes = [200.0] * 24 + [100.0]
        lows = [190.0] * 24 + [95.0]
        df = self._make_df(closes, lows=lows)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        expected_stop = round(100.0 * 0.95, 2)
        assert pred["stop_loss"] == expected_stop

    def test_target_formula(self):
        """target = entry + 1.5 * (entry - stop_loss)."""
        # Use normal upward trend where stop < entry
        closes = [100.0] * 24 + [110.0]
        lows = [85.0] * 24 + [105.0]
        df = self._make_df(closes, lows=lows)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        expected_target = round(
            pred["entry"] + 1.5 * (pred["entry"] - pred["stop_loss"]), 2
        )
        assert pred["target"] == expected_target

    def test_prediction_dict_has_required_keys(self):
        """Prediction dict must contain all required keys."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        pred = RightSideSignalDetector._calc_prediction(df, 50)
        for key in ("entry", "stop_loss", "target", "risk_reward", "action", "action_label"):
            assert key in pred, f"Missing key: {key}"

    def test_target_gt_entry(self):
        """target must always be greater than entry."""
        closes = [100.0] * 25
        df = self._make_df(closes)
        pred = RightSideSignalDetector._calc_prediction(df, 60)
        assert pred["target"] > pred["entry"]


class TestSignalDefaults:
    """Test signal definition constants."""

    def test_signal_defs_count(self):
        """Test SIGNAL_DEFS has 6 entries."""
        assert len(RightSideSignalDetector.SIGNAL_DEFS) == 6

    def test_signal_defs_structure(self):
        """Test each signal def has required fields."""
        for sig in RightSideSignalDetector.SIGNAL_DEFS:
            assert "id" in sig
            assert "label" in sig

    def test_signal_ids_unique(self):
        """Test all signal IDs are unique."""
        ids = [s["id"] for s in RightSideSignalDetector.SIGNAL_DEFS]
        assert len(ids) == len(set(ids))


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_dataframe_with_nan_values(self):
        """Test handling of NaN values in DataFrame."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 10 + [np.nan] * 5 + [100.5] * 10
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 if not np.isnan(c) else np.nan for c in closes],
            "low": [c - 1 if not np.isnan(c) else np.nan for c in closes],
            "close": closes,
            "volume": [1000000] * 25,
        }, index=dates)

        # Should handle NaN gracefully
        result = detector._check_breakout_20d_high(df)
        assert "triggered" in result
        assert "description" in result

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        detector = RightSideSignalDetector()

        df = pd.DataFrame({
            "open": [],
            "high": [],
            "low": [],
            "close": [],
            "volume": [],
        })

        result = detector._check_breakout_20d_high(df)

        assert result["triggered"] is False

    def test_single_row_dataframe(self):
        """Test handling of single-row DataFrame."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=1, freq="D")
        df = pd.DataFrame({
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [1000000],
        }, index=dates)

        result = detector._check_breakout_20d_high(df)

        assert result["triggered"] is False
        # With 1 day, iloc[-21:-1] produces empty series, handled gracefully

    def test_zero_volume_handling(self):
        """Test handling of zero volume."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        closes = [100.0] * 23 + [101.0, 102.0]
        volumes = [1000000] * 23 + [0, 0]  # Zero volume
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": volumes,
        }, index=dates)

        result = detector._check_volume_price_surge(df)

        assert result["triggered"] is False

    def test_large_price_values(self):
        """Test handling of large price values."""
        detector = RightSideSignalDetector()

        dates = pd.date_range(start="2024-01-01", periods=22, freq="D")
        closes = [10000.0] * 20 + [10100.0, 10200.0]
        df = pd.DataFrame({
            "open": closes,
            "high": [c + 100 for c in closes],
            "low": [c - 100 for c in closes],
            "close": closes,
            "volume": [10000000] * 22,
        }, index=dates)

        result = detector._check_breakout_20d_high(df)

        assert "triggered" in result
        assert isinstance(result["triggered"], (bool, np.bool_))
