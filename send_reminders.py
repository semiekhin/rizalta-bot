#!/usr/bin/env python3
"""Отправка напоминаний за 15 минут до события."""

import asyncio
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

BOT_TOKEN = "8343378629:AAE4OlxArGXPpju0oEzk19Wmp4ofummP788"
DB_PATH = Path("/opt/bot/secretary.db")

# Алтай = MSK + 4
ALTAI_OFFSET = 4


def get_pending_reminders():
    """Получает задачи, для которых пора отправить напоминание."""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Текущее время по Алтаю
    now_msk = datetime.now()
    now_altai = now_msk + timedelta(hours=ALTAI_OFFSET)
    
    # Время через 15 минут
    remind_time = now_altai + timedelta(minutes=15)
    
    today = now_altai.strftime("%Y-%m-%d")
    current_time = now_altai.strftime("%H:%M")
    remind_time_str = remind_time.strftime("%H:%M")
    
    # Ищем задачи на сегодня, которые начнутся в ближайшие 15 минут
    cursor.execute("""
        SELECT id, user_id, task_text, due_date, due_time, client_name
        FROM tasks 
        WHERE status = 'pending' 
        AND reminder_sent = 0
        AND due_date = ?
        AND due_time IS NOT NULL
        AND due_time <= ?
        AND due_time > ?
    """, (today, remind_time_str, current_time))
    
    tasks = cursor.fetchall()
    conn.close()
    
    return tasks


def mark_reminder_sent(task_id: int):
    """Отмечает что напоминание отправлено."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET reminder_sent = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


async def send_reminder(user_id: int, task_text: str, due_time: str, client_name: str = None):
    """Отправляет напоминание со звуком."""
    
    client_info = f"\n👤 Клиент: {client_name}" if client_name else ""
    
    message = f"""⏰ <b>Напоминание!</b>

📋 {task_text}{client_info}
🕐 Через 15 минут ({due_time})"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_notification": False  # Со звуком!
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            status = "✅" if result.get("ok") else "❌"
            print(f"{status} User {user_id}: {task_text}")
            return result.get("ok", False)


async def main():
    tasks = get_pending_reminders()
    
    if not tasks:
        return
    
    print(f"[{datetime.now()}] Найдено задач для напоминания: {len(tasks)}")
    
    for task in tasks:
        task_id, user_id, task_text, due_date, due_time, client_name = task
        
        success = await send_reminder(user_id, task_text, due_time, client_name)
        
        if success:
            mark_reminder_sent(task_id)
        
        await asyncio.sleep(0.3)


if __name__ == "__main__":
    asyncio.run(main())
