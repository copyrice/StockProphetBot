from typing import Any
from aiogram_dialog import ChatEvent, DialogManager
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button
from aiogram.types import BufferedInputFile, InputFile
# from pages.ticker_info import layout
from repo import TickerPortfolio, JsonSerializer
from aiogram.utils.markdown import hbold
from database.database import db_get_user_by_tg_id, db_get_portfolio_by_user_id, db_update_portfolio_dict, db_get_portfolio_by_user_tg_id, db_set_user_notifications, db_set_user_job_id

from states import MainMenu, TickerMenu, PortfolioMenu, FindMenu
from functions import create_ticker_info_startdata
import pandas as pd
from items import report_fields_list
import tempfile
from repo import generate_report
async def on_ticker_field_choose(
    callback: CallbackQuery,
    select: Any,
    dialog_manager: DialogManager,
    item_id: str,
):
    ticker = dialog_manager.dialog_data.get('ticker_object')
    if ticker is not None:
        if(item_id=='📊 График'):
          await dialog_manager.switch_to(TickerMenu.graphs)
                
        elif(item_id=="ℹ️ Описание"):
            await dialog_manager.switch_to(TickerMenu.description)

        elif(item_id=="⏺ Рекомендации"):
            await dialog_manager.switch_to(TickerMenu.recommendations)

        elif(item_id=='💬 Последние новости'):
            await dialog_manager.switch_to(TickerMenu.news)

        elif(item_id=='ℹ️ Индексы'):
            await dialog_manager.switch_to(TickerMenu.indices)

    else:
        pass

async def on_graph_field_choose(
    callback: CallbackQuery,
    select: Any,
    dialog_manager: DialogManager,
    item_id: str,
):
    ticker = dialog_manager.dialog_data.get('ticker_object')
    if(item_id=="График за все время"):
        # plot_file = await build_graph(ticker.yticker.history(period='max')['Close'],'D', dialog_manager.dialog_data.get('symbol'))
        plot_file = await ticker.build_graph()
        with open(plot_file, "rb") as image_from_buffer:
            result = await callback.message.answer_photo(
            BufferedInputFile(
                image_from_buffer.read(),
                filename="image_from_buffer.png"
            ),
            caption='')
        await dialog_manager.switch_to(TickerMenu.ticker_info)
    elif(item_id=="График за последние N дней"):
        await dialog_manager.switch_to(TickerMenu.waiting_for_days)
    


async def on_find(callback: CallbackQuery, button: Button,
                     dialog_manager: DialogManager):
    await dialog_manager.start(FindMenu.choosing_category)
    
    dialog_manager.dialog_data['portfolio'] = TickerPortfolio()
    

async def on_portfolio(callback: CallbackQuery, button: Button,
                     dialog_manager: DialogManager):
    user_portfolio = {}
    # db_session = dialog_manager.middleware_data.get('db_session')
    # db_portfolio = await db_get_portfolio_by_user_tg_id(callback.from_user.id, db_session)
    # serialized_portfolio = JsonSerializer.load_object_from_string(db_portfolio.serialized_portfolio)
    # user_portfolio['serialized_portfolio_dict'] = serialized_portfolio
    user_portfolio['tg_id'] = callback.from_user.id
    
    await dialog_manager.start(PortfolioMenu.main, user_portfolio)

async def on_category_chosen(callback: CallbackQuery, button: Button,
                     dialog_manager: DialogManager):
    dialog_manager.dialog_data['category'] = button.widget_id
    await dialog_manager.switch_to(FindMenu.entering_symbol)


async def on_translate_button_clicked(callback: CallbackQuery, button: Button,
                     dialog_manager: DialogManager):
    translator = dialog_manager.middleware_data.get('translator')
    translated_text = translator.translate(callback.message.text, dest='ru').text
    msg = await callback.message.answer(translated_text)
    dialog_manager.dialog_data['last_translation_message'] = msg


async def on_click(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
):
    pass


async def on_description_switch_to(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
):
    if(dialog_manager.dialog_data.get('last_translation_message')):
        msg = dialog_manager.dialog_data.get('last_translation_message')
        await msg.delete()
        del dialog_manager.dialog_data['last_translation_message']

