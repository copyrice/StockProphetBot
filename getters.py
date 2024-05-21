from aiogram_dialog import Dialog, Window, setup_dialogs, DialogManager
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Checkbox, Button, Row, Cancel, Start
from functions import get_necessary_info_from_ticker, find_ticker_fields, create_news_message, get_ending
from predictor import get_prediction_emoji, get_prediction_text
from database.database import db_get_user_by_tg_id, db_get_portfolio_by_user_tg_id
from repo import JsonSerializer, TickerPortfolio
from config import SERVER_URL
from aiogram.utils.markdown import hbold, hlink, hpre, hunderline
from repo import RuStockTicker
from items import portfolio_menu_size

def get_text_on_button_id(button_id):
    if(button_id=='ir_stock'):
        return 'международной акции'
    elif(button_id=='crypto'):
        return 'криптовалюты'
    elif(button_id=='ir_index'):
        return 'международного индекса'
    elif(button_id=='ru_stock'):
        return 'российской акции'
    return ''

async def get_ticker_info(dialog_manager: DialogManager, **kwargs):

    dialog_manager.dialog_data.update(dialog_manager.start_data)

    symbol = dialog_manager.dialog_data.get("symbol")
    ticker = dialog_manager.dialog_data.get('ticker_object')
    translator = dialog_manager.middleware_data.get('translator')

    ticker_data = await get_necessary_info_from_ticker(ticker, translator)

    

    ticker_data['parent_portfolio'] = 1 if dialog_manager.dialog_data.get('parent')=='portfolio' else 0
    ticker_data['parent_find'] = 1 if dialog_manager.dialog_data.get('parent')=='find' else 0

    
    ticker_data['user_symbol'] = symbol
    ticker_data['items_fields'] = find_ticker_fields(ticker.ticker_type)

    db_session = dialog_manager.middleware_data.get('db_session')
    tg_id = dialog_manager.dialog_data.get('user_tg_id')
    user = await db_get_user_by_tg_id(tg_id, db_session)
    
    if(user):
        ticker_data['user_link'] = f"{SERVER_URL}/ticker_info/{user.token}"
    else:
        ticker_data['user_link'] = f"{SERVER_URL}"

    JsonSerializer.add_object_to_json(user.token, ticker)
    # ticker_data['introduction_message'] = intoduction_message
    return ticker_data
    
async def get_category_info(dialog_manager: DialogManager, **kwargs):
    category_id = dialog_manager.dialog_data.get('category')
    data = {}
    data['message'] = get_text_on_button_id(category_id)
    return data
    
async def graphs_getter(dialog_manager: DialogManager, **kwargs):
    data = {}
    ticker = dialog_manager.dialog_data.get('ticker_object')
    data['symbol'] = ticker.ticker_name
    
    return data

async def description_getter(dialog_manager: DialogManager, **kwargs):
    data = {}
    ticker = dialog_manager.dialog_data.get('ticker_object')
    data['descriptopn'] = ticker.description

    return data

async def recommendations_getter(dialog_manager: DialogManager, **kwargs):
    data = {}
    ticker = dialog_manager.dialog_data.get('ticker_object')
    recommendations_message = f"Рекомендации - список рекомендаций аналитиков по данному тикеру\n\n {hbold('period')} указывает на временной интервал, за который анализируются рекомендации\n\n\n"
    for index, row in ticker.recommendations.iterrows():
        recommendations_message += f"•Период: {row['period']}\n"
        recommendations_message += f"\t\t\tStrongBuy: {row['strongBuy']}\n"
        recommendations_message += f"\t\t\tBuy: {row['buy']}\n"
        recommendations_message += f"\t\t\tHold: {row['hold']}\n"
        recommendations_message += f"\t\t\tSell: {row['sell']}\n"
        recommendations_message += f"\t\t\tStrongSell: {row['strongSell']}\n\n"
    data['recommendations_message'] = recommendations_message
    return data

async def indices_getter(dialog_manager: DialogManager, **kwargs):
    data = {}
    ticker = dialog_manager.dialog_data.get('ticker_object')
    indices_message = f"{hlink('Индексы','https://ru.wikipedia.org/wiki/%D0%A4%D0%BE%D0%BD%D0%B4%D0%BE%D0%B2%D1%8B%D0%B9_%D0%B8%D0%BD%D0%B4%D0%B5%D0%BA%D1%81')}, в которые входит {ticker.ticker_name}\n\n"
    indices = await ticker.get_indexes_include_ticker()
    for index in indices:
        indices_message += f"Индекс {hbold(index['secid'])}\n"
        indices_message += f"\t\t\t{hunderline(index['shortname'])}\n"
        indices_message += f"\t\t\t {index['value']}{ticker.currency_symbol}\n\n"
    data['indices_message'] = indices_message
    return data

