import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot_app.config import Settings
from bot_app.api.client import LibraryApiClient
from bot_app.handlers import start_router, auth_router, books_router, favorites_router, admin_router
from bot_app.storage.session_store import InMemorySessionStore


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def main() -> None:
    setup_logging()
    settings = Settings()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    api_client = LibraryApiClient(base_url=str(settings.API_BASE_URL))
    session_store = InMemorySessionStore()

    dp["api_client"] = api_client
    dp["session_store"] = session_store
    dp["settings"] = settings  # ✅ добавили

    dp.include_router(start_router)
    dp.include_router(auth_router)
    dp.include_router(books_router)
    dp.include_router(favorites_router)
    dp.include_router(admin_router)

    try:
        await dp.start_polling(bot)
    finally:
        await api_client.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
