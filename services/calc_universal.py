"""
Универсальные расчёты для любого лота из properties.db.
"""

from typing import Dict, Any, Optional
from services.calculations import fmt_rub

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
    programs = []
    
    pv_12 = price * 0.30
    remaining_12 = price - pv_12
    monthly_12 = remaining_12 / 12
    programs.append({
        "name": "Рассрочка 12 мес", "description": "Без удорожания",
        "first_payment": pv_12, "first_payment_pct": 30,
        "monthly": monthly_12, "months": 12, "overpay": 0, "total": price,
    })
    
    pv_24 = price * 0.30
    remaining_24 = price - pv_24
    total_with_rate = remaining_24 * 1.06
    monthly_24 = total_with_rate / 24
    overpay_24 = total_with_rate - remaining_24
    programs.append({
        "name": "Рассрочка 24 мес", "description": "+6% годовых",
        "first_payment": pv_24, "first_payment_pct": 30,
        "monthly": monthly_24, "months": 24, "overpay": overpay_24, "total": price + overpay_24,
    })
    
    pv_mortgage = price * 0.283
    credit_amount = price - pv_mortgage
    promo_rate = 0.044
    monthly_promo = credit_amount * promo_rate / 12
    programs.append({
        "name": "Ипотека", "description": "Льготный период 12 мес",
        "first_payment": pv_mortgage, "first_payment_pct": 28.3,
        "monthly": monthly_promo, "months": 12, "promo_rate": promo_rate * 100,
        "credit_amount": credit_amount, "note": "После сдачи аренда помогает гасить",
    })
    
    return {"code": code, "area": area, "price": price, "programs": programs}


def format_installment_text(calc: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"💳 <b>Варианты покупки: {calc['code']}</b>")
    lines.append("")
    lines.append(f"📐 Площадь: {calc['area']} м²")
    lines.append(f"💰 Цена: {fmt_rub(calc['price'])}")
    lines.append("")
    
    for i, prog in enumerate(calc['programs'], 1):
        emoji = ["1️⃣", "2️⃣", "3️⃣"][i-1]
        lines.append(f"{emoji} <b>{prog['name']}</b> ({prog['description']})")
        lines.append(f"   • Первый взнос: {fmt_rub(prog['first_payment'])} ({prog['first_payment_pct']}%)")
        lines.append(f"   • Платёж: ~{fmt_rub(prog['monthly'])}/мес")
        if prog.get('overpay', 0) > 0:
            lines.append(f"   • Переплата: ~{fmt_rub(prog['overpay'])}")
        if prog.get('note'):
            lines.append(f"   • {prog['note']}")
        lines.append("")
    
    lines.append("✅ <b>Бонус:</b> Оформление включено (~150 000 ₽)")
    return "\n".join(lines)
