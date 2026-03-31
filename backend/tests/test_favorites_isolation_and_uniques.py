import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _seed_author_genre_book(async_session: AsyncSession) -> int:
    author_id = (await async_session.execute(
        text("INSERT INTO authors (name) VALUES ('Author Fav') RETURNING id;")
    )).scalar_one()

    genre_id = (await async_session.execute(
        text("INSERT INTO genres (name) VALUES ('Genre Fav') RETURNING id;")
    )).scalar_one()

    book_id = (await async_session.execute(
        text("INSERT INTO books (title, description, year, isbn) VALUES ('Book Fav', 'Desc', 2023, 'ISBN-FAV') RETURNING id;")
    )).scalar_one()

    await async_session.execute(
        text("INSERT INTO book_authors (book_id, author_id) VALUES (:b, :a);"),
        {"b": book_id, "a": author_id},
    )
    await async_session.execute(
        text("INSERT INTO book_genres (book_id, genre_id) VALUES (:b, :g);"),
        {"b": book_id, "g": genre_id},
    )
    await async_session.commit()
    return book_id


async def _count_favorites(async_session: AsyncSession, user_id: int, book_id: int) -> int:
    return (await async_session.execute(
        text("SELECT COUNT(*) FROM favorites WHERE user_id=:u AND book_id=:b"),
        {"u": user_id, "b": book_id},
    )).scalar_one()


@pytest.mark.asyncio
async def test_unique_conflict_email(client: AsyncClient):
    r1 = await client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "pass123456"})
    assert r1.status_code == 201, r1.text

    r2 = await client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "pass123456"})
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_favorites_only_own_two_users_isolated(
    client: AsyncClient,
    login_user,
    async_session: AsyncSession,
):
    book_id = await _seed_author_genre_book(async_session)

    # create 2 users
    u1 = (await client.post("/api/v1/auth/register", json={"email": "u1@example.com", "password": "pass123456"})).json()
    u2 = (await client.post("/api/v1/auth/register", json={"email": "u2@example.com", "password": "pass123456"})).json()
    u1_id, u2_id = u1["id"], u2["id"]

    h1 = await login_user(email="u1@example.com", password="pass123456")
    h2 = await login_user(email="u2@example.com", password="pass123456")

    # u1 adds favorite
    r1 = await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=h1)
    assert r1.status_code == 204, r1.text

    assert await _count_favorites(async_session, u1_id, book_id) == 1
    assert await _count_favorites(async_session, u2_id, book_id) == 0

    # u2 delete same book from "his" favorites (не должно влиять на u1)
    r2 = await client.delete(f"/api/v1/users/me/favorites/{book_id}", headers=h2)
    assert r2.status_code == 204, r2.text

    assert await _count_favorites(async_session, u1_id, book_id) == 1
    assert await _count_favorites(async_session, u2_id, book_id) == 0

    # u2 add favorite independently
    r3 = await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=h2)
    assert r3.status_code == 204, r3.text

    assert await _count_favorites(async_session, u1_id, book_id) == 1
    assert await _count_favorites(async_session, u2_id, book_id) == 1


@pytest.mark.asyncio
async def test_unique_conflict_favorites_pair(
    client: AsyncClient,
    login_user,
    async_session: AsyncSession,
):
    book_id = await _seed_author_genre_book(async_session)

    u = (await client.post("/api/v1/auth/register", json={"email": "favdup@example.com", "password": "pass123456"})).json()
    user_id = u["id"]
    headers = await login_user(email="favdup@example.com", password="pass123456")

    # add first time
    r1 = await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=headers)
    assert r1.status_code == 204, r1.text
    assert await _count_favorites(async_session, user_id, book_id) == 1

    # add second time: допускаем 204 (идемпотентно) ИЛИ 409 (конфликт), но в БД должно остаться 1
    r2 = await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=headers)
    assert r2.status_code in (204, 409), r2.text
    assert await _count_favorites(async_session, user_id, book_id) == 1
