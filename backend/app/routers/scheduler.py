"""Scheduler API endpoints for pipeline management."""
import logging
import threading
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from apscheduler.triggers.cron import CronTrigger
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.pipeline_log import PipelineLog
from app.tasks.daily_pipeline import run_daily_pipeline
from app.tasks.pipeline_status import (
    get_latest_pipeline_log,
    get_pipeline_logs,
    is_pipeline_running
)
from app.models.system_setting import SystemSetting
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


class TriggerResponse(BaseModel):
    """Response for manual pipeline trigger."""
    message: str
    pipeline_id: Optional[int] = None
    status: str


class PipelineStatusResponse(BaseModel):
    """Response for pipeline status."""
    is_running: bool
    latest_log: Optional[dict]
    next_scheduled_run: str


class PipelineLogResponse(BaseModel):
    """Response for single pipeline log."""
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    steps_completed: int
    total_steps: int
    error: Optional[str]
    trigger_type: str


class PipelineLogsResponse(BaseModel):
    """Response for paginated pipeline logs."""
    logs: list[PipelineLogResponse]
    total: int
    page: int
    limit: int


class SchedulerSettingsResponse(BaseModel):
    """Response for scheduler settings."""
    enabled: bool
    hour: int
    minute: int


class SchedulerSettingsUpdate(BaseModel):
    """Request to update scheduler settings."""
    enabled: Optional[bool] = None
    hour: Optional[int] = None
    minute: Optional[int] = None


def _run_pipeline_in_background():
    """Background thread function to run pipeline."""
    import asyncio
    try:
        # Ensure event loop exists for libraries that need it (e.g. google-genai)
        asyncio.set_event_loop(asyncio.new_event_loop())
        logger.info("Starting pipeline in background thread")
        result = run_daily_pipeline(trigger_type="manual")
        logger.info(f"Background pipeline completed: {result}")
    except Exception as e:
        logger.error(f"Background pipeline failed: {e}", exc_info=True)


@router.post("/cron-trigger", response_model=TriggerResponse)
def cron_trigger_pipeline(
    secret: str = Query(..., description="Cron secret key"),
    db: Session = Depends(get_db)
):
    """
    External cron trigger endpoint, protected by CRON_SECRET.
    Use this with cron-job.org or similar services.
    Example: POST /api/scheduler/cron-trigger?secret=YOUR_SECRET
    """
    if not settings.CRON_SECRET or secret != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    if is_pipeline_running(db):
        return TriggerResponse(message="Pipeline already running", status="skipped")

    thread = threading.Thread(target=_run_pipeline_in_background, daemon=True)
    thread.start()
    logger.info("Pipeline triggered by external cron")

    return TriggerResponse(message="Pipeline triggered by cron", status="started")


@router.post("/trigger", response_model=TriggerResponse)
def trigger_pipeline(
    admin_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Manually trigger the daily pipeline (admin only).

    Args:
        admin_user: Current admin user
        db: Database session

    Returns:
        Trigger response with status

    Raises:
        HTTPException: If pipeline is already running
    """
    try:
        # Check if pipeline is already running
        if is_pipeline_running(db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pipeline 正在執行中，請稍後再試"
            )

        # Start pipeline in background thread
        thread = threading.Thread(target=_run_pipeline_in_background, daemon=True)
        thread.start()

        logger.info(f"Pipeline triggered manually by user: {admin_user.username}")

        return TriggerResponse(
            message="Pipeline triggered successfully",
            status="started"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger pipeline: {str(e)}"
        )


@router.get("/status", response_model=PipelineStatusResponse)
def get_pipeline_status(
    admin_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get current pipeline status and next scheduled run (admin only).

    Args:
        admin_user: Current admin user
        db: Database session

    Returns:
        Pipeline status response
    """
    try:
        # Check if pipeline is running
        running = is_pipeline_running(db)

        # Get latest log
        latest_log = get_latest_pipeline_log(db)
        latest_log_dict = None

        if latest_log:
            latest_log_dict = {
                "id": latest_log.id,
                "started_at": latest_log.started_at.isoformat(),
                "finished_at": latest_log.finished_at.isoformat() if latest_log.finished_at else None,
                "status": latest_log.status,
                "steps_completed": latest_log.steps_completed,
                "total_steps": latest_log.total_steps,
                "trigger_type": latest_log.trigger_type
            }

        # Next scheduled run from settings
        row = _get_or_create_settings(db)
        if row.scheduler_enabled:
            next_run = f"每日 {row.scheduler_hour:02d}:{row.scheduler_minute:02d} (台北時間)"
        else:
            next_run = "已停用"

        return PipelineStatusResponse(
            is_running=running,
            latest_log=latest_log_dict,
            next_scheduled_run=next_run
        )

    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline status: {str(e)}"
        )


