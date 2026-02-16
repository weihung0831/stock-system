"""Chip statistics service for institutional and margin trading trends."""
import logging
from typing import List, Dict, Any
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading

logger = logging.getLogger(__name__)


def get_institutional_trend(
    db: Session,
    days: int = 30,
    end_date: date = None,
    stock_id: str = None
) -> List[Dict[str, Any]]:
    """
    Get institutional investor trading trend aggregated by date.
    If stock_id is provided, returns data for that specific stock only.

    Args:
        db: Database session
        days: Number of days to look back (default 30)
        end_date: End date for the trend (default: today)
        stock_id: Optional stock ID to filter by

    Returns:
        List of daily aggregated institutional trading data
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days)

    logger.info(
        f"Fetching institutional trend from {start_date} to {end_date}"
        f"{f' for stock {stock_id}' if stock_id else ''}"
    )

    # Query aggregated data grouped by trade_date
    query = db.query(
        Institutional.trade_date,
        func.sum(Institutional.foreign_net).label('total_foreign_net'),
        func.sum(Institutional.trust_net).label('total_trust_net'),
        func.sum(Institutional.dealer_net).label('total_dealer_net'),
        func.sum(Institutional.total_net).label('total_net')
    ).filter(
        Institutional.trade_date >= start_date,
        Institutional.trade_date <= end_date
    )

    if stock_id:
        query = query.filter(Institutional.stock_id == stock_id)

    results = query.group_by(
        Institutional.trade_date
    ).order_by(
        Institutional.trade_date.asc()
    ).all()

    logger.info(f"Found {len(results)} days of institutional data")

    # Format results
    output = []
    for row in results:
        output.append({
            "trade_date": row.trade_date.isoformat(),
            "foreign_net": int(row.total_foreign_net) if row.total_foreign_net else 0,
            "trust_net": int(row.total_trust_net) if row.total_trust_net else 0,
            "dealer_net": int(row.total_dealer_net) if row.total_dealer_net else 0,
            "total_net": int(row.total_net) if row.total_net else 0,
        })

    return output


def get_margin_trend(
    db: Session,
    days: int = 30,
    end_date: date = None,
    stock_id: str = None
) -> List[Dict[str, Any]]:
    """
    Get margin trading and short selling trend aggregated by date.
    If stock_id is provided, returns data for that specific stock only.

    Args:
        db: Database session
        days: Number of days to look back (default 30)
        end_date: End date for the trend (default: today)
        stock_id: Optional stock ID to filter by

    Returns:
        List of daily aggregated margin trading data
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days)

    logger.info(
        f"Fetching margin trend from {start_date} to {end_date}"
        f"{f' for stock {stock_id}' if stock_id else ''}"
    )

    # Query aggregated data grouped by trade_date
    query = db.query(
        MarginTrading.trade_date,
        func.sum(MarginTrading.margin_balance).label('total_margin_balance'),
        func.sum(MarginTrading.margin_change).label('total_margin_change'),
        func.sum(MarginTrading.short_balance).label('total_short_balance'),
        func.sum(MarginTrading.short_change).label('total_short_change')
    ).filter(
        MarginTrading.trade_date >= start_date,
        MarginTrading.trade_date <= end_date
    )

    if stock_id:
        query = query.filter(MarginTrading.stock_id == stock_id)

    results = query.group_by(
        MarginTrading.trade_date
    ).order_by(
        MarginTrading.trade_date.asc()
    ).all()

    logger.info(f"Found {len(results)} days of margin data")

    # Format results
    output = []
    for row in results:
        output.append({
            "trade_date": row.trade_date.isoformat(),
            "margin_balance": int(row.total_margin_balance) if row.total_margin_balance else 0,
            "margin_change": int(row.total_margin_change) if row.total_margin_change else 0,
            "short_balance": int(row.total_short_balance) if row.total_short_balance else 0,
            "short_change": int(row.total_short_change) if row.total_short_change else 0,
        })

    return output
