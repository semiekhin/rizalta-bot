#!/usr/bin/env python3
"""
ГЕНЕРАТОР КП RIZALTA
====================

Использование:
1. Положить рядом: properties.db, header_image_base64.txt
2. Запустить: python kp_generator.py

Функции:
- generate_kp_by_codes(codes, output_name) — КП по списку кодов
- generate_kp_by_filter(area_min, area_max, floor, block_section, output_name) — КП по фильтру
- generate_kp_by_budget(budget, block_section, output_name) — КП по бюджету
"""

import sqlite3
import base64
from collections import defaultdict
from pathlib import Path

# === НАСТРОЙКИ ===
SERVICE_FEE = 150_000  # Вычет с каждого лота перед расчётом
DB_PATH = "properties.db"
HEADER_IMAGE_PATH = "header_image_base64.txt"

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def format_price(price: int) -> str:
    """Форматирует цену: 15 375 750 ₽"""
    return f"{price:,}".replace(",", " ") + " ₽"

def format_price_short(price: int) -> str:
    """Короткий формат: 15.4 млн"""
    return f"{price/1_000_000:.1f} млн"

def get_lot_type(area: float, rooms: int) -> str:
    """Определяет тип лота по площади и комнатам"""
    if rooms == 2:
        return "Евро-2"
    elif area <= 26:
        return "Business Studio"
    elif area <= 30:
        return "1-комнатная"
    else:
        return "1-комнатная Large"

def get_building_name(block_section: int) -> str:
    """Возвращает номер и название корпуса"""
    # block_section = 1 → Корпус 2 (А) = Business
    # block_section = 2 → Корпус 1 (В) = Family
    if block_section == 1:
        return 'Корпус 2 — "Business"'
    else:
        return 'Корпус 1 — "Family"'

def calc_installment(price: int):
    """
    Рассчитывает рассрочку на 12 месяцев.
    ВАЖНО: сначала вычитаем SERVICE_FEE, потом считаем!
    """
    base = price - SERVICE_FEE
    
    # ПВ 30% — равные платежи
    pv_30 = int(base * 0.30)
    remaining_30 = base - pv_30
    monthly_30 = int(remaining_30 / 12)
    
    # ПВ 40% — 11 × 200К, на 12-й остаток
    pv_40 = int(base * 0.40)
    remaining_40 = base - pv_40
    last_40 = remaining_40 - (200_000 * 11)
    
    # ПВ 50% — 11 × 100К, на 12-й остаток
    pv_50 = int(base * 0.50)
    remaining_50 = base - pv_50
    last_50 = remaining_50 - (100_000 * 11)
    
    return {
        'base': base,
        'pv_30': pv_30, 'monthly_30': monthly_30,
        'pv_40': pv_40, 'last_40': last_40,
        'pv_50': pv_50, 'last_50': last_50,
    }

