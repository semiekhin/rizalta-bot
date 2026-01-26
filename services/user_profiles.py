"""
Управление профилями риэлторов.
"""

import sqlite3
from typing import Optional, Dict
from datetime import datetime

DB_PATH = "/opt/bot/properties.db"


def get_profile(user_id: int) -> Optional[Dict]:
    """Получает профиль пользователя."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, name, phone, timezone, created_at, updated_at
        FROM user_profiles WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "name": row[1],
            "phone": row[2],
            "timezone": row[3] or "altai",
            "created_at": row[4],
            "updated_at": row[5]
        }
    return None


def save_profile(user_id: int, name: str = None, phone: str = None, timezone: str = None):
    """Создаёт или обновляет профиль."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    existing = get_profile(user_id)
    now = datetime.now().isoformat()
    
    if existing:
        # Обновляем только переданные поля
        updates = []
        values = []
        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if phone is not None:
            updates.append("phone = ?")
            values.append(phone)
        if timezone is not None:
            updates.append("timezone = ?")
            values.append(timezone)
        
        if updates:
            updates.append("updated_at = ?")
            values.append(now)
            values.append(user_id)
            
            cursor.execute(f"""
                UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = ?
            """, values)
    else:
        # Создаём новый
        cursor.execute("""
            INSERT INTO user_profiles (user_id, name, phone, timezone, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, phone, timezone or "altai", now))
    
    conn.commit()
    conn.close()


def convert_time(time_str: str, from_tz: str, to_tz: str) -> str:
    """
    Конвертирует время между часовыми поясами.
    altai = UTC+7, moscow = UTC+3
    Разница: Алтай = Москва + 4 часа
    """
    if from_tz == to_tz:
        return time_str
    
    try:
        hours, minutes = map(int, time_str.split(':'))
        
        if from_tz == "altai" and to_tz == "moscow":
            hours -= 4
        elif from_tz == "moscow" and to_tz == "altai":
            hours += 4
        
        # Обработка перехода через полночь
        if hours < 0:
            hours += 24
        elif hours >= 24:
            hours -= 24
        
        return f"{hours:02d}:{minutes:02d}"
    except:
        return time_str


def format_dual_time(time_str: str, base_tz: str = "altai") -> str:
    """
    Форматирует время для обоих поясов.
    Возвращает: "14:30 (Алтай) / 10:30 (Мск)"
    """
    if base_tz == "altai":
        altai_time = time_str
        moscow_time = convert_time(time_str, "altai", "moscow")
    else:
        moscow_time = time_str
        altai_time = convert_time(time_str, "moscow", "altai")
    
    return f"{altai_time} (Алтай) / {moscow_time} (Мск)"


def validate_time(time_str: str) -> Optional[str]:
    """
    Валидирует и нормализует время.
    Принимает: "10:30", "10.30", "1030", "10 30"
    Возвращает: "10:30" или None если невалидно
    """
    import re
    
    # Убираем лишние символы
    cleaned = re.sub(r'[^\d]', '', time_str)
    
    # Пробуем разные форматы
    if len(cleaned) == 4:
        hours = int(cleaned[:2])
        minutes = int(cleaned[2:])
    elif len(cleaned) == 3:
        hours = int(cleaned[0])
        minutes = int(cleaned[1:])
    elif ':' in time_str or '.' in time_str:
        parts = re.split(r'[:.]', time_str)
        if len(parts) == 2:
            hours = int(parts[0])
            minutes = int(parts[1])
        else:
            return None
    else:
        return None
    
    # Валидация
    if 0 <= hours <= 23 and 0 <= minutes <= 59:
        return f"{hours:02d}:{minutes:02d}"
    
    return None
