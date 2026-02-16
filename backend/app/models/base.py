"""Base model mixins."""
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

TZ_TAIPEI = timezone(timedelta(hours=8))


def _now_taipei():
    """Get current datetime in Taipei timezone without tzinfo for MySQL."""
    return datetime.now(TZ_TAIPEI).replace(tzinfo=None)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(
        DateTime,
        nullable=False,
        default=_now_taipei,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=_now_taipei,
        onupdate=_now_taipei,
        server_default=func.now(),
        server_onupdate=func.now()
    )
