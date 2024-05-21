import dash
from dash import html
from flask import request


dash.register_page(__name__, path='/')

def layout():
    layout = html.Div([
        html.H1('Home page'),
    ])
    return layout