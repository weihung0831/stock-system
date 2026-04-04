"""Notification-related schemas."""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Single notification response."""
    id: int
    type: str
    title: str
    message: Optional[str] = None
    is_read: bool
    created_date: date
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """List of notifications."""
    items: List[NotificationResponse]
    total: int


class UnreadCountResponse(BaseModel):
    """Unread notification count."""
    count: int
