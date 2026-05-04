"""Shows service — CRUD for showings calendar (separate shows.db)."""

import os
import sqlite3
from typing import Optional

SHOWS_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shows.db")

MANAGERS = [
    "Дегтярева Марина",
    "Шумова Дарья",
    "Хватик Светлана",
    "Панченко Инна",
]

VALID_STATUS = {"planned", "rescheduled", "completed", "cancelled", "no_show"}
VALID_RESULT = {"interested", "booked", "not_interested", "contact_saved"}


def get_conn():
    conn = sqlite3.connect(SHOWS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_shows_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            show_datetime TEXT NOT NULL,
            manager TEXT NOT NULL,
            realtor_name TEXT NOT NULL,
            realtor_phone TEXT,
            realtor_agency TEXT,
            client_name TEXT,
            planned_lot TEXT NOT NULL,
            actual_lot TEXT,
            status TEXT NOT NULL DEFAULT 'planned',
            reschedule_to TEXT,
            reschedule_reason TEXT,
            result TEXT,
            comment TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_shows_datetime ON shows(show_datetime)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_shows_manager ON shows(manager)")
    conn.commit()
    conn.close()
    print(f"[SHOWS] DB initialized: {SHOWS_DB}")


def _row_to_dict(row) -> Optional[dict]:
    if row is None:
        return None
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "show_datetime": row["show_datetime"],
        "manager": row["manager"],
        "realtor_name": row["realtor_name"],
        "realtor_phone": row["realtor_phone"],
        "realtor_agency": row["realtor_agency"],
        "client_name": row["client_name"],
        "planned_lot": row["planned_lot"],
        "actual_lot": row["actual_lot"],
        "status": row["status"],
        "reschedule_to": row["reschedule_to"],
        "reschedule_reason": row["reschedule_reason"],
        "result": row["result"],
        "comment": row["comment"],
    }


def get_managers() -> list[str]:
    return list(MANAGERS)


def create_show(
    show_datetime: str,
    manager: str,
    realtor_name: str,
    planned_lot: str,
    realtor_phone: Optional[str] = None,
    realtor_agency: Optional[str] = None,
    client_name: Optional[str] = None,
) -> dict:
    if manager not in MANAGERS:
        raise ValueError(f"Unknown manager: {manager}")
    conn = get_conn()
    cursor = conn.execute(
        """INSERT INTO shows
           (show_datetime, manager, realtor_name, realtor_phone, realtor_agency,
            client_name, planned_lot, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'planned')""",
        (show_datetime, manager, realtor_name, realtor_phone, realtor_agency,
         client_name, planned_lot),
    )
    show_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM shows WHERE id = ?", (show_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def list_shows(
    manager: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    conditions = []
    params: list = []
    if manager:
        conditions.append("manager = ?")
        params.append(manager)
    if date_from:
        conditions.append("show_datetime >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("show_datetime <= ?")
        params.append(date_to)
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM shows {where} ORDER BY show_datetime ASC, id ASC"
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


_ALLOWED_FIELDS = {
    "show_datetime", "manager", "realtor_name", "realtor_phone", "realtor_agency",
    "client_name", "planned_lot", "actual_lot", "status",
    "reschedule_to", "reschedule_reason", "result", "comment",
}


def update_show(show_id: int, fields: dict) -> Optional[dict]:
    clean: dict = {}
    for k, v in fields.items():
        if k in _ALLOWED_FIELDS and v is not None:
            clean[k] = v
    if "status" in clean and clean["status"] not in VALID_STATUS:
        raise ValueError(f"Invalid status: {clean['status']}")
    if "result" in clean and clean["result"] not in VALID_RESULT:
        raise ValueError(f"Invalid result: {clean['result']}")
    if "manager" in clean and clean["manager"] not in MANAGERS:
        raise ValueError(f"Unknown manager: {clean['manager']}")
    if not clean:
        conn = get_conn()
        row = conn.execute("SELECT * FROM shows WHERE id = ?", (show_id,)).fetchone()
        conn.close()
        return _row_to_dict(row)

    set_clause = ", ".join(f"{k} = ?" for k in clean) + ", updated_at = datetime('now')"
    params = list(clean.values()) + [show_id]
    conn = get_conn()
    cursor = conn.execute(f"UPDATE shows SET {set_clause} WHERE id = ?", params)
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return None
    row = conn.execute("SELECT * FROM shows WHERE id = ?", (show_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def delete_show(show_id: int) -> bool:
    conn = get_conn()
    cursor = conn.execute("DELETE FROM shows WHERE id = ?", (show_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
