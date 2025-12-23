"""
База данных для AI-секретаря.
Хранение задач, напоминаний.
Версия 2.0 — без режима секретаря
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "secretary.db"


# DEPRECATED: Режим секретаря больше не используется
# GPT-роутинг обрабатывает все сообщения централизованно
def is_secretary_mode(user_id: int) -> bool:
    """DEPRECATED: Всегда возвращает False."""
    return False


def set_secretary_mode(user_id: int, enabled: bool):
    """DEPRECATED: Ничего не делает."""
    pass


def init_db():
    """Создаёт таблицу задач."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_text TEXT NOT NULL,
            due_date TEXT,
            due_time TEXT,
            client_name TEXT,
            client_phone TEXT,
            priority TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'pending',
            description TEXT,
            reminder_sent INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_task(user_id, task_text, due_date=None, due_time=None, client_name=None,
             client_phone=None, priority="normal", description=None):
    """Добавляет задачу. Возвращает ID."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks
        (user_id, task_text, due_date, due_time, client_name, client_phone,
         priority, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, task_text, due_date, due_time, client_name, client_phone,
          priority, description, datetime.now().isoformat()))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_tasks_for_date(user_id, target_date):
    """Получает задачи на дату (YYYY-MM-DD)."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM tasks
        WHERE user_id = ? AND due_date = ? AND status != 'cancelled'
        ORDER BY CASE WHEN due_time IS NULL THEN 1 ELSE 0 END, due_time
    """, (user_id, target_date))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_tasks_for_week(user_id, start_date):
    """Получает задачи на неделю."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = start + timedelta(days=6)
    cursor.execute("""
        SELECT * FROM tasks
        WHERE user_id = ? AND due_date BETWEEN ? AND ? AND status != 'cancelled'
        ORDER BY due_date, due_time
    """, (user_id, start_date, end.strftime("%Y-%m-%d")))
    rows = cursor.fetchall()
    conn.close()
    week = {}
    for i in range(7):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        week[day] = []
    for row in rows:
        day = row["due_date"]
        if day in week:
            week[day].append(dict(row))
    return week


def get_task_by_id(task_id):
    """Получает задачу по ID."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_task_status(task_id, status):
    """Обновляет статус задачи."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    completed_at = datetime.now().isoformat() if status == "done" else None
    cursor.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                   (status, completed_at, task_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def update_task_date(task_id, new_date, new_time=None):
    """Переносит задачу."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    if new_time:
        cursor.execute("UPDATE tasks SET due_date = ?, due_time = ? WHERE id = ?",
                       (new_date, new_time, task_id))
    else:
        cursor.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (new_date, task_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_task(task_id):
    """Удаляет задачу."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def count_tasks_for_date(user_id, target_date):
    """Считает задачи на дату."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN priority IN ('urgent','high') THEN 1 ELSE 0 END) as urgent,
               SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done
        FROM tasks WHERE user_id = ? AND due_date = ? AND status != 'cancelled'
    """, (user_id, target_date))
    row = cursor.fetchone()
    conn.close()
    return {"total": row[0] or 0, "urgent": row[1] or 0, "done": row[2] or 0}


def get_pending_reminders():
    """Задачи для напоминаний."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_hour = now.strftime("%H")
    cursor.execute("""
        SELECT * FROM tasks
        WHERE due_date = ? AND due_time LIKE ? AND status = 'pending' AND reminder_sent = 0
    """, (today, f"{current_hour}:%"))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_reminder_sent(task_id):
    """Отмечает напоминание отправленным."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET reminder_sent = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


init_db()
