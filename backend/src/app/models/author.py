from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # back_populates defined in Book
    books: Mapped[list["Book"]] = relationship(
        secondary="book_authors",
        back_populates="authors",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Author(id={self.id!r}, name={self.name!r})"
