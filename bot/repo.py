from dataclasses import dataclass, field
from yfinance import Ticker
import matplotlib.pyplot as plt
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from MoexApiHandler import MoexApiHandler
from aiogram.utils.markdown import hbold, hlink, hpre, hunderline
import pandas as pd
import jsonpickle, json
import asyncio
import apimoex
from datetime import timedelta
import requests
from predictor import get_prediction_emoji, get_prediction_text

class JsonSerializer:

    @staticmethod
    def add_object_to_json(token: str, ticker, path: str = 'recent_user_tickers.json'):
        with open(path, "r") as f:
            dct = json.load(f)
        dct = json.loads(dct)
        dct[token] = ticker
        json_data = jsonpickle.encode(dct)
        with open(path, "w") as f:
            json.dump(json_data, f)

    @staticmethod
    def deserialize_object_from_json_file(token: str, path: str = 'recent_user_tickers.json'):
        with open(path, "r") as f:
            dct = jsonpickle.decode(f.read())
            dct = jsonpickle.decode(dct)
            ticker = dct[token]
        return ticker
    
    @staticmethod
    def load_object_from_string(string: str):
        return json.loads(string)
    
    @staticmethod
    def cast_to_string(obj: object) -> str:
        return json.dumps(obj)



@dataclass
class News:
    title: str
    publisher: str
    link: str
    timestamp_publish_time: int
    realated_tickers: list[str]

    def __post_init__(self):
        self.publish_date = datetime.fromtimestamp(self.timestamp_publish_time)

    def __str__(self) -> str:
        return self.title
    

    

@dataclass
class MainTicker:
    ticker_type: str
    ticker_name: str
    
    @abstractmethod
    async def build_graph(self):
        pass
    
    @abstractmethod
    async def get_historical_data(self):
        pass

    @abstractmethod
    async def generate_history_report(self):
        pass

    @abstractmethod
    async def generate_info_report(self):
        pass

@dataclass
class StockIndex(MainTicker):
    yticker: Ticker

    def __post_init__(self):
        self.currency_symbol = '$'

        self.current_bid = round(self.yticker.info.get('bid'), 2)
        self.day_low = round(self.yticker.info.get('dayLow'), 2)
        self.day_high = round(self.yticker.info.get('dayHigh'), 2)
        self.short_name = self.yticker.info.get('shortName')
        self.history_first_year = self.get_first_history_year()
        self.year_low = round(self.yticker.info.get('fiftyTwoWeekLow'), 2)
        self.year_high = round(self.yticker.info.get('fiftyTwoWeekHigh'), 2)
        self.previous_close = self.yticker.info.get('previousClose')
        self.volume = self.yticker.info.get('volume')
        # self.get_historical_data()

    async def build_graph(self, step='D', period='max'):
        data = self.yticker.history(period=period)['Close']
        return await build_graph(data, self.ticker_name)

    async def generate_history_report(self):
        data = self.get_historical_data()
        data['Date'] = data.index
        return await generate_report(data, self.ticker_name)

    async def generate_info_report(self):
        data = pd.DataFrame.from_dict(self.yticker.info, orient='index').T
        return await generate_report(data, self.ticker_name)


    def get_historical_data(self, period=None):
        df = self.yticker.history(period=period)
        df.index = pd.to_datetime(df.index)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    
    def get_first_history_year(self) -> int:
        df = self.yticker.history(period='max')
        return df.index[0].year

    @staticmethod
    async def get_ticker(symbol: str):
        yticker = Ticker(symbol)
        
        if(len(list(yticker.info.keys()))<=2):
            return None
        
        ticker = StockIndex(ticker_type='ir_index', ticker_name=symbol, yticker=yticker)
        return ticker
    
    async def get_last_news(self, amount: int=3):
        news = []
        for item in self.yticker.news:
            news.append(News(item['title'], item['publisher'],
                              item['link'], item['providerPublishTime'],
                              item['relatedTickers']))
        if(len(news)>amount):
            return news[0:amount]
        return news



