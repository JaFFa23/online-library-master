from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class BookDTO(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    title: str
    year: Optional[int] = None
    description: Optional[str] = None
    authors: Optional[List[Any]] = None
    genres: Optional[List[Any]] = None


class TokenDTO(BaseModel):
    access_token: str
    token_type: str


class MeDTO(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    email: str
    role: str  # "admin" | "client"
