import asyncio
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserSession:
    access_token: str
    role: Optional[str] = None  # "admin" | "client" | None


class InMemorySessionStore:
    """
    Самый простой безопасный вариант для учебного проекта:
    - токен и роль только в памяти (не пишем на диск)
    - при перезапуске бота сессии пропадают
    """
    def __init__(self) -> None:
        self._sessions: dict[int, UserSession] = {}
        self._lock = asyncio.Lock()

    async def set_token(self, user_id: int, token: str) -> None:
        async with self._lock:
            sess = self._sessions.get(user_id)
            if sess:
                sess.access_token = token
            else:
                self._sessions[user_id] = UserSession(access_token=token)

    async def set_role(self, user_id: int, role: Optional[str]) -> None:
        async with self._lock:
            sess = self._sessions.get(user_id)
            if sess:
                sess.role = role

    async def get_token(self, user_id: int) -> Optional[str]:
        async with self._lock:
            sess = self._sessions.get(user_id)
            return sess.access_token if sess else None

    async def get_role(self, user_id: int) -> Optional[str]:
        async with self._lock:
            sess = self._sessions.get(user_id)
            return sess.role if sess else None

    async def is_admin(self, user_id: int) -> bool:
        role = await self.get_role(user_id)
        return role == "admin"

    async def clear(self, user_id: int) -> None:
        async with self._lock:
            self._sessions.pop(user_id, None)
