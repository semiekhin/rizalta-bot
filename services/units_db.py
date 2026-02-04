"""
Сервис для работы с лотами из properties.db.
Единый источник данных для расчётов и КП.

v2.1.0 — Все 348 лотов, фильтрация по корпусам/этажам
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Путь к БД
DB_PATH = Path(__file__).parent.parent / "properties.db"

# Таблица транслитерации кириллица ↔ латиница
CYRILLIC_TO_LATIN = {
    "А": "A", "В": "B", "Е": "E", "К": "K",
    "М": "M", "Н": "H", "О": "O", "Р": "P",
    "С": "S", "Т": "T", "У": "Y", "Х": "X",
}
LATIN_TO_CYRILLIC = {v: k for k, v in CYRILLIC_TO_LATIN.items()}


def get_db_connection():
    """Возвращает соединение с БД."""
    return sqlite3.connect(str(DB_PATH))


def get_hidden_buildings() -> List[int]:
    """Возвращает список скрытых корпусов из конфига."""
    import json
    config_path = Path(__file__).parent.parent / "data" / "hidden_buildings.json"
    try:
        with open(config_path) as f:
            return json.load(f).get("hidden", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def normalize_code(code: str) -> Tuple[str, str]:
    """
    Нормализует код лота.
    Возвращает (код_кириллица, код_латиница) для поиска в БД.
    
    Примеры:
        "В708" → ("В708", "B708")
        "B708" → ("В708", "B708")
        "в708" → ("В708", "B708")
    """
    code = code.strip().upper()
    
    # Создаём оба варианта
    code_cyrillic = code
    code_latin = code
    
    for cyr, lat in CYRILLIC_TO_LATIN.items():
        code_latin = code_latin.replace(cyr, lat)
    
    for lat, cyr in LATIN_TO_CYRILLIC.items():
        code_cyrillic = code_cyrillic.replace(lat, cyr)
    
    return code_cyrillic, code_latin


def parse_floor_query(floor_query: str) -> List[int]:
    """
    Парсит запрос по этажам.
    
    Примеры:
        "5" → [5]
        "верхние" → [7, 8, 9]
        "нижние" → [1, 2, 3]
        "средние" → [4, 5, 6]
        "1-3" → [1, 2, 3]
    """
    floor_query = floor_query.lower().strip()
    
    if floor_query in ("верхние", "верхних", "высокие", "высоких", "top"):
        return [7, 8, 9]
    elif floor_query in ("нижние", "нижних", "низкие", "низких", "bottom"):
        return [1, 2, 3]
    elif floor_query in ("средние", "средних", "middle"):
        return [4, 5, 6]
    elif "-" in floor_query:
        # Диапазон "1-3"
        parts = floor_query.split("-")
        try:
            start, end = int(parts[0]), int(parts[1])
            return list(range(start, end + 1))
        except (ValueError, IndexError):
            return []
    else:
        # Одиночный этаж
        try:
            return [int(floor_query)]
        except ValueError:
            return []


# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

def get_all_available_lots() -> List[Dict[str, Any]]:
    """
    Возвращает ВСЕ доступные лоты (348 шт).
    Сортировка: корпус → этаж → код.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section
        FROM units
        ORDER BY building, floor, code
    """)
    
    columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
               'layout_url', 'block_section']
    lots = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return lots


def get_lots_by_building(building: int) -> List[Dict[str, Any]]:
    """
    Возвращает лоты по номеру корпуса.
    building: 1 или 2
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section
        FROM units
        WHERE building = ?
        ORDER BY floor, code
    """, (building,))
    
    columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
               'layout_url', 'block_section']
    lots = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return lots


def get_lots_by_floor(building: int, floor: int) -> List[Dict[str, Any]]:
    """
    Возвращает лоты по корпусу и этажу.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section
        FROM units
        WHERE building = ? AND floor = ?
        ORDER BY area_m2, price_rub
    """, (building, floor))
    
    columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
               'layout_url', 'block_section']
    lots = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return lots


def get_lots_filtered(
    building: Optional[int] = None,
    floors: Optional[List[int]] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    limit: int = None
) -> List[Dict[str, Any]]:
    """
    Универсальный фильтр лотов.
    
    Параметры:
        building: номер корпуса (1 или 2)
        floors: список этажей [1, 2, 3] или None для всех
        min_price, max_price: диапазон цены в рублях
        min_area, max_area: диапазон площади в м²
        limit: максимум записей
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section
        FROM units
        WHERE 1=1
    """
    params = []
    
    hidden = get_hidden_buildings()
    if hidden:
        placeholders = ",".join("?" * len(hidden))
        query += f" AND building NOT IN ({placeholders})"
        params.extend(hidden)
    
    if building is not None:
        query += " AND building = ?"
        params.append(building)
    
    if floors:
        placeholders = ",".join("?" * len(floors))
        query += f" AND floor IN ({placeholders})"
        params.extend(floors)
    
    if min_price is not None:
        query += " AND price_rub >= ?"
        params.append(min_price)
    
    if max_price is not None:
        query += " AND price_rub <= ?"
        params.append(max_price)
    
    if min_area is not None:
        query += " AND area_m2 >= ?"
        params.append(min_area)
    
    if max_area is not None:
        query += " AND area_m2 <= ?"
        params.append(max_area)
    
    query += " ORDER BY price_rub, area_m2"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query, params)
    
    columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
               'layout_url', 'block_section']
    lots = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return lots


def get_lot_by_code(code: str, building: int = None) -> Optional[Dict[str, Any]]:
    """
    Находит лот по коду.
    Учитывает кириллицу/латиницу автоматически.
    
    Параметры:
        code: код лота (В708, A101 и т.д.)
        building: номер корпуса (1 или 2), если нужен конкретный
    """
    code_cyr, code_lat = normalize_code(code)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if building is not None:
        cursor.execute("""
            SELECT code, building, floor, rooms, area_m2, price_rub, 
                   layout_url, block_section
            FROM units
            WHERE (code = ? OR code = ?) AND building = ?
            LIMIT 1
        """, (code_cyr, code_lat, building))
    else:
        cursor.execute("""
            SELECT code, building, floor, rooms, area_m2, price_rub, 
                   layout_url, block_section
            FROM units
            WHERE code = ? OR code = ?
            LIMIT 1
        """, (code_cyr, code_lat))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
                   'layout_url', 'block_section']
        return dict(zip(columns, row))
    
    # Fallback: Корпус 3 (данные в corp3_units.json, не в properties.db)
    if building == 3 or building is None:
        try:
            from handlers.corp3 import get_unit_by_code as corp3_get
            c3 = corp3_get(code)
            if c3:
                return {
                    'code': c3['code'], 'building': 3, 'floor': c3['floor'],
                    'rooms': c3['rooms'], 'area': c3['area'], 'price': c3['price'],
                    'layout_url': c3.get('layout_path', ''), 'block_section': ''
                }
        except Exception:
            pass
    
    return None


def get_lots_by_code(code: str) -> List[Dict[str, Any]]:
    """
    Находит ВСЕ лоты по коду (может быть в нескольких корпусах).
    Возвращает список лотов.
    """
    code_cyr, code_lat = normalize_code(code)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section
        FROM units
        WHERE code = ? OR code = ?
        ORDER BY building
    """, (code_cyr, code_lat))
    
    rows = cursor.fetchall()
    conn.close()
    
    columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
               'layout_url', 'block_section']
    hidden = get_hidden_buildings()
    return [dict(zip(columns, row)) for row in rows if row[1] not in hidden]


