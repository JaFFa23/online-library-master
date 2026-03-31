from __future__ import annotations

from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_admin
from app.core.db import get_session
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.schemas.book import BookCreateRequest, BookDetailResponse, BookListItemResponse


router = APIRouter(prefix="/books", tags=["books"])


def _as_list_items(books: Iterable[Book]) -> list[BookListItemResponse]:
    return [
        BookListItemResponse(
            id=b.id,
            title=b.title,
            year=b.year,
            authors=[a.name for a in (b.authors or [])],
            genres=[g.name for g in (b.genres or [])],
        )
        for b in books
    ]


def _as_detail(book: Book) -> BookDetailResponse:
    return BookDetailResponse(
        id=book.id,
        title=book.title,
        description=book.description,
        year=book.year,
        isbn=book.isbn,
        authors=[a.name for a in (book.authors or [])],
        genres=[g.name for g in (book.genres or [])],
    )


async def _load_authors(session: AsyncSession, authors: list[int] | list[str]) -> list[Author]:
    if not authors:
        raise HTTPException(status_code=422, detail="authors must not be empty")

    # by ids
    if isinstance(authors[0], int):
        ids = sorted(set(int(x) for x in authors))
        res = await session.execute(select(Author).where(Author.id.in_(ids)))
        found = list(res.scalars().all())
        if len(found) != len(ids):
            raise HTTPException(status_code=422, detail="One or more author ids not found")
        return found

    # by names (create missing)
    names = []
    seen = set()
    for raw in authors:
        name = str(raw).strip()
        if not name:
            continue
        if name not in seen:
            seen.add(name)
            names.append(name)
    if not names:
        raise HTTPException(status_code=422, detail="authors must not be empty")

    res = await session.execute(select(Author).where(Author.name.in_(names)))
    existing = {a.name: a for a in res.scalars().all()}
    result: list[Author] = []
    for name in names:
        author = existing.get(name)
        if author is None:
            author = Author(name=name)
            session.add(author)
            await session.flush()  # assigns id
        result.append(author)
    return result


async def _load_genres(session: AsyncSession, genres: list[int] | list[str]) -> list[Genre]:
    if not genres:
        raise HTTPException(status_code=422, detail="genres must not be empty")

    # by ids
    if isinstance(genres[0], int):
        ids = sorted(set(int(x) for x in genres))
        res = await session.execute(select(Genre).where(Genre.id.in_(ids)))
        found = list(res.scalars().all())
        if len(found) != len(ids):
            raise HTTPException(status_code=422, detail="One or more genre ids not found")
        return found

    # by names (create missing)
    names = []
    seen = set()
    for raw in genres:
        name = str(raw).strip()
        if not name:
            continue
        if name not in seen:
            seen.add(name)
            names.append(name)
    if not names:
        raise HTTPException(status_code=422, detail="genres must not be empty")

    res = await session.execute(select(Genre).where(Genre.name.in_(names)))
    existing = {g.name: g for g in res.scalars().all()}
    result: list[Genre] = []
    for name in names:
        genre = existing.get(name)
        if genre is None:
            genre = Genre(name=name)
            session.add(genre)
            await session.flush()
        result.append(genre)
    return result


@router.get("", response_model=list[BookListItemResponse])
async def list_books(session: AsyncSession = Depends(get_session)) -> list[BookListItemResponse]:
    stmt = (
        select(Book)
        .options(selectinload(Book.authors), selectinload(Book.genres))
        .order_by(Book.id)
    )
    res = await session.execute(stmt)
    books = res.scalars().unique().all()
    return _as_list_items(books)


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book(book_id: int, session: AsyncSession = Depends(get_session)) -> BookDetailResponse:
    stmt = (
        select(Book)
        .where(Book.id == book_id)
        .options(selectinload(Book.authors), selectinload(Book.genres))
    )
    res = await session.execute(stmt)
    book = res.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return _as_detail(book)


@router.post("", response_model=BookDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreateRequest,
    session: AsyncSession = Depends(get_session),
    _admin=Depends(require_admin),
) -> BookDetailResponse:
    authors = await _load_authors(session, payload.authors)
    genres = await _load_genres(session, payload.genres)

    book = Book(
        title=payload.title,
        description=payload.description,
        year=payload.year,
        isbn=payload.isbn,
    )
    book.authors = authors
    book.genres = genres
    session.add(book)
    await session.commit()
    await session.refresh(book)
    await session.refresh(book, attribute_names=["authors", "genres"])

    return _as_detail(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    _admin=Depends(require_admin),
) -> Response:
    res = await session.execute(select(Book).where(Book.id == book_id))
    book = res.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    await session.delete(book)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
