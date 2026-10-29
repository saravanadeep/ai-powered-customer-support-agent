
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from app.auth import hash_password
from app.database import SessionLocal
from app.models import User


ALLOWED_ROLES = ["Admin", "Support Agent", "Viewer"]


def create_user():
    db = SessionLocal()

    try:
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip()
        role = input(
            "Enter role (Admin / Support Agent / Viewer): "
        ).strip()

        if role not in ALLOWED_ROLES:
            print("Invalid role. Choose one of:", ALLOWED_ROLES)
            return

        password = getpass("Enter password: ")
        confirm_password = getpass("Confirm password: ")

        if not username or not email or not password:
            print("Username, email, and password are required.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        if db.query(User).filter(
            (User.username == username) |
            (User.email == email)
        ).first():
            print("Username or email already exists.")
            return

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True
        )

        db.add(user)
        db.commit()

        print(f"User '{username}' created successfully.")
        print(f"Assigned role: {role}")

    except IntegrityError:
        db.rollback()
        print("Username or email already exists.")

    except Exception as e:
        db.rollback()
        print(f"Unable to create user: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_user()