def get_lot_by_area(area: float, tolerance: float = 0.05) -> Optional[Dict[str, Any]]:
    """
    Находит лот по площади (с допуском).
    Возвращает первый найденный.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section
        FROM units
        WHERE ABS(area_m2 - ?) < ?
        ORDER BY price_rub
        LIMIT 1
    """, (area, tolerance))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
                   'layout_url', 'block_section']
        return dict(zip(columns, row))
    
    return None


# ==================== СТАТИСТИКА И НАВИГАЦИЯ ====================

def get_available_floors(building: int) -> List[Dict[str, Any]]:
    """
    Возвращает список этажей корпуса с количеством лотов.
    
    Returns:
        [{"floor": 1, "count": 12, "min_price": 15000000}, ...]
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT floor, COUNT(*) as count, MIN(price_rub) as min_price
        FROM units
        WHERE building = ?
        GROUP BY floor
        ORDER BY floor
    """, (building,))
    
    floors = [{"floor": row[0], "count": row[1], "min_price": row[2]} 
              for row in cursor.fetchall()]
    conn.close()
    
    return floors


def get_building_stats() -> List[Dict[str, Any]]:
    """
    Возвращает статистику по корпусам.
    
    Returns:
        [{"building": 1, "name": "Family", "count": 180, "min_price": ..., "floors": [1,2,..]}, ...]
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            building,
            COUNT(*) as count,
            MIN(price_rub) as min_price,
            MAX(price_rub) as max_price,
            MIN(area_m2) as min_area,
            MAX(area_m2) as max_area,
            MIN(floor) as min_floor,
            MAX(floor) as max_floor
        FROM units
        WHERE status='available'
        GROUP BY building
        ORDER BY building
    """)
    
    # Названия корпусов (из block_section логики)
    building_names = {
        1: "Family",
        2: "Business"
    }
    
    stats = []
    for row in cursor.fetchall():
        stats.append({
            "building": row[0],
            "name": building_names.get(row[0], f"Корпус {row[0]}"),
            "count": row[1],
            "min_price": row[2],
            "max_price": row[3],
            "min_area": row[4],
            "max_area": row[5],
            "floors": list(range(row[6], row[7] + 1))
        })
    
    conn.close()
    hidden = get_hidden_buildings()
    return [s for s in stats if s["building"] not in hidden]


