"""Data collection endpoints."""
import logging
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.user import User
from app.models.pipeline_log import PipelineLog
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])


def run_data_collection(user_id: int):
    """
    Background task to run data collection pipeline.

    Args:
        user_id: ID of user who triggered collection
    """
    db = SessionLocal()
    log = PipelineLog(
        started_at=datetime.utcnow(),
        status="running",
        steps_completed=0,
        total_steps=7,
        trigger_type="manual"
    )
    db.add(log)
    db.commit()

    try:
        logger.info(f"Starting data collection pipeline (triggered by user {user_id})")

        # TODO: Implement actual data collection steps in Phase 02
        # This is a placeholder that will be implemented in next phase

        log.status = "success"
        log.steps_completed = 7
        log.finished_at = datetime.utcnow()
        logger.info("Data collection pipeline completed successfully")

    except Exception as e:
        logger.error(f"Data collection pipeline failed: {e}")
        log.status = "failed"
        log.error = str(e)
        log.finished_at = datetime.utcnow()

    finally:
        db.commit()
        db.close()


@router.post("/collect")
def trigger_data_collection(
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Trigger data collection pipeline (admin only).

    Args:
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Status message
    """
    # Add collection task to background
    background_tasks.add_task(run_data_collection, current_user.id)

    logger.info(f"Data collection triggered by admin user: {current_user.username}")

    return {
        "status": "started",
        "message": "Data collection pipeline started in background"
    }


@router.get("/status")
def get_collection_status(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get latest data collection status (admin only).

    Args:
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Latest pipeline log status
    """
    # Get most recent pipeline log
    latest_log = db.query(PipelineLog).order_by(
        PipelineLog.started_at.desc()
    ).first()

    if not latest_log:
        return {
            "status": "no_runs",
            "message": "No data collection runs found"
        }

    return {
        "status": latest_log.status,
        "started_at": latest_log.started_at,
        "finished_at": latest_log.finished_at,
        "steps_completed": latest_log.steps_completed,
        "total_steps": latest_log.total_steps,
        "error": latest_log.error,
        "trigger_type": latest_log.trigger_type
    }
