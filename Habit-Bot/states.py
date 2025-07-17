from aiogram.fsm.state import State, StatesGroup

class AddHabit(StatesGroup):
    waiting_for_habit = State()