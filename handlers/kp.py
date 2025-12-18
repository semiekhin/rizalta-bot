"""
Обработчик коммерческих предложений.
Данные из БД через services/units_db.py
PDF генерация через services/kp_pdf_generator.py
"""

from typing import List, Dict, Any
import os
import re

from services.telegram import send_message, send_message_inline, send_photo, send_document
from services.units_db import (
    get_unique_lots, get_lots_by_area, get_lots_by_budget,
    get_lot_by_area, get_lot_by_code, format_price_short
)
from services.kp_pdf_generator import generate_kp_pdf
from models.state import clear_dialog_state
from config.settings import BASE_DIR


# Путь к папке с готовыми КП (JPG) - для fallback
KP_DIR = os.path.join(BASE_DIR, "kp_all")

# Сколько кнопок показывать по умолчанию
DEFAULT_DISPLAY_LIMIT = 8


def find_kp_by_area(area: float) -> str:
    """Ищет готовый JPG файл КП по площади (fallback)."""
    if not os.path.exists(KP_DIR):
        return None
    
    for f in os.listdir(KP_DIR):
        if not f.endswith(".jpg"):
            continue
        match = re.match(r"kp_([\d.]+)m_", f)
        if match:
            file_area = float(match.group(1))
            if abs(file_area - area) < 0.05:
                return os.path.join(KP_DIR, f)
    return None


def get_lots_by_area_range(min_area: float, max_area: float) -> List[Dict[str, Any]]:
    """Получает лоты по диапазону площади из БД."""
    return get_lots_by_area(min_area, max_area)


def get_lots_by_budget_range(min_budget: int, max_budget: int) -> List[Dict[str, Any]]:
    """Получает лоты по диапазону бюджета из БД."""
    return get_lots_by_budget(min_budget, max_budget)


