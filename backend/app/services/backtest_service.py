"""Backtest service for historical performance analysis."""
import logging
from typing import List, Dict, Any
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.score_result import ScoreResult
from app.models.daily_price import DailyPrice
from app.models.stock import Stock

logger = logging.getLogger(__name__)


def get_available_score_dates(db: Session) -> List[dict]:
    """Get all score dates with backtestability status.

    Returns each date with a flag indicating whether enough future
    price data exists for meaningful backtest results.
    """
    max_trade_date = db.query(func.max(DailyPrice.trade_date)).scalar()

    dates = db.query(ScoreResult.score_date).distinct().order_by(
        ScoreResult.score_date.desc()
    ).all()

    result = []
    for (d,) in dates:
        has_future_data = (
            max_trade_date is not None
            and d + timedelta(days=5) <= max_trade_date
        )
        result.append({
            "date": d.isoformat(),
            "backtestable": has_future_data,
        })
    return result


def get_historical_top_stocks(
    db: Session,
    start_date: date,
    end_date: date,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Get historical top N stocks for each score date in date range.

    Args:
        db: Database session
        start_date: Start date for historical data
        end_date: End date for historical data
        top_n: Number of top stocks per date (default 10)

    Returns:
        List of historical top stocks grouped by score_date
    """
    logger.info(
        f"Fetching top {top_n} stocks from {start_date} to {end_date}"
    )

    # Get all score dates in range
    score_dates = db.query(ScoreResult.score_date).filter(
        ScoreResult.score_date >= start_date,
        ScoreResult.score_date <= end_date
    ).distinct().order_by(ScoreResult.score_date.asc()).all()

    logger.info(f"Found {len(score_dates)} score dates")

    results = []
    for (score_date,) in score_dates:
        # Get top N stocks for this date
        top_stocks = db.query(
            ScoreResult,
            Stock.stock_name
        ).join(
            Stock,
            ScoreResult.stock_id == Stock.stock_id
        ).filter(
            ScoreResult.score_date == score_date
        ).order_by(
            ScoreResult.total_score.desc()
        ).limit(top_n).all()

        stocks_list = []
        for score_result, stock_name in top_stocks:
            stocks_list.append({
                "stock_id": score_result.stock_id,
                "stock_name": stock_name,
                "total_score": float(score_result.total_score),
                "rank": score_result.rank
            })

        results.append({
            "score_date": score_date.isoformat(),
            "top_stocks": stocks_list
        })

    return results


def calculate_performance(
    db: Session,
    score_date: date,
    top_n: int = 10,
    forward_days: List[int] = None,
    stock_ids: List[str] = None,
) -> Dict[str, Any]:
    """
    Calculate performance of selected or top N stocks from a given score date.

    Args:
        db: Database session
        score_date: The score date to analyze
        top_n: Number of top stocks (ignored when stock_ids provided)
        forward_days: List of forward-looking periods [5, 10, 20] days
        stock_ids: Specific stock IDs to analyze (overrides top_n)

    Returns:
        Performance metrics including return rates for each stock
    """
    if forward_days is None:
        forward_days = [5, 10, 20]

    logger.info(
        f"Calculating performance for {f'stocks {stock_ids}' if stock_ids else f'top {top_n}'} on {score_date}"
    )

    # Build query for selected stocks or top N
    query = db.query(
        ScoreResult.stock_id,
        Stock.stock_name,
        ScoreResult.total_score,
        ScoreResult.rank
    ).join(
        Stock,
        ScoreResult.stock_id == Stock.stock_id
    ).filter(
        ScoreResult.score_date == score_date
    )

    if stock_ids:
        query = query.filter(ScoreResult.stock_id.in_(stock_ids))

    top_stocks = query.order_by(
        ScoreResult.total_score.desc()
    ).limit(top_n if not stock_ids else None).all()

    if not top_stocks:
        logger.warning(f"No stocks found for date {score_date}")
        return {
            "score_date": score_date.isoformat(),
            "stocks": [],
            "average_returns": {}
        }

    # Get base price (close price on score_date or nearest previous date)
    results = []
    for stock_id, stock_name, total_score, rank in top_stocks:
        base_price_data = db.query(DailyPrice.close).filter(
            DailyPrice.stock_id == stock_id,
            DailyPrice.trade_date <= score_date
        ).order_by(DailyPrice.trade_date.desc()).first()

        if not base_price_data:
            logger.warning(f"No base price found for {stock_id}")
            continue

        base_price = float(base_price_data[0])

        # Calculate returns for each forward period
        returns = {}
        for days in forward_days:
            target_date = score_date + timedelta(days=days)
            future_price_data = db.query(DailyPrice.close).filter(
                DailyPrice.stock_id == stock_id,
                DailyPrice.trade_date >= target_date
            ).order_by(DailyPrice.trade_date.asc()).first()

            if future_price_data:
                future_price = float(future_price_data[0])
                return_rate = ((future_price - base_price) / base_price) * 100
                returns[f"return_{days}d"] = round(return_rate, 2)
            else:
                returns[f"return_{days}d"] = None

        results.append({
            "stock_id": stock_id,
            "stock_name": stock_name,
            "total_score": float(total_score),
            "rank": rank,
            "base_price": base_price,
            **returns
        })

    # Calculate average returns across all stocks
    average_returns = {}
    for days in forward_days:
        key = f"return_{days}d"
        valid_returns = [
            stock[key] for stock in results if stock[key] is not None
        ]
        if valid_returns:
            average_returns[key] = round(
                sum(valid_returns) / len(valid_returns), 2
            )
        else:
            average_returns[key] = None

    return {
        "score_date": score_date.isoformat(),
        "stocks": results,
        "average_returns": average_returns
    }
