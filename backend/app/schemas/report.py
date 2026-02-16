"""LLM report-related schemas."""
from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict


class LLMReportResponse(BaseModel):
    """LLM-generated stock analysis report response."""

    id: int
    stock_id: str
    stock_name: str = ""
    report_date: date
    chip_analysis: str
    fundamental_analysis: str
    technical_analysis: str
    news_sentiment: str
    news_summary: str
    risk_alerts: List[str]
    recommendation: str
    confidence: str
    model_used: str

    model_config = ConfigDict(from_attributes=True)


class ReportsListResponse(BaseModel):
    """List of LLM reports response."""

    items: List[LLMReportResponse]
    total: int
    page: int
    limit: int
