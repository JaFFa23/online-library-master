from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings


def create_access_token(*, sub: str, role: str) -> str:
    """Create JWT access token.

    Payload:
      - sub: user_id as string
      - role: user role (admin/client)
      - exp: expiration datetime
    """
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_min)
    payload = {
        "sub": sub,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT access token.

    Raises jose.exceptions.JWTError (or subclasses) on invalid/expired token.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
