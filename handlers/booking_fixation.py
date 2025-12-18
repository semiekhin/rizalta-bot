"""
Обработчики фиксации клиентов на ri.rclick.ru

Состояния диалога:
- waiting_phone: ждём телефон риэлтора
- waiting_password: ждём пароль
- waiting_client_name: ждём ФИО клиента
- waiting_client_phone: ждём телефон клиента
- waiting_client_comment: ждём комментарий (опционально)
"""

from typing import Dict, Any
from services.telegram import send_message, send_message_inline
from services.rclick_service import (
    is_authorized,
    get_token,
    save_token,
    delete_token,
    login_rclick,
    create_booking
)

# Хранение состояний диалога (в памяти, для простоты)
# В продакшене лучше использовать Redis или БД
user_states: Dict[int, Dict[str, Any]] = {}


def get_state(telegram_id: int) -> Dict[str, Any]:
    """Получает состояние пользователя."""
    return user_states.get(telegram_id, {})


def set_state(telegram_id: int, state: str, data: Dict[str, Any] = None):
    """Устанавливает состояние пользователя."""
    user_states[telegram_id] = {
        "state": state,
        "data": data or {}
    }


def clear_state(telegram_id: int):
    """Очищает состояние пользователя."""
    if telegram_id in user_states:
        del user_states[telegram_id]


