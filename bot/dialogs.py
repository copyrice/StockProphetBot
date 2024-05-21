from typing import Any
from magic_filter import F
from items import graph_fields_list, ticker_fields_list, portfolio_menu_size, report_fields_list
from states import MainMenu, TickerMenu, PortfolioMenu, FindMenu
from getters import (get_ticker_info, get_category_info, graphs_getter, description_getter, recommendations_getter,
                     indices_getter, news_getter, portfolio_getter, predictions_getter, report_getter)

from handlers import input_ticker_handler, other_type_handler, input_days_handler, input_time_handler

from onclicks import (on_ticker_field_choose, on_find, on_portfolio, on_category_chosen,
                       on_translate_button_clicked, on_click,
                       on_graph_field_choose, on_description_switch_to, on_add_to_portfolio_click,
                       on_back_to_main_menu_click, on_ticker_choose, on_remove_from_portfolio_click,
                       on_back_to_portfolio_click, on_predictions_click, on_enable_notifications_click, on_disable_notifications_click,
                       on_report_click, on_report_field_choose)

from onresults import on_ticker_menu_result

from aiogram_dialog import Dialog, Window, setup_dialogs, DialogManager
from aiogram_dialog.widgets.text import Format, Const, Jinja
from aiogram_dialog.widgets.kbd import Checkbox, Button, Back, Url
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Row, Select, SwitchTo, Group, Cancel, ScrollingGroup
from aiogram.types import ContentType
import operator

welcome_message = f"Приветствую!\n\n🤖 StockProphetBot может помочь в получении данных об акциях, криптовалютах и индексах\n\n📊 Показать тенденции рынка\n\n💼 Cоставить портфолио и следить за его изменением в реальном времени\n\n📈Получение прогноза движения графика актива на основе нейросетей"



translate_button = Button(
    Const('Перевести текст'),
    id='translate',
    on_click=on_translate_button_clicked)

back_button = Back(
    Const("<<"),
    id='b_back',
    on_click=on_click
    )

cancel_button = Cancel(
    Const("<<"),
    id='b_cancel',
    on_click=on_click
    )

switch_to_ticker_info = SwitchTo(
    Const("<<"),
    id='b_switch',
    state=TickerMenu.ticker_info
)

