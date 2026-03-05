"""
Обработчик траншевой ипотеки RIZALTA.
3 транша по 8 месяцев, срок 20 лет.
Все 4 сценария ПВ в одном сообщении.

v1.1 (03.03.2026)
"""

from services.telegram import send_message_inline, send_document
from services.tranche_mortgage_calculator import (
    calc_all_scenarios,
    get_down_payment_options,
)
from services.units_db import get_lot_by_code, get_building_name, format_price_full


def fmt(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _scenario_text(calc: dict) -> str:
    tp = calc["tranche_period"]
    remaining_months = calc["term_months"] - 2 * tp

    return f"""⚙️ <b>ПВ {calc['down_payment_pct']}%</b> • Ставка <b>{calc['rate']}%</b>
💵 ПВ: <b>{fmt(calc['down_payment'])} ₽</b> • Ипотека: <b>{fmt(calc['mortgage_total'])} ₽</b>
📅 1 транш ({tp} мес): <b>{fmt(calc['ep_1'])} ₽/мес</b>
📅 2 транш ({tp} мес): <b>{fmt(calc['ep_2'])} ₽/мес</b>
📅 3 транш ({remaining_months} мес): <b>{fmt(calc['ep_3'])} ₽/мес</b>"""


async def handle_tranche_mortgage_menu(
    chat_id: int,
    code: str,
    building: int,
    **kwargs
):
    lot = get_lot_by_code(code, building)
    if not lot:
        await send_message_inline(
            chat_id,
            "❌ Лот не найден",
            [[{"text": "🔙 К поиску", "callback_data": "kp_menu"}]]
        )
        return

    scenarios = calc_all_scenarios(lot["price"])
    valid = [s for s in scenarios if s is not None]

    if not valid:
        await send_message_inline(
            chat_id,
            "❌ Для данного лота расчёт траншевой ипотеки недоступен.",
            [[{"text": "🔙 К лоту", "callback_data": f"kp_lot_{code}_{building}"}]]
        )
        return

    building_name = get_building_name(lot["building"])

    header = f"""🏗 <b>Траншевая ипотека</b>
<i>3 транша • 20 лет</i>
━━━━━━━━━━━━━━━━━━━━━

📍 <b>Лот {lot['code']}</b> • Корпус {lot['building']} «{building_name}»
💰 Стоимость: <b>{format_price_full(lot['price'])}</b>
📐 Площадь: {lot['area']} м²
━━━━━━━━━━━━━━━━━━━━━"""

    blocks = [header]
    for sc in valid:
        blocks.append(_scenario_text(sc))

    blocks.append("<i>⚠️ Расчёт предварительный. Точные условия уточняйте в банке.</i>")

    text = "\n\n".join(blocks)

    inline_buttons = [
        [{"text": "📄 Скачать PDF", "callback_data": f"tmort_pdf_{code}_{building}"}],
        [{"text": "🔙 К лоту", "callback_data": f"kp_lot_{code}_{building}"}],
    ]

    await send_message_inline(chat_id, text, inline_buttons)


async def handle_tranche_mortgage_pdf(
    chat_id: int,
    code: str,
    building: int
):
    from services.tranche_mortgage_pdf_generator import generate_tranche_mortgage_pdf

    lot = get_lot_by_code(code, building)
    if not lot:
        await send_message_inline(
            chat_id,
            "❌ Лот не найден",
            [[{"text": "🔙 К поиску", "callback_data": "kp_menu"}]]
        )
        return

    pdf_path = generate_tranche_mortgage_pdf(code=code, building=building)

    if pdf_path:
        filename = f"Траншевая_ипотека_{code}.pdf"
        await send_document(chat_id, pdf_path, filename)

        inline_buttons = [
            [{"text": "🔙 К лоту", "callback_data": f"kp_lot_{code}_{building}"}],
        ]
        await send_message_inline(chat_id, "✅ Расчёт траншевой ипотеки готов!", inline_buttons)

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