@router.get("/logs", response_model=PipelineLogsResponse)
def get_logs(
    admin_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get historical pipeline execution logs (admin only).

    Args:
        admin_user: Current admin user
        db: Database session
        page: Page number (1-indexed)
        limit: Number of items per page

    Returns:
        Paginated pipeline logs
    """
    try:
        logs, total = get_pipeline_logs(db, page=page, limit=limit)

        logs_response = [
            PipelineLogResponse(
                id=log.id,
                started_at=log.started_at,
                finished_at=log.finished_at,
                status=log.status,
                steps_completed=log.steps_completed,
                total_steps=log.total_steps,
                error=log.error,
                trigger_type=log.trigger_type
            )
            for log in logs
        ]

        return PipelineLogsResponse(
            logs=logs_response,
            total=total,
            page=page,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Failed to get pipeline logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline logs: {str(e)}"
        )


def _get_or_create_settings(db: Session) -> SystemSetting:
    """Get system settings row, create with defaults if missing."""
    row = db.query(SystemSetting).first()
    if not row:
        row = SystemSetting(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/settings", response_model=SchedulerSettingsResponse)
def get_scheduler_settings(
    admin_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """Get current scheduler settings."""
    row = _get_or_create_settings(db)
    return SchedulerSettingsResponse(
        enabled=bool(row.scheduler_enabled),
        hour=row.scheduler_hour,
        minute=row.scheduler_minute,
    )


@router.put("/settings", response_model=SchedulerSettingsResponse)
def update_scheduler_settings(
    body: SchedulerSettingsUpdate,
    admin_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """Update scheduler settings and reschedule the job."""
    row = _get_or_create_settings(db)
    if body.enabled is not None:
        row.scheduler_enabled = 1 if body.enabled else 0
    if body.hour is not None:
        row.scheduler_hour = body.hour
    if body.minute is not None:
        row.scheduler_minute = body.minute
    db.commit()
    db.refresh(row)

    # Reschedule the APScheduler job
    from app.main import scheduler as app_scheduler
    if app_scheduler:
        try:
            if row.scheduler_enabled:
                app_scheduler.reschedule_job(
                    "daily_pipeline",
                    trigger=CronTrigger(
                        day_of_week="mon-fri",
                        hour=row.scheduler_hour,
                        minute=row.scheduler_minute,
                        timezone="Asia/Taipei",
                    ),
                )
                logger.info(f"Rescheduled pipeline to {row.scheduler_hour:02d}:{row.scheduler_minute:02d}")
            else:
                app_scheduler.pause_job("daily_pipeline")
                logger.info("Paused scheduled pipeline")
        except Exception as e:
            logger.error(f"Failed to reschedule: {e}")

    return SchedulerSettingsResponse(
        enabled=bool(row.scheduler_enabled),
        hour=row.scheduler_hour,
        minute=row.scheduler_minute,
    )


@router.delete("/logs")
def clear_logs(
    admin_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """Clear all pipeline execution logs (admin only)."""
    try:
        count = db.query(PipelineLog).delete()
        db.commit()
        return {"message": f"Deleted {count} logs"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
