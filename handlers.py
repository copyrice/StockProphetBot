from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog import DialogManager
from functions import find_ticker, create_ticker_info_startdata, validate_time, get_portfolio_and_send
from aiogram import types
from aiogram.types import BufferedInputFile
from states import TickerMenu, PortfolioMenu
from database.database import db_get_user_by_tg_id, db_set_user_notifications, db_set_user_notifications_time, db_set_user_job_id
from datetime import datetime

async def input_ticker_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
):
    temp_messages = []
    temporary_message = await message.answer(f"Ищу информацию...")
    temp_messages.append(temporary_message)
    dialog_manager.dialog_data["symbol"] = message.text.upper()
    if(dialog_manager.dialog_data['category']=='ir_index' and not message.text.startswith('^')):
        wrong_name_message = await message.answer('Символ международного индекса должен начинаться с символа "^"')
        temp_messages.append(wrong_name_message)
        return
    if(message.text.startswith('^') and dialog_manager.dialog_data['category']!='ir_index'):
        dialog_manager.dialog_data['category'] = 'ir_index'
        wrong_menu_message = await message.answer(f'Вы ввели индекс, перевожу на меню международного индекса...')
        temp_messages.append(wrong_menu_message)


    ticker = await find_ticker(dialog_manager.dialog_data['category'], dialog_manager.dialog_data['symbol'])

    if(ticker):
        # dialog_manager.dialog_data['ticker_object'] = ticker
        # dialog_manager.dialog_data['recent_tickers']['category'] = ticker
        # dialog_manager.dialog_data['recent_ticker'] = ticker
        # dialog_manager.dialog_data['user_tg_id'] = message.from_user.id
        # dialog_manager.dialog_data['parent'] = 'find'
        start_data = await create_ticker_info_startdata(ticker, message.from_user.id)
        await dialog_manager.start(TickerMenu.ticker_info, start_data)
    else:
        non_ticker_message = await message.answer(f'Символ не существует!')
        temp_messages.append(non_ticker_message)

    for message in temp_messages:
        await message.delete()
    # if(non_ticker_message):
        # await non_ticker_message.delete()

    # await temporary_message.delete()
    # if(wrong_menu_message):
        # await wrong_menu_message.delete()


async def input_time_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
):
    if validate_time(message.text):
        time = message.text
        hour, minute = time.split(':')
        hour = int(hour)
        minute = int(minute)
    else:
        await message.answer("Пожалуйста, введите корректное значение времени формата HH:MM")
        return
    
    db_session = dialog_manager.middleware_data.get('db_session')
    user = await db_get_user_by_tg_id(message.from_user.id, db_session)
    if(user):
        await db_set_user_notifications(db_session, user, True)
        await db_set_user_notifications_time(db_session, user, time)
        scheduler = dialog_manager.middleware_data.get('scheduler')
        job = scheduler.add_job(get_portfolio_and_send, "cron",  hour=hour, minute=minute, args=(db_session, message.from_user.id, message),
                    timezone='Europe/Moscow')
        await db_set_user_job_id(db_session, user, job.id)
        # print(job.id)
        await dialog_manager.switch_to(PortfolioMenu.main)
    

async def input_days_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
):
    try:
        days = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное целое число дней")
        return
    ticker = dialog_manager.dialog_data.get('ticker_object')
    plot_file = await ticker.build_graph(period=f"{days}d")
    with open(plot_file, "rb") as image_from_buffer:
            result = await message.answer_photo(
            BufferedInputFile(
                image_from_buffer.read(),
                filename="image_from_buffer.png"
            ),
            caption='')
    await dialog_manager.switch_to(TickerMenu.ticker_info)
    
async def other_type_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    await message.answer("Неверный ввод!")