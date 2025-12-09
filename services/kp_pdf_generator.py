#!/usr/bin/env python3
"""
ГЕНЕРАТОР PDF КП RIZALTA
Использует системный шрифт Montserrat + wkhtmltopdf
"""

import os
import sqlite3
import subprocess
import tempfile
import requests
import base64
from pathlib import Path
from typing import Dict, Any, Optional

# === ПУТИ ===
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "properties.db"
LOGO_PATH = BASE_DIR / "services" / "logo_rizalta.png"

# === КОНСТАНТЫ ===
SERVICE_FEE = 150_000

# === ЦВЕТА ===
COLORS = {
    "forest": "#313D20",
    "gold": "#DCB764",
    "ivory": "#F6F0E3",
    "white": "#FFFFFF",
    "text": "#333333",
}


def get_lot_from_db(area: float = 0, code: str = "") -> Optional[Dict[str, Any]]:
    """Получает данные лота из БД."""
    if not DB_PATH.exists():
        return None
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    if area > 0:
        cursor.execute("""
            SELECT code, building, floor, rooms, area_m2, price_rub, layout_url, block_section
            FROM units WHERE ABS(area_m2 - ?) < 0.1
            ORDER BY price_rub LIMIT 1
        """, (area,))
    elif code:
        code_upper = code.strip().upper()
        table = str.maketrans({"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "S", "Т": "T"})
        code_latin = code_upper.translate(table)
        cursor.execute("""
            SELECT code, building, floor, rooms, area_m2, price_rub, layout_url, block_section
            FROM units WHERE code = ? OR code = ? LIMIT 1
        """, (code_upper, code_latin))
    else:
        conn.close()
        return None
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "code": row[0], "building": row[1], "floor": row[2], "rooms": row[3],
            "area": row[4], "price": row[5], "layout_url": row[6], "block_section": row[7],
        }
    return None


def download_layout(url: str) -> str:
    """Скачивает планировку и возвращает base64."""
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    except Exception as e:
        print(f"[KP PDF] Ошибка скачивания планировки: {e}")
        return ""


def format_price(price: int) -> str:
    return f"{price:,}".replace(",", " ") + " ₽"


def get_building_name(building: int) -> str:
    return 'Корпус 1 — "Family"' if building == 1 else 'Корпус 2 — "Business"'


def get_lot_type(area: float, rooms: int) -> str:
    if rooms == 2:
        return "Евро-2"
    elif area <= 26:
        return "Студия"
    elif area <= 35:
        return "1-комнатная"
    else:
        return "1-комнатная Large"


def calc_installment_12(price: int) -> Dict[str, Any]:
    base = price - SERVICE_FEE
    pv_30 = int(base * 0.30)
    monthly_30 = int((base - pv_30) / 12)
    pv_40 = int(base * 0.40)
    last_40 = (base - pv_40) - (200_000 * 11)
    pv_50 = int(base * 0.50)
    last_50 = (base - pv_50) - (100_000 * 11)
    return {"pv_30": pv_30, "monthly_30": monthly_30, "pv_40": pv_40, "last_40": last_40, "pv_50": pv_50, "last_50": last_50}


def calc_installment_24(price: int) -> Dict[str, Any]:
    base = price - SERVICE_FEE
    payment_12 = int(base * 0.10)
    
    pv_30 = int(base * 0.30)
    remaining_30 = base - pv_30
    markup_30 = int(remaining_30 * 0.12)
    monthly_30 = int((remaining_30 + markup_30) / 24)
    final_30 = price + markup_30
    
    pv_40 = int(base * 0.40)
    remaining_40 = base - pv_40
    markup_40 = int(remaining_40 * 0.09)
    paid_40 = (250_000 * 11) + payment_12 + (250_000 * 11)
    last_40 = (remaining_40 + markup_40) - paid_40
    final_40 = price + markup_40
    
    pv_50 = int(base * 0.50)
    remaining_50 = base - pv_50
    markup_50 = int(remaining_50 * 0.06)
    paid_50 = (150_000 * 11) + payment_12 + (150_000 * 11)
    last_50 = (remaining_50 + markup_50) - paid_50
    final_50 = price + markup_50
    
    return {
        "payment_12": payment_12,
        "pv_30": pv_30, "monthly_30": monthly_30, "markup_30": markup_30, "final_30": final_30,
        "pv_40": pv_40, "last_40": last_40, "markup_40": markup_40, "final_40": final_40,
        "pv_50": pv_50, "last_50": last_50, "markup_50": markup_50, "final_50": final_50,
    }


def generate_html(lot: Dict[str, Any], include_24m: bool = True) -> str:
    layout_b64 = download_layout(lot.get("layout_url", ""))
    logo_b64 = ""
    if LOGO_PATH.exists():
        logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    
    inst_12 = calc_installment_12(lot["price"])
    inst_24 = calc_installment_24(lot["price"]) if include_24m else {}
    building_name = get_building_name(lot["building"])
    lot_type = get_lot_type(lot["area"], lot.get("rooms", 1))
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Montserrat', sans-serif; font-size: 11px; color: {COLORS["text"]}; background: {COLORS["white"]}; }}
        .header {{ background: {COLORS["forest"]}; height: 80px; text-align: center; padding-top: 15px; }}
        .logo {{ height: 50px; }}
        .title-bar {{ background: {COLORS["gold"]}; padding: 10px 25px; overflow: hidden; }}
        .title-left {{ float: left; font-weight: 600; font-size: 13px; color: {COLORS["forest"]}; }}
        .title-right {{ float: right; font-size: 11px; color: {COLORS["forest"]}; }}
        .main {{ padding: 20px 25px; }}
        .unit-card {{ border: 1px solid #ddd; margin-bottom: 15px; }}
        .unit-header {{ background: {COLORS["forest"]}; color: {COLORS["white"]}; padding: 10px 15px; overflow: hidden; }}
        .unit-code {{ float: left; font-weight: 600; font-size: 14px; }}
        .unit-price {{ float: right; font-weight: 600; font-size: 14px; color: {COLORS["gold"]}; }}
        .unit-body {{ padding: 15px; overflow: hidden; }}
        .unit-layout {{ float: left; width: 40%; }}
        .unit-layout img {{ max-width: 100%; max-height: 180px; }}
        .unit-details {{ float: right; width: 55%; }}
        .detail-row {{ padding: 6px 0; border-bottom: 1px solid #eee; }}
        .detail-label {{ color: #666; font-size: 9px; }}
        .detail-value {{ font-weight: 500; font-size: 11px; }}
        .installment-section {{ background: {COLORS["ivory"]}; padding: 12px 15px; margin-top: 10px; }}
        .installment-title {{ font-weight: 600; font-size: 11px; color: {COLORS["forest"]}; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid {COLORS["forest"]}; }}
        .installment-title.gold {{ border-bottom-color: {COLORS["gold"]}; }}
        .inst-cards {{ overflow: hidden; }}
        .inst-card {{ float: left; width: 32%; margin-right: 2%; padding: 8px; border: 1px solid {COLORS["forest"]}; background: {COLORS["white"]}; }}
        .inst-card:last-child {{ margin-right: 0; }}
        .inst-card.gold {{ border-color: {COLORS["gold"]}; }}
        .inst-card-title {{ font-weight: 600; font-size: 10px; color: {COLORS["forest"]}; margin-bottom: 5px; }}
        .inst-card-pv {{ font-size: 12px; font-weight: 600; color: {COLORS["forest"]}; margin-bottom: 3px; }}
        .inst-card-monthly {{ font-size: 9px; color: #666; line-height: 1.3; }}
        .badge {{ display: inline-block; background: #dc2626; color: white; font-size: 8px; padding: 1px 4px; border-radius: 2px; margin-left: 3px; }}
        .inst-total {{ margin-top: 5px; padding-top: 5px; border-top: 1px solid #ddd; font-size: 9px; color: {COLORS["gold"]}; }}
        .footer {{ background: {COLORS["forest"]}; color: {COLORS["white"]}; text-align: center; padding: 12px; font-size: 9px; letter-spacing: 2px; position: fixed; bottom: 0; width: 100%; }}
        .note {{ font-size: 8px; color: #888; margin-top: 8px; font-style: italic; }}
        .clearfix {{ clear: both; }}
    </style>
</head>
<body>

<div class="header">
    {"<img class='logo' src='data:image/png;base64," + logo_b64 + "' alt='RIZALTA'>" if logo_b64 else "<h1 style='color:white;padding-top:10px'>RIZALTA</h1>"}
</div>

<div class="title-bar">
    <div class="title-left">Коммерческое предложение</div>
    <div class="title-right">{building_name} • {lot["floor"]} этаж • {lot["area"]} м²</div>
    <div class="clearfix"></div>
</div>

<div class="main">
    <div class="unit-card">
        <div class="unit-header">
            <div class="unit-code">{lot_type} • {lot["code"]}</div>
            <div class="unit-price">{format_price(lot["price"])}</div>
            <div class="clearfix"></div>
        </div>
        <div class="unit-body">
            <div class="unit-layout">
                {"<img src='data:image/jpeg;base64," + layout_b64 + "' alt='Планировка'>" if layout_b64 else "<p style='color:#999'>Планировка</p>"}
            </div>
            <div class="unit-details">
                <div class="detail-row"><div class="detail-label">Площадь</div><div class="detail-value">{lot["area"]} м²</div></div>
                <div class="detail-row"><div class="detail-label">Этаж</div><div class="detail-value">{lot["floor"]}</div></div>
                <div class="detail-row"><div class="detail-label">Корпус</div><div class="detail-value">{building_name}</div></div>
                <div class="detail-row"><div class="detail-label">Срок сдачи</div><div class="detail-value">4 кв. 2027</div></div>
                <div class="detail-row"><div class="detail-label">Цена за м²</div><div class="detail-value">{format_price(int(lot["price"] / lot["area"]))}</div></div>
            </div>
            <div class="clearfix"></div>
        </div>
        
        <div class="installment-section">
            <div class="installment-title">Рассрочка 0% на 12 месяцев</div>
            <div class="inst-cards">
                <div class="inst-card">
                    <div class="inst-card-title">ПВ 30%</div>
                    <div class="inst-card-pv">{format_price(inst_12["pv_30"])}</div>
                    <div class="inst-card-monthly">12 мес × {format_price(inst_12["monthly_30"])}</div>
                </div>
                <div class="inst-card">
                    <div class="inst-card-title">ПВ 40%</div>
                    <div class="inst-card-pv">{format_price(inst_12["pv_40"])}</div>
                    <div class="inst-card-monthly">11 мес × 200 000 ₽<br>12-й: {format_price(inst_12["last_40"])}</div>
                </div>
                <div class="inst-card">
                    <div class="inst-card-title">ПВ 50%</div>
                    <div class="inst-card-pv">{format_price(inst_12["pv_50"])}</div>
                    <div class="inst-card-monthly">11 мес × 100 000 ₽<br>12-й: {format_price(inst_12["last_50"])}</div>
                </div>
            </div>
            <div class="clearfix"></div>
        </div>'''
    
    if include_24m:
        html += f'''
        <div class="installment-section">
            <div class="installment-title gold">Рассрочка на 24 месяца</div>
            <div class="inst-cards">
                <div class="inst-card gold">
                    <div class="inst-card-title">ПВ 30% <span class="badge">+12%</span></div>
                    <div class="inst-card-pv">{format_price(inst_24["pv_30"])}</div>
                    <div class="inst-card-monthly">24 мес × {format_price(inst_24["monthly_30"])}</div>
                    <div class="inst-total">Итого: {format_price(inst_24["final_30"])}</div>
                </div>
                <div class="inst-card gold">
                    <div class="inst-card-title">ПВ 40% <span class="badge">+9%</span></div>
                    <div class="inst-card-pv">{format_price(inst_24["pv_40"])}</div>
                    <div class="inst-card-monthly">11×250К + 12-й:{format_price(inst_24["payment_12"])}<br>11×250К + 24-й:{format_price(inst_24["last_40"])}</div>
                    <div class="inst-total">Итого: {format_price(inst_24["final_40"])}</div>
                </div>
                <div class="inst-card gold">
                    <div class="inst-card-title">ПВ 50% <span class="badge">+6%</span></div>
                    <div class="inst-card-pv">{format_price(inst_24["pv_50"])}</div>
                    <div class="inst-card-monthly">11×150К + 12-й:{format_price(inst_24["payment_12"])}<br>11×150К + 24-й:{format_price(inst_24["last_50"])}</div>
                    <div class="inst-total">Итого: {format_price(inst_24["final_50"])}</div>
                </div>
            </div>
            <div class="clearfix"></div>
        </div>'''
    
    html += f'''
        <div class="note">* Расчёт с учётом вычета {format_price(SERVICE_FEE)}</div>
    </div>
</div>

<div class="footer">RIZALTA RESORT BELOKURIKHA</div>

</body>
</html>'''
    
    return html


def generate_kp_pdf(area: float = 0, code: str = "", include_24m: bool = True, output_dir: str = None) -> Optional[str]:
    lot = get_lot_from_db(area=area, code=code)
    if not lot:
        print(f"[KP PDF] Лот не найден: area={area}, code={code}")
        return None
    
    print(f"[KP PDF] Генерируем КП для {lot['code']} ({lot['area']} м²)")
    
    html = generate_html(lot, include_24m=include_24m)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        html_path = f.name
    
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    
    suffix = "_12m_24m" if include_24m else "_12m"
    pdf_filename = f"KP_{lot['code']}{suffix}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    
    try:
        cmd = ['wkhtmltopdf', '--page-size', 'A4', '--orientation', 'Portrait',
               '--margin-top', '0', '--margin-bottom', '0', '--margin-left', '0', '--margin-right', '0',
               '--enable-local-file-access', '--quiet', html_path, pdf_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"[KP PDF] Ошибка wkhtmltopdf: {result.stderr}")
            return None
        
        print(f"[KP PDF] ✅ Создан: {pdf_path}")
        return pdf_path
        
    except subprocess.TimeoutExpired:
        print("[KP PDF] Таймаут генерации PDF")
        return None
    except Exception as e:
        print(f"[KP PDF] Ошибка: {e}")
        return None
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("python kp_pdf_generator.py --area 22.0")
        print("python kp_pdf_generator.py --code В227")
        sys.exit(1)
    
    area = 0
    code = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--area" and i + 1 < len(sys.argv):
            area = float(sys.argv[i + 1])
        elif arg == "--code" and i + 1 < len(sys.argv):
            code = sys.argv[i + 1]
    
    if area > 0 or code:
        pdf = generate_kp_pdf(area=area, code=code)
        print(f"Результат: {pdf}" if pdf else "Ошибка")
