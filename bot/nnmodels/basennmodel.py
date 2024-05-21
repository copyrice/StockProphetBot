

class BaseNNModel:
    def __init__(self, model, name: str = '', ru_name: str = '', base_train_days_amount: int = 100) -> None:
        self.model = model
        self.name = name
        self.ru_name = ru_name
        self.base_train_days_amount = base_train_days_amount