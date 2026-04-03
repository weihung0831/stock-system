"""動能篩選器模組 — 依序過濾低品質標的，保留強勢股。"""

from __future__ import annotations

from typing import Dict

import pandas as pd

from app.services.technical_indicators import calculate_ma, calculate_return

MIN_PRICE = 20
MIN_VOLUME = 1000
MA_SHORT = 20
MA_LONG = 60
RETURN_PERIOD = 10


def initial_filter(
    stocks_data: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    """篩選收盤價 > 20 且成交量 > 1000 的股票。"""
    result: Dict[str, pd.DataFrame] = {}
    for stock_id, df in stocks_data.items():
        if df.empty:
            continue
        latest = df.iloc[-1]
        if latest["Close"] > MIN_PRICE and latest["Volume"] > MIN_VOLUME:
            result[stock_id] = df
    return result


def trend_filter(
    stocks_data: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    """篩選 MA20 > MA60 的股票（短期均線在長期均線之上）。"""
    result: Dict[str, pd.DataFrame] = {}
    for stock_id, df in stocks_data.items():
        if len(df) < MA_LONG:
            continue
        ma_short = calculate_ma(df["Close"], MA_SHORT)
        ma_long = calculate_ma(df["Close"], MA_LONG)
        if pd.notna(ma_short.iloc[-1]) and pd.notna(ma_long.iloc[-1]):
            if ma_short.iloc[-1] > ma_long.iloc[-1]:
                result[stock_id] = df
    return result


def relative_strength_filter(
    stocks_data: Dict[str, pd.DataFrame],
    market_df: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """篩選個股 10 日報酬 > 大盤 10 日報酬的股票。"""
    market_return = calculate_return(market_df["Close"], RETURN_PERIOD)
    result: Dict[str, pd.DataFrame] = {}
    for stock_id, df in stocks_data.items():
        stock_return = calculate_return(df["Close"], RETURN_PERIOD)
        if stock_return > market_return:
            result[stock_id] = df
    return result


def run_all_filters(
    stocks_data: Dict[str, pd.DataFrame],
    market_df: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """依序執行所有篩選器，回傳最終通過的股票。"""
    filtered = initial_filter(stocks_data)
    filtered = trend_filter(filtered)
    filtered = relative_strength_filter(filtered, market_df)
    return filtered
