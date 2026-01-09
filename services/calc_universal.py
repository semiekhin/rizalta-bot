"""
Универсальные расчёты для любого лота из properties.db.
Формулы из kp_generator.py
"""

from typing import Dict, Any, Optional
from services.calculations import fmt_rub

# === КОНСТАНТЫ ===
SERVICE_FEE = 150_000  # Вычет с каждого лота
RENT_RATE_PER_M2 = 408
SEASON_MULTIPLIER = 1.725
AVERAGE_OCCUPANCY = 0.706
EXPENSE_RATIO_YEAR1 = 0.50

GROWTH_FACTORS = {
    2025: 1.0339, 2026: 1.2373, 2027: 1.5424,
    2028: 1.7569, 2029: 1.8465, 2030: 1.9388,
    2031: 2.0358, 2032: 2.1376, 2033: 2.2445,
}

OCCUPANCY_BY_YEAR = {
    2025: 0.0, 2026: 0.0, 2027: 0.0,
    2028: 0.50, 2029: 0.70, 2030: 0.70,
    2031: 0.70, 2032: 0.70, 2033: 0.70,
}

RENT_INFLATION = 0.05


def calculate_roi_for_lot(price: int, area: float, code: str) -> Dict[str, Any]:
    """Расчёт ROI для лота."""
    daily_rate = area * RENT_RATE_PER_M2 * SEASON_MULTIPLIER
    gross_year = daily_rate * 365 * AVERAGE_OCCUPANCY
    net_year = gross_year * (1 - EXPENSE_RATIO_YEAR1)
    roi_pct = (net_year / price) * 100 if price > 0 else 0
    
    projections = []
    cumulative_income = 0
    
    for year in range(2025, 2034):
        factor = GROWTH_FACTORS.get(year, GROWTH_FACTORS[2033])
        occupancy = OCCUPANCY_BY_YEAR.get(year, 0.70)
        asset_value = price * factor
        years_from_start = year - 2028
        inflation_factor = (1 + RENT_INFLATION) ** max(0, years_from_start)
        year_income = net_year * occupancy * inflation_factor if occupancy > 0 else 0
        cumulative_income += year_income
        total_capital = asset_value + cumulative_income
        projections.append({
            "year": year, "asset_value": asset_value, "year_income": year_income,
            "cumulative_income": cumulative_income, "total_capital": total_capital,
            "growth_pct": (factor - 1) * 100,
        })
    
    return {
        "code": code, "area": area, "price": price,
        "daily_rate": daily_rate, "gross_year": gross_year,
        "net_year": net_year, "roi_pct": roi_pct, "projections": projections,
    }


