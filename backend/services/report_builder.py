"""Report data builder — collects all data for AI reports in one JSON."""

import json
import os
import sqlite3
from dataclasses import asdict

from services.tool_definitions import (
    execute_get_lot_details,
    execute_search_lots,
    execute_calculate_roi,
)
from services.installment_calculator import calc_12m, calc_18m, calc_full
from services.deposit_calculator import calculate_all_scenarios
from services.data_loader import load_finance
from services.calculator import calculate_investment_metrics, calculate_roi, RATE_PER_M2, OCCUPANCY, DAYS_IN_YEAR, EXPENSES_PCT


def slim_deposit(scenarios: dict) -> dict:
    """Оставить только итоговые цифры для AI (без yearly_details)."""
    result = {}
    for name, data in scenarios.items():
        if hasattr(data, '__dict__'):
            d = data.__dict__ if not hasattr(data, '_asdict') else data._asdict()
        else:
            d = data
        result[name] = {
            "final_balance": d.get("final_balance"),
            "total_net_interest": d.get("total_net_interest"),
            "total_roi_pct": d.get("total_roi_pct"),
            "effective_rate": d.get("effective_rate"),
        }
    return result


def slim_roi(roi: dict) -> dict:
    """Убрать highlights, оставить только totals."""
    return {k: v for k, v in roi.items() if k != "highlights"}


def build_lot_report_data(code: str, building: int | None = None) -> dict:
    """Собрать ВСЕ данные по лоту для фин. отчёта.

    Вызывает функции напрямую (не через AI).
    Результат — один JSON со всеми цифрами.
    """
    # 1. Детали лота
    args = {"code": code}
    if building:
        args["building"] = building
    lot_json = execute_get_lot_details(args)
    lot = json.loads(lot_json)

    if "error" in lot:
        return {"error": lot["error"]}
    if lot.get("multiple"):
        return lot  # AI уточнит корпус

    price = lot["price_rub"]

    # 2. ROI расчёт
    roi_json = execute_calculate_roi({
        "code": code,
        "building": building or lot.get("building_num"),
    })
    roi = json.loads(roi_json)

    # 3. Варианты рассрочки
    installment = {
        "full_payment": calc_full(price),
        "installment_12m": calc_12m(price),
        "installment_18m": calc_18m(price),
    }

    # 4. Сравнение с депозитом (только итоги)
    deposit_raw = calculate_all_scenarios(price, years=11)
    deposit = slim_deposit(deposit_raw)

    # 5. Инвестиционные метрики (NOI, Cap Rate, CoC, Equity Multiple)
    metrics = calculate_investment_metrics(lot["area_m2"], price)

    # 6. Финансовые параметры проекта
    finance = load_finance()

    return {
        "lot": lot,
        "roi": slim_roi(roi),
        "metrics": metrics,
        "installment": installment,
        "deposit_comparison": deposit,
        "project": {
            "name": finance.get("project", "RIZALTA Resort Belokurikha"),
            "completion": finance.get("completion_year", 2027),
            "daily_rate": finance.get("defaults", {}).get("daily_rate_rub", 15000),
            "occupancy": finance.get("defaults", {}).get("occupancy_pct", 60),
            "expenses": finance.get("defaults", {}).get("expenses_pct", 50),
        },
    }