@dataclass
class StockTicker(MainTicker):
    yticker: Ticker
    
    def __post_init__(self):
        self.currency_symbol = '$'
        
        self.recommendations = self.yticker.recommendations
        self.current_bid = round(self.yticker.info.get('bid'),  2)
        self.day_low = round(self.yticker.info.get(('dayLow')),  2)
        self.day_high = round(self.yticker.info.get('dayHigh'), 2)
        self.short_name = self.yticker.info.get('shortName')
        self.industry = self.yticker.info.get('industry')
        self.history_first_year = self.get_first_history_year()
        self.year_low = round(self.yticker.info.get('fiftyTwoWeekLow'), 2)
        self.year_high = round(self.yticker.info.get('fiftyTwoWeekHigh'), 2)
        self.previous_close = self.yticker.info.get('previousClose')
        self.volume = self.yticker.info.get('volume')
 
        if('longBusinessSummary' in list(self.yticker.info.keys())):
                self.description = self.yticker.info['longBusinessSummary']
        else:
            if('descripton' in list(self.yticker.info.keys())):
                self.description = self.yticker.info['description']
        
        # self.intoduction_message = f"{hbold(self.tikcer_name)}\n\nЦена:{self.current_bid}{self.currency_symbol}\nМинимальная и максимальная цена за день торогов:{self.day_low}/{self.day_high}\nОтрасль:" 

    @staticmethod
    async def get_ticker(symbol: str):
        yticker = Ticker(symbol)
        
        if(len(list(yticker.info.keys()))<=2):
            return None
        
        ticker = StockTicker(ticker_type='ir_stock', ticker_name=symbol, yticker=yticker)
        return ticker

    def get_historical_data(self, period=None):
        df = self.yticker.history(period=period)
        df.index = pd.to_datetime(df.index)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    
    async def get_last_news(self, amount: int=3):
        news = []
        for item in self.yticker.news:
            news.append(News(item['title'], item['publisher'],
                              item['link'], item['providerPublishTime'],
                              item['relatedTickers']))
        if(len(news)>amount):
            return news[0:amount]
        return news

    async def build_graph(self, step='D', period='max'):
        data = self.yticker.history(period=period)['Close']
        return await build_graph(data, self.ticker_name)
    
    def get_first_history_year(self) -> int:
        df = self.yticker.history(period='max')
        return df.index[0].year
    
    async def generate_history_report(self):
        data = self.get_historical_data()
        data['Date'] = data.index
        return await generate_report(data, self.ticker_name)

    async def generate_info_report(self):
        data = pd.DataFrame.from_dict(self.yticker.info, orient='index').T
        return await generate_report(data, self.ticker_name)
    
    
@dataclass
class CryptoTicker(MainTicker):
    yticker: Ticker

    def __post_init__(self):
        self.currency_symbol = '$'

        if('longBusinessSummary' in list(self.yticker.info.keys())):
                self.description = self.yticker.info['longBusinessSummary']
        else:
            if('description' in list(self.yticker.info.keys())):
                pass

        self.day_low = round(self.yticker.info.get('dayLow'), 3)
        self.day_high = round(self.yticker.info.get('dayHigh'), 3)
        self.short_name = self.yticker.info.get('name')
        self.current_bid = round(self.yticker.info.get('regularMarketPreviousClose'), 3)
        self.description = self.yticker.info.get('description')
        self.previous_close = self.yticker.info.get('previousClose')
        self.year_low = round(self.yticker.info.get('fiftyTwoWeekLow'), 3)
        self.year_high = round(self.yticker.info.get('fiftyTwoWeekHigh'), 3)
        self.history_first_year = self.get_first_history_year()
        self.volume = self.yticker.info.get('volume')

    async def build_graph(self, step='D', period='max'):
        data = self.yticker.history(period=period)['Close']
        return await build_graph(data, self.ticker_name)
    
    async def generate_history_report(self):
        data = self.get_historical_data()
        data['Date'] = data.index
        return await generate_report(data, self.ticker_name)

    async def generate_info_report(self):
        data = pd.DataFrame.from_dict(self.yticker.info, orient='index').T
        return await generate_report(data, self.ticker_name)

    @staticmethod
    async def get_ticker(symbol: str):
        yticker = Ticker(f"{symbol}-USD")
        
        if(len(list(yticker.info.keys()))<=2):
            return None
        
        ticker = CryptoTicker(ticker_type='crypto', ticker_name=symbol, yticker=yticker)
        return ticker

    def get_historical_data(self, period=None):
        df = self.yticker.history(period=period)
        df.index = pd.to_datetime(df.index)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    
    def get_first_history_year(self) -> int:
        df = self.yticker.history(period='max')
        return df.index[0].year

