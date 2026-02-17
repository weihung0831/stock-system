"""Stock data endpoints."""
import logging
from typing import Annotated, Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.stock import (
    StockResponse,
    StockListResponse,
    DailyPriceResponse,
    InstitutionalResponse,
    MarginTradingResponse
)
from app.services.stock_service import (
    get_stocks,
    get_stock_prices,
    get_stock_institutional,
    get_stock_margin
)
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("", response_model=StockListResponse)
def list_stocks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    search: Optional[str] = Query(default=None)
):
    """
    Get paginated stock list with optional search.

    Args:
        db: Database session
        current_user: Authenticated user
        skip: Number of records to skip
        limit: Maximum number of records
        search: Optional search term

    Returns:
        Paginated stock list
    """
    stocks, total = get_stocks(db, skip=skip, limit=limit, search=search)

    return StockListResponse(
        items=stocks,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{stock_id}/prices", response_model=List[DailyPriceResponse])
def get_stock_price_history(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None)
):
    """
    Get historical price data for a stock.

    Args:
        stock_id: Stock ID
        db: Database session
        current_user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of daily price records
    """
    prices = get_stock_prices(db, stock_id, start_date, end_date)
    return prices


@router.get("/{stock_id}/institutional", response_model=List[InstitutionalResponse])
def get_stock_institutional_data(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None)
):
    """
    Get institutional investor data for a stock.

    Args:
        stock_id: Stock ID
        db: Database session
        current_user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of institutional investor records
    """
    data = get_stock_institutional(db, stock_id, start_date, end_date)
    return data


@router.get("/{stock_id}/margin", response_model=List[MarginTradingResponse])
def get_stock_margin_data(
    stock_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None)
):
    """
    Get margin trading data for a stock.

    Args:
        stock_id: Stock ID
        db: Database session
        current_user: Authenticated user
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of margin trading records
    """
    data = get_stock_margin(db, stock_id, start_date, end_date)
    return data
