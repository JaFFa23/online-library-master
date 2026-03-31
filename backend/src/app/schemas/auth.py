from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema


def _validate_bcrypt_password(password: str) -> str:
    # bcrypt ограничен 72 байтами (UTF-8!)
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password is too long for bcrypt (max 72 bytes in UTF-8).")
    return password


class AuthRegisterRequest(BaseSchema):
    email: EmailStr
    # ограничим и по символам, и отдельно проверим байты
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_bcrypt_password(v)


class AuthLoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_bcrypt_password(v)


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
