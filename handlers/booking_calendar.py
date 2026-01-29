"""
Календарь бронирования на онлайн-показ.
Выбор даты → время → заявка в группу → специалист берёт.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from services.telegram import send_message, send_message_inline
from services.user_profiles import get_profile, save_profile, convert_time, format_dual_time, validate_time

# Путь к базе данных
BOT_DB_PATH = "/opt/bot-dev/properties.db"

# === НАСТРОЙКИ ===

# Рабочие дни (0=Пн, 1=Вт, ..., 5=Сб, 6=Вс)
WORK_DAYS = [0, 1, 2, 3, 4, 5]  # Пн-Сб

# Рабочие часы
WORK_HOUR_START = 10
WORK_HOUR_END = 16  # Последний слот в 15:00 (на 1 час)

# Длительность слота в минутах
SLOT_DURATION = 60

# Сколько дней вперёд показывать
DAYS_AHEAD = 14

# Названия дней недели
WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS_RU = ["", "января", "февраля", "марта", "апреля", "мая", "июня", 
             "июля", "августа", "сентября", "октября", "ноября", "декабря"]


# === ИНИЦИАЛИЗАЦИЯ БД ===

def init_bookings_db():
    """Создаёт таблицу bookings если не существует."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            username TEXT,
            specialist_id INTEGER NOT NULL,
            specialist_name TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            contact_info TEXT,
            group_message_id INTEGER,
            taken_by_id INTEGER,
            taken_by_name TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_booked_slots(date_str: str) -> List[str]:
    """Возвращает список забронированных слотов на дату."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT booking_time FROM bookings 
        WHERE booking_date = ? AND status IN ('pending', 'taken', 'confirmed')
    """, (date_str,))
    slots = [row[0] for row in cursor.fetchall()]
    conn.close()
    return slots


