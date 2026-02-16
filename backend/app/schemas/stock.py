"""Stock-related schemas."""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class StockResponse(BaseModel):
    """Stock basic information response."""

    id: int
    stock_id: str
    stock_name: str
    market: str
    industry: Optional[str] = None
    listed_date: Optional[date] = None

    class Config:
        from_attributes = True


class StockListResponse(BaseModel):
    """Stock list response with pagination."""

    items: List[StockResponse]
    total: int
    skip: int
    limit: int


class DailyPriceResponse(BaseModel):
    """Daily price data response."""

    id: int
    stock_id: str
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    turnover: Optional[int] = None
    change_price: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None

    class Config:
        from_attributes = True


class InstitutionalResponse(BaseModel):
    """Institutional investor data response."""

    id: int
    stock_id: str
    trade_date: date
    foreign_buy: int
    foreign_sell: int
    foreign_net: int
    trust_buy: int
    trust_sell: int
    trust_net: int
    dealer_buy: int
    dealer_sell: int
    dealer_net: int
    total_net: int

    class Config:
        from_attributes = True


class MarginTradingResponse(BaseModel):
    """Margin trading data response."""

    id: int
    stock_id: str
    trade_date: date
    margin_buy: int
    margin_sell: int
    margin_balance: int
    margin_change: int
    short_buy: int
    short_sell: int
    short_balance: int
    short_change: int

    class Config:
        from_attributes = True
