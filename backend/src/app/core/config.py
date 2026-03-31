from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/src/app/core/config.py -> parents:
# core(0) -> app(1) -> src(2) -> backend(3)
BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = Field(default="online-library", validation_alias="APP_NAME")
    env: str = Field(default="local", validation_alias="ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/online_library",
        validation_alias="DATABASE_URL",
    )

    jwt_secret: str = Field(default="CHANGE_ME_SUPER_SECRET", validation_alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", validation_alias="JWT_ALG")
    jwt_expires_min: int = Field(default=60, validation_alias="JWT_EXPIRES_MIN")

    # Тип = str, чтобы env не пытался парсить JSON в list и не падал.
    # Поддерживаем:
    # 1) CSV-строку
    # 2) JSON-массив
    # По умолчанию CORS выключен, так как web/mini app удалён.
    cors_origins: str = Field(
        default="",
        validation_alias="CORS_ORIGINS",
    )

    def cors_origins_list(self) -> list[str]:
        v = (self.cors_origins or "").strip()
        if not v:
            return []
        if v.startswith("[") and v.endswith("]"):
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return [str(x).strip() for x in data if str(x).strip()]
            except Exception:
                pass
        return [x.strip() for x in v.split(",") if x.strip()]

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()