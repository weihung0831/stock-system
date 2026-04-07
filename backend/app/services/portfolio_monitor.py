"""Portfolio monitoring service for real-time data and target alerts."""
import logging
from datetime import date
from typing import List, Dict, Any, Optional

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.notification import Notification
from app.models.daily_price import DailyPrice
from app.models.score_result import ScoreResult
from app.services.fugle_client import get_quotes, is_market_open, is_quote_available, QuoteData

logger = logging.getLogger(__name__)


def _get_fallback_prices(db: Session, stock_ids: List[str]) -> Dict[str, float]:
    """Get latest closing prices from DB as fallback (batch query)."""
    from sqlalchemy import func

    subq = (
        db.query(
            DailyPrice.stock_id,
            func.max(DailyPrice.trade_date).label("max_date"),
        )
        .filter(DailyPrice.stock_id.in_(stock_ids))
        .group_by(DailyPrice.stock_id)
        .subquery()
    )
    rows = (
        db.query(DailyPrice.stock_id, DailyPrice.close)
        .join(subq, (DailyPrice.stock_id == subq.c.stock_id) & (DailyPrice.trade_date == subq.c.max_date))
        .all()
    )
    return {row.stock_id: float(row.close) for row in rows}


def _get_current_momentum_grades(db: Session, stock_ids: List[str]) -> Dict[str, Optional[str]]:
    """Get the latest momentum classification for each stock (batch query)."""
    from sqlalchemy import func

    subq = (
        db.query(
            ScoreResult.stock_id,
            func.max(ScoreResult.score_date).label("max_date"),
        )
        .filter(ScoreResult.stock_id.in_(stock_ids))
        .group_by(ScoreResult.stock_id)
        .subquery()
    )
    rows = (
        db.query(ScoreResult.stock_id, ScoreResult.classification)
        .join(subq, (ScoreResult.stock_id == subq.c.stock_id) & (ScoreResult.score_date == subq.c.max_date))
        .all()
    )
    grades = {row.stock_id: row.classification for row in rows}
    for sid in stock_ids:
        grades.setdefault(sid, None)
    return grades


def _momentum_status(entry_grade: Optional[str], current_grade: Optional[str]) -> str:
    """Compare entry vs current momentum grade. Returns green/yellow/red."""
    if not entry_grade or not current_grade:
        return "unknown"
    grade_order = {"A": 0, "B": 1, "C": 2, "D": 3}
    entry_val = grade_order.get(entry_grade, 4)
    current_val = grade_order.get(current_grade, 4)
    diff = current_val - entry_val
    if diff <= 0:
        return "green"
    elif diff == 1:
        return "yellow"
    else:
        return "red"


def _check_and_notify(
    db: Session, portfolio: Portfolio, profit_pct: float
) -> Optional[Dict[str, Any]]:
    """Check if target reached and create notification if needed."""
    if profit_pct < portfolio.target_return_pct:
        return None

    today = date.today()
    notification = Notification(
        user_id=portfolio.user_id,
        portfolio_id=portfolio.id,
        type="target_reached",
        title=f"{portfolio.stock_name}({portfolio.stock_id}) 達標",
        message=f"報酬率 {profit_pct:.1f}% 已達目標 {portfolio.target_return_pct:.1f}%",
        created_date=today,
    )
    try:
        db.add(notification)
        db.commit()
        return {
            "portfolio_id": portfolio.id,
            "stock_id": portfolio.stock_id,
            "stock_name": portfolio.stock_name,
            "profit_pct": profit_pct,
            "target_return_pct": portfolio.target_return_pct,
        }
    except IntegrityError:
        db.rollback()
        return None


def get_realtime_data(user_id: int, db: Session) -> Dict[str, Any]:
    """Get real-time portfolio data with profit calculations and target checks."""
    portfolios = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .all()
    )

    if not portfolios:
        return {
            "is_market_open": is_market_open(),
            "is_realtime": False,
            "total_profit_amount": 0,
            "total_profit_pct": 0,
            "items": [],
            "new_alerts": [],
        }

    stock_ids = list({p.stock_id for p in portfolios})
    market_open = is_market_open()

    quotes = get_quotes(stock_ids) if is_quote_available() else {}
    any_realtime = any(q is not None for q in quotes.values())

    fallback_prices = {}
    if not any_realtime:
        fallback_prices = _get_fallback_prices(db, stock_ids)

    momentum_grades = _get_current_momentum_grades(db, stock_ids)

    items = []
    total_profit = 0.0
    total_cost = 0.0
    new_alerts = []

    for p in portfolios:
        quote = quotes.get(p.stock_id)
        if quote:
            current_price = quote.price
            is_realtime = True
        elif p.stock_id in fallback_prices:
            current_price = fallback_prices[p.stock_id]
            is_realtime = False
        else:
            current_price = p.cost_price
            is_realtime = False

        profit_amount = (current_price - p.cost_price) * p.quantity
        profit_pct = ((current_price - p.cost_price) / p.cost_price * 100) if p.cost_price > 0 else 0
        target_reached = profit_pct >= p.target_return_pct

        total_profit += profit_amount
        total_cost += p.cost_price * p.quantity

        current_momentum = momentum_grades.get(p.stock_id)

        if target_reached and is_realtime:
            alert = _check_and_notify(db, p, profit_pct)
            if alert:
                new_alerts.append(alert)

        items.append({
            "portfolio_id": p.id,
            "stock_id": p.stock_id,
            "stock_name": p.stock_name,
            "cost_price": p.cost_price,
            "current_price": current_price,
            "quantity": p.quantity,
            "profit_amount": round(profit_amount, 0),
            "profit_pct": round(profit_pct, 2),
            "target_return_pct": p.target_return_pct,
            "target_reached": target_reached,
            "is_realtime": is_realtime,
            "entry_momentum_grade": p.entry_momentum_grade,
            "current_momentum_grade": current_momentum,
            "momentum_status": _momentum_status(p.entry_momentum_grade, current_momentum),
        })

    total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0

    return {
        "is_market_open": market_open,
        "is_realtime": any_realtime,
        "total_profit_amount": round(total_profit, 0),
        "total_profit_pct": round(total_profit_pct, 2),
        "items": items,
        "new_alerts": new_alerts,
    }
