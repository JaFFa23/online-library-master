import asyncio
from typing import Optional


class InMemoryTokenStore:
    """
    Простой in-memory storage: user_id -> access_token.
    Плюсы: максимально просто, токены не пишутся на диск.
    Минус: при перезапуске бота токены исчезают.
    """
    def __init__(self) -> None:
        self._tokens: dict[int, str] = {}
        self._lock = asyncio.Lock()

    async def set(self, user_id: int, token: str) -> None:
        async with self._lock:
            self._tokens[user_id] = token

    async def get(self, user_id: int) -> Optional[str]:
        async with self._lock:
            return self._tokens.get(user_id)

    async def delete(self, user_id: int) -> None:
        async with self._lock:
            self._tokens.pop(user_id, None)
