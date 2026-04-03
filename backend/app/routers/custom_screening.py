"""Custom screening router for advanced filtering."""
import logging
from typing import Annotated, List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.custom_screening_service import custom_screen

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/custom-screening",
    tags=["custom-screening"]
)


class CustomScreeningRequest(BaseModel):
    """Request model for custom screening."""
    industry: Optional[str] = Field(None, description="Industry filter")
    min_total_score: Optional[float] = Field(None, ge=0, le=100)
    min_momentum_score: Optional[float] = Field(None, ge=0, le=100)
    classification: Optional[str] = Field(None, description="BUY/HOLD/SELL filter")
    score_date: Optional[date] = Field(None, description="Target score date")


@router.post("")
def custom_screening(
    request: CustomScreeningRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Perform custom screening with multiple filter criteria."""
    try:
        filters = {
            "industry": request.industry,
            "min_total_score": request.min_total_score,
            "min_momentum_score": request.min_momentum_score,
            "classification": request.classification,
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        results = custom_screen(
            db=db,
            filters=filters,
            score_date=request.score_date
        )

        return {
            "success": True,
            "count": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Custom screening failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Custom screening failed: {str(e)}"
        )
