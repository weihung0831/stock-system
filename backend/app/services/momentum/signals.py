"""信號偵測模組 — 吸籌、突破、飆股偵測。"""

import pandas as pd
import numpy as np
from app.services.technical_indicators import calculate_atr, calculate_return


def detect_accumulation(df: pd.DataFrame) -> tuple[bool, float]:
    """偵測吸籌信號。

    條件 1：5 日均量 > 20 日均量 × 1.3
    條件 2：10 日收盤價波動率 < 5%
    條件 3：近 5 日最低 > 前 5 日最低（低點墊高）

    回傳 (all_passed, score)，score = 符合條件數 / 3。
    """
    if len(df) < 20:
        return False, 0.0

    vol_5 = df["Volume"].iloc[-5:].mean()
    vol_20 = df["Volume"].iloc[-20:].mean()
    cond_volume = vol_5 > vol_20 * 1.3

    closes_10 = df["Close"].iloc[-10:]
    volatility = (closes_10.max() - closes_10.min()) / closes_10.mean()
    cond_sideways = volatility < 0.05

    recent_low = df["Low"].iloc[-5:].min()
    prev_low = df["Low"].iloc[-10:-5].min()
    cond_higher_low = recent_low > prev_low

    conditions = [cond_volume, cond_sideways, cond_higher_low]
    score = sum(conditions) / 3
    return all(conditions), score


def detect_breakout(df: pd.DataFrame) -> tuple[bool, float]:
    """偵測突破信號。

    條件 1：最新收盤 > 20 日最高價 × 1.01
    條件 2：最新成交量 > 20 日均量 × 1.5

    回傳 (passed, magnitude)，magnitude = 突破幅度 %。
    """
    if len(df) < 21:
        return False, 0.0

    close = df["Close"].iloc[-1]
    high_20 = df["High"].iloc[-21:-1].max()
    volume = df["Volume"].iloc[-1]
    vol_avg_20 = df["Volume"].iloc[-21:-1].mean()

    cond_price = close > high_20 * 1.01
    cond_volume = volume > vol_avg_20 * 1.5

    if cond_price and cond_volume:
        magnitude = (close / high_20 - 1) * 100
        return True, magnitude
    return False, 0.0


def detect_momentum_stock(
    df: pd.DataFrame, market_df: pd.DataFrame
) -> bool:
    """偵測飆股信號。

    條件 1：RS 創 60 日新高
    條件 2：ATR(14) < 20 日前 ATR(14) × 0.75
    條件 3：5 日均量 < 20 日均量 × 0.7

    三個條件都通過才回傳 True，資料不足回傳 False。
    """
    min_len = 80  # 需要足夠資料計算 60 日 RS + ATR
    if len(df) < min_len or len(market_df) < min_len:
        return False

    # 條件 1：RS 創 60 日新高
    stock_closes = df["Close"]
    market_closes = market_df["Close"]

    rs_series = stock_closes.pct_change() / market_closes.pct_change().replace(0, np.nan)
    rs_series = rs_series.replace([np.inf, -np.inf], np.nan).fillna(0)
    rs_cumulative = (1 + rs_series).cumprod()

    today_rs = rs_cumulative.iloc[-1]
    past_60_rs = rs_cumulative.iloc[-61:-1]
    cond_rs = today_rs >= past_60_rs.max()

    # 條件 2：ATR(14) 收縮 25%
    atr = calculate_atr(df["High"], df["Low"], df["Close"], period=14)
    cond_atr = atr.iloc[-1] < atr.iloc[-20] * 0.75

    # 條件 3：量縮 30%
    vol_5 = df["Volume"].iloc[-5:].mean()
    vol_20 = df["Volume"].iloc[-20:].mean()
    cond_vol = vol_5 < vol_20 * 0.7

    return bool(cond_rs and cond_atr and cond_vol)
