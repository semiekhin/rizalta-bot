"""RClick service — auth and client fixation via ri.rclick.ru.

Ported from /opt/bot-dev/services/rclick_service.py but adapted for webapp:
  - httpx.AsyncClient instead of requests.Session
  - keyed by session_id (browser cookie) instead of telegram_id
  - shared webapp.db, table rclick_sessions
  - auto-relogin on dead PHP session (HTTP 500 + empty body)
  - Fernet-encrypted password for auto-relogin

RCLICK API contract (reverse-engineered):
  - POST /auth/login/ with form {phone, password} → sets cookies rClick_token AND PHPSESSID
  - POST /notice/newbooking/ requires BOTH cookies, multipart/form-data,
    browser-like headers (UA + Origin + Referer), phone "8 (XXX) XXX-XX-XX",
    and empty agentLastName/FirstName/Phone + pasImage[] empty file.
  - PHPSESSID TTL ≈ 30 min; once dead → HTTP 500 empty body. rClick_token alone is NOT enough.
"""

import os
import sqlite3
import logging
import time
import httpx
from datetime import datetime
from typing import Optional, Dict, Any

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

RCLICK_BASE_URL = os.getenv("RCLICK_BASE_URL", "https://ri.rclick.ru")
RCLICK_LOGIN_URL = f"{RCLICK_BASE_URL}/auth/login/"
RCLICK_BOOKING_URL = f"{RCLICK_BASE_URL}/notice/newbooking/"
RCLICK_NOTICE_URL = f"{RCLICK_BASE_URL}/notice/"

PROJECT_ID = "340"       # RIZALTA project id on rclick
DEFAULT_MANAGER_ID = 2   # RIZALTA manager id

WEBAPP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp.db")

# PHPSESSID on rclick backend lives ~30 min; we treat as potentially dead after 25 min.
SESSION_TTL_SECONDS = 25 * 60

# Browser-like headers — /notice/newbooking/ rejects plain HTTP clients without Origin/Referer/UA
_RCLICK_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    ),
    "Origin": RCLICK_BASE_URL,
    "Referer": RCLICK_NOTICE_URL,
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


# ─── DB layer ─────────────────────────────────────────────────────────────────

def init_rclick_table():
    """Idempotent schema for rclick_sessions. Does NOT drop existing data."""
    conn = sqlite3.connect(WEBAPP_DB)
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
    # Idempotent migrations (SQLite <3.35 has no ADD COLUMN IF NOT EXISTS)
    for col, ddl in (
        ("token", "TEXT"),
        ("phpsessid", "TEXT"),
        ("encrypted_password", "TEXT"),
        ("session_refreshed_at", "TEXT"),
    ):
        try:
            conn.execute(f"ALTER TABLE rclick_sessions ADD COLUMN {col} {ddl}")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
    conn.commit()
    conn.close()
    print("[RCLICK] Sessions table initialized")


