"""
Обработчик Корпуса 3 (КП-only патч).

Временное решение до появления корпуса 3 на ri.rclick.ru.
Доступ только для whitelist пользователей.

v1.0.0 — 23.01.2026
"""

import json
import base64
import os
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from services.telegram import send_message, send_message_inline, send_document, send_photo_inline
import sqlite3

DB_PATH = "/opt/bot/properties.db"

# Путь к данным корпуса 3
DATA_PATH = Path(__file__).parent.parent / "data" / "corp3_units.json"

# Кеш данных
_units_cache: List[Dict[str, Any]] = []
_filter_cache: Dict[int, Dict[str, Any]] = {}  # chat_id -> {filter_type, params, units}


def load_units() -> List[Dict[str, Any]]:
    """Загружает данные корпуса 3 из JSON."""
    global _units_cache
    if _units_cache:
        return _units_cache
    
    if not DATA_PATH.exists():
        return []
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    _units_cache = [u for u in data.get("units", []) if u.get('area', 0) >= 23.5 and u.get('status') == 'available']
    return _units_cache


def is_whitelisted(chat_id: int) -> bool:
    """Проверяет, есть ли пользователь в whitelist (из БД)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM corp3_whitelist WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def fmt(price: int) -> str:
    """Форматирует цену."""
    return f"{price:,}".replace(",", " ")


def get_unit_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Находит лот по коду."""
    units = load_units()
    code_upper = code.strip().upper()
    # Нормализация: латиница ↔ кириллица
    code_cyr = code_upper.replace('A', 'А').replace('B', 'В')
    code_lat = code_upper.replace('А', 'A').replace('В', 'B')
    
    for u in units:
        if u['code'].upper() in (code_upper, code_cyr, code_lat):
            return u
    return None


