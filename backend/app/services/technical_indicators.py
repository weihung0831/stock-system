"""技術指標純函式模組 — 無副作用、無 DB 存取。"""
import pandas as pd
import numpy as np


def calculate_ma(closes: pd.Series, period: int) -> pd.Series:
    """計算簡單移動平均線。"""
    return closes.rolling(window=period).mean()


def calculate_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """計算 RSI，使用 Wilder 平滑法（EWM alpha=1/period）。"""
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """計算 Average True Range (ATR)，使用 Wilder 平滑。"""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return atr


def calculate_adx(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """計算 ADX（Wilder 方向運動系統）。

    平滑因子 1/period，初始值用前 period 期簡單平均。
    """
    prev_high = high.shift(1)
    prev_low = low.shift(1)

    plus_dm = (high - prev_high).where((high - prev_high) > (prev_low - low), 0.0)
    plus_dm = plus_dm.where(plus_dm > 0, 0.0)
    minus_dm = (prev_low - low).where((prev_low - low) > (high - prev_high), 0.0)
    minus_dm = minus_dm.where(minus_dm > 0, 0.0)

    atr = calculate_atr(high, low, close, period)

    smooth_plus = plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    smooth_minus = minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    plus_di = 100 * smooth_plus / atr
    minus_di = 100 * smooth_minus / atr

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return adx


def calculate_rs(stock_returns: float, market_returns: float) -> float:
    """計算相對強度。market_returns <= 0 時改用差值法。"""
    if market_returns <= 0:
        return stock_returns - market_returns
    return stock_returns / market_returns


def calculate_return(closes: pd.Series, period: int = 20) -> float:
    """計算 N 日報酬率 (%)。資料不足時回傳 0.0。"""
    if len(closes) < period + 1:
        return 0.0
    start = closes.iloc[-(period + 1)]
    end = closes.iloc[-1]
    if start == 0:
        return 0.0
    return ((end - start) / start) * 100
