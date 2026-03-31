from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.book import Book
from app.models.favorite import Favorite
from app.models.user import User
from app.schemas.book import BookListItemResponse
from app.services.favorites_service import FavoritesService

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("/favorites", response_model=list[BookListItemResponse])
async def list_favorites(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[BookListItemResponse]:
    stmt = (
        select(Book)
        .join(Favorite, Favorite.book_id == Book.id)
        .where(Favorite.user_id == current_user.id)
        .options(selectinload(Book.authors), selectinload(Book.genres))
        .order_by(Book.id)
    )
    res = await session.execute(stmt)
    books = res.scalars().unique().all()

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


@router.post("/favorites/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    service = FavoritesService(session)
    result = await service.add_favorite(user_id=current_user.id, book_id=book_id)

    if result == "book_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # created/exists -> 204 (идемпотентно)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/favorites/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Поведение зафиксировано:
    - если книги нет -> 404
    - если не было в избранном -> 204 (идемпотентно)
    - если удалили -> 204
    """
    service = FavoritesService(session)
    result = await service.remove_favorite(user_id=current_user.id, book_id=book_id)

    if result == "book_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # deleted/missing -> 204
    return Response(status_code=status.HTTP_204_NO_CONTENT)
