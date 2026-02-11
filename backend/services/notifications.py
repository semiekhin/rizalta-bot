"""
Notification service — отправка заявок менеджерам через Telegram и Email.
Includes inline "Взять" button for the shows group (compatible with bot's booking_calendar).
"""
import os
import json
import sqlite3
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID", "")  # Может быть через запятую: "123,456"
SHOWS_GROUP_ID = os.getenv("SHOWS_GROUP_ID", "")  # Группа «Показы RIZALTA» для кнопки «Взять»
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Email config
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "")
BOT_EMAIL = os.getenv("BOT_EMAIL", "")

# Bot DB for bookings table (write-through for "Взять" button integration)
BOT_DB_PATH = os.getenv("BOT_DB_PATH", "/opt/bot/properties.db")


def get_manager_chat_ids() -> list[int]:
    """Парсит MANAGER_CHAT_ID (может быть через запятую)."""
    if not MANAGER_CHAT_ID:
        return []
    return [int(cid.strip()) for cid in MANAGER_CHAT_ID.split(",") if cid.strip()]


async def send_telegram_message(chat_id: int, text: str) -> bool:
    """Отправка сообщения через Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram notification")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                }
            )
            if resp.status_code == 200 and resp.json().get("ok"):
                return True
            else:
                logger.error(f"Telegram API error: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def send_telegram_with_buttons(chat_id: int, text: str,
                                      inline_keyboard: list) -> int | None:
    """Sends a message with inline keyboard buttons. Returns message_id or None."""
    if not TELEGRAM_BOT_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps({"inline_keyboard": inline_keyboard}),
                }
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("ok"):
                return data["result"]["message_id"]
            else:
                logger.error(f"Telegram inline API error: {resp.text}")
                return None
    except Exception as e:
        logger.error(f"Telegram inline send failed: {e}")
        return None


async def send_telegram_to_managers(text: str) -> int:
    """Отправка сообщения всем менеджерам. Возвращает кол-во успешных."""
    chat_ids = get_manager_chat_ids()
    if not chat_ids:
        logger.warning("No MANAGER_CHAT_ID configured")
        return 0

    success = 0
    for cid in chat_ids:
        if await send_telegram_message(cid, text):
            success += 1
    return success


def send_email(to: str, subject: str, body_html: str) -> bool:
    """Отправка email через SMTP."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, to]):
        logger.warning("Email config incomplete, skipping email notification")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = BOT_EMAIL or SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def _create_booking_record(name: str, phone: str, lot_code: str, comment: str) -> int | None:
    """Creates a booking record in the bot's DB for 'Взять' button integration.
    Returns booking_id or None on failure."""
    try:
        conn = sqlite3.connect(BOT_DB_PATH)
        cursor = conn.cursor()
        # Ensure table exists (same schema as bot)
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
        today = datetime.now().strftime("%Y-%m-%d")
        contact_info = f"{name} | {phone}"
        if lot_code:
            contact_info += f" | Лот: {lot_code}"
        if comment:
            contact_info += f" | {comment}"

        cursor.execute("""
            INSERT INTO bookings (chat_id, username, specialist_id, specialist_name,
                                  booking_date, booking_time, status, contact_info)
            VALUES (0, 'webapp', 0, '', ?, 'TBD', 'pending', ?)
        """, (today, contact_info))
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return booking_id
    except Exception as e:
        logger.error(f"[BOOKING] DB error: {e}")
        return None


