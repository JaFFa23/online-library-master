from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, List, Optional

import httpx

from bot_app.api.dtos import BookDTO, TokenDTO, MeDTO

log = logging.getLogger("bot.api")


class ApiError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass
class CsvFile:
    filename: str
    content: bytes
    content_type: str = "text/csv"


def _jwt_get_claim(token: str, key: str) -> Optional[Any]:
    """
    Fallback: читаем payload JWT без верификации подписи.
    Предпочтительно определять роль через /auth/me.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        data = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload = json.loads(data.decode("utf-8"))
        return payload.get(key)
    except Exception:
        return None


def _extract_filename_from_cd(cd: str) -> Optional[str]:
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


class LibraryApiClient:
    """
    base_url ожидается вида: http://host:8000/api/v1
    """

    def __init__(self, base_url: str, timeout_s: float = 15.0):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_s),
            headers={"Accept": "application/json"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _raise_for_bad_response(self, resp: httpx.Response, action: str) -> None:
        if resp.status_code < 400:
            return

        content_type = resp.headers.get("content-type", "")
        text_preview = resp.text[:800]

        payload: Any = text_preview
        if "application/json" in content_type:
            try:
                payload = resp.json()
            except Exception:
                payload = text_preview

        log.error("%s failed: status=%s payload=%s", action, resp.status_code, payload)
        raise ApiError(status_code=resp.status_code, message=f"Ошибка API при {action}", payload=payload)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[dict[str, str]] = None,
        json_body: Any = None,
    ) -> httpx.Response:
        # чистый URL для лога без двойных слешей
        base = str(self._client.base_url).rstrip("/")
        url = f"{base}{path}"
        log.info("%s %s", method.upper(), url)

        try:
            return await self._client.request(method, path, headers=headers, json=json_body)
        except httpx.RequestError as e:
            log.exception("Request error: %s", e)
            raise ApiError(status_code=0, message="API недоступно") from e

    # --- Auth ---
    async def register(self, email: str, password: str) -> Any:
        resp = await self._request("POST", "/auth/register", json_body={"email": email, "password": password})
        self._raise_for_bad_response(resp, "регистрации")
        return resp.json()

    async def login(self, email: str, password: str) -> TokenDTO:
        resp = await self._request("POST", "/auth/login", json_body={"email": email, "password": password})
        self._raise_for_bad_response(resp, "входе")
        return TokenDTO.model_validate(resp.json())

    async def me(self, token: str) -> MeDTO:
        resp = await self._request("GET", "/auth/me", headers=self._auth_headers(token))
        self._raise_for_bad_response(resp, "получении профиля /auth/me")
        return MeDTO.model_validate(resp.json())

    async def detect_role(self, token: str) -> Optional[str]:
        try:
            me = await self.me(token)
            return me.role
        except ApiError as e:
            if e.status_code in (404, 405):
                return _jwt_get_claim(token, "role")
            return _jwt_get_claim(token, "role")

    # --- Books (public) ---
    async def get_books(self) -> List[BookDTO]:
        resp = await self._request("GET", "/books")
        self._raise_for_bad_response(resp, "получении списка книг")

        data = resp.json()
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and isinstance(data.get("items"), list):
            items = data["items"]
        elif isinstance(data, dict) and isinstance(data.get("data"), list):
            items = data["data"]
        else:
            raise ApiError(status_code=500, message="Неожиданный формат ответа /books", payload=data)

        return [BookDTO.model_validate(x) for x in items]

    async def get_book(self, book_id: int) -> BookDTO:
        resp = await self._request("GET", f"/books/{book_id}")
        self._raise_for_bad_response(resp, "получении карточки книги")
        return BookDTO.model_validate(resp.json())

    # --- Favorites (auth) ---
    async def get_favorites(self, token: str) -> List[BookDTO]:
        resp = await self._request("GET", "/users/me/favorites", headers=self._auth_headers(token))
        self._raise_for_bad_response(resp, "получении избранного")

        data = resp.json()
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and isinstance(data.get("items"), list):
            items = data["items"]
        elif isinstance(data, dict) and isinstance(data.get("data"), list):
            items = data["data"]
        else:
            raise ApiError(status_code=500, message="Неожиданный формат ответа favorites", payload=data)

        return [BookDTO.model_validate(x) for x in items]

    async def add_favorite(self, token: str, book_id: int) -> None:
        resp = await self._request("POST", f"/users/me/favorites/{book_id}", headers=self._auth_headers(token))
        self._raise_for_bad_response(resp, "добавлении в избранное")

    async def del_favorite(self, token: str, book_id: int) -> None:
        resp = await self._request("DELETE", f"/users/me/favorites/{book_id}", headers=self._auth_headers(token))
        self._raise_for_bad_response(resp, "удалении из избранного")

    # --- Books (admin) ---
    def _parse_list(self, raw: str) -> list[int] | list[str]:
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not parts:
            return []
        if all(p.isdigit() for p in parts):
            return [int(p) for p in parts]
        return parts

    async def create_book(
        self,
        token: str,
        title: str,
        year: int,
        authors_raw: str,
        genres_raw: str,
    ) -> BookDTO:
        # ВАЖНО: backend ожидает authors/genres именно как список (ids или names)
        authors = self._parse_list(authors_raw)
        genres = self._parse_list(genres_raw)

        payload: dict[str, Any] = {
            "title": title,
            "year": year,
            "authors": authors,
            "genres": genres,
        }

        resp = await self._request("POST", "/books", headers=self._auth_headers(token), json_body=payload)
        self._raise_for_bad_response(resp, "создании книги")
        return BookDTO.model_validate(resp.json())

    async def delete_book(self, token: str, book_id: int) -> None:
        resp = await self._request("DELETE", f"/books/{book_id}", headers=self._auth_headers(token))
        self._raise_for_bad_response(resp, "удалении книги")

    # --- Export (admin) ---
    async def export_books_csv(self, token: str) -> CsvFile:
        resp = await self._request("GET", "/admin/books/export.csv", headers=self._auth_headers(token))
        if resp.status_code >= 400:
            self._raise_for_bad_response(resp, "экспорте CSV")

        cd = resp.headers.get("content-disposition", "")
        filename = _extract_filename_from_cd(cd) or "books_export.csv"
        content_type = resp.headers.get("content-type", "text/csv")
        return CsvFile(filename=filename, content=resp.content, content_type=content_type)
