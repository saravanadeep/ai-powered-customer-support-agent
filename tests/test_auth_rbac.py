"""Automated authentication and RBAC tests for Customer Support CRM Agent.

Copy this file into the project's tests/ directory as tests/test_auth_rbac.py.
These tests use an isolated in-memory SQLite database and do not touch your
configured PostgreSQL database.
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import app
from app.auth import create_access_token, hash_password
from app.database import Base
from app.dependencies import get_db
from app.models import User


@pytest.fixture()
def test_db():
    """Create an isolated SQLite database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    # Only the User table is needed for auth/RBAC tests.
    User.__table__.create(bind=engine, checkfirst=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        User.__table__.drop(bind=engine, checkfirst=True)
        engine.dispose()


@pytest.fixture()
def client(test_db):
    """Override the API database dependency with the isolated test database."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def make_user(
    db,
    *,
    username="testadmin",
    email="testadmin@example.com",
    password="TestPassword123!",
    role="Admin",
    is_active=True,
):
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, username, password="TestPassword123!"):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json().get("access_token")
    assert token
    return token


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_success_returns_access_token_and_user(client, test_db):
    make_user(test_db)

    response = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "TestPassword123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("access_token")
    assert body.get("token_type", "bearer").lower() == "bearer"


def test_login_rejects_wrong_password(client, test_db):
    make_user(test_db)

    response = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_username(client):
    response = client.post(
        "/auth/login",
        json={"username": "missing-user", "password": "TestPassword123!"},
    )

    assert response.status_code == 401


def test_login_rejects_inactive_user(client, test_db):
    make_user(test_db, is_active=False)

    response = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "TestPassword123!"},
    )

    assert response.status_code == 403


def test_auth_me_requires_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_rejects_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers=auth_headers("this-is-not-a-valid-jwt"),
    )
    assert response.status_code == 401


def test_auth_me_accepts_valid_token(client, test_db):
    user = make_user(test_db)
    token = login(client, user.username)

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    # Support either flat /auth/me responses or a response nested under "user".
    body = body.get("user", body)
    assert body.get("username") == user.username
    assert body.get("role") == "Admin"


def test_auth_me_rejects_expired_token(client, test_db):
    user = make_user(test_db)
    expired_token = create_access_token(
        user.user_id,
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/auth/me",
        headers=auth_headers(expired_token),
    )

    assert response.status_code == 401


def test_auth_me_rejects_token_for_inactive_user(client, test_db):
    user = make_user(test_db)
    token = create_access_token(user.user_id)

    user.is_active = False
    test_db.commit()

    response = client.get("/auth/me", headers=auth_headers(token))
    assert response.status_code == 401


def test_customer_endpoint_requires_authentication(client):
    response = client.get("/customers")
    assert response.status_code == 401


def test_admin_can_list_users(client, test_db):
    admin = make_user(test_db)
    token = login(client, admin.username)

    response = client.get("/admin/users", headers=auth_headers(token))

    assert response.status_code == 200, response.text
    body = response.json()
    assert "users" in body
    assert any(user.get("username") == admin.username for user in body["users"])
    assert all("hashed_password" not in user for user in body["users"])


@pytest.mark.parametrize("role", ["Support Agent", "Viewer"])
def test_non_admin_cannot_list_users(client, test_db, role):
    user = make_user(
        test_db,
        username=f"{role.lower().replace(' ', '_')}",
        email=f"{role.lower().replace(' ', '_')}@example.com",
        role=role,
    )
    token = login(client, user.username)

    response = client.get("/admin/users", headers=auth_headers(token))

    assert response.status_code == 403


def test_admin_can_create_user_without_exposing_password_hash(client, test_db):
    admin = make_user(test_db)
    token = login(client, admin.username)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "username": "newviewer",
            "email": "newviewer@example.com",
            "password": "ViewerPassword123!",
            "role": "Viewer",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    created_user = body.get("user", body)
    assert created_user.get("username") == "newviewer"
    assert created_user.get("role") == "Viewer"
    assert "hashed_password" not in created_user

    saved_user = test_db.query(User).filter(User.username == "newviewer").first()
    assert saved_user is not None
    assert saved_user.hashed_password != "ViewerPassword123!"


def test_admin_user_creation_rejects_duplicate_username_or_email(client, test_db):
    admin = make_user(test_db)
    make_user(
        test_db,
        username="existingagent",
        email="existingagent@example.com",
        role="Support Agent",
    )
    token = login(client, admin.username)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "username": "existingagent",
            "email": "another@example.com",
            "password": "AnotherPassword123!",
            "role": "Viewer",
        },
    )

    assert response.status_code == 409


def test_non_admin_cannot_create_users(client, test_db):
    agent = make_user(
        test_db,
        username="supportagent",
        email="supportagent@example.com",
        role="Support Agent",
    )
    token = login(client, agent.username)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "username": "blockedviewer",
            "email": "blockedviewer@example.com",
            "password": "ViewerPassword123!",
            "role": "Viewer",
        },
    )

    assert response.status_code == 403


def test_admin_cannot_deactivate_their_own_account(client, test_db):
    admin = make_user(test_db)
    token = login(client, admin.username)

    response = client.patch(
        f"/admin/users/{admin.user_id}/status",
        headers=auth_headers(token),
        json={"is_active": False},
    )

    assert response.status_code == 400


def test_last_active_admin_cannot_be_demoted(client, test_db):
    admin = make_user(test_db)
    token = login(client, admin.username)

    response = client.patch(
        f"/admin/users/{admin.user_id}/role",
        headers=auth_headers(token),
        json={"role": "Support Agent"},
    )

    assert response.status_code == 400