def calc_installment_24(price: int):
    """
    Рассчитывает рассрочку на 24 месяца с удорожанием.
    ВАЖНО: сначала вычитаем SERVICE_FEE, потом считаем!
    
    ПВ 30% + 12% удорожание: 24 равных платежа
    ПВ 40% + 9% удорожание: 11×250К, 12-й (10% базы), 11×250К, 24-й остаток
    ПВ 50% + 6% удорожание: 11×150К, 12-й (10% базы), 11×150К, 24-й остаток
    """
    base = price - SERVICE_FEE
    payment_12 = int(base * 0.10)  # 12-й платёж = 10% от базы
    
    # ПВ 30% + удорожание 12%
    pv_30 = int(base * 0.30)
    remaining_30 = base - pv_30
    markup_30 = int(remaining_30 * 0.12)
    total_30 = remaining_30 + markup_30
    monthly_30 = int(total_30 / 24)
    final_price_30 = price + markup_30  # цена + удорожание (без вычета 150К)
    
    # ПВ 40% + удорожание 9%
    pv_40 = int(base * 0.40)
    remaining_40 = base - pv_40
    markup_40 = int(remaining_40 * 0.09)
    total_40 = remaining_40 + markup_40
    # 11×250К + 12-й + 11×250К + 24-й
    paid_40 = (250_000 * 11) + payment_12 + (250_000 * 11)
    last_40 = total_40 - paid_40
    final_price_40 = price + markup_40  # цена + удорожание (без вычета 150К)
    
    # ПВ 50% + удорожание 6%
    pv_50 = int(base * 0.50)
    remaining_50 = base - pv_50
    markup_50 = int(remaining_50 * 0.06)
    total_50 = remaining_50 + markup_50
    # 11×150К + 12-й + 11×150К + 24-й
    paid_50 = (150_000 * 11) + payment_12 + (150_000 * 11)
    last_50 = total_50 - paid_50
    final_price_50 = price + markup_50  # цена + удорожание (без вычета 150К)
    
    return {
        'base': base,
        'payment_12': payment_12,
        # 30%
        'pv_30': pv_30, 'monthly_30': monthly_30, 
        'markup_30': markup_30, 'final_price_30': final_price_30,
        # 40%
        'pv_40': pv_40, 'last_40': last_40,
        'markup_40': markup_40, 'final_price_40': final_price_40,
        # 50%
        'pv_50': pv_50, 'last_50': last_50,
        'markup_50': markup_50, 'final_price_50': final_price_50,
    }

def calc_portfolio_installment(units: list):
    """Рассчитывает рассрочку для портфеля"""
    total_count = len(units)
    total_price = sum(u['price'] for u in units)
    total_savings = SERVICE_FEE * total_count
    base = total_price - total_savings
    
    # === РАССРОЧКА 12 МЕСЯЦЕВ ===
    # ПВ 30%
    pv_30 = int(base * 0.30)
    monthly_30 = int((base - pv_30) / 12)
    
    # ПВ 40%
    pv_40 = int(base * 0.40)
    monthly_40 = 200_000 * total_count
    last_40 = (base - pv_40) - (monthly_40 * 11)
    
    # ПВ 50%
    pv_50 = int(base * 0.50)
    monthly_50 = 100_000 * total_count
    last_50 = (base - pv_50) - (monthly_50 * 11)
    
    # === РАССРОЧКА 24 МЕСЯЦА (с удорожанием) ===
    payment_12 = int(base * 0.10)  # 12-й платёж = 10% от базы
    
    # ПВ 30% + 12%
    remaining_30_24 = base - pv_30
    markup_30_24 = int(remaining_30_24 * 0.12)
    monthly_30_24 = int((remaining_30_24 + markup_30_24) / 24)
    final_price_30_24 = total_price + markup_30_24  # полная цена + удорожание
    
    # ПВ 40% + 9%
    remaining_40_24 = base - pv_40
    markup_40_24 = int(remaining_40_24 * 0.09)
    monthly_40_24 = 250_000 * total_count
    paid_40_24 = (monthly_40_24 * 11) + payment_12 + (monthly_40_24 * 11)
    last_40_24 = (remaining_40_24 + markup_40_24) - paid_40_24
    final_price_40_24 = total_price + markup_40_24  # полная цена + удорожание
    
    # ПВ 50% + 6%
    remaining_50_24 = base - pv_50
    markup_50_24 = int(remaining_50_24 * 0.06)
    monthly_50_24 = 150_000 * total_count
    paid_50_24 = (monthly_50_24 * 11) + payment_12 + (monthly_50_24 * 11)
    last_50_24 = (remaining_50_24 + markup_50_24) - paid_50_24
    final_price_50_24 = total_price + markup_50_24  # полная цена + удорожание
    
    return {
        'total_price': total_price,
        'total_savings': total_savings,
        'base': base,
        # 12 мес
        'pv_30': pv_30, 'monthly_30': monthly_30,
        'pv_40': pv_40, 'monthly_40': monthly_40, 'last_40': last_40,
        'pv_50': pv_50, 'monthly_50': monthly_50, 'last_50': last_50,
        # 24 мес
        'payment_12': payment_12,
        'monthly_30_24': monthly_30_24, 'markup_30_24': markup_30_24, 'final_price_30_24': final_price_30_24,
        'monthly_40_24': monthly_40_24, 'last_40_24': last_40_24, 'markup_40_24': markup_40_24, 'final_price_40_24': final_price_40_24,
        'monthly_50_24': monthly_50_24, 'last_50_24': last_50_24, 'markup_50_24': markup_50_24, 'final_price_50_24': final_price_50_24,
    }

