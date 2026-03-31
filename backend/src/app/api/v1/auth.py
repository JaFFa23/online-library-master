from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, TokenResponse
from app.schemas.user import UserMeResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserMeResponse,
)
async def register(
    payload: AuthRegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> UserMeResponse:
    service = AuthService(session)
    user = await service.register(email=payload.email, password=payload.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    return UserMeResponse.model_validate(user)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def login(
    payload: AuthLoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    service = AuthService(session)
    token = await service.login(email=payload.email, password=payload.password)

    if token is None:
        # одинаковое сообщение, без утечки что именно неверно
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(access_token=token)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserMeResponse,
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserMeResponse:
    return UserMeResponse.model_validate(current_user)
