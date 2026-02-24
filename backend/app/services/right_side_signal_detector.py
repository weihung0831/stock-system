"""Right-side (momentum) trading signal detector."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.daily_price import DailyPrice

logger = logging.getLogger(__name__)


class RightSideSignalDetector:
    """Detect 6 right-side entry signals for a given stock."""

    SIGNAL_DEFS = [
        {"id": "breakout_20d_high", "label": "突破20日高點", "weight": 20},
        {"id": "reclaim_ma20", "label": "站回MA20", "weight": 15},
        {"id": "kd_golden_cross", "label": "KD低檔黃金交叉", "weight": 12},
        {"id": "macd_golden_cross", "label": "MACD黃金交叉", "weight": 20},
        {"id": "volume_price_surge", "label": "量價齊揚", "weight": 25},
        {"id": "breakout_bb_upper", "label": "突破布林上軌", "weight": 8},
    ]

    def detect(self, db: Session, stock_id: str, preloaded_df: pd.DataFrame | None = None) -> dict:
        """Run all 6 signal checks, calculate score & trade prediction."""
        df = preloaded_df if preloaded_df is not None else self._load_prices(db, stock_id)
        if df is None or len(df) < 20:
            signals = [
                {**s, "triggered": False, "description": "資料不足"}
                for s in self.SIGNAL_DEFS
            ]
            return {
                "signals": signals,
                "score": 0,
                "triggered_count": 0,
                "prediction": None,
            }

        signals = [
            self._check_breakout_20d_high(df),
            self._check_reclaim_ma20(df),
            self._check_kd_golden_cross(df),
            self._check_macd_golden_cross(df),
            self._check_volume_price_surge(df),
            self._check_breakout_bb_upper(df),
        ]
        score = self.calc_score(signals)
        triggered = sum(1 for s in signals if s["triggered"])
        prediction = self._calc_prediction(df, score)

        # Extra screening tags
        today_breakout = self._check_today_breakout(df)
        weekly_trend_up = self._check_weekly_trend_up(df)
        risk_level = self._calc_risk_level(df, score)
        strong_recommend = self._check_strong_recommend(
            score, triggered, today_breakout, weekly_trend_up, risk_level
        )

        return {
            "signals": signals,
            "score": score,
            "triggered_count": triggered,
            "prediction": prediction,
            "today_breakout": today_breakout,
            "weekly_trend_up": weekly_trend_up,
            "strong_recommend": strong_recommend,
            "risk_level": risk_level,
        }

    @staticmethod
    def calc_score(signals: list[dict]) -> int:
        """Calculate weighted score (0-100) from signal results."""
        return sum(s.get("weight", 0) for s in signals if s.get("triggered"))

    @staticmethod
    def _calc_prediction(df: pd.DataFrame, score: int) -> dict:
        """Calculate buy/sell price prediction based on technicals.

        - entry: latest close (signal confirmed = enter)
        - stop_loss: max(MA20, 20-day low) — nearest support
        - target: entry + 1.5 * (entry - stop_loss) — 1.5x reward/risk
        - action: buy / hold / avoid based on score
        """
        close = float(df.iloc[-1]["close"])
        ma20 = float(df["close"].rolling(20).mean().iloc[-1])
        low_20d = float(df["low"].iloc[-20:].min())

        stop_loss = round(max(ma20, low_20d), 2)
        # Ensure stop_loss is below entry
        if stop_loss >= close:
            stop_loss = round(close * 0.95, 2)

        risk = close - stop_loss
        reward_multiplier = 2.0 if score >= 60 else 1.5 if score >= 35 else 1.0
        target = round(close + reward_multiplier * risk, 2) if risk > 0 else round(close * 1.05, 2)
        rr = round((target - close) / risk, 1) if risk > 0 else 0.0

        if score >= 60:
            action = "buy"
            action_label = "建議買入"
        elif score >= 35:
            action = "hold"
            action_label = "觀望等待"
        else:
            action = "avoid"
            action_label = "暫不建議"

        return {
            "entry": round(close, 2),
            "stop_loss": stop_loss,
            "target": target,
            "risk_reward": rr,
            "action": action,
            "action_label": action_label,
        }

    def _load_prices(self, db: Session, stock_id: str) -> pd.DataFrame | None:
        """Load 120 trading days of price data into DataFrame."""
        cutoff = date.today() - timedelta(days=180)
        rows = (
            db.query(DailyPrice)
            .filter(DailyPrice.stock_id == stock_id, DailyPrice.trade_date >= cutoff)
            .order_by(DailyPrice.trade_date.asc())
            .all()
        )
        if not rows:
            return None

        df = pd.DataFrame([
            {
                "date": r.trade_date,
                "open": float(r.open),
                "high": float(r.high),
                "low": float(r.low),
                "close": float(r.close),
                "volume": int(r.volume),
            }
            for r in rows
        ])
        df.set_index("date", inplace=True)
        return df

    # --- Signal 1: 突破20日高點 ---
    def _check_breakout_20d_high(self, df: pd.DataFrame) -> dict:
        sig = {**self.SIGNAL_DEFS[0]}
        try:
            latest_close = df.iloc[-1]["close"]
            prev_20d_high = df["high"].iloc[-21:-1].max()
            triggered = bool(latest_close > prev_20d_high)
            sig["triggered"] = triggered
            sig["description"] = (
                f"收盤 {latest_close:.2f} {'>' if triggered else '≤'} "
                f"前20日高 {prev_20d_high:.2f}"
            )
        except Exception:
            sig["triggered"] = False
            sig["description"] = "資料不足"
        return sig

    # --- Signal 2: 站回MA20 ---
    def _check_reclaim_ma20(self, df: pd.DataFrame) -> dict:
        sig = {**self.SIGNAL_DEFS[1]}
        try:
            ma20 = df["close"].rolling(20).mean()
            latest_close = df.iloc[-1]["close"]
            prev_close = df.iloc[-2]["close"]
            latest_ma = ma20.iloc[-1]
            prev_ma = ma20.iloc[-2]
            triggered = bool(prev_close < prev_ma and latest_close >= latest_ma)
            sig["triggered"] = triggered
            sig["description"] = (
                f"今收 {latest_close:.2f} vs MA20 {latest_ma:.2f}"
            )
        except Exception:
            sig["triggered"] = False
            sig["description"] = "資料不足"
        return sig

    # --- Signal 3: KD低檔黃金交叉 ---
    def _check_kd_golden_cross(self, df: pd.DataFrame) -> dict:
        sig = {**self.SIGNAL_DEFS[2]}
        try:
            low9 = df["low"].rolling(9).min()
            high9 = df["high"].rolling(9).max()
            rsv = 100 * (df["close"] - low9) / (high9 - low9)

            k_vals = pd.Series(np.nan, index=df.index)
            d_vals = pd.Series(np.nan, index=df.index)
            first = rsv.first_valid_index()
            if first is None:
                sig["triggered"] = False
                sig["description"] = "資料不足"
                return sig

            k_vals.loc[first] = (2 / 3) * 50 + (1 / 3) * rsv.loc[first]
            d_vals.loc[first] = (2 / 3) * 50 + (1 / 3) * k_vals.loc[first]

            indices = df.index.tolist()
            start = indices.index(first)
            for i in range(start + 1, len(indices)):
                c, p = indices[i], indices[i - 1]
                if pd.isna(rsv.loc[c]):
                    continue
                k_vals.loc[c] = (2 / 3) * k_vals.loc[p] + (1 / 3) * rsv.loc[c]
                d_vals.loc[c] = (2 / 3) * d_vals.loc[p] + (1 / 3) * k_vals.loc[c]

            k_now, d_now = k_vals.iloc[-1], d_vals.iloc[-1]
            k_prev, d_prev = k_vals.iloc[-2], d_vals.iloc[-2]
            triggered = bool(
                k_now > d_now and k_prev <= d_prev and k_now < 30
            )
            sig["triggered"] = triggered
            sig["description"] = f"K={k_now:.1f} D={d_now:.1f}"
        except Exception:
            sig["triggered"] = False
            sig["description"] = "計算錯誤"
        return sig

    # --- Signal 4: MACD黃金交叉 ---
    def _check_macd_golden_cross(self, df: pd.DataFrame) -> dict:
        sig = {**self.SIGNAL_DEFS[3]}
        try:
            ema12 = df["close"].ewm(span=12, adjust=False).mean()
            ema26 = df["close"].ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            signal = dif.ewm(span=9, adjust=False).mean()

            triggered = bool(
                dif.iloc[-1] > signal.iloc[-1]
                and dif.iloc[-2] <= signal.iloc[-2]
            )
            sig["triggered"] = triggered
            sig["description"] = (
                f"DIF={dif.iloc[-1]:.2f} Signal={signal.iloc[-1]:.2f}"
            )
        except Exception:
            sig["triggered"] = False
            sig["description"] = "計算錯誤"
        return sig

    # --- Signal 5: 量價齊揚 ---
    def _check_volume_price_surge(self, df: pd.DataFrame) -> dict:
        sig = {**self.SIGNAL_DEFS[4]}
        try:
            vol_ma20 = df["volume"].rolling(20).mean()
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            price_up = latest["close"] > prev["close"]
            vol_surge = latest["volume"] >= 1.5 * vol_ma20.iloc[-1]
            triggered = bool(price_up and vol_surge)
            ratio = latest["volume"] / vol_ma20.iloc[-1] if vol_ma20.iloc[-1] > 0 else 0
            sig["triggered"] = triggered
            sig["description"] = f"量比={ratio:.2f}x, 漲跌={'漲' if price_up else '跌'}"
        except Exception:
            sig["triggered"] = False
            sig["description"] = "計算錯誤"
        return sig

    # --- Signal 6: 突破布林上軌 ---
    def _check_breakout_bb_upper(self, df: pd.DataFrame) -> dict:
        sig = {**self.SIGNAL_DEFS[5]}
        try:
            ma20 = df["close"].rolling(20).mean()
            std20 = df["close"].rolling(20).std()
            upper = ma20 + 2 * std20

            latest_close = df.iloc[-1]["close"]
            prev_close = df.iloc[-2]["close"]
            upper_now = upper.iloc[-1]
            upper_prev = upper.iloc[-2]
            triggered = bool(prev_close <= upper_prev and latest_close > upper_now)
            sig["triggered"] = triggered
            sig["description"] = (
                f"收盤 {latest_close:.2f} vs 上軌 {upper_now:.2f}"
            )
        except Exception:
            sig["triggered"] = False
            sig["description"] = "計算錯誤"
        return sig

    # ========== Extra screening tags ==========

    @staticmethod
    def _check_today_breakout(df: pd.DataFrame) -> bool:
        """今日突破：當日收盤創 20 日新高。"""
        try:
            if len(df) < 21:
                return False
            latest_close = df.iloc[-1]["close"]
            prev_20d_high = df["high"].iloc[-21:-1].max()
            return bool(latest_close > prev_20d_high)
        except Exception:
            return False

    @staticmethod
    def _check_weekly_trend_up(df: pd.DataFrame) -> bool:
        """週趨勢向上：5日均線 > 20日均線，且 5日均線近3日上升。"""
        try:
            if len(df) < 23:
                return False
            ma5 = df["close"].rolling(5).mean()
            ma20 = df["close"].rolling(20).mean()
            ma5_above_ma20 = bool(ma5.iloc[-1] > ma20.iloc[-1])
            ma5_rising = bool(ma5.iloc[-1] > ma5.iloc[-3])
            return ma5_above_ma20 and ma5_rising
        except Exception:
            return False

    @staticmethod
    def _calc_risk_level(df: pd.DataFrame, score: int) -> str:
        """風險評估：依波動率 + 分數綜合判定 low / medium / high。"""
        try:
            if len(df) < 20:
                return "high"
            # 20日報酬率標準差（年化波動率簡化版）
            returns = df["close"].pct_change().dropna().iloc[-20:]
            volatility = float(returns.std()) * (252 ** 0.5)
            if volatility < 0.25 and score >= 60:
                return "low"
            if volatility < 0.40 or score >= 45:
                return "medium"
            return "high"
        except Exception:
            return "high"

    @staticmethod
    def _check_strong_recommend(
        score: int,
        triggered: int,
        today_breakout: bool,
        weekly_trend_up: bool,
        risk_level: str,
    ) -> bool:
        """強力推薦：分數 >= 60、觸發 >= 3、週趨勢向上、風險非高。"""
        return (
            score >= 60
            and triggered >= 3
            and weekly_trend_up
            and risk_level != "high"
        )
