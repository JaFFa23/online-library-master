from __future__ import annotations

import csv
import io
from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book


class ExportService:
    async def stream_books_csv(self, session: AsyncSession) -> AsyncIterator[bytes]:
        """
        Генерирует CSV построчно (UTF-8).
        """
        buf = io.StringIO()
        writer = csv.writer(buf)

        # header
        writer.writerow(["id", "title", "year", "isbn", "authors", "genres"])
        yield buf.getvalue().encode("utf-8")
        buf.seek(0)
        buf.truncate(0)

        stmt = (
            select(Book)
            .options(selectinload(Book.authors), selectinload(Book.genres))
            .order_by(Book.id)
        )
        result = await session.execute(stmt)

        for book in result.scalars().unique():
            authors = ";".join(a.name for a in (book.authors or []))
            genres = ";".join(g.name for g in (book.genres or []))

            writer.writerow(
                [
                    book.id,
                    book.title,
                    book.year,
                    book.isbn or "",
                    authors,
                    genres,
                ]
            )
            yield buf.getvalue().encode("utf-8")
            buf.seek(0)
            buf.truncate(0)
