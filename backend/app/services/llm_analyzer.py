"""LLM-based stock analysis orchestrator."""
import json
import logging
import time
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading
from app.models.financial import Financial
from app.models.revenue import Revenue
from app.models.llm_report import LLMReport
from app.services.llm_client import LLMClient
from app.services.news_preparator import NewsPreparator
from app.services.right_side_signal_detector import RightSideSignalDetector
from app.services.prompt_templates import (
    SYSTEM_PROMPT,
    RESPONSE_SCHEMA,
    build_analysis_prompt
)

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """Orchestrates LLM analysis for stocks."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize LLM analyzer.

        Args:
            llm_client: LLM API client instance
        """
        self.llm = llm_client
        self.news_prep = NewsPreparator()
        self.rate_limit_delay = 0.5  # Seconds between API calls

    def analyze_stock(
        self,
        db: Session,
        stock_id: str,
        score_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate LLM analysis for a single stock.

        Args:
            db: Database session
            stock_id: Stock ticker (e.g., "2330")
            score_data: Scoring data with chip/fundamental/technical scores

        Returns:
            Report dict or None on failure
        """
        try:
            logger.info(f"Starting LLM analysis for {stock_id}")

            # Get stock info
            stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
            if not stock:
                logger.error(f"Stock {stock_id} not found in database")
                return None

            # Gather all data
            stock_data = self._gather_stock_data(db, stock_id)

            # Prepare news summary (14 days to cover holidays/weekends)
            news_text = self.news_prep.prepare_stock_news(db, stock_id, days=14)

            # Build prompt
            prompt = build_analysis_prompt(
                stock_id=stock_id,
                stock_name=stock.stock_name,
                chip_data=stock_data['chip'],
                fundamental_data=stock_data['fundamental'],
                technical_data=stock_data['technical'],
                right_side_data=stock_data['right_side'],
                news_text=news_text,
                scores=score_data
            )

            # Call LLM
            result = self.llm.generate_structured(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                response_schema=RESPONSE_SCHEMA
            )

            if not result:
                logger.error(f"LLM API failed for {stock_id}")
                return None

            # Normalize confidence to one of: 高/中/低
            result['confidence'] = self._normalize_confidence(result.get('confidence', '中'))

            # Normalize news_sentiment to one of: 正面/中性/負面
            result['news_sentiment'] = self._normalize_sentiment(result.get('news_sentiment', '中性'))

            # Ensure risk_alerts is a list
            if isinstance(result.get('risk_alerts'), str):
                result['risk_alerts'] = [result['risk_alerts']]

            # Use latest trading date from DB instead of today
            max_date = db.query(func.max(DailyPrice.trade_date)).scalar()
            report_date = max_date if max_date else date.today()

            # Upsert: update if same stock+date exists, else insert
            existing = db.query(LLMReport).filter(
                LLMReport.stock_id == stock_id,
                LLMReport.report_date == report_date
            ).first()

            right_side_text = result.get('right_side_analysis', '')

            if existing:
                existing.chip_analysis = result['chip_analysis']
                existing.fundamental_analysis = result['fundamental_analysis']
                existing.technical_analysis = result['technical_analysis']
                existing.right_side_analysis = right_side_text
                existing.news_sentiment = result['news_sentiment']
                existing.news_summary = result['news_summary']
                existing.risk_alerts = result['risk_alerts']
                existing.recommendation = result['recommendation']
                existing.confidence = result['confidence']
                existing.raw_response = json.dumps(result, ensure_ascii=False)
                existing.model_used = self.llm.model
                report = existing
            else:
                report = LLMReport(
                    stock_id=stock_id,
                    report_date=report_date,
                    chip_analysis=result['chip_analysis'],
                    fundamental_analysis=result['fundamental_analysis'],
                    technical_analysis=result['technical_analysis'],
                    right_side_analysis=right_side_text,
                    news_sentiment=result['news_sentiment'],
                    news_summary=result['news_summary'],
                    risk_alerts=result['risk_alerts'],
                    recommendation=result['recommendation'],
                    confidence=result['confidence'],
                    raw_response=json.dumps(result, ensure_ascii=False),
                    model_used=self.llm.model
                )
                db.add(report)

            db.commit()
            db.refresh(report)

            logger.info(f"LLM analysis saved for {stock_id}")
            return {
                'id': report.id,
                'stock_id': report.stock_id,
                'report_date': report.report_date,
                'recommendation': report.recommendation,
                'confidence': report.confidence
            }

        except Exception as e:
            logger.error(f"Failed to analyze {stock_id}: {e}", exc_info=True)
            db.rollback()
            return None

    @staticmethod
    def _normalize_confidence(raw: str) -> str:
        """Map LLM confidence response to 高/中/低."""
        raw_lower = raw.lower()
        if '高' in raw or 'high' in raw_lower:
            return '高'
        if '低' in raw or 'low' in raw_lower:
            return '低'
        return '中'

    @staticmethod
    def _normalize_sentiment(raw: str) -> str:
        """Map LLM sentiment response to 正面/中性/負面."""
        if '正' in raw or 'positive' in raw.lower():
            return '正面'
        if '負' in raw or 'negative' in raw.lower():
            return '負面'
        return '中性'

    def analyze_batch(
        self,
        db: Session,
        top_stocks: List[Dict[str, Any]],
        max_workers: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze a batch of top-ranked stocks using parallel threads.

        Each worker gets its own DB session to avoid SQLAlchemy thread-safety issues.

        Args:
            db: Database session (unused in parallel mode, kept for API compat)
            top_stocks: List of stock dicts with stock_id and scores
            max_workers: Max concurrent LLM requests (default 5)

        Returns:
            List of successful report dicts
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from app.database import SessionLocal

        results = []
        total = len(top_stocks)

        def _analyze_one(idx: int, stock_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            stock_id = stock_data['stock_id']
            scores = stock_data.get('scores', {})
            logger.info(f"Analyzing {idx + 1}/{total}: {stock_id}")
            thread_db = SessionLocal()
            try:
                return self.analyze_stock(thread_db, stock_id, scores)
            finally:
                thread_db.close()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_analyze_one, idx, sd): sd['stock_id']
                for idx, sd in enumerate(top_stocks)
            }
            for future in as_completed(futures):
                stock_id = futures[future]
                try:
                    report = future.result()
                    if report:
                        results.append(report)
                    else:
                        logger.warning(f"Skipping {stock_id} due to analysis failure")
                except Exception as e:
                    logger.error(f"Thread error for {stock_id}: {e}")

        logger.info(f"Batch analysis complete: {len(results)}/{total} successful")
        return results

    def _gather_stock_data(self, db: Session, stock_id: str) -> Dict[str, Any]:
        """
        Gather all relevant data for prompt building.

        Args:
            db: Database session
            stock_id: Stock ticker

        Returns:
            Dict with chip/fundamental/technical data
        """
        data: Dict[str, Any] = {
            'chip': {},
            'fundamental': {},
            'technical': {},
            'right_side': {}
        }

        try:
            # Use DB max date as reference instead of datetime.now()
            max_date = db.query(func.max(DailyPrice.trade_date)).scalar()
            if not max_date:
                return data
            ref_date = max_date

            # -- Chip: institutional last 10 trading days --
            institutional = (
                db.query(Institutional)
                .filter(Institutional.stock_id == stock_id)
                .order_by(desc(Institutional.trade_date))
                .limit(10)
                .all()
            )

            data['chip']['institutional'] = [
                {
                    'date': inst.trade_date.strftime('%Y-%m-%d'),
                    'foreign_net': inst.foreign_net,
                    'trust_net': inst.trust_net,
                    'dealer_net': inst.dealer_net,
                    'total_net': inst.total_net,
                }
                for inst in institutional
            ]

            # -- Chip: margin trading last 5 days --
            margins = (
                db.query(MarginTrading)
                .filter(MarginTrading.stock_id == stock_id)
                .order_by(desc(MarginTrading.trade_date))
                .limit(5)
                .all()
            )

            data['chip']['margin'] = [
                {
                    'date': m.trade_date.strftime('%Y-%m-%d'),
                    'margin_balance': m.margin_balance,
                    'margin_change': m.margin_change,
                    'short_balance': m.short_balance,
                    'short_change': m.short_change,
                }
                for m in margins
            ] if margins else []

            # -- Fundamental: revenue last 3 months --
            revenues = (
                db.query(Revenue)
                .filter(Revenue.stock_id == stock_id)
                .order_by(desc(Revenue.revenue_date))
                .limit(3)
                .all()
            )

            data['fundamental']['revenue'] = [
                {
                    'month': rev.revenue_date.strftime('%Y-%m'),
                    'yoy': float(rev.revenue_yoy)
                }
                for rev in revenues
            ]

            # -- Fundamental: EPS last 4 quarters --
            financials = (
                db.query(Financial)
                .filter(Financial.stock_id == stock_id)
                .order_by(desc(Financial.report_date))
                .limit(4)
                .all()
            )

            data['fundamental']['eps'] = [
                {
                    'quarter': fin.report_date.strftime('%Y-Q%m'),
                    'eps': float(fin.eps)
                }
                for fin in financials
            ]

            if financials:
                latest = financials[0]
                data['fundamental']['roe'] = float(latest.roe) if latest.roe else 'N/A'
                data['fundamental']['debt_ratio'] = float(latest.debt_ratio) if latest.debt_ratio else 'N/A'
                data['fundamental']['cash_flow'] = int(latest.operating_cash_flow / 100000000) if latest.operating_cash_flow else 'N/A'

            # -- Technical: prices for indicator calculation --
            prices = (
                db.query(DailyPrice)
                .filter(DailyPrice.stock_id == stock_id)
                .order_by(desc(DailyPrice.trade_date))
                .limit(120)
                .all()
            )

            if prices:
                latest = prices[0]  # desc order, index 0 = most recent
                data['technical']['close'] = f"{float(latest.close):.2f}"
                data['technical']['volume'] = int(latest.volume)
                data['technical']['trade_date'] = latest.trade_date.strftime('%Y-%m-%d')

                closes = [float(p.close) for p in prices]
                # Moving averages
                for period in [5, 10, 20, 60, 120]:
                    key = f'ma{period}'
                    if len(closes) >= period:
                        data['technical'][key] = f"{sum(closes[:period]) / period:.2f}"
                    else:
                        data['technical'][key] = 'N/A'

                # KD (9-period stochastic)
                if len(prices) >= 9:
                    data['technical'].update(self._calc_kd(prices))
                else:
                    data['technical']['k'] = 'N/A'
                    data['technical']['d'] = 'N/A'

                # RSI (14-period)
                if len(closes) >= 15:
                    data['technical']['rsi'] = f"{self._calc_rsi(closes, 14):.2f}"
                else:
                    data['technical']['rsi'] = 'N/A'

                # MACD (12, 26, 9)
                if len(closes) >= 26:
                    data['technical'].update(self._calc_macd(closes))
                else:
                    data['technical']['macd_dif'] = 'N/A'
                    data['technical']['macd'] = 'N/A'

            # -- Right-side signals --
            try:
                detector = RightSideSignalDetector()
                rs = detector.detect(db, stock_id)
                triggered = [
                    s for s in rs.get('signals', []) if s.get('triggered')
                ]
                data['right_side'] = {
                    'score': rs.get('score', 0),
                    'triggered_count': rs.get('triggered_count', 0),
                    'triggered_signals': [
                        {'label': s['label'], 'description': s.get('description', '')}
                        for s in triggered
                    ],
                    'prediction': rs.get('prediction'),
                    'today_breakout': rs.get('today_breakout', False),
                    'weekly_trend_up': rs.get('weekly_trend_up', False),
                    'strong_recommend': rs.get('strong_recommend', False),
                    'risk_level': rs.get('risk_level', 'high'),
                }
            except Exception as e:
                logger.warning(f"Right-side signals failed for {stock_id}: {e}")

        except Exception as e:
            logger.error(f"Error gathering data for {stock_id}: {e}")

        return data

    @staticmethod
    def _calc_kd(prices: list, period: int = 9) -> Dict[str, str]:
        """Calculate latest K and D values."""
        k_val, d_val = 50.0, 50.0
        for i in range(period - 1, len(prices)):
            window = prices[max(0, i - period + 1):i + 1]
            close = float(window[0].close)  # desc order, index 0 = latest in window
            lowest = min(float(p.low) for p in window)
            highest = max(float(p.high) for p in window)
            if highest == lowest:
                rsv = 50.0
            else:
                rsv = ((close - lowest) / (highest - lowest)) * 100
            k_val = (2 / 3) * k_val + (1 / 3) * rsv
            d_val = (2 / 3) * d_val + (1 / 3) * k_val
        return {'k': f"{k_val:.2f}", 'd': f"{d_val:.2f}"}

    @staticmethod
    def _calc_rsi(closes: List[float], period: int = 14) -> float:
        """Calculate latest RSI value. closes[0] = most recent."""
        # Reverse to chronological order for calculation
        c = list(reversed(closes[:period + 1]))
        gains, losses = 0.0, 0.0
        for i in range(1, len(c)):
            change = c[i] - c[i - 1]
            if change > 0:
                gains += change
            else:
                losses += abs(change)
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _calc_macd(closes: List[float]) -> Dict[str, str]:
        """Calculate latest MACD DIF and MACD signal. closes[0] = most recent."""
        # Reverse to chronological order
        c = list(reversed(closes))

        def ema(data: List[float], period: int) -> List[float]:
            result = [data[0]]
            multiplier = 2 / (period + 1)
            for i in range(1, len(data)):
                result.append(data[i] * multiplier + result[-1] * (1 - multiplier))
            return result

        ema12 = ema(c, 12)
        ema26 = ema(c, 26)
        dif_line = [ema12[i] - ema26[i] for i in range(len(ema26))]
        signal = ema(dif_line, 9)
        return {
            'macd_dif': f"{dif_line[-1]:.2f}",
            'macd': f"{signal[-1]:.2f}",
        }