def save_booking(chat_id: int, username: str, date_str: str, time_str: str,
                 contact_info: str = None) -> int:
    """Сохраняет бронирование в БД. Возвращает ID записи."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings (chat_id, username, specialist_id, specialist_name, 
                              booking_date, booking_time, contact_info)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (chat_id, username, 0, "", date_str, time_str, contact_info))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return booking_id


# === ГЕНЕРАЦИЯ СЛОТОВ ===

def get_available_dates() -> List[Dict]:
    """Возвращает список доступных дат на ближайшие дни."""
    dates = []
    today = datetime.now()
    
    for i in range(DAYS_AHEAD):
        date = today + timedelta(days=i)
        
        # Пропускаем нерабочие дни
        if date.weekday() not in WORK_DAYS:
            continue
        
        # Если сегодня и уже поздно — пропускаем
        if i == 0 and today.hour >= WORK_HOUR_END - 1:
            continue
        
        dates.append({
            "date": date,
            "date_str": date.strftime("%Y-%m-%d"),
            "display": f"{date.day} {WEEKDAYS_RU[date.weekday()]}"
        })
    
    return dates[:10]  # Максимум 10 дат


def get_available_times(date_str: str) -> List[str]:
    """Возвращает список свободных слотов на дату."""
    booked = get_booked_slots(date_str)
    
    times = []
    for hour in range(WORK_HOUR_START, WORK_HOUR_END):
        time_str = f"{hour:02d}:00"
        
        # Пропускаем занятые
        if time_str in booked:
            continue
        
        # Если сегодня — пропускаем прошедшие
        today = datetime.now()
        if date_str == today.strftime("%Y-%m-%d") and hour <= today.hour:
            continue
        
        times.append(time_str)
    
    return times


def format_date_display(date_str: str) -> str:
    """Форматирует дату для отображения: 9 декабря (Пн)"""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{date.day} {MONTHS_RU[date.month]} ({WEEKDAYS_RU[date.weekday()]})"


# === ХРАНИЛИЩЕ СОСТОЯНИЙ БРОНИРОВАНИЯ ===

# chat_id -> {"date": ...}
booking_states: Dict[int, Dict] = {}


def set_booking_state(chat_id: int, **kwargs):
    """Сохраняет состояние бронирования."""
    if chat_id not in booking_states:
        booking_states[chat_id] = {}
    booking_states[chat_id].update(kwargs)


def get_booking_state(chat_id: int) -> Dict:
    """Получает состояние бронирования."""
    return booking_states.get(chat_id, {})


def clear_booking_state(chat_id: int):
    """Очищает состояние бронирования."""
    if chat_id in booking_states:
        del booking_states[chat_id]


# === ОБРАБОТЧИКИ ===

async def handle_booking_start(chat_id: int):
    """Начало бронирования — выбор часового пояса."""
    init_bookings_db()
    clear_booking_state(chat_id)
    
    await send_message_inline(
        chat_id,
        "📅 <b>Запись на онлайн-показ</b>\n\n"
        "Выберите ваш часовой пояс:",
        [
            [{"text": "🌴 Москва / Сочи", "callback_data": "book_tz_moscow"}],
            [{"text": "🏔 Алтай / Сибирь", "callback_data": "book_tz_altai"}],
            [{"text": "🔙 В меню", "callback_data": "back_to_menu"}]
        ]
    )


async def handle_select_timezone(chat_id: int, tz: str):
    """Выбран часовой пояс — показываем даты."""
    set_booking_state(chat_id, user_tz=tz)
    
    dates = get_available_dates()
    if not dates:
        await send_message(chat_id, "К сожалению, нет доступных дат. Попробуйте позже.")
        return
    
    # Группируем по 5 кнопок в ряд
    buttons = []
    row = []
    for d in dates:
        row.append({
            "text": d["display"],
            "callback_data": f"book_date_{d['date_str']}"
        })
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([{"text": "◀️ Назад", "callback_data": "online_show"}, {"text": "🔙 В меню", "callback_data": "back_to_menu"}])
    
    tz_name = "Москва/Сочи" if tz == "moscow" else "Алтай/Сибирь"
    
    await send_message_inline(
        chat_id,
        f"🌍 Ваш пояс: <b>{tz_name}</b>\n\n"
        "📅 Выберите дату:",
        buttons
    )


async def handle_select_date(chat_id: int, date_str: str):
    """Выбрана дата — просим ввести данные одним сообщением."""
    set_booking_state(chat_id, date=date_str, step="awaiting_booking_info")
    
    date_display = format_date_display(date_str)
    
    await send_message_inline(
        chat_id,
        f"📅 <b>{date_display}</b>\n\n"
        "Напишите <b>одним сообщением</b>:\n"
        "Время, телефон, имя, агентство\n\n"
        "<i>Пример:</i>\n"
        "<code>10:30 +79991234567 Иван АН Риэлт</code>",
        [
            [{"text": "◀️ Назад", "callback_data": "online_show"}, {"text": "🔙 В меню", "callback_data": "back_to_menu"}]
        ]
    )


async def handle_select_time(chat_id: int, time_str: str, username: str = None):
    """Выбрано время — отправляем заявку в группу."""
    state = get_booking_state(chat_id)
    date_str = state.get("date")
    
    if not date_str:
        await handle_booking_start(chat_id)
        return
    
    # Форматируем время обратно (1000 -> 10:00)
    time_formatted = f"{time_str[:2]}:{time_str[2:]}"
    
    # Сохраняем в БД со статусом pending
    booking_id = save_booking(
        chat_id=chat_id,
        username=username,
        date_str=date_str,
        time_str=time_formatted
    )
    
    date_display = format_date_display(date_str)
    
    # Очищаем состояние
    clear_booking_state(chat_id)
    
    # Отправляем клиенту сообщение об ожидании
    await send_message_inline(
        chat_id,
        f"⏳ <b>Заявка отправлена!</b>\n\n"
        f"📅 Дата: {date_display}\n"
        f"🕐 Время: {time_formatted}\n"
        f"🆔 Номер заявки: #{booking_id}\n\n"
        "Ожидайте подтверждения от специалиста.\n"
        "Вы получите уведомление.",
        [[{"text": "🔙 В главное меню", "callback_data": "back_to_menu"}]]
    )
    
    # Отправляем в группу показов с кнопкой "Взять"
    try:
        from config.settings import SHOWS_GROUP_ID
        from services.telegram import send_message_inline_return_id
        
        group_msg = (
            f"🆕 <b>Новая заявка на онлайн-показ</b>\n\n"
            f"📅 {date_display}, {time_formatted}\n"
            f"📱 Клиент: @{username if username else chat_id}\n"
            f"🆔 Заявка: #{booking_id}"
        )
        group_buttons = [[{"text": "🙋 Взять заявку", "callback_data": f"book_take_{booking_id}"}]]
        
        if SHOWS_GROUP_ID:
            msg_id = await send_message_inline_return_id(SHOWS_GROUP_ID, group_msg, group_buttons)
            if msg_id:
                save_booking_group_message_id(booking_id, msg_id)
    except Exception as e:
        print(f"[BOOKING] Group notify error: {e}")


def get_booking_by_id(booking_id: int) -> Optional[Dict]:
    """Получает запись по ID."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, chat_id, username, specialist_id, specialist_name, 
               booking_date, booking_time, status
        FROM bookings WHERE id = ?
    """, (booking_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "chat_id": row[1],
            "username": row[2],
            "specialist_id": row[3],
            "specialist_name": row[4],
            "booking_date": row[5],
            "booking_time": row[6],
            "status": row[7]
        }
    return None


def update_booking_status(booking_id: int, status: str):
    """Обновляет статус записи."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings SET status = ? WHERE id = ?
    """, (status, booking_id))
    conn.commit()
    conn.close()


async def handle_take_booking(chat_id: int, booking_id: int, from_user: dict):
    """Специалист взял заявку из группы."""
    from services.telegram import edit_message_inline
    from services.secretary_db import add_task
    from config.settings import SHOWS_GROUP_ID
    
    booking = get_booking_by_id(booking_id)
    
    if not booking:
        await send_message(chat_id, "❌ Заявка не найдена.")
        return
    
    if booking["status"] != "pending":
        pass  # Тихо игнорируем повторное нажатие
        return
    
    # Получаем данные специалиста
    user_id = from_user.get("id", chat_id)
    first_name = from_user.get("first_name", "")
    last_name = from_user.get("last_name", "")
    username = from_user.get("username", "")
    full_name = f"{first_name} {last_name}".strip() or username or str(user_id)
    
    # Обновляем статус в БД
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings 
        SET status = 'taken', taken_by_id = ?, taken_by_name = ?
        WHERE id = ?
    """, (user_id, full_name, booking_id))
    conn.commit()
    conn.close()
    
    date_display = format_date_display(booking["booking_date"])
    
    # Редактируем сообщение в группе
    group_message_id = get_booking_group_message_id(booking_id)
    if group_message_id and SHOWS_GROUP_ID:
        try:
            new_text = (
                f"✅ <b>Заявка #{booking_id} — ВЗЯТА</b>\n\n"
                f"👤 Взял: {full_name}\n"
                f"📅 {date_display}, {booking['booking_time']}\n"
                f"📱 Клиент: @{booking['username'] or booking['chat_id']}"
            )
            await edit_message_inline(SHOWS_GROUP_ID, group_message_id, new_text, None)
        except Exception as e:
            print(f"[BOOKING] Error editing group message: {e}")
    
    # Добавляем задачу в секретарь специалисту
    try:
        client_info = f"@{booking['username']}" if booking['username'] else f"ID:{booking['chat_id']}"
        task_text = f"📞 Онлайн-показ: {client_info}"
        add_task(
            user_id=user_id,
            task_text=task_text,
            due_date=booking["booking_date"],
            due_time=booking["booking_time"],
            client_name=client_info,
            priority="high"
        )
    except Exception as e:
        print(f"[BOOKING] Error adding task: {e}")
    
    # Уведомляем клиента
    await send_message_inline(
        booking["chat_id"],
        f"✅ <b>Ваша заявка принята!</b>\n\n"
        f"👤 Специалист: {full_name}\n"
        f"📅 {date_display}, {booking['booking_time']}\n\n"
        f"Специалист свяжется с вами в назначенное время.",
        [[{"text": "🔙 В главное меню", "callback_data": "back_to_menu"}]]
    )