def build_portfolio_data(budget: int) -> dict:
    """Собрать данные для портфельного анализа.

    1. Найти лоты в бюджете (100% оплата)
    2. Найти лоты для рассрочки (ПВ 30% от бюджета)
    3. Рассчитать ROI для топ-кандидатов
    """
    # Стратегия A: один лот за 100% (со скидкой 5%)
    max_price_full = int(budget / 0.95)
    lots_full_json = execute_search_lots({
        "max_price": max_price_full,
        "status": "available",
        "limit": 5,
    })
    lots_full = json.loads(lots_full_json)

    # Стратегия B: лоты в рассрочку (ПВ 30% = бюджет)
    max_price_installment = int(budget / 0.3)
    lots_installment_json = execute_search_lots({
        "max_price": max_price_installment,
        "status": "available",
        "limit": 5,
    })
    lots_installment = json.loads(lots_installment_json)

    # ROI + метрики для топ лотов (до 5 штук)
    roi_results = {}
    metrics_results = {}
    all_codes = set()

    for lot_list in [lots_full.get("lots", []), lots_installment.get("lots", [])]:
        for lot in lot_list[:5]:
            code = lot["code"]
            if code not in all_codes:
                all_codes.add(code)
                roi_json = execute_calculate_roi({
                    "area": lot["area_m2"],
                    "price": lot["price_rub"],
                })
                roi_results[code] = slim_roi(json.loads(roi_json))
                metrics_results[code] = calculate_investment_metrics(
                    lot["area_m2"], lot["price_rub"]
                )

    # Депозит для сравнения (только итоги)
    deposit_raw = calculate_all_scenarios(budget, years=11)
    deposit = slim_deposit(deposit_raw)

    finance = load_finance()

    return {
        "budget": budget,
        "strategy_a": {
            "name": "100% оплата (скидка 5%)",
            "lots": lots_full,
        },
        "strategy_b": {
            "name": "Рассрочка (ПВ 30%)",
            "max_lot_price": max_price_installment,
            "lots": lots_installment,
        },
        "roi": roi_results,
        "metrics": metrics_results,
        "deposit_comparison": deposit,
        "installment_programs": finance.get("installment_programs", []),
        "project": {
            "name": finance.get("project", "RIZALTA Resort Belokurikha"),
            "completion": finance.get("completion_year", 2027),
        },
    }


# ---------------------------------------------------------------------------
# Portfolio v2 — 3 investment scenarios
# ---------------------------------------------------------------------------

SERVICE_FEE = 150_000  # from installment_config.json
MARKUP_18M_30_PCT = 0.09  # 9% markup on remaining after 30% DP


def _load_all_available_lots() -> list[dict]:
    """Load all available lots directly from DB (no limit cap)."""
    db_path = os.getenv("PROPERTIES_DB", "/opt/bot/properties.db")
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT code, building, floor, rooms, area_m2, price_rub, "
        "price_per_m2_rub, status FROM units "
        "WHERE status = 'available' ORDER BY price_rub ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _enrich_lots(lots: list[dict], budget: int) -> list[dict]:
    """Pre-compute ROI + metrics for lots within budget.

    Only enriches lots where price * 0.30 <= budget (max leverage scenario).
    Computes metrics inline from ROI result — avoids double calculate_roi().
    """
    max_price = budget / 0.30  # cheapest entry = 30% DP
    # Stabilized year 2030 constants (same as calculator.py)
    rate_m2 = RATE_PER_M2[2030]      # 787.31
    occ = OCCUPANCY[2030] / 100      # 0.70
    days = DAYS_IN_YEAR[2030]        # 365
    exp = EXPENSES_PCT               # 0.50

    enriched = []
    for lot in lots:
        price = lot["price_rub"]
        if price > max_price:
            continue

        area = lot["area_m2"]
        roi = calculate_roi(area, price)

        # Inline metrics (avoids calling calculate_investment_metrics → 2nd calculate_roi)
        gross_income = days * rate_m2 * area * occ
        noi = int(gross_income * (1 - exp))
        cap_rate = round(noi / price * 100, 1) if price > 0 else 0
        coc_full = round(noi / (price * 0.95) * 100, 1) if price > 0 else 0
        coc_installment = round(noi / (price * 0.30) * 100, 1) if price > 0 else 0
        invested_full = price * 0.95
        eq_full = round((roi["final_value"] + roi["total_rental"]) / invested_full, 2) if invested_full > 0 else 0
        eq_inst = round((roi["final_value"] + roi["total_rental"]) / price, 2) if price > 0 else 0

        enriched.append({
            **lot,
            "_metrics": {
                "noi": noi, "cap_rate": cap_rate,
                "coc_full": coc_full, "coc_installment": coc_installment,
                "equity_multiple_full": eq_full, "equity_multiple_installment": eq_inst,
                "roi_pct": roi["roi_pct"], "avg_annual_pct": roi["avg_annual_pct"],
                "total_rental": roi["total_rental"], "total_growth": roi["total_growth"],
                "final_value": roi["final_value"], "gross_income": int(gross_income),
            },
            "roi_pct": roi["roi_pct"],
            "total_profit": roi["total_rental"] + roi["total_growth"],
            "total_rental": roi["total_rental"],
            "total_growth": roi["total_growth"],
            "final_value": roi["final_value"],
            "noi": noi,
            "cap_rate": cap_rate,
            "coc_full": coc_full,
            "coc_installment": coc_installment,
        })
    return enriched


