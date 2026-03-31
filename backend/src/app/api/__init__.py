from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.v1 import v1_router

api_router = APIRouter()

# без префикса
api_router.include_router(health_router, tags=["health"])

# версия API
api_router.include_router(v1_router)