def get_booking_group_message_id(booking_id: int) -> Optional[int]:
    """Получает message_id сообщения в группе."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT group_message_id FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


def save_booking_group_message_id(booking_id: int, message_id: int):
    """Сохраняет message_id сообщения в группе."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET group_message_id = ? WHERE id = ?", (message_id, booking_id))
    conn.commit()
    conn.close()


async def handle_booking_text_input(chat_id: int, text: str, user_info: dict = None) -> bool:
    """
    Обрабатывает текстовый ввод в процессе бронирования.
    Возвращает True если сообщение обработано, False если нет активного состояния.
    """
    state = get_booking_state(chat_id)
    step = state.get("step")
    
    if not step:
        return False
    
    # === Шаг: ввод всех данных одним сообщением ===
    if step == "awaiting_booking_info":
        # Парсим: время, телефон, имя, агентство
        parsed = parse_booking_message(text)
        
        if not parsed.get("time"):
            await send_message_inline(
                chat_id,
                "❌ Не удалось распознать время.\n\n"
                "Напишите в формате:\n"
                "<code>10:30 +79991234567 Иван АН Риэлт</code>",
                [[{"text": "◀️ Назад", "callback_data": "online_show"}]]
            )
            return True
        
        # Сохраняем
        set_booking_state(
            chat_id,
            time=parsed["time"],
            realtor_phone=parsed.get("phone", ""),
            contact=parsed.get("contact", ""),
            step="confirm_booking"
        )
        
        # Показываем подтверждение
        await show_booking_confirmation(chat_id, user_info)
        return True
    
    # === Шаг: ввод телефона (если добавляют отдельно) ===
    if step == "awaiting_phone":
        import re
        phone_match = re.search(r'[\+]?[0-9]{10,12}', text.replace(" ", ""))
        if phone_match:
            phone = phone_match.group()
            save_profile(chat_id, phone=phone)
            set_booking_state(chat_id, realtor_phone=phone, step="confirm_booking")
            await show_booking_confirmation(chat_id, user_info)
        else:
            await send_message(chat_id, "❌ Не удалось распознать номер. Введите телефон цифрами.")
        return True
    
    return False


