from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book


class BooksRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, book_id: int) -> Book | None:
        res = await self.session.execute(select(Book).where(Book.id == book_id))
        return res.scalar_one_or_none()
