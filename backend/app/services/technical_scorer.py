"""Technical analysis scoring service using pure pandas."""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from app.models.daily_price import DailyPrice

logger = logging.getLogger(__name__)


class TechnicalScorer:
    """Calculate technical analysis score for stocks using pandas-ta."""

    def score(self, db: Session, stock_id: str, as_of_date: date = None) -> dict:
        """
        Calculate technical score using pandas-ta.

        Load 120 days of daily price data into DataFrame, then:

        Indicators (weighted sum, normalize to 0-100):
        A. MA alignment: MA5>MA10>MA20>MA60>MA120 = full score (20%)
        B. KD golden cross / low zone consolidation (15%)
        C. MACD histogram turns positive / DIF crosses above MACD (20%)
        D. RSI 50-70 bonus, >80 overbought penalty (15%)
        E. Price above BB middle band bonus (15%)
        F. Volume > MA20 volume bonus (15%)

        Args:
            db: Database session
            stock_id: Stock ID to score

        Returns:
            Dict with technical_score (0-100) and details
        """
        try:
            # Get 120 days of price data relative to as_of_date
            ref_date = as_of_date or date.today()
            cutoff_date = ref_date - timedelta(days=180)

            query = db.query(DailyPrice).filter(
                DailyPrice.stock_id == stock_id,
                DailyPrice.trade_date >= cutoff_date,
            )
            if as_of_date:
                query = query.filter(DailyPrice.trade_date <= as_of_date)

            price_data = (
                query.order_by(DailyPrice.trade_date.asc())
                .all()
            )

            data_days = len(price_data)
            if data_days < 20:
                logger.warning(f"Insufficient price data for {stock_id}: {data_days} days (need 20+)")
                return {"technical_score": 0.0, "details": {"error": "Insufficient data"}}

            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'date': p.trade_date,
                    'open': float(p.open),
                    'high': float(p.high),
                    'low': float(p.low),
                    'close': float(p.close),
                    'volume': int(p.volume)
                }
                for p in price_data
            ])

            df.set_index('date', inplace=True)

            # Calculate indicators (adaptive to available data)
            ma_score = self._calculate_ma_score(df, data_days) * 0.20
            kd_score = self._calculate_kd_score(df) * 0.15
            macd_score = self._calculate_macd_score(df, data_days) * 0.20
            rsi_score = self._calculate_rsi_score(df) * 0.15
            bb_score = self._calculate_bb_score(df) * 0.15
            volume_score = self._calculate_volume_score(df) * 0.15

            # Weighted composite
            technical_score = (
                ma_score + kd_score + macd_score +
                rsi_score + bb_score + volume_score
            )

            details = {
                "ma_score": round(ma_score / 0.20, 2),
                "kd_score": round(kd_score / 0.15, 2),
                "macd_score": round(macd_score / 0.20, 2),
                "rsi_score": round(rsi_score / 0.15, 2),
                "bb_score": round(bb_score / 0.15, 2),
                "volume_score": round(volume_score / 0.15, 2),
            }

            logger.info(f"Technical score for {stock_id}: {technical_score:.2f}")

            return {
                "technical_score": round(technical_score, 2),
                "details": details
            }

        except Exception as e:
            logger.error(f"Error calculating technical score for {stock_id}: {e}")
            return {"technical_score": 0.0, "details": {"error": str(e)}}

    def _calculate_ma_score(self, df: pd.DataFrame, data_days: int = 120) -> float:
        """Calculate MA alignment score, adaptive to available data."""
        try:
            # Calculate moving averages based on available data
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()

            latest = df.iloc[-1]
            # Build comparison pairs based on available data
            pairs = [('ma5', 'ma10'), ('ma10', 'ma20')]
            if data_days >= 60:
                df['ma60'] = df['close'].rolling(window=60).mean()
                pairs.append(('ma20', 'ma60'))
            if data_days >= 120:
                df['ma120'] = df['close'].rolling(window=120).mean()
                pairs.append(('ma60', 'ma120'))

            latest = df.iloc[-1]
            alignment_count = 0
            for fast, slow in pairs:
                if not pd.isna(latest.get(fast)) and not pd.isna(latest.get(slow)):
                    if latest[fast] > latest[slow]:
                        alignment_count += 1

            return (alignment_count / len(pairs)) * 100 if pairs else 50.0

        except Exception as e:
            logger.error(f"Error calculating MA score: {e}")
            return 0.0

    def _calculate_kd_score(self, df: pd.DataFrame) -> float:
        """Calculate KD stochastic score (golden cross / low zone).

        Uses industry-standard smoothed KD formula:
        RSV = (close - 9日最低) / (9日最高 - 9日最低) * 100
        K = 2/3 * 前日K + 1/3 * RSV
        D = 2/3 * 前日D + 1/3 * K
        """
        try:
            # Calculate RSV (Raw Stochastic Value)
            low_min = df['low'].rolling(window=9).min()
            high_max = df['high'].rolling(window=9).max()
            rsv = 100 * (df['close'] - low_min) / (high_max - low_min)

            # Smoothed K and D (industry standard, matches frontend)
            k_values = pd.Series(np.nan, index=df.index)
            d_values = pd.Series(np.nan, index=df.index)

            first_valid = rsv.first_valid_index()
            if first_valid is None:
                return 50.0

            # Initialize K=50, D=50 as standard convention
            k_values.loc[first_valid] = (2/3) * 50 + (1/3) * rsv.loc[first_valid]
            d_values.loc[first_valid] = (2/3) * 50 + (1/3) * k_values.loc[first_valid]

            # Iterate to compute smoothed values
            indices = df.index.tolist()
            start_idx = indices.index(first_valid)
            for i in range(start_idx + 1, len(indices)):
                curr = indices[i]
                prev = indices[i - 1]
                if pd.isna(rsv.loc[curr]):
                    continue
                k_values.loc[curr] = (2/3) * k_values.loc[prev] + (1/3) * rsv.loc[curr]
                d_values.loc[curr] = (2/3) * d_values.loc[prev] + (1/3) * k_values.loc[curr]

            latest_k = k_values.iloc[-1]
            latest_d = d_values.iloc[-1]

            if pd.isna(latest_k) or pd.isna(latest_d):
                return 50.0

            # Check for golden cross (K crosses above D)
            if len(k_values) >= 2:
                prev_k = k_values.iloc[-2]
                prev_d = d_values.iloc[-2]

                if not pd.isna(prev_k) and not pd.isna(prev_d):
                    if latest_k > latest_d and prev_k <= prev_d and latest_k < 30:
                        return 100
                    elif latest_k > latest_d and prev_k <= prev_d:
                        return 80

            # K and D in low zone (20-40)
            if 20 <= latest_k <= 40 and 20 <= latest_d <= 40:
                return 70

            # Normal range
            if 20 <= latest_k <= 80:
                return 50

            # Overbought
            return 30

        except Exception as e:
            logger.error(f"Error calculating KD score: {e}")
            return 50.0

    def _calculate_macd_score(self, df: pd.DataFrame, data_days: int = 120) -> float:
        """Calculate MACD score (histogram positive / DIF crosses MACD)."""
        try:
            # MACD needs at least 35 days (26-day EMA + 9-day signal)
            if data_days < 35:
                return 50.0  # Neutral when insufficient data
            # Calculate MACD manually
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line

            latest_macd = macd_line.iloc[-1]
            latest_signal = signal_line.iloc[-1]
            latest_hist = histogram.iloc[-1]

            if pd.isna(latest_hist):
                return 50.0

            # Histogram turning positive
            if latest_hist > 0:
                score = 70

                # DIF crosses above MACD
                if len(macd_line) >= 2:
                    prev_macd = macd_line.iloc[-2]
                    prev_signal = signal_line.iloc[-2]

                    if latest_macd > latest_signal and prev_macd <= prev_signal:
                        score = 100

                return score
            else:
                return 30

        except Exception as e:
            logger.error(f"Error calculating MACD score: {e}")
            return 50.0

    def _calculate_rsi_score(self, df: pd.DataFrame) -> float:
        """Calculate RSI score (50-70 bonus, >80 overbought penalty)."""
        try:
            # Calculate RSI manually
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            if rsi.empty:
                return 50.0

            latest_rsi = rsi.iloc[-1]

            if pd.isna(latest_rsi):
                return 50.0

            # Score mapping
            if 50 <= latest_rsi <= 70:
                return 100
            elif 40 <= latest_rsi < 50:
                return 80
            elif 30 <= latest_rsi < 40:
                return 60
            elif latest_rsi > 80:
                return 20  # Overbought penalty
            elif latest_rsi < 30:
                return 40  # Oversold
            else:
                return 50

        except Exception as e:
            logger.error(f"Error calculating RSI score: {e}")
            return 50.0

    def _calculate_bb_score(self, df: pd.DataFrame) -> float:
        """Calculate Bollinger Bands score using %B position.

        Bollinger Bands (20-day, 2 standard deviations):
        Middle = SMA(20)
        Upper = Middle + 2 * std(20)
        Lower = Middle - 2 * std(20)
        %B = (close - Lower) / (Upper - Lower)

        %B interpretation:
        >1.0 = above upper band (極強或過熱)
        0.5-1.0 = upper half (偏多)
        0.0-0.5 = lower half (偏空)
        <0.0 = below lower band (極弱或超跌)
        """
        try:
            middle = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            upper = middle + 2 * std
            lower = middle - 2 * std

            latest_close = df.iloc[-1]['close']
            latest_upper = upper.iloc[-1]
            latest_lower = lower.iloc[-1]
            latest_middle = middle.iloc[-1]

            if pd.isna(latest_middle) or pd.isna(latest_upper):
                return 50.0

            band_width = latest_upper - latest_lower
            if band_width == 0:
                return 50.0

            # %B = (close - lower) / (upper - lower)
            percent_b = (latest_close - latest_lower) / band_width

            # Score mapping based on %B position
            if percent_b >= 1.0:
                return 70   # 突破上軌，強勢但可能過熱
            elif percent_b >= 0.8:
                return 100  # 上軌附近，強勢趨勢
            elif percent_b >= 0.5:
                return 80   # 中軌以上，偏多
            elif percent_b >= 0.2:
                return 40   # 中軌以下，偏空
            elif percent_b >= 0.0:
                return 20   # 下軌附近，弱勢
            else:
                return 30   # 跌破下軌，極弱但可能超跌反彈

        except Exception as e:
            logger.error(f"Error calculating BB score: {e}")
            return 50.0

    def _calculate_volume_score(self, df: pd.DataFrame) -> float:
        """Calculate volume score (volume > MA20 volume)."""
        try:
            # Calculate 20-day average volume
            df['volume_ma20'] = df['volume'].rolling(window=20).mean()

            latest_volume = df.iloc[-1]['volume']
            latest_volume_ma = df.iloc[-1]['volume_ma20']

            if pd.isna(latest_volume_ma) or latest_volume_ma == 0:
                return 50.0

            # Volume ratio
            volume_ratio = latest_volume / latest_volume_ma

            if volume_ratio >= 1.5:
                return 100
            elif volume_ratio >= 1.2:
                return 80
            elif volume_ratio >= 1.0:
                return 60
            else:
                return 40

        except Exception as e:
            logger.error(f"Error calculating volume score: {e}")
            return 50.0
