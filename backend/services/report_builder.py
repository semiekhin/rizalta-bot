"""Report data builder — collects all data for AI reports in one JSON."""

import json
from dataclasses import asdict

from services.tool_definitions import (
    execute_get_lot_details,
    execute_search_lots,
    execute_calculate_roi,
)
from services.installment_calculator import calc_12m, calc_18m, calc_full
from services.deposit_calculator import calculate_all_scenarios
from services.data_loader import load_finance


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

    # 4. Сравнение с депозитом (dataclass → dict)
    deposit_raw = calculate_all_scenarios(price, years=11)
    deposit = {k: asdict(v) for k, v in deposit_raw.items()}

    # 5. Финансовые параметры проекта
    finance = load_finance()

    return {
        "lot": lot,
        "roi": roi,
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
        "limit": 10,
    })
    lots_installment = json.loads(lots_installment_json)

    # ROI для топ лотов (до 5 штук)
    roi_results = {}
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
                roi_results[code] = json.loads(roi_json)

    # Депозит для сравнения (dataclass → dict)
    deposit_raw = calculate_all_scenarios(budget, years=11)
    deposit = {k: asdict(v) for k, v in deposit_raw.items()}

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
        "deposit_comparison": deposit,
        "installment_programs": finance.get("installment_programs", []),
        "project": {
            "name": finance.get("project", "RIZALTA Resort Belokurikha"),
            "completion": finance.get("completion_year", 2027),
        },
    }
