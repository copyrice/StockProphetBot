
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import datetime
from nnmodels.nnmodels import NNModels

class Predictor:
    def __init__(self, nnmodels: NNModels) -> None:
        self.nnmodels = nnmodels
        self.train_days_amount = 1000

    def predict_(self, data: pd.DataFrame, features: list[str], target: str, random_state: int, model):
        data['Date'] = pd.to_numeric(pd.to_datetime(data['Date']))
        x = data[features]
        y = data[target]

        x = x.to_numpy()
        y = y.to_numpy()

        X_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=random_state)

        model.fit(X_train, y_train)

        last_date = data["Date"].iloc[-1]

        future_days_extension = 1
        future_dates = []
        future_dates.append(last_date + datetime.timedelta(days=future_days_extension+1).total_seconds()*10**9)
        future_data_extension = pd.DataFrame()
        for col in data.columns:
            if col != 'Date':
                future_data_extension[col] = [np.nan]
        future_data_extension['Date'] = future_dates
        # future_data_extension = pd.DataFrame({
        # 'Date': future_dates,
        # 'Open': np.nan,
        # 'High': np.nan,
        # 'Low': np.nan,
        # 'Close': np.nan,
        # 'Volume': np.nan
        # })
        future_data_extension['Date'] = pd.to_numeric(pd.to_datetime(future_data_extension['Date']))

        pred_ = model.predict(data.to_numpy())

        prediction = model.predict(future_data_extension.to_numpy())

        return prediction[0]
        

    @staticmethod
    def predict(data: pd.DataFrame, features: list[str], target: str, random_state: int, model):
        data['Date'] = pd.to_numeric(pd.to_datetime(data['Date']))
        x = data[features]
        y = data[target]

        x = x.to_numpy()
        y = y.to_numpy()

        X_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=random_state)

        model.fit(X_train, y_train)

        last_date = data["Date"].iloc[-1]

        future_days_extension = 1
        future_dates = []
        future_dates.append(last_date + datetime.timedelta(days=future_days_extension+1).total_seconds()*10**9)
        future_data_extension = pd.DataFrame()
        for col in data.columns:
            if col != 'Date':
                future_data_extension[col] = [np.nan]
        future_data_extension['Date'] = future_dates
        # future_data_extension = pd.DataFrame({
        # 'Date': future_dates,
        # 'Open': np.nan,
        # 'High': np.nan,
        # 'Low': np.nan,
        # 'Close': np.nan,
        # 'Volume': np.nan
        # })
        future_data_extension['Date'] = pd.to_numeric(pd.to_datetime(future_data_extension['Date']))

        pred_ = model.predict(data.to_numpy())

        prediction = model.predict(future_data_extension.to_numpy())

        return prediction[0]
    

def get_prediction_emoji(previous_close: int, prediction_close: int):
        if(previous_close <  prediction_close):
            return '📈'
        if(previous_close > prediction_close):
            return '📉'
        
        return '📊'
    
def get_prediction_text(previous_close: int, prediction_close: int):
        if(previous_close <  prediction_close):
            return 'рост'
        if(previous_close > prediction_close):
            return 'падение'
        
        return ''