def get_stats() -> Dict[str, Any]:
    """
    Возвращает общую статистику по БД.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT area_m2) as unique_areas,
            MIN(price_rub) as min_price,
            MAX(price_rub) as max_price,
            MIN(area_m2) as min_area,
            MAX(area_m2) as max_area
        FROM units
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        'total_lots': row[0],
        'unique_areas': row[1],
        'min_price': row[2],
        'max_price': row[3],
        'min_area': row[4],
        'max_area': row[5],
    }


# ==================== LEGACY: для совместимости ====================

def get_unique_lots() -> List[Dict[str, Any]]:
    """
    LEGACY: Возвращает уникальные типы лотов (по площади).
    Оставлено для обратной совместимости.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            u.code,
            u.building,
            u.floor,
            u.rooms,
            u.area_m2,
            u.price_rub,
            u.layout_url,
            u.block_section
        FROM units u
        INNER JOIN (
            SELECT area_m2, MIN(price_rub) as min_price
            FROM units
            GROUP BY area_m2
        ) grouped ON u.area_m2 = grouped.area_m2 AND u.price_rub = grouped.min_price
        GROUP BY u.area_m2
        ORDER BY u.area_m2, u.price_rub
    """)
    
    columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 'layout_url', 'block_section']
    lots = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return lots


def get_lots_by_area(min_area: float, max_area: float) -> List[Dict[str, Any]]:
    """LEGACY: Возвращает все лоты по диапазону площади."""
    return get_lots_filtered(min_area=min_area, max_area=max_area)


def get_lots_by_budget(min_budget: int, max_budget: int) -> List[Dict[str, Any]]:
    """LEGACY: Возвращает все лоты по диапазону бюджета."""
    return get_lots_filtered(min_price=min_budget, max_price=max_budget)


# ==================== УТИЛИТЫ ====================

def format_price_short(price: int) -> str:
    """Форматирует цену: 15.2 млн"""
    return f"{price / 1_000_000:.1f} млн"


def format_price_full(price: int) -> str:
    """Форматирует цену: 15 250 000 ₽"""
    return f"{price:,}".replace(",", " ") + " ₽"


def get_building_name(building: int) -> str:
    """Возвращает название корпуса."""
    names = {1: "Family", 2: "Business"}
    return names.get(building, f"Корпус {building}")


# ==================== ТЕСТ ====================

if __name__ == "__main__":
    print("=== Тест units_db.py v2.1.0 ===\n")
    
    # Общая статистика
    stats = get_stats()
    print(f"📊 Общая статистика:")
    print(f"   Всего лотов: {stats['total_lots']}")
    print(f"   Уникальных площадей: {stats['unique_areas']}")
    print(f"   Цены: {format_price_short(stats['min_price'])} — {format_price_short(stats['max_price'])}")
    print(f"   Площади: {stats['min_area']} — {stats['max_area']} м²")
    print()
    
    # По корпусам
    building_stats = get_building_stats()
    print("🏢 По корпусам:")
    for bs in building_stats:
        print(f"   Корпус {bs['building']} ({bs['name']}): {bs['count']} лотов, этажи {bs['floors'][0]}-{bs['floors'][-1]}")
    print()
    
    # Тест фильтра
    print("🔍 Тест фильтра (корпус 1, этажи 7-9, до 30 млн):")
    lots = get_lots_filtered(building=1, floors=[7, 8, 9], max_price=30_000_000, limit=5)
    for lot in lots:
        print(f"   {lot['code']}: {lot['area']} м², {lot['floor']} эт., {format_price_short(lot['price'])}")
    print()
    
    # Тест нормализации
    print("🔤 Тест нормализации кодов:")
    test_codes = ["В708", "B708", "в708", "А101", "A101"]
    for code in test_codes:
        cyr, lat = normalize_code(code)
        print(f"   '{code}' → ('{cyr}', '{lat}')")
    print()
    
    # Тест поиска по коду
    print("🔎 Тест поиска по коду:")
    for code in ["В708", "B708"]:
        lot = get_lot_by_code(code)
        if lot:
            print(f"   '{code}' → {lot['code']}, {lot['area']} м², {format_price_short(lot['price'])}")
        else:
            print(f"   '{code}' → не найден")
