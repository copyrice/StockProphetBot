from typing import Any
from aiogram_dialog import ChatEvent, DialogManager, Data
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button
from aiogram.types import BufferedInputFile
# from pages.ticker_info import layout
from repo import TickerPortfolio, JsonSerializer
from database.database import db_update_portfolio, db_get_portfolio_by_user_id, db_get_user_by_tg_id



async def on_ticker_menu_result(start_data: Data, result: Any,
                              dialog_manager: DialogManager):
    pass

