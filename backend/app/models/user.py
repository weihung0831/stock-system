"""User model for authentication."""
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """User account for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    membership_tier = Column(String(20), default='free', nullable=False, server_default='free')

    def __repr__(self) -> str:
        return f"<User {self.username} tier={self.membership_tier} admin={self.is_admin}>"
