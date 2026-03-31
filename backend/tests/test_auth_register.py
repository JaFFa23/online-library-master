import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strong_password_123"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["id"] > 0
    assert data["email"] == "user@example.com"
    assert data["role"] == "client"


@pytest.mark.asyncio
async def test_register_conflict_email_taken(client: AsyncClient):
    # 1) create first time
    r1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strong_password_123"},
    )
    assert r1.status_code == 201, r1.text

    # 2) create second time -> 409
    r2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strong_password_123"},
    )
    assert r2.status_code == 409, r2.text

    # unified error format
    err = r2.json()
    assert err["error"] == "http_error"
    assert "already" in str(err["details"]).lower()
