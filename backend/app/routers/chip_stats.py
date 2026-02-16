"""Chip statistics router for institutional and margin trading trends."""
import logging
from typing import Annotated, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.chip_stats_service import (
    get_institutional_trend,
    get_margin_trend
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chip-stats",
    tags=["chip-stats"]
)


@router.get("/institutional")
def get_institutional_stats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    end_date: Optional[date] = Query(default=None, description="End date (default: today)"),
    stock_id: Optional[str] = Query(default=None, description="Stock ID to filter (e.g. 2330)")
):
    """
    Get institutional investor trading trend aggregated by date.
    If stock_id is provided, returns data for that specific stock only.

    Requires authentication.
    """
    try:
        results = get_institutional_trend(
            db=db,
            days=days,
            end_date=end_date,
            stock_id=stock_id
        )

        return {
            "success": True,
            "days": days,
            "data": results
        }

    except Exception as e:
        logger.error(f"Failed to fetch institutional stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得法人買賣超資料失敗，請稍後再試"
        )


@router.get("/margin")
def get_margin_stats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    end_date: Optional[date] = Query(default=None, description="End date (default: today)"),
    stock_id: Optional[str] = Query(default=None, description="Stock ID to filter (e.g. 2330)")
):
    """
    Get margin trading and short selling trend aggregated by date.
    If stock_id is provided, returns data for that specific stock only.

    Requires authentication.
    """
    try:
        results = get_margin_trend(
            db=db,
            days=days,
            end_date=end_date,
            stock_id=stock_id
        )

        return {
            "success": True,
            "days": days,
            "data": results
        }

    except Exception as e:
        logger.error(f"Failed to fetch margin stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得融資融券資料失敗，請稍後再試"
        )
