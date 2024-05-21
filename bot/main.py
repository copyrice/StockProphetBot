import asyncio
from config import BOT_TOKEN, DB_PATH

import subprocess
import dash_server

from aiogram.filters import CommandStart, Command

from aiogram import Router, Bot, Dispatcher
from aiogram.types import Message

from aiogram_dialog import setup_dialogs, DialogManager, StartMode
from aiogram_dialog import setup_dialogs

from dialogs import dialogs
from states import TickerMenu, MainMenu, FindMenu, PortfolioMenu

from middlewares.translator_md import TranslatorMiddleware
from middlewares.db import DbSessionMiddleware
from middlewares.predictor_md import PredictorMiddleware
from middlewares.scheduler_md import SchedulerMiddleware

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.database import db_register_user, db_get_all_users_with_enabled_notifications
from models.base import Base

from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = Router()



async def start(message: Message, dialog_manager: DialogManager):
    db_session = dialog_manager.middleware_data.get('db_session')
    await db_register_user(message, db_session)
    await dialog_manager.start(MainMenu.start, mode=StartMode.RESET_STACK)

async def command_find(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(FindMenu.choosing_category)

async def db_main(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    bot = Bot(token=BOT_TOKEN)
    engine = create_async_engine(url=DB_PATH, echo=True)
    await db_main(engine)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    dp = Dispatcher()
    scheduler = AsyncIOScheduler()
    for dialog in dialogs:
        dp.include_router(dialog)
    dp.update.middleware(TranslatorMiddleware())
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dp.update.middleware(PredictorMiddleware())
    dp.update.middleware(SchedulerMiddleware(scheduler))
    dp.message.register(start, CommandStart())
    dp.message.register(command_find, Command(commands=["find"]))
    dp.include_router(router)
    setup_dialogs(dp)

    # def run_dash_server():
        # app.run_server(debug=True, use_reloader=False)

    # thread = threading.Thread(target=run_dash_server)
    # thread.start()
    subprocess.Popen(['python', 'dash_server.py'])
    scheduler.start()
    await dp.start_polling(bot)


asyncio.run(main())