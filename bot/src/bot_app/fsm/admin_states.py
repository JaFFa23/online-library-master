from aiogram.fsm.state import State, StatesGroup


class AdminAddBookFSM(StatesGroup):
    title = State()
    year = State()
    authors = State()
    genres = State()
    confirm = State()


class AdminDeleteBookFSM(StatesGroup):
    book_id = State()
