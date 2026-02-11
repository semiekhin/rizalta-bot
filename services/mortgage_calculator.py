"""
Ипотечный калькулятор RIZALTA — Совкомбанк.
Акция "Сниженный платёж" с льготным периодом.

v1.0 (30.01.2026)
"""

import json
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path(__file__).parent.parent / "data" / "mortgage_config.json"


def load_config() -> Dict[str, Any]:
    """Загружает конфиг ипотеки."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_service_fee() -> int:
    """Возвращает сервисный сбор."""
    return load_config()["service_fee"]


def calc_annuity_coefficient(annual_rate: float, months: int) -> float:
    """
    Рассчитывает коэффициент аннуитета.
    
    Формула: K = (r * (1+r)^n) / ((1+r)^n - 1)
    где r = месячная ставка, n = количество месяцев
    """
    if annual_rate <= 0 or months <= 0:
        return 0
    
    monthly_rate = annual_rate / 100 / 12
    power = (1 + monthly_rate) ** months
    return (monthly_rate * power) / (power - 1)


def calc_mortgage(
    price: int,
    down_payment_pct: int = 30,
    tariff: str = "base",
    loan_term_months: int = 360
) -> Dict[str, Any]:
    """
    Рассчитывает ипотеку по программе Совкомбанк "Сниженный платёж".
    
    Args:
        price: Цена лота (полная)
        down_payment_pct: Процент первоначального взноса (30, 40, 50)
        tariff: Тариф ("base" или "profitable")
        loan_term_months: Срок кредита в месяцах (240 или 360)
    
    Returns:
        Dict с результатами расчёта
    """
    cfg = load_config()
    service_fee = cfg["service_fee"]
    
    # Получаем параметры ПВ
    dp_key = str(down_payment_pct)
    if dp_key not in cfg["down_payment_options"]:
        dp_key = "30"
    dp_opts = cfg["down_payment_options"][dp_key]
    
    # Получаем параметры тарифа
    if tariff not in cfg["tariffs"]:
        tariff = "base"
    tariff_opts = cfg["tariffs"][tariff]
    
    # === РАСЧЁТ ===
    
    # 1. База для расчёта (цена минус сервисный сбор)
    base_price = price - service_fee
    
    # 2. Первоначальный взнос (от базы)
    down_payment = int(base_price * dp_opts["pct"] / 100)
    
    # 3. Остаток после ПВ
    remaining = base_price - down_payment
    
    # 4. Удорожание на остаток (за льготный период)
    markup = int(remaining * dp_opts["markup_pct"] / 100)
    
    # 5. Стоимость объекта с удорожанием
    object_price = price + markup
    
    # 6. Сумма кредита = Стоимость объекта - ПВ
    loan_amount = object_price - down_payment
    
    # 7. Льготный период
    grace_months = dp_opts["grace_months"]
    
    # 8. Платёж в льготный период = сумма кредита × комиссия аккредитива
    grace_payment = int(loan_amount * tariff_opts["accreditive_pct"] / 100)
    
    # 9. Платёж после льготного периода (аннуитет)
    remaining_months = loan_term_months - grace_months
    annuity_coef = calc_annuity_coefficient(tariff_opts["rate_after_grace"], remaining_months)
    regular_payment = int(loan_amount * annuity_coef)
    
    # 10. Общая переплата (приблизительная)
    total_grace_payments = grace_payment * grace_months
    total_regular_payments = regular_payment * remaining_months
    total_paid = down_payment + total_grace_payments + total_regular_payments
    overpayment = total_paid - price
    
    return {
        # Входные данные
        "price": price,
        "base_price": base_price,
        "service_fee": service_fee,
        
        # Параметры
        "down_payment_pct": dp_opts["pct"],
        "tariff": tariff,
        "tariff_name": tariff_opts["name"],
        "loan_term_months": loan_term_months,
        "loan_term_years": loan_term_months // 12,
        
        # Расчёт
        "down_payment": down_payment,
        "markup": markup,
        "markup_pct": dp_opts["markup_pct"],
        "object_price": object_price,
        "loan_amount": loan_amount,
        
        # Льготный период
        "grace_months": grace_months,
        "grace_payment": grace_payment,
        "grace_rate": tariff_opts["grace_rate"],
        "accreditive_pct": tariff_opts["accreditive_pct"],
        
        # После льготного
        "remaining_months": remaining_months,
        "regular_payment": regular_payment,
        "rate_after_grace": tariff_opts["rate_after_grace"],
        
        # Итоги
        "total_paid": total_paid,
        "overpayment": overpayment,
    }


def get_tariff_names() -> Dict[str, str]:
    """Возвращает названия тарифов."""
    cfg = load_config()
    return {k: v["name"] for k, v in cfg["tariffs"].items()}


def get_loan_terms() -> list:
    """Возвращает доступные сроки кредита."""
    return load_config()["loan_terms"]


def get_down_payment_options() -> list:
    """Возвращает доступные варианты ПВ."""
    cfg = load_config()
    return [int(k) for k in cfg["down_payment_options"].keys()]


def get_texts() -> Dict[str, str]:
    """Возвращает тексты для UI."""
    return load_config()["texts"]
