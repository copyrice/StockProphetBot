import asyncio
from apscheduler import AsyncIOScheduler

from database.database import db_get_portfolio_by_user_tg_id

async def send_report(bot, chat_id: int, report_message: str):
        await bot.send_message(chat_id, report_message)

class Scheduler:
    def __init__(self, db_session) -> None:
        self.tasks = {}
        self.db_session = db_session
    

    async def generate_report(chat_id)

    async def create_task(time, chat_id):
        task = aioschedule.every().day.at(time).do(send_report, chat_id, await generate_report())

    async def del_task(self, tg_id: int):
        del self.tasks[tg_id]