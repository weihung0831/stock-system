"""Daily pipeline orchestrator for automated stock screening."""
import logging
import requests
from datetime import datetime, date, timedelta, timezone

# UTC+8 Taipei timezone
TZ_TAIPEI = timezone(timedelta(hours=8))


def now_taipei() -> datetime:
    """Get current datetime in Taipei timezone (UTC+8)."""
    return datetime.now(TZ_TAIPEI).replace(tzinfo=None)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pipeline_log import PipelineLog
from app.tasks.data_fetch_steps import step_fetch_stock_data, _fetch_taiex_daily
from app.tasks.analysis_steps import step_scoring

logger = logging.getLogger(__name__)

# In-memory cache: {year: set[date]}
_holiday_cache: dict[int, set[date]] = {}

TWSE_HOLIDAY_API = "https://www.twse.com.tw/holidaySchedule/holidaySchedule"
# Names containing these keywords are trading-day markers, not holidays
_TRADING_DAY_KEYWORDS = ("開始交易", "最後交易日")


def _fetch_twse_holidays(year: int) -> set[date]:
    """
    Fetch TWSE closed dates from official API for the given year.
    Results are cached in memory so only one request per year per process.
    """
    if year in _holiday_cache:
        return _holiday_cache[year]

    # TWSE API uses ROC year (民國年)
    roc_year = year - 1911
    try:
        resp = requests.get(
            TWSE_HOLIDAY_API,
            params={"response": "json", "queryYear": roc_year},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("stat") != "ok" or "data" not in data:
            logger.warning(f"TWSE holiday API returned unexpected format for {year}")
            _holiday_cache[year] = set()
            return set()

        holidays: set[date] = set()
        for row in data["data"]:
            date_str, name = row[0], row[1]
            # Skip entries that mark trading days (e.g. "春節後開始交易日")
            if any(kw in name for kw in _TRADING_DAY_KEYWORDS):
                continue
            try:
                holidays.add(date.fromisoformat(date_str))
            except ValueError:
                continue

        _holiday_cache[year] = holidays
        logger.info(f"Fetched {len(holidays)} TWSE holidays for {year}")
        return holidays

    except Exception as e:
        logger.warning(f"Failed to fetch TWSE holidays for {year}: {e}")
        _holiday_cache[year] = set()
        return set()


def is_trading_day(check_date: date) -> bool:
    """
    Check if the given date is a TWSE trading day.
    Excludes weekends and TWSE holidays (auto-fetched from official API).
    """
    if check_date.weekday() >= 5:
        return False
    if check_date in _fetch_twse_holidays(check_date.year):
        return False
    return True


def run_daily_pipeline(trigger_type: str = "scheduled") -> dict:
    """
    Main daily pipeline orchestrator.

    Pipeline steps:
    1. Fetch stock data (prices, institutional, margin, TAIEX)
    2. Momentum strategy scoring (filters + scoring all stocks)
    News is fetched on-demand during LLM report generation.

    Args:
        trigger_type: "scheduled" or "manual"

    Returns:
        Result dict with status and details
    """
    # Early exit for scheduled triggers on non-trading days (no log created)
    today = now_taipei().date()
    if trigger_type != "manual" and not is_trading_day(today):
        logger.info(f"Skipping pipeline: {today} is not a trading day (no log created)")
        return {"status": "skipped", "reason": "Not a trading day"}

    # For manual triggers on non-trading days, use last trading day
    target_date = today
    if not is_trading_day(today):
        while not is_trading_day(target_date):
            target_date -= timedelta(days=1)
        logger.info(f"Non-trading day, using last trading day: {target_date}")

    db = SessionLocal()
    pipeline_log = None

    try:
        # Create pipeline log
        pipeline_log = PipelineLog(
            started_at=now_taipei(),
            status="running",
            steps_completed=0,
            total_steps=2,
            trigger_type=trigger_type
        )
        db.add(pipeline_log)
        db.commit()
        db.refresh(pipeline_log)

        logger.info(f"Pipeline started (ID: {pipeline_log.id}, trigger: {trigger_type})")

        date_str = target_date.strftime("%Y-%m-%d")
        errors = []

        # Step 1: Fetch stock data + TAIEX
        logger.info("Step 1/2: Fetching stock data + TAIEX")
        result = step_fetch_stock_data(db, date_str)
        # Also fetch TAIEX market index for momentum strategy
        try:
            _fetch_taiex_daily(db, days=300)
        except Exception as e:
            db.rollback()
            logger.warning(f"TAIEX fetch warning: {e}")
        if result["success"]:
            pipeline_log.steps_completed = 1
            db.commit()
            logger.info("Stock data fetch completed")
        else:
            errors.append(f"Step 1: {result['message']}")
            logger.error(f"Stock data fetch failed: {result['message']}")

        # Step 2: Momentum strategy scoring
        logger.info("Step 2/2: Running momentum strategy")
        result = step_scoring(db, date_str)
        if result["success"]:
            pipeline_log.steps_completed = 2
            db.commit()
            logger.info("Scoring completed")
        else:
            errors.append(f"Step 2: {result['message']}")
            logger.error(f"Scoring failed: {result['message']}")

        # Finalize pipeline log
        pipeline_log.finished_at = now_taipei()

        if errors:
            pipeline_log.status = "failed"
            pipeline_log.error = "; ".join(errors)
            logger.warning(f"Pipeline completed with errors: {len(errors)} errors")
        else:
            pipeline_log.status = "success"
            logger.info("Pipeline completed successfully")

        # Clear right-side signal cache so new data is reflected immediately
        try:
            from app.routers.right_side_signals import _cache
            _cache.clear()
            logger.info("Cleared right-side signal cache")
        except Exception as e:
            logger.warning(f"Failed to clear signal cache: {e}")

        db.commit()

        return {
            "status": pipeline_log.status,
            "pipeline_id": pipeline_log.id,
            "steps_completed": pipeline_log.steps_completed,
            "errors": errors if errors else None
        }

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}", exc_info=True)

        # Update pipeline log on error
        if pipeline_log:
            pipeline_log.status = "failed"
            pipeline_log.finished_at = now_taipei()
            pipeline_log.error = str(e)
            db.commit()

        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()
