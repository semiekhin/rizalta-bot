#!/usr/bin/env python3
"""
Сравнение доходности: Депозит vs RIZALTA
Версия 2.0 — на основе официальных данных ЦБ РФ

Источники:
- Ключевая ставка и прогноз: cbr.ru
- Ставки вкладов топ-10: cbr.ru/statistics/avgprocstav/
- Данные RIZALTA: таблица застройщика

Дата актуализации: 18.12.2025
"""

from dataclasses import dataclass
from typing import Dict, List
from services.deposit_calculator import (
    calculate_deposit,
    calculate_all_scenarios,
    DepositResult,
)


@dataclass
class RizaltaYearResult:
    """Результат RIZALTA за один год."""
    year: int
    start_value: float
    growth_profit: float
    rental_profit: float
    total_profit: float
    end_value: float
    cumulative_profit: float


@dataclass
class RizaltaResult:
    """Результат расчёта RIZALTA."""
    initial_cost: float
    area_m2: float
    years: int
    yearly_results: List[RizaltaYearResult]
    total_growth_profit: float
    total_rental_profit: float
    total_profit: float
    final_value: float
    total_roi_pct: float


@dataclass
class ComparisonResult:
    """Результат сравнения."""
    amount: float
    years: int
    deposit: Dict[str, DepositResult]  # base, optimistic, pessimistic
    rizalta: RizaltaResult
    advantage_vs_base: float
    advantage_pct_vs_base: float


# =============================================================================
# ДАННЫЕ RIZALTA (из таблицы застройщика)
# =============================================================================

# Коэффициенты роста стоимости
RIZALTA_GROWTH = {
    2025: 0.18,   # +18%
    2026: 0.20,   # +20%
    2027: 0.20,   # +20%
    2028: 0.10,   # +10%
    2029: 0.088,  # +8.8%
    2030: 0.088,
    2031: 0.088,
    2032: 0.088,
    2033: 0.088,
    2034: 0.088,
    2035: 0.088,
}

# Арендные ставки (₽/м²/сутки)
RENTAL_RATE_PER_M2 = {
    2028: 664.18,
    2029: 723.88,
    2030: 787.31,
    2031: 858.21,
    2032: 932.84,
    2033: 1014.93,
    2034: 1104.48,
    2035: 1201.49,
}

# Загрузка (%)
OCCUPANCY = {
    2028: 40,
    2029: 60,
    2030: 70,
    2031: 70,
    2032: 70,
    2033: 70,
    2034: 70,
    2035: 70,
}

EXPENSES_PCT = 50  # Расходы на эксплуатацию


def calculate_rizalta(
    amount: float,
    years: int,
    area_m2: float = 26.8,  # Минимальный лот
) -> RizaltaResult:
    """Рассчитывает доходность RIZALTA."""
    
    initial_cost = amount
    yearly_results = []
    
    cumulative_growth = 0
    cumulative_rental = 0
    start_year = 2026
    
    for i in range(years):
        year = start_year + i
        
        # Рост стоимости
        growth_rate = RIZALTA_GROWTH.get(year, 0.088)
        growth_profit = (initial_cost + cumulative_growth) * growth_rate
        cumulative_growth += growth_profit
        
        # Аренда (с 2028)
        rental_profit = 0
        if year >= 2028:
            rate_m2 = RENTAL_RATE_PER_M2.get(year, 0)
            occupancy = OCCUPANCY.get(year, 70)
            days = 366 if year in [2028, 2032] else 365
            
            gross = days * rate_m2 * area_m2 * occupancy / 100
            rental_profit = gross * (1 - EXPENSES_PCT / 100)
        
        cumulative_rental += rental_profit
        
        end_value = initial_cost + cumulative_growth
        cumulative_profit = cumulative_growth + cumulative_rental
        
        yearly_results.append(RizaltaYearResult(
            year=year,
            start_value=round(initial_cost + cumulative_growth - growth_profit, 2),
            growth_profit=round(growth_profit, 2),
            rental_profit=round(rental_profit, 2),
            total_profit=round(growth_profit + rental_profit, 2),
            end_value=round(end_value, 2),
            cumulative_profit=round(cumulative_profit, 2),
        ))
    
    total_profit = cumulative_growth + cumulative_rental
    total_roi = (total_profit / initial_cost) * 100
    
    return RizaltaResult(
        initial_cost=initial_cost,
        area_m2=area_m2,
        years=years,
        yearly_results=yearly_results,
        total_growth_profit=round(cumulative_growth, 2),
        total_rental_profit=round(cumulative_rental, 2),
        total_profit=round(total_profit, 2),
        final_value=round(initial_cost + cumulative_growth, 2),
        total_roi_pct=round(total_roi, 2),
    )


