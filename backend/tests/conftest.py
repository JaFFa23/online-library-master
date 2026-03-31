from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncIterator, Callable

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# --- src-layout imports: import app.*
BACKEND_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- Test database url (Postgres test on host port 5433)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/online_library_test",
)

# Alembic env.py у тебя берёт url из Settings(DATABASE_URL) -> подменяем для тестов
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("ENV", "test")
os.environ.setdefault("APP_NAME", "online-library-test")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALG", "HS256")
os.environ.setdefault("JWT_EXPIRES_MIN", "60")


# ✅ ВАЖНО: loop = function-scope, engine = function-scope и engine зависит от loop
@pytest.fixture(scope="function")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
    asyncio.set_event_loop(None)


# ✅ Миграции запускаем синхронно (до запуска async-тестов)
@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="function")
def db_engine(event_loop) -> AsyncEngine:
    """
    Engine на каждый тест + NullPool => никаких соединений между тестами/лупами.
    Это критично на Windows.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    return engine


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_db(db_engine: AsyncEngine) -> AsyncIterator[None]:
    """
    Перед каждым тестом: TRUNCATE всех таблиц (кроме alembic_version).
    """
    async with db_engine.begin() as conn:
        res = await conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename <> 'alembic_version';
                """
            )
        )
        tables = [row[0] for row in res.fetchall()]
        if tables:
            quoted = ", ".join(f'"{t}"' for t in tables)
            await conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE;"))
    yield

    # ✅ гарантированно закрываем все ресурсы до закрытия event loop
    await db_engine.dispose()


@pytest.fixture(scope="function")
def async_session_maker(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def async_session(async_session_maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="session")
def app():
    # импорт после установки env-переменных
    from app.main import create_app
    return create_app()


@pytest_asyncio.fixture(scope="function")
async def client(app, async_session_maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncClient]:
    """
    httpx AsyncClient по ASGI + override get_session -> тестовая БД.
    """
    from app.core.db import get_session

    async def override_get_session():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def create_user(client: AsyncClient) -> Callable[..., dict]:
    async def _create_user(email: str = "user@example.com", password: str = "strong_password_123") -> dict:
        resp = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _create_user


@pytest_asyncio.fixture(scope="function")
async def login_user(client: AsyncClient) -> Callable[..., dict]:
    """Login existing user and return Authorization headers."""

    async def _login_user(email: str = "user@example.com", password: str = "strong_password_123") -> dict:
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        token = data["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login_user


@pytest_asyncio.fixture(scope="function")
async def get_token(create_user: Callable[..., dict], login_user: Callable[..., dict]) -> Callable[..., dict]:
    """Create user (register) and return Bearer JWT headers."""

    async def _get_token(email: str = "user@example.com", password: str = "strong_password_123") -> dict:
        await create_user(email=email, password=password)
        return await login_user(email=email, password=password)

    return _get_token
