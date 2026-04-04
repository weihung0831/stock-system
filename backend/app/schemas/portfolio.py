"""Portfolio-related schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class PortfolioCreate(BaseModel):
    """Create a new portfolio holding."""
    stock_id: str = Field(..., max_length=10)
    cost_price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    target_return_pct: float = Field(..., gt=0)


class PortfolioUpdate(BaseModel):
    """Update an existing portfolio holding."""
    cost_price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0)
    target_return_pct: Optional[float] = Field(None, gt=0)


class PortfolioResponse(BaseModel):
    """Portfolio holding response."""
    id: int
    stock_id: str
    stock_name: str
    cost_price: float
    quantity: int
    target_return_pct: float
    entry_momentum_grade: Optional[str] = None

    model_config = {"from_attributes": True}


class RealtimeItem(BaseModel):
    """Single portfolio item with real-time data."""
    portfolio_id: int
    stock_id: str
    stock_name: str
    cost_price: float
    current_price: float
    quantity: int
    profit_amount: float
    profit_pct: float
    target_return_pct: float
    target_reached: bool
    is_realtime: bool
    entry_momentum_grade: Optional[str] = None
    current_momentum_grade: Optional[str] = None
    momentum_status: str = "unknown"


class AlertItem(BaseModel):
    """New alert triggered during this request."""
    portfolio_id: int
    stock_id: str
    stock_name: str
    profit_pct: float
    target_return_pct: float


class RealtimeResponse(BaseModel):
    """Real-time portfolio data response."""
    is_market_open: bool
    is_realtime: bool
    total_profit_amount: float
    total_profit_pct: float
    items: List[RealtimeItem]
    new_alerts: List[AlertItem] = []
