from repo import StockTicker, CryptoTicker, RuStockTicker, StockIndex, RuStockIndex
from dash import html, dcc
from googletrans import Translator
from aiogram.utils.markdown import hbold, hlink, hpre, hunderline
from repo import News, JsonSerializer, TickerPortfolio
import emoji
import re
import datetime
from database.database import db_get_portfolio_by_user_tg_id
ticker_types = [
    'ir_stock', 'crypto', 'ru_stock', 'ir_index', 'ru_index'
]


async def find_ticker(ticker_type: str, symbol:str):
    if(ticker_type=='ir_stock'):
        # if(symbol.startswith('^')):

        return await StockTicker.get_ticker(symbol)
    
    if(ticker_type=='crypto'):
        
        return await CryptoTicker.get_ticker(symbol)
    
    if(ticker_type=='ru_stock'):
        return await RuStockTicker.get_ticker(symbol)
    
    if(ticker_type=='ir_index'):
        pass
        
        return await StockIndex.get_ticker(symbol)
    
    if(ticker_type=='ru_index'):
        pass
        
        return await RuStockIndex.get_ticker(symbol)
        
    return None

async def get_necessary_info_from_ticker(ticker, translator:Translator = None):
    data = {}
    introduction_message = f"{hbold(ticker.ticker_name)} - {hunderline(ticker.short_name)}\n\nЦена: {ticker.current_bid}{ticker.currency_symbol}"
    introduction_message += f"\nПредыдущая цена закрытия: {ticker.previous_close}"
    introduction_message += f"\nМин. и макс. цена за день торогов: {ticker.day_low}{ticker.currency_symbol} / {ticker.day_high}{ticker.currency_symbol}\nМин. и макс. цена за год: {ticker.year_low}{ticker.currency_symbol} / {ticker.year_high}{ticker.currency_symbol}"

    if(ticker.ticker_type=='ir_stock'):
        data['description'] = ticker.description
        industry_ru = translator.translate(ticker.industry, dest='ru').text
        introduction_message += f"\nОтрасль: {industry_ru}"
        introduction_message += f"\nОбъем: {ticker.volume}"
    # introduction_message = f"{hbold(ticker.ticker_name)}\n\nЦена: {ticker.current_bid}{ticker.currency_symbol}\nМин. и макс. цена за день торогов: {ticker.day_low}/{ticker.day_high}{ticker.currency_symbol}"

    if(ticker.ticker_type=='crypto'):
        data['description'] = ticker.description
        introduction_message += f"\nОбъем: {ticker.volume}"

    if(ticker.ticker_type=='ru_stock'):
        board_title = await ticker.get_board_title()
        introduction_message += f"\nРежим торогов: {board_title}"
        introduction_message += f"\nКапитализация: {ticker.capitalization}{ticker.currency_symbol}"
        introduction_message += f"\nСпред: {ticker.spread}"
        introduction_message += f"\nВремя обновления: {ticker.update_time}"

    if(ticker.ticker_type=='ir_index'):
        board_title = await ticker.get_board_title()
        introduction_message += f"\nРежим торогов: {board_title}"
        introduction_message += f"\nОбъем: {ticker.volume}"

    if(ticker.ticker_type=='ru_index'):
        introduction_message += f"\nКапитализация: {ticker.capitalization}{ticker.currency_symbol}"
        introduction_message += f"\nВремя обновления: {ticker.update_time}"
        
    data['introduction_message'] = introduction_message
    return data

def create_news_message(news: News, translator: Translator) -> str:
        
        ru_title = translator.translate(news.title, dest='ru').text
        """Создает сообщение с новостью для пользователя.

        Использует эмодзи и HTML-теги для форматирования текста.
        """

        message = f"""
        💬 {news.title}
        {emoji.emojize(':loudspeaker:')}{news.publisher}
        🔗 {news.link}
        🗓 {news.publish_date:%d.%m.%Y %H:%M}
        Тикеры, связанные с новостью:
        {news.realated_tickers}
        """

        # for ticker in news.realated_tickers:
            # message += f"{hbold(ticker)}"

        message += '\n'
        return message

def find_ticker_fields(ticker_type):
    tickers_fields = {
        'ir_stock': [
            '📊 График',
            'ℹ️ Описание',
            '⏺ Рекомендации',
            '💬 Последние новости'
        ],

        'ru_stock':
        [
            '📊 График',
            'ℹ️ Индексы'
        ],

        'ir_index':
        [
            '📊 График',
            '💬 Последние новости'
        ],
        'crypto':
        [
            '📊 График',
            'ℹ️ Описание'
        ],
        'ru_index':
        [
            '📊 График'        
        ],
        }
    
    return tickers_fields.get(ticker_type)

def get_field_emoji(field: str):
    pass

def create_ticker_info_page_layout():
    layout = html.Div([
    html.H1("Stock Data Analysis", style={'textAlign': 'center', 'color': 'black'}),
    
    # Input field for the stock symbol with debounce
    # dcc.Input(id='stock-symbol', type='text', value='AMZN', debounce=True, style={'textAlign': 'center'}),
    
    # Button to trigger data retrieval
    # html.Button('Fetch Data', id='fetch-button', style={'textAlign': 'center'}),

    # Historical candlestick chart
    dcc.Graph(id='candlestick-chart'),
    
    # Table to display results
    html.Table(id='results-table', children=[
        html.Tr([html.Th("Metric", style={'textAlign': 'center', 'color': 'black'}), html.Th("Value", style={'textAlign': 'center', 'color': 'black'})], style={'backgroundColor': 'rgb(35, 35, 35)'}),
    ], style={'textAlign': 'center', 'color': 'black'})
])

    return layout

async def get_ending(num: int) -> str:
    if(num==1):
        return ''
    return 'ов'


async def create_ticker_info_startdata(ticker, user_tg_id):
    dialog_data = {}
    dialog_data['recent_tickers'] = {
        'ir_stock': None,
        'ir_index': None,
        'crypto': None,
        'ru_stock': None,
        'ru_index': None
    }
    dialog_data['symbol'] = ticker.ticker_name
    dialog_data['ticker_object'] = ticker
    dialog_data['recent_tickers']['category'] = ticker
    dialog_data['recent_ticker'] = ticker
    dialog_data['user_tg_id'] = user_tg_id
    dialog_data['parent'] = 'find'
    
    return dialog_data


def validate_time(time_str: str) -> bool:

    # Проверить, соответствует ли введенное время формату HH:MM
    pattern = r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
    if not re.match(pattern, time_str):
        return False

    # Проверить, существует ли указанное время
    try:
        datetime.datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return False

    return True



async def send_message(message, text: str):
  await message.answer(text)


async def get_portfolio_and_send(db_session, user_tg_id, message):
    db_portfolio = await db_get_portfolio_by_user_tg_id(user_tg_id, db_session)
    portfolio_dct = JsonSerializer.load_object_from_string(db_portfolio.serialized_portfolio)
    tickerPortfolio = await TickerPortfolio.desirialize_from_dict(portfolio_dct)
    text = await tickerPortfolio.get_report_message()
    await send_message(message, text)