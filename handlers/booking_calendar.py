"""
Календарь бронирования на онлайн-показ.
Выбор специалиста → дата → время → подтверждение.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from services.telegram import send_message, send_message_inline

# Путь к базе данных
BOT_DB_PATH = "/opt/bot/properties.db"

# === НАСТРОЙКИ ===

# Специалисты (потом заменим на реальные данные)
SPECIALISTS = [
    {"id": 1, "name": "Специалист 1", "telegram_id": 512319063, "email": "89181011091s@mail.ru"},
    {"id": 2, "name": "Специалист 2", "telegram_id": 512319063, "email": "89181011091s@mail.ru"},
    {"id": 3, "name": "Специалист 3", "telegram_id": 512319063, "email": "89181011091s@mail.ru"},
]

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
            contact_info TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_booked_slots(specialist_id: int, date_str: str) -> List[str]:
    """Возвращает список забронированных слотов для специалиста на дату."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT booking_time FROM bookings 
        WHERE specialist_id = ? AND booking_date = ? AND status = 'confirmed'
    """, (specialist_id, date_str))
    slots = [row[0] for row in cursor.fetchall()]
    conn.close()
    return slots


def save_booking(chat_id: int, username: str, specialist_id: int, 
                 specialist_name: str, date_str: str, time_str: str,
                 contact_info: str = None) -> int:
    """Сохраняет бронирование в БД. Возвращает ID записи."""
    conn = sqlite3.connect(BOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings (chat_id, username, specialist_id, specialist_name, 
                              booking_date, booking_time, contact_info)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (chat_id, username, specialist_id, specialist_name, date_str, time_str, contact_info))
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


def get_available_times(specialist_id: int, date_str: str) -> List[str]:
    """Возвращает список свободных слотов для специалиста на дату."""
    booked = get_booked_slots(specialist_id, date_str)
    
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

# chat_id -> {"specialist_id": ..., "specialist_name": ..., "date": ...}
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
    """Начало бронирования — выбор специалиста."""
    init_bookings_db()
    clear_booking_state(chat_id)
    
    buttons = []
    for spec in SPECIALISTS:
        buttons.append([{
            "text": f"👤 {spec['name']}", 
            "callback_data": f"book_spec_{spec['id']}"
        }])
    
    buttons.append([{"text": "🔙 В меню", "callback_data": "back_to_menu"}])
    
    await send_message_inline(
        chat_id,
        "📅 <b>Запись на онлайн-показ</b>\n\n"
        "Выберите специалиста:",
        buttons
    )


async def handle_select_specialist(chat_id: int, specialist_id: int):
    """Выбран специалист — показываем даты."""
    specialist = next((s for s in SPECIALISTS if s["id"] == specialist_id), None)
    if not specialist:
        await send_message(chat_id, "Ошибка: специалист не найден")
        return
    
    set_booking_state(chat_id, specialist_id=specialist_id, specialist_name=specialist["name"])
    
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
    
    buttons.append([
        {"text": "◀️ Назад", "callback_data": "book_back_specialist"},
        {"text": "🔙 В меню", "callback_data": "back_to_menu"}
    ])
    
    await send_message_inline(
        chat_id,
        f"👤 <b>{specialist['name']}</b>\n\n"
        "Выберите дату:",
        buttons
    )


async def handle_select_date(chat_id: int, date_str: str):
    """Выбрана дата — показываем время."""
    state = get_booking_state(chat_id)
    specialist_id = state.get("specialist_id")
    specialist_name = state.get("specialist_name")
    
    if not specialist_id:
        await handle_booking_start(chat_id)
        return
    
    set_booking_state(chat_id, date=date_str)
    
    times = get_available_times(specialist_id, date_str)
    if not times:
        await send_message_inline(
            chat_id,
            f"😔 К сожалению, на {format_date_display(date_str)} нет свободных слотов.\n\n"
            "Выберите другую дату.",
            [[{"text": "◀️ Выбрать другую дату", "callback_data": f"book_spec_{specialist_id}"}]]
        )
        return
    
    # Группируем по 3 кнопки в ряд
    buttons = []
    row = []
    for t in times:
        row.append({
            "text": f"🕐 {t}",
            "callback_data": f"book_time_{t.replace(':', '')}"
        })
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([
        {"text": "◀️ Назад", "callback_data": f"book_spec_{specialist_id}"},
        {"text": "🔙 В меню", "callback_data": "back_to_menu"}
    ])
    
    date_display = format_date_display(date_str)
    
    await send_message_inline(
        chat_id,
        f"👤 <b>{specialist_name}</b>\n"
        f"📅 <b>{date_display}</b>\n\n"
        "Выберите время:",
        buttons
    )


async def handle_select_time(chat_id: int, time_str: str, username: str = None):
    """Выбрано время — отправляем заявку специалисту на подтверждение."""
    state = get_booking_state(chat_id)
    specialist_id = state.get("specialist_id")
    specialist_name = state.get("specialist_name")
    date_str = state.get("date")
    
    if not specialist_id or not date_str:
        await handle_booking_start(chat_id)
        return
    
    # Форматируем время обратно (1000 -> 10:00)
    time_formatted = f"{time_str[:2]}:{time_str[2:]}"
    
    # Сохраняем в БД со статусом pending
    booking_id = save_booking(
        chat_id=chat_id,
        username=username,
        specialist_id=specialist_id,
        specialist_name=specialist_name,
        date_str=date_str,
        time_str=time_formatted
    )
    
    date_display = format_date_display(date_str)
    
    # Отправляем риэлтору сообщение об ожидании
    clear_booking_state(chat_id)
    
    await send_message_inline(
        chat_id,
        f"⏳ <b>Заявка отправлена!</b>\n\n"
        f"👤 Специалист: {specialist_name}\n"
        f"📅 Дата: {date_display}\n"
        f"🕐 Время: {time_formatted}\n"
        f"🆔 Номер заявки: #{booking_id}\n\n"
        "Ожидайте подтверждения от специалиста.\n"
        "Вы получите уведомление.",
        [[{"text": "🔙 В главное меню", "callback_data": "back_to_menu"}]]
    )
    
    # Отправляем специалисту уведомление с кнопками
    specialist = next((s for s in SPECIALISTS if s["id"] == specialist_id), None)
    if specialist and specialist.get("telegram_id"):
        await send_message_inline(
            specialist["telegram_id"],
            f"📅 <b>Новая заявка на показ!</b>\n\n"
            f"🆔 Номер: #{booking_id}\n"
            f"📅 Дата: {date_display}\n"
            f"🕐 Время: {time_formatted}\n"
            f"👤 Риэлтор: @{username if username else 'не указан'}\n\n"
            "Подтвердить запись?",
            [
                [
                    {"text": "✅ Подтвердить", "callback_data": f"book_confirm_{booking_id}"},
                    {"text": "❌ Отклонить", "callback_data": f"book_decline_{booking_id}"}
                ]
            ]
        )
    
    # Отправляем в группу показов
    try:
        from services.notifications import notify_shows_group
        group_msg = (
            f"🆕 <b>Новая запись на онлайн-показ</b>\n\n"
            f"👤 Специалист: {specialist_name}\n"
            f"📅 Дата: {date_display}\n"
            f"🕐 Время: {time_formatted}\n"
            f"🆔 Бронь: #{booking_id}\n"
            f"📱 Клиент: @{username if username else chat_id}"
        )
        await notify_shows_group(group_msg)
    except Exception as e:
        print(f"[BOOKING] Group notify error: {e}")

    # Также отправляем email
    if specialist and specialist.get("email"):
        try:
            await send_booking_notification_email(
                to_email=specialist["email"],
                specialist_name=specialist_name,
                date_display=date_display,
                time_str=time_formatted,
                username=username,
                chat_id=chat_id,
                booking_id=booking_id
            )
        except Exception as e:
            print(f"[BOOKING] Email error: {e}")


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


async def handle_confirm_booking(chat_id: int, booking_id: int):
    """Специалист подтвердил запись."""
    booking = get_booking_by_id(booking_id)
    
    if not booking:
        await send_message(chat_id, "❌ Запись не найдена.")
        return
    
    if booking["status"] != "pending":
        await send_message(chat_id, "ℹ️ Эта запись уже обработана.")
        return
    
    # Обновляем статус
    update_booking_status(booking_id, "confirmed")
    
    date_display = format_date_display(booking["booking_date"])
    
    # Уведомляем специалиста
    await send_message(
        chat_id,
        f"✅ <b>Запись подтверждена!</b>\n\n"
        f"🆔 Номер: #{booking_id}\n"
        f"📅 {date_display}, {booking['booking_time']}\n"
        f"👤 Риэлтор: @{booking['username'] or 'не указан'}"
    )
    
    # Уведомляем риэлтора
    await send_message_inline(
        booking["chat_id"],
        f"✅ <b>Ваша запись подтверждена!</b>\n\n"
        f"👤 Специалист: {booking['specialist_name']}\n"
        f"📅 Дата: {date_display}\n"
        f"🕐 Время: {booking['booking_time']}\n"
        f"🆔 Номер записи: #{booking_id}\n\n"
        "Специалист свяжется с вами в назначенное время.",
        [[{"text": "🔙 В главное меню", "callback_data": "back_to_menu"}]]
    )


async def handle_decline_booking(chat_id: int, booking_id: int):
    """Специалист отклонил запись."""
    booking = get_booking_by_id(booking_id)
    
    if not booking:
        await send_message(chat_id, "❌ Запись не найдена.")
        return
    
    if booking["status"] != "pending":
        await send_message(chat_id, "ℹ️ Эта запись уже обработана.")
        return
    
    # Обновляем статус
    update_booking_status(booking_id, "declined")
    
    date_display = format_date_display(booking["booking_date"])
    
    # Уведомляем специалиста
    await send_message(
        chat_id,
        f"❌ <b>Запись отклонена</b>\n\n"
        f"🆔 Номер: #{booking_id}\n"
        f"📅 {date_display}, {booking['booking_time']}"
    )
    
    # Уведомляем риэлтора
    await send_message_inline(
        booking["chat_id"],
        f"😔 <b>К сожалению, выбранное время недоступно</b>\n\n"
        f"👤 Специалист: {booking['specialist_name']}\n"
        f"📅 Дата: {date_display}\n"
        f"🕐 Время: {booking['booking_time']}\n\n"
        "Пожалуйста, выберите другое время.",
        [[{"text": "📅 Выбрать другое время", "callback_data": "booking_calendar"}],
         [{"text": "🔙 В главное меню", "callback_data": "back_to_menu"}]]
    )


async def send_booking_notification_email(to_email: str, specialist_name: str,
                                          date_display: str, time_str: str,
                                          username: str, chat_id: int, booking_id: int):
    """Отправляет email уведомление о новой записи."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, BOT_EMAIL
    
    subject = f"🗓 Новая запись на показ #{booking_id}"
    
    body = f"""
Новая запись на онлайн-показ RIZALTA!

📋 Детали записи:
━━━━━━━━━━━━━━━━━━━━━
🆔 Номер: #{booking_id}
👤 Специалист: {specialist_name}
📅 Дата: {date_display}
🕐 Время: {time_str}

👤 Клиент:
• Telegram: @{username if username else 'не указан'}
• Chat ID: {chat_id}
━━━━━━━━━━━━━━━━━━━━━

Пожалуйста, свяжитесь с клиентом в назначенное время.
"""
    
    msg = MIMEMultipart()
    msg["From"] = BOT_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    
    print(f"[BOOKING] Email sent to {to_email}")
