from aiogram.fsm.state import State, StatesGroup


class BookSelectFSM(StatesGroup):
    book_id = State()