dialogs = [
     Dialog(
        Window(
            Const(welcome_message),
            Button(
                Const('🔎Поиск'),
                id='find',
                on_click=on_find),

            Button(
                Const('💼Портфолио'),
                id='portfolio',
                on_click=on_portfolio),
            state=MainMenu.start,
            
        )
    ),
    Dialog(
        Window(
            Format('{portfolio_message}'),
            ScrollingGroup(
                Select(
                Format("{item[0]}"),
                items='tickers',
                item_id_getter=operator.itemgetter(2),
                id="ticker_item",
                on_click=on_ticker_choose,
                ),
                id="portfolio_tickers",
                width=portfolio_menu_size['width'],
                height=portfolio_menu_size['height'],
            ),
            Button(
                Const("🔔 Уведомлять об изменениях"),
                id='notifications_btn',
                on_click=on_enable_notifications_click,
                when=F["notifications_disabled"]
            ),
            Button(
                Const("🔕 Отключить уведомления"),
                id='notifications_cancel_btn',
                on_click=on_disable_notifications_click,
                when=F["notifications_enabled"]
            ),
            cancel_button,
            state=PortfolioMenu.main,
            getter=portfolio_getter,
            parse_mode="HTML"
        ),
        Window(
            Const('Введите время формата HH:MM (19:00)'),
            MessageInput(input_time_handler, content_types=[ContentType.TEXT]),
            MessageInput(other_type_handler),
            back_button,
            state=PortfolioMenu.waiting_for_time
            ),
        
    ),
    Dialog(
        Window(
            Const("Выбор категории поиска:"),
            Button(Const('🌐 Международные акции'), id='ir_stock', on_click=on_category_chosen),
            Button(Const('🌐 ^Международные индексы'), id='ir_index', on_click=on_category_chosen),
            Button(Const('🔸 Криптовалюта'), id='crypto', on_click=on_category_chosen),
            Button(Const('🇷🇺 Российские акции'), id='ru_stock', on_click=on_category_chosen),
            Button(Const('🇷🇺 Российские индексы'), id='ru_index', on_click=on_category_chosen),
            Button(
                Const("<<"),
                id='b_cancel',
                on_click=on_back_to_main_menu_click,
                
            ),
            state=FindMenu.choosing_category,
            
        ),
        Window(
            Format("Введите символ {message}"),
            MessageInput(input_ticker_handler, content_types=[ContentType.TEXT]),
            MessageInput(other_type_handler),
            Back(
                 Const("<<"),
                id='b_back',
                on_click=on_click
            ),
            state=FindMenu.entering_symbol,
            getter=get_category_info
        ),
    ),
    Dialog(
        Window(
            Format("{introduction_message}"),
            Group(
            Select(
                Format("{item}"),
                items='items_fields',
                item_id_getter=lambda x: x,
                id="w_item",
                on_click=on_ticker_field_choose,
            ),
            width=2,
            ),
            Group(
            Button(
                Format(f"🤖 Прогнозы"),
                id='predictions_btn',
                on_click=on_predictions_click
            ),
            Button(
                Format(f"📄 Отчет"),
                id='report_btn',
                on_click=on_report_click
            ),
            width=2),
            Url(
                text=Const('📌 Анализ'),
                url=Format('{user_link}')
            ),
            Button(
            Const(f"💼 Добавить в портфолио"),
            id='portfolio_add',
            on_click=on_add_to_portfolio_click,
            when=F["parent_find"]
            ),
            Button(
            Const(f"❌ Удалить из портфолио"),
            id='portfolio_remove',
            on_click=on_remove_from_portfolio_click,
            when=F['parent_portfolio']
            ),

            Button(
                Const("<<"),
                id='back_btn',
                on_click=on_back_to_portfolio_click
            ),
            state=TickerMenu.ticker_info,
            getter=get_ticker_info,
            parse_mode="HTML",
        ),
        Window(
            Format("{predictions_message}"),
            switch_to_ticker_info,
            parse_mode="HTML",
            state=TickerMenu.predictions,
            getter=predictions_getter
        ),
        Window(
            Format("Построить графики для {symbol}"),
            Select(
                Format("{item}"),
                items=graph_fields_list,
                item_id_getter=lambda x: x,
                id="w_item",
                on_click=on_graph_field_choose,
            ),
            switch_to_ticker_info,
            state=TickerMenu.graphs,
            getter=graphs_getter
        ),
        Window(
            Const('Введите количество дней...'),
            MessageInput(input_days_handler, content_types=[ContentType.TEXT]),
            MessageInput(other_type_handler),
            switch_to_ticker_info,
            state=TickerMenu.waiting_for_days
        ),
        Window(
            Format('{recommendations_message}'),
            switch_to_ticker_info,
            parse_mode="HTML",
            state=TickerMenu.recommendations,
            getter=recommendations_getter
        ),
        Window(
            Format('{indices_message}'),
            switch_to_ticker_info,
            parse_mode="HTML",
            state=TickerMenu.indices,
            getter=indices_getter
        ),
        Window(
            Format('📰 {news_message}'),
            switch_to_ticker_info,
            parse_mode="HTML",
            state=TickerMenu.news,
            getter=news_getter
        ),
        Window(
            Format('{descriptopn}'),
            translate_button,
            SwitchTo(
                Const("<<"),
                id='d_switch',
                state=TickerMenu.ticker_info,
                on_click=on_description_switch_to
            ),
            state=TickerMenu.description,
            getter=description_getter
        ),
        Window(
            Format('{report_message}'),
            Group(
            Select(
                Format("{item[0]}"),
                items=report_fields_list,
                item_id_getter=operator.itemgetter(1),
                id="w_item",
                on_click=on_report_field_choose,
            ),
            width=1),
            switch_to_ticker_info,
            state=TickerMenu.report,
            getter=report_getter,
            parse_mode='HTML'
        ),
        
    )

]