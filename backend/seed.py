"""Database seeder - creates initial admin user."""
import sys
from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password


def seed_admin():
    """Create default admin user if not exists."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("Admin user already exists, skipping.")
            return

        admin = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            is_admin=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
        print("  Username: admin")
        print("  Password: admin123")
        print("  (Please change password after first login)")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
