"""API routers for all endpoints."""
from app.routers.auth import router as auth_router
from app.routers.stocks import router as stocks_router
from app.routers.data import router as data_router
from app.routers.reports import router as reports_router
from app.routers.screening import router as screening_router
from app.routers.scheduler import router as scheduler_router
from app.routers.custom_screening import router as custom_screening_router
from app.routers.chip_stats import router as chip_stats_router
from app.routers.backtest import router as backtest_router
from app.routers.sector_tags import router as sector_tags_router

__all__ = [
    "auth_router",
    "stocks_router",
    "data_router",
    "reports_router",
    "screening_router",
    "scheduler_router",
    "custom_screening_router",
    "chip_stats_router",
    "backtest_router",
    "sector_tags_router",
]