def load_header_image():
    """Загружает base64 картинку для шапки"""
    try:
        with open(HEADER_IMAGE_PATH, 'r') as f:
            return f.read().strip()
    except:
        return ""

def get_units_from_db(where_clause: str = "1=1", params: tuple = ()):
    """Получает лоты из базы"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT code, block_section, floor, rooms, area_m2, price_rub, layout_url
        FROM units 
        WHERE {where_clause}
        ORDER BY area_m2, price_rub
    ''', params)
    columns = ['code', 'block_section', 'floor', 'rooms', 'area', 'price', 'layout_url']
    units = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return units

# === ГЕНЕРАЦИЯ HTML ===

def generate_lot_card(group_units: list, header_image_b64: str, mode: str = "default") -> str:
    """
    Генерирует HTML карточку для группы лотов.
    mode: "default" или "two_installments"
    """
    min_price = min(u['price'] for u in group_units)
    min_area = min(u['area'] for u in group_units)
    max_area = max(u['area'] for u in group_units)
    
    inst = calc_installment(min_price)
    lot_type = get_lot_type(min_area, group_units[0]['rooms'])
    layout_url = group_units[0].get('layout_url', '')
    area_text = f"{min_area}" if min_area == max_area else f"{min_area}–{max_area}"
    
    if mode == "two_installments":
        inst24 = calc_installment_24(min_price)
        return f'''
    <div class="lot-card">
        <div class="lot-visual">
            <img src="{layout_url}" alt="Планировка">
        </div>
        <div class="lot-info">
            <div class="lot-top">
                <div class="lot-title-row">
                    <h3 class="lot-title">{lot_type}</h3>
                    <span class="lot-area">{area_text} м²</span>
                </div>
            </div>
            <div class="price-box">
                <span class="price-label">Цена от</span>
                <span class="price-val">{format_price(min_price)}</span>
            </div>
            
            <!-- РАССРОЧКА 12 МЕСЯЦЕВ -->
            <div class="installment-block">
                <div class="installment-title">Рассрочка 12 месяцев (0%)</div>
                
                <div class="installment-option">
                    <span class="option-num">1</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 30% — {format_price(inst['pv_30'])}</div>
                        <div class="option-sub">— остаток 12 мес равными платежами по {format_price(inst['monthly_30'])}</div>
                    </div>
                </div>
                
                <div class="installment-option">
                    <span class="option-num">2</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 40% — {format_price(inst['pv_40'])}</div>
                        <div class="option-sub">— 11 мес по 200 000 ₽, на 12-й месяц {format_price(inst['last_40'])}</div>
                    </div>
                </div>
                
                <div class="installment-option">
                    <span class="option-num">3</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 50% — {format_price(inst['pv_50'])}</div>
                        <div class="option-sub">— 11 мес по 100 000 ₽, на 12-й месяц {format_price(inst['last_50'])}</div>
                    </div>
                </div>
            </div>
            
            <!-- РАССРОЧКА 24 МЕСЯЦА -->
            <div class="installment-block installment-24">
                <div class="installment-title">Рассрочка 24 месяца (с удорожанием)</div>
                
                <div class="installment-option">
                    <span class="option-num">1</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 30% — {format_price(inst24['pv_30'])} <span class="markup-badge">+12%</span></div>
                        <div class="option-sub">— 24 мес равными платежами по {format_price(inst24['monthly_30'])}</div>
                        <div class="option-total">Удорожание: +{format_price(inst24['markup_30'])} → Итого: {format_price(inst24['final_price_30'])}</div>
                    </div>
                </div>
                
                <div class="installment-option">
                    <span class="option-num">2</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 40% — {format_price(inst24['pv_40'])} <span class="markup-badge">+9%</span></div>
                        <div class="option-sub">— 11 мес по 250 000 ₽, 12-й: {format_price(inst24['payment_12'])}, 11 мес по 250 000 ₽, 24-й: {format_price(inst24['last_40'])}</div>
                        <div class="option-total">Удорожание: +{format_price(inst24['markup_40'])} → Итого: {format_price(inst24['final_price_40'])}</div>
                    </div>
                </div>
                
                <div class="installment-option">
                    <span class="option-num">3</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 50% — {format_price(inst24['pv_50'])} <span class="markup-badge">+6%</span></div>
                        <div class="option-sub">— 11 мес по 150 000 ₽, 12-й: {format_price(inst24['payment_12'])}, 11 мес по 150 000 ₽, 24-й: {format_price(inst24['last_50'])}</div>
                        <div class="option-total">Удорожание: +{format_price(inst24['markup_50'])} → Итого: {format_price(inst24['final_price_50'])}</div>
                    </div>
                </div>
            </div>
            
            <div class="installment-note">
                * Расчёт с учётом вычета 150 000 ₽
            </div>
        </div>
    </div>
'''
    
    # mode == "default"
    return f'''
    <div class="lot-card">
        <div class="lot-visual">
            <img src="{layout_url}" alt="Планировка">
        </div>
        <div class="lot-info">
            <div class="lot-top">
                <div class="lot-title-row">
                    <h3 class="lot-title">{lot_type}</h3>
                    <span class="lot-area">{area_text} м²</span>
                </div>
            </div>
            <div class="price-box">
                <span class="price-label">Цена от</span>
                <span class="price-val">{format_price(min_price)}</span>
            </div>
            
            <div class="installment-block">
                <div class="installment-title">Рассрочка на 12 месяцев *</div>
                
                <div class="installment-option">
                    <span class="option-num">1</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 30% — {format_price(inst['pv_30'])}</div>
                        <div class="option-sub">— остаток 12 мес равными платежами по {format_price(inst['monthly_30'])}</div>
                    </div>
                </div>
                
                <div class="installment-option">
                    <span class="option-num">2</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 40% — {format_price(inst['pv_40'])}</div>
                        <div class="option-sub">— 11 мес по 200 000 ₽, на 12-й месяц {format_price(inst['last_40'])}</div>
                    </div>
                </div>
                
                <div class="installment-option">
                    <span class="option-num">3</span>
                    <div class="option-text">
                        <div class="option-main">ПВ 50% — {format_price(inst['pv_50'])}</div>
                        <div class="option-sub">— 11 мес по 100 000 ₽, на 12-й месяц {format_price(inst['last_50'])}</div>
                    </div>
                </div>
                
                <div class="installment-note">
                    * Расчёт с учётом вычета 150 000 ₽<br>
                    Также доступна рассрочка на 24 мес с удорожанием 12% / 9% / 6% в зависимости от ПВ
                </div>
            </div>
        </div>
    </div>
'''

def generate_html(units: list, title: str, subtitle: str, output_path: str, extra_stats: dict = None, mode: str = "default"):
    """
    Генерирует полный HTML документ.
    mode: "default" или "two_installments"
    """
    header_image_b64 = load_header_image()
    is_single = len(units) == 1
    
    # Для одного лота — особый subtitle
    if is_single:
        u = units[0]
        building = get_building_name(u['block_section'])
        subtitle = f"{building} • {u['floor']} этаж • {u['area']} м²"
    
    # Группируем по площадям
    groups = defaultdict(list)
    for u in units:
        area_key = round(u['area'], 1)
        groups[area_key].append(u)
    groups = dict(sorted(groups.items()))
    
    # Генерируем карточки
    lot_cards = ""
    for area_key, group_units in groups.items():
        lot_cards += generate_lot_card(group_units, header_image_b64, mode)
    
    # Расчёт портфеля
    portfolio = calc_portfolio_installment(units)
    
    min_area = min(u['area'] for u in units)
    max_area = max(u['area'] for u in units)
    
    # Статистика убрана
    stats_html = ""
    
    # Блок "Инвестиционный портфель" (не показываем для одного лота)
    if is_single:
        portfolio_html = ""
    elif mode == "two_installments":
        portfolio_html = f'''
    <div class="total-block">
        <div class="total-title">Инвестиционный портфель</div>
        <div style="color: #a7f3d0; margin-bottom: 20px;">{len(units)} гостиничных номеров</div>
        <div class="total-price-large">{format_price(portfolio['total_price'])}</div>

        <h3 style="color:#fff; margin-bottom:25px; text-transform:uppercase; font-size:1rem; letter-spacing:1px;">Рассрочка 12 месяцев (0%)</h3>
        
        <div class="total-grid">
            <div class="t-card">
                <div class="t-head">При ПВ 30%<span>{format_price(portfolio['pv_30'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_30'])}</div>
                <div class="t-monthly-desc">ежемесячно × 12 месяцев</div>
            </div>
            <div class="t-card">
                <div class="t-head">При ПВ 40%<span>{format_price(portfolio['pv_40'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_40'])}</div>
                <div class="t-monthly-desc">ежемесячно × 11 мес, на 12-й: {format_price(portfolio['last_40'])}</div>
            </div>
            <div class="t-card">
                <div class="t-head">При ПВ 50%<span>{format_price(portfolio['pv_50'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_50'])}</div>
                <div class="t-monthly-desc">ежемесячно × 11 мес, на 12-й: {format_price(portfolio['last_50'])}</div>
            </div>
        </div>

        <h3 style="color:#fff; margin: 50px 0 25px; text-transform:uppercase; font-size:1rem; letter-spacing:1px; border-top: 2px solid var(--accent); padding-top: 40px;">Рассрочка 24 месяца (с удорожанием)</h3>
        
        <div class="total-grid">
            <div class="t-card">
                <div class="t-head">При ПВ 30% <span class="markup-badge" style="display:inline; font-size:0.7rem;">+12%</span><span>{format_price(portfolio['pv_30'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_30_24'])}</div>
                <div class="t-monthly-desc">ежемесячно × 24 месяца</div>
                <div class="t-total">Удорожание: +{format_price(portfolio['markup_30_24'])}<br>Итого: {format_price(portfolio['final_price_30_24'])}</div>
            </div>
            <div class="t-card">
                <div class="t-head">При ПВ 40% <span class="markup-badge" style="display:inline; font-size:0.7rem;">+9%</span><span>{format_price(portfolio['pv_40'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_40_24'])}</div>
                <div class="t-monthly-desc">× 11 мес, 12-й: {format_price(portfolio['payment_12'])}, × 11 мес, 24-й: {format_price(portfolio['last_40_24'])}</div>
                <div class="t-total">Удорожание: +{format_price(portfolio['markup_40_24'])}<br>Итого: {format_price(portfolio['final_price_40_24'])}</div>
            </div>
            <div class="t-card">
                <div class="t-head">При ПВ 50% <span class="markup-badge" style="display:inline; font-size:0.7rem;">+6%</span><span>{format_price(portfolio['pv_50'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_50_24'])}</div>
                <div class="t-monthly-desc">× 11 мес, 12-й: {format_price(portfolio['payment_12'])}, × 11 мес, 24-й: {format_price(portfolio['last_50_24'])}</div>
                <div class="t-total">Удорожание: +{format_price(portfolio['markup_50_24'])}<br>Итого: {format_price(portfolio['final_price_50_24'])}</div>
            </div>
        </div>
        
        <div style="margin-top: 40px; font-size: 0.8rem; color: #a7f3d0;">
            * Расчёт с учётом вычета 150 000 ₽ с каждого лота (экономия {format_price_short(portfolio['total_savings'])})
        </div>
    </div>
'''
    else:
        portfolio_html = f'''
    <div class="total-block">
        <div class="total-title">Инвестиционный портфель</div>
        <div style="color: #a7f3d0; margin-bottom: 20px;">{len(units)} гостиничных номеров</div>
        <div class="total-price-large">{format_price(portfolio['total_price'])}</div>

        <h3 style="color:#fff; margin-bottom:25px; text-transform:uppercase; font-size:1rem; letter-spacing:1px;">Варианты входа в сделку</h3>
        
        <div class="total-grid">
            <div class="t-card">
                <div class="t-head">При ПВ 30%<span>{format_price(portfolio['pv_30'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_30'])}</div>
                <div class="t-monthly-desc">ежемесячно × 12 месяцев</div>
            </div>
            <div class="t-card">
                <div class="t-head">При ПВ 40%<span>{format_price(portfolio['pv_40'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_40'])}</div>
                <div class="t-monthly-desc">ежемесячно × 11 мес, на 12-й: {format_price(portfolio['last_40'])}</div>
            </div>
            <div class="t-card">
                <div class="t-head">При ПВ 50%<span>{format_price(portfolio['pv_50'])}</span></div>
                <div class="t-monthly-val">{format_price(portfolio['monthly_50'])}</div>
                <div class="t-monthly-desc">ежемесячно × 11 мес, на 12-й: {format_price(portfolio['last_50'])}</div>
            </div>
        </div>
        
        <div style="margin-top: 40px; font-size: 0.8rem; color: #a7f3d0;">
            * Расчёт с учётом вычета 150 000 ₽ с каждого лота (экономия {format_price_short(portfolio['total_savings'])})<br>
            Также доступна рассрочка на 24 мес с удорожанием 12% / 9% / 6% в зависимости от ПВ
        </div>
    </div>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Manrope:wght@300;400;600&display=swap');

        :root {{
            --bg-body-start: #064e3b; 
            --bg-body-end: #022c22;   
            --accent: #D4AF37;        
            --text-main: #FFFFFF;
            --text-muted: #a7f3d0;    
        }}

        body {{
            background: radial-gradient(circle at top center, var(--bg-body-start), var(--bg-body-end));
            color: var(--text-main);
            font-family: 'Manrope', sans-serif;
            margin: 0; padding: 0; line-height: 1.4;
        }}

        .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}

        header {{
            text-align: center;
            background-image: 
                linear-gradient(to bottom, rgba(6, 78, 59, 0.7), rgba(2, 44, 34, 0.95)),
                url('data:image/png;base64,{header_image_b64}');
            background-size: cover;
            background-position: center;
            padding: 100px 20px 60px;
            margin-bottom: 50px;
            border-bottom: 2px solid var(--accent);
        }}

        h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 5rem; color: var(--accent); margin: 0;
            letter-spacing: 8px; text-transform: uppercase;
        }}
        .subtitle {{ font-size: 1.4rem; color: #fff; margin-top: 15px; letter-spacing: 4px; text-transform: uppercase; }}

        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 60px; }}
        .stat-card {{
            background: rgba(6, 95, 70, 0.4); padding: 20px; border-left: 3px solid var(--accent);
            border-radius: 4px;
        }}
        .stat-label {{ color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; }}
        .stat-value {{ font-size: 1.5rem; font-family: 'Playfair Display', serif; margin-top: 5px; }}

        .lot-card {{
            background-color: #fff; color: #000; display: grid; grid-template-columns: 1fr 1.2fr;
            margin-bottom: 40px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); border-radius: 8px;
            overflow: hidden;
        }}
        .lot-visual {{
            padding: 15px; display: flex; align-items: center; justify-content: center;
            border-right: 1px solid #eee; background: #fff; min-height: 320px;
        }}
        .lot-visual img {{ max-width: 100%; max-height: 525px; object-fit: contain; }}
        .lot-info {{
            background: #064e3b; color: var(--text-main); padding: 30px;
            display: flex; flex-direction: column; justify-content: center;
        }}
        .lot-top {{ border-bottom: 1px solid rgba(52, 211, 153, 0.2); padding-bottom: 10px; margin-bottom: 15px; }}
        .lot-title-row {{ display: flex; justify-content: space-between; align-items: flex-end; }}
        .lot-title {{ font-family: 'Playfair Display', serif; font-size: 1.8rem; margin: 0; }}
        .lot-area {{ font-size: 1.6rem; color: var(--accent); font-family: 'Playfair Display', serif; }}
        
        .price-box {{
            background: rgba(212, 175, 55, 0.1); padding: 15px 20px; border-radius: 6px; margin-bottom: 20px;
            display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--accent);
        }}
        .price-label {{ font-size: 0.9rem; color: var(--accent); text-transform: uppercase; }}
        .price-val {{ font-size: 1.5rem; font-weight: 600; }}
        
        .installment-block {{ margin-top: 10px; }}
        .installment-title {{
            font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;
            margin-bottom: 15px; letter-spacing: 1px;
        }}
        .installment-option {{
            display: flex; align-items: flex-start; margin-bottom: 12px; padding-bottom: 12px;
            border-bottom: 1px solid rgba(52, 211, 153, 0.15);
        }}
        .installment-option:last-of-type {{ border-bottom: none; margin-bottom: 15px; }}
        .option-num {{
            font-family: 'Playfair Display', serif; font-size: 1.6rem; color: var(--accent);
            margin-right: 15px; line-height: 1.2; min-width: 25px;
        }}
        .option-text {{ flex: 1; }}
        .option-main {{ font-weight: 600; font-size: 0.95rem; line-height: 1.4; }}
        .option-sub {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 4px; }}
        .option-total {{ 
            font-size: 0.85rem; color: var(--accent); margin-top: 6px; 
            padding: 4px 8px; background: rgba(212, 175, 55, 0.1); 
            border-radius: 4px; display: inline-block;
        }}
        .markup-badge {{
            font-size: 0.75rem; color: #fff; background: #dc2626;
            padding: 2px 6px; border-radius: 3px; margin-left: 8px;
        }}
        .installment-24 {{
            margin-top: 25px; border-top: 2px solid var(--accent); padding-top: 20px;
        }}
        .installment-note {{
            font-size: 0.75rem; color: #aaa; font-style: italic;
            padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);
        }}

        .total-block {{
            margin-top: 60px; border: 2px solid var(--accent); padding: 40px;
            background: #022c22; text-align: center;
        }}
        .total-title {{ font-family: 'Playfair Display', serif; font-size: 2.5rem; margin-bottom: 10px; }}
        .total-price-large {{ font-size: 3.5rem; font-weight: 600; color: var(--accent); margin: 20px 0 40px; }}
        .total-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: left; }}
        .t-card {{ background: rgba(255,255,255,0.05); padding: 25px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); }}
        .t-head {{ color: var(--text-muted); text-transform: uppercase; font-size: 0.85rem; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }}
        .t-head span {{ display: block; color: #fff; font-size: 1.2rem; font-weight: 600; margin-top: 5px; font-family: 'Playfair Display', serif; }}
        .t-monthly-val {{ color: var(--accent); font-size: 1.3rem; font-weight: 600; margin-bottom: 5px; }}
        .t-monthly-desc {{ font-size: 0.8rem; color: #ccc; }}
        .t-total {{ 
            margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);
            font-size: 0.85rem; color: var(--accent);
        }}

        @media (max-width: 768px) {{
            h1 {{ font-size: 3rem; }}
            .stats, .total-grid {{ grid-template-columns: 1fr; }}
            .lot-card {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>

<header>
    <h1>RIZALTA</h1>
    <div class="subtitle">{subtitle}</div>
</header>

<div class="container">
    {stats_html}

    {lot_cards}

    {portfolio_html}
</div>

</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ КП сохранено: {output_path}")
    print(f"   Лотов: {len(units)}")
    print(f"   Сумма: {format_price(portfolio['total_price'])}")
    
    return output_path


# === ПУБЛИЧНЫЕ ФУНКЦИИ ===

def generate_kp_by_codes(codes: list, output_name: str = "kp_custom.html"):
    """
    Генерирует КП по списку кодов лотов.
    
    Пример: generate_kp_by_codes(['А419', 'В401', 'В403'])
    """
    placeholders = ','.join(['?' for _ in codes])
    units = get_units_from_db(f"code IN ({placeholders})", tuple(codes))
    
    if not units:
        print("❌ Лоты не найдены")
        return None
    
    return generate_html(
        units,
        title=f"КП RIZALTA — {len(units)} лотов",
        subtitle=f"Подборка • {len(units)} гостиничных номеров",
        output_path=output_name
    )


def generate_kp_by_filter(
    area_min: float = 0,
    area_max: float = 100,
    floor: int = None,
    block_section: int = None,  # 1 = Корпус 2 (А), 2 = Корпус 1 (В)
    output_name: str = "kp_filter.html"
):
    """
    Генерирует КП по фильтру.
    
    Пример: generate_kp_by_filter(area_min=22, area_max=25, floor=4, block_section=2)
    """
    where = "area_m2 >= ? AND area_m2 <= ?"
    params = [area_min, area_max]
    
    if floor:
        where += " AND floor = ?"
        params.append(floor)
    
    if block_section:
        where += " AND block_section = ?"
        params.append(block_section)
    
    units = get_units_from_db(where, tuple(params))
    
    if not units:
        print("❌ Лоты не найдены")
        return None
    
    # Формируем subtitle
    corp = f"Корпус {2 if block_section == 1 else 1}" if block_section else "Все корпуса"
    floor_text = f"{floor} этаж" if floor else "Все этажи"
    
    return generate_html(
        units,
        title=f"КП RIZALTA — {area_min}-{area_max} м²",
        subtitle=f"{corp} • {floor_text} • {area_min}-{area_max} м²",
        output_path=output_name
    )


def generate_kp_by_budget(
    budget: int,
    block_section: int = None,  # 1 = Корпус 2 (А), 2 = Корпус 1 (В)
    output_name: str = "kp_budget.html"
):
    """
    Распределяет бюджет по самым маленьким лотам.
    
    Пример: generate_kp_by_budget(100_000_000, block_section=1)
    """
    where = "1=1"
    params = []
    
    if block_section:
        where = "block_section = ?"
        params.append(block_section)
    
    all_units = get_units_from_db(where, tuple(params))
    
    # Выбираем лоты в рамках бюджета
    selected = []
    total = 0
    for u in all_units:
        if total + u['price'] <= budget:
            selected.append(u)
            total += u['price']
    
    if not selected:
        print("❌ Не удалось подобрать лоты")
        return None
    
    remaining = budget - total
    corp = f"Корпус {2 if block_section == 1 else 1}" if block_section else "Все корпуса"
    
    return generate_html(
        selected,
        title=f"КП RIZALTA — Бюджет {format_price_short(budget)}",
        subtitle=f"{corp} • Бюджет {format_price_short(budget)}",
        output_path=output_name,
        extra_stats={"Остаток": format_price_short(remaining)}
    )


# === MAIN ===

if __name__ == "__main__":
    # Пример использования
    print("=== Генератор КП RIZALTA ===\n")
    
    # Пример 1: КП по бюджету
    # generate_kp_by_budget(100_000_000, block_section=1, output_name="kp_100m.html")
    
    # Пример 2: КП по фильтру
    # generate_kp_by_filter(area_min=22, area_max=25, floor=4, block_section=2, output_name="kp_22-25m.html")
    
    # Пример 3: КП по кодам
    # generate_kp_by_codes(['А419', 'В401'], output_name="kp_custom.html")
    
    print("Используй функции:")
    print("  generate_kp_by_codes(['А419', 'В401'])")
    print("  generate_kp_by_filter(area_min=22, area_max=25, floor=4)")
    print("  generate_kp_by_budget(100_000_000, block_section=1)")
