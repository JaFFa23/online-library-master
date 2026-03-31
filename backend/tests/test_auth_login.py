from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, async_session: AsyncSession):
    # prepare user in DB (email + password_hash)
    email = "user@example.com"
    password = "strong_password_123"
    password_hash = pwd_context.hash(password)

    user = User(email=email, password_hash=password_hash, role=UserRole.client)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # POST /api/v1/auth/login with correct password
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text

    data = r.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"].strip() != ""

    token = data["access_token"]

    # decode JWT with same secret/alg
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])

    # check claims exist
    assert "sub" in payload
    assert "role" in payload
    assert "exp" in payload

    # sub must be user_id as string
    assert payload["sub"] == str(user.id)
    # role should match user role
    assert payload["role"] == user.role.value

    # exp should be in the future
    exp = payload["exp"]
    now_ts = int(datetime.now(timezone.utc).timestamp())
    assert isinstance(exp, (int, float))
    assert int(exp) > now_ts


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401_same_message(client: AsyncClient, async_session: AsyncSession):
    email = "user@example.com"
    password_correct = "strong_password_123"
    password_wrong = "wrong_password_123"

    user = User(
        email=email,
        password_hash=pwd_context.hash(password_correct),
        role=UserRole.client,
    )
    async_session.add(user)
    await async_session.commit()

    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password_wrong},
    )
    assert r.status_code == 401, r.text

    # unified error format
    err = r.json()
    assert err["error"] == "http_error"
    assert err["details"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401_same_message(client: AsyncClient):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "no_such_user@example.com", "password": "strong_password_123"},
    )
    assert r.status_code == 401, r.text

    # must be the same message as wrong password (no account enumeration)
    err = r.json()
    assert err["error"] == "http_error"
    assert err["details"] == "Invalid email or password"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"email": "", "password": "strong_password_123"},              # empty email
        {"email": "not-an-email", "password": "strong_password_123"},  # invalid email format
        {"email": "user@example.com", "password": "short"},            # too short password (<8)
        {"password": "strong_password_123"},                           # missing email
        {"email": "user@example.com"},                                 # missing password
    ],
)
async def test_login_validation_422(client: AsyncClient, payload: dict):
    r = await client.post("/api/v1/auth/login", json=payload)
    assert r.status_code == 422, r.text

    err = r.json()
    assert err["error"] == "validation_error"
    assert isinstance(err["details"], list)
    assert len(err["details"]) > 0
