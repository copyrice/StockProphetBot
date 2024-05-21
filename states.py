from aiogram.fsm.state import State, StatesGroup


class MainMenu(StatesGroup):
    start = State()

class FindMenu(StatesGroup):
    choosing_category = State()
    entering_symbol = State()

class TickerMenu(StatesGroup):
    ticker_info = State()
    graphs = State()
    waiting_for_days = State()
    description = State()
    recommendations = State()
    news = State()
    indices = State()
    predictions = State()
    report = State()

class PortfolioMenu(StatesGroup):
    main = State()
    waiting_for_time = State()