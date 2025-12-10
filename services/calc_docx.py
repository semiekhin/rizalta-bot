#!/usr/bin/env python3
"""Генератор DOCX для инвестиционных расчётов"""

import json
import subprocess
import tempfile
import sqlite3
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "properties.db"

def get_lot_from_db(code: str) -> Optional[Dict]:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    code_upper = code.strip().upper()
    table = str.maketrans({"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "S", "Т": "T"})
    code_latin = code_upper.translate(table)
    cursor.execute("SELECT code, area_m2, price_rub FROM units WHERE code = ? OR code = ? LIMIT 1", (code_upper, code_latin))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"code": row[0], "area": row[1], "price": row[2], "price_m2": int(row[2] / row[1])}
    return None

def generate_roi_docx(unit_code: str, output_dir: str = None) -> Optional[str]:
    lot = get_lot_from_db(unit_code)
    if not lot:
        print(f"[DOCX] Лот {unit_code} не найден")
        return None
    
    # Используем инвестиционный калькулятор
    from services.investment_calc import calculate_investment
    calc = calculate_investment(lot['area'], lot['price_m2'])
    
    def fmt(v): return f"{v:,}".replace(",", " ")
    
    # Ключевые годы для таблицы
    key_years = []
    for y in calc['years']:
        key_years.append({
            "year": str(y['year']),
            "rental": fmt(y['rental_profit']) + " ₽" if y['rental_profit'] > 0 else "—",
            "growth": fmt(y['growth_profit']) + " ₽",
            "total_pct": f"{y['total_pct']:.1f}%"
        })
    
    data = {
        "title": f"Лот {lot['code']} ({lot['area']} м²)",
        "area": f"{lot['area']} м²",
        "price": fmt(calc['cost']) + " ₽",
        "price_m2": fmt(lot['price_m2']) + " ₽",
        "years": key_years,
        "total_rental": fmt(calc['total_rental']) + " ₽",
        "total_growth": fmt(calc['total_growth']) + " ₽",
        "total_profit": fmt(calc['total_profit']) + " ₽",
        "roi_pct": f"{calc['roi_pct']:.0f}%",
        "avg_annual_pct": f"{calc['avg_annual_pct']:.1f}%",
        "final_value": fmt(calc['final_value']) + " ₽"
    }
    
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    
    output_path = Path(output_dir) / f"ROI_{lot['code']}.docx"
    script_path = BASE_DIR / "services" / "calc_docx_generator.js"
    
    try:
        cmd = ["node", str(script_path), json.dumps(data), str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(BASE_DIR))
        if result.returncode != 0:
            print(f"[DOCX] Ошибка: {result.stderr}")
            return None
        print(f"[DOCX] ✅ Создан: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"[DOCX] Ошибка: {e}")
        return None

if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "В200"
    generate_roi_docx(code, "/tmp")