# class Security:
#     def __init__(self, **kwargs) -> None:
#         for key, value in kwargs.items():
#             setattr(self, key.lower(), value)


@dataclass
class RuStockIndex(MainTicker):

    security: dict
    
    def __post_init__(self):
        self.currency_symbol = '₽'
        self.current_bid = self.security.get('CURRENTVALUE')
        self.day_low = self.security.get('LOW')
        self.day_high = self.security.get('HiGH')
        self.short_name = self.security.get('SHORTNAME')
        self.history_first_year = self.get_first_history_year()
        self.update_time = self.security.get('UPDATETIME')
        self.secname = self.security.get('SECNAME')
        self.capitalization = self.security.get('CAPITALIZATION')
        self.previous_close = self.security.get('LASTVALUE')
    
    async def build_graph(self, period=None):
        data = await self.get_historical_data_async()
        if(period):
            user_input_days = int(period[:-1])
            end_date = datetime.today()
            start_date = (end_date - timedelta(days=user_input_days))
            data = data[(data.index >= start_date) & (data.index <= end_date)]
        return await build_graph(data['Close'], self.ticker_name)


    async def get_historical_data_async(self):
        data = await MoexApiHandler.get_index_history(self.ticker_name)
        df = pd.DataFrame(data)
        df.columns = df.columns.str.title()
        df.set_index('Begin', inplace=True)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    
    def get_historical_data(self) -> pd.DataFrame:
        with requests.Session() as session:
            df = pd.DataFrame(apimoex.get_market_candles(session=session, market='index', security=self.ticker_name))
        df.columns = df.columns.str.title()
        df = df.set_index('Begin')
        df.index = pd.to_datetime(df.index)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    
    def get_first_history_year(self) -> int:
        df = self.get_historical_data()
        return df.index[0].year

    async def get_board_title(self):
        boardid = self.security.get('boardid')
        board_title = await MoexApiHandler.get_board_name(boardid)
        return f"{boardid} - {board_title}"
    
    @staticmethod
    async def get_ticker(symbol: str):
        data = await MoexApiHandler.get_index_data(symbol)
        if(data['securities'] and data['marketdata']):
            def_dict = {}
            def_dict.update(data['securities'][0])
            def_dict.update(data['marketdata'][0])
            print(def_dict)
            ticker = RuStockIndex('ru_index', symbol, security=def_dict)
            return ticker
        return None
    
    async def generate_history_report(self):
        data = self.get_historical_data()
        data['Begin'] = data.index
        return await generate_report(data, self.ticker_name)

    async def generate_info_report(self):
        data = pd.DataFrame.from_dict(self.security, orient='index').T
        return await generate_report(data, self.ticker_name)

