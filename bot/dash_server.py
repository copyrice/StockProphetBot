from dash import Dash
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, use_pages=True, external_stylesheets=external_stylesheets)

if __name__ == '__main__':
    app.run(debug=True)

# def run_dash_app():
    # app.run(debug=True)