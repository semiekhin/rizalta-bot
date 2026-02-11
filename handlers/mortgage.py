"""
Обработчик ипотечного калькулятора RIZALTA.
Совкомбанк — акция "Сниженный платёж".

v1.0 (30.01.2026)
"""

from typing import Optional
from services.telegram import send_message_inline, send_document
from services.mortgage_calculator import (
    calc_mortgage,
    get_tariff_names,
    get_loan_terms,
    get_down_payment_options,
)
from services.units_db import get_lot_by_code, get_building_name, format_price_full


def fmt(value: int) -> str:
    """Форматирует число с пробелами."""
    return f"{value:,}".replace(",", " ")


async def handle_mortgage_menu(
    chat_id: int,
    code: str,
    building: int,
    down_payment_pct: int = 30,
    tariff: str = "base",
    loan_term: int = 360
):
    """
    Показывает расчёт ипотеки для лота с интерактивными кнопками.
    """
    # Получаем лот
    lot = get_lot_by_code(code, building)
    if not lot:
        await send_message_inline(
            chat_id,
            "❌ Лот не найден",
            [[{"text": "🔙 К поиску", "callback_data": "kp_menu"}]]
        )
        return
    
    # Расчёт ипотеки
    calc = calc_mortgage(
        price=lot["price"],
        down_payment_pct=down_payment_pct,
        tariff=tariff,
        loan_term_months=loan_term
    )
    
    building_name = get_building_name(lot["building"])
    
    # Формируем текст
    text = f"""🏦 <b>Ипотека Совкомбанк</b>
<i>Акция «Сниженный платёж»</i>
━━━━━━━━━━━━━━━━━━━━━

📍 <b>Лот {lot['code']}</b> • Корпус {lot['building']} «{building_name}»
💰 Цена: {format_price_full(lot['price'])}
📐 Площадь: {lot['area']} м²

⚙️ <b>ПВ {calc['down_payment_pct']}%</b> • <b>{calc['tariff_name']}</b> • <b>{calc['loan_term_years']} лет</b>
━━━━━━━━━━━━━━━━━━━━━

💵 Первоначальный взнос: <b>{fmt(calc['down_payment'])} ₽</b>
📈 Удорожание ({calc['markup_pct']}%): {fmt(calc['markup'])} ₽
💳 Сумма кредита: <b>{fmt(calc['loan_amount'])} ₽</b>

📅 <b>Льготный период ({calc['grace_months']} мес):</b>
   {fmt(calc['grace_payment'])} ₽/мес
   <i>(комиссия аккредитива {calc['accreditive_pct']}%)</i>

📅 <b>После льготного ({calc['remaining_months']} мес):</b>
   {fmt(calc['regular_payment'])} ₽/мес
   <i>(ставка {calc['rate_after_grace']}% годовых)</i>

━━━━━━━━━━━━━━━━━━━━━
<i>⚠️ Расчёт предварительный. Точные условия уточняйте в банке.</i>"""

    # Формируем callback base
    cb_base = f"mort_{code}_{building}"
    
    # Кнопки ПВ
    dp_buttons = []
    for dp in get_down_payment_options():
        mark = " ✓" if dp == down_payment_pct else ""
        dp_buttons.append({
            "text": f"ПВ {dp}%{mark}",
            "callback_data": f"{cb_base}_{dp}_{tariff}_{loan_term}"
        })
    
    # Кнопки тарифа
    tariff_buttons = []
    for t_key, t_name in get_tariff_names().items():
        mark = " ✓" if t_key == tariff else ""
        tariff_buttons.append({
            "text": f"{t_name}{mark}",
            "callback_data": f"{cb_base}_{down_payment_pct}_{t_key}_{loan_term}"
        })
    
    # Кнопки срока
    term_buttons = []
    for term in get_loan_terms():
        years = term // 12
        mark = " ✓" if term == loan_term else ""
        term_buttons.append({
            "text": f"{years} лет{mark}",
            "callback_data": f"{cb_base}_{down_payment_pct}_{tariff}_{term}"
        })
    
    inline_buttons = [
        dp_buttons,
        tariff_buttons,
        term_buttons,
        [{"text": "📄 Скачать PDF", "callback_data": f"mort_pdf_{code}_{building}_{down_payment_pct}_{tariff}_{loan_term}"}],
        [{"text": "🔙 К лоту", "callback_data": f"kp_lot_{code}_{building}"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_mortgage_pdf(
    chat_id: int,
    code: str,
    building: int,
    down_payment_pct: int = 30,
    tariff: str = "base",
    loan_term: int = 360
):
    """
    Генерирует и отправляет PDF с расчётом ипотеки.
    """
    from services.mortgage_pdf_generator import generate_mortgage_pdf
    
    lot = get_lot_by_code(code, building)
    if not lot:
        await send_message_inline(
            chat_id,
            "❌ Лот не найден",
            [[{"text": "🔙 К поиску", "callback_data": "kp_menu"}]]
        )
        return
    
    # Генерируем PDF
    pdf_path = generate_mortgage_pdf(
        code=code,
        building=building,
        down_payment_pct=down_payment_pct,
        tariff=tariff,
        loan_term_months=loan_term
    )
    
    if pdf_path:
        filename = f"Ипотека_{code}_ПВ{down_payment_pct}.pdf"
        await send_document(chat_id, pdf_path, filename)
        
        cb_base = f"mort_{code}_{building}_{down_payment_pct}_{tariff}_{loan_term}"
        inline_buttons = [
            [{"text": "🔄 Изменить параметры", "callback_data": cb_base}],
            [{"text": "🔙 К лоту", "callback_data": f"kp_lot_{code}_{building}"}],
        ]
        await send_message_inline(chat_id, "✅ Расчёт ипотеки готов!", inline_buttons)
        
        # Удаляем временный файл
        import os
        try:
            os.unlink(pdf_path)
        except:
            pass
    else:
        await send_message_inline(
            chat_id,
            "❌ Ошибка генерации PDF. Попробуйте позже.",
            [[{"text": "🔙 К лоту", "callback_data": f"kp_lot_{code}_{building}"}]]
        )