@dataclass
class RuStockTicker(MainTicker):
    security: dict
    
    def __post_init__(self):
        self.currency_symbol = '₽'
        self.current_bid = self.security.get('OFFER')
        if(not self.current_bid):
            self.current_bid = self.security.get('MARKETPRICETODAY')
        self.day_low = self.security.get('LOW')
        self.day_high = self.security.get('HiGH')
        self.short_name = self.security.get('SHORTNAME')
        self.history_first_year = self.get_first_history_year()
        self.capitalization = self.security.get('ISSUECAPITALIZATION')
        self.update_time = self.security.get('UPDATETIME')
        self.secname = self.security.get('SECNAME')
        self.spread = self.security.get('SPREAD')
        self.previous_close = self.security.get('PREVLEGALCLOSEPRICE')

    async def build_graph(self, period = None):
        data = await self.get_historical_data_async()
        if(period):
            user_input_days = int(period[:-1])
            end_date = datetime.today()
            start_date = (end_date - timedelta(days=user_input_days))
            data = data[(data.index >= start_date) & (data.index <= end_date)]
        return await build_graph(data['Close'], self.ticker_name)


    async def get_historical_data_async(self):
        data = await MoexApiHandler.get_share_history(self.ticker_name)
        df = pd.DataFrame(data)
        df.columns = df.columns.str.title()
        df.set_index('Begin', inplace=True)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    
    def get_historical_data(self) -> pd.DataFrame:
        with requests.Session() as session:
            df = pd.DataFrame(apimoex.get_board_candles(session=session, security=self.ticker_name))
        df.columns = df.columns.str.title()
        df = df.set_index('Begin')
        df.index = pd.to_datetime(df.index)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    
    def get_first_history_year(self) -> int:
        df = self.get_historical_data()
        return df.index[0].year
    

    async def get_indexes_include_ticker(self):
        data = await MoexApiHandler.get_indeces_including_security(self.ticker_name)
        indices = []
        for elem in data['indices']:
            indices.append({'secid': elem['SECID'],
                            'shortname': elem['SHORTNAME'],
                            'value': elem['CURRENTVALUE']})
        return indices
    
    async def get_board_title(self):
        boardid = self.security.get('boardid')
        board_title = await MoexApiHandler.get_board_name(boardid)
        return f"{boardid} - {board_title}"
    
    @staticmethod
    async def get_ticker(symbol: str):
        data = await MoexApiHandler.get_security_data(symbol)
        if(data['securities'] and data['marketdata']):
            def_dict = {}
            def_dict.update(data['securities'][0])
            def_dict.update(data['marketdata'][0])
            ticker = RuStockTicker('ru_stock', symbol, security=def_dict)
            return ticker
        return None
    
    async def generate_history_report(self):
        data = self.get_historical_data()
        data['Begin'] = data.index
        return await generate_report(data, self.ticker_name)

    async def generate_info_report(self):
        data = pd.DataFrame.from_dict(self.security, orient='index').T
        return await generate_report(data, self.ticker_name)

    # @staticmethod
    # async def get_ticker(symbol: str):
    #     data = await MoexApiHandler.get_all_shares()
    #     # print(data)
    #     for item in data:
    #         if(item['SECID']==symbol):
    #             print(item)
    #             return RuStockTicker('ru_stock', symbol, security=Security(**item))
    #     return None




