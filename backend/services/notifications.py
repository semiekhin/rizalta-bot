"""
Notification service — отправка заявок менеджерам через Telegram и Email.
"""
import os
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
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Email config
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "")
BOT_EMAIL = os.getenv("BOT_EMAIL", "")


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


async def notify_showing_request(
    name: str,
    phone: str,
    lot_code: str = "",
    comment: str = "",
    source: str = "webapp"
) -> dict:
    """
    Отправка заявки на показ менеджерам (Telegram + Email).
    Возвращает статус отправки.
    """
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Формируем сообщение для Telegram
    lot_info = f"\n🏢 <b>Лот:</b> {lot_code}" if lot_code else ""
    comment_info = f"\n💬 <b>Комментарий:</b> {comment}" if comment else ""

    tg_text = (
        f"📋 <b>Новая заявка на показ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"📱 <b>Телефон:</b> {phone}"
        f"{lot_info}"
        f"{comment_info}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🌐 Источник: {source}\n"
        f"🕐 {now}"
    )

    # Формируем email
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

    # Отправляем
    tg_count = await send_telegram_to_managers(tg_text)
    email_ok = send_email(MANAGER_EMAIL, email_subject, email_body)

    result = {
        "telegram_sent": tg_count,
        "telegram_total": len(get_manager_chat_ids()),
        "email_sent": email_ok,
    }

    logger.info(f"[SHOWING] {name} / {phone} / {lot_code} → TG: {tg_count}, Email: {email_ok}")
    return result
