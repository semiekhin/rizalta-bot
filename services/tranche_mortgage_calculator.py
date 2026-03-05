"""
Калькулятор траншевой ипотеки RIZALTA.
3 транша по 8 месяцев, срок 20 лет.

v1.1 (03.03.2026) — service_fee 150 000
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

CONFIG_PATH = Path(__file__).parent.parent / "data" / "tranche_mortgage_config.json"

SERVICE_FEE = 150_000


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _annuity(principal: float, monthly_rate: float, months: int) -> float:
    if principal <= 0 or months <= 0 or monthly_rate <= 0:
        return 0
    x = (1 + monthly_rate) ** months
    return principal * monthly_rate * x / (x - 1)


def _remaining_balance(principal: float, monthly_rate: float, total_months: int, payments_made: int) -> float:
    r = monthly_rate
    x = (1 + r) ** total_months
    y = (1 + r) ** payments_made
    return principal * (x - y) / (x - 1)


def _get_price_range(price: int) -> str:
    if price < 20_000_000:
        return "under_20m"
    elif price <= 30_000_000:
        return "20m_30m"
    else:
        return "over_30m"


def get_down_payment_options() -> List[float]:
    cfg = load_config()
    return [float(k) for k in cfg["down_payment_options"].keys()]


def calc_tranche_mortgage(
    price: int,
    down_payment_pct: float = 30.1
) -> Optional[Dict[str, Any]]:
    """
    Рассчитывает траншевую ипотеку.
    Сумма ипотеки = (цена - 150 000) * (1 - ПВ%)
    """
    cfg = load_config()
    N = cfg["term_months"]
    tp = cfg["tranche_period_months"]

    dp_key = str(down_payment_pct)
    if dp_key not in cfg["down_payment_options"]:
        dp_key = "30.1"

    dp_opts = cfg["down_payment_options"][dp_key]
    rate_annual = dp_opts["rate"]
    pct = dp_opts["pct"]

    base_price = price - SERVICE_FEE
    down_payment = int(base_price * pct / 100)
    mortgage_total = base_price - down_payment

    price_range = _get_price_range(price)
    tranche_cfg = cfg["tranche_amounts"][dp_key][price_range]
    t1 = tranche_cfg[0]
    t2 = tranche_cfg[1]
    t3 = mortgage_total - t1 - t2

    if t3 <= 0:
        return None

    r = rate_annual / 100 / 12

    ep1 = _annuity(t1, r, N)
    b1 = _remaining_balance(t1, r, N, tp)
    ep2 = _annuity(b1 + t2, r, N - tp)
    b2 = _remaining_balance(b1 + t2, r, N - tp, tp)
    ep3 = _annuity(b2 + t3, r, N - 2 * tp)

    total_paid = (
        down_payment
        + ep1 * tp
        + ep2 * tp
        + ep3 * (N - 2 * tp)
    )
    overpayment = total_paid - price

    return {
        "price": price,
        "base_price": base_price,
        "service_fee": SERVICE_FEE,
        "down_payment_pct": pct,
        "down_payment": down_payment,
        "rate": rate_annual,
        "term_months": N,
        "term_years": N // 12,
        "tranche_period": tp,
        "tranche_1": t1,
        "tranche_2": t2,
        "tranche_3": t3,
        "mortgage_total": mortgage_total,
        "ep_1": int(round(ep1)),
        "ep_2": int(round(ep2)),
        "ep_3": int(round(ep3)),
        "total_paid": int(round(total_paid)),
        "overpayment": int(round(overpayment)),
        "price_range": price_range,
    }


def calc_all_scenarios(price: int) -> List[Optional[Dict[str, Any]]]:
    """Рассчитывает все 4 сценария ПВ для одного лота."""
    results = []
    for dp in get_down_payment_options():
        results.append(calc_tranche_mortgage(price, dp))
    return results
