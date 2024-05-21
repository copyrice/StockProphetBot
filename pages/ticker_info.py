import dash
from dash import html, dcc, callback, Input, Output, State
from datetime import datetime, timedelta
import plotly.graph_objs as go
import pandas as pd
from repo import JsonSerializer, StockTicker
from yfinance import Ticker

dash.register_page(__name__, path_template="ticker_info/<token>")

# layout = html.Div([html.H1("Stock Data Analysis", style={'textAlign': 'center', 'color': 'black'})])

def layout(token: str = None, **kwargs):
    
    if token is None:
        return html.Div([html.H1("Invalid token", style={'textAlign': 'center', 'color': 'red'})])
    ticker = JsonSerializer.deserialize_object_from_json_file(token)

    dcc.Dropdown()
    # print(ticker.ticker_name)
    layout = html.Div([
    # html.P(f'Token: {token}', style={'display': 'inline', 'marginRight': '10px'}),
    dcc.Location(id='url', refresh=True),
    html.H1(f"Анализ {ticker.ticker_name}", style={'textAlign': 'center', 'color': 'black'}),

    dcc.Dropdown(
    id='date-range-dropdown',
    options=[],
    value=None,
    style={
            'width': '300px',
            'background-color': '#f5f5f5',
            'border-color': '#cccccc',
            'font-size': '14px'
        }
    ),
     html.Div([
        html.Div(id='date-container'),
    ],
    style={
        'font-size': '14px',
        'text-align': 'center',
        'margin-top': '10px',
        'background-color': '#ffffff',
        'border-color': '#cccccc',
        'padding': '10px',
        'position': 'relative',
        'top': '0px'
    }),
    # dcc.Input(id='period', type='text', value='1y', debounce=True, style={'textAlign': 'center'}),

    dcc.Graph(id='candlestick-chart'),
    
    # Table to display results
    html.Table(id='results-table', children=[
        html.Tr([html.Th("Metric", style={'textAlign': 'center', 'color': 'black'}), html.Th("Value", style={'textAlign': 'center', 'color': 'black'})], style={'backgroundColor': 'rgb(35, 35, 35)'}),
    ], style={'textAlign': 'center', 'color': 'black'})
])
    
    return layout


