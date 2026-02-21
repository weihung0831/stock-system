"""Authentication endpoints."""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
    UpdateEmailRequest, ChangePasswordRequest,
)
from app.services.auth_service import (
    hash_password, verify_password, create_access_token,
)
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    request: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new free-tier user."""
    # Check duplicate username
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=409, detail="帳號已被使用")

    # Check duplicate email (case-insensitive)
    email_normalized = request.email.lower().strip()
    if db.query(User).filter(func.lower(User.email) == email_normalized).first():
        raise HTTPException(status_code=409, detail="Email 已被使用")

    user = User(
        username=request.username,
        email=email_normalized,
        hashed_password=hash_password(request.password),
        membership_tier="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {user.username}")
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Authenticate user and return JWT token with tier info."""
    user = db.query(User).filter(User.username == request.username).first()

    if not user:
        logger.warning(f"Login attempt with non-existent username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not verify_password(request.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        logger.warning(f"Login attempt by inactive user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(
        data={"sub": user.username, "tier": user.membership_tier}
    )

    logger.info(f"User logged in successfully: {request.username}")
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current authenticated user information."""
    return current_user


@router.put("/profile/email", response_model=UserResponse)
def update_email(
    request: UpdateEmailRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update current user's email."""
    email_normalized = request.email.lower().strip()

    # Check if email already used by another user
    existing = db.query(User).filter(
        func.lower(User.email) == email_normalized,
        User.id != current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email 已被使用")

    current_user.email = email_normalized
    db.commit()
    db.refresh(current_user)
    logger.info(f"User {current_user.username} updated email")
    return current_user


@router.put("/profile/password")
def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Change current user's password."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="目前密碼不正確")

    current_user.hashed_password = hash_password(request.new_password)
    db.commit()
    logger.info(f"User {current_user.username} changed password")
    return {"message": "密碼已更新"}