def compare_investments(amount: float, years: int, area_m2: float = 26.8) -> ComparisonResult:
    """Сравнивает депозит и RIZALTA."""
    
    deposit = calculate_all_scenarios(amount, years)
    rizalta = calculate_rizalta(amount, years, area_m2)
    
    # Сравнение с базовым сценарием (прогноз ЦБ)
    base = deposit["base"]
    advantage = rizalta.total_profit - base.total_net_interest
    advantage_pct = (advantage / amount) * 100
    
    return ComparisonResult(
        amount=amount,
        years=years,
        deposit=deposit,
        rizalta=rizalta,
        advantage_vs_base=round(advantage, 2),
        advantage_pct_vs_base=round(advantage_pct, 2),
    )


def fmt(value: float) -> str:
    """Форматирует число."""
    return f"{int(round(value)):,}".replace(",", " ")


def format_comparison_short(result: ComparisonResult) -> str:
    """Краткое сравнение."""
    lines = []
    
    lines.append(f"📊 <b>Депозит vs RIZALTA</b>")
    lines.append(f"💰 Сумма: {fmt(result.amount)} ₽ │ Срок: {pluralize_years(result.years)}")
    lines.append("")
    
    # Депозит (базовый)
    dep = result.deposit["base"]
    lines.append(f"🏦 <b>Депозит</b> (прогноз ЦБ: ключевая 14% → 7%)")
    lines.append(f"   Капитал: {fmt(dep.final_balance)} ₽")
    lines.append(f"   Чистый доход: +{fmt(dep.total_net_interest)} ₽")
    lines.append(f"   Налог: -{fmt(dep.total_tax)} ₽")
    lines.append(f"   ROI: {dep.total_roi_pct:.0f}%")
    lines.append("")
    
    # RIZALTA
    riz = result.rizalta
    total_capital = riz.final_value + riz.total_rental_profit
    lines.append(f"🏡 <b>RIZALTA</b>")
    lines.append(f"   Капитал: {fmt(total_capital)} ₽")
    lines.append(f"   Рост стоимости: +{fmt(riz.total_growth_profit)} ₽")
    if riz.total_rental_profit > 0:
        lines.append(f"   Аренда: +{fmt(riz.total_rental_profit)} ₽")
    lines.append(f"   <b>Общий доход: +{fmt(riz.total_profit)} ₽</b>")
    lines.append(f"   ROI: <b>{riz.total_roi_pct:.0f}%</b>")
    lines.append("")
    
    # Вывод
    if result.advantage_vs_base > 0:
        lines.append(f"✅ <b>RIZALTA выгоднее на {fmt(result.advantage_vs_base)} ₽</b>")
        lines.append(f"   (+{result.advantage_pct_vs_base:.0f}% к капиталу)")
    else:
        lines.append(f"⚠️ Депозит выгоднее на {fmt(-result.advantage_vs_base)} ₽")
    
    return "\n".join(lines)


def format_comparison_table(amount: float, area_m2: float = 26.8) -> str:
    """Таблица сравнения всех периодов."""
    lines = []
    lines.append(f"📊 <b>Сравнение инвестиций: {fmt(amount)} ₽</b>")
    lines.append("")
    lines.append("Период │ Депозит* │ RIZALTA │ Разница")
    lines.append("───────┼──────────┼─────────┼────────")
    
    for years in [1, 3, 5, 11]:
        r = compare_investments(amount, years, area_m2)
        dep_roi = f"{r.deposit['base'].total_roi_pct:.0f}%"
        riz_roi = f"{r.rizalta.total_roi_pct:.0f}%"
        
        if r.advantage_vs_base > 0:
            diff = f"+{r.advantage_pct_vs_base:.0f}%"
        else:
            diff = f"{r.advantage_pct_vs_base:.0f}%"
        
        lines.append(f"{pluralize_years(years):>10} │ {dep_roi:>8} │ {riz_roi:>7} │ {diff:>7}")
    
    lines.append("")
    lines.append("<i>* Депозит: базовый сценарий ЦБ (ключ. 14% → 7%)</i>")
    lines.append("<i>  Источник: cbr.ru, прогноз на 2026+</i>")
    
    return "\n".join(lines)