@callback(
    [Output('results-table', 'children'), Output('candlestick-chart', 'figure'),
     Output('date-range-dropdown', 'options'),
     Output('date-container', 'children')],
    Input('url', 'pathname'),
    Input('date-range-dropdown', 'value')
)
def update_table(pathname, value):
    token = pathname.split('/')[-1]
    user_input_year = value
    # try:
    if(token):    
                ticker = JsonSerializer.deserialize_object_from_json_file(token)
                if(ticker):

                    if(user_input_year==None):
                        user_input_year = datetime.today().year - 1


                    start_date = datetime.strptime(f"{user_input_year}-01-01", '%Y-%m-%d')
                    end_date = (start_date + timedelta(days=365))

                    whole_historical_data = ticker.get_historical_data()

                    dates_pairs = get_start_end_pairs(ticker.history_first_year)
                    options = [f"{pair['start'].strftime('%Y')}" for pair in dates_pairs]
                    
                    
                    historical_data = whole_historical_data[(whole_historical_data.index >= start_date) & (whole_historical_data.index <= end_date)]
                    current_date = historical_data.index[-1]
                    one_week_ago = current_date - timedelta(weeks=1)
                    one_month_ago = current_date - timedelta(weeks=4)
                    three_months_ago = current_date - timedelta(weeks=12)
                    six_months_ago = current_date - timedelta(weeks=24)
                    one_year_ago = current_date - timedelta(weeks=52)

                    returns = {
                "1 Week": (get_close_price(historical_data, current_date) / get_close_price(historical_data, one_week_ago) - 1) * 100,
                "1 Month": (get_close_price(historical_data, current_date) / get_close_price(historical_data, one_month_ago) - 1) * 100,
                "3 Months": (get_close_price(historical_data, current_date) / get_close_price(historical_data, three_months_ago) - 1) * 100,
                "6 Months": (get_close_price(historical_data, current_date) / get_close_price(historical_data, six_months_ago) - 1) * 100,
                "1 Year": (get_close_price(historical_data, current_date) / get_close_price(historical_data, one_year_ago) - 1) * 100,
            }

                    # Convert high and low columns to numeric and find max and min
                    high_52_weeks = pd.to_numeric(historical_data["High"]).max()
                    low_52_weeks = pd.to_numeric(historical_data["Low"]).min()

                    # Calculate how far the current price is from 52-week high and low
                    # current_price = historical_data["Close"][current_date]


                    # Create a table of results
                    table_rows = [
                        html.Tr([html.Td("1 Неделя", style={'color': 'black'}), 
                                html.Td("1 Месяц", style={'color': 'black'}),
                                html.Td("3 Месяца", style={'color': 'black'}),
                                html.Td("6 Месяцев", style={'color': 'black'}),
                                html.Td("1 Год", style={'color': 'black'}),
                                html.Td("Макс. за год", style={'color': 'black'}),
                                html.Td("Мин. за год", style={'color': 'black'})
                                ]),
                            html.Tr([html.Td(f"{returns['1 Week']:.2f}%", style={'color': 'white', 'backgroundColor': 'green' if returns['1 Week'] > 25 else ('orange' if returns['1 Week'] > 0 else 'red')}),
                                html.Td(f"{returns['1 Month']:.2f}%", style={'color': 'white', 'backgroundColor': 'green' if returns['1 Month'] > 25 else ('orange' if returns['1 Month'] > 0 else 'red')}),
                                html.Td(f"{returns['3 Months']:.2f}%", style={'color': 'white', 'backgroundColor': 'green' if returns['3 Months'] > 25 else ('orange' if returns['3 Months'] > 0 else 'red')}),
                                html.Td(f"{returns['6 Months']:.2f}%", style={'color': 'white', 'backgroundColor': 'green' if returns['6 Months'] > 25 else ('orange' if returns['6 Months'] > 0 else 'red')}),
                                html.Td(f"{returns['1 Year']:.2f}%", style={'color': 'white', 'backgroundColor': 'green' if returns['1 Year'] > 25 else ('orange' if returns['1 Year'] > 0 else 'red')}),
                                html.Td(f"{high_52_weeks:.3f}{ticker.currency_symbol}", style={'color': 'black', 'backgroundColor': 'LightSteelBlue'}),
                                html.Td(f"{low_52_weeks:.3f}{ticker.currency_symbol}", style={'color': 'black', 'backgroundColor': 'RosyBrown'})
                            ])

                        ]
                    
                    
                    html.Div(id='output-container')
                    candlestick_chart = go.Figure(data=[go.Candlestick(x=historical_data.index,
                                                                    open=historical_data['Open'],
                                                                    high=historical_data['High'],
                                                                    low=historical_data['Low'],
                                                                    close=historical_data['Close'])])
                    candlestick_chart.update_layout(title=f'График свечей {ticker.ticker_name}',
                                                    xaxis_title='Дата',
                                                    yaxis_title='Цена',
                                                    xaxis_rangeslider_visible=True)
                    date_container_text = f"{start_date.year} - {end_date.year}" if start_date.year != end_date.year else f"{start_date.year}"
                    return table_rows, candlestick_chart, options, date_container_text

        # return [], go.Figure()

    # except Exception as e:
        # print(f'Exception {e}')


def get_close_price(data, date):
    if date in data.index:
        return data["Close"][date]
    else:
        # Если ключ отсутствует, ищем ближайшую дату
        closest_date_index = data.index.get_indexer([date], method='nearest')[0]
        return data['Close'].iloc[closest_date_index]
    
def get_start_end_pairs(first_history_year):
    dates_pairs = []
    for year in range(first_history_year, datetime.today().year + 1):
        start_date = datetime.strptime(f"{year}-01-01", '%Y-%m-%d')
        end_date = start_date + timedelta(days=365)
        dates_pairs.append({
            'start': start_date,
             'end': end_date
        })

    return dates_pairs


layout()