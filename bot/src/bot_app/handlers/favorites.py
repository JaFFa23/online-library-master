from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot_app.api.client import LibraryApiClient, ApiError
from bot_app.keyboards.main_menu import guest_menu_kb
from bot_app.storage.session_store import InMemorySessionStore

router = Router()


@router.message(F.text == "⭐ Избранное")
async def favorites_list(
    message: Message,
    api_client: LibraryApiClient,
    session_store: InMemorySessionStore,
) -> None:
    token = await session_store.get_token(message.from_user.id)
    if not token:
        await message.answer("🔐 Нужно войти, чтобы смотреть избранное.", reply_markup=guest_menu_kb())
        return

    try:
        favs = await api_client.get_favorites(token)
    except ApiError as e:
        if e.status_code == 404:
            await message.answer(
                "⚠️ Сервер пока не поддерживает получение списка избранного.\n"
                "Нужно добавить endpoint GET /users/me/favorites в backend.\n\n"
                "При этом добавление/удаление работает (через карточку книги)."
            )
            return
        if e.status_code == 401:
            await session_store.clear(message.from_user.id)
            await message.answer("Сессия истекла. Войдите заново.", reply_markup=guest_menu_kb())
            return
        await message.answer(f"Не удалось получить избранное (status={e.status_code}).")
        return

    if not favs:
        await message.answer("⭐ Избранное пусто.\n\nОткройте книгу (📚 Книги → ID) и нажмите «➕ В избранное».")
        return

    lines = ["⭐ Ваше избранное:"]
    for b in favs[:30]:
        lines.append(f"• {b.title} — id={b.id}")
    if len(favs) > 30:
        lines.append(f"\n…и ещё {len(favs) - 30} книг.")

    lines.append("\nЧтобы удалить: откройте книгу по ID и нажмите «➖ Удалить».")
    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("fav:add:"))
async def fav_add_cb(
    cq: CallbackQuery,
    api_client: LibraryApiClient,
    session_store: InMemorySessionStore,
) -> None:
    await cq.answer()
    token = await session_store.get_token(cq.from_user.id)
    if not token:
        await cq.message.answer("🔐 Нужно войти, чтобы добавлять в избранное.")
        return

    book_id = int(cq.data.split(":")[-1])
    try:
        await api_client.add_favorite(token, book_id)
        await cq.message.answer(f"✅ Книга id={book_id} добавлена в избранное.")
    except ApiError as e:
        if e.status_code == 409:
            await cq.message.answer("ℹ️ Эта книга уже есть в избранном.")
        elif e.status_code == 404:
            await cq.message.answer("Книга не найдена.")
        elif e.status_code == 401:
            await session_store.clear(cq.from_user.id)
            await cq.message.answer("Сессия истекла. Войдите заново.")
        else:
            await cq.message.answer(f"Не удалось добавить в избранное (status={e.status_code}).")


@router.callback_query(F.data.startswith("fav:del:"))
async def fav_del_cb(
    cq: CallbackQuery,
    api_client: LibraryApiClient,
    session_store: InMemorySessionStore,
) -> None:
    await cq.answer()
    token = await session_store.get_token(cq.from_user.id)
    if not token:
        await cq.message.answer("🔐 Нужно войти, чтобы удалять из избранного.")
        return

    book_id = int(cq.data.split(":")[-1])
    try:
        await api_client.del_favorite(token, book_id)
        await cq.message.answer(f"✅ Книга id={book_id} удалена из избранного.")
    except ApiError as e:
        if e.status_code == 404:
            await cq.message.answer("ℹ️ Этой книги нет в избранном (или книга не найдена).")
        elif e.status_code == 401:
            await session_store.clear(cq.from_user.id)
            await cq.message.answer("Сессия истекла. Войдите заново.")
        else:
            await cq.message.answer(f"Не удалось удалить из избранного (status={e.status_code}).")
