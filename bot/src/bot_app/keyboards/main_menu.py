from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def guest_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="📚 Книги")],
        [KeyboardButton(text="🔑 Вход"), KeyboardButton(text="📝 Регистрация")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def user_menu_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="📚 Книги"), KeyboardButton(text="⭐ Избранное")]
    ]

    if is_admin:
        rows.append([KeyboardButton(text="🛠 Админ")])

    rows.append([KeyboardButton(text="🚪 Выйти")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Меню",
    )


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить книгу")],
            [KeyboardButton(text="🗑 Удалить книгу")],
            [KeyboardButton(text="⬇️ Экспорт CSV")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Админ-меню",
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        input_field_placeholder="Отмена",
    )


def confirm_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Подтверждение",
    )