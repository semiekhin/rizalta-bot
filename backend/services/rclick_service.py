"""RClick service — auth and client fixation via ri.rclick.ru."""

import os
import sqlite3
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

RCLICK_BASE_URL = os.getenv("RCLICK_BASE_URL", "https://ri.rclick.ru")
WEBAPP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp.db")


def init_rclick_table():
    """Create rclick_sessions table in webapp.db."""
    conn = sqlite3.connect(WEBAPP_DB)
    # Drop old table with 'login' column if it exists (schema changed to 'phone')
    conn.execute("DROP TABLE IF EXISTS rclick_sessions")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rclick_sessions (
            session_id TEXT PRIMARY KEY,
            phone TEXT NOT NULL,
            cookies TEXT,
            agent_name TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            last_used TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
    print("[RCLICK] Sessions table initialized")


def _get_session(session_id: str) -> dict | None:
    """Get stored rclick session."""
    conn = sqlite3.connect(WEBAPP_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM rclick_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def _save_session(session_id: str, phone: str, cookies: str, agent_name: str = ""):
    """Save rclick session."""
    conn = sqlite3.connect(WEBAPP_DB)
    conn.execute("""
        INSERT OR REPLACE INTO rclick_sessions (session_id, phone, cookies, agent_name, last_used)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (session_id, phone, cookies, agent_name))
    conn.commit()
    conn.close()


def _delete_session(session_id: str):
    """Delete rclick session."""
    conn = sqlite3.connect(WEBAPP_DB)
    conn.execute("DELETE FROM rclick_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


async def rclick_auth(phone: str, password: str, session_id: str) -> dict:
    """Authenticate with ri.rclick.ru.

    Returns: {ok: bool, message: str, agent_name?: str}
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Attempt login via phone + password
            resp = await client.post(
                f"{RCLICK_BASE_URL}/auth/login/",
                data={"phone": phone, "password": password},
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") or data.get("ok"):
                    agent_name = data.get("name", data.get("agent_name", phone))
                    # Store cookies for future requests
                    cookies_str = "; ".join(f"{k}={v}" for k, v in resp.cookies.items())
                    _save_session(session_id, phone, cookies_str, agent_name)
                    return {"ok": True, "message": f"Авторизован как {agent_name}", "agent_name": agent_name}
                else:
                    return {"ok": False, "message": data.get("message", "Неверный телефон или пароль")}

            elif resp.status_code == 401:
                return {"ok": False, "message": "Неверный телефон или пароль"}
            else:
                logger.error(f"[RCLICK] Auth error: HTTP {resp.status_code}")
                return {"ok": False, "message": "Ошибка авторизации, попробуйте позже"}

    except httpx.ConnectError:
        return {"ok": False, "message": "Сервис ri.rclick.ru недоступен"}
    except Exception as e:
        logger.error(f"[RCLICK] Auth exception: {e}")
        return {"ok": False, "message": "Ошибка подключения к сервису фиксации"}


async def rclick_check_status(session_id: str) -> dict:
    """Check if session is still valid by checking local DB.

    Returns: {ok: bool, authenticated: bool, agent_name?: str}
    """
    session = _get_session(session_id)
    if not session:
        return {"ok": True, "authenticated": False}

    return {
        "ok": True,
        "authenticated": True,
        "agent_name": session.get("agent_name", session.get("phone", "")),
    }


async def rclick_create_fixation(session_id: str, client_name: str, client_phone: str,
                                  comment: str = "") -> dict:
    """Create a client fixation on ri.rclick.ru.

    Returns: {ok: bool, message: str, fixation_id?: str}
    """
    session = _get_session(session_id)
    if not session:
        return {"ok": False, "message": "Не авторизован. Выполните вход."}

    cookies = {}
    if session.get("cookies"):
        for pair in session["cookies"].split("; "):
            if "=" in pair:
                k, v = pair.split("=", 1)
                cookies[k] = v

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.post(
                f"{RCLICK_BASE_URL}/notice/newbooking/",
                data={
                    "client_name": client_name,
                    "client_phone": client_phone,
                    "comment": comment,
                },
                cookies=cookies,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") or data.get("ok"):
                    fixation_id = data.get("fixation_id", data.get("id", ""))
                    return {
                        "ok": True,
                        "message": "Клиент зафиксирован за вами на 30 дней",
                        "fixation_id": str(fixation_id),
                    }
                else:
                    return {"ok": False, "message": data.get("message", "Ошибка фиксации")}
            elif resp.status_code == 401:
                _delete_session(session_id)
                return {"ok": False, "message": "Сессия истекла. Авторизуйтесь заново."}
            else:
                logger.error(f"[RCLICK] Fixation error: HTTP {resp.status_code}")
                return {"ok": False, "message": "Ошибка сервиса фиксации"}

    except httpx.ConnectError:
        return {"ok": False, "message": "Сервис ri.rclick.ru недоступен"}
    except Exception as e:
        logger.error(f"[RCLICK] Fixation exception: {e}")
        return {"ok": False, "message": "Ошибка подключения к сервису фиксации"}


async def rclick_logout(session_id: str) -> dict:
    """Logout / clear session."""
    _delete_session(session_id)
    return {"ok": True, "message": "Вы вышли из системы"}
