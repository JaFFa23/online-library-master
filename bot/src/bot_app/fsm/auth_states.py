from aiogram.fsm.state import State, StatesGroup


class RegisterFSM(StatesGroup):
    email = State()
    password = State()


class LoginFSM(StatesGroup):
    email = State()
    password = State()