def parse_booking_message(text: str) -> dict:
    """
    Парсит сообщение формата: 10:30 89181011091 Сергей Меганедвижка
    Возвращает: {time, phone, contact}
    """
    import re
    result = {"time": None, "phone": "", "contact": ""}
    
    # Ищем время (формат HH:MM или H:MM)
    time_match = re.search(r'\b(\d{1,2}[:\.][0-5]\d)\b', text)
    if time_match:
        time_str = time_match.group(1).replace(".", ":")
        validated = validate_time(time_str)
        if validated:
            result["time"] = validated
    
    # Ищем телефон: +79181011091 или 89181011091 (11 цифр)
    phone_match = re.search(r'[\+]?[78]\d{10}', text)
    if not phone_match:
        # Может быть без 8/7: 9181011091 (10 цифр)
        phone_match = re.search(r'\b9\d{9}\b', text)
    
    if phone_match:
        phone = re.sub(r'[^\d]', '', phone_match.group())
        result["phone"] = phone
    
    # Остальное — контакт (имя + агентство)
    remaining = text
    if time_match:
        remaining = remaining.replace(time_match.group(), "")
    if phone_match:
        remaining = remaining.replace(phone_match.group(), "")
    
    # Убираем лишние пробелы
    contact = " ".join(remaining.split())
    result["contact"] = contact
    
    return result


