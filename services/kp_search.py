"""
Сервис поиска коммерческих предложений (JPG файлов).
"""

import os
import re
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

from config.settings import BASE_DIR


# Путь к папке с КП
KP_DIR = os.path.join(BASE_DIR, "kp_all")

# Путь к базе данных
DB_PATH = os.path.join(BASE_DIR, "properties.db")


def normalize_unit_code(raw: str) -> str:
    """Нормализует код лота (кириллица → латиница)."""
    if not raw:
        return ""
    
    code = str(raw).strip().upper()
    
    # Кириллица → латиница
    table = str.maketrans({
        "А": "A", "В": "B", "Е": "E", "К": "K",
        "М": "M", "Н": "H", "О": "O", "Р": "P",
        "С": "S", "Т": "T", "У": "Y", "Х": "X",
    })
    code = code.translate(table)
    
    return "".join(ch for ch in code if ch.isalnum())


def get_all_kp_files() -> Dict[str, str]:
    """
    Возвращает словарь {normalized_code: filepath} для всех КП.
    """
    result = {}
    
    if not os.path.exists(KP_DIR):
        print(f"[KP] Папка не найдена: {KP_DIR}")
        return result
    
    for filename in os.listdir(KP_DIR):
        if not filename.endswith(".jpg"):
            continue
        
        # Паттерн: kp_{площадь}m_{тип}_{код}.jpg
        # Пример: kp_24.5m_business_А209.jpg
        match = re.match(r"kp_[\d.]+m_\w+_(.+)\.jpg", filename)
        if match:
            raw_code = match.group(1)
            normalized = normalize_unit_code(raw_code)
            result[normalized] = os.path.join(KP_DIR, filename)
    
    return result


def find_kp_by_code(unit_code: str) -> Optional[str]:
    """
    Ищет КП по коду лота.
    Возвращает путь к JPG или None.
    """
    normalized = normalize_unit_code(unit_code)
    all_kp = get_all_kp_files()
    
    return all_kp.get(normalized)


def find_kp_by_area(area: float, tolerance: float = 0.5) -> List[str]:
    """
    Ищет КП по площади (±tolerance м²).
    Возвращает список путей к JPG.
    """
    result = []
    
    if not os.path.exists(KP_DIR):
        return result
    
    for filename in os.listdir(KP_DIR):
        if not filename.endswith(".jpg"):
            continue
        
        # Извлекаем площадь из имени файла
        match = re.match(r"kp_([\d.]+)m_", filename)
        if match:
            file_area = float(match.group(1))
            if abs(file_area - area) <= tolerance:
                result.append(os.path.join(KP_DIR, filename))
    
    return result


def find_kp_by_budget(budget: int) -> List[str]:
    """
    Ищет КП по бюджету.
    Находит лоты в пределах ±10% от бюджета.
    Возвращает список путей к JPG.
    """
    if not os.path.exists(DB_PATH):
        print(f"[KP] База данных не найдена: {DB_PATH}")
        return []
    
    # Диапазон цен
    min_price = int(budget * 0.9)
    max_price = int(budget * 1.1)
    
    # Ищем лоты в базе
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT code FROM units 
        WHERE price_rub >= ? AND price_rub <= ?
        ORDER BY price_rub
    """, (min_price, max_price))
    
    codes = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Ищем КП по кодам
    all_kp = get_all_kp_files()
    result = []
    
    for code in codes:
        normalized = normalize_unit_code(code)
        if normalized in all_kp:
            result.append(all_kp[normalized])
    
    return result


def find_kp_by_floor(floor: int, block_section: int = None) -> List[str]:
    """
    Ищет КП по этажу (и корпусу).
    block_section: 1 = корпус 2 (А), 2 = корпус 1 (В)
    Возвращает список путей к JPG.
    """
    if not os.path.exists(DB_PATH):
        print(f"[KP] База данных не найдена: {DB_PATH}")
        return []
    
    # Ищем лоты в базе
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if block_section:
        cursor.execute("""
            SELECT code FROM units 
            WHERE floor = ? AND block_section = ?
            ORDER BY code
        """, (floor, block_section))
    else:
        cursor.execute("""
            SELECT code FROM units 
            WHERE floor = ?
            ORDER BY code
        """, (floor,))
    
    codes = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Ищем КП по кодам
    all_kp = get_all_kp_files()
    result = []
    
    for code in codes:
        normalized = normalize_unit_code(code)
        if normalized in all_kp:
            result.append(all_kp[normalized])
    
    return result


def parse_kp_request(text: str) -> Dict[str, Any]:
    """
    Парсит запрос пользователя и определяет тип поиска.
    
    Возвращает:
    {
        "type": "code" | "area" | "budget" | "floor" | "unknown",
        "value": ...,
        "block_section": ... (для floor)
    }
    """
    text = text.lower().strip()
    
    # Ищем код лота (А209, B210, В415 и т.д.)
    code_match = re.search(r"[аaвb][- ]?\d{3,4}", text, re.IGNORECASE)
    if code_match:
        return {"type": "code", "value": code_match.group()}
    
    # Ищем площадь (25 м², 30 метров, 22.5 кв.м)
    area_match = re.search(r"(\d+[.,]?\d*)\s*(м²|м2|кв\.?м?|метр)", text)
    if area_match:
        area = float(area_match.group(1).replace(",", "."))
        return {"type": "area", "value": area}
    
    # Ищем бюджет (16 млн, 15000000, 20 миллионов)
    budget_match = re.search(r"(\d+[.,]?\d*)\s*(млн|миллион)", text)
    if budget_match:
        budget = float(budget_match.group(1).replace(",", ".")) * 1_000_000
        return {"type": "budget", "value": int(budget)}
    
    # Просто число > 1 млн — скорее всего бюджет
    big_num_match = re.search(r"(\d{7,})", text.replace(" ", ""))
    if big_num_match:
        return {"type": "budget", "value": int(big_num_match.group(1))}
    
    # Ищем этаж (4 этаж, этаж 5)
    floor_match = re.search(r"(\d+)\s*этаж|этаж\s*(\d+)", text)
    if floor_match:
        floor = int(floor_match.group(1) or floor_match.group(2))
        
        # Определяем корпус
        block_section = None
        if "корпус 1" in text or "корпус1" in text:
            block_section = 2  # В = block_section 2
        elif "корпус 2" in text or "корпус2" in text:
            block_section = 1  # А = block_section 1
        
        return {"type": "floor", "value": floor, "block_section": block_section}
    
    return {"type": "unknown", "value": None}


def get_kp_info_from_filename(filepath: str) -> Dict[str, Any]:
    """
    Извлекает информацию о КП из имени файла.
    """
    filename = os.path.basename(filepath)
    
    # kp_24.5m_business_А209.jpg
    match = re.match(r"kp_([\d.]+)m_(\w+)_(.+)\.jpg", filename)
    if match:
        return {
            "area": float(match.group(1)),
            "type": match.group(2),
            "code": match.group(3),
        }
    
    return {"area": 0, "type": "unknown", "code": "unknown"}
