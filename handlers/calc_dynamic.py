"""
Обработчики динамических расчётов для всех лотов с КП.
"""

from typing import List, Dict, Any
from services.telegram import send_message, send_message_inline
from services.calc_universal import (
    calculate_roi_for_lot, format_roi_text,
    calculate_installment_for_lot, format_installment_text,
)
from handlers.kp import (
    get_lots_by_area_range, get_lots_by_budget_range,
    normalize_code, format_price_short,
)


async def handle_calculations_menu_new(chat_id: int):
    text = "💰 <b>Расчёты</b>\n\nВыберите тип расчёта:"
    inline_buttons = [
        [{"text": "📊 Доходность (ROI)", "callback_data": "calc_roi_menu"}],
        [{"text": "💳 Рассрочка/ипотека", "callback_data": "calc_finance_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_menu(chat_id: int):
    text = "📊 <b>Расчёт доходности</b>\n\nКак искать лот?"
    inline_buttons = [
        [{"text": "📐 По площади", "callback_data": "calc_roi_by_area"}],
        [{"text": "💰 По бюджету", "callback_data": "calc_roi_by_budget"}],
        [{"text": "🔙 Назад", "callback_data": "calc_main_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_by_area_menu(chat_id: int):
    text = "📐 <b>Выберите диапазон площади:</b>"
    inline_buttons = [
        [{"text": "22-25 м²", "callback_data": "calc_roi_area_22_25"},
         {"text": "26-30 м²", "callback_data": "calc_roi_area_26_30"},
         {"text": "31-35 м²", "callback_data": "calc_roi_area_31_35"}],
        [{"text": "36-40 м²", "callback_data": "calc_roi_area_36_40"},
         {"text": "41-50 м²", "callback_data": "calc_roi_area_41_50"},
         {"text": "51+ м²", "callback_data": "calc_roi_area_51_999"}],
        [{"text": "🔙 Назад", "callback_data": "calc_roi_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_by_budget_menu(chat_id: int):
    text = "💰 <b>Выберите диапазон бюджета:</b>"
    inline_buttons = [
        [{"text": "до 15 млн", "callback_data": "calc_roi_budget_0_15"},
         {"text": "15-18 млн", "callback_data": "calc_roi_budget_15_18"},
         {"text": "18-22 млн", "callback_data": "calc_roi_budget_18_22"}],
        [{"text": "22-26 млн", "callback_data": "calc_roi_budget_22_26"},
         {"text": "26-30 млн", "callback_data": "calc_roi_budget_26_30"},
         {"text": "30+ млн", "callback_data": "calc_roi_budget_30_999"}],
        [{"text": "🔙 Назад", "callback_data": "calc_roi_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_area_range(chat_id: int, min_area: float, max_area: float):
    lots = get_lots_by_area_range(min_area, max_area)
    if not lots:
        await send_message_inline(chat_id, f"❌ Лоты на {min_area}-{max_area} м² не найдены.",
                                  [[{"text": "🔙 Назад", "callback_data": "calc_roi_by_area"}]])
        return
    display_lots = lots[:8]
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"📊 <b>ROI для {area_text} м²</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_roi_lot_{lot['code']}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_roi_by_area"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_budget_range(chat_id: int, min_budget: int, max_budget: int):
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    if not lots:
        await send_message_inline(chat_id, f"❌ Лоты на {min_budget}-{max_budget} млн не найдены.",
                                  [[{"text": "🔙 Назад", "callback_data": "calc_roi_by_budget"}]])
        return
    display_lots = lots[:8]
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"📊 <b>ROI для {budget_text} млн</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_roi_lot_{lot['code']}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_roi_by_budget"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_lot(chat_id: int, unit_code: str):
    lots = get_lots_by_area_range(0, 9999)
    normalized = normalize_code(unit_code)
    lot = None
    for l in lots:
        if normalize_code(l['code']) == normalized:
            lot = l
            break
    if not lot:
        await send_message(chat_id, f"❌ Лот {unit_code} не найден.")
        return
    calc = calculate_roi_for_lot(lot['price'], lot['area'], lot['code'])
    text = format_roi_text(calc)
    inline_buttons = [
        [{"text": "💳 Рассрочка", "callback_data": f"calc_finance_lot_{lot['code']}"},
         {"text": "📋 Получить КП", "callback_data": f"kp_send_{lot['code']}"}],
        [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        [{"text": "🔙 К списку", "callback_data": "calc_roi_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_menu(chat_id: int):
    text = "💳 <b>Рассрочка и ипотека</b>\n\nКак искать лот?"
    inline_buttons = [
        [{"text": "📐 По площади", "callback_data": "calc_finance_by_area"}],
        [{"text": "💰 По бюджету", "callback_data": "calc_finance_by_budget"}],
        [{"text": "🔙 Назад", "callback_data": "calc_main_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_by_area_menu(chat_id: int):
    text = "📐 <b>Выберите диапазон площади:</b>"
    inline_buttons = [
        [{"text": "22-25 м²", "callback_data": "calc_fin_area_22_25"},
         {"text": "26-30 м²", "callback_data": "calc_fin_area_26_30"},
         {"text": "31-35 м²", "callback_data": "calc_fin_area_31_35"}],
        [{"text": "36-40 м²", "callback_data": "calc_fin_area_36_40"},
         {"text": "41-50 м²", "callback_data": "calc_fin_area_41_50"},
         {"text": "51+ м²", "callback_data": "calc_fin_area_51_999"}],
        [{"text": "🔙 Назад", "callback_data": "calc_finance_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_by_budget_menu(chat_id: int):
    text = "💰 <b>Выберите диапазон бюджета:</b>"
    inline_buttons = [
        [{"text": "до 15 млн", "callback_data": "calc_fin_budget_0_15"},
         {"text": "15-18 млн", "callback_data": "calc_fin_budget_15_18"},
         {"text": "18-22 млн", "callback_data": "calc_fin_budget_18_22"}],
        [{"text": "22-26 млн", "callback_data": "calc_fin_budget_22_26"},
         {"text": "26-30 млн", "callback_data": "calc_fin_budget_26_30"},
         {"text": "30+ млн", "callback_data": "calc_fin_budget_30_999"}],
        [{"text": "🔙 Назад", "callback_data": "calc_finance_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_area_range(chat_id: int, min_area: float, max_area: float):
    lots = get_lots_by_area_range(min_area, max_area)
    if not lots:
        await send_message_inline(chat_id, f"❌ Лоты на {min_area}-{max_area} м² не найдены.",
                                  [[{"text": "🔙 Назад", "callback_data": "calc_finance_by_area"}]])
        return
    display_lots = lots[:8]
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"💳 <b>Рассрочка для {area_text} м²</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_finance_lot_{lot['code']}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_finance_by_area"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_budget_range(chat_id: int, min_budget: int, max_budget: int):
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    if not lots:
        await send_message_inline(chat_id, f"❌ Лоты на {min_budget}-{max_budget} млн не найдены.",
                                  [[{"text": "🔙 Назад", "callback_data": "calc_finance_by_budget"}]])
        return
    display_lots = lots[:8]
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"💳 <b>Рассрочка для {budget_text} млн</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_finance_lot_{lot['code']}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_finance_by_budget"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_lot(chat_id: int, unit_code: str):
    lots = get_lots_by_area_range(0, 9999)
    normalized = normalize_code(unit_code)
    lot = None
    for l in lots:
        if normalize_code(l['code']) == normalized:
            lot = l
            break
    if not lot:
        await send_message(chat_id, f"❌ Лот {unit_code} не найден.")
        return
    calc = calculate_installment_for_lot(lot['price'], lot['area'], lot['code'])
    text = format_installment_text(calc)
    inline_buttons = [
        [{"text": "📊 Доходность", "callback_data": f"calc_roi_lot_{lot['code']}"},
         {"text": "📋 Получить КП", "callback_data": f"kp_send_{lot['code']}"}],
        [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        [{"text": "🔙 К списку", "callback_data": "calc_finance_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)