async def on_add_to_portfolio_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    portfolio = dialog_manager.dialog_data.get('portfolio')
    recent_ticker = dialog_manager.dialog_data.get('recent_ticker')
    db_session = dialog_manager.middleware_data.get('db_session')
    user = await db_get_user_by_tg_id(callback.from_user.id, db_session)
    if(user):
        db_portfolio = await db_get_portfolio_by_user_id(user.id, db_session)
        portfolio_dict = JsonSerializer.load_object_from_string(db_portfolio.serialized_portfolio)
        for key in portfolio_dict:
            if(key==recent_ticker.ticker_type):
                if(recent_ticker.ticker_name in portfolio_dict[key]):
                    await callback.answer(f'{recent_ticker.ticker_name} уже в вашем портфолио!')
                    return 
        new_portfolio_dict = await TickerPortfolio.update_portfolio(portfolio_dict, recent_ticker)
        if(db_portfolio.serialized_portfolio!=new_portfolio_dict):
            await db_update_portfolio_dict(db_session, db_portfolio, new_portfolio_dict)
    
    await callback.answer(f"{recent_ticker.ticker_name} успешно добавлен в портфолио!")

async def on_back_to_main_menu_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    await dialog_manager.done()
    # portfolio = dialog_manager.dialog_data.get('portfolio')
    # if(portfolio):
    #     if(not await portfolio.is_empty()):
    #         await dialog_manager.done({'portfolio': portfolio,
    #                              'user_tg_id': callback.from_user.id})
    #     else:
    #         await dialog_manager.done()
    
async def on_ticker_choose(callback: CallbackQuery, widget: Any,
                            dialog_manager: DialogManager, item_id: str):
    select_ticers = dialog_manager.dialog_data.get('select_tickers')
    for pair in select_ticers:
        if(pair[2]==int(item_id)):
            selected_ticker = pair[1]
    start_data = await create_ticker_info_startdata(selected_ticker, callback.from_user.id)
    start_data['parent'] = 'portfolio'
    if(selected_ticker):
        await dialog_manager.start(TickerMenu.ticker_info, start_data)

async def on_remove_from_portfolio_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    portfolio = dialog_manager.dialog_data.get('portfolio')
    ticker = dialog_manager.start_data.get('ticker_object')
    db_session = dialog_manager.middleware_data.get('db_session')
    user = await db_get_user_by_tg_id(callback.from_user.id, db_session)
    if(user):
        db_portfolio = await db_get_portfolio_by_user_id(user.id, db_session)
        portfolio_dict = JsonSerializer.load_object_from_string(db_portfolio.serialized_portfolio)
        new_portfolio_dict = await TickerPortfolio.delete_from_portfolio(portfolio_dict, ticker)
        if(db_portfolio.serialized_portfolio!=new_portfolio_dict):
            await db_update_portfolio_dict(db_session, db_portfolio, new_portfolio_dict)
            await dialog_manager.start(PortfolioMenu.main, callback.from_user.id)

async def on_back_to_portfolio_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    await dialog_manager.done()


async def on_predictions_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    temporary_message = await callback.message.answer(f"Производятся прогноз, это может занять некоторое время...")
    dialog_manager.dialog_data['predictions_temp_message'] = temporary_message
    await dialog_manager.switch_to(TickerMenu.predictions)
    # await temporary_message.delete()


async def on_enable_notifications_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    # db_session = dialog_manager.middleware_data.get('db_session')
    # user = await db_get_user_by_tg_id(callback.from_user.id, db_session)
    # if(user):
    #     await db_set_user_notifications(db_session, user, True)
    await dialog_manager.switch_to(PortfolioMenu.waiting_for_time)

async def on_disable_notifications_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    db_session = dialog_manager.middleware_data.get('db_session')
    user = await db_get_user_by_tg_id(callback.from_user.id, db_session)
    if(user):
        await db_set_user_notifications(db_session, user, False)
        scheduler = dialog_manager.middleware_data.get('scheduler')
        scheduler.remove_job(user.job_id)
        await db_set_user_job_id(db_session, user, '')
    # scheduler.remo
    # scheduler.add_job(get_portfolio_and_send, "cron",  hour=hour, minute=minute, args=(db_session, message.from_user.id, message),
                #   timezone='Europe/Moscow')
async def on_report_click(callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager):
    await dialog_manager.switch_to(TickerMenu.report)

async def on_report_field_choose(callback: CallbackQuery,
    select: Any,
    dialog_manager: DialogManager,
    item_id: str):
    item_name = report_fields_list[int(item_id)][0]
    ticker = dialog_manager.dialog_data.get('ticker_object')
    if(item_name=="Отчет со всей информацией о тикере"):
        csv_file = await ticker.generate_info_report()
        await dialog_manager.switch_to(TickerMenu.ticker_info)
    elif(item_name=="Отчет об истории цен"):
        csv_file = await ticker.generate_history_report()
        await dialog_manager.switch_to(TickerMenu.ticker_info)

    
    with open(csv_file, "rb") as file_from_buffer:
        result = await callback.message.answer_document(
        BufferedInputFile(
            file_from_buffer.read(),
            filename=f"{ticker.ticker_name}_report.csv"
        ),
        caption='')