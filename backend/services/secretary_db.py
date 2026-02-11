"""Secretary DB — SQLite CRUD for tasks and schedule."""

import sqlite3
import os
from datetime import datetime, timedelta

SECRETARY_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "secretary.db")


def get_conn():
    conn = sqlite3.connect(SECRETARY_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_secretary_db():
    """Create tables on startup."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'webapp',
            task TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            client_name TEXT,
            priority TEXT DEFAULT 'normal',
            done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_date ON tasks(user_id, date)
    """)
    conn.commit()
    conn.close()
    print(f"[SECRETARY] DB initialized: {SECRETARY_DB}")


def _row_to_dict(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "task": row["task"],
        "date": row["date"],
        "time": row["time"],
        "client_name": row["client_name"],
        "priority": row["priority"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
    }


def add_task(task: str, date: str, time: str = None, client_name: str = None,
             priority: str = "normal", user_id: str = "webapp") -> dict:
    """Add a new task. Returns the created task."""
    conn = get_conn()
    cursor = conn.execute(
        "INSERT INTO tasks (user_id, task, date, time, client_name, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, task, date, time, client_name, priority)
    )
    task_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_tasks_for_date(date: str, user_id: str = "webapp") -> list[dict]:
    """Get all tasks for a specific date, ordered by time then id."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND date = ? ORDER BY time IS NULL, time, id",
        (user_id, date)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_tasks_for_week(start_date: str, user_id: str = "webapp") -> dict[str, list[dict]]:
    """Get tasks for 7 days starting from start_date."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = start + timedelta(days=6)
    end_str = end.strftime("%Y-%m-%d")

    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND date >= ? AND date <= ? ORDER BY date, time IS NULL, time, id",
        (user_id, start_date, end_str)
    ).fetchall()
    conn.close()

    result = {}
    for i in range(7):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        result[day] = []
    for r in rows:
        d = r["date"]
        if d in result:
            result[d].append(_row_to_dict(r))
    return result


def mark_done(task_id: int, user_id: str = "webapp") -> bool:
    """Mark task as done."""
    conn = get_conn()
    cursor = conn.execute(
        "UPDATE tasks SET done = 1, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def mark_undone(task_id: int, user_id: str = "webapp") -> bool:
    """Mark task as not done."""
    conn = get_conn()
    cursor = conn.execute(
        "UPDATE tasks SET done = 0, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def move_task(task_id: int, new_date: str, user_id: str = "webapp") -> bool:
    """Move task to a different date."""
    conn = get_conn()
    cursor = conn.execute(
        "UPDATE tasks SET date = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
        (new_date, task_id, user_id)
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def delete_task(task_id: int, user_id: str = "webapp") -> bool:
    """Delete a task."""
    conn = get_conn()
    cursor = conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