def _scenario_premium(lots: list[dict], budget: int) -> dict:
    """Scenario 1: One premium lot, 100% payment with 5% discount."""
    max_price = budget / 0.95
    eligible = sorted(
        [l for l in lots if l["price_rub"] <= max_price],
        key=lambda l: -l["price_rub"],
    )

    if not eligible:
        return {"name": "Один премиальный лот (100%)", "error": "no_lots"}

    lot = eligible[0]
    price = lot["price_rub"]
    discounted = int(price * 0.95)
    remaining = budget - discounted

    return {
        "name": "Один премиальный лот (100%)",
        "lot": lot,
        "discounted_price": discounted,
        "remaining_cash": remaining,
        "metrics": lot["_metrics"],
        "roi_pct": lot["roi_pct"],
        "total_profit": lot["total_profit"],
        "total_rental": lot["total_rental"],
        "total_growth": lot["total_growth"],
        "final_value": lot["final_value"],
        "reasoning": f"Самый дорогой доступный лот: {lot['code']}, {lot['area_m2']}м², К{lot.get('building', '?')}, этаж {lot.get('floor', '?')}. Макс. площадь = макс. арендный доход.",
    }


def _scenario_portfolio_full(lots: list[dict], budget: int) -> dict:
    """Scenario 2: Portfolio with 100% payment, building rotation for diversification."""
    # Group by building, sort each by price DESC
    by_building = {}
    for lot in lots:
        b = lot.get("building", 0)
        dp = int(lot["price_rub"] * 0.95)
        if dp <= budget:
            by_building.setdefault(b, []).append({**lot, "discounted_price": dp})

    for b in by_building:
        by_building[b].sort(key=lambda l: l["price_rub"])  # ASC — pack more lots

    # Round-robin: К1 → К2 → К3 → К1 → ...
    buildings = sorted(by_building.keys())
    pointers = {b: 0 for b in buildings}

    selected = []
    spent = 0
    used_keys = set()  # (building, floor) to avoid same building+floor

    max_rounds = 50  # safety limit
    rounds = 0
    while rounds < max_rounds:
        added_this_round = False
        for b in buildings:
            bl = by_building.get(b, [])
            while pointers[b] < len(bl):
                candidate = bl[pointers[b]]
                pointers[b] += 1
                key = (candidate.get("building"), candidate.get("floor"))

                # Skip if same building+floor already selected
                if key in used_keys:
                    continue

                # Skip if same area+price combo (near-duplicate)
                if any(
                    abs(s["area_m2"] - candidate["area_m2"]) < 1.0
                    and s.get("building") == candidate.get("building")
                    for s in selected
                ):
                    continue

                if spent + candidate["discounted_price"] <= budget:
                    selected.append(candidate)
                    spent += candidate["discounted_price"]
                    used_keys.add(key)
                    added_this_round = True
                    break  # next building

        rounds += 1
        if not added_this_round:
            break

    if not selected:
        return {"name": "Портфель 100% оплата", "error": "no_lots"}

    return {
        "name": "Портфель 100% оплата",
        "lots": selected,
        "lot_count": len(selected),
        "total_invested": spent,
        "remaining_cash": budget - spent,
        "total_noi": sum(l["noi"] for l in selected),
        "total_profit": sum(l["total_profit"] for l in selected),
        "total_rental": sum(l["total_rental"] for l in selected),
        "total_growth": sum(l["total_growth"] for l in selected),
        "avg_roi_pct": round(sum(l["roi_pct"] for l in selected) / len(selected), 1),
        "reasoning": f"Диверсификация: {len(set(l.get('building') for l in selected))} корпуса, {len(set(l.get('floor') for l in selected))} этажей. Round-robin подбор от дорогих к дешёвым.",
    }


