from .start import router as start_router
from .auth import router as auth_router
from .books import router as books_router
from .favorites import router as favorites_router
from .admin import router as admin_router

__all__ = ["start_router", "auth_router", "books_router", "favorites_router", "admin_router"]
