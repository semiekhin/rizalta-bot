"""
Уведомления менеджерам: Telegram + Email.
"""

import os
import asyncio
from typing import Optional, List

from config.settings import (
    MANAGER_EMAIL,
    BOT_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    get_manager_ids,
)
from services.telegram import send_message
from services.calculations import fmt_rub


async def notify_managers_telegram(
    message: str,
    manager_ids: Optional[List[int]] = None,
) -> int:
    """
    Отправляет уведомление менеджерам в Telegram.
    
    Returns:
        Количество успешных отправок
    """
    if manager_ids is None:
        manager_ids = get_manager_ids()
    
    if not manager_ids:
        print("[NOTIFY] No manager IDs configured")
        return 0
    
    success_count = 0
    for manager_id in manager_ids:
        try:
            result = await send_message(manager_id, message)
            if result:
                print(f"[NOTIFY] ✅ Sent to manager {manager_id}")
                success_count += 1
        except Exception as e:
            print(f"[NOTIFY] ❌ Error sending to {manager_id}: {e}")
    
    return success_count


async def notify_managers_email(subject: str, body: str) -> bool:
    """
    Отправляет email уведомление.
    Поддерживает несколько адресов через запятую.
    
    Returns:
        True если хотя бы одна отправка успешна
    """
    if not SMTP_USER or not SMTP_PASSWORD or not MANAGER_EMAIL:
        print(f"[EMAIL] SMTP not configured, email not sent: {subject}")
        return False
    
    # Разбиваем адреса
    email_list = [email.strip() for email in MANAGER_EMAIL.split(",") if email.strip()]
    
    if not email_list:
        print(f"[EMAIL] No valid email addresses found")
        return False
    
    print(f"[EMAIL] Sending to {len(email_list)} recipient(s)")
    
    success_count = 0
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        def _send_to_one(email_to: str) -> bool:
            """Отправляет письмо одному получателю."""
            msg = MIMEMultipart()
            msg['From'] = BOT_EMAIL
            msg['To'] = email_to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            return True
        
        loop = asyncio.get_event_loop()
        
        for email_to in email_list:
            try:
                await loop.run_in_executor(None, _send_to_one, email_to)
                print(f"[EMAIL] ✅ Sent to {email_to}")
                success_count += 1
            except Exception as e:
                print(f"[EMAIL] ❌ Error sending to {email_to}: {e}")
        
        if success_count > 0:
            print(f"[EMAIL] 📊 Summary: {success_count}/{len(email_list)} emails sent")
            return True
        else:
            print(f"[EMAIL] ❌ All {len(email_list)} emails failed")
            return False
    
    except Exception as e:
        print(f"[EMAIL] ❌ Fatal error: {e}")
        return False


async def send_booking_notification(
    chat_id: int,
    name: Optional[str] = None,
    contact: Optional[str] = None,
    budget: Optional[int] = None,
    pay_format: Optional[str] = None,
    time_pref: Optional[str] = None,
) -> None:
    """
    Отправляет уведомление о новой заявке на онлайн-показ.
    """
    # Формируем сообщение для Telegram
    tg_lines = []
    tg_lines.append("🆕 <b>Новая заявка на онлайн-показ RIZALTA</b>\n")
    tg_lines.append(f"👤 Chat ID: {chat_id}")
    
    if name:
        tg_lines.append(f"📝 Имя: {name}")
    if contact:
        tg_lines.append(f"📞 Контакт: {contact}")
    if budget:
        tg_lines.append(f"💰 Бюджет: {fmt_rub(budget)}")
    if pay_format:
        tg_lines.append(f"💳 Формат: {pay_format}")
    if time_pref:
        tg_lines.append(f"⏰ Удобное время: {time_pref}")
    
    # Отправляем в Telegram
    await notify_managers_telegram("\n".join(tg_lines))
    
    # Формируем email
    email_lines = []
    email_lines.append("Новая заявка на онлайн-показ RIZALTA Resort Belokurikha")
    email_lines.append("")
    email_lines.append(f"Chat ID: {chat_id}")
    
    if name:
        email_lines.append(f"Имя: {name}")
    if contact:
        email_lines.append(f"Контакт: {contact}")
    if budget:
        email_lines.append(f"Бюджет: {fmt_rub(budget)}")
    if pay_format:
        email_lines.append(f"Формат оплаты: {pay_format}")
    if time_pref:
        email_lines.append(f"Удобное время: {time_pref}")
    
    email_lines.append("")
    email_lines.append(f"Ссылка для связи: https://t.me/user?id={chat_id}")
    email_lines.append("")
    email_lines.append("---")
    email_lines.append("Это автоматическое уведомление от бота RIZALTA")
    
    await notify_managers_email(
        "🔥 Новая заявка на онлайн-показ RIZALTA",
        "\n".join(email_lines)
    )
