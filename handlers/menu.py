"""
Обработчики меню и навигации.
"""

import os
from typing import Dict, Any

from config.settings import (
    MAIN_MENU_BUTTONS,
    ABOUT_PROJECT_BUTTONS,
    CALCULATIONS_BUTTONS,
    UNIT_SELECT_BUTTONS,
    TEXT_WHY_RIZALTA_PATH,
    ARCHITECT_PDF_PATH,
)
from models.state import (
    clear_user_state,
    clear_dialog_state,
    set_dialog_state,
    DialogStates,
)
from services.telegram import send_message, send_message_inline, send_document, send_photo_inline
from services.data_loader import load_why_rizalta_text


async def handle_start(chat_id: int, text: str = "", user_info: Dict[str, Any] = None):
    """
    Обработка /start — приветствие и главное меню.
    """
    # Полностью очищаем все состояния
    clear_user_state(chat_id)
    
    welcome = (
        "Добро пожаловать в RIZALTA AI SYSTEM!\n\n"
        "🚀 Я первый AI-консультант по инвестициям в курортную недвижимость Алтая.\n\n"
        "<b>RIZALTA RESORT BELOKURIKHA</b> — премиальный комплекс курортных отелей "
        "с международным уровнем сервиса в туристическом центре Большого Алтая.\n\n"
        "🤖 <b>Что я умею:</b>\n\n"
        "• Предоставляю актуальную информацию и презентации проекта\n"
        "• Отвечаю на вопросы голосом и текстом\n"
        "• Помогаю записаться на онлайн-показ\n"
        "• Рассчитываю доходность любого гостиничного номера\n"
        "• Подбираю варианты рассрочки и ипотеки\n"
        "• Генерирую персональные коммерческие предложения для клиентов\n"
        "• Показываю планировки\n"
        "• Направляю фото и видео-материалы\n\n"
        "⬇️ Выберите необходимый раздел в меню ниже или задайте мне свой вопрос!"
    )
    
    await send_message(chat_id, welcome, with_keyboard=True, buttons=MAIN_MENU_BUTTONS)


async def handle_help(chat_id: int):
    """Обработка /help."""
    text = (
        "🆘 <b>Помощь по боту RIZALTA</b>\n\n"
        "Используйте кнопки меню или напишите свой вопрос — я постараюсь ответить.\n\n"
        "<b>Основные разделы:</b>\n"
        "📖 О проекте — информация о RIZALTA и Алтае\n"
        "💰 Расчёты — доходность, рассрочка, ипотека\n"
        "🎯 Подобрать лот — подбор по бюджету\n"
        "📎 Планировки — PDF-документы\n"
        "✅ Записаться — связь с менеджером\n\n"
        "Вы также можете задать любой вопрос текстом."
    )
    await send_message(chat_id, text, with_keyboard=True, buttons=MAIN_MENU_BUTTONS)


async def handle_back(chat_id: int):
    """
    Обработка кнопки "Назад" — возврат в главное меню.
    """
    clear_dialog_state(chat_id)
    
    await send_message(
        chat_id,
        "Главное меню:",
        with_keyboard=True,
        buttons=MAIN_MENU_BUTTONS,
    )


async def handle_main_menu(chat_id: int):
    """Показ главного меню."""
    buttons = MAIN_MENU_BUTTONS

    await send_message(
        chat_id,
        "Главное меню:",
        with_keyboard=True,
        buttons=buttons,
    )


# ====== Меню "О проекте" ======

async def handle_about_project(chat_id: int):
    """Подменю 'Купи себе отель!'."""
    text = """🔥<b>Купи себе отель!</b>

RIZALTA RESORT BELOKURIKHA — премиальный комплекс курортных отелей с международным уровнем сервиса в туристическом центре Большого Алтая.

🔹Четыре премиальных девятиэтажных корпуса 4* и 5* уровня.
🔸Рост капитализации объекта более 60% за период строительства.
🔹Окупаемость номера 6 лет, пассивный доход от 2 000 000 рублей в год.
🔸Номера в полной комплектации: ремонт, мебель и техника.
🔹Застройщик ГК «Жилищная инициатива» — 27 лет на строительном рынке.
🔸Международный отельный оператор «ZONT Hotel Group».

Срок сдачи объекта: 2027 год.

✅Становитесь частью одного из крупнейших проектов инвестиционной коммерческой недвижимости в России!"""

    inline_buttons = [
        [{"text": "🏢 Выбрать номер", "callback_data": "kp_menu"}],
        [{"text": "💰 Расчёт доходности", "callback_data": "calc_nav_menu"}],
        [{"text": "✅ Записаться на показ", "callback_data": "online_show"}],
    ]
    
    await send_photo_inline(chat_id, "/opt/bot/data/images/rizalta_resort.jpg", text, inline_buttons)


