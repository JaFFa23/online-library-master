import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _pick_books_base() -> list[str]:
    return ["/api/v1/books", "/books"]


async def _detect_books_base(client: AsyncClient) -> str:
    for base in _pick_books_base():
        r = await client.get(base)
        if r.status_code != 404:
            return base
    raise AssertionError("Books endpoint not found. Expected /api/v1/books or /books")


async def _seed_author_genre(async_session: AsyncSession) -> tuple[int, int]:
    author_id = (await async_session.execute(
        text("INSERT INTO authors (name) VALUES ('Author Seed') RETURNING id;")
    )).scalar_one()

    genre_id = (await async_session.execute(
        text("INSERT INTO genres (name) VALUES ('Genre Seed') RETURNING id;")
    )).scalar_one()

    await async_session.commit()
    return author_id, genre_id


async def _seed_book(async_session: AsyncSession) -> int:
    book_id = (await async_session.execute(
        text("INSERT INTO books (title, description, year, isbn) VALUES ('Book For Delete', 'D', 2020, 'ISBN-DEL') RETURNING id;")
    )).scalar_one()
    await async_session.commit()
    return book_id


@pytest.mark.asyncio
async def test_guest_cannot_access_favorites_and_admin(client: AsyncClient):
    # guest favorites
    r1 = await client.post("/api/v1/users/me/favorites/1")
    assert r1.status_code in (401, 403), r1.text

    # guest admin export
    r2 = await client.get("/api/v1/admin/books/export.csv")
    assert r2.status_code in (401, 403), r2.text


@pytest.mark.asyncio
async def test_client_cannot_write_books_and_export_csv(
    client: AsyncClient,
    get_token,
    async_session: AsyncSession,
):
    books_base = await _detect_books_base(client)
    headers = await get_token(email="client1@example.com")  # role=client by default

    author_id, genre_id = await _seed_author_genre(async_session)
    book_id = await _seed_book(async_session)

    # client export forbidden
    r_export = await client.get("/api/v1/admin/books/export.csv", headers=headers)
    assert r_export.status_code == 403, r_export.text

    # client POST book forbidden
    payload = {
        "title": "Client Cannot Create",
        "description": "x",
        "year": 2021,
        "isbn": "ISBN-CLIENT",
        "authors": [author_id],
        "genres": [genre_id],
    }
    r_post = await client.post(books_base, json=payload, headers=headers)
    assert r_post.status_code == 403, r_post.text

    # client DELETE book forbidden
    r_del = await client.delete(f"{books_base}/{book_id}", headers=headers)
    assert r_del.status_code == 403, r_del.text


@pytest.mark.asyncio
async def test_admin_can_export_csv_and_manage_books(
    client: AsyncClient,
    create_user,
    login_user,
    async_session: AsyncSession,
):
    books_base = await _detect_books_base(client)

    # create admin user
    admin = await create_user(email="admin1@example.com")
    admin_id = admin["id"]

    # set admin role in DB
    await async_session.execute(
        text("UPDATE users SET role='admin' WHERE id=:id"),
        {"id": admin_id},
    )
    await async_session.commit()

    # логинимся после апдейта роли, чтобы role в JWT совпадала
    headers_admin = await login_user(email="admin1@example.com", password="strong_password_123")

    author_id, genre_id = await _seed_author_genre(async_session)

    # admin POST book (основной вариант: authors/genres = ids)
    payload_ids = {
        "title": "Admin Created",
        "description": "desc",
        "year": 2022,
        "isbn": "ISBN-ADMIN",
        "authors": [author_id],
        "genres": [genre_id],
    }
    r_post = await client.post(books_base, json=payload_ids, headers=headers_admin)

    # если у тебя внезапно схема принимает list[str], дадим fallback (чтобы не ломать прогресс)
    if r_post.status_code == 422:
        payload_names = {
            "title": "Admin Created",
            "description": "desc",
            "year": 2022,
            "isbn": "ISBN-ADMIN",
            "authors": ["Author Seed"],
            "genres": ["Genre Seed"],
        }
        r_post = await client.post(books_base, json=payload_names, headers=headers_admin)

    assert r_post.status_code in (200, 201), r_post.text
    created = r_post.json()
    created_id = created.get("id")
    assert isinstance(created_id, int) and created_id > 0

    # admin export csv ok
    r_csv = await client.get("/api/v1/admin/books/export.csv", headers=headers_admin)
    assert r_csv.status_code == 200, r_csv.text
    assert r_csv.headers.get("content-type", "").startswith("text/csv")
    assert 'attachment; filename="books.csv"' in r_csv.headers.get("content-disposition", "")
    assert "id,title,year,isbn,authors,genres" in r_csv.text
    assert "Admin Created" in r_csv.text

    # admin delete book
    r_del = await client.delete(f"{books_base}/{created_id}", headers=headers_admin)
    assert r_del.status_code in (200, 204), r_del.text
