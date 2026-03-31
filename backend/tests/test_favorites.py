import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_add_favorite_404_if_book_not_found(client: AsyncClient, get_token):
    headers = await get_token(email="u1@example.com")
    r = await client.post("/api/v1/users/me/favorites/999999", headers=headers)
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_add_and_delete_favorite_idempotent(
    client: AsyncClient,
    get_token,
    async_session: AsyncSession,
):
    headers = await get_token(email="u2@example.com")

    # создаём книгу напрямую
    res = await async_session.execute(
        text("INSERT INTO books (title, year) VALUES ('Test Book', 2024) RETURNING id;")
    )
    book_id = res.scalar_one()
    await async_session.commit()

    # add -> 204
    r1 = await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=headers)
    assert r1.status_code == 204, r1.text

    # add again -> 204 (идемпотентно)
    r2 = await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=headers)
    assert r2.status_code == 204, r2.text

    # delete -> 204
    r3 = await client.delete(f"/api/v1/users/me/favorites/{book_id}", headers=headers)
    assert r3.status_code == 204, r3.text

    # delete again -> 204 (идемпотентно)
    r4 = await client.delete(f"/api/v1/users/me/favorites/{book_id}", headers=headers)
    assert r4.status_code == 204, r4.text
