"""
Сервис интеграции с ri.rclick.ru
- Авторизация риэлторов
- Фиксация клиентов
"""

import os
import sqlite3
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "rclick_tokens.db"

# API endpoints
RCLICK_LOGIN_URL = "https://ri.rclick.ru/auth/login/"
RCLICK_BOOKING_URL = "https://ri.rclick.ru/notice/newbooking/"
RCLICK_NOTICE_URL = "https://ri.rclick.ru/notice/"
PROJECT_ID = "340"  # ID проекта RIZALTA

# Заголовки как у живого браузера (RCLICK /notice/newbooking/ проверяет Origin/Referer/UA)
_RCLICK_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    ),
    "Origin": "https://ri.rclick.ru",
    "Referer": RCLICK_NOTICE_URL,
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

# PHP-сессия на бэке RCLICK живёт ~30 мин. Чуть консервативнее — треатим как истёкшую через 25 мин.
SESSION_TTL_SECONDS = 25 * 60


def init_db():
    """Создаёт таблицу токенов если не существует и мигрирует на новую схему.

    Добавляемые поля (NULL для старых записей):
      - encrypted_password: Fernet-зашифрованный пароль от ri.rclick.ru
      - phpsessid: PHP-сессия, привязанная к последнему успешному login
      - session_refreshed_at: когда получили текущую PHPSESSID
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rclick_tokens (
            telegram_id INTEGER PRIMARY KEY,
            phone TEXT NOT NULL,
            token TEXT NOT NULL,
            agent_name TEXT,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    # Миграция: добавляем колонки если их ещё нет. ALTER TABLE ADD COLUMN идемпотентна только через try/except —
    # SQLite не поддерживает ADD COLUMN IF NOT EXISTS до версии 3.35+ на всех платформах, и проще ловить ошибку.
    for col, ddl in (
        ("encrypted_password", "TEXT"),
        ("phpsessid",          "TEXT"),
        ("session_refreshed_at", "TEXT"),
    ):
        try:
            cursor.execute(f"ALTER TABLE rclick_tokens ADD COLUMN {col} {ddl}")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
    conn.commit()
    conn.close()


# ─── Encryption helpers ───────────────────────────────────────────────────────

_fernet_instance: Optional[Fernet] = None


def _get_fernet() -> Optional[Fernet]:
    """Возвращает Fernet instance из .env ключа; None если ключ не настроен."""
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
    """Шифрует пароль через Fernet; возвращает str (base64) или None если ключ не настроен."""
    f = _get_fernet()
    if f is None:
        return None
    return f.encrypt(password.encode("utf-8")).decode("utf-8")


def _decrypt_password(encrypted: Optional[str]) -> Optional[str]:
    """Расшифровывает пароль. Возвращает None если:
       - encrypted is None (старая запись без сохранённого пароля)
       - ключ не настроен
       - ключ сменился или шифротекст повреждён (InvalidToken)
    """
    if not encrypted:
        return None
    f = _get_fernet()
    if f is None:
        return None
    try:
        return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        print(f"[RCLICK] Password decryption failed — key mismatch or corrupted data")
        return None


def get_token(telegram_id: int) -> Optional[str]:
    """Получает действующий токен риэлтора."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT token, expires_at FROM rclick_tokens WHERE telegram_id = ?",
        (telegram_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    token, expires_at = row
    if datetime.fromisoformat(expires_at) < datetime.now():
        # Токен истёк
        delete_token(telegram_id)
        return None
    
    return token


def _get_auth_row(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Читает всю auth-строку юзера. Возвращает None если записи нет или токен протух (90-д)."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT telegram_id, phone, token, expires_at, "
        "encrypted_password, phpsessid, session_refreshed_at "
        "FROM rclick_tokens WHERE telegram_id=?", (telegram_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.now():
        delete_token(telegram_id)
        return None
    return dict(row)


def save_token(
    telegram_id: int,
    phone: str,
    token: str,
    agent_name: str = "",
    encrypted_password: Optional[str] = None,
    phpsessid: Optional[str] = None,
    session_refreshed_at: Optional[str] = None,
):
    """Сохраняет токен риэлтора. Новые поля опциональны — при None остаются/становятся NULL."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Токен действует ~100 дней
    expires_at = (datetime.now() + timedelta(days=90)).isoformat()
    created_at = datetime.now().isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO rclick_tokens
        (telegram_id, phone, token, agent_name, expires_at, created_at,
         encrypted_password, phpsessid, session_refreshed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (telegram_id, phone, token, agent_name, expires_at, created_at,
          encrypted_password, phpsessid, session_refreshed_at))

    conn.commit()
    conn.close()


def delete_token(telegram_id: int):
    """Удаляет токен риэлтора."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rclick_tokens WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()


def save_auth_after_login(
    telegram_id: int,
    phone: str,
    password: str,
    login_result: Dict[str, Any],
) -> None:
    """Сохраняет auth-стейт после успешного login_rclick().

    Шифрует пароль (Fernet) и кладёт вместе с token + phpsessid в БД.
    Handler не должен знать про шифрование — вызывает эту функцию с plaintext.
    Если RCLICK_ENCRYPTION_KEY не настроен, encrypted_password останется NULL,
    авто-релогин работать не будет (но login один раз — пройдёт).
    """
    save_token(
        telegram_id,
        phone,
        login_result["token"],
        login_result.get("agent_name", ""),
        encrypted_password=_encrypt_password(password),
        phpsessid=login_result["phpsessid"],
        session_refreshed_at=datetime.now().isoformat(),
    )


def login_rclick(phone: str, password: str) -> Dict[str, Any]:
    """
    Авторизация на ri.rclick.ru через requests.Session с браузерными заголовками.

    Returns:
        {"success": True, "token": "...", "phpsessid": "...", "agent_name": ""}
      или {"success": False, "error": "..."}

    ВАЖНО: RCLICK выдаёт ДВЕ куки (rClick_token + PHPSESSID), обе обязательны для
    последующих вызовов /notice/newbooking/. Если какой-то нет — считаем login'ом неудачным.
    """
    try:
        session = requests.Session()
        session.headers.update(_RCLICK_BROWSER_HEADERS)
        response = session.post(
            RCLICK_LOGIN_URL,
            data={"phone": phone, "password": password},
            timeout=30,
            allow_redirects=False,
        )
        token = session.cookies.get("rClick_token")
        phpsessid = session.cookies.get("PHPSESSID")
        if token and phpsessid:
            return {
                "success": True,
                "token": token,
                "phpsessid": phpsessid,
                "agent_name": "",
            }
        print(f"[RCLICK-LOGIN] failed: status={response.status_code} "
              f"has_token={bool(token)} has_phpsessid={bool(phpsessid)} "
              f"body={response.text[:200]!r}")
        return {"success": False, "error": "Неверный телефон или пароль"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Ошибка подключения: {str(e)}"}


def _format_phone_for_rclick(phone: str) -> str:
    """Преобразует 11-значный номер в формат '8 (XXX) XXX-XX-XX' для RCLICK API."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 11 and digits[0] in ("7", "8"):
        return f"8 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone


# ─── Low-level booking primitives ─────────────────────────────────────────────

def _do_rclick_booking(token, phpsessid, client_name, client_phone, message, manager_id):
    """Отправляет один POST /notice/newbooking/ с заданными cookies.

    Returns (response, parsed_json_or_None). JSON=None если тело не парсится.
    Может выбросить requests.RequestException — обрабатывает вызывающий.
    """
    client_phone_fmt = _format_phone_for_rclick(client_phone)
    multipart = [
        ("agentLastName",  (None, "")),
        ("agentFirstName", (None, "")),
        ("agentPhone",     (None, "")),
        ("project",        (None, PROJECT_ID)),
        ("clientName",     (None, client_name)),
        ("clientPhone",    (None, client_phone_fmt)),
        ("manager",        (None, str(manager_id))),
        ("message",        (None, message)),
        ("pasImage[]",     ("", b"", "application/octet-stream")),
        ("policy",         (None, "on")),
    ]
    cookies = {"rClick_token": token}
    if phpsessid:
        cookies["PHPSESSID"] = phpsessid
    req_preview = [(k, v[1] if v[0] is None else f"<file name={v[0]!r} len={len(v[1])}>") for k, v in multipart]
    print(
        f"[RCLICK-REQ] url={RCLICK_BOOKING_URL} method=POST "
        f"cookies={sorted(cookies.keys())} "
        f"headers_added={sorted(_RCLICK_BROWSER_HEADERS.keys())} "
        f"multipart={req_preview!r}"
    )
    response = requests.post(
        RCLICK_BOOKING_URL,
        cookies=cookies,
        headers=_RCLICK_BROWSER_HEADERS,
        files=multipart,
        timeout=30,
    )
    print(f"[RCLICK] status={response.status_code} len={len(response.content)} "
          f"ct={response.headers.get('content-type')} body={response.text[:500]!r}")
    try:
        return response, response.json()
    except ValueError:
        return response, None


def _is_dead_session(response) -> bool:
    """RCLICK сигнализирует о мёртвой PHP-сессии как HTTP 500 с пустым телом."""
    return response.status_code >= 500 and len(response.content) == 0


def _interpret_booking_result(data) -> Dict[str, Any]:
    """Преобразует JSON-ответ RCLICK в стандартизированный словарь для UI."""
    if data is None:
        return {"success": False, "error": "Некорректный ответ от сервера"}
    if data.get("success") == 1 and data.get("status") == 1:
        return {
            "success": True,
            "message": "Клиент зафиксирован! Номер отправлен в CRM застройщика.",
        }
    if data.get("success") == 1 and data.get("status") == 0:
        view = data.get("view", "")
        if "Телефон клиента не может совпадать" in view:
            return {"success": False, "error": "Телефон клиента совпадает с вашим номером"}
        if "уже зафиксирован" in view.lower():
            return {"success": False, "error": "Этот клиент уже зафиксирован"}
        return {"success": False, "error": "Ошибка при фиксации. Проверьте данные."}
    return {"success": False, "error": "Неизвестная ошибка от сервера"}


# Rate-limit для авто-релогина. Не чаще 1 раза в 30 сек на telegram_id.
_RELOGIN_COOLDOWN_SECONDS = 30
_last_relogin_attempt: Dict[int, float] = {}


def _attempt_relogin(telegram_id: int) -> Dict[str, Any]:
    """Пробует перелогинить юзера используя сохранённый зашифрованный пароль.

    Returns:
        {"success": True, "token":..., "phpsessid":...}
      или {"success": False, "error":..., "reauth_required": bool}
    """
    now = datetime.now().timestamp()
    last = _last_relogin_attempt.get(telegram_id, 0)
    if now - last < _RELOGIN_COOLDOWN_SECONDS:
        return {
            "success": False,
            "error": "Сервис временно недоступен, попробуйте через минуту",
            "reauth_required": False,
        }
    _last_relogin_attempt[telegram_id] = now

    row = _get_auth_row(telegram_id)
    if not row:
        return {"success": False, "error": "Не авторизованы в RCLICK", "reauth_required": True}
    password = _decrypt_password(row.get("encrypted_password"))
    if not password:
        # Старая запись без пароля / ключ потерян / шифротекст повреждён — чистим и просим авторизацию
        delete_token(telegram_id)
        return {
            "success": False,
            "error": "Сессия истекла, пожалуйста авторизуйтесь заново",
            "reauth_required": True,
        }
    print(f"[RCLICK-RELOGIN] telegram_id={telegram_id} phone={row['phone']}")
    result = login_rclick(row["phone"], password)
    if not result["success"]:
        return {
            "success": False,
            "error": "Не удалось возобновить сессию. Возможно, сменился пароль в ri.rclick.ru — авторизуйтесь заново",
            "reauth_required": True,
        }
    save_token(
        telegram_id, row["phone"], result["token"], result.get("agent_name", ""),
        encrypted_password=row["encrypted_password"],
        phpsessid=result["phpsessid"],
        session_refreshed_at=datetime.now().isoformat(),
    )
    return {"success": True, "token": result["token"], "phpsessid": result["phpsessid"]}


def create_booking(
    token: str,
    client_name: str,
    client_phone: str,
    message: str = "",
    manager_id: int = 2,
) -> Dict[str, Any]:
    """LOW-LEVEL: одна попытка фиксации по rClick_token, без авто-релогина.

    Используется внутренне и для обратной совместимости (внешние вызовы).
    UI-код должен предпочитать create_booking_for_user() — с релогином.

    Returns:
        {"success": True, "message": "..."} или
        {"success": False, "error": "..."}
    """
    try:
        response, data = _do_rclick_booking(
            token, None, client_name, client_phone, message, manager_id
        )
    except requests.RequestException as e:
        return {"success": False, "error": f"Ошибка подключения: {str(e)}"}
    return _interpret_booking_result(data)


def create_booking_for_user(
    telegram_id: int,
    client_name: str,
    client_phone: str,
    message: str = "",
    manager_id: int = 2,
) -> Dict[str, Any]:
    """HIGH-LEVEL: фиксация с авто-релогином при мёртвой PHP-сессии.

    Алгоритм:
      1. Читаем auth-строку юзера из БД (token + phpsessid + encrypted_password)
      2. Первая попытка POST /notice/newbooking/ с обеими cookies
      3. Если сервер вернул 500+пусто → детектор мёртвой сессии
         → _attempt_relogin() с rate-limit 30 сек
         → повтор booking (максимум 1 раз)
      4. Если повтор тоже 500+пусто → считаем глобальным сбоем RCLICK

    Returns:
        {"success": True, "message": "..."} при успехе
      или {"success": False, "error": "...", "reauth_required": bool} при ошибке.
    """
    row = _get_auth_row(telegram_id)
    if not row:
        return {"success": False, "error": "Не авторизованы в RCLICK", "reauth_required": True}

    try:
        response, data = _do_rclick_booking(
            row["token"], row.get("phpsessid"),
            client_name, client_phone, message, manager_id,
        )
    except requests.RequestException as e:
        return {"success": False, "error": f"Ошибка подключения: {str(e)}"}

    if not _is_dead_session(response):
        return _interpret_booking_result(data)

    # Детектор мёртвой сессии сработал — авто-релогин
    print(f"[RCLICK-DEAD-SESSION] telegram_id={telegram_id} — auto-relogin")
    relogin = _attempt_relogin(telegram_id)
    if not relogin["success"]:
        return relogin  # содержит error + reauth_required

    try:
        response2, data2 = _do_rclick_booking(
            relogin["token"], relogin["phpsessid"],
            client_name, client_phone, message, manager_id,
        )
    except requests.RequestException as e:
        return {"success": False, "error": f"Ошибка подключения: {str(e)}"}

    if _is_dead_session(response2):
        # Даже со свежей сессией 500+пусто → глобальный сбой RCLICK
        return {
            "success": False,
            "error": "CRM временно недоступен, попробуйте через несколько минут",
            "reauth_required": False,
        }
    return _interpret_booking_result(data2)


def is_authorized(telegram_id: int) -> bool:
    """Проверяет авторизован ли риэлтор."""
    return get_token(telegram_id) is not None


# Инициализация БД при импорте
init_db()