def _get_session(session_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(WEBAPP_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM rclick_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _save_session(
    session_id: str,
    phone: str,
    token: str,
    phpsessid: str,
    agent_name: str = "",
    encrypted_password: Optional[str] = None,
):
    """Save full auth row after successful login."""
    conn = sqlite3.connect(WEBAPP_DB)
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO rclick_sessions
        (session_id, phone, token, phpsessid, agent_name, encrypted_password,
         session_refreshed_at, last_used, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE(
            (SELECT created_at FROM rclick_sessions WHERE session_id = ?),
            datetime('now')
        ))
    """, (session_id, phone, token, phpsessid, agent_name, encrypted_password,
          now, now, session_id))
    conn.commit()
    conn.close()


def _update_session_tokens(session_id: str, token: str, phpsessid: str):
    """Refresh token + phpsessid after auto-relogin (keep phone + encrypted_password)."""
    conn = sqlite3.connect(WEBAPP_DB)
    conn.execute("""
        UPDATE rclick_sessions
        SET token = ?, phpsessid = ?, session_refreshed_at = ?, last_used = ?
        WHERE session_id = ?
    """, (token, phpsessid, datetime.now().isoformat(), datetime.now().isoformat(), session_id))
    conn.commit()
    conn.close()


def _delete_session(session_id: str):
    conn = sqlite3.connect(WEBAPP_DB)
    conn.execute("DELETE FROM rclick_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ─── Fernet (password encryption for auto-relogin) ────────────────────────────

_fernet_instance: Optional[Fernet] = None


def _get_fernet() -> Optional[Fernet]:
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance
    key = os.getenv("RCLICK_ENCRYPTION_KEY")
    if not key:
        return None
    try:
        _fernet_instance = Fernet(key.encode())
        return _fernet_instance
    except (ValueError, TypeError) as e:
        print(f"[RCLICK] RCLICK_ENCRYPTION_KEY is malformed: {e}")
        return None


def _encrypt_password(password: str) -> Optional[str]:
    f = _get_fernet()
    if f is None:
        return None
    return f.encrypt(password.encode("utf-8")).decode("utf-8")


def _decrypt_password(encrypted: Optional[str]) -> Optional[str]:
    if not encrypted:
        return None
    f = _get_fernet()
    if f is None:
        return None
    try:
        return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        print("[RCLICK] Password decryption failed — key mismatch or corrupted data")
        return None


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _format_phone_for_rclick(phone: str) -> str:
    """11-digit phone → '8 (XXX) XXX-XX-XX' for RCLICK /notice/newbooking/."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 11 and digits[0] in ("7", "8"):
        return f"8 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone


def _is_dead_session(status_code: int, content_len: int) -> bool:
    """RCLICK signals dead PHP session as HTTP 500 with empty body."""
    return status_code >= 500 and content_len == 0


def _interpret_booking_result(data: Optional[dict]) -> Dict[str, Any]:
    """Map rclick JSON → {ok, message}."""
    if data is None:
        return {"ok": False, "message": "Некорректный ответ от сервера"}
    if data.get("success") == 1 and data.get("status") == 1:
        return {"ok": True, "message": "Клиент зафиксирован! Номер отправлен в CRM застройщика."}
    if data.get("success") == 1 and data.get("status") == 0:
        view = data.get("view", "")
        if "Телефон клиента не может совпадать" in view:
            return {"ok": False, "message": "Телефон клиента совпадает с вашим номером"}
        if "уже зафиксирован" in view.lower():
            return {"ok": False, "message": "Этот клиент уже зафиксирован"}
        return {"ok": False, "message": "Ошибка при фиксации. Проверьте данные."}
    return {"ok": False, "message": "Неизвестная ошибка от сервера"}


# ─── Public API ───────────────────────────────────────────────────────────────

async def rclick_auth(phone: str, password: str, session_id: str) -> Dict[str, Any]:
    """Login to ri.rclick.ru. Stores rClick_token + PHPSESSID + encrypted password.

    Returns: {ok: bool, message: str, agent_name?: str}
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False,
                                     headers=_RCLICK_BROWSER_HEADERS) as client:
            resp = await client.post(RCLICK_LOGIN_URL, data={"phone": phone, "password": password})

        token = resp.cookies.get("rClick_token")
        phpsessid = resp.cookies.get("PHPSESSID")

        if not (token and phpsessid):
            logger.warning(
                f"[RCLICK-LOGIN] failed: status={resp.status_code} "
                f"has_token={bool(token)} has_phpsessid={bool(phpsessid)}"
            )
            return {"ok": False, "message": "Неверный телефон или пароль"}

        agent_name = phone  # rclick login doesn't return name; use phone as label
        _save_session(
            session_id=session_id,
            phone=phone,
            token=token,
            phpsessid=phpsessid,
            agent_name=agent_name,
            encrypted_password=_encrypt_password(password),
        )
        return {"ok": True, "message": f"Авторизован как {agent_name}", "agent_name": agent_name}

    except httpx.ConnectError:
        return {"ok": False, "message": "Сервис ri.rclick.ru недоступен"}
    except Exception as e:
        logger.error(f"[RCLICK] Auth exception: {e}")
        return {"ok": False, "message": "Ошибка подключения к сервису фиксации"}


async def rclick_check_status(session_id: str) -> Dict[str, Any]:
    """Lightweight check: has any row for this session_id."""
    session = _get_session(session_id)
    if not session or not session.get("token"):
        return {"ok": True, "authenticated": False}
    return {
        "ok": True,
        "authenticated": True,
        "agent_name": session.get("agent_name") or session.get("phone", ""),
    }


async def _do_booking(
    token: str,
    phpsessid: Optional[str],
    client_name: str,
    client_phone: str,
    comment: str,
    manager_id: int,
) -> tuple[int, int, Optional[dict]]:
    """One POST to /notice/newbooking/. Returns (status_code, content_len, parsed_json_or_None)."""
    client_phone_fmt = _format_phone_for_rclick(client_phone)

    # httpx multipart: dict of name → (filename, content, content_type). filename=None → plain form field.
    files = {
        "agentLastName":  (None, ""),
        "agentFirstName": (None, ""),
        "agentPhone":     (None, ""),
        "project":        (None, PROJECT_ID),
        "clientName":     (None, client_name),
        "clientPhone":    (None, client_phone_fmt),
        "manager":        (None, str(manager_id)),
        "message":        (None, comment),
        "pasImage[]":     ("", b"", "application/octet-stream"),
        "policy":         (None, "on"),
    }
    cookies = {"rClick_token": token}
    if phpsessid:
        cookies["PHPSESSID"] = phpsessid

    print(
        f"[RCLICK-REQ] url={RCLICK_BOOKING_URL} method=POST "
        f"cookies={sorted(cookies.keys())} "
        f"client_name={client_name!r} client_phone={client_phone_fmt!r}"
    )

    async with httpx.AsyncClient(timeout=30.0, headers=_RCLICK_BROWSER_HEADERS) as client:
        resp = await client.post(RCLICK_BOOKING_URL, cookies=cookies, files=files)

    print(f"[RCLICK] status={resp.status_code} len={len(resp.content)} "
          f"ct={resp.headers.get('content-type')} body={resp.text[:500]!r}")

    try:
        return resp.status_code, len(resp.content), resp.json()
    except ValueError:
        return resp.status_code, len(resp.content), None


# Rate limit for auto-relogin: not more than once per 30 sec per session_id
_RELOGIN_COOLDOWN_SECONDS = 30
_last_relogin_attempt: Dict[str, float] = {}


async def _attempt_relogin(session_id: str) -> Dict[str, Any]:
    """Try to re-login using saved encrypted password. Updates DB on success.

    Returns: {ok: True, token, phpsessid} or {ok: False, message, reauth_required}
    """
    now = time.time()
    last = _last_relogin_attempt.get(session_id, 0.0)
    if now - last < _RELOGIN_COOLDOWN_SECONDS:
        return {
            "ok": False,
            "message": "Сервис временно недоступен, попробуйте через минуту",
            "reauth_required": False,
        }
    _last_relogin_attempt[session_id] = now

    session = _get_session(session_id)
    if not session:
        return {"ok": False, "message": "Не авторизованы в RCLICK", "reauth_required": True}

    password = _decrypt_password(session.get("encrypted_password"))
    if not password:
        # Old record w/o saved password, or key rotated, or ciphertext corrupted → reauth
        _delete_session(session_id)
        return {
            "ok": False,
            "message": "Сессия истекла, пожалуйста авторизуйтесь заново",
            "reauth_required": True,
        }

    print(f"[RCLICK-RELOGIN] session_id={session_id[:8]}… phone={session['phone']}")
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False,
                                     headers=_RCLICK_BROWSER_HEADERS) as client:
            resp = await client.post(
                RCLICK_LOGIN_URL,
                data={"phone": session["phone"], "password": password},
            )
        token = resp.cookies.get("rClick_token")
        phpsessid = resp.cookies.get("PHPSESSID")
        if not (token and phpsessid):
            return {
                "ok": False,
                "message": "Не удалось возобновить сессию. Возможно, сменился пароль в ri.rclick.ru — авторизуйтесь заново",
                "reauth_required": True,
            }
        _update_session_tokens(session_id, token, phpsessid)
        return {"ok": True, "token": token, "phpsessid": phpsessid}
    except httpx.HTTPError as e:
        return {"ok": False, "message": f"Ошибка подключения: {e}", "reauth_required": False}


async def rclick_create_fixation(
    session_id: str,
    client_name: str,
    client_phone: str,
    comment: str = "",
) -> Dict[str, Any]:
    """High-level booking with auto-relogin on dead PHP session.

    Returns: {ok, message, reauth_required?}
    """
    session = _get_session(session_id)
    if not session or not session.get("token"):
        return {"ok": False, "message": "Не авторизованы. Выполните вход.", "reauth_required": True}

    try:
        status, content_len, data = await _do_booking(
            session["token"], session.get("phpsessid"),
            client_name, client_phone, comment, DEFAULT_MANAGER_ID,
        )
    except httpx.ConnectError:
        return {"ok": False, "message": "Сервис ri.rclick.ru недоступен"}
    except httpx.HTTPError as e:
        logger.error(f"[RCLICK] booking HTTP error: {e}")
        return {"ok": False, "message": "Ошибка подключения к сервису фиксации"}

    if not _is_dead_session(status, content_len):
        return _interpret_booking_result(data)

    # Dead PHP session → auto-relogin → one retry
    print(f"[RCLICK-DEAD-SESSION] session_id={session_id[:8]}… — auto-relogin")
    relogin = await _attempt_relogin(session_id)
    if not relogin["ok"]:
        return relogin  # has message + reauth_required

    try:
        status2, content_len2, data2 = await _do_booking(
            relogin["token"], relogin["phpsessid"],
            client_name, client_phone, comment, DEFAULT_MANAGER_ID,
        )
    except httpx.HTTPError as e:
        return {"ok": False, "message": f"Ошибка подключения: {e}"}

    if _is_dead_session(status2, content_len2):
        return {
            "ok": False,
            "message": "CRM временно недоступен, попробуйте через несколько минут",
            "reauth_required": False,
        }
    return _interpret_booking_result(data2)


async def rclick_logout(session_id: str) -> Dict[str, Any]:
    _delete_session(session_id)
    return {"ok": True, "message": "Вы вышли из системы"}
