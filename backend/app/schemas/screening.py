"""Screening-related schemas."""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ScreeningRequest(BaseModel):
    """Stock screening request with custom weights."""

    weights: Dict[str, float] = Field(
        default={"chip": 40, "fundamental": 35, "technical": 25},
        description="Weight distribution for chip/fundamental/technical factors"
    )
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
    chip_score: float
    fundamental_score: float
    technical_score: float
    total_score: float
    rank: int
    industry: Optional[str] = None
    close_price: float = 0.0
    change_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ScoreDetailResponse(BaseModel):
    """Score detail response with breakdown."""

    stock_id: str
    stock_name: Optional[str] = None
    industry: Optional[str] = None
    chip_score: float
    chip_details: dict
    fundamental_score: float
    fundamental_details: dict
    technical_score: float
    technical_details: dict
    total_score: float


class ScreeningResultsResponse(BaseModel):
    """Screening results response."""

    items: List[ScoreResultResponse]
    total: int
    threshold: float
    weights: Dict[str, float]


class ScreeningSettingsResponse(BaseModel):
    """Persisted screening settings."""

    weights: Dict[str, float]
    threshold: float


class ScreeningSettingsUpdate(BaseModel):
    """Update screening settings."""

    weights: Optional[Dict[str, float]] = None
    threshold: Optional[float] = None
