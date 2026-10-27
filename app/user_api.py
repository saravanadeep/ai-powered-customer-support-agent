"""Admin-only user management endpoints for the Customer Support CRM."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.dependencies import get_db, get_current_user, require_role
from app.models import User

router = APIRouter(prefix="/admin/users", tags=["User Management"])

RoleName = Literal["Admin", "Support Agent", "Viewer"]


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    role: RoleName = "Support Agent"


class UserRoleUpdateRequest(BaseModel):
    role: RoleName


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


def serialize_user(user: User) -> dict:
    """Return safe user fields; never expose the password hash."""
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def active_admin_count(db: Session) -> int:
    return (
        db.query(User)
        .filter(User.role == "Admin", User.is_active.is_(True))
        .count()
    )


def validate_email(email: str) -> None:
    email = email.strip()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid email address.",
        )


@router.get("", dependencies=[Depends(require_role("Admin"))])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.user_id.asc()).all()
    return {"users": [serialize_user(user) for user in users]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    username = request.username.strip()
    email = request.email.strip().lower()
    validate_email(email)

    existing_user = db.query(User).filter(
        or_(
            func.lower(User.username) == username.lower(),
            func.lower(User.email) == email,
        )
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists.",
        )

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(request.password),
        role=request.role,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create user. Check that the username and email are unique.",
        )
    return {"message": "User created successfully.", "user": serialize_user(user)}


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    request: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.user_id == current_user.user_id and request.role != "Admin":
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own Admin role.",
        )

    if user.role == "Admin" and user.is_active and request.role != "Admin":
        if active_admin_count(db) <= 1:
            raise HTTPException(
                status_code=400,
                detail="The last active Admin cannot be demoted.",
            )

    user.role = request.role
    db.commit()
    db.refresh(user)
    return {"message": "User role updated successfully.", "user": serialize_user(user)}


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: int,
    request: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.user_id == current_user.user_id and not request.is_active:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account.",
        )

    if user.role == "Admin" and user.is_active and not request.is_active:
        if active_admin_count(db) <= 1:
            raise HTTPException(
                status_code=400,
                detail="The last active Admin cannot be deactivated.",
            )

    user.is_active = request.is_active
    db.commit()
    db.refresh(user)
    action = "activated" if user.is_active else "deactivated"
    return {"message": f"User {action} successfully.", "user": serialize_user(user)}
