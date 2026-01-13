"""
Обработчики КП (Коммерческих предложений).

v2.1.0 — Все 348 лотов, навигация по корпусам и этажам
"""

from typing import Optional, List, Dict, Any
from services.telegram import send_message, send_message_inline, send_document
from services.units_db import (
    get_all_available_lots,
    get_lots_by_building,
    get_lots_by_floor,
    get_lots_filtered,
    get_lot_by_code,
    get_lots_by_code,
    get_lot_by_area,
    get_available_floors,
    get_building_stats,
    format_price_short,
    format_price_full,
    get_building_name,
    parse_floor_query,
    normalize_code,
)
from services.kp_pdf_generator import generate_kp_pdf

# Константы
MAX_BUTTONS_PER_MESSAGE = 20
DEFAULT_DISPLAY_LIMIT = 10

# Кеш последнего поиска для пагинации
_search_cache = {}

# Заголовки для разных режимов
MODE_TITLES = {
    "kp": "📋 <b>Коммерческие предложения</b>",
    "calc": "💰 <b>Расчёты доходности и рассрочки</b>",
    "compare": "📊 <b>Сравнение: Депозит vs RIZALTA</b>",
}

MODE_CALLBACKS = {
    "kp": "kp",
    "calc": "calc_nav",
    "compare": "compare_nav",
}


def fmt(price: int) -> str:
    """Форматирует цену с пробелами."""
    return f"{price:,}".replace(",", " ")


# ==================== УНИВЕРСАЛЬНАЯ НАВИГАЦИЯ ====================

