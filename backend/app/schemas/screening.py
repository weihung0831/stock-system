"""Screening-related schemas."""
from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ScreeningRequest(BaseModel):
    """Stock screening request."""

    threshold: float = Field(
        default=2.5,
        ge=1.0,
        le=10.0,
        description="Volume threshold multiplier for hard filter"
    )


class ScoreResultResponse(BaseModel):
    """Score result response."""

    stock_id: str
    stock_name: Optional[str] = None
    score_date: str
    total_score: float
    momentum_score: float = 0.0
    classification: str = ""
    rank: int
    industry: Optional[str] = None
    close_price: float = 0.0
    change_percent: float = 0.0
    buy_price: Optional[float] = None
    stop_price: Optional[float] = None
    add_price: Optional[float] = None
    target_price: Optional[float] = None
    sector_name: Optional[str] = None
    sector_rank: Optional[int] = None
    market_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SectorRankItem(BaseModel):
    """Sector ranking item."""
    name: str
    return_pct: float = 0.0


class ScreeningResultsResponse(BaseModel):
    """Screening results response."""

    items: List[ScoreResultResponse]
    total: int
    threshold: float
    market_status: Optional[str] = None
    top_sectors: List[SectorRankItem] = []


class ScreeningSettingsResponse(BaseModel):
    """Persisted screening settings."""

    threshold: float


class ScreeningSettingsUpdate(BaseModel):
    """Update screening settings."""

    threshold: Optional[float] = None
