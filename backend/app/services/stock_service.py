"""Stock data service for database queries."""
import logging
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading

logger = logging.getLogger(__name__)


def get_stocks(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> tuple[List[Stock], int]:
    """
    Get paginated stock list with optional search.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records
        search: Optional search term for stock_id or stock_name

    Returns:
        Tuple of (stock list, total count)
    """
    query = db.query(Stock)

    if search:
        query = query.filter(
            or_(
                Stock.stock_id.contains(search),
                Stock.stock_name.contains(search)
            )
        )

    total = query.count()
    stocks = query.offset(skip).limit(limit).all()

    return stocks, total


def get_stock_prices(
    db: Session,
    stock_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[DailyPrice]:
    """
    Get historical price data for a stock.

    Args:
        db: Database session
        stock_id: Stock ID
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of DailyPrice records
    """
    query = db.query(DailyPrice).filter(DailyPrice.stock_id == stock_id)

    if start_date:
        query = query.filter(DailyPrice.trade_date >= start_date)
    if end_date:
        query = query.filter(DailyPrice.trade_date <= end_date)

    return query.order_by(DailyPrice.trade_date.desc()).all()


def get_stock_institutional(
    db: Session,
    stock_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Institutional]:
    """
    Get institutional investor data for a stock.

    Args:
        db: Database session
        stock_id: Stock ID
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of Institutional records
    """
    query = db.query(Institutional).filter(Institutional.stock_id == stock_id)

    if start_date:
        query = query.filter(Institutional.trade_date >= start_date)
    if end_date:
        query = query.filter(Institutional.trade_date <= end_date)

    return query.order_by(Institutional.trade_date.desc()).all()


def get_stock_margin(
    db: Session,
    stock_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[MarginTrading]:
    """
    Get margin trading data for a stock.

    Args:
        db: Database session
        stock_id: Stock ID
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of MarginTrading records
    """
    query = db.query(MarginTrading).filter(MarginTrading.stock_id == stock_id)

    if start_date:
        query = query.filter(MarginTrading.trade_date >= start_date)
    if end_date:
        query = query.filter(MarginTrading.trade_date <= end_date)

    return query.order_by(MarginTrading.trade_date.desc()).all()
