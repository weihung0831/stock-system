"""Pipeline status tracking utilities."""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.pipeline_log import PipelineLog

logger = logging.getLogger(__name__)


def get_latest_pipeline_log(db: Session) -> Optional[PipelineLog]:
    """
    Get the most recent pipeline log.

    Args:
        db: Database session

    Returns:
        Latest PipelineLog or None
    """
    try:
        return db.query(PipelineLog).order_by(desc(PipelineLog.started_at)).first()
    except Exception as e:
        logger.error(f"Failed to get latest pipeline log: {e}")
        return None


def get_pipeline_logs(
    db: Session,
    page: int = 1,
    limit: int = 20
) -> tuple[List[PipelineLog], int]:
    """
    Get paginated pipeline logs.

    Args:
        db: Database session
        page: Page number (1-indexed)
        limit: Number of records per page

    Returns:
        Tuple of (logs list, total count)
    """
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Query logs with pagination
        query = db.query(PipelineLog).order_by(desc(PipelineLog.started_at))
        total = query.count()
        logs = query.offset(offset).limit(limit).all()

        return logs, total

    except Exception as e:
        logger.error(f"Failed to get pipeline logs: {e}")
        return [], 0


def is_pipeline_running(db: Session, timeout_minutes: int = 30) -> bool:
    """
    Check if any pipeline is currently running.
    Auto-recovers stuck pipelines that exceed timeout_minutes.

    Args:
        db: Database session
        timeout_minutes: Max minutes a pipeline can run before auto-recovery

    Returns:
        True if pipeline is running, False otherwise
    """
    try:
        running_pipelines = db.query(PipelineLog).filter(
            PipelineLog.status == "running"
        ).all()

        if not running_pipelines:
            return False

        from datetime import datetime, timezone, timedelta
        TZ_TAIPEI = timezone(timedelta(hours=8))
        now = datetime.now(TZ_TAIPEI).replace(tzinfo=None)

        for pipeline in running_pipelines:
            elapsed = (now - pipeline.started_at).total_seconds() / 60
            if elapsed > timeout_minutes:
                logger.warning(
                    f"Auto-recovering stuck pipeline id={pipeline.id} "
                    f"(running for {elapsed:.0f} min, timeout={timeout_minutes})"
                )
                pipeline.status = "failed"
                pipeline.finished_at = now
                pipeline.error = f"Pipeline 超時自動恢復 (超過 {timeout_minutes} 分鐘)"
                db.commit()
            else:
                return True

        return False

    except Exception as e:
        logger.error(f"Failed to check pipeline status: {e}")
        return False