def _scenario_max_leverage(lots: list[dict], budget: int) -> dict:
    """Scenario 3: Maximum leverage via installment, DP 30%, building rotation."""
    by_building = {}
    for lot in lots:
        b = lot.get("building", 0)
        dp = int(lot["price_rub"] * 0.30)
        if dp <= budget:
            by_building.setdefault(b, []).append(lot)

    for b in by_building:
        by_building[b].sort(key=lambda l: -l["price_rub"])

    buildings = sorted(by_building.keys())
    pointers = {b: 0 for b in buildings}

    selected = []
    spent = 0
    used_keys = set()

    max_rounds = 50
    rounds = 0
    while rounds < max_rounds:
        added_this_round = False
        for b in buildings:
            bl = by_building.get(b, [])
            while pointers[b] < len(bl):
                candidate = bl[pointers[b]]
                pointers[b] += 1
                key = (candidate.get("building"), candidate.get("floor"))

                if key in used_keys:
                    continue

                if any(
                    abs(s["area_m2"] - candidate["area_m2"]) < 1.0
                    and s.get("building") == candidate.get("building")
                    for s in selected
                ):
                    continue

                dp = int(candidate["price_rub"] * 0.30)
                if spent + dp <= budget:
                    price = candidate["price_rub"]
                    base = price - SERVICE_FEE
                    remaining_debt = int(base * 0.70)
                    markup = int(remaining_debt * MARKUP_18M_30_PCT)

                    selected.append({
                        **candidate,
                        "down_payment": dp,
                        "markup": markup,
                        "total_cost": price + markup,
                    })
                    spent += dp
                    used_keys.add(key)
                    added_this_round = True
                    break

        rounds += 1
        if not added_this_round:
            break

    if not selected:
        return {"name": "Максимальное плечо (рассрочка)", "error": "no_lots"}

    total_markup = sum(l["markup"] for l in selected)
    total_profit = sum(l["total_profit"] for l in selected)

    return {
        "name": "Максимальное плечо (рассрочка)",
        "lots": selected,
        "lot_count": len(selected),
        "total_down_payment": spent,
        "total_portfolio_value": sum(l["price_rub"] for l in selected),
        "total_markup": total_markup,
        "total_noi": sum(l["noi"] for l in selected),
        "total_profit": total_profit,
        "total_rental": sum(l["total_rental"] for l in selected),
        "total_growth": sum(l["total_growth"] for l in selected),
        "net_profit": total_profit - total_markup,
        "remaining_cash": budget - spent,
        "avg_coc": round(sum(l["coc_installment"] for l in selected) / len(selected), 1),
        "reasoning": f"Макс. плечо: {len(selected)} лотов, {len(set(l.get('building') for l in selected))} корпуса. ПВ {spent:,}₽ из {budget:,}₽ ({round(spent/budget*100)}%).",
    }


def build_portfolio_data_v2(budget: int) -> dict:
    """Build data for 3-scenario portfolio analysis (v2)."""
    lots = _enrich_lots(_load_all_available_lots(), budget)

    s_premium = _scenario_premium(lots, budget)
    s_portfolio = _scenario_portfolio_full(lots, budget)
    s_leverage = _scenario_max_leverage(lots, budget)

    # Deposit comparison
    deposit_raw = calculate_all_scenarios(budget, years=11)
    deposit = slim_deposit(deposit_raw)
    dep_base_interest = deposit.get("base", {}).get("total_net_interest", 0) or 0

    # Add vs_deposit delta to each scenario
    for scenario in [s_premium, s_portfolio, s_leverage]:
        profit = scenario.get("total_profit", 0) or 0
        scenario["vs_deposit"] = profit - dep_base_interest

    finance = load_finance()

    return {
        "budget": budget,
        "version": 2,
        "scenario_premium": s_premium,
        "scenario_portfolio": s_portfolio,
        "scenario_leverage": s_leverage,
        "deposit_comparison": deposit,
        "project": {
            "name": finance.get("project", "RIZALTA Resort Belokurikha"),
            "completion": finance.get("completion_year", 2027),
        },
    }
