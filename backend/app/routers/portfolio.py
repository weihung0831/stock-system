"""Portfolio router for holding management and real-time monitoring."""
import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.stock import Stock
from app.models.score_result import ScoreResult
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    RealtimeResponse,
)
from app.services.portfolio_monitor import get_realtime_data

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/portfolio",
    tags=["portfolio"]
)


@router.get("/realtime", response_model=RealtimeResponse)
def get_portfolio_realtime(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get real-time data for all user holdings."""
    return get_realtime_data(current_user.id, db)


@router.get("", response_model=List[PortfolioResponse])
def list_portfolios(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all holdings for the current user."""
    return (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id)
        .all()
    )


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    data: PortfolioCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Add a new stock holding to monitor."""
    existing = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id, Portfolio.stock_id == data.stock_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="此股票已在持倉中")

    stock = db.query(Stock).filter(Stock.stock_id == data.stock_id).first()
    stock_name = stock.stock_name if stock else data.stock_id

    momentum = (
        db.query(ScoreResult.classification)
        .filter(ScoreResult.stock_id == data.stock_id)
        .order_by(desc(ScoreResult.score_date))
        .first()
    )
    entry_grade = momentum.classification if momentum else None

    portfolio = Portfolio(
        user_id=current_user.id,
        stock_id=data.stock_id,
        stock_name=stock_name,
        cost_price=data.cost_price,
        quantity=data.quantity,
        target_return_pct=data.target_return_pct,
        entry_momentum_grade=entry_grade,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    data: PortfolioUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a holding's cost, quantity, or target."""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="持倉不存在")

    if data.cost_price is not None:
        portfolio.cost_price = data.cost_price
    if data.quantity is not None:
        portfolio.quantity = data.quantity
    if data.target_return_pct is not None:
        portfolio.target_return_pct = data.target_return_pct

    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Remove a holding from monitoring."""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="持倉不存在")

    db.delete(portfolio)
    db.commit()