def format_comparison_full(result: ComparisonResult) -> str:
    """Полный отчёт."""
    lines = []
    
    lines.append(f"📊 <b>Полное сравнение: Депозит vs RIZALTA</b>")
    lines.append(f"💰 Сумма: {fmt(result.amount)} ₽")
    lines.append(f"📅 Горизонт: {pluralize_years(result.years)} (2026-{2025 + result.years})")
    lines.append("")
    
    # Депозит — все сценарии
    lines.append("🏦 <b>ДЕПОЗИТ</b>")
    lines.append("<i>Источник: ЦБ РФ (cbr.ru/statistics/avgprocstav/)</i>")
    lines.append("")
    
    scenarios = [
        ("pessimistic", "📈 Пессимистичный (ставки выше)"),
        ("base", "📊 Базовый (прогноз ЦБ)"),
        ("optimistic", "📉 Оптимистичный (быстрое снижение)"),
    ]
    
    for key, label in scenarios:
        dep = result.deposit[key]
        lines.append(f"<b>{label}</b>")
        lines.append(f"  • Чистый доход: {fmt(dep.total_net_interest)} ₽")
        lines.append(f"  • Налог: -{fmt(dep.total_tax)} ₽")
        lines.append(f"  • Капитал: {fmt(dep.final_balance)} ₽")
        lines.append(f"  • ROI: {dep.total_roi_pct:.1f}%")
        lines.append("")
    
    # RIZALTA
    riz = result.rizalta
    lines.append("🏡 <b>RIZALTA RESORT</b>")
    lines.append("<i>Источник: таблица застройщика</i>")
    lines.append("")
    
    if result.years >= 3:
        lines.append("<b>По годам:</b>")
        for yr in riz.yearly_results[:min(6, len(riz.yearly_results))]:
            rental = f" + аренда {fmt(yr.rental_profit)}" if yr.rental_profit > 0 else ""
            lines.append(f"  {yr.year}: рост +{fmt(yr.growth_profit)} ₽{rental}")
        if len(riz.yearly_results) > 6:
            lines.append("  ...")
        lines.append("")
    
    lines.append("<b>Итого:</b>")
    lines.append(f"  • Рост стоимости: +{fmt(riz.total_growth_profit)} ₽")
    lines.append(f"  • Доход от аренды: +{fmt(riz.total_rental_profit)} ₽")
    lines.append(f"  • <b>Общий доход: +{fmt(riz.total_profit)} ₽</b>")
    lines.append(f"  • Стоимость актива: {fmt(riz.final_value)} ₽")
    lines.append(f"  • <b>ROI: {riz.total_roi_pct:.1f}%</b>")
    lines.append("")
    
    # Сравнение
    lines.append("═" * 40)
    lines.append("")
    lines.append("🎯 <b>ПРЕИМУЩЕСТВО RIZALTA</b>")
    lines.append("")
    
    for key, label in [("pessimistic", "vs Депозит (высокие ставки)"),
                       ("base", "vs Депозит (базовый)"),
                       ("optimistic", "vs Депозит (низкие ставки)")]:
        dep = result.deposit[key]
        adv = riz.total_profit - dep.total_net_interest
        adv_pct = (adv / result.amount) * 100
        
        if adv > 0:
            lines.append(f"✅ {label}: <b>+{fmt(adv)} ₽</b> (+{adv_pct:.0f}%)")
        else:
            lines.append(f"⚠️ {label}: {fmt(adv)} ₽ ({adv_pct:.0f}%)")
    
    lines.append("")
    lines.append("💡 <b>Ключевые факторы:</b>")
    lines.append("• ЦБ прогнозирует снижение ставки до 7%")
    lines.append("• Налог 13-15% «съедает» часть дохода по депозиту")
    lines.append("• RIZALTA: рост стоимости + пассивный доход с 2028")
    lines.append("• Недвижимость — защита от инфляции")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("СРАВНЕНИЕ: ДЕПОЗИТ vs RIZALTA (данные ЦБ)")
    print("=" * 60)
    
    amount = 15_000_000
    
    print(format_comparison_table(amount))
    
    for years in [1, 3, 5, 11]:
        print(f"\n{'─' * 60}")
        r = compare_investments(amount, years)
        print(format_comparison_short(r))


def pluralize_years(n: int) -> str:
    """Склонение слова 'год'."""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} год"
    elif n % 10 in [2, 3, 4] and n % 100 not in [12, 13, 14]:
        return f"{n} года"
    else:
        return f"{n} лет"
