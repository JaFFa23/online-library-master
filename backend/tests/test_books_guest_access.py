import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _pick_books_base() -> list[str]:
    # поддержим оба варианта, если ты вдруг сделал без /api/v1
    return ["/api/v1/books", "/books"]


async def _detect_books_base(client: AsyncClient) -> str:
    for base in _pick_books_base():
        r = await client.get(base)
        if r.status_code != 404:
            return base
    raise AssertionError("Books endpoint not found. Expected /api/v1/books or /books")


async def _seed_author_genre_book(async_session: AsyncSession) -> int:
    author_id = (await async_session.execute(
        text("INSERT INTO authors (name) VALUES ('Author Test') RETURNING id;")
    )).scalar_one()

    genre_id = (await async_session.execute(
        text("INSERT INTO genres (name) VALUES ('Genre Test') RETURNING id;")
    )).scalar_one()

    book_id = (await async_session.execute(
        text("INSERT INTO books (title, description, year, isbn) VALUES ('Book Test', 'Desc', 2024, 'ISBN-TEST') RETURNING id;")
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


@pytest.mark.asyncio
async def test_guest_can_get_books_list_and_detail(
    client: AsyncClient,
    async_session: AsyncSession,
):
    book_id = await _seed_author_genre_book(async_session)
    books_base = await _detect_books_base(client)

    # guest list
    r_list = await client.get(books_base)
    assert r_list.status_code == 200, r_list.text
    data = r_list.json()
    assert isinstance(data, list)
    assert any(item.get("id") == book_id for item in data)

    # guest detail
    r_detail = await client.get(f"{books_base}/{book_id}")
    assert r_detail.status_code == 200, r_detail.text
    d = r_detail.json()
    assert d["id"] == book_id
    assert d["title"] == "Book Test"
    assert "authors" in d and isinstance(d["authors"], list)
    assert "genres" in d and isinstance(d["genres"], list)
