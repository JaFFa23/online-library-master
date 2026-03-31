from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.favorite import Favorite


class FavoritesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists(self, *, user_id: int, book_id: int) -> bool:
        res = await self.session.execute(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.book_id == book_id)
        )
        return res.scalar_one_or_none() is not None

    async def add(self, *, user_id: int, book_id: int) -> None:
        fav = Favorite(user_id=user_id, book_id=book_id)
        self.session.add(fav)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise

    async def delete(self, *, user_id: int, book_id: int) -> int:
        """
        Возвращает число удалённых строк (0 или 1).
        """
        stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.book_id == book_id)
        res = await self.session.execute(stmt)
        await self.session.commit()
        return int(res.rowcount or 0)
