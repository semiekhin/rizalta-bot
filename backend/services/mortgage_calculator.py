"""Mortgage calculator — Sovcombank "Reduced Payment" program.
Ported from /opt/bot-dev/services/mortgage_calculator.py."""

import json
import os
import subprocess
import tempfile
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


def _fmt(val: int) -> str:
    return f"{val:,}".replace(",", " ")


def generate_mortgage_pdf(data: Dict[str, Any]) -> str:
    """Generates PDF with mortgage calculation. Returns path to temp file."""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #1a1a1a; }}
    h1 {{ font-size: 20px; color: #1a3a5c; margin-bottom: 5px; }}
    h2 {{ font-size: 14px; color: #555; font-weight: normal; margin-top: 0; }}
    table {{ width: 75%; border-collapse: collapse; margin-top: 20px; }}
    th {{ background: #1a3a5c; color: white; padding: 10px 14px; text-align: left; font-size: 13px; }}
    td {{ padding: 8px 14px; border-bottom: 1px solid #ddd; font-size: 13px; }}
    td.val {{ text-align: right; font-family: monospace; font-weight: bold; }}
    tr:nth-child(even) {{ background: #f5f7fa; }}
    .highlight td {{ background: #e8f5e9; }}
    .footer {{ margin-top: 30px; font-size: 11px; color: #888; }}
</style></head><body>
    <h1>🏦 Ипотека Совкомбанк — Акция «Сниженный платёж»</h1>
    <h2>Тариф: {data['tariff_name']} | Срок: {data['loan_term_years']} лет | ПВ: {data['down_payment_pct']}%</h2>
    <table>
        <tr><th colspan="2">Параметры расчёта</th></tr>
        <tr><td>Стоимость объекта</td><td class="val">{_fmt(data['price'])} ₽</td></tr>
        <tr><td>Первоначальный взнос ({data['down_payment_pct']}%)</td><td class="val">{_fmt(data['down_payment'])} ₽</td></tr>
        <tr><td>Сумма кредита</td><td class="val">{_fmt(data['loan_amount'])} ₽</td></tr>
        <tr><th colspan="2">Льготный период ({data['grace_months']} мес)</th></tr>
        <tr class="highlight"><td>Платёж в льготный период</td><td class="val">{_fmt(data['grace_payment'])} ₽/мес</td></tr>
        <tr><td>Комиссия аккредитива</td><td class="val">{data['accreditive_pct']}%</td></tr>
        <tr><th colspan="2">После льготного ({data['remaining_months']} мес)</th></tr>
        <tr><td>Ставка</td><td class="val">{data['rate_after_grace']}%</td></tr>
        <tr class="highlight"><td>Ежемесячный платёж</td><td class="val">{_fmt(data['regular_payment'])} ₽/мес</td></tr>
        <tr><th colspan="2">Итого</th></tr>
        <tr><td>Общая сумма выплат</td><td class="val">{_fmt(data['total_paid'])} ₽</td></tr>
        <tr><td>Переплата</td><td class="val">{_fmt(data['overpayment'])} ₽</td></tr>
    </table>
    <p class="footer">Расчёт предварительный. Точные условия уточняйте в банке.</p>
</body></html>"""

    tmp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    tmp_html.write(html.encode())
    tmp_html.close()

    pdf_path = tmp_html.name.replace(".html", ".pdf")
    subprocess.run([
        "wkhtmltopdf", "--quiet",
        "--page-size", "A4",
        "--margin-top", "10mm",
        "--margin-bottom", "10mm",
        tmp_html.name, pdf_path
    ], check=True)

    os.unlink(tmp_html.name)
    return pdf_path
