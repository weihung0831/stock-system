"""Admin management endpoints."""
import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.admin import TierUpdateRequest
from app.schemas.auth import UserResponse, UpdateEmailRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """List all users (admin only)."""
    return db.query(User).order_by(User.id).all()


@router.patch("/users/{user_id}/tier", response_model=UserResponse)
def update_user_tier(
    user_id: int,
    request: TierUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Update a user's membership tier (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    user.membership_tier = request.membership_tier
    db.commit()
    db.refresh(user)

    logger.info(f"Admin {admin.username} updated user {user.username} tier to {request.membership_tier}")
    return user


@router.patch("/users/{user_id}/email", response_model=UserResponse)
def update_user_email(
    user_id: int,
    request: UpdateEmailRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Update a user's email (admin only)."""
    from sqlalchemy import func

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    email_normalized = request.email.lower().strip()
    existing = db.query(User).filter(
        func.lower(User.email) == email_normalized,
        User.id != user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email 已被使用")

    user.email = email_normalized
    db.commit()
    db.refresh(user)

    logger.info(f"Admin {admin.username} updated user {user.username} email")
    return user


@router.patch("/users/{user_id}/active", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Toggle a user's active status (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    status = "啟用" if user.is_active else "停用"
    logger.info(f"Admin {admin.username} {status} user {user.username}")
    return user
