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
    "Васильченко Евгения",
    "Товт Александра",
]

AGENCIES = [
    "Арт-инвест",
    "Атлас",
    "Гордон А.",
    "Града",
    "ДМ групп",
    "ДомРил",
    "ЗАЙРЕКС",
    "Интегрити",
    "Интегрити 2",
    "Кипарис",
    "КосмосРиалти",
    "Лехто Групп",
    "Лето Недвижимость",
    "Мегаполис",
    "НВС Групп",
    "НикаЭстейт",
    "Оазис",
    "Остров",
    "ПроСторе Сочи",
    "Семья Мосейкиных",
    "Сириус Групп",
    "Сочи ЮДВ",
    "Финвилас",
    "Элитный Сочи",
    "ЭСТАДЕЛЬ",
    "Ю-ХАУС",
]

VALID_STATUS = {"planned", "completed", "completed_booked", "rescheduled", "cancelled"}


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
            realtor_agency TEXT,
            realtor_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planned',
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
        "realtor_agency": row["realtor_agency"],
        "realtor_name": row["realtor_name"],
        "status": row["status"],
        "comment": row["comment"],
    }


def get_managers() -> list[str]:
    return list(MANAGERS)


def get_agencies() -> list[str]:
    return list(AGENCIES)


def create_show(
    show_datetime: str,
    manager: str,
    realtor_name: str,
    realtor_agency: Optional[str] = None,
    comment: Optional[str] = None,
) -> dict:
    if manager not in MANAGERS:
        raise ValueError(f"Unknown manager: {manager}")
    conn = get_conn()
    cursor = conn.execute(
        """INSERT INTO shows
           (show_datetime, manager, realtor_agency, realtor_name, status, comment)
           VALUES (?, ?, ?, ?, 'planned', ?)""",
        (show_datetime, manager, realtor_agency, realtor_name, comment),
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
    "show_datetime", "manager", "realtor_agency", "realtor_name", "status", "comment",
}


def update_show(show_id: int, fields: dict) -> Optional[dict]:
    clean: dict = {}
    for k, v in fields.items():
        if k in _ALLOWED_FIELDS and v is not None:
            clean[k] = v
    if "status" in clean and clean["status"] not in VALID_STATUS:
        raise ValueError(f"Invalid status: {clean['status']}")
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


def get_stats_by_manager(date_from: Optional[str] = None,
                         date_to: Optional[str] = None) -> list[dict]:
    """Aggregate counts per manager. Always returns a row per known manager
    (zero-filled if no shows in period). booking_rate is None when there are
    no conducted shows (completed + completed_booked == 0)."""
    conditions = []
    params: list = []
    if date_from:
        conditions.append("show_datetime >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("show_datetime <= ?")
        params.append(date_to)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT
            manager,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'planned' THEN 1 ELSE 0 END) AS planned,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status = 'completed_booked' THEN 1 ELSE 0 END) AS completed_booked,
            SUM(CASE WHEN status = 'rescheduled' THEN 1 ELSE 0 END) AS rescheduled,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
        FROM shows
        {where}
        GROUP BY manager
    """
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    by_name = {r["manager"]: r for r in rows}
    result = []
    for name in MANAGERS:
        r = by_name.get(name)
        total = r["total"] if r else 0
        planned = r["planned"] if r else 0
        completed = r["completed"] if r else 0
        completed_booked = r["completed_booked"] if r else 0
        rescheduled = r["rescheduled"] if r else 0
        cancelled = r["cancelled"] if r else 0
        conducted = completed + completed_booked
        booking_rate = round(100 * completed_booked / conducted, 1) if conducted > 0 else None
        result.append({
            "manager": name,
            "name": name,
            "total": total,
            "planned": planned,
            "completed": completed,
            "completed_booked": completed_booked,
            "rescheduled": rescheduled,
            "cancelled": cancelled,
            "booking_rate": booking_rate,
        })
    return result


def get_stats_by_agency(date_from: Optional[str] = None,
                        date_to: Optional[str] = None) -> list[dict]:
    """Aggregate counts per agency. Unlike get_stats_by_manager there is no
    zero-fill — only agencies with shows in the period are returned. NULL or
    empty realtor_agency is bucketed into a synthetic 'Без агентства' row."""
    conditions = []
    params: list = []
    if date_from:
        conditions.append("show_datetime >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("show_datetime <= ?")
        params.append(date_to)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT
            COALESCE(NULLIF(realtor_agency, ''), 'Без агентства') AS name,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'planned' THEN 1 ELSE 0 END) AS planned,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status = 'completed_booked' THEN 1 ELSE 0 END) AS completed_booked,
            SUM(CASE WHEN status = 'rescheduled' THEN 1 ELSE 0 END) AS rescheduled,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
        FROM shows
        {where}
        GROUP BY COALESCE(NULLIF(realtor_agency, ''), 'Без агентства')
    """
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    result = []
    for r in rows:
        completed = r["completed"]
        completed_booked = r["completed_booked"]
        conducted = completed + completed_booked
        booking_rate = round(100 * completed_booked / conducted, 1) if conducted > 0 else None
        result.append({
            "name": r["name"],
            "total": r["total"],
            "planned": r["planned"],
            "completed": completed,
            "completed_booked": completed_booked,
            "rescheduled": r["rescheduled"],
            "cancelled": r["cancelled"],
            "booking_rate": booking_rate,
        })

    # Sort: lowest booking_rate first (problem agencies on top).
    # None (no completed shows) goes to the end.
    result.sort(key=lambda r: (r["booking_rate"] is None, r["booking_rate"] or 0))
    return result
