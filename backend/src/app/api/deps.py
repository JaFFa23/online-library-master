from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.users_repo import UsersRepository

bearer_scheme = HTTPBearer(auto_error=False)


def _raise_unauthorized(detail: str = "Not authenticated") -> None:
    # Единый стиль: HTTPException -> обработчик вернёт {error, details}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> User:
    """Get current user.

    Primary auth: Authorization: Bearer <jwt>

    Backward-compatible dev auth (optional): X-User-Id header.
    Allowed only in env in {local,test} to keep local/dev workflows.
    """
    users_repo = UsersRepository(session)

    # 1) JWT Bearer
    if credentials is not None:
        token = credentials.credentials
        if not token:
            _raise_unauthorized("Invalid authentication credentials")

        try:
            payload = decode_access_token(token)
        except JWTError as exc:
            # Не раскрываем клиенту детали, но логируем для отладки.
            logger.warning("JWT decode failed: {}", exc)
            _raise_unauthorized("Invalid authentication credentials")

        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub:
            _raise_unauthorized("Invalid authentication credentials")

        try:
            user_id = int(sub)
        except ValueError:
            _raise_unauthorized("Invalid authentication credentials")

        user = await users_repo.get_by_id(user_id)
        if user is None:
            _raise_unauthorized("Invalid authentication credentials")

        return user

    # 2) DEV fallback: X-User-Id
    if x_user_id is not None and settings.env in ("local", "test"):
        user = await users_repo.get_by_id(x_user_id)
        if user is None:
            _raise_unauthorized("User not found")
        return user

    _raise_unauthorized("Not authenticated")


async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Explicit dependency for endpoints that require any authenticated user."""
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return current_user