def format_roi_text(calc: Dict[str, Any]) -> str:
    """Форматирует ROI в текст."""
    lines = []
    lines.append(f"📊 <b>Расчёт доходности: {calc['code']}</b>")
    lines.append("")
    lines.append(f"📐 Площадь: {calc['area']} м²")
    lines.append(f"💰 Цена: {fmt_rub(calc['price'])}")
    lines.append("")
    lines.append("📈 <b>Доходность от аренды:</b>")
    lines.append(f"• Ставка: ~{fmt_rub(calc['daily_rate'])}/сутки")
    lines.append(f"• Загрузка: {AVERAGE_OCCUPANCY*100:.0f}% (средняя)")
    lines.append(f"• Валовый доход: ~{fmt_rub(calc['gross_year'])}/год")
    lines.append(f"• Чистый доход: ~{fmt_rub(calc['net_year'])}/год")
    lines.append(f"• <b>ROI: {calc['roi_pct']:.1f}% годовых</b>")
    lines.append("")
    
    proj_2027 = next((p for p in calc['projections'] if p['year'] == 2027), None)
    proj_2029 = next((p for p in calc['projections'] if p['year'] == 2029), None)
    
    lines.append("🏗 <b>Капитализация:</b>")
    if proj_2027:
        lines.append(f"• 2027 (сдача): ~{fmt_rub(proj_2027['asset_value'])} (+{proj_2027['growth_pct']:.0f}%)")
    if proj_2029:
        lines.append(f"• 2029: ~{fmt_rub(proj_2029['asset_value'])} (+{proj_2029['growth_pct']:.0f}%)")
    lines.append("")
    
    lines.append("💎 <b>Прогноз капитала:</b>")
    for year in [2025, 2027, 2029, 2033]:
        proj = next((p for p in calc['projections'] if p['year'] == year), None)
        if proj:
            note = {2025: " (старт)", 2027: " (сдача)", 2029: " (стабильный доход)"}.get(year, "")
            lines.append(f"• {year}: ~{fmt_rub(proj['total_capital'])}{note}")
    lines.append("")
    
    proj_2033 = next((p for p in calc['projections'] if p['year'] == 2033), None)
    if proj_2033:
        profit = proj_2033['total_capital'] - calc['price']
        profit_pct = (profit / calc['price']) * 100
        lines.append(f"🎯 <b>Итог к 2033:</b>")
        lines.append(f"• Капитал: ~{fmt_rub(proj_2033['total_capital'])}")
        lines.append(f"• Прибыль: +{fmt_rub(profit)} (+{profit_pct:.0f}%)")
    
    return "\n".join(lines)


def calculate_installment_for_lot(price: int, area: float, code: str) -> Dict[str, Any]:
    """
    Рассчитывает рассрочку по формулам из kp_generator.py.
    Сначала вычитаем SERVICE_FEE, потом считаем.
    """
    base = price - SERVICE_FEE
    
    # === РАССРОЧКА 12 МЕСЯЦЕВ (0%) ===
    
    # ПВ 30% — равные платежи
    pv_30_12 = int(base * 0.30)
    remaining_30_12 = base - pv_30_12
    monthly_30_12 = int(remaining_30_12 / 12)
    
    # ПВ 40% — 11 × 200К, на 12-й остаток
    pv_40_12 = int(base * 0.40)
    remaining_40_12 = base - pv_40_12
    last_40_12 = remaining_40_12 - (200_000 * 11)
    
    # ПВ 50% — 11 × 100К, на 12-й остаток
    pv_50_12 = int(base * 0.50)
    remaining_50_12 = base - pv_50_12
    last_50_12 = remaining_50_12 - (100_000 * 11)
    
    # === РАССРОЧКА 18 МЕСЯЦЕВ (с удорожанием) ===
    payment_9th = int(base * 0.10)  # 9-й платёж = 10% от базы
    
    # ПВ 30% + 9% удорожание: 18 равных платежа
    pv_30_18 = int(base * 0.30)
    remaining_30_18 = base - pv_30_18
    markup_30 = int(remaining_30_18 * 0.09)
    total_30_18 = remaining_30_18 + markup_30
    monthly_30_18 = int(total_30_18 / 18)
    final_price_30 = price + markup_30
    
    # ПВ 40% + 7% удорожание: 8×250К, 9-й, 8×250К, 18-й остаток
    pv_40_18 = int(base * 0.40)
    remaining_40_18 = base - pv_40_18
    markup_40 = int(remaining_40_18 * 0.07)
    total_40_18 = remaining_40_18 + markup_40
    paid_40_18 = (250_000 * 8) + payment_9th + (250_000 * 8)
    last_40_18 = total_40_18 - paid_40_18
    final_price_40 = price + markup_40
    
    # ПВ 50% + 4% удорожание: 8×150К, 9-й, 8×150К, 18-й остаток
    pv_50_18 = int(base * 0.50)
    remaining_50_18 = base - pv_50_18
    markup_50 = int(remaining_50_18 * 0.04)
    total_50_18 = remaining_50_18 + markup_50
    paid_50_18 = (150_000 * 8) + payment_9th + (150_000 * 8)
    last_50_18 = total_50_18 - paid_50_18
    final_price_50 = price + markup_50
    
    return {
        "code": code, "area": area, "price": price, "base": base,
        # 12 мес
        "pv_30_12": pv_30_12, "monthly_30_12": monthly_30_12,
        "pv_40_12": pv_40_12, "last_40_12": last_40_12,
        "pv_50_12": pv_50_12, "last_50_12": last_50_12,
        # 24 мес
        "payment_9th": payment_9th,
        "pv_30_18": pv_30_18, "monthly_30_18": monthly_30_18, "markup_30": markup_30, "final_price_30": final_price_30,
        "pv_40_18": pv_40_18, "last_40_18": last_40_18, "markup_40": markup_40, "final_price_40": final_price_40,
        "pv_50_18": pv_50_18, "last_50_18": last_50_18, "markup_50": markup_50, "final_price_50": final_price_50,
    }


