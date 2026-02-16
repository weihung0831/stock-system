"""Backtest router for historical performance analysis."""
import logging
from typing import Annotated, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.backtest_service import (
    get_available_score_dates,
    get_historical_top_stocks,
    calculate_performance
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/backtest",
    tags=["backtest"]
)


@router.get("/score-dates")
def get_score_dates(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get all available score dates (descending order)."""
    dates = get_available_score_dates(db)
    return {"dates": dates}


@router.get("/history")
def get_backtest_history(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: date = Query(..., description="Start date for historical data"),
    end_date: date = Query(..., description="End date for historical data"),
    top_n: int = Query(default=10, ge=1, le=50, description="Number of top stocks per date")
):
    """
    Get historical top N stocks for each score date in date range.

    Requires authentication.

    Args:
        start_date: Start date for historical data
        end_date: End date for historical data
        top_n: Number of top stocks per date (1-50)
        db: Database session
        current_user: Authenticated user

    Returns:
        List of historical top stocks grouped by score_date
    """
    try:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before or equal to end_date"
            )

        results = get_historical_top_stocks(
            db=db,
            start_date=start_date,
            end_date=end_date,
            top_n=top_n
        )

        return {
            "success": True,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "top_n": top_n,
            "data": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch backtest history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得回測歷史資料失敗，請稍後再試"
        )


@router.get("/performance")
def get_backtest_performance(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    score_date: date = Query(..., description="Score date to analyze"),
    top_n: int = Query(default=10, ge=1, le=50, description="Number of top stocks to analyze"),
    forward_days: List[int] = Query(default=[5, 10, 20], description="Forward-looking periods"),
    stock_ids: List[str] = Query(default=[], description="Specific stock IDs (overrides top_n)"),
):
    """
    Calculate performance of top N stocks from a given score date.

    Requires authentication.

    Args:
        score_date: The score date to analyze
        top_n: Number of top stocks to analyze (1-50)
        forward_days: List of forward-looking periods (e.g., [5, 10, 20] days)
        db: Database session
        current_user: Authenticated user

    Returns:
        Performance metrics including return rates for each stock
    """
    try:
        # Validate forward_days
        if not forward_days or len(forward_days) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="forward_days must contain 1-5 values"
            )

        for days in forward_days:
            if days < 1 or days > 365:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each forward_days value must be between 1-365"
                )

        results = calculate_performance(
            db=db,
            score_date=score_date,
            top_n=top_n,
            forward_days=forward_days,
            stock_ids=stock_ids if stock_ids else None,
        )

        return {
            "success": True,
            **results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="計算回測績效失敗，請稍後再試"
        )
