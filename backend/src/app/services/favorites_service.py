from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.repositories.books_repo import BooksRepository
from app.repositories.favorites_repo import FavoritesRepository


class FavoritesService:
    def __init__(self, session: AsyncSession) -> None:
        self.books = BooksRepository(session)
        self.favorites = FavoritesRepository(session)

    async def add_favorite(self, *, user_id: int, book_id: int) -> str:
        """
        returns: "created" | "exists" | "book_not_found"
        """
        book = await self.books.get_by_id(book_id)
        if book is None:
            return "book_not_found"

        if await self.favorites.exists(user_id=user_id, book_id=book_id):
            return "exists"

        try:
            await self.favorites.add(user_id=user_id, book_id=book_id)
            return "created"
        except IntegrityError:
            return "exists"

    async def remove_favorite(self, *, user_id: int, book_id: int) -> str:
        """
        Идемпотентное удаление:
        returns: "deleted" | "missing" | "book_not_found"
        """
        book = await self.books.get_by_id(book_id)
        if book is None:
            return "book_not_found"

        deleted = await self.favorites.delete(user_id=user_id, book_id=book_id)
        return "deleted" if deleted > 0 else "missing"
