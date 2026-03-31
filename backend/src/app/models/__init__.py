# Import order matters a bit: ensure tables are registered in Base.metadata

from app.models.base import Base
from app.models.associations import book_authors, book_genres
from app.models.user import User, UserRole
from app.models.author import Author
from app.models.genre import Genre
from app.models.book import Book
from app.models.favorite import Favorite

__all__ = [
    "Base",
    "book_authors",
    "book_genres",
    "User",
    "UserRole",
    "Author",
    "Genre",
    "Book",
    "Favorite",
]
