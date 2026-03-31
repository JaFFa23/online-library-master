from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def book_detail_kb(book_id: int) -> InlineKeyboardMarkup:
    # Важно: callback_data <= 64 символов
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ В избранное", callback_data=f"fav:add:{book_id}"),
                InlineKeyboardButton(text="➖ Удалить", callback_data=f"fav:del:{book_id}"),
            ]
        ]
    )
