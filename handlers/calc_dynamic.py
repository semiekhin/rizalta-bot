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

DEFAULT_DISPLAY_LIMIT = 8


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
        [{"text": "22-30 м²", "callback_data": "calc_roi_area_22_30"},
         {"text": "31-40 м²", "callback_data": "calc_roi_area_31_40"},
         {"text": "41-50 м²", "callback_data": "calc_roi_area_41_50"}],
        [{"text": "51-70 м²", "callback_data": "calc_roi_area_51_70"},
         {"text": "71-90 м²", "callback_data": "calc_roi_area_71_90"},
         {"text": "90+ м²", "callback_data": "calc_roi_area_90_999"}],
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
    display_lots = lots[:DEFAULT_DISPLAY_LIMIT]
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"📊 <b>ROI для {area_text} м²</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} (корп.{lot.get('building', '?')}) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_roi_lot_{int(lot['area']*10)}"}])
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{"text": f"📋 Показать все ({len(lots)} шт.)", "callback_data": f"calc_roi_show_area_{int(min_area)}_{int(max_area)}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_roi_by_area"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_show_all_area(chat_id: int, min_area: float, max_area: float):
    lots = get_lots_by_area_range(min_area, max_area)
    if not lots:
        await send_message(chat_id, "❌ Лоты не найдены.")
        return
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"📊 <b>Все лоты ROI на {area_text} м²</b> ({len(lots)} шт.):"
    inline_buttons = []
    for lot in lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_roi_lot_{int(lot['area']*10)}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"calc_roi_area_{int(min_area)}_{int(max_area)}"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_budget_range(chat_id: int, min_budget: int, max_budget: int):
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    if not lots:
        await send_message_inline(chat_id, f"❌ Лоты на {min_budget}-{max_budget} млн не найдены.",
                                  [[{"text": "🔙 Назад", "callback_data": "calc_roi_by_budget"}]])
        return
    display_lots = lots[:DEFAULT_DISPLAY_LIMIT]
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"📊 <b>ROI для {budget_text} млн</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} (корп.{lot.get('building', '?')}) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_roi_lot_{int(lot['area']*10)}"}])
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{"text": f"📋 Показать все ({len(lots)} шт.)", "callback_data": f"calc_roi_show_budget_{min_budget}_{max_budget}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_roi_by_budget"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_show_all_budget(chat_id: int, min_budget: int, max_budget: int):
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    if not lots:
        await send_message(chat_id, "❌ Лоты не найдены.")
        return
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"📊 <b>Все лоты ROI на {budget_text} млн</b> ({len(lots)} шт.):"
    inline_buttons = []
    for lot in lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_roi_lot_{int(lot['area']*10)}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"calc_roi_budget_{min_budget}_{max_budget}"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_roi_lot(chat_id: int, area: float):
    lots = get_lots_by_area_range(0, 9999)
    lot = None
    for l in lots:
        if abs(l['area'] - area) < 0.05:
            lot = l
            break
    if not lot:
        await send_message(chat_id, f"❌ Лот не найден.")
        return
    
    from services.investment_calc import calculate_investment, format_investment_text
    price_m2 = int(lot['price'] / lot['area'])
    calc = calculate_investment(lot['area'], price_m2)
    text = format_investment_text(lot['code'], calc)
    
    inline_buttons = [
        [{"text": "💳 Рассрочка", "callback_data": f"calc_finance_lot_{int(lot['area']*10)}"},
         {"text": "📥 Excel", "callback_data": f"roi_xlsx_{int(lot['area']*10)}"},
         {"text": "📋 Получить КП", "callback_data": f"kp_send_{int(lot['area']*10)}"}],
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
    display_lots = lots[:DEFAULT_DISPLAY_LIMIT]
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"💳 <b>Рассрочка для {area_text} м²</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} (корп.{lot.get('building', '?')}) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_finance_lot_{int(lot['area']*10)}"}])
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{"text": f"📋 Показать все ({len(lots)} шт.)", "callback_data": f"calc_fin_show_area_{int(min_area)}_{int(max_area)}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_finance_by_area"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_show_all_area(chat_id: int, min_area: float, max_area: float):
    lots = get_lots_by_area_range(min_area, max_area)
    if not lots:
        await send_message(chat_id, "❌ Лоты не найдены.")
        return
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"💳 <b>Все лоты рассрочки на {area_text} м²</b> ({len(lots)} шт.):"
    inline_buttons = []
    for lot in lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_finance_lot_{int(lot['area']*10)}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"calc_fin_area_{int(min_area)}_{int(max_area)}"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_budget_range(chat_id: int, min_budget: int, max_budget: int):
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    if not lots:
        await send_message_inline(chat_id, f"❌ Лоты на {min_budget}-{max_budget} млн не найдены.",
                                  [[{"text": "🔙 Назад", "callback_data": "calc_finance_by_budget"}]])
        return
    display_lots = lots[:DEFAULT_DISPLAY_LIMIT]
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"💳 <b>Рассрочка для {budget_text} млн</b> ({len(lots)} лотов)\n\nВыберите лот:"
    inline_buttons = []
    for lot in display_lots:
        btn_text = f"{lot['code']} (корп.{lot.get('building', '?')}) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_finance_lot_{int(lot['area']*10)}"}])
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{"text": f"📋 Показать все ({len(lots)} шт.)", "callback_data": f"calc_fin_show_budget_{min_budget}_{max_budget}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "calc_finance_by_budget"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_show_all_budget(chat_id: int, min_budget: int, max_budget: int):
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    if not lots:
        await send_message(chat_id, "❌ Лоты не найдены.")
        return
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"💳 <b>Все лоты рассрочки на {budget_text} млн</b> ({len(lots)} шт.):"
    inline_buttons = []
    for lot in lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"calc_finance_lot_{int(lot['area']*10)}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"calc_fin_budget_{min_budget}_{max_budget}"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_calc_finance_lot(chat_id: int, area: float):
    lots = get_lots_by_area_range(0, 9999)
    lot = None
    for l in lots:
        if abs(l['area'] - area) < 0.05:
            lot = l
            break
    if not lot:
        await send_message(chat_id, f"❌ Лот не найден.")
        return
    calc = calculate_installment_for_lot(lot['price'], lot['area'], lot['code'])
    text = format_installment_text(calc)
    inline_buttons = [
        [{"text": "📊 Доходность", "callback_data": f"calc_roi_lot_{int(lot['area']*10)}"},
         {"text": "📋 Получить КП", "callback_data": f"kp_send_{int(lot['area']*10)}"}],
        [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        [{"text": "🔙 К списку", "callback_data": "calc_finance_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)
