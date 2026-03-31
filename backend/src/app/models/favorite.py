from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Favorite(Base):
    __tablename__ = "favorites"

    # Уникальность пары (user_id, book_id) обеспечивается композитным PRIMARY KEY
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="favorites",
        lazy="selectin",
    )
    book: Mapped["Book"] = relationship(
        back_populates="favorites",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Favorite(user_id={self.user_id!r}, book_id={self.book_id!r})"
