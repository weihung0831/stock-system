"""FastAPI main application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth_router,
    stocks_router,
    data_router,
    reports_router,
    screening_router,
    scheduler_router,
    custom_screening_router,
    chip_stats_router,
    backtest_router,
    sector_tags_router,
    chat_router,
    right_side_signals_router,
    admin_router,
)
from app.tasks.daily_pipeline import run_daily_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    global scheduler

    # Startup: Create database tables
    logger.info("Starting application...")
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Auto-migrate: add missing columns
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT top_sectors_json FROM system_settings LIMIT 1"))
        except Exception:
            try:
                conn.execute(text("ALTER TABLE system_settings ADD COLUMN top_sectors_json TEXT NULL"))
                conn.commit()
                logger.info("Auto-migrated: added top_sectors_json column")
            except Exception:
                pass

    # Migrations
    from sqlalchemy import inspect, text
    insp = inspect(engine)

    # Migrate: drop unused top_n column from system_settings
    settings_cols = {c["name"] for c in insp.get_columns("system_settings")}
    if "top_n" in settings_cols:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE system_settings DROP COLUMN top_n"))
            conn.commit()
        logger.info("Dropped unused top_n column from system_settings")

    # Migrate: add email and membership_tier columns to users
    user_cols = {c["name"] for c in insp.get_columns("users")}
    with engine.connect() as conn:
        if "email" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL"))
            conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))
            conn.commit()
            logger.info("Added email column to users table")
        if "membership_tier" not in user_cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN membership_tier VARCHAR(20) NOT NULL DEFAULT 'free'"
            ))
            conn.commit()
            logger.info("Added membership_tier column to users table")

    # Migrate: add right_side_analysis column to llm_reports
    if "llm_reports" in insp.get_table_names():
        report_cols = {c["name"] for c in insp.get_columns("llm_reports")}
        if "right_side_analysis" not in report_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE llm_reports ADD COLUMN right_side_analysis TEXT NULL"))
                conn.commit()
            logger.info("Added right_side_analysis column to llm_reports table")

    logger.info("Database tables created successfully")

    # Read scheduler settings from DB
    from app.database import SessionLocal
    from app.models.system_setting import SystemSetting
    db = SessionLocal()
    try:
        row = db.query(SystemSetting).first()
        sched_hour = row.scheduler_hour if row else 16
        sched_minute = row.scheduler_minute if row else 30
        sched_enabled = bool(row.scheduler_enabled) if row else True
    finally:
        db.close()

    # Initialize and start scheduler
    logger.info("Initializing APScheduler...")
    scheduler = BackgroundScheduler(timezone="Asia/Taipei")

    scheduler.add_job(
        func=run_daily_pipeline,
        trigger=CronTrigger(day_of_week="mon-fri", hour=sched_hour, minute=sched_minute),
        id="daily_pipeline",
        name="Daily Stock Screening Pipeline",
        replace_existing=True
    )

    scheduler.start()
    if sched_enabled:
        logger.info(f"Scheduler started: daily pipeline at {sched_hour:02d}:{sched_minute:02d}")
    else:
        scheduler.pause_job("daily_pipeline")
        logger.info("Scheduler started: pipeline paused (disabled in settings)")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="TW Stock Screener API",
    description="Taiwan stock multi-factor screening platform API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(data_router)
app.include_router(reports_router)
app.include_router(screening_router)
app.include_router(scheduler_router)
app.include_router(custom_screening_router)
app.include_router(chip_stats_router)
app.include_router(backtest_router)
app.include_router(sector_tags_router)
app.include_router(chat_router)
app.include_router(right_side_signals_router)
app.include_router(admin_router)


@app.get("/api/health")
def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "TW Stock Screener API",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
