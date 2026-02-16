"""Fundamental analysis scoring service."""
import logging
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.revenue import Revenue
from app.models.financial import Financial
from app.models.stock import Stock

logger = logging.getLogger(__name__)


class FundamentalScorer:
    """Calculate fundamental analysis score for stocks."""

    def score(self, db: Session, stock_id: str) -> dict:
        """
        Calculate fundamental score (0-100).

        When financial data unavailable (TWSE quarterly not yet published),
        revenue-based scoring gets higher weight to avoid 0 scores.

        Args:
            db: Database session
            stock_id: Stock ID to score

        Returns:
            Dict with fundamental_score (0-100) and details
        """
        try:
            # Get revenue data (latest available)
            revenue_data = (
                db.query(Revenue)
                .filter(Revenue.stock_id == stock_id)
                .order_by(Revenue.revenue_date.desc())
                .limit(3)
                .all()
            )

            # Get financial data (latest available)
            financial_data = (
                db.query(Financial)
                .filter(Financial.stock_id == stock_id)
                .order_by(Financial.report_date.desc())
                .limit(4)
                .all()
            )

            # Get stock PER/PBR from Stock table (TWSE bulk data)
            stock = db.query(Stock).filter_by(stock_id=stock_id).first()

            if not revenue_data and not financial_data:
                # Use PER/PBR/Dividend yield as fallback
                if stock and (stock.per or stock.pbr or stock.dividend_yield):
                    return self._score_from_valuation(stock)
                logger.warning(f"No fundamental data for {stock_id}")
                return {"fundamental_score": 0.0, "details": {"error": "No data"}}

            has_financial = len(financial_data) > 0

            if has_financial:
                # Full scoring with all data
                revenue_score = self._calculate_revenue_score(revenue_data) * 0.20
                eps_score = self._calculate_eps_score(financial_data) * 0.15
                margin_score = self._calculate_margin_score(financial_data) * 0.10
                roe_score = self._calculate_roe_score(financial_data) * 0.15
                debt_score = self._calculate_debt_score(financial_data) * 0.15
                cashflow_score = self._calculate_cashflow_score(financial_data) * 0.15
                pe_score = self._calculate_pe_score(financial_data) * 0.10
            else:
                # Revenue-only: revenue gets 60% weight, rest neutral at 50
                revenue_score = self._calculate_revenue_score(revenue_data) * 0.60
                eps_score = 50.0 * 0.10
                margin_score = 50.0 * 0.05
                roe_score = 50.0 * 0.05
                debt_score = 50.0 * 0.05
                cashflow_score = 50.0 * 0.05
                pe_score = 50.0 * 0.10

            fundamental_score = (
                revenue_score + eps_score + margin_score +
                roe_score + debt_score + cashflow_score + pe_score
            )

            rev_raw = revenue_score / (0.60 if not has_financial else 0.20) if revenue_data else 0
            details = {
                "revenue_score": round(rev_raw, 2),
                "has_financial": has_financial,
            }

            logger.info(f"Fundamental score for {stock_id}: {fundamental_score:.2f}")

            return {
                "fundamental_score": round(fundamental_score, 2),
                "details": details
            }

        except Exception as e:
            logger.error(f"Error calculating fundamental score for {stock_id}: {e}")
            return {"fundamental_score": 0.0, "details": {"error": str(e)}}

    def _calculate_revenue_score(self, data: list) -> float:
        """Calculate revenue score based on YoY or MoM trend."""
        if not data:
            return 0.0

        # Check if YoY data available (non-zero)
        yoy_values = [float(d.revenue_yoy) for d in data if d.revenue_yoy and float(d.revenue_yoy) != 0]

        if yoy_values:
            avg_yoy = sum(yoy_values) / len(yoy_values)
            if avg_yoy >= 20:
                return 100
            elif avg_yoy >= 10:
                return 80
            elif avg_yoy >= 5:
                return 60
            elif avg_yoy >= 0:
                return 40
            elif avg_yoy >= -5:
                return 20
            return 0

        # Fallback: revenue trend (MoM from raw revenue values)
        if len(data) >= 2:
            revenues = [int(d.revenue) for d in data]
            # data is desc order: [latest, prev, ...]
            latest, prev = revenues[0], revenues[1]
            if prev > 0:
                mom = ((latest - prev) / prev) * 100
                if mom >= 10:
                    return 85
                elif mom >= 5:
                    return 70
                elif mom >= 0:
                    return 55
                elif mom >= -5:
                    return 35
                return 15

        # Single month data, neutral
        return 50

    def _calculate_eps_score(self, data: list) -> float:
        """Calculate EPS quarterly trend score."""
        if len(data) < 2:
            return 50.0

        # Count quarters with increasing EPS
        increasing_count = 0
        for i in range(len(data) - 1):
            if data[i].eps > data[i + 1].eps:
                increasing_count += 1

        # Score based on trend strength
        ratio = increasing_count / (len(data) - 1)
        return ratio * 100

    def _calculate_margin_score(self, data: list) -> float:
        """Calculate gross margin stability/upward trend score."""
        if not data or not data[0].gross_margin:
            return 50.0

        margins = [float(d.gross_margin) for d in data if d.gross_margin]

        if not margins:
            return 50.0

        # Check stability (low variance)
        avg_margin = sum(margins) / len(margins)
        variance = sum((m - avg_margin) ** 2 for m in margins) / len(margins)
        std_dev = variance ** 0.5

        # Stability score
        stability_score = max(0, 100 - (std_dev * 10))

        # Trend score
        if len(margins) >= 2:
            trend = margins[0] - margins[-1]
            trend_score = 50 + (trend * 5)
        else:
            trend_score = 50

        return (stability_score * 0.6 + trend_score * 0.4)

    def _calculate_roe_score(self, data: list) -> float:
        """Calculate ROE score (>15% bonus, <8% penalty)."""
        if not data or not data[0].roe:
            return 50.0

        latest_roe = float(data[0].roe)

        if latest_roe >= 15:
            return 100
        elif latest_roe >= 12:
            return 80
        elif latest_roe >= 10:
            return 70
        elif latest_roe >= 8:
            return 60
        elif latest_roe >= 5:
            return 40
        elif latest_roe >= 0:
            return 20
        else:
            return 0

    def _calculate_debt_score(self, data: list) -> float:
        """Calculate debt ratio score (<50% bonus, >70% penalty)."""
        if not data or not data[0].debt_ratio:
            return 50.0

        debt_ratio = float(data[0].debt_ratio)

        if debt_ratio < 30:
            return 100
        elif debt_ratio < 50:
            return 80
        elif debt_ratio < 60:
            return 60
        elif debt_ratio < 70:
            return 40
        elif debt_ratio < 80:
            return 20
        else:
            return 0

    def _calculate_cashflow_score(self, data: list) -> float:
        """Calculate cash flow score (operating + free cash flow positive)."""
        if not data:
            return 50.0

        latest = data[0]
        ocf = latest.operating_cash_flow if latest.operating_cash_flow else 0
        fcf = latest.free_cash_flow if latest.free_cash_flow else 0

        score = 0

        # Operating cash flow positive
        if ocf > 0:
            score += 50

        # Free cash flow positive
        if fcf > 0:
            score += 50

        return score

    def _calculate_pe_score(self, data: list) -> float:
        """Calculate P/E ratio score (reasonable range)."""
        if not data or not data[0].eps:
            return 50.0
        return 50.0

    def _score_from_valuation(self, stock) -> dict:
        """Score using PER/PBR/dividend_yield when no revenue/financial data."""
        per = float(stock.per) if stock.per else 0
        pbr = float(stock.pbr) if stock.pbr else 0
        div_yield = float(stock.dividend_yield) if stock.dividend_yield else 0

        # PER score (30%): 10-15 is ideal range
        if per <= 0:
            per_score = 50
        elif per < 10:
            per_score = 80
        elif per < 15:
            per_score = 100
        elif per < 20:
            per_score = 70
        elif per < 30:
            per_score = 50
        else:
            per_score = 30

        # PBR score (30%): <1.5 is value, >3 is expensive
        if pbr <= 0:
            pbr_score = 50
        elif pbr < 1:
            pbr_score = 90
        elif pbr < 1.5:
            pbr_score = 80
        elif pbr < 2:
            pbr_score = 60
        elif pbr < 3:
            pbr_score = 40
        else:
            pbr_score = 20

        # Dividend yield score (40%): higher is better
        if div_yield <= 0:
            div_score = 30
        elif div_yield >= 6:
            div_score = 100
        elif div_yield >= 4:
            div_score = 80
        elif div_yield >= 3:
            div_score = 60
        elif div_yield >= 2:
            div_score = 40
        else:
            div_score = 30

        total = per_score * 0.30 + pbr_score * 0.30 + div_score * 0.40

        return {
            "fundamental_score": round(total, 2),
            "details": {
                "source": "valuation",
                "per": per,
                "pbr": pbr,
                "dividend_yield": div_yield,
            },
        }
