from __future__ import annotations

import asyncio
from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.base import Base

# ВАЖНО: импортируем модели, чтобы они зарегистрировались в Base.metadata
import app.models  # noqa: F401


# Alembic Config object (читает alembic.ini)
config = context.config

# Настройка логов alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- ВАЖНО для src-layout (на случай если prepend_sys_path не сработал) ---
BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Теперь можно импортировать app.*
from app.core.config import settings
from app.core.db import Base  # target_metadata


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Offline: генерирует SQL без подключения к БД.
    """
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """
    Синхронная функция, которую Alembic вызывает через connection.run_sync(...)
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Online: async engine + запуск миграций.
    """
    # Чтобы в логах/командах показывался реальный URL:
    config.set_main_option("sqlalchemy.url", settings.database_url)

    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