def _save_group_message_id(booking_id: int, message_id: int):
    """Saves group message ID for the booking (so bot can edit it on 'Взять')."""
    try:
        conn = sqlite3.connect(BOT_DB_PATH)
        conn.execute(
            "UPDATE bookings SET group_message_id = ? WHERE id = ?",
            (message_id, booking_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[BOOKING] Save msg_id error: {e}")


async def notify_showing_request(
    name: str,
    phone: str,
    lot_code: str = "",
    comment: str = "",
    source: str = "webapp"
) -> dict:
    """
    Отправка заявки на показ:
    1. В группу «Показы» с кнопкой «Взять» (для интеграции с ботом)
    2. Менеджерам (plain text)
    3. Email
    """
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # --- 1. Создаём запись в БД и отправляем в группу показов с кнопкой ---
    group_sent = False
    booking_id = None

    if SHOWS_GROUP_ID:
        booking_id = _create_booking_record(name, phone, lot_code, comment)

        lot_info = f"\n🏢 Лот: {lot_code}" if lot_code else ""
        comment_info = f"\n💬 {comment}" if comment else ""

        group_text = (
            f"🆕 <b>Новая заявка на онлайн-показ</b>\n\n"
            f"👤 {name}\n"
            f"📱 {phone}"
            f"{lot_info}"
            f"{comment_info}\n\n"
            f"🌐 Источник: {source}\n"
            f"🕐 {now}"
        )

        if booking_id:
            group_text += f"\n🆔 Заявка: #{booking_id}"
            buttons = [[{"text": "🙋 Взять заявку", "callback_data": f"book_take_{booking_id}"}]]
        else:
            buttons = []

        try:
            group_chat_id = int(SHOWS_GROUP_ID)
            if buttons:
                msg_id = await send_telegram_with_buttons(group_chat_id, group_text, buttons)
                if msg_id and booking_id:
                    _save_group_message_id(booking_id, msg_id)
                group_sent = msg_id is not None
            else:
                group_sent = await send_telegram_message(group_chat_id, group_text)
        except Exception as e:
            logger.error(f"[SHOWING] Group notify error: {e}")

    # --- 2. Отправляем менеджерам (plain text), исключая группу показов ---
    lot_info_html = f"\n🏢 <b>Лот:</b> {lot_code}" if lot_code else ""
    comment_info_html = f"\n💬 <b>Комментарий:</b> {comment}" if comment else ""

    tg_text = (
        f"📋 <b>Новая заявка на показ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"📱 <b>Телефон:</b> {phone}"
        f"{lot_info_html}"
        f"{comment_info_html}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🌐 Источник: {source}\n"
        f"🕐 {now}"
    )

    # Exclude SHOWS_GROUP_ID from manager list to avoid duplicate messages
    shows_id = int(SHOWS_GROUP_ID) if SHOWS_GROUP_ID else None
    manager_ids = [cid for cid in get_manager_chat_ids() if cid != shows_id]
    tg_count = 0
    for cid in manager_ids:
        if await send_telegram_message(cid, tg_text):
            tg_count += 1

    # --- 3. Email ---
    email_subject = f"RIZALTA — Заявка на показ от {name}"
    email_body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #263524;">📋 Новая заявка на показ</h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><b>👤 Имя</b></td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{name}</td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><b>📱 Телефон</b></td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{phone}</td></tr>
        {"<tr><td style='padding: 8px; border-bottom: 1px solid #eee;'><b>🏢 Лот</b></td><td style='padding: 8px; border-bottom: 1px solid #eee;'>" + lot_code + "</td></tr>" if lot_code else ""}
        {"<tr><td style='padding: 8px; border-bottom: 1px solid #eee;'><b>💬 Комментарий</b></td><td style='padding: 8px; border-bottom: 1px solid #eee;'>" + comment + "</td></tr>" if comment else ""}
    </table>
    <p style="color: #888; font-size: 12px; margin-top: 20px;">
        Источник: {source} | {now}
    </p>
    </body></html>
    """

    email_ok = send_email(MANAGER_EMAIL, email_subject, email_body)

    result = {
        "telegram_sent": tg_count,
        "telegram_total": len(get_manager_chat_ids()),
        "group_sent": group_sent,
        "booking_id": booking_id,
        "email_sent": email_ok,
    }

    logger.info(f"[SHOWING] {name} / {phone} / {lot_code} → TG: {tg_count}, Group: {group_sent}, Email: {email_ok}")
    return result
