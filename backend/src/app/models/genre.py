from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    books: Mapped[list["Book"]] = relationship(
        secondary="book_genres",
        back_populates="genres",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Genre(id={self.id!r}, name={self.name!r})"
