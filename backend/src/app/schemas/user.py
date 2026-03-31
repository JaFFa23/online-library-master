from pydantic import EmailStr

from app.schemas.base import BaseSchema


class UserMeResponse(BaseSchema):
    id: int
    email: EmailStr
    role: str  # "admin" | "client"
