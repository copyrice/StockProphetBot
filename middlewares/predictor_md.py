from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Awaitable, Any
from predictor import Predictor
from nnmodels.nnmodels import NNModels
class PredictorMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        nnmodels = NNModels()
        self.predictor = Predictor(nnmodels)
        data['predictor'] = self.predictor 
        return await handler(event, data)