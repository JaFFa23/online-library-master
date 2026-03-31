from aiogram import Router, F
from aiogram.types import Message

from aiogram.fsm.context import FSMContext

from bot_app.api.client import LibraryApiClient, ApiError
from bot_app.fsm.book_states import BookSelectFSM
from bot_app.keyboards.book_detail import book_detail_kb
from bot_app.keyboards.main_menu import guest_menu_kb, user_menu_kb
from bot_app.storage.session_store import InMemorySessionStore

router = Router()


@router.message(F.text == "📚 Книги")
async def books_start(
    message: Message,
    state: FSMContext,
    api_client: LibraryApiClient,
    session_store: InMemorySessionStore,
) -> None:
    await state.clear()

    try:
        books = await api_client.get_books()
    except ApiError as e:
        await message.answer(f"Не удалось получить список книг (status={e.status_code}).")
        return

    if not books:
        await message.answer("Список книг пуст.")
        return

    # Покажем короткий список и попросим ID
    lines = ["📚 Список книг (первые 20):"]
    for b in books[:20]:
        year = f" ({b.year})" if b.year else ""
        lines.append(f"• {b.title}{year} — id={b.id}")

    lines.append("\nОтправьте ID книги, чтобы открыть карточку и добавить/удалить из избранного.")
    await state.set_state(BookSelectFSM.book_id)
    await message.answer("\n".join(lines))


@router.message(BookSelectFSM.book_id)
async def book_detail(
    message: Message,
    state: FSMContext,
    api_client: LibraryApiClient,
    session_store: InMemorySessionStore,
) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите числовой ID книги (например: 12) или нажмите ❌ Отмена.")
        return

    book_id = int(raw)
    try:
        book = await api_client.get_book(book_id)
    except ApiError as e:
        if e.status_code == 404:
            await message.answer("Книга не найдена. Попробуйте другой ID.")
        else:
            await message.answer(f"Не удалось получить книгу (status={e.status_code}).")
        return

    await state.clear()

    text = f"📖 {book.title}\nID: {book.id}"
    if book.year:
        text += f"\nГод: {book.year}"
    if book.description:
        text += f"\n\n{book.description}"

    token = await session_store.get_token(message.from_user.id)
    if not token:
        await message.answer(text + "\n\n🔐 Чтобы управлять избранным — войдите.", reply_markup=guest_menu_kb())
        return

    role = await session_store.get_role(message.from_user.id)
    await message.answer(
        text + "\n\nНиже кнопки для избранного:",
        reply_markup=user_menu_kb(is_admin=(role == "admin")),
    )
    await message.answer("Действия:", reply_markup=book_detail_kb(book_id))
