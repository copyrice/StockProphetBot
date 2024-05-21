from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Awaitable, Any
from googletrans import Translator

translator = Translator()

class TranslatorMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        self.translator = translator
        data['translator'] = self.translator 
        return await handler(event, data)