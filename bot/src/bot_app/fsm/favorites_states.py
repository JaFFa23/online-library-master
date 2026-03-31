from aiogram.fsm.state import State, StatesGroup


class FavoritesFSM(StatesGroup):
    action = State()   # "add" | "del"
    book_id = State()