async def show_booking_confirmation(chat_id: int, user_info: dict = None):
    """Показывает итоговое подтверждение бронирования."""
    state = get_booking_state(chat_id)
    
    date_str = state.get("date")
    user_time = state.get("time")  # Время в поясе риэлтора
    user_tz = state.get("user_tz", "altai")
    contact = state.get("contact", "")
    phone = state.get("realtor_phone", "")
    
    # Fallback на данные из Telegram
    username = user_info.get("username", "") if user_info else ""
    if not contact and user_info:
        first = user_info.get("first_name", "")
        last = user_info.get("last_name", "")
        contact = f"{first} {last}".strip()
    
    # Сохраняем username
    set_booking_state(chat_id, username=username)
    
    date_display = format_date_display(date_str)
    
    # Формируем строку времени — сначала пояс риэлтора
    if user_tz == "moscow":
        other_time = convert_time(user_time, "moscow", "altai")
        time_str = f"{user_time} (Мск) — {other_time} (Алтай)"
    else:
        other_time = convert_time(user_time, "altai", "moscow")
        time_str = f"{user_time} (Алтай) — {other_time} (Мск)"
    
    text = f"✅ <b>Проверьте заявку:</b>\n\n"
    text += f"📅 {date_display}\n"
    text += f"🕐 {time_str}\n\n"
    
    if contact:
        text += f"👤 {contact}\n"
    if phone:
        text += f"📱 {phone}\n"
    if username:
        text += f"💬 @{username}\n"
    
    buttons = [
        [{"text": "✅ Отправить заявку", "callback_data": "book_submit"}],
        [{"text": "✏️ Изменить", "callback_data": "online_show"}],
        [{"text": "❌ Отмена", "callback_data": "back_to_menu"}]
    ]
    
    # Если нет телефона — предлагаем добавить
    if not phone:
        buttons.insert(1, [{"text": "📱 Добавить телефон", "callback_data": "book_add_phone"}])
    
    await send_message_inline(chat_id, text, buttons)


async def handle_time_confirmed(chat_id: int, user_info: dict = None):
    """Время подтверждено — запрашиваем описание показа."""
    state = get_booking_state(chat_id)
    
    if not state.get("time"):
        await handle_booking_start(chat_id)
        return
    
    set_booking_state(chat_id, step="awaiting_description")
    
    await send_message_inline(
        chat_id,
        "📝 <b>Что показываем клиенту?</b>\n\n"
        "Напишите кратко:\n"
        "• Корпус, тип апартамента\n"
        "• Бюджет клиента\n"
        "• Особые пожелания",
        [[{"text": "◀️ Назад", "callback_data": f"book_date_{state.get('date')}"}]]
    )


async def handle_change_timezone(chat_id: int):
    """Смена часового пояса."""
    state = get_booking_state(chat_id)
    profile = get_profile(chat_id)
    current_tz = profile.get("timezone", "altai") if profile else "altai"
    
    altai_mark = "✅ " if current_tz == "altai" else ""
    moscow_mark = "✅ " if current_tz == "moscow" else ""
    
    await send_message_inline(
        chat_id,
        "🌍 <b>Выберите ваш часовой пояс:</b>\n\n"
        "Это нужно для корректного отображения времени показа.",
        [
            [{"text": f"{altai_mark}🏔 Алтай / Сибирь (UTC+7)", "callback_data": "book_set_tz_altai"}],
            [{"text": f"{moscow_mark}🌴 Москва / Сочи (UTC+3)", "callback_data": "book_set_tz_moscow"}],
            [{"text": "◀️ Назад", "callback_data": f"book_date_{state.get('date', '')}"}]
        ]
    )


async def handle_set_timezone(chat_id: int, tz: str):
    """Установка часового пояса."""
    if tz not in ("altai", "moscow"):
        tz = "altai"
    
    save_profile(chat_id, timezone=tz)
    
    state = get_booking_state(chat_id)
    date_str = state.get("date")
    
    tz_name = "Алтай (UTC+7)" if tz == "altai" else "Москва (UTC+3)"
    
    await send_message(chat_id, f"✅ Часовой пояс установлен: {tz_name}")
    
    # Возвращаемся к вводу времени
    if date_str:
        await handle_select_date(chat_id, date_str)
    else:
        await handle_booking_start(chat_id)


