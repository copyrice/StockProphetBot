
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import datetime
from sklearn.ensemble import RandomForestRegressor, BaggingRegressor
from xgboost import XGBRFRegressor, XGBRegressor
from catboost import CatBoostRegressor
from .basennmodel import BaseNNModel

class NNModels:
    def __init__(self):
        self.estimators = 100
        self.random_state = 41

        self.rf_model = BaseNNModel(RandomForestRegressor(n_estimators=self.estimators, random_state=self.random_state), 'RandomForestRegressor', 'Метод случайного леса')
        self.bagging_model = BaseNNModel(BaggingRegressor(estimator=self.rf_model.model, n_estimators=self.estimators, random_state=self.random_state), 'Bagging', 'Бэггинг')
        self.xgbr_model = BaseNNModel(XGBRegressor(), 'Extreme Gradient Boosting', 'Градиентный бустинг', 50)
        self.xgbrf_model = BaseNNModel(XGBRFRegressor(), 'Extreme Gradient Boosting with Random Forest', 'Градиентный бустинг c использованием метода случайного леса', 50)
        self.catbr_model = BaseNNModel(CatBoostRegressor(random_seed=0, logging_level='Silent'), 'CatBoost Regressor', 'Градиентный бустинг CatBoost', 5)

        self.models_list = [
            self.rf_model, self.bagging_model, self.xgbr_model, self.xgbrf_model, self.catbr_model
        ]
