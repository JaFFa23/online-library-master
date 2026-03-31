import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_admin_export_forbidden_for_client(client: AsyncClient, get_token):
    headers = await get_token(email="client@example.com")
    r = await client.get("/api/v1/admin/books/export.csv", headers=headers)
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_admin_export_csv_ok(
    client: AsyncClient,
    create_user,
    login_user,
    async_session: AsyncSession,
):
    # создаём пользователя
    user = await create_user(email="admin@example.com")
    user_id = user["id"]

    # делаем admin + добавляем данные
    await async_session.execute(text("UPDATE users SET role='admin' WHERE id=:id"), {"id": user_id})

    author_id = (await async_session.execute(
        text("INSERT INTO authors (name) VALUES ('Author 1') RETURNING id;")
    )).scalar_one()

    genre_id = (await async_session.execute(
        text("INSERT INTO genres (name) VALUES ('Genre 1') RETURNING id;")
    )).scalar_one()

    book_id = (await async_session.execute(
        text("INSERT INTO books (title, year, isbn) VALUES ('Book 1', 2020, 'ISBN1') RETURNING id;")
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

    # запрос от admin (через JWT login)
    headers = await login_user(email="admin@example.com", password="strong_password_123")
    r = await client.get("/api/v1/admin/books/export.csv", headers=headers)
    assert r.status_code == 200, r.text

    assert r.headers.get("content-type", "").startswith("text/csv")
    assert 'attachment; filename="books.csv"' in r.headers.get("content-disposition", "")

    body = r.text
    assert "id,title,year,isbn,authors,genres" in body
    assert "Book 1" in body
    assert "Author 1" in body
    assert "Genre 1" in body