def format_installment_text(calc: Dict[str, Any]) -> str:
    """Форматирует рассрочку в текст."""
    lines = []
    lines.append(f"💳 <b>Варианты покупки: {calc['code']}</b>")
    lines.append("")
    lines.append(f"📐 Площадь: {calc['area']} м²")
    lines.append(f"💰 Цена: {fmt_rub(calc['price'])}")
    lines.append(f"✅ Бонус: вычет {fmt_rub(SERVICE_FEE)} уже учтён")
    lines.append("")
    
    # 12 месяцев
    lines.append("📅 <b>РАССРОЧКА 12 МЕСЯЦЕВ (0%)</b>")
    lines.append("")
    lines.append(f"1️⃣ <b>ПВ 30%</b> — {fmt_rub(calc['pv_30_12'])}")
    lines.append(f"   → 12 мес по {fmt_rub(calc['monthly_30_12'])}")
    lines.append("")
    lines.append(f"2️⃣ <b>ПВ 40%</b> — {fmt_rub(calc['pv_40_12'])}")
    lines.append(f"   → 11 мес по 200 000 ₽, 12-й: {fmt_rub(calc['last_40_12'])}")
    lines.append("")
    lines.append(f"3️⃣ <b>ПВ 50%</b> — {fmt_rub(calc['pv_50_12'])}")
    lines.append(f"   → 11 мес по 100 000 ₽, 12-й: {fmt_rub(calc['last_50_12'])}")
    lines.append("")
    
    # 18 месяцев
    lines.append("📅 <b>РАССРОЧКА 18 МЕСЯЦЕВ</b>")
    lines.append("")
    lines.append(f"1️⃣ <b>ПВ 30% (+9%)</b> — {fmt_rub(calc['pv_30_18'])}")
    lines.append(f"   → 18 мес по {fmt_rub(calc['monthly_30_18'])}")
    lines.append(f"   → Итого: {fmt_rub(calc['final_price_30'])} (+{fmt_rub(calc['markup_30'])})")
    lines.append("")
    lines.append(f"2️⃣ <b>ПВ 40% (+7%)</b> — {fmt_rub(calc['pv_40_18'])}")
    lines.append(f"   → 8×250К, 9-й: {fmt_rub(calc['payment_9th'])}, 8×250К, 18-й: {fmt_rub(calc['last_40_18'])}")
    lines.append(f"   → Итого: {fmt_rub(calc['final_price_40'])} (+{fmt_rub(calc['markup_40'])})")
    lines.append("")
    lines.append(f"3️⃣ <b>ПВ 50% (+4%)</b> — {fmt_rub(calc['pv_50_18'])}")
    lines.append(f"   → 8×150К, 9-й: {fmt_rub(calc['payment_9th'])}, 8×150К, 18-й: {fmt_rub(calc['last_50_18'])}")
    lines.append(f"   → Итого: {fmt_rub(calc['final_price_50'])} (+{fmt_rub(calc['markup_50'])})")
    
    return "\n".join(lines)