async def handle_request_phone(chat_id: int):
    """Запрос телефона."""
    set_booking_state(chat_id, step="awaiting_phone")
    
    # Используем ReplyKeyboard с request_contact
    from services.telegram import send_message_keyboard
    
    await send_message_keyboard(
        chat_id,
        "📱 <b>Отправьте ваш контакт</b>\n\n"
        "Нажмите кнопку ниже или напишите номер вручную:",
        [[{"text": "📲 Отправить контакт", "request_contact": True}]],
        one_time=True
    )


async def handle_submit_booking(chat_id: int, from_user: dict = None):
    """Отправка заявки."""
    state = get_booking_state(chat_id)
    
    date_str = state.get("date")
    user_time = state.get("time")  # Время в поясе риэлтора
    user_tz = state.get("user_tz", "altai")
    contact = state.get("contact", "")
    phone = state.get("realtor_phone", "")
    username = state.get("username", "")
    
    if not date_str or not user_time:
        await handle_booking_start(chat_id)
        return
    
    # Конвертируем в время Алтая для хранения (единый стандарт)
    if user_tz == "moscow":
        altai_time = convert_time(user_time, "moscow", "altai")
    else:
        altai_time = user_time
    
    # Сохраняем в БД (всегда в Алтайском времени)
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings (
            chat_id, username, specialist_id, specialist_name,
            booking_date, booking_time, status,
            realtor_name, realtor_phone, show_description, timezone
        ) VALUES (?, ?, 0, '', ?, ?, 'pending', ?, ?, '', ?)
    """, (chat_id, username, date_str, altai_time, contact, phone, user_tz))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    date_display = format_date_display(date_str)
    
    # Формируем строку времени — сначала пояс риэлтора
    if user_tz == "moscow":
        other_time = convert_time(user_time, "moscow", "altai")
        time_str = f"{user_time} (Мск) — {other_time} (Алтай)"
    else:
        other_time = convert_time(user_time, "altai", "moscow")
        time_str = f"{user_time} (Алтай) — {other_time} (Мск)"
    
    # Очищаем состояние
    clear_booking_state(chat_id)
    
    # Уведомление риэлтору
    await send_message_inline(
        chat_id,
        f"✅ <b>Заявка #{booking_id} отправлена!</b>\n\n"
        f"📅 {date_display}\n"
        f"🕐 {time_str}\n\n"
        "Ожидайте подтверждения от специалиста.",
        [[{"text": "🔙 В главное меню", "callback_data": "back_to_menu"}]]
    )
    
    # Отправляем в группу показов
    try:
        from config.settings import SHOWS_GROUP_ID
        from services.telegram import send_message_inline_return_id
        
        group_text = f"🆕 <b>Новая заявка на онлайн-показ</b>\n\n"
        group_text += f"📅 {date_display}\n"
        group_text += f"🕐 {time_str}\n\n"
        
        if contact:
            group_text += f"👤 {contact}\n"
        if phone:
            group_text += f"📱 {phone}\n"
        if username:
            group_text += f"💬 @{username}\n"
        
        group_text += f"\n🆔 Заявка: #{booking_id}"
        
        group_buttons = [[{"text": "🙋 Взять заявку", "callback_data": f"book_take_{booking_id}"}]]
        
        if SHOWS_GROUP_ID:
            msg_id = await send_message_inline_return_id(SHOWS_GROUP_ID, group_text, group_buttons)
            if msg_id:
                save_booking_group_message_id(booking_id, msg_id)
    except Exception as e:
        print(f"[BOOKING] Group notify error: {e}")


async def handle_edit_menu(chat_id: int):
    """Меню редактирования заявки."""
    state = get_booking_state(chat_id)
    
    await send_message_inline(
        chat_id,
        "✏️ <b>Что изменить?</b>",
        [
            [{"text": "📅 Дата", "callback_data": "online_show"}],
            [{"text": "🕐 Время", "callback_data": f"book_date_{state.get('date', '')}"}],
            [{"text": "📝 Описание", "callback_data": "book_time_confirmed"}],
            [{"text": "◀️ Назад", "callback_data": "book_back_to_confirm"}]
        ]
    )
