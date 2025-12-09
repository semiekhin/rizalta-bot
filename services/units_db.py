"""
Сервис для работы с лотами из properties.db.
Единый источник данных для расчётов и КП.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

# Путь к БД
DB_PATH = Path(__file__).parent.parent / "properties.db"


def get_db_connection():
    """Возвращает соединение с БД."""
    return sqlite3.connect(str(DB_PATH))


def get_unique_lots() -> List[Dict[str, Any]]:
    """
    Возвращает 69 уникальных типов лотов (по площади).
    Для каждой уникальной площади берём один лот с минимальной ценой.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Группируем по площади, берём минимальную цену
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


def get_all_lots() -> List[Dict[str, Any]]:
    """
    Возвращает ВСЕ 369 лотов.
    Для будущей шахматки.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section, status
        FROM units
        ORDER BY building, floor, code
    """)
    
    columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
               'layout_url', 'block_section', 'status']
    lots = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return lots


def get_lots_by_area(min_area: float, max_area: float) -> List[Dict[str, Any]]:
    """
    Возвращает уникальные лоты по диапазону площади.
    """
    all_lots = get_unique_lots()
    return [lot for lot in all_lots if min_area <= lot['area'] <= max_area]


def get_lots_by_budget(min_budget: int, max_budget: int) -> List[Dict[str, Any]]:
    """
    Возвращает уникальные лоты по диапазону бюджета.
    """
    all_lots = get_unique_lots()
    return [lot for lot in all_lots if min_budget <= lot['price'] <= max_budget]


def get_lot_by_area(area: float, tolerance: float = 0.05) -> Optional[Dict[str, Any]]:
    """
    Находит лот по площади (с допуском).
    """
    all_lots = get_unique_lots()
    for lot in all_lots:
        if abs(lot['area'] - area) < tolerance:
            return lot
    return None


def get_lot_by_code(code: str) -> Optional[Dict[str, Any]]:
    """
    Находит лот по коду.
    Учитывает кириллицу/латиницу.
    """
    # Нормализация кода
    code = code.strip().upper()
    table = str.maketrans({
        "А": "A", "В": "B", "Е": "E", "К": "K",
        "М": "M", "Н": "H", "О": "O", "Р": "P",
        "С": "S", "Т": "T", "У": "Y", "Х": "X",
    })
    code_latin = code.translate(table)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Пробуем найти как есть и в латинице
    cursor.execute("""
        SELECT code, building, floor, rooms, area_m2, price_rub, 
               layout_url, block_section
        FROM units
        WHERE code = ? OR code = ?
        LIMIT 1
    """, (code, code_latin))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = ['code', 'building', 'floor', 'rooms', 'area', 'price', 
                   'layout_url', 'block_section']
        return dict(zip(columns, row))
    
    return None


def get_stats() -> Dict[str, Any]:
    """
    Возвращает статистику по БД.
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


def format_price_short(price: int) -> str:
    """Форматирует цену: 15.2 млн"""
    return f"{price / 1_000_000:.1f} млн"


# === Тест ===
if __name__ == "__main__":
    print("=== Тест units_db.py ===\n")
    
    stats = get_stats()
    print(f"📊 Статистика БД:")
    print(f"   Всего лотов: {stats['total_lots']}")
    print(f"   Уникальных площадей: {stats['unique_areas']}")
    print(f"   Цены: {format_price_short(stats['min_price'])} — {format_price_short(stats['max_price'])}")
    print(f"   Площади: {stats['min_area']} — {stats['max_area']} м²")
    print()
    
    lots = get_unique_lots()
    print(f"📦 Уникальных лотов: {len(lots)}")
    print(f"   Первые 5:")
    for lot in lots[:5]:
        print(f"   - {lot['code']}: {lot['area']} м², {format_price_short(lot['price'])}")