async def handle_nav_menu(chat_id: int, mode: str = "kp"):
    """Универсальное меню навигации для КП/Расчётов/Сравнения."""
    
    stats = get_building_stats()
    total_lots = sum(s["count"] for s in stats)
    
    title = MODE_TITLES.get(mode, MODE_TITLES["kp"])
    cb = MODE_CALLBACKS.get(mode, "kp")
    
    text = f"""{title}

📊 Доступно лотов: <b>{total_lots}</b>

<b>Выберите способ поиска:</b>"""

    inline_buttons = [
        [{"text": "🏢 По корпусу", "callback_data": f"{cb}_by_building"}],
        [{"text": "📐 По площади", "callback_data": f"{cb}_by_area"}],
        [{"text": "💰 По бюджету", "callback_data": f"{cb}_by_budget"}],
        [{"text": "🔍 По номеру лота", "callback_data": f"{cb}_by_code"}],
        [{"text": "🔙 Главное меню", "callback_data": "back_to_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_nav_by_building_menu(chat_id: int, mode: str = "kp"):
    """Меню выбора корпуса."""
    stats = get_building_stats()
    cb = MODE_CALLBACKS.get(mode, "kp")
    
    text = "🏢 <b>Выберите корпус:</b>"
    
    inline_buttons = []
    for s in stats:
        btn_text = f"Корпус {s['building']} «{s['name']}» ({s['count']} лотов)"
        inline_buttons.append([{"text": btn_text, "callback_data": f"{cb}_building_{s['building']}"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"{cb}_menu"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_nav_building(chat_id: int, building: int, mode: str = "kp"):
    """Показывает этажи выбранного корпуса."""
    
    floors = get_available_floors(building)
    building_name = get_building_name(building)
    total_lots = sum(f["count"] for f in floors)
    cb = MODE_CALLBACKS.get(mode, "kp")
    
    text = f"""🏢 <b>Корпус {building} «{building_name}»</b>

📊 Лотов: {total_lots}
🏗 Этажей: {len(floors)}

<b>Выберите этаж:</b>"""

    inline_buttons = []
    
    # Группируем этажи по 3 в ряд
    row = []
    for f in floors:
        btn_text = f"{f['floor']} эт. ({f['count']})"
        row.append({"text": btn_text, "callback_data": f"{cb}_floor_{building}_{f['floor']}"})
        if len(row) == 3:
            inline_buttons.append(row)
            row = []
    if row:
        inline_buttons.append(row)
    
    # Быстрый доступ к группам этажей
    inline_buttons.append([
        {"text": "⬇️ Нижние (1-3)", "callback_data": f"{cb}_floors_{building}_lower"},
        {"text": "⬆️ Верхние (7-9)", "callback_data": f"{cb}_floors_{building}_upper"},
    ])
    
    inline_buttons.append([{"text": f"📋 Все {total_lots} лотов корпуса", "callback_data": f"{cb}_building_all_{building}"}])
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"{cb}_by_building"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_nav_floor(chat_id: int, building: int, floor: int, mode: str = "kp"):
    """Показывает лоты на этаже."""
    
    lots = get_lots_by_floor(building, floor)
    building_name = get_building_name(building)
    cb = MODE_CALLBACKS.get(mode, "kp")
    
    if not lots:
        await send_message(chat_id, f"На {floor} этаже корпуса {building} нет доступных лотов.")
        return
    
    text = f"""🏢 Корпус {building} «{building_name}» — <b>{floor} этаж</b>

📊 Лотов: {len(lots)}

<b>Выберите лот:</b>"""

    inline_buttons = []
    for lot in lots[:MAX_BUTTONS_PER_MESSAGE]:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"{cb}_lot_{lot['code']}_{building}"}])
    
    if len(lots) > MAX_BUTTONS_PER_MESSAGE:
        # Сохраняем в кеш для пагинации
        _search_cache[chat_id] = {"lots": lots, "offset": MAX_BUTTONS_PER_MESSAGE, "mode": mode, "back_callback": f"{cb}_building_{building}"}
        remaining = len(lots) - MAX_BUTTONS_PER_MESSAGE
        inline_buttons.append([{"text": f"📋 Показать ещё {remaining} лотов", "callback_data": "kp_show_more"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"{cb}_building_{building}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_nav_lot(chat_id: int, code: str, building: int = None, mode: str = "kp"):
    """Показывает карточку лота с кнопками в зависимости от режима."""
    
    # Если корпус указан — ищем конкретный лот
    if building is not None:
        lot = get_lot_by_code(code, building=building)
    else:
        lots = get_lots_by_code(code)
        
        if not lots:
            await send_message_inline(
                chat_id,
                f"❌ Лот <b>{code}</b> не найден в базе.",
                [[{"text": "🔙 К поиску", "callback_data": f"{MODE_CALLBACKS.get(mode, 'kp')}_menu"}]]
            )
            return
        
        if len(lots) > 1:
            cb = MODE_CALLBACKS.get(mode, "kp")
            text = f"""🔍 <b>Лот {code}</b> найден в нескольких корпусах:

<b>Выберите корпус:</b>"""
            
            inline_buttons = []
            for l in lots:
                building_name = get_building_name(l["building"])
                btn_text = f"Корпус {l['building']} «{building_name}» — {l['area']} м² — {format_price_short(l['price'])}"
                inline_buttons.append([{"text": btn_text, "callback_data": f"{cb}_lot_{code}_{l['building']}"}])
            
            inline_buttons.append([{"text": "🔙 К поиску", "callback_data": f"{cb}_menu"}])
            
            await send_message_inline(chat_id, text, inline_buttons)
            return
        
        lot = lots[0]
    
    if not lot:
        cb = MODE_CALLBACKS.get(mode, "kp")
        await send_message_inline(
            chat_id,
            f"❌ Лот <b>{code}</b> не найден.",
            [[{"text": "🔙 К поиску", "callback_data": f"{cb}_menu"}]]
        )
        return
    
    building_name = get_building_name(lot["building"])
    price_m2 = int(lot["price"] / lot["area"])
    cb = MODE_CALLBACKS.get(mode, "kp")
    
    text = f"""📋 <b>Лот {lot['code']}</b>

🏢 Корпус {lot['building']} «{building_name}»
🏗 Этаж: {lot['floor']}
📐 Площадь: {lot['area']} м²
💰 Цена: <b>{format_price_full(lot['price'])}</b>
📊 Цена за м²: {fmt(price_m2)} ₽
"""

    lot_id = f"{lot['code']}_{lot['building']}"
    
    inline_buttons = [
        [{"text": "📄 КП 100% оплата", "callback_data": f"kp_gen_{lot_id}_100"}],
        [{"text": "📄 КП с рассрочкой 12 мес", "callback_data": f"kp_gen_{lot_id}_12"}],
        [{"text": "📄 КП с рассрочкой 12+18 мес", "callback_data": f"kp_gen_{lot_id}_full"}],
        [{"text": "📊 Расчёт доходности", "callback_data": f"calc_roi_code_{lot['code']}"}],
        [{"text": "💳 Варианты оплаты", "callback_data": f"calc_finance_code_{lot['code']}"}],
        [{"text": "📈 Сравнить с депозитом", "callback_data": f"compare_lot_{lot['code']}_{lot['price']//1000}"}],
        [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        [{"text": "🔙 К поиску", "callback_data": f"{cb}_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


# ==================== ГЛАВНОЕ МЕНЮ КП ====================

async def handle_kp_menu(chat_id: int):
    """Главное меню КП — выбор способа поиска."""
    
    # Получаем статистику
    stats = get_building_stats()
    total_lots = sum(s["count"] for s in stats)
    
    text = f"""📋 <b>Коммерческие предложения</b>

📊 Доступно лотов: <b>{total_lots}</b>

<b>Выберите способ поиска:</b>"""

    inline_buttons = [
        [{"text": "🏢 По корпусу", "callback_data": "kp_by_building"}],
        [{"text": "📐 По площади", "callback_data": "kp_by_area"}],
        [{"text": "💰 По бюджету", "callback_data": "kp_by_budget"}],
        [{"text": "🔍 По номеру лота", "callback_data": "kp_by_code"}],
        [{"text": "🔙 Главное меню", "callback_data": "back_to_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


# ==================== ПОИСК ПО КОРПУСУ ====================

async def handle_kp_by_building_menu(chat_id: int):
    """Меню выбора корпуса."""
    
    stats = get_building_stats()
    
    text = "🏢 <b>Выберите корпус:</b>"
    
    inline_buttons = []
    for s in stats:
        btn_text = f"Корпус {s['building']} «{s['name']}» ({s['count']} лотов)"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_building_{s['building']}"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "kp_menu"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_building(chat_id: int, building: int):
    """Показывает этажи выбранного корпуса."""
    
    floors = get_available_floors(building)
    building_name = get_building_name(building)
    total_lots = sum(f["count"] for f in floors)
    
    text = f"""🏢 <b>Корпус {building} «{building_name}»</b>

📊 Лотов: {total_lots}
🏗 Этажей: {len(floors)}

<b>Выберите этаж:</b>"""

    inline_buttons = []
    
    # Группируем этажи по 3 в ряд
    row = []
    for f in floors:
        btn_text = f"{f['floor']} эт. ({f['count']})"
        row.append({"text": btn_text, "callback_data": f"kp_floor_{building}_{f['floor']}"})
        
        if len(row) == 3:
            inline_buttons.append(row)
            row = []
    
    if row:
        inline_buttons.append(row)
    
    # Быстрые фильтры
    inline_buttons.append([
        {"text": "⬆️ Верхние (7-9)", "callback_data": f"kp_floors_{building}_верхние"},
        {"text": "⬇️ Нижние (1-3)", "callback_data": f"kp_floors_{building}_нижние"}
    ])
    
    inline_buttons.append([
        {"text": "📋 Все лоты корпуса", "callback_data": f"kp_building_all_{building}"}
    ])
    
    inline_buttons.append([{"text": "🔙 К корпусам", "callback_data": "kp_by_building"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_floor(chat_id: int, building: int, floor: int):
    """Показывает лоты на конкретном этаже."""
    
    lots = get_lots_by_floor(building, floor)
    building_name = get_building_name(building)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ На {floor} этаже корпуса {building} нет доступных лотов.",
            [[{"text": "🔙 Назад", "callback_data": f"kp_building_{building}"}]]
        )
        return
    
    min_price = min(lot["price"] for lot in lots)
    max_price = max(lot["price"] for lot in lots)
    
    text = f"""🏢 <b>Корпус {building} «{building_name}», {floor} этаж</b>

📊 Лотов: {len(lots)}
💰 Цены: {format_price_short(min_price)} — {format_price_short(max_price)}

<b>Выберите лот:</b>"""

    inline_buttons = []
    
    for lot in lots[:MAX_BUTTONS_PER_MESSAGE]:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    if len(lots) > MAX_BUTTONS_PER_MESSAGE:
        # Сохраняем в кеш для пагинации
        _search_cache[chat_id] = {"lots": lots, "offset": MAX_BUTTONS_PER_MESSAGE, "back_callback": f"kp_building_{building}"}
        remaining = len(lots) - MAX_BUTTONS_PER_MESSAGE
        inline_buttons.append([{"text": f"📋 Показать ещё {remaining} лотов", "callback_data": "kp_show_more"}])
    
    inline_buttons.append([{"text": "🔙 К этажам", "callback_data": f"kp_building_{building}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_floors_range(chat_id: int, building: int, floor_range: str):
    """Показывает лоты на диапазоне этажей (верхние/нижние/средние)."""
    
    floors = parse_floor_query(floor_range)
    building_name = get_building_name(building)
    
    lots = get_lots_filtered(building=building, floors=floors)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ На выбранных этажах корпуса {building} нет доступных лотов.",
            [[{"text": "🔙 Назад", "callback_data": f"kp_building_{building}"}]]
        )
        return
    
    floor_label = {
        "верхние": "Верхние этажи (7-9)",
        "нижние": "Нижние этажи (1-3)",
        "средние": "Средние этажи (4-6)"
    }.get(floor_range, f"Этажи {floors}")
    
    text = f"""🏢 <b>Корпус {building} «{building_name}»</b>
🏗 <b>{floor_label}</b>

📊 Лотов: {len(lots)}

<b>Выберите лот:</b>"""

    inline_buttons = []
    
    for lot in lots[:MAX_BUTTONS_PER_MESSAGE]:
        btn_text = f"{lot['code']} ({lot['floor']} эт.) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    if len(lots) > MAX_BUTTONS_PER_MESSAGE:
        inline_buttons.append([{"text": f"... ещё {len(lots) - MAX_BUTTONS_PER_MESSAGE} лотов", "callback_data": "noop"}])
    
    inline_buttons.append([{"text": "🔙 К этажам", "callback_data": f"kp_building_{building}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


# ==================== ПОИСК ПО ПЛОЩАДИ ====================

async def handle_kp_by_area_menu(chat_id: int):
    """Меню выбора по площади."""
    
    text = "📐 <b>Выберите диапазон площади:</b>"
    
    inline_buttons = [
        [{"text": "22-31 м²", "callback_data": "kp_area_22_31"},
         {"text": "31-41 м²", "callback_data": "kp_area_31_41"}],
        [{"text": "41-51 м²", "callback_data": "kp_area_41_51"},
         {"text": "51-71 м²", "callback_data": "kp_area_51_71"}],
        [{"text": "71-91 м²", "callback_data": "kp_area_71_91"},
         {"text": "91+ м²", "callback_data": "kp_area_91_200"}],
        [{"text": "🔙 Назад", "callback_data": "kp_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_area_range(chat_id: int, min_area: float, max_area: float):
    """Показывает лоты в диапазоне площади."""
    
    lots = get_lots_filtered(min_area=min_area, max_area=max_area)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ Лоты в диапазоне {min_area}-{max_area} м² не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "kp_by_area"}]]
        )
        return
    
    area_label = f"{int(min_area)}-{int(max_area)}" if max_area < 200 else f"{int(min_area)}+"
    
    text = f"""📐 <b>Лоты {area_label} м²</b>

📊 Найдено: {len(lots)}

<b>Выберите лот:</b>"""

    inline_buttons = []
    
    for lot in lots[:DEFAULT_DISPLAY_LIMIT]:
        btn_text = f"{lot['code']} (корп.{lot['building']}, {lot['floor']} эт.) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{"text": f"📋 Показать все ({len(lots)} шт.)", "callback_data": f"kp_show_area_{int(min_area)}_{int(max_area)}"}])
    
    inline_buttons.append([{"text": "🔙 К площадям", "callback_data": "kp_by_area"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_show_all_area(chat_id: int, min_area: float, max_area: float, offset: int = 0):
    """Показывает лоты в диапазоне площади с пагинацией."""
    
    PAGE_SIZE = 50  # Лотов на странице
    
    lots = get_lots_filtered(min_area=min_area, max_area=max_area)
    
    if not lots:
        await send_message(chat_id, "❌ Лоты не найдены.")
        return
    
    total = len(lots)
    area_label = f"{int(min_area)}-{int(max_area)}" if max_area < 200 else f"{int(min_area)}+"
    
    # Срез для текущей страницы
    page_lots = lots[offset:offset + PAGE_SIZE]
    page_num = (offset // PAGE_SIZE) + 1
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    
    if total_pages > 1:
        text = f"📐 <b>Все лоты {area_label} м²</b> ({total} шт.)\n📄 Страница {page_num}/{total_pages}:"
    else:
        text = f"📐 <b>Все лоты {area_label} м²</b> ({total} шт.):"
    
    inline_buttons = []
    for lot in page_lots:
        btn_text = f"{lot['code']} (корп.{lot['building']}) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    # Кнопки навигации
    nav_buttons = []
    if offset > 0:
        prev_offset = max(0, offset - PAGE_SIZE)
        nav_buttons.append({"text": "⬅️ Назад", "callback_data": f"kp_show_area_{int(min_area)}_{int(max_area)}_{prev_offset}"})
    
    if offset + PAGE_SIZE < total:
        next_offset = offset + PAGE_SIZE
        nav_buttons.append({"text": "Вперёд ➡️", "callback_data": f"kp_show_area_{int(min_area)}_{int(max_area)}_{next_offset}"})
    
    if nav_buttons:
        inline_buttons.append(nav_buttons)
    
    inline_buttons.append([{"text": "🔙 К площадям", "callback_data": f"kp_area_{int(min_area)}_{int(max_area)}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)
async def handle_kp_by_budget_menu(chat_id: int):
    """Меню выбора по бюджету."""
    
    text = "💰 <b>Выберите диапазон бюджета:</b>"
    
    inline_buttons = [
        [{"text": "до 15 млн", "callback_data": "kp_budget_0_15"},
         {"text": "15-18 млн", "callback_data": "kp_budget_15_18"}],
        [{"text": "18-22 млн", "callback_data": "kp_budget_18_22"},
         {"text": "22-26 млн", "callback_data": "kp_budget_22_26"}],
        [{"text": "26-35 млн", "callback_data": "kp_budget_26_35"},
         {"text": "35-50 млн", "callback_data": "kp_budget_35_50"}],
        [{"text": "50+ млн", "callback_data": "kp_budget_50_999"}],
        [{"text": "🔙 Назад", "callback_data": "kp_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_budget_range(chat_id: int, min_budget: int, max_budget: int):
    """Показывает лоты в диапазоне бюджета."""
    
    min_price = min_budget * 1_000_000
    max_price = max_budget * 1_000_000 if max_budget < 999 else 999_000_000
    
    lots = get_lots_filtered(min_price=min_price, max_price=max_price)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ Лоты в диапазоне {min_budget}-{max_budget} млн не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "kp_by_budget"}]]
        )
        return
    
    budget_label = f"{min_budget}-{max_budget}" if max_budget < 999 else f"{min_budget}+"
    
    text = f"""💰 <b>Лоты {budget_label} млн</b>

📊 Найдено: {len(lots)}

<b>Выберите лот:</b>"""

    inline_buttons = []
    
    for lot in lots[:DEFAULT_DISPLAY_LIMIT]:
        btn_text = f"{lot['code']} (корп.{lot['building']}, {lot['floor']} эт.) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{"text": f"📋 Показать все ({len(lots)} шт.)", "callback_data": f"kp_show_budget_{min_budget}_{max_budget}"}])
    
    inline_buttons.append([{"text": "🔙 К бюджетам", "callback_data": "kp_by_budget"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_show_all_budget(chat_id: int, min_budget: int, max_budget: int):
    """Показывает ВСЕ лоты в диапазоне бюджета."""
    
    min_price = min_budget * 1_000_000
    max_price = max_budget * 1_000_000 if max_budget < 999 else 999_000_000
    
    lots = get_lots_filtered(min_price=min_price, max_price=max_price)
    
    if not lots:
        await send_message(chat_id, "❌ Лоты не найдены.")
        return
    
    budget_label = f"{min_budget}-{max_budget}" if max_budget < 999 else f"{min_budget}+"
    
    text = f"💰 <b>Все лоты {budget_label} млн</b> ({len(lots)} шт.):"
    
    inline_buttons = []
    for lot in lots:
        btn_text = f"{lot['code']} (корп.{lot['building']}) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"kp_budget_{min_budget}_{max_budget}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


# ==================== ПОИСК ПО КОДУ ====================

async def handle_kp_by_code_menu(chat_id: int):
    """Промпт для ввода кода лота."""
    
    text = """🔍 <b>Поиск по номеру лота</b>

Введите код лота, например:
• <code>В708</code>
• <code>А101</code>
• <code>B215</code>

💡 Можно использовать русские или английские буквы."""

    inline_buttons = [[{"text": "🔙 Назад", "callback_data": "kp_menu"}]]
    
    await send_message_inline(chat_id, text, inline_buttons)


# ==================== ДЕТАЛИ ЛОТА И ГЕНЕРАЦИЯ КП ====================

async def handle_kp_lot(chat_id: int, code: str, building: int = None):
    """
    Показывает детали лота и кнопки генерации КП.
    Если лот есть в нескольких корпусах и building не указан — показывает выбор корпуса.
    """
    
    # Если корпус указан — ищем конкретный лот
    if building is not None:
        lot = get_lot_by_code(code, building=building)
    else:
        # Проверяем, есть ли дубли
        lots = get_lots_by_code(code)
        
        if not lots:
            await send_message_inline(
                chat_id,
                f"❌ Лот <b>{code}</b> не найден в базе.",
                [[{"text": "🔙 К поиску", "callback_data": "kp_menu"}]]
            )
            return
        
        # Если лот есть в нескольких корпусах — показываем выбор
        if len(lots) > 1:
            text = f"""🔍 <b>Лот {code}</b> найден в нескольких корпусах:

<b>Выберите корпус:</b>"""
            
            inline_buttons = []
            for l in lots:
                building_name = get_building_name(l["building"])
                btn_text = f"Корпус {l['building']} «{building_name}» — {l['area']} м² — {format_price_short(l['price'])}"
                inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{code}_{l['building']}"}])
            
            inline_buttons.append([{"text": "🔙 К поиску", "callback_data": "kp_menu"}])
            
            await send_message_inline(chat_id, text, inline_buttons)
            return
        
        # Один лот — показываем его
        lot = lots[0]
    
    if not lot:
        await send_message_inline(
            chat_id,
            f"❌ Лот <b>{code}</b> не найден в корпусе {building}.",
            [[{"text": "🔙 К поиску", "callback_data": "kp_menu"}]]
        )
        return
    
    building_name = get_building_name(lot["building"])
    price_m2 = int(lot["price"] / lot["area"])
    
    text = f"""📋 <b>Лот {lot['code']}</b>

🏢 Корпус {lot['building']} «{building_name}»
🏗 Этаж: {lot['floor']}
📐 Площадь: {lot['area']} м²
💰 Цена: <b>{format_price_full(lot['price'])}</b>
📊 Цена за м²: {fmt(price_m2)} ₽

<b>Выберите формат КП:</b>"""

    # Используем код + корпус для генерации
    lot_id = f"{lot['code']}_{lot['building']}"
    
    inline_buttons = [
        [{"text": "📄 КП 100% оплата", "callback_data": f"kp_gen_{lot_id}_100"}],
        [{"text": "📄 КП с рассрочкой 12 мес", "callback_data": f"kp_gen_{lot_id}_12"}],
        [{"text": "📄 КП с рассрочкой 12+18 мес", "callback_data": f"kp_gen_{lot_id}_full"}],
        [{"text": "📊 Расчёт доходности", "callback_data": f"calc_roi_code_{lot['code']}"}],
        [{"text": "💳 Варианты оплаты", "callback_data": f"calc_finance_code_{lot['code']}"}],
        [{"text": "📈 Сравнить с депозитом", "callback_data": f"compare_lot_{lot['code']}_{lot['price']//1000}"}],
        [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        [{"text": "🔙 К поиску", "callback_data": "kp_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_generate(chat_id: int, code: str, mode: str, building: int = None):
    """
    Генерирует и отправляет PDF КП.
    code: код лота (В708) или код_корпус (В708_1)
    building: номер корпуса (если не указан в code)
    """
    
    # Парсим код и корпус
    if "_" in code and building is None:
        parts = code.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            code = parts[0]
            building = int(parts[1])
    
    await send_message(chat_id, f"⏳ Создаю КП для лота {code}...")
    
    # Определяем параметры генерации
    if mode == "100":
        pdf_path = generate_kp_pdf(code=code, building=building, include_18m=False, full_payment=True)
        filename = f"КП_{code}_100.pdf"
    elif mode == "12":
        pdf_path = generate_kp_pdf(code=code, building=building, include_18m=False, full_payment=False)
        filename = f"КП_{code}_12m.pdf"
    else:  # full
        pdf_path = generate_kp_pdf(code=code, building=building, include_18m=True, full_payment=False)
        filename = f"КП_{code}_12m_18m.pdf"
    
    if pdf_path:
        await send_document(chat_id, pdf_path, filename)
        
        # Формируем callback для возврата к лоту
        lot_callback = f"kp_lot_{code}_{building}" if building else f"kp_lot_{code}"
        
        inline_buttons = [
            [{"text": "📋 Другой формат КП", "callback_data": lot_callback}],
            [{"text": "🔍 Другой лот", "callback_data": "kp_menu"}],
            [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        ]
        await send_message_inline(chat_id, "✅ КП готово!", inline_buttons)
        
        # Удаляем временный файл
        import os
        try:
            os.unlink(pdf_path)
        except:
            pass
    else:
        await send_message(chat_id, f"❌ Ошибка создания КП для {code}. Попробуйте позже.")


# ==================== УМНЫЙ ПОИСК (для голосовых команд) ====================

async def handle_kp_smart_search(
    chat_id: int,
    code: Optional[str] = None,
    building: Optional[int] = None,
    floor: Optional[Any] = None,
    budget: Optional[int] = None,
    area: Optional[float] = None
):
    """
    Умный поиск КП по параметрам из голосовой команды.
    Вызывается из app.py после классификации intent'а.
    """
    
    # 1. Если есть код — показываем конкретный лот
    if code:
        await handle_kp_lot(chat_id, code)
        return
    
    # 2. Собираем фильтры
    floors = None
    if floor:
        if isinstance(floor, int):
            floors = [floor]
        elif isinstance(floor, str):
            floors = parse_floor_query(floor)
    
    min_price = None
    max_price = None
    if budget:
        # ±10% от указанной суммы
        min_price = int(budget * 0.9)
        max_price = int(budget * 1.1)
    
    min_area_val = None
    max_area_val = None
    if area:
        min_area_val = area - 3
        max_area_val = area + 3
    
    # 3. Выполняем поиск
    lots = get_lots_filtered(
        building=building,
        floors=floors,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area_val,
        max_area=max_area_val,
        limit=30
    )
    
    if not lots:
        text = "❌ По вашему запросу лоты не найдены.\n\nПопробуйте изменить параметры поиска."
        inline_buttons = [[{"text": "🔍 Новый поиск", "callback_data": "kp_menu"}]]
        await send_message_inline(chat_id, text, inline_buttons)
        return
    
    # 4. Формируем описание запроса
    query_parts = []
    if building:
        query_parts.append(f"корпус {building}")
    if floors:
        if len(floors) > 3:
            query_parts.append(f"этажи {floors[0]}-{floors[-1]}")
        else:
            query_parts.append(f"этаж {', '.join(map(str, floors))}")
    if budget:
        query_parts.append(f"до {format_price_short(budget)}")
    if area:
        query_parts.append(f"~{area} м²")
    
    query_desc = ", ".join(query_parts) if query_parts else "все лоты"
    
    text = f"""🔍 <b>Результаты поиска</b>
<i>{query_desc}</i>

📊 Найдено: {len(lots)}

<b>Выберите лот:</b>"""

    inline_buttons = []
    
    for lot in lots[:DEFAULT_DISPLAY_LIMIT]:
        btn_text = f"{lot['code']} (корп.{lot['building']}, {lot['floor']} эт.) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        # Сохраняем результаты поиска в кеш
        _search_cache[chat_id] = {"lots": lots, "offset": DEFAULT_DISPLAY_LIMIT}
        remaining = len(lots) - DEFAULT_DISPLAY_LIMIT
        inline_buttons.append([{"text": f"📋 Показать ещё {remaining} лотов", "callback_data": "kp_show_more"}])
    
    inline_buttons.append([{"text": "🔍 Новый поиск", "callback_data": "kp_menu"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_show_more(chat_id: int):
    """Показывает оставшиеся лоты из кеша."""
    
    cache = _search_cache.get(chat_id)
    if not cache:
        await send_message(chat_id, "❌ Поиск устарел. Выполните новый поиск.")
        return
    
    lots = cache["lots"]
    offset = cache["offset"]
    remaining_lots = lots[offset:]
    
    if not remaining_lots:
        await send_message(chat_id, "Больше лотов нет.")
        return
    
    text = f"📋 <b>Ещё {len(remaining_lots)} лотов:</b>"
    
    inline_buttons = []
    for lot in remaining_lots[:20]:  # Показываем до 20 за раз
        btn_text = f"{lot['code']} (корп.{lot['building']}, {lot['floor']} эт.) — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_lot_{lot['code']}"}])
    
    # Если ещё остались
    new_offset = offset + 20
    if new_offset < len(lots):
        _search_cache[chat_id]["offset"] = new_offset
        remaining = len(lots) - new_offset
        inline_buttons.append([{"text": f"📋 Показать ещё {remaining} лотов", "callback_data": "kp_show_more"}])
    else:
        # Очищаем кеш
        _search_cache.pop(chat_id, None)
    
    inline_buttons.append([{"text": "🔍 Новый поиск", "callback_data": "kp_menu"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


# ==================== LEGACY: для совместимости ====================

async def handle_kp_request(chat_id: int, text: str):
    """LEGACY: Обработка текстового запроса на КП."""
    # Пробуем найти код лота в тексте
    import re
    code_match = re.search(r'[АаAaВвBb]\s*\d{3,4}', text, re.IGNORECASE)
    
    if code_match:
        code = code_match.group().upper().replace(" ", "")
        code = code.replace("A", "А").replace("B", "В")
        await handle_kp_lot(chat_id, code)
    else:
        await handle_kp_menu(chat_id)


async def handle_kp_send_one(chat_id: int, area: float = 0):
    """LEGACY: КП по площади."""
    lot = get_lot_by_area(area)
    if lot:
        await handle_kp_lot(chat_id, lot["code"])
    else:
        await send_message(chat_id, f"❌ Лот с площадью ~{area} м² не найден.")


async def handle_kp_select_lot(chat_id: int, area_x10: int):
    """LEGACY: Выбор лота по area*10."""
    area = area_x10 / 10.0
    lot = get_lot_by_area(area)
    if lot:
        await handle_kp_lot(chat_id, lot["code"])
    else:
        await send_message(chat_id, f"❌ Лот с площадью ~{area} м² не найден.")


async def handle_kp_generate_pdf(chat_id: int, area_x10: int, mode: str):
    """LEGACY: Генерация PDF по area*10."""
    area = area_x10 / 10.0
    lot = get_lot_by_area(area)
    if lot:
        await handle_kp_generate(chat_id, lot["code"], mode)
    else:
        await send_message(chat_id, f"❌ Лот с площадью ~{area} м² не найден.")


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (для calc_dynamic) ====================

def get_lots_by_area_range(min_area: float, max_area: float) -> List[Dict[str, Any]]:
    """Для совместимости с calc_dynamic.py"""
    return get_lots_filtered(min_area=min_area, max_area=max_area)


def get_lots_by_budget_range(min_budget: int, max_budget: int) -> List[Dict[str, Any]]:
    """Для совместимости с calc_dynamic.py"""
    return get_lots_filtered(min_price=min_budget, max_price=max_budget)


def normalize_code(code: str) -> str:
    """Для совместимости — возвращает нормализованный код."""
    from services.units_db import normalize_code as nc
    cyr, lat = nc(code)
    return cyr
