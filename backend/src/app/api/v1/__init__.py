from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.books import router as books_router
from app.api.v1.users import router as users_router
from app.api.v1.admin import router as admin_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(books_router)
v1_router.include_router(users_router)
v1_router.include_router(admin_router)
