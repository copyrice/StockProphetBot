import asyncio
from AsyncDatabaseInteractor import AsyncDatabaseInteractor
from ExchangeRateAsyncHandler import ExchangeRateAsyncHandler
from TelegramBot import TelegramBot, dp
from TelegramMessage import TelegramMessage

telegram_bot = TelegramBot()
async_exchange_rate_handler = ExchangeRateAsyncHandler()
# async_database_interactor = AsyncDatabaseInteractor('database.db')


async def change_course_in_channel():
    global recent_course_rub
    while True:
        resp = await async_exchange_rate_handler.get_exchange_rate('USD')
        recent_course_rub = resp['rates']['RUB']
        await telegram_bot.edit_course_message_in_main_channel(TelegramMessage.create_course_message(resp['rates']))
        await asyncio.sleep(10)

async def main():
    await dp.start_polling(telegram_bot.bot)


async def main_execution():
    await asyncio.gather(main(), change_course_in_channel())

asyncio.run(main_execution())