def normalize_code(code: str) -> str:
    """Нормализует код лота."""
    if not code:
        return ""
    code = str(code).strip().upper()
    table = str.maketrans({"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "S", "Т": "T"})
    return code.translate(table)


async def handle_kp_menu(chat_id: int):
    """Показывает главное меню КП."""
    clear_dialog_state(chat_id)
    
    text = "📋 <b>Коммерческие предложения</b>\n\nКак искать?"
    
    inline_buttons = [
        [{"text": "📐 По площади", "callback_data": "kp_by_area"}],
        [{"text": "💰 По бюджету", "callback_data": "kp_by_budget"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_by_area_menu(chat_id: int):
    """Показывает выбор диапазона площади."""
    text = "📐 <b>Выберите диапазон площади:</b>"
    
    inline_buttons = [
        [
            {"text": "22-30 м²", "callback_data": "kp_area_22_30"},
            {"text": "31-40 м²", "callback_data": "kp_area_31_40"},
            {"text": "41-50 м²", "callback_data": "kp_area_41_50"},
        ],
        [
            {"text": "51-70 м²", "callback_data": "kp_area_51_70"},
            {"text": "71-90 м²", "callback_data": "kp_area_71_90"},
            {"text": "90+ м²", "callback_data": "kp_area_90_999"},
        ],
        [{"text": "🔙 Назад", "callback_data": "kp_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_by_budget_menu(chat_id: int):
    """Показывает выбор диапазона бюджета."""
    text = "💰 <b>Выберите диапазон бюджета:</b>"
    
    inline_buttons = [
        [
            {"text": "до 15 млн", "callback_data": "kp_budget_0_15"},
            {"text": "15-18 млн", "callback_data": "kp_budget_15_18"},
            {"text": "18-22 млн", "callback_data": "kp_budget_18_22"},
        ],
        [
            {"text": "22-26 млн", "callback_data": "kp_budget_22_26"},
            {"text": "26-30 млн", "callback_data": "kp_budget_26_30"},
            {"text": "30+ млн", "callback_data": "kp_budget_30_999"},
        ],
        [{"text": "🔙 Назад", "callback_data": "kp_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_area_range(chat_id: int, min_area: float, max_area: float):
    """Показывает лоты по диапазону площади (первые 8)."""
    lots = get_lots_by_area_range(min_area, max_area)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ КП на {min_area}-{max_area} м² не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "kp_by_area"}]]
        )
        return
    
    display_lots = lots[:DEFAULT_DISPLAY_LIMIT]
    
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"📋 <b>КП на {area_text} м²</b> ({len(lots)} шт.):\n"
    
    inline_buttons = []
    
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        # Изменено: передаём код лота для точного поиска
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_select_{int(lot['area']*10)}"}])
    
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{
            "text": f"📋 Показать все ({len(lots)} шт.)", 
            "callback_data": f"kp_show_area_{int(min_area)}_{int(max_area)}"
        }])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "kp_by_area"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_budget_range(chat_id: int, min_budget: int, max_budget: int):
    """Показывает лоты по диапазону бюджета (первые 8)."""
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ КП на {min_budget}-{max_budget} млн не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "kp_by_budget"}]]
        )
        return
    
    display_lots = lots[:DEFAULT_DISPLAY_LIMIT]
    
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"📋 <b>КП на {budget_text} млн</b> ({len(lots)} шт.):\n"
    
    inline_buttons = []
    
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        # Изменено: передаём код лота для точного поиска
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_select_{int(lot['area']*10)}"}])
    
    if len(lots) > DEFAULT_DISPLAY_LIMIT:
        inline_buttons.append([{
            "text": f"📋 Показать все ({len(lots)} шт.)", 
            "callback_data": f"kp_show_budget_{min_budget}_{max_budget}"
        }])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "kp_by_budget"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_show_all_area(chat_id: int, min_area: float, max_area: float):
    """Показывает ВСЕ лоты по диапазону площади."""
    lots = get_lots_by_area_range(min_area, max_area)
    
    if not lots:
        await send_message(chat_id, "❌ КП не найдены.")
        return
    
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"📋 <b>Все КП на {area_text} м²</b> ({len(lots)} шт.):\n"
    
    inline_buttons = []
    
    for lot in lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_select_{int(lot['area']*10)}"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"kp_area_{int(min_area)}_{int(max_area)}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_show_all_budget(chat_id: int, min_budget: int, max_budget: int):
    """Показывает ВСЕ лоты по диапазону бюджета."""
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    
    if not lots:
        await send_message(chat_id, "❌ КП не найдены.")
        return
    
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"📋 <b>Все КП на {budget_text} млн</b> ({len(lots)} шт.):\n"
    
    inline_buttons = []
    
    for lot in lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_select_{int(lot['area']*10)}"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": f"kp_budget_{min_budget}_{max_budget}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_select_lot(chat_id: int, area_x10: int):
    """
    После выбора лота — спрашиваем какую рассрочку указать.
    area_x10: площадь * 10 (например 287 для 28.7 м²)
    """
    area = area_x10 / 10.0
    lots = get_lots_by_area_range(0, 9999)
    lot = None
    for l in lots:
        if abs(l['area'] - area) < 0.05:
            lot = l
            break
    
    if not lot:
        await send_message(chat_id, f"❌ Лот с площадью {area} м² не найден.")
        return
    
    text = (
        f"📋 <b>Лот {lot['code']}</b>\n"
        f"📐 {lot['area']} м² • 💰 {format_price_short(lot['price'])}\n\n"
        f"<b>Какую рассрочку указать в КП?</b>"
    )
    
    inline_buttons = [
        [
            {"text": "💯 100% оплата", "callback_data": f"kp_gen_{area_x10}_100"}],
        [
            {"text": "📄 12 месяцев", "callback_data": f"kp_gen_{area_x10}_12"},
            {"text": "📄 12 и 24 месяца", "callback_data": f"kp_gen_{area_x10}_24"},
        ],
        [{"text": "🔙 Назад", "callback_data": "kp_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_generate_pdf(chat_id: int, area_x10: int, mode: str = "24"):
    """
    Генерирует и отправляет PDF КП.
    area_x10: площадь * 10 (например 287 для 28.7 м²)
    """
    area = area_x10 / 10.0
    lots = get_lots_by_area_range(0, 9999)
    lot = None
    for l in lots:
        if abs(l['area'] - area) < 0.05:
            lot = l
            break
    
    if not lot:
        await send_message(chat_id, f"❌ Лот с площадью {area} м² не найден.")
        return
    
    # Отправляем "печатаем..."
    await send_message(chat_id, "⏳ Генерирую PDF...")
    
    # Генерируем PDF
    # Режим: "100" - 100% оплата, "12" - 12 мес, "24" - 12+24 мес
    full_payment = (mode == "100")
    include_24m = (mode == "24")
    pdf_path = generate_kp_pdf(area=lot["area"], include_24m=include_24m, full_payment=full_payment)
    
    if pdf_path and os.path.exists(pdf_path):
        # Отправляем PDF
        mode_text = "100% оплата (скидка 5%)" if full_payment else ("12 и 24 месяца" if include_24m else "12 месяцев")
        caption = f"📋 КП: {lot['code']} ({lot['area']} м²)\n💰 {format_price_short(lot['price'])}\n📅 {mode_text}"
        
        await send_document(chat_id, pdf_path, caption)
        
        # Удаляем временный файл
        try:
            os.remove(pdf_path)
        except:
            pass
        
        # Предлагаем дальнейшие действия
        inline_buttons = [
            [
                {"text": "📊 Доходность", "callback_data": f"calc_roi_lot_{int(lot['area']*10)}"},
                {"text": "💳 Рассрочка", "callback_data": f"calc_finance_lot_{int(lot['area']*10)}"},
            ],
            [
                {"text": "📋 Ещё КП", "callback_data": "kp_menu"},
                {"text": "🔥 Записаться на показ", "callback_data": "online_show"}
            ]
        ]
        await send_message_inline(chat_id, "Выберите действие:", inline_buttons)
    else:
        # Fallback на JPG если есть
        jpg_path = find_kp_by_area(lot['area'])
        
        if jpg_path and os.path.exists(jpg_path):
            caption = f"📋 КП: {lot['code']} ({lot['area']} м²)\n💰 {format_price_short(lot['price'])}"
            await send_photo(chat_id, jpg_path, caption)
            
            inline_buttons = [
                [
                    {"text": "📊 Доходность", "callback_data": f"calc_roi_lot_{int(lot['area']*10)}"},
                    {"text": "💳 Рассрочка", "callback_data": f"calc_finance_lot_{int(lot['area']*10)}"},
                ],
                [{"text": "📋 Ещё КП", "callback_data": "kp_menu"}]
            ]
            await send_message_inline(chat_id, "Выберите действие:", inline_buttons)
        else:
            await send_message(chat_id, "❌ Не удалось сгенерировать PDF. Попробуйте позже.")


# === LEGACY: для обратной совместимости ===

async def handle_kp_send_one(chat_id: int, unit_code: str = "", area: float = 0):
    """
    Отправляет одно КП по площади (legacy).
    Теперь перенаправляет на выбор рассрочки.
    """
    lot = get_lot_by_area(area) if area > 0 else get_lot_by_code(unit_code)
    
    if not lot:
        await send_message(chat_id, f"❌ Лот не найден.")
        return
    
    # Перенаправляем на выбор рассрочки
    await handle_kp_select_lot(chat_id, int(lot['area']*10))


async def handle_kp_request(chat_id: int, text: str):
    """Обрабатывает текстовый запрос на КП (для AI)."""
    code_match = re.search(r"[аaвb]\d{3,4}", text, re.IGNORECASE)
    if code_match:
        lot = get_lot_by_code(code_match.group())
        if lot:
            await handle_kp_select_lot(chat_id, int(lot['area']*10))
            return
    
    await handle_kp_menu(chat_id)
