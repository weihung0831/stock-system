"""動能評分與分類模組。"""
from __future__ import annotations

import pandas as pd

from app.services.technical_indicators import calculate_atr, calculate_ma


def calculate_momentum_score(
    rs: float,
    rsi: float,
    adx: float,
    volume_ratio: float,
    breakout_magnitude: float,
    accumulation_score: float,
) -> float:
    """計算動能綜合評分（0-100）。

    6 個維度正規化後取平均。
    """
    norm_rs = min(max(rs * 50, 0), 100)
    norm_rsi = min(max(rsi, 0), 100)
    norm_adx = min(max(adx, 0), 100)
    norm_vol = min(volume_ratio * 50, 100)
    norm_breakout = min(breakout_magnitude * 100, 100)
    norm_acc = min(max(accumulation_score * 100, 0), 100)

    return (
        norm_rs + norm_rsi + norm_adx + norm_vol + norm_breakout + norm_acc
    ) / 6


def classify(
    score: float,
    breakout_passed: bool,
    accumulation_passed: bool,
    in_top_sector: bool,
) -> str:
    """依評分與信號分類股票動能狀態。

    優先順序：BUY > WATCH > EARLY > IGNORE。
    """
    if breakout_passed and score >= 70 and in_top_sector:
        return "BUY"
    if score >= 60 and not breakout_passed:
        return "WATCH"
    if accumulation_passed and score >= 50:
        return "EARLY"
    return "IGNORE"


def calculate_trading_plan(df: pd.DataFrame) -> dict:
    """根據 OHLCV DataFrame 計算交易計畫。

    回傳 buy_price / stop_price / add_price / target_price。
    資料不足時所有值為 None。
    """
    empty = {
        "buy_price": None,
        "stop_price": None,
        "add_price": None,
        "target_price": None,
    }

    if len(df) < 20:
        return empty

    try:
        buy_price = float(df["Close"].iloc[-20:].max() * 1.01)
        stop_price = float(df["Low"].iloc[-10:].min())
        ma20 = calculate_ma(df["Close"], 20)
        add_price = float(ma20.iloc[-1])

        atr = calculate_atr(df["High"], df["Low"], df["Close"], period=14)
        atr_val = atr.iloc[-1]
        if pd.isna(atr_val):
            return empty
        target_price = buy_price + 2 * float(atr_val)
    except (KeyError, IndexError):
        return empty

    return {
        "buy_price": round(buy_price, 2),
        "stop_price": round(stop_price, 2),
        "add_price": round(add_price, 2),
        "target_price": round(target_price, 2),
    }
