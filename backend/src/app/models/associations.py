from __future__ import annotations

import sqlalchemy as sa

from app.models.base import Base

# M2M: books <-> authors
book_authors = sa.Table(
    "book_authors",
    Base.metadata,
    sa.Column("book_id", sa.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("author_id", sa.ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
)

# M2M: books <-> genres
book_genres = sa.Table(
    "book_genres",
    Base.metadata,
    sa.Column("book_id", sa.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("genre_id", sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)
