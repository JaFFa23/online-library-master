from fastapi import APIRouter
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, TokenResponse

router = APIRouter(prefix="/auth")

@router.post("/register")
async def register(payload: AuthRegisterRequest):
    # позже: создать пользователя в БД
    return {"ok": True}

@router.post("/login", response_model=TokenResponse)
async def login(payload: AuthLoginRequest) -> TokenResponse:
    # позже: проверить пароль, выдать JWT
    return TokenResponse(access_token="demo-token")