async def handle_booking_menu(chat_id: int, telegram_id: int):
    """Главное меню фиксации."""
    
    if is_authorized(telegram_id):
        # Уже авторизован — показываем меню фиксации
        text = """📌 <b>Фиксация клиента</b>

Вы авторизованы в системе ri.rclick.ru

Выберите действие:"""
        
        inline_buttons = [
            [{"text": "➕ Новая фиксация", "callback_data": "booking_new"}],
            [{"text": "🔄 Сменить аккаунт", "callback_data": "booking_reauth"}],
            [{"text": "🔙 В меню", "callback_data": "main_menu"}],
        ]
    else:
        # Не авторизован — предлагаем авторизоваться
        text = """📌 <b>Фиксация клиента</b>

Для фиксации клиентов нужно авторизоваться в системе ri.rclick.ru

Это нужно сделать один раз. Потом бот будет фиксировать клиентов автоматически."""
        
        inline_buttons = [
            [{"text": "🔑 Авторизоваться", "callback_data": "booking_auth"}],
            [{"text": "📝 Регистрация на ri.rclick.ru", "url": "https://ri.rclick.ru/signup/"}],
            [{"text": "🔙 В меню", "callback_data": "main_menu"}],
        ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_booking_auth_start(chat_id: int, telegram_id: int):
    """Начало авторизации."""
    set_state(telegram_id, "waiting_phone")
    
    text = """🔑 <b>Авторизация ri.rclick.ru</b>

Введите ваш <b>телефон</b> от личного кабинета ri.rclick.ru:

<i>Формат: 89181234567 или +79181234567</i>"""
    
    inline_buttons = [
        [{"text": "❌ Отмена", "callback_data": "booking_cancel"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_booking_reauth(chat_id: int, telegram_id: int):
    """Повторная авторизация (смена аккаунта)."""
    delete_token(telegram_id)
    await handle_booking_auth_start(chat_id, telegram_id)


async def handle_booking_new(chat_id: int, telegram_id: int):
    """Начало новой фиксации."""
    if not is_authorized(telegram_id):
        await handle_booking_auth_start(chat_id, telegram_id)
        return
    
    set_state(telegram_id, "waiting_client_name")
    
    text = """📝 <b>Новая фиксация</b>

Введите <b>ФИО клиента</b> полностью:

<i>Пример: Иванов Иван Иванович</i>"""
    
    inline_buttons = [
        [{"text": "❌ Отмена", "callback_data": "booking_cancel"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_booking_cancel(chat_id: int, telegram_id: int):
    """Отмена операции."""
    clear_state(telegram_id)
    
    text = "❌ Операция отменена"
    inline_buttons = [
        [{"text": "📌 Фиксация", "callback_data": "booking_menu"}],
        [{"text": "🔙 В меню", "callback_data": "main_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_booking_input(chat_id: int, telegram_id: int, text: str):
    # Если нажата кнопка меню — сбрасываем состояние
    menu_buttons = ["📖 О проекте", "💰 Расчёты", "📋 КП", "📄 Договоры", "📊 Депозит",
                    "📌 Фиксация", "🏠 Шахматка", "🎬 Медиа", "📰 Новости", "🔥 Записаться"]
    if any(btn in text for btn in menu_buttons):
        clear_state(telegram_id)
        return False
    """
    Обработка текстового ввода в зависимости от состояния.
    Возвращает True если сообщение обработано, False если нет активного состояния.
    """
    state_data = get_state(telegram_id)
    state = state_data.get("state")
    data = state_data.get("data", {})
    
    if not state:
        return False
    
    if state == "waiting_phone":
        # Сохраняем телефон, просим пароль
        phone = text.strip()
        set_state(telegram_id, "waiting_password", {"phone": phone})
        
        msg = """🔐 Теперь введите <b>пароль</b> от ri.rclick.ru:

<i>Пароль не сохраняется — только токен авторизации</i>"""
        
        inline_buttons = [
            [{"text": "❌ Отмена", "callback_data": "booking_cancel"}],
        ]
        await send_message_inline(chat_id, msg, inline_buttons)
        return True
    
    elif state == "waiting_password":
        # Авторизуемся
        phone = data.get("phone", "")
        password = text.strip()
        
        await send_message(chat_id, "⏳ Авторизация...")
        
        result = login_rclick(phone, password)
        
        if result["success"]:
            save_token(telegram_id, phone, result["token"], result.get("agent_name", ""))
            clear_state(telegram_id)
            
            msg = """✅ <b>Авторизация успешна!</b>

Теперь вы можете фиксировать клиентов прямо из бота."""
            
            inline_buttons = [
                [{"text": "➕ Новая фиксация", "callback_data": "booking_new"}],
                [{"text": "🔙 В меню", "callback_data": "main_menu"}],
            ]
            await send_message_inline(chat_id, msg, inline_buttons)
        else:
            clear_state(telegram_id)
            
            msg = f"""❌ <b>Ошибка авторизации</b>

{result["error"]}

Попробуйте ещё раз."""
            
            inline_buttons = [
                [{"text": "🔑 Повторить", "callback_data": "booking_auth"}],
                [{"text": "🔙 В меню", "callback_data": "main_menu"}],
            ]
            await send_message_inline(chat_id, msg, inline_buttons)
        
        return True
    
    elif state == "waiting_client_name":
        # Сохраняем ФИО, просим телефон
        client_name = text.strip()
        set_state(telegram_id, "waiting_client_phone", {"client_name": client_name})
        
        msg = f"""📱 Клиент: <b>{client_name}</b>

Введите <b>телефон клиента</b>:

<i>Формат: 89991234567</i>"""
        
        inline_buttons = [
            [{"text": "❌ Отмена", "callback_data": "booking_cancel"}],
        ]
        await send_message_inline(chat_id, msg, inline_buttons)
        return True
    
    elif state == "waiting_client_phone":
        # Сохраняем телефон, просим комментарий
        client_name = data.get("client_name", "")
        client_phone = text.strip()
        
        set_state(telegram_id, "waiting_client_comment", {
            "client_name": client_name,
            "client_phone": client_phone
        })
        
        msg = f"""📝 Клиент: <b>{client_name}</b>
📱 Телефон: <b>{client_phone}</b>

Введите <b>комментарий</b> (например, какой лот интересует):

<i>Или нажмите "Пропустить"</i>"""
        
        inline_buttons = [
            [{"text": "⏭ Пропустить", "callback_data": "booking_skip_comment"}],
            [{"text": "❌ Отмена", "callback_data": "booking_cancel"}],
        ]
        await send_message_inline(chat_id, msg, inline_buttons)
        return True
    
    elif state == "waiting_client_comment":
        # Отправляем фиксацию
        client_name = data.get("client_name", "")
        client_phone = data.get("client_phone", "")
        comment = text.strip()
        
        await send_booking(chat_id, telegram_id, client_name, client_phone, comment)
        return True
    
    return False


async def handle_booking_skip_comment(chat_id: int, telegram_id: int):
    """Пропуск комментария."""
    state_data = get_state(telegram_id)
    data = state_data.get("data", {})
    
    client_name = data.get("client_name", "")
    client_phone = data.get("client_phone", "")
    
    await send_booking(chat_id, telegram_id, client_name, client_phone, "")


async def send_booking(chat_id: int, telegram_id: int, client_name: str, client_phone: str, comment: str):
    """Отправляет фиксацию на ri.rclick.ru."""
    clear_state(telegram_id)
    
    token = get_token(telegram_id)
    if not token:
        msg = "❌ Токен истёк. Авторизуйтесь заново."
        inline_buttons = [
            [{"text": "🔑 Авторизоваться", "callback_data": "booking_auth"}],
            [{"text": "📝 Регистрация на ri.rclick.ru", "url": "https://ri.rclick.ru/signup/"}],
        ]
        await send_message_inline(chat_id, msg, inline_buttons)
        return
    
    await send_message(chat_id, "⏳ Отправляю фиксацию...")
    
    result = create_booking(token, client_name, client_phone, comment)
    
    if result["success"]:
        msg = f"""✅ <b>Клиент зафиксирован!</b>

👤 {client_name}
📱 {client_phone}
{f"💬 {comment}" if comment else ""}

Информация отправлена в CRM застройщика."""
        
        inline_buttons = [
            [{"text": "➕ Ещё фиксация", "callback_data": "booking_new"}],
            [{"text": "🔙 В меню", "callback_data": "main_menu"}],
        ]
    else:
        msg = f"""❌ <b>Ошибка фиксации</b>

{result["error"]}"""
        
        inline_buttons = [
            [{"text": "🔄 Повторить", "callback_data": "booking_new"}],
            [{"text": "🔙 В меню", "callback_data": "main_menu"}],
        ]
    
    await send_message_inline(chat_id, msg, inline_buttons)


def has_active_booking_state(telegram_id: int) -> bool:
    """Проверяет есть ли активное состояние фиксации."""
    state_data = get_state(telegram_id)
    return bool(state_data.get("state"))