async def handle_why_altai(chat_id: int):
    """
    ❇️ Почему Алтай — готовый продающий текст.
    """
    text = (
        "<b>Почему нужно инвестировать в RIZALTA</b>\n\n"
        "❇️ <b>Алтай</b>\n\n"
        "🏆 Более 5 млн человек в год. Регион не зависит от сезонности.\n"
        "📈 Прогноз ведущих аналитиков: рост турпотока около +40% в ближайшие 5 лет.\n"
        "🏔️ Сочетание первозданной природы и развитой инфраструктуры.\n"
        "👼 Регион удалён от зон геополитических конфликтов.\n"
        "🚀 Стабильно высокий рост цен на землю и недвижимость — около 30% в год.\n"
        "💰 Главный инвестор — государство: в развитие территории планируется вложить более 300 млрд ₽ в ближайшие 5 лет.\n\n"
        "❇️ <b>Белокуриха</b>\n\n"
        "🗺️ «Ворота Алтая», находится в самом сердце региона.\n"
        "🥇 Один из лучших курортных городов России.\n"
        "🏥 Круглогодичный лечебный курорт с развитой санаторно-курортной базой.\n\n"
        "❇️ <b>RIZALTA</b>\n\n"
        "🏨 Комплекс отелей с богатой инфраструктурой — подойдёт и для отдыха, и для инвестиций.\n"
        "👍🏾 Федеральный отельный оператор с опытом управления гостиничным бизнесом.\n"
        "🫰 Доходность, подтверждённая авторитетным источником CORE.XP, — как правило выше, чем у обычного жилья или гостиничных номеров.\n"
        "🛡️ Безопасность вложений: проект реализуется по ФЗ-214 с проектным финансированием Сбербанка.\n\n"
        "Если хотите, могу подобрать лот под ваш бюджет и показать, "
        "как эти преимущества работают именно для вас. 💬"
    )
    
    inline_buttons = [
        [
            {"text": "🎯 Подобрать лот", "callback_data": "select_lot"},
            {"text": "📞 Вызвать менеджера", "callback_data": "call_manager"}
        ]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_why_rizalta(chat_id: int):
    """
    ✨ Почему RIZALTA — текст из файла.
    """
    text = load_why_rizalta_text()
    
    inline_buttons = [
        [
            {"text": "📊 Расчёт доходности", "callback_data": "calculate_roi"},
            {"text": "📞 Вызвать менеджера", "callback_data": "call_manager"}
        ]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_architect(chat_id: int):
    """
    👨‍🎨 Об архитекторе — отправка PDF.
    """
    if os.path.exists(ARCHITECT_PDF_PATH):
        await send_message(
            chat_id,
            "👨‍🎨 Отправляю официальный документ об архитекторе проекта RIZALTA.",
        )
        await send_document(chat_id, ARCHITECT_PDF_PATH)
    else:
        await send_message(
            chat_id,
            "Файл с информацией об архитекторе пока не загружен на сервер."
        )


# ====== Меню "Расчёты" ======

async def handle_calculations_menu(chat_id: int):
    """Подменю 'Расчёты'."""
    await send_message(
        chat_id,
        "💰 <b>Расчёты</b>\n\n📊 Доходность — сколько заработаете\n💳 Рассрочка — варианты оплаты\n📈 Сравнение — RIZALTA vs депозит\n\nВыберите:",
        with_keyboard=True,
        buttons=CALCULATIONS_BUTTONS,
    )


async def handle_choose_unit_for_roi(chat_id: int):
    """Выбор юнита для расчёта доходности."""
    set_dialog_state(chat_id, DialogStates.CHOOSE_ROI_UNIT)
    
    await send_message(
        chat_id,
        "📊 <b>Рентабельность и доходность</b>\n\nВыберите гостиничный номер для расчёта:",
        with_keyboard=True,
        buttons=UNIT_SELECT_BUTTONS,
    )


async def handle_choose_unit_for_finance(chat_id: int):
    """Выбор юнита для рассрочки/ипотеки."""
    set_dialog_state(chat_id, DialogStates.CHOOSE_FINANCE_UNIT)
    
    await send_message(
        chat_id,
        "💳 <b>Рассрочка и ипотека</b>\n\nВыберите гостиничный номер для расчёта:",
        with_keyboard=True,
        buttons=UNIT_SELECT_BUTTONS,
    )


async def handle_choose_unit_for_layout(chat_id: int):
    """Выбор юнита для планировки."""
    set_dialog_state(chat_id, DialogStates.CHOOSE_PLAN_UNIT)
    
    await send_message(
        chat_id,
        "📎 Выберите гостиничный номер, чтобы получить планировку:",
        with_keyboard=True,
        buttons=UNIT_SELECT_BUTTONS,
    )


async def handle_myid(chat_id: int, user_info: dict = None):
    """Показывает пользователю его Telegram chat_id."""
    username = user_info.get("username", "") if user_info else ""
    first_name = user_info.get("first_name", "") if user_info else ""
    
    text = f"ℹ️ <b>Ваши данные Telegram:</b>\n\n🆔 Chat ID: <code>{chat_id}</code>\n"
    if username:
        text += f"👤 Username: @{username}\n"
    if first_name:
        text += f"📝 Имя: {first_name}\n"
    text += "\n💡 <i>Chat ID используется для системы бронирования.</i>"
    
    await send_message(chat_id, text)
