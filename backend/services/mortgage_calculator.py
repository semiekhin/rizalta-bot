"""Mortgage calculator — Sovcombank "Reduced Payment" program.
Ported from /opt/bot-dev/services/mortgage_calculator.py."""

import json
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path(__file__).parent.parent / "data" / "mortgage_config.json"


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calc_annuity_coefficient(annual_rate: float, months: int) -> float:
    if annual_rate <= 0 or months <= 0:
        return 0
    monthly_rate = annual_rate / 100 / 12
    power = (1 + monthly_rate) ** months
    return (monthly_rate * power) / (power - 1)


def calc_mortgage(
    price: int,
    down_payment_pct: int = 30,
    tariff: str = "base",
    loan_term_months: int = 360,
) -> Dict[str, Any]:
    cfg = load_config()
    service_fee = cfg["service_fee"]

    dp_key = str(down_payment_pct)
    if dp_key not in cfg["down_payment_options"]:
        dp_key = "30"
    dp_opts = cfg["down_payment_options"][dp_key]

    if tariff not in cfg["tariffs"]:
        tariff = "base"
    tariff_opts = cfg["tariffs"][tariff]

    base_price = price - service_fee
    down_payment = int(base_price * dp_opts["pct"] / 100)
    remaining = base_price - down_payment
    markup = int(remaining * dp_opts["markup_pct"] / 100)
    object_price = price + markup
    loan_amount = object_price - down_payment
    grace_months = dp_opts["grace_months"]
    grace_payment = int(loan_amount * tariff_opts["accreditive_pct"] / 100)
    remaining_months = loan_term_months - grace_months
    annuity_coef = calc_annuity_coefficient(tariff_opts["rate_after_grace"], remaining_months)
    regular_payment = int(loan_amount * annuity_coef)
    total_grace_payments = grace_payment * grace_months
    total_regular_payments = regular_payment * remaining_months
    total_paid = down_payment + total_grace_payments + total_regular_payments
    overpayment = total_paid - price

    return {
        "price": price,
        "base_price": base_price,
        "service_fee": service_fee,
        "down_payment_pct": dp_opts["pct"],
        "tariff": tariff,
        "tariff_name": tariff_opts["name"],
        "loan_term_months": loan_term_months,
        "loan_term_years": loan_term_months // 12,
        "down_payment": down_payment,
        "markup": markup,
        "markup_pct": dp_opts["markup_pct"],
        "object_price": object_price,
        "loan_amount": loan_amount,
        "grace_months": grace_months,
        "grace_payment": grace_payment,
        "grace_rate": tariff_opts["grace_rate"],
        "accreditive_pct": tariff_opts["accreditive_pct"],
        "remaining_months": remaining_months,
        "regular_payment": regular_payment,
        "rate_after_grace": tariff_opts["rate_after_grace"],
        "total_paid": total_paid,
        "overpayment": overpayment,
    }


def get_mortgage_options() -> Dict[str, Any]:
    """Returns available options for the UI."""
    cfg = load_config()
    return {
        "down_payment_options": [int(k) for k in cfg["down_payment_options"].keys()],
        "tariffs": {k: v["name"] for k, v in cfg["tariffs"].items()},
        "loan_terms": cfg["loan_terms"],
        "service_fee": cfg["service_fee"],
    }