@dataclass
class TickerPortfolio:
    ir_stock: list[StockTicker] = field(default_factory=list)
    crypto: list[CryptoTicker] = field(default_factory=list)
    ru_stock: list[RuStockTicker] = field(default_factory=list)
    ir_index: list[StockIndex] = field(default_factory=list)
    ru_index: list[RuStockIndex] = field(default_factory=list)

    async def add(self, ticker):
        if(isinstance(ticker, StockTicker)):
            self.ir_stock.append(ticker.ticker_name)
        elif(isinstance(ticker, CryptoTicker)):
            self.crypto.append(ticker.ticker_name)
        elif(isinstance(ticker, RuStockTicker)):
            self.ru_stock.append(ticker.ticker_name)

        elif(isinstance(ticker, StockIndex)):
            self.ir_index.append(ticker.ticker_name)
        elif(isinstance(ticker, RuStockIndex)):
            self.ru_index.append(ticker.ticker_name)
        
    async def remove(self, ticker):
        if(isinstance(ticker, StockTicker)):
            self.ir_stock.remove(ticker.ticker_name)
        elif(isinstance(ticker, CryptoTicker)):
            self.crypto.remove(ticker.ticker_name)
        elif(isinstance(ticker, RuStockTicker)):
            self.ru_stock.remove(ticker.ticker_name)

        elif(isinstance(ticker, StockIndex)):
            self.ir_index.remove(ticker.ticker_name)
        elif(isinstance(ticker, RuStockIndex)):
            self.ru_index.remove(ticker.ticker_name)

    async def is_empty(self):
        if(self.ir_stock or self.crypto or self. ru_stock or self.ir_index or self.ru_index):
            return False
        return True

    async def serialize_to_string(self):
        portfolio_dict = {
            'ir_stock': self.ir_stock,
            'crypto': self.crypto,
            'ru_stock': self.ru_stock,
            'ir_index': self.ir_index,
            'ru_index': self.ru_index
        }
        return JsonSerializer.cast_to_string(portfolio_dict)
    
    @staticmethod
    async def desirialize_from_dict(db_dict: dict):
        ir_stock_tickers = await asyncio.gather(*map(lambda x: StockTicker.get_ticker(x), db_dict['ir_stock']))
        crypto_tickers = await asyncio.gather(*map(lambda x: CryptoTicker.get_ticker(x), db_dict['crypto']))
        ru_stock_tickers = await asyncio.gather(*map(lambda x: RuStockTicker.get_ticker(x), db_dict['ru_stock']))
        ir_index_tickers = await asyncio.gather(*map(lambda x: StockIndex.get_ticker(x), db_dict['ir_index']))
        ru_index_tickers = await asyncio.gather(*map(lambda x: RuStockIndex.get_ticker(x), db_dict['ru_index']))

        return TickerPortfolio(
            ir_stock_tickers,
            crypto_tickers,
            ru_stock_tickers,
            ir_index_tickers,
            ru_index_tickers,
        )    
    @staticmethod
    async def update_portfolio(portfolio_dict, ticker):
        portfolio_dict[ticker.ticker_type].append(ticker.ticker_name)
        for key, value in portfolio_dict.items():
            portfolio_dict[key] = list(set(value))
        
        return portfolio_dict
    
    @staticmethod
    async def delete_from_portfolio(portfolio_dict, ticker):
        if(ticker.ticker_name in portfolio_dict[ticker.ticker_type]):
            portfolio_dict[ticker.ticker_type].remove(ticker.ticker_name)
        
        return portfolio_dict

    @staticmethod
    async def check_if_ticker_already_in(ticker_name, ticker_type, db_dict):
        if(ticker_name in [ticker.ticker_name for ticker in db_dict[ticker_type]]):
            return True
        return False
    
    @staticmethod
    async def get_emoji_for_ticker(ticker):
        if(ticker.ticker_type=='ir_stock' or ticker.ticker_type=='ir_index'):
            return '🌐'
        elif(ticker.ticker_type=='crypto'):
            return '🔸'
        elif(ticker.ticker_type=='ru_stock' or ticker.ticker_type=='ru_index'):
            return '🇷🇺'
        else:
            return ''
        
    async def get_full_tickers_list(self):
        full_list = []
        full_list += self.ir_stock
        full_list += self.ir_index
        full_list += self.ru_stock
        full_list += self.ru_index
        full_list += self.crypto
        return full_list
        
    async def get_report_message(self):
        message = f"{datetime.now().strftime('%d.%m.%Y %H:%M')}\nОтчет по портфолио:\n"
        all_tickers = await self.get_full_tickers_list()
        for ticker in all_tickers:
            emoji = await TickerPortfolio.get_emoji_for_ticker(ticker)
            percent = round((ticker.current_bid - ticker.previous_close) / ticker.previous_close * 100, 2)
            message+=f"\n{emoji}{hbold(ticker.ticker_name)}: P: {ticker.previous_close}{ticker.currency_symbol}, C: {ticker.current_bid}{ticker.currency_symbol} -> {get_prediction_text(ticker.previous_close, ticker.current_bid)} {percent}% {get_prediction_emoji(ticker.previous_close, ticker.current_bid)}\n"
        
        return message
    
async def build_graph(data, ticker_name):
        plt.figure(figsize=(12, 10))
        plt.plot(data.index, data.values, label='Цена', color='blue', markersize=3, markerfacecolor='lightblue')
        plt.title(f'Цена закрытия {ticker_name}', fontsize=16, fontweight='bold')
        plt.xlabel('Дата')
        plt.ylabel('Цена')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
            plt.savefig(tmpfile.name)
            return tmpfile.name
        

async def generate_report(data, ticker_name):
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmpfile:
        csv = data.to_csv(tmpfile.name, encoding='utf-8')
        return tmpfile.name