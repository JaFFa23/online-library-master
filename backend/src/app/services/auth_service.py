from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token
from app.repositories.users_repo import UsersRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users_repo = UsersRepository(session)

    async def register(self, *, email: str, password: str):
        # нормализация (на всякий)
        email_norm = email.strip().lower()

        existing = await self.users_repo.get_by_email(email_norm)
        if existing:
            return None  # сигнал "занято"

        password_hash = pwd_context.hash(password)

        try:
            user = await self.users_repo.create(email=email_norm, password_hash=password_hash)
        except IntegrityError:
            # на случай гонки (если два запроса одновременно)
            return None

        return user

    async def login(self, *, email: str, password: str) -> str | None:
        """Validate credentials and return JWT access token.

        IMPORTANT: must not leak whether email or password is wrong.
        """
        email_norm = email.strip().lower()

        user = await self.users_repo.get_by_email(email_norm)
        if user is None:
            return None

        if not pwd_context.verify(password, user.password_hash):
            return None

        # JWT: sub=user_id (string), role, exp
        return create_access_token(sub=str(user.id), role=user.role.value)
