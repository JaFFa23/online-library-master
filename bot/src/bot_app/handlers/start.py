from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot_app.api.client import LibraryApiClient, ApiError
from bot_app.keyboards.main_menu import guest_menu_kb, user_menu_kb
from bot_app.storage.session_store import InMemorySessionStore

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    api_client: LibraryApiClient,
    session_store: InMemorySessionStore,
) -> None:
    user_id = message.from_user.id
    token = await session_store.get_token(user_id)

    guest_text = (
        "Привет! Я бот онлайн-библиотеки.\n\n"
        "Гостю доступно: 📚 Книги.\n"
        "Для избранного и админ-меню нужно войти."
    )

    if not token:
        await message.answer(
            guest_text,
            reply_markup=guest_menu_kb(),
        )
        return

    try:
        role = await api_client.detect_role(token)
        await session_store.set_role(user_id, role)

        auth_text = f"Вы авторизованы. Роль: {role or 'не определена'}"
        await message.answer(
            auth_text,
            reply_markup=user_menu_kb(is_admin=(role == "admin")),
        )

    except ApiError as e:
        if e.status_code == 401:
            await session_store.clear(user_id)
            await message.answer(
                "Сессия истекла. Войдите заново.",
                reply_markup=guest_menu_kb(),
            )
        else:
            is_admin = await session_store.is_admin(user_id)
            await message.answer(
                f"⚠️ Не удалось обновить профиль (status={e.status_code}).",
                reply_markup=user_menu_kb(is_admin=is_admin),
            )