from aiogram.fsm.state import State, StatesGroup

class Register(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()
    waiting_for_name = State()
    waiting_for_injury_type = State()
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    completed = State()


class Login(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()
    completed = State()