async def news_getter(dialog_manager: DialogManager, **kwargs):
    data = {}

    ticker = dialog_manager.dialog_data.get('ticker_object')
    translator = dialog_manager.middleware_data.get('translator')
    news_message = f"Последние новости, связанные с выбранным тикером {hbold(ticker.ticker_name)}\n\n"
    last_news = await ticker.get_last_news()
    for news in last_news:
        news_message += create_news_message(news, translator)

    data['news_message'] = news_message
    return data

async def portfolio_getter(dialog_manager: DialogManager, **kwargs):
    data = {}

    portfolio_message = f"💼В меню портфолио вы можете отслеживать активы"
    db_session = dialog_manager.middleware_data.get('db_session')
    # portfolio_dct = dialog_manager.start_data.get('serialized_portfolio_dict')
    user_tg_id = dialog_manager.start_data.get('tg_id')
    db_portfolio = await db_get_portfolio_by_user_tg_id(user_tg_id, db_session)
    portfolio_dct = JsonSerializer.load_object_from_string(db_portfolio.serialized_portfolio)
    tickerPortfolio = await TickerPortfolio.desirialize_from_dict(portfolio_dct)
    dialog_manager.dialog_data['tickerPortfolio'] = tickerPortfolio
    tickers = await tickerPortfolio.get_full_tickers_list()
    tickers = [(f"{await TickerPortfolio.get_emoji_for_ticker(ticker)}{ticker.ticker_name}", ticker, tickers.index(ticker)) for ticker in tickers]
    dialog_manager.dialog_data['select_tickers'] = tickers


    user = await db_get_user_by_tg_id(user_tg_id, db_session)

    if(tickers):
        portfolio_message+=f"\nНа данный момент в вашем портфолио {hbold(len(tickers))} элемент{await get_ending(len(tickers))}"
        # portfolio_message+=f"\nДля просмотра всех тикеров используйте кнопки управления страницами\nОдна страница вмещает:\n {portfolio_menu_size['height']} элементов по вертикали, {portfolio_menu_size['width']} по горизонатил"
    else:
        portfolio_message+=f"\nДля добавления тикеров в портфолио воспользуйтесь пунктом меню 🔎Поиск"

    if(user.notifications_enabled):
        data['notifications_enabled'] = 1
    else:
        portfolio_message+=f"\nВ боте есть возможность получения уведомлений об изменении цен тикеров из портфолио.\nДля этого воспользуйтесь кнопкой включения уведомлений."
        data['notifications_disabled'] = 1

    data['portfolio_message'] = portfolio_message
    data['tickers'] = tickers
    return data

async def predictions_getter(dialog_manager: DialogManager, **kwargs):
    data = {}
    

    predictor = dialog_manager.middleware_data.get('predictor')
    ticker = dialog_manager.dialog_data.get('ticker_object')
    predictions_message = f"Прогнозы для {hbold(ticker.ticker_name)}\n"

    predictions_message+="Бот использует технологии машинного обучения при получении предполагаемой цены закрытия торогов следующего дня.\n\n"
    for basemodel in predictor.nnmodels.models_list:
        history = ticker.get_historical_data()
        history['Date'] = history.index
        last= history['Date'].tail(basemodel.base_train_days_amount).index
        train_data = history.loc[last]
        target = 'Close'
        features = history.columns
        features.drop(target)
        prediction_close = predictor.predict_(train_data, features, target, predictor.nnmodels.random_state, basemodel.model)

        percent = round((prediction_close - ticker.previous_close) / ticker.previous_close * 100, 2)

        predictions_message+=f"{basemodel.ru_name} - {get_prediction_text(ticker.previous_close, prediction_close)} {percent}% {get_prediction_emoji(ticker.previous_close, prediction_close)}\n\n"

    data['predictions_message'] = predictions_message

    temp_message = dialog_manager.dialog_data.get('predictions_temp_message')
    if(temp_message):
        await temp_message.delete()

    return data

async def report_getter(dialog_manager: DialogManager, **kwargs):
    data = {}

    report_message = f"Бот отправляет отчет в виде файла формаата .csv\nОткрыть отчет можно с помощью {hbold('MS Excel')} или в текстовом редакторе"

    data['report_message'] = report_message
    return data