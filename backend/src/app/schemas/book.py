from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class BookListItemResponse(BaseSchema):
    id: int
    title: str
    year: int
    authors: list[str]
    genres: list[str]


class BookDetailResponse(BaseSchema):
    id: int
    title: str
    description: str | None = None
    year: int
    isbn: str | None = None
    authors: list[str]
    genres: list[str]


class BookCreateRequest(BaseSchema):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    year: int = Field(ge=0, le=2100)
    isbn: str | None = Field(default=None, max_length=32)
    authors: list[int] | list[str] = Field(min_length=1)
    genres: list[int] | list[str] = Field(min_length=1)


    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("authors", "genres")
    @classmethod
    def normalize_list(cls, v):
        # ids
        if v and isinstance(v[0], int):
            cleaned = sorted(set(int(x) for x in v))
            if not cleaned:
                raise ValueError("list must contain at least one value")
            return cleaned

        # names
        cleaned: list[str] = []
        for item in v:
            s = str(item).strip()
            if not s:
                continue
            if s not in cleaned:
                cleaned.append(s)
        if not cleaned:
            raise ValueError("list must contain at least one non-empty value")
        return cleaned
