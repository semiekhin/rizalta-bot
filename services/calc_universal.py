"""
Универсальный расчёт рассрочки и ROI RIZALTA.
Использует единый калькулятор из installment_calculator.py

v4.0 (11.01.2026) — рефакторинг на Single Source of Truth
"""

from typing import Dict, Any, Optional
from services.calculations import fmt_rub
from services.installment_calculator import calc_12m, calc_18m, get_service_fee, get_texts
from services.kp_pdf_generator import CUSTOM_INSTALLMENT_UNITS

SERVICE_FEE = get_service_fee()

# === ROI КОНСТАНТЫ ===
RENT_RATE_PER_M2 = 3500
SEASON_MULTIPLIER = 1.0
AVERAGE_OCCUPANCY = 0.65
EXPENSE_RATIO_YEAR1 = 0.35
RENT_INFLATION = 0.08

GROWTH_FACTORS = {
    2025: 1.00, 2026: 1.12, 2027: 1.28, 2028: 1.38,
    2029: 1.49, 2030: 1.61, 2031: 1.74, 2032: 1.88, 2033: 2.03,
}

OCCUPANCY_BY_YEAR = {
    2025: 0, 2026: 0, 2027: 0.35, 2028: 0.55,
    2029: 0.65, 2030: 0.70, 2031: 0.70, 2032: 0.70, 2033: 0.70,
}

# === ROI ФУНКЦИИ ===
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


# === РАССРОЧКА ФУНКЦИИ ===
def calculate_installment_for_lot(price: int, area: float, code: str) -> Dict[str, Any]:
    """
    Рассчитывает все варианты рассрочки для одного лота.
    Использует единый калькулятор.
    """
    i12 = calc_12m(price)
    i18 = calc_18m(price)
    
    return {
        "code": code, "area": area, "price": price, "base": i12["base"],
        # 12 мес
        "pv_30_12": i12["pv_30"], "monthly_30_12": i12["monthly_30"],
        "pv_40_12": i12["pv_40"], "last_40_12": i12["last_40"],
        "pv_50_12": i12["pv_50"], "last_50_12": i12["last_50"],
        # 18 мес
        "payment_9th": i18["payment_9"],
        "pv_30_18": i18["pv_30"], "monthly_30_18": i18["monthly_30"], "markup_30": i18["markup_30"], "final_price_30": i18["final_price_30"],
        "pv_40_18": i18["pv_40"], "last_40_18": i18["last_40"], "markup_40": i18["markup_40"], "final_price_40": i18["final_price_40"],
        "pv_50_18": i18["pv_50"], "last_50_18": i18["last_50"], "markup_50": i18["markup_50"], "final_price_50": i18["final_price_50"],
    }

def format_installment_text(calc: Dict[str, Any]) -> str:
    """Форматирует результаты расчёта в читаемый текст."""
    texts = get_texts()
    
    # Для лотов с особыми условиями — только 12 мес ПВ 50%
    if calc['code'] in CUSTOM_INSTALLMENT_UNITS:
        return f"""📊 **Расчёт для лота {calc['code']}**
Площадь: {calc['area']} м² | Цена: {fmt_rub(calc['price'])}

━━━ {texts['12m_title']} ━━━

**ПВ 50%** — {fmt_rub(calc['pv_50_12'])}
└ 11 × 100 000 ₽, последний: {fmt_rub(calc['last_50_12'])}

ℹ️ Для данного лота доступна только рассрочка 12 месяцев с ПВ 50%
"""
    
    return f"""📊 **Расчёт для лота {calc['code']}**
Площадь: {calc['area']} м² | Цена: {fmt_rub(calc['price'])}

━━━ {texts['12m_title']} ━━━

**ПВ 30%** — {fmt_rub(calc['pv_30_12'])}
└ Ежемесячно: {fmt_rub(calc['monthly_30_12'])}

**ПВ 40%** — {fmt_rub(calc['pv_40_12'])}
└ 11 × 200 000 ₽, последний: {fmt_rub(calc['last_40_12'])}

**ПВ 50%** — {fmt_rub(calc['pv_50_12'])}
└ 11 × 100 000 ₽, последний: {fmt_rub(calc['last_50_12'])}

━━━ {texts['18m_title']} ━━━

**ПВ 30%** — {fmt_rub(calc['pv_30_18'])} (+9%)
└ 18 × {fmt_rub(calc['monthly_30_18'])}
└ Итого: {fmt_rub(calc['final_price_30'])}

**ПВ 40%** — {fmt_rub(calc['pv_40_18'])} (+7%)
└ 8×250К, 9-й: {fmt_rub(calc['payment_9th'])}, 8×250К, 18-й: {fmt_rub(calc['last_40_18'])}
└ Итого: {fmt_rub(calc['final_price_40'])}

**ПВ 50%** — {fmt_rub(calc['pv_50_18'])} (+4%)
└ 8×150К, 9-й: {fmt_rub(calc['payment_9th'])}, 8×150К, 18-й: {fmt_rub(calc['last_50_18'])}
└ Итого: {fmt_rub(calc['final_price_50'])}
"""
def format_short_text(calc: Dict[str, Any]) -> str:
    """Короткий вариант для inline-ответов."""
    return f"""💰 Лот {calc['code']} ({calc['area']} м²)

**12 мес (0%):** от {fmt_rub(calc['pv_30_12'])} ПВ
**18 мес:** от {fmt_rub(calc['pv_30_18'])} ПВ (+9%)

Итого от {fmt_rub(calc['final_price_30'])}"""
