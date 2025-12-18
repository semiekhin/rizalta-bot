"""
Сервис интеграции с ri.rclick.ru
- Авторизация риэлторов
- Фиксация клиентов
"""

import sqlite3
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "rclick_tokens.db"

# API endpoints
RCLICK_LOGIN_URL = "https://ri.rclick.ru/auth/login/"
RCLICK_BOOKING_URL = "https://ri.rclick.ru/notice/newbooking/"
PROJECT_ID = "340"  # ID проекта RIZALTA


def init_db():
    """Создаёт таблицу токенов если не существует."""
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
    conn.commit()
    conn.close()


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


def save_token(telegram_id: int, phone: str, token: str, agent_name: str = ""):
    """Сохраняет токен риэлтора."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Токен действует ~100 дней
    expires_at = (datetime.now() + timedelta(days=90)).isoformat()
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT OR REPLACE INTO rclick_tokens 
        (telegram_id, phone, token, agent_name, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (telegram_id, phone, token, agent_name, expires_at, created_at))
    
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


def login_rclick(phone: str, password: str) -> Dict[str, Any]:
    """
    Авторизация на ri.rclick.ru
    
    Returns:
        {"success": True, "token": "...", "agent_name": "..."} или
        {"success": False, "error": "..."}
    """
    try:
        response = requests.post(
            RCLICK_LOGIN_URL,
            data={"phone": phone, "password": password},
            timeout=30,
            allow_redirects=False
        )
        
        # Токен приходит в Set-Cookie
        cookies = response.cookies
        token = cookies.get("rClick_token")
        
        if token:
            return {
                "success": True,
                "token": token,
                "agent_name": ""  # Можно парсить из ответа если нужно
            }
        else:
            return {
                "success": False,
                "error": "Неверный телефон или пароль"
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Ошибка подключения: {str(e)}"
        }


def create_booking(
    token: str,
    client_name: str,
    client_phone: str,
    message: str = "",
    manager_id: int = 2
) -> Dict[str, Any]:
    """
    Создаёт фиксацию клиента на ri.rclick.ru
    
    Returns:
        {"success": True, "message": "..."} или
        {"success": False, "error": "..."}
    """
    try:
        response = requests.post(
            RCLICK_BOOKING_URL,
            cookies={"rClick_token": token},
            data={
                "project": PROJECT_ID,
                "clientName": client_name,
                "clientPhone": client_phone,
                "manager": str(manager_id),
                "message": message,
                "policy": "on"
            },
            timeout=30
        )
        
        data = response.json()
        
        if data.get("success") == 1 and data.get("status") == 1:
            return {
                "success": True,
                "message": "Клиент зафиксирован! Номер отправлен в CRM застройщика."
            }
        elif data.get("success") == 1 and data.get("status") == 0:
            # Парсим сообщение об ошибке из HTML
            view = data.get("view", "")
            if "Телефон клиента не может совпадать" in view:
                return {
                    "success": False,
                    "error": "Телефон клиента совпадает с вашим номером"
                }
            elif "уже зафиксирован" in view.lower():
                return {
                    "success": False,
                    "error": "Этот клиент уже зафиксирован"
                }
            else:
                return {
                    "success": False,
                    "error": "Ошибка при фиксации. Проверьте данные."
                }
        else:
            return {
                "success": False,
                "error": "Неизвестная ошибка от сервера"
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Ошибка подключения: {str(e)}"
        }
    except ValueError:
        return {
            "success": False,
            "error": "Некорректный ответ от сервера"
        }


def is_authorized(telegram_id: int) -> bool:
    """Проверяет авторизован ли риэлтор."""
    return get_token(telegram_id) is not None


# Инициализация БД при импорте
init_db()