def filter_units(
    rooms: Optional[int] = None,
    floor: Optional[int] = None,
    area_min: Optional[float] = None,
    area_max: Optional[float] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Фильтрует лоты по критериям."""
    units = load_units()
    result = []
    
    for u in units:
        if rooms is not None and u['rooms'] != rooms:
            continue
        if floor is not None and u['floor'] != floor:
            continue
        if area_min is not None and u['area'] < area_min:
            continue
        if area_max is not None and u['area'] > area_max:
            continue
        if price_min is not None and u['price'] < price_min:
            continue
        if price_max is not None and u['price'] > price_max:
            continue
        result.append(u)
    
    # Сортировка: этаж → код
    result.sort(key=lambda x: (x['floor'], x['code']))
    return result


def get_stats() -> Dict[str, Any]:
    """Возвращает статистику по корпусу 3."""
    units = load_units()
    if not units:
        return {"total": 0, "floors": [], "rooms": [], "price_min": 0, "price_max": 0, "area_min": 0, "area_max": 0}
    
    floors = sorted(set(u['floor'] for u in units))
    rooms = sorted(set(u['rooms'] for u in units))
    
    return {
        "total": len(units),
        "floors": floors,
        "rooms": rooms,
        "price_min": min(u['price'] for u in units),
        "price_max": max(u['price'] for u in units),
        "area_min": min(u['area'] for u in units),
        "area_max": max(u['area'] for u in units),
    }


# ==================== HANDLERS ====================

async def handle_corp3_start(chat_id: int):
    """Главное меню корпуса 3."""
    if not is_whitelisted(chat_id):
        await send_message(chat_id, "🔒 Доступ к Корпусу 3 ограничен.\n\nОбратитесь к администратору.")
        return
    
    stats = get_stats()
    
    if stats["total"] == 0:
        await send_message(chat_id, "❌ Данные Корпуса 3 не загружены.")
        return
    
    text = f"""🏢 <b>Корпус 3 — Эксклюзивный доступ</b>

📊 Доступно: <b>{stats['total']} лотов</b>
🏗 Этажи: {stats['floors'][0]}—{stats['floors'][-1]}
💰 Цены: от {fmt(stats['price_min'])} до {fmt(stats['price_max'])} ₽
📐 Площади: от {stats['area_min']} до {stats['area_max']} м²

<b>Выберите способ поиска:</b>"""

    buttons = [
        [{"text": "🏠 По комнатам", "callback_data": "c3_by_rooms"}],
        [{"text": "🏗 По этажу", "callback_data": "c3_by_floor"}],
        [{"text": "📐 По площади", "callback_data": "c3_by_area"}],
        [{"text": "🔍 По номеру лота", "callback_data": "c3_by_code"}],
        [{"text": "📋 Все 282 лота", "callback_data": "c3_all_0"}],
        [{"text": "🔙 Главное меню", "callback_data": "back_to_menu"}],
    ]
    
    await send_message_inline(chat_id, text, buttons)


async def handle_corp3_by_rooms(chat_id: int):
    """Выбор по количеству комнат."""
    if not is_whitelisted(chat_id):
        return
    
    units = load_units()
    rooms_count = {}
    for u in units:
        r = u['rooms']
        rooms_count[r] = rooms_count.get(r, 0) + 1
    
    text = "🏠 <b>Выберите количество комнат:</b>"
    
    buttons = []
    room_labels = {1: "Студии", 2: "2-комнатные", 3: "3-комнатные", 4: "4-комнатные"}
    for r in sorted(rooms_count.keys()):
        label = room_labels.get(r, f"{r}-комнатные")
        buttons.append([{"text": f"{label} ({rooms_count[r]} шт)", "callback_data": f"c3_rooms_{r}_0"}])
    
    buttons.append([{"text": "🔙 Назад", "callback_data": "c3_menu"}])
    
    await send_message_inline(chat_id, text, buttons)


async def handle_corp3_by_floor(chat_id: int):
    """Выбор по этажу."""
    if not is_whitelisted(chat_id):
        return
    
    units = load_units()
    floors_count = {}
    for u in units:
        f = u['floor']
        floors_count[f] = floors_count.get(f, 0) + 1
    
    text = "🏗 <b>Выберите этаж:</b>"
    
    buttons = []
    row = []
    for f in sorted(floors_count.keys()):
        row.append({"text": f"{f} эт. ({floors_count[f]})", "callback_data": f"c3_floor_{f}_0"})
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([{"text": "🔙 Назад", "callback_data": "c3_menu"}])
    
    await send_message_inline(chat_id, text, buttons)


async def handle_corp3_by_area(chat_id: int):
    """Выбор по диапазону площади."""
    if not is_whitelisted(chat_id):
        return
    
    text = "📐 <b>Выберите диапазон площади:</b>"
    
    buttons = [
        [{"text": "22-31 м²", "callback_data": "c3_area_22_31_0"}, {"text": "31-41 м²", "callback_data": "c3_area_31_41_0"}],
        [{"text": "41-51 м²", "callback_data": "c3_area_41_51_0"}, {"text": "51-71 м²", "callback_data": "c3_area_51_71_0"}],
        [{"text": "71-91 м²", "callback_data": "c3_area_71_91_0"}, {"text": "91+ м²", "callback_data": "c3_area_91_999_0"}],
        [{"text": "🔙 Назад", "callback_data": "c3_menu"}],
    ]
    
    await send_message_inline(chat_id, text, buttons)


async def handle_corp3_by_code(chat_id: int):
    """Запрос кода лота."""
    if not is_whitelisted(chat_id):
        return
    
    # Сохраняем состояние ожидания ввода кода
    _filter_cache[chat_id] = {"awaiting_code": True}
    
    text = """🔍 <b>Введите код лота</b>

Например: <code>А200</code>, <code>В101</code>, <code>A300</code>"""
    
    buttons = [[{"text": "🔙 Назад", "callback_data": "c3_menu"}]]
    
    await send_message_inline(chat_id, text, buttons)


async def handle_corp3_show_list(
    chat_id: int,
    units: List[Dict[str, Any]],
    title: str,
    page: int = 0,
    page_size: int = 10,
    callback_prefix: str = "c3_all"
):
    """Показывает список лотов с пагинацией."""
    if not is_whitelisted(chat_id):
        return
    
    # Сортировка по площади (возрастание)
    units = sorted(units, key=lambda u: u['area'])
    
    if not units:
        await send_message_inline(chat_id, "❌ Лоты не найдены.", [[{"text": "🔙 Назад", "callback_data": "c3_menu"}]])
        return
    
    total = len(units)
    start = page * page_size
    end = min(start + page_size, total)
    page_units = units[start:end]
    
    text = f"""📋 <b>{title}</b>

📊 Найдено: {total}
📄 Показаны: {start + 1}—{end}

<b>Выберите лот:</b>"""

    buttons = []
    for u in page_units:
        btn_text = f"{u['code']} ({u['floor']} эт.) — {u['area']} м² — {fmt(u['price'])} ₽"
        buttons.append([{"text": btn_text, "callback_data": f"c3_lot_{u['code']}"}])
    
    # Пагинация
    nav_row = []
    if page > 0:
        nav_row.append({"text": "⬅️ Назад", "callback_data": f"{callback_prefix}_{page - 1}"})
    if end < total:
        nav_row.append({"text": "Вперёд ➡️", "callback_data": f"{callback_prefix}_{page + 1}"})
    if nav_row:
        buttons.append(nav_row)
    
    buttons.append([{"text": "🔙 К фильтрам", "callback_data": "c3_menu"}])
    
    await send_message_inline(chat_id, text, buttons)


async def handle_corp3_lot_detail(chat_id: int, code: str):
    """Показывает детали лота и кнопки КП."""
    if not is_whitelisted(chat_id):
        return
    
    unit = get_unit_by_code(code)
    if not unit:
        await send_message(chat_id, f"❌ Лот {code} не найден в Корпусе 3.")
        return
    
    room_labels = {1: "Студия", 2: "2-комнатная", 3: "3-комнатная", 4: "4-комнатная"}
    rooms_label = room_labels.get(unit['rooms'], f"{unit['rooms']}-комнатная")
    
    text = f"""🏢 <b>Корпус 3 — {unit['code']}</b>

🏠 Тип: {rooms_label}
🏗 Этаж: {unit['floor']}
📐 Площадь: {unit['area']} м²
💰 Цена: <b>{fmt(unit['price'])} ₽</b>
📊 Цена за м²: {fmt(int(unit['price'] / unit['area']))} ₽

<b>Выберите действие:</b>"""

    buttons = [
        [{"text": "📋 КП с рассрочкой 12 мес", "callback_data": f"c3_kp12_{code}"}],
        [{"text": "📋 КП с рассрочкой 12+18 мес", "callback_data": f"c3_kp18_{code}"}],
        [{"text": "🖼 Показать планировку", "callback_data": f"c3_layout_{code}"}],
        [{"text": "📊 Расчёт доходности", "callback_data": f"calc_roi_code_{code}_3"}],
        [{"text": "📈 Сравнить с депозитом", "callback_data": f"compare_lot_{code}_3_{unit['price']//1000}"}],
        [{"text": "🔙 Назад", "callback_data": "c3_menu"}],
    ]
    
    await send_message_inline(chat_id, text, buttons)


async def handle_corp3_layout(chat_id: int, code: str):
    """Отправляет планировку лота."""
    if not is_whitelisted(chat_id):
        return
    
    unit = get_unit_by_code(code)
    if not unit:
        await send_message(chat_id, f"❌ Лот {code} не найден.")
        return
    
    layout_path = Path(unit['layout_path'])
    
    if not layout_path.exists():
        await send_message(chat_id, f"❌ Планировка для {code} не найдена.\nПуть: {layout_path}")
        return
    
    caption = f"🏢 Корпус 3 — {unit['code']}\n📐 {unit['area']} м² | 💰 {fmt(unit['price'])} ₽"
    
    buttons = [
        [{"text": "📋 Создать КП", "callback_data": f"c3_lot_{code}"}],
        [{"text": "🔙 Назад", "callback_data": "c3_menu"}],
    ]
    
    await send_photo_inline(chat_id, str(layout_path), caption, buttons)


async def handle_corp3_generate_kp(chat_id: int, code: str, include_18m: bool = False):
    """Генерирует КП для лота корпуса 3."""
    if not is_whitelisted(chat_id):
        return
    
    unit = get_unit_by_code(code)
    if not unit:
        await send_message(chat_id, f"❌ Лот {code} не найден.")
        return
    
    await send_message(chat_id, f"⏳ Генерирую КП для {code}...")
    
    try:
        pdf_path = generate_corp3_kp_pdf(unit, include_18m=include_18m)
        
        if pdf_path and Path(pdf_path).exists():
            suffix = "12+18m" if include_18m else "12m"
            filename = f"KP_Corp3_{code}_{suffix}.pdf"
            
            await send_document(chat_id, pdf_path, filename)
            
            # Удаляем временный файл
            Path(pdf_path).unlink(missing_ok=True)
        else:
            await send_message(chat_id, "❌ Ошибка генерации КП.")
    except Exception as e:
        print(f"[CORP3] Ошибка генерации КП: {e}")
        await send_message(chat_id, f"❌ Ошибка: {str(e)}")


# ==================== KP GENERATOR ====================

def generate_corp3_kp_pdf(unit: Dict[str, Any], include_18m: bool = False) -> Optional[str]:
    """Генерирует PDF КП для лота корпуса 3."""
    from services.installment_calculator import calc_12m, calc_18m
    from services.kp_pdf_generator import load_resource, CUSTOM_INSTALLMENT_UNITS
    
    # Загружаем планировку
    layout_path = Path(unit['layout_path'])
    layout_b64 = ""
    if layout_path.exists():
        with open(layout_path, 'rb') as f:
            layout_b64 = base64.b64encode(f.read()).decode()
    
    # Загружаем ресурсы
    logo_b64 = load_resource("logo_mono_trim_base64.txt")
    font_regular = load_resource("montserrat_regular_base64.txt")
    font_medium = load_resource("montserrat_medium_base64.txt")
    font_semibold = load_resource("montserrat_semibold_base64.txt")
    
    # Расчёты рассрочки
    price = unit["price"]
    i12_raw = calc_12m(price)
    i12 = {
        "pv_30": i12_raw["pv_30"], "monthly_30": i12_raw["monthly_30"],
        "pv_40": i12_raw["pv_40"], "last_40": i12_raw["last_40"],
        "pv_50": i12_raw["pv_50"], "last_50": i12_raw["last_50"],
    }
    
    i18 = {}
    if include_18m:
        i18_raw = calc_18m(price)
        i18 = {
            "p9": i18_raw["payment_9"],
            "pv_30": i18_raw["pv_30"], "monthly_30": i18_raw["monthly_30"], 
            "markup_30": i18_raw["markup_30"], "final_30": i18_raw["final_price_30"],
            "pv_40": i18_raw["pv_40"], "last_40": i18_raw["last_40"], 
            "markup_40": i18_raw["markup_40"], "final_40": i18_raw["final_price_40"],
            "pv_50": i18_raw["pv_50"], "last_50": i18_raw["last_50"], 
            "markup_50": i18_raw["markup_50"], "final_50": i18_raw["final_price_50"],
        }
    
    # Данные лота
    bname = '3 — "Digital"'  # Корпус 3
    rooms = unit.get("rooms", 1)
    area = unit["area"]
    
    if rooms == 2:
        ltype = "Евро-2"
    elif rooms >= 3:
        ltype = f"{rooms}-комнатная"
    elif area <= 26:
        ltype = "Студия"
    elif area <= 35:
        ltype = "1-комнатная"
    else:
        ltype = "1-комнатная Large"
    
    ppm2 = int(price / area)
    
    def fmt_p(p: int) -> str:
        return f"{p:,}".replace(",", " ") + " ₽"
    
    # Генерируем HTML
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
.unit-image {{ float: left; width: 296px; }}
.unit-image img {{ width: 100%; display: block; }}
.unit-details {{ margin-left: 326px; }}

.detail-table {{ width: 100%; border-collapse: collapse; }}
.detail-table td {{ padding: 12px 0; border-bottom: 1px solid rgba(49, 61, 32, 0.15); }}
.detail-label {{ color: #313D20; font-size: 15px; }}
.detail-value {{ text-align: right; font-weight: 600; font-size: 15px; }}

.installment-section {{ padding: 22px 25px; background: #F6F0E3; }}
.installment-section-18 {{ padding-top: 8px; }}
.installment-title {{ font-size: 22px; font-weight: 500; margin-bottom: 18px; color: #313D20; }}

.options-table {{ width: 100%; border-collapse: collapse; }}
.option-card {{ background: white; border: 2px solid #313D20; padding: 18px; text-align: center; vertical-align: top; }}
.option-card-mid {{ border-left: none; border-right: none; }}
.option-card-18 {{ background: white; border: 2px solid #DCB764; padding: 18px; text-align: center; vertical-align: top; }}
.option-card-18-mid {{ border-left: none; border-right: none; }}

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
<div class="title-right">Корпус {bname} • {unit["floor"]} этаж • {unit["area"]} м²</div>
<div style="clear:both"></div>
</div>

<div class="main">
<div class="unit-card">

<div class="unit-header">
<div class="unit-code">Гостиничный номер, {unit["code"]}</div>
<div class="unit-price">{fmt_p(price)}</div>
<div style="clear:both"></div>
</div>

<div class="unit-body">
<div class="unit-image">
{"<img src='data:image/jpeg;base64," + layout_b64 + "'>" if layout_b64 else ""}
</div>
<div class="unit-details">
<table class="detail-table">
<tr><td class="detail-label">Корпус</td><td class="detail-value">{bname}</td></tr>
<tr><td class="detail-label">Этаж</td><td class="detail-value">{unit["floor"]}</td></tr>
<tr><td class="detail-label">Площадь</td><td class="detail-value">{unit["area"]} м²</td></tr>
<tr><td class="detail-label">Комнат</td><td class="detail-value">{ltype}</td></tr>
<tr><td class="detail-label">Сдача</td><td class="detail-value">4 кв. 2027</td></tr>
<tr><td class="detail-label">Цена за м²</td><td class="detail-value">{fmt_p(ppm2)}</td></tr>
</table>
<div style="margin-top: 45px; padding-top: 15px; border-top: 1px solid #eee;">
<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
<span style="color: #666; font-size: 14px;">Стоимость номера</span>
<span style="font-size: 14px; color: #666;">{fmt_p(price)}</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="color: #313D20; font-size: 15px; font-weight: 500;">При 100% оплате <span style="color: #4a7c23;">(–5%)</span></span>
<span style="font-weight: 700; font-size: 20px; color: #4a7c23;">{fmt_p(int(price * 0.95))}</span>
</div>
</div>
</div>
<div style="clear:both"></div>
</div>

<div class="installment-section">
<div class="installment-title">Рассрочка 0% на 12 месяцев</div>
<table class="options-table"><tr>
<td class="option-card">
<div class="option-pv">Первый взнос 30%</div>
<div class="option-amount">{fmt_p(i12["pv_30"])}</div>
<div class="option-monthly">Ежемесячно:<br>{fmt_p(i12["monthly_30"])}</div>
</td>
<td class="option-card option-card-mid">
<div class="option-pv">Первый взнос 40%</div>
<div class="option-amount">{fmt_p(i12["pv_40"])}</div>
<div class="option-monthly">11 платежей × 200 000 ₽<br>12-й платёж: {fmt_p(i12["last_40"])}</div>
</td>
<td class="option-card">
<div class="option-pv">Первый взнос 50%</div>
<div class="option-amount">{fmt_p(i12["pv_50"])}</div>
<div class="option-monthly">11 платежей × 100 000 ₽<br>12-й платёж: {fmt_p(i12["last_50"])}</div>
</td>
</tr></table>
</div>'''

    if include_18m:
        html += f'''
<div class="installment-section installment-section-18">
<div class="installment-title">Рассрочка на 18 месяцев</div>
<table class="options-table"><tr>
<td class="option-card-18">
<div class="option-pv">Первый взнос 30% <span class="option-badge">+9%</span></div>
<div class="option-amount">{fmt_p(i18["pv_30"])}</div>
<div class="option-monthly">18 платежей × {fmt_p(i18["monthly_30"])}</div>
<div class="option-total">Удорожание: +{fmt_p(i18["markup_30"])}<div class="option-total-sum">Итого: {fmt_p(i18["final_30"])}</div></div>
</td>
<td class="option-card-18 option-card-18-mid">
<div class="option-pv">Первый взнос 40% <span class="option-badge">+7%</span></div>
<div class="option-amount">{fmt_p(i18["pv_40"])}</div>
<div class="option-monthly">8 платежей × 250 000 ₽<br>9-й платёж: {fmt_p(i18["p9"])}<br>8 платежей × 250 000 ₽<br>18-й платёж: {fmt_p(i18["last_40"])}</div>
<div class="option-total">Удорожание: +{fmt_p(i18["markup_40"])}<div class="option-total-sum">Итого: {fmt_p(i18["final_40"])}</div></div>
</td>
<td class="option-card-18">
<div class="option-pv">Первый взнос 50% <span class="option-badge">+4%</span></div>
<div class="option-amount">{fmt_p(i18["pv_50"])}</div>
<div class="option-monthly">8 платежей × 150 000 ₽<br>9-й платёж: {fmt_p(i18["p9"])}<br>8 платежей × 150 000 ₽<br>18-й платёж: {fmt_p(i18["last_50"])}</div>
<div class="option-total">Удорожание: +{fmt_p(i18["markup_50"])}<div class="option-total-sum">Итого: {fmt_p(i18["final_50"])}</div></div>
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

    # Конвертируем в PDF
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        html_path = f.name
    
    suffix = "_12m_18m" if include_18m else "_12m"
    pdf_path = os.path.join(tempfile.gettempdir(), f"KP_Corp3_{unit['code']}{suffix}.pdf")
    
    try:
        cmd = [
            'wkhtmltopdf', '--page-size', 'A4', '--orientation', 'Portrait',
            '--margin-top', '0', '--margin-bottom', '0', '--margin-left', '0', '--margin-right', '0',
            '--enable-local-file-access', '--disable-smart-shrinking', '--quiet',
            html_path, pdf_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"[CORP3 KP] Ошибка wkhtmltopdf: {result.stderr}")
            return None
        
        print(f"[CORP3 KP] ✅ Создан: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"[CORP3 KP] Ошибка: {e}")
        return None
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)


# ==================== CALLBACK ROUTER ====================

async def handle_corp3_callback(chat_id: int, data: str):
    """Роутер callback'ов корпуса 3."""
    if not is_whitelisted(chat_id):
        await send_message(chat_id, "🔒 Доступ ограничен.")
        return
    
    print(f"[CORP3] callback: {data}")
    
    if data == "c3_menu":
        await handle_corp3_start(chat_id)
    
    elif data == "c3_by_rooms":
        await handle_corp3_by_rooms(chat_id)
    
    elif data == "c3_by_floor":
        await handle_corp3_by_floor(chat_id)
    
    elif data == "c3_by_area":
        await handle_corp3_by_area(chat_id)
    
    elif data == "c3_by_code":
        await handle_corp3_by_code(chat_id)
    
    # Все лоты с пагинацией: c3_all_{page}
    elif data.startswith("c3_all_"):
        page = int(data.split("_")[-1])
        units = load_units()
        await handle_corp3_show_list(chat_id, units, "Все лоты Корпуса 3", page=page, callback_prefix="c3_all")
    
    # По комнатам: c3_rooms_{rooms}_{page}
    elif data.startswith("c3_rooms_"):
        parts = data.replace("c3_rooms_", "").split("_")
        rooms = int(parts[0])
        page = int(parts[1]) if len(parts) > 1 else 0
        units = filter_units(rooms=rooms)
        room_labels = {1: "Студии", 2: "2-комнатные", 3: "3-комнатные", 4: "4-комнатные"}
        label = room_labels.get(rooms, f"{rooms}-комнатные")
        await handle_corp3_show_list(chat_id, units, f"{label} — Корпус 3", page=page, callback_prefix=f"c3_rooms_{rooms}")
    
    # По этажу: c3_floor_{floor}_{page}
    elif data.startswith("c3_floor_"):
        parts = data.replace("c3_floor_", "").split("_")
        floor = int(parts[0])
        page = int(parts[1]) if len(parts) > 1 else 0
        units = filter_units(floor=floor)
        await handle_corp3_show_list(chat_id, units, f"{floor} этаж — Корпус 3", page=page, callback_prefix=f"c3_floor_{floor}")
    
    # По площади: c3_area_{min}_{max}_{page}
    elif data.startswith("c3_area_"):
        parts = data.replace("c3_area_", "").split("_")
        area_min = float(parts[0])
        area_max = float(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
        units = filter_units(area_min=area_min, area_max=area_max)
        await handle_corp3_show_list(chat_id, units, f"{int(area_min)}-{int(area_max)} м² — Корпус 3", page=page, callback_prefix=f"c3_area_{int(area_min)}_{int(area_max)}")
    
    # Детали лота: c3_lot_{code}
    elif data.startswith("c3_lot_"):
        code = data.replace("c3_lot_", "")
        await handle_corp3_lot_detail(chat_id, code)
    
    # Планировка: c3_layout_{code}
    elif data.startswith("c3_layout_"):
        code = data.replace("c3_layout_", "")
        await handle_corp3_layout(chat_id, code)
    
    # КП 12 мес: c3_kp12_{code}
    elif data.startswith("c3_kp12_"):
        code = data.replace("c3_kp12_", "")
        await handle_corp3_generate_kp(chat_id, code, include_18m=False)
    
    # КП 12+18 мес: c3_kp18_{code}
    elif data.startswith("c3_kp18_"):
        code = data.replace("c3_kp18_", "")
        await handle_corp3_generate_kp(chat_id, code, include_18m=True)


# ==================== TEXT HANDLER ====================

async def handle_corp3_text(chat_id: int, text: str) -> bool:
    """
    Обрабатывает текстовый ввод для корпуса 3 (поиск по коду).
    Возвращает True если обработано, False если нет.
    """
    if not is_whitelisted(chat_id):
        return False
    
    # Проверяем, ожидаем ли ввод кода
    cache = _filter_cache.get(chat_id, {})
    if not cache.get("awaiting_code"):
        return False
    
    # Сбрасываем флаг ожидания
    _filter_cache[chat_id] = {}
    
    # Ищем лот
    text_clean = text.strip()
    unit = get_unit_by_code(text_clean)
    
    if unit:
        await handle_corp3_lot_detail(chat_id, unit['code'])
        return True
    else:
        await send_message(chat_id, f"❌ Лот «{text_clean}» не найден в Корпусе 3.\n\nПопробуйте другой код или вернитесь в меню.")
        return True
