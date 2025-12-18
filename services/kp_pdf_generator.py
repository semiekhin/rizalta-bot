#!/usr/bin/env python3
"""ГЕНЕРАТОР PDF КП RIZALTA v3.1"""

import os, sqlite3, subprocess, tempfile, requests, base64
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "properties.db"
RESOURCES_DIR = BASE_DIR / "services" / "kp_resources"
SERVICE_FEE = 150_000

def load_resource(filename: str) -> str:
    path = RESOURCES_DIR / filename
    return path.read_text().strip() if path.exists() else ""

def get_lot_from_db(area: float = 0, code: str = "") -> Optional[Dict[str, Any]]:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    if code:
        code_upper = code.strip().upper()
        table = str.maketrans({"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "S", "Т": "T"})
        code_latin = code_upper.translate(table)
        cursor.execute("SELECT code, building, floor, rooms, area_m2, price_rub, layout_url, block_section FROM units WHERE code = ? OR code = ? LIMIT 1", (code_upper, code_latin))
    elif area > 0:
        cursor.execute("SELECT code, building, floor, rooms, area_m2, price_rub, layout_url, block_section FROM units WHERE ABS(area_m2 - ?) < 0.1 ORDER BY price_rub LIMIT 1", (area,))
    else:
        conn.close()
        return None
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"code": row[0], "building": row[1], "floor": row[2], "rooms": row[3], "area": row[4], "price": row[5], "layout_url": row[6], "block_section": row[7]}
    return None

def download_layout(url: str) -> str:
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    except:
        return ""

def fmt(price: int) -> str:
    return f"{price:,}".replace(",", " ") + " ₽"

def get_building_name(block_section: int) -> str:
    return '2 — "Business"' if block_section == 1 else '1 — "Family"'

def get_lot_type(area: float, rooms: int) -> str:
    if rooms == 2: return "Евро-2"
    elif area <= 26: return "Студия"
    elif area <= 35: return "1-комнатная"
    return "1-комнатная Large"

def calc_12(price: int) -> Dict:
    base = price - SERVICE_FEE
    pv_30 = int(base * 0.30)
    pv_40 = int(base * 0.40)
    pv_50 = int(base * 0.50)
    return {
        "pv_30": pv_30, "monthly_30": int((base - pv_30) / 12),
        "pv_40": pv_40, "last_40": (base - pv_40) - (200_000 * 11),
        "pv_50": pv_50, "last_50": (base - pv_50) - (100_000 * 11),
    }

def calc_24(price: int) -> Dict:
    base = price - SERVICE_FEE
    payment_12 = int(base * 0.10)
    pv_30 = int(base * 0.30)
    r30 = base - pv_30
    m30 = int(r30 * 0.12)
    pv_40 = int(base * 0.40)
    r40 = base - pv_40
    m40 = int(r40 * 0.09)
    pv_50 = int(base * 0.50)
    r50 = base - pv_50
    m50 = int(r50 * 0.06)
    return {
        "p12": payment_12,
        "pv_30": pv_30, "monthly_30": int((r30 + m30) / 24), "markup_30": m30, "final_30": price + m30,
        "pv_40": pv_40, "last_40": (r40 + m40) - (250_000 * 11) - payment_12 - (250_000 * 11), "markup_40": m40, "final_40": price + m40,
        "pv_50": pv_50, "last_50": (r50 + m50) - (150_000 * 11) - payment_12 - (150_000 * 11), "markup_50": m50, "final_50": price + m50,
    }

def generate_html(lot: Dict[str, Any], include_24m: bool = True, full_payment: bool = False) -> str:
    layout_b64 = download_layout(lot.get("layout_url", ""))
    logo_b64 = load_resource("logo_mono_trim_base64.txt")
    font_regular = load_resource("montserrat_regular_base64.txt")
    font_medium = load_resource("montserrat_medium_base64.txt")
    font_semibold = load_resource("montserrat_semibold_base64.txt")
    
    i12 = calc_12(lot["price"])
    i24 = calc_24(lot["price"]) if include_24m else {}
    bname = get_building_name(lot.get("block_section", 2))
    ltype = get_lot_type(lot["area"], lot.get("rooms", 1))
    ppm2 = int(lot["price"] / lot["area"])

    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_regular}) format('truetype'); font-weight: 400; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_medium}) format('truetype'); font-weight: 500; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_semibold}) format('truetype'); font-weight: 600; }}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Montserrat', Arial, sans-serif; background: #F6F0E3; color: #313D20; font-size: 15px; line-height: 1.4; }}

