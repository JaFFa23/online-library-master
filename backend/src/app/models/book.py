from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # optional unique (Postgres допускает несколько NULL в UNIQUE)
    isbn: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    authors: Mapped[list["Author"]] = relationship(
        secondary="book_authors",
        back_populates="books",
        lazy="selectin",
    )

    genres: Mapped[list["Genre"]] = relationship(
        secondary="book_genres",
        back_populates="books",
        lazy="selectin",
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Book(id={self.id!r}, title={self.title!r}, year={self.year!r}, isbn={self.isbn!r})"
