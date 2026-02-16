#!/usr/bin/env python3
"""
Create admin user script.

Usage:
    python scripts/create_admin.py <username> <password>
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password


def create_admin_user(username: str, password: str) -> None:
    """
    Create an admin user account.

    Args:
        username: Admin username
        password: Admin password
    """
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()

        if existing_user:
            print(f"Error: User '{username}' already exists")
            sys.exit(1)

        # Create new admin user
        hashed_password = hash_password(password)

        admin_user = User(
            username=username,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"Admin user '{username}' created successfully!")
        print(f"User ID: {admin_user.id}")

    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        sys.exit(1)

    finally:
        db.close()


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_admin.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    # Validate inputs
    if len(username) < 3 or len(username) > 50:
        print("Error: Username must be 3-50 characters")
        sys.exit(1)

    if len(password) < 6:
        print("Error: Password must be at least 6 characters")
        sys.exit(1)

    create_admin_user(username, password)


if __name__ == "__main__":
    main()