.header-table {{ width: 100%; height: 160px; background: #313D20; }}
.header-table td {{ text-align: center; vertical-align: middle; }}
.logo-header {{ height: 120px; }}

.title-bar {{ background: #DCB764; padding: 14px 40px; overflow: hidden; }}
.title-left {{ float: left; font-size: 20px; font-weight: 500; color: #313D20; }}
.title-right {{ float: right; font-size: 15px; font-weight: 500; color: #313D20; line-height: 26px; }}

.main {{ padding: 25px 40px; }}
.unit-card {{ background: white; }}

.unit-header {{ background: #313D20; padding: 16px 25px; overflow: hidden; }}
.unit-code {{ float: left; font-size: 24px; font-weight: 500; color: #F6F0E3; }}
.unit-price {{ float: right; font-size: 28px; font-weight: 600; color: #DCB764; }}

.unit-body {{ background: white; padding: 22px 25px; overflow: hidden; }}
.unit-image {{ float: left; width: 380px; }}
.unit-image-full {{ width: 100%; margin-bottom: 25px; text-align: center; }}
.unit-image-full img {{ max-width: 500px; max-height: 450px; }}
.unit-details-full {{ margin-left: 0; font-size: 17px; }}
.unit-details-full .detail-table td {{ padding: 15px 0; }}
.unit-details-full .detail-label {{ font-size: 17px; }}
.unit-details-full .detail-value {{ font-size: 17px; }}
.unit-image img {{ width: 100%; display: block; }}
.unit-details {{ margin-left: 410px; }}

.detail-table {{ width: 100%; border-collapse: collapse; }}
.detail-table td {{ padding: 12px 0; border-bottom: 1px solid rgba(49, 61, 32, 0.15); }}
.detail-label {{ color: #313D20; font-size: 15px; }}
.detail-value {{ text-align: right; font-weight: 600; font-size: 15px; }}

.installment-section {{ padding: 22px 25px; background: #F6F0E3; }}
.installment-section-24 {{ padding-top: 8px; }}
.installment-title {{ font-size: 22px; font-weight: 500; margin-bottom: 18px; color: #313D20; }}

.options-table {{ width: 100%; border-collapse: collapse; }}
.option-card {{ background: white; border: 2px solid #313D20; padding: 18px; text-align: center; vertical-align: top; }}
.option-card-mid {{ border-left: none; border-right: none; }}
.option-card-24 {{ background: white; border: 2px solid #DCB764; padding: 18px; text-align: center; vertical-align: top; }}
.option-card-24-mid {{ border-left: none; border-right: none; }}

.option-pv {{ font-size: 14px; color: #313D20; margin-bottom: 10px; font-weight: 500; }}
.option-badge {{ display: inline-block; background: #DCB764; color: #313D20; font-size: 11px; font-weight: 600; padding: 3px 7px; margin-left: 6px; }}
.option-amount {{ font-size: 22px; font-weight: 600; color: #313D20; margin-bottom: 14px; }}
.option-monthly {{ font-size: 14px; color: #313D20; line-height: 1.6; font-weight: 500; }}
.option-total {{ font-size: 13px; color: #313D20; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(49, 61, 32, 0.15); }}
.option-total-sum {{ font-size: 15px; font-weight: 600; color: #DCB764; margin-top: 4px; }}

.footer {{ background: #313D20; text-align: center; padding: 22px; }}
.footer-text {{ font-size: 13px; color: #F6F0E3; letter-spacing: 4px; }}
</style>
</head>
<body>

<table class="header-table"><tr><td>
{"<img class='logo-header' src='data:image/png;base64," + logo_b64 + "'>" if logo_b64 else ""}
</td></tr></table>

<div class="title-bar">
<div class="title-left">Коммерческое предложение</div>
<div class="title-right">Корпус {bname} • {lot["floor"]} этаж • {lot["area"]} м²</div>
<div style="clear:both"></div>
</div>

<div class="main">
<div class="unit-card">

<div class="unit-header">
<div class="unit-code">Гостиничный номер, {lot["code"]}</div>
<div class="unit-price">{fmt(lot["price"])}</div>
<div style="clear:both"></div>
</div>

<div class="unit-body">
<div class="{'unit-image-full' if full_payment else 'unit-image'}">
{"<img src='data:image/jpeg;base64," + layout_b64 + "'>" if layout_b64 else ""}
</div>
<div class="{'unit-details-full' if full_payment else 'unit-details'}">
<table class="detail-table">
<tr><td class="detail-label">Корпус</td><td class="detail-value">{bname}</td></tr>
<tr><td class="detail-label">Этаж</td><td class="detail-value">{lot["floor"]}</td></tr>
<tr><td class="detail-label">Площадь</td><td class="detail-value">{lot["area"]} м²</td></tr>
<tr><td class="detail-label">Комнат</td><td class="detail-value">{ltype}</td></tr>
<tr><td class="detail-label">Сдача</td><td class="detail-value">4 кв. 2027</td></tr>
<tr><td class="detail-label">Цена за м²</td><td class="detail-value">{fmt(ppm2)}</td></tr>
</table>
<div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
<span style="color: #666; font-size: 14px;">Базовая стоимость</span>
<span style="font-size: 14px; color: #666;">{fmt(lot["price"])}</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="color: #313D20; font-size: 15px; font-weight: 500;">При 100% оплате <span style="color: #4a7c23;">(–5%)</span></span>
<span style="font-weight: 700; font-size: 20px; color: #4a7c23;">{fmt(int(lot["price"] * 0.95))}</span>
</div>
</div>
</div>
<div style="clear:both"></div>
</div>

'''

    if not full_payment:
        html += f'''<div class="installment-section">
<div class="installment-title">Рассрочка 0% на 12 месяцев</div>
<table class="options-table"><tr>
<td class="option-card">
<div class="option-pv">Первый взнос 30%</div>
<div class="option-amount">{fmt(i12["pv_30"])}</div>
<div class="option-monthly">Ежемесячно:<br>{fmt(i12["monthly_30"])}</div>
</td>
<td class="option-card option-card-mid">
<div class="option-pv">Первый взнос 40%</div>
<div class="option-amount">{fmt(i12["pv_40"])}</div>
<div class="option-monthly">11 мес. × 200 000 ₽<br>12-й: {fmt(i12["last_40"])}</div>
</td>
<td class="option-card">
<div class="option-pv">Первый взнос 50%</div>
<div class="option-amount">{fmt(i12["pv_50"])}</div>
<div class="option-monthly">11 мес. × 100 000 ₽<br>12-й: {fmt(i12["last_50"])}</div>
</td>
</tr></table>
</div>'''

    if include_24m and not full_payment:
        html += f'''
<div class="installment-section installment-section-24">
<div class="installment-title">Рассрочка на 24 месяца</div>
<table class="options-table"><tr>
<td class="option-card-24">
<div class="option-pv">Первый взнос 30% <span class="option-badge">+12%</span></div>
<div class="option-amount">{fmt(i24["pv_30"])}</div>
<div class="option-monthly">24 мес. × {fmt(i24["monthly_30"])}</div>
<div class="option-total">Удорожание: +{fmt(i24["markup_30"])}<div class="option-total-sum">Итого: {fmt(i24["final_30"])}</div></div>
</td>
<td class="option-card-24 option-card-24-mid">
<div class="option-pv">Первый взнос 40% <span class="option-badge">+9%</span></div>
<div class="option-amount">{fmt(i24["pv_40"])}</div>
<div class="option-monthly">11 мес. × 250 000 ₽<br>12-й: {fmt(i24["p12"])}<br>11 мес. × 250 000 ₽<br>24-й: {fmt(i24["last_40"])}</div>
<div class="option-total">Удорожание: +{fmt(i24["markup_40"])}<div class="option-total-sum">Итого: {fmt(i24["final_40"])}</div></div>
</td>
<td class="option-card-24">
<div class="option-pv">Первый взнос 50% <span class="option-badge">+6%</span></div>
<div class="option-amount">{fmt(i24["pv_50"])}</div>
<div class="option-monthly">11 мес. × 150 000 ₽<br>12-й: {fmt(i24["p12"])}<br>11 мес. × 150 000 ₽<br>24-й: {fmt(i24["last_50"])}</div>
<div class="option-total">Удорожание: +{fmt(i24["markup_50"])}<div class="option-total-sum">Итого: {fmt(i24["final_50"])}</div></div>
</td>
</tr></table>
</div>'''

    html += '''
</div>
</div>

<div class="footer">
<div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div>
</div>

</body></html>'''
    return html

def generate_kp_pdf(area: float = 0, code: str = "", include_24m: bool = True, full_payment: bool = False, output_dir: str = None) -> Optional[str]:
    lot = get_lot_from_db(area=area, code=code)
    if not lot:
        print(f"[KP PDF] Лот не найден: area={area}, code={code}")
        return None
    print(f"[KP PDF] Генерируем КП для {lot['code']} ({lot['area']} м²)")
    html = generate_html(lot, include_24m=include_24m, full_payment=full_payment)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        html_path = f.name
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    suffix = "_100" if full_payment else ("_12m_24m" if include_24m else "_12m")
    pdf_path = os.path.join(output_dir, f"KP_{lot['code']}{suffix}.pdf")
    try:
        cmd = ['wkhtmltopdf', '--page-size', 'A4', '--orientation', 'Portrait', '--margin-top', '0', '--margin-bottom', '0', '--margin-left', '0', '--margin-right', '0', '--enable-local-file-access', '--disable-smart-shrinking', '--quiet', html_path, pdf_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[KP PDF] Ошибка: {result.stderr}")
            return None
        print(f"[KP PDF] ✅ Создан: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"[KP PDF] Ошибка: {e}")
        return None
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)

if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "В101"
    generate_kp_pdf(code=code, include_24m=True, output_dir="/tmp")
