"""
Обработчик коммерческих предложений.
"""

from typing import List, Dict, Any
import sqlite3
import os
import re

from services.telegram import send_message, send_message_inline, send_photo, send_media_group
from services.kp_search import (
    find_kp_by_code,
    get_all_kp_files,
    get_kp_info_from_filename,
    KP_DIR,
)
from models.state import set_dialog_state, clear_dialog_state, DialogStates
from config.settings import BASE_DIR


DB_PATH = os.path.join(BASE_DIR, "properties.db")


def find_kp_by_area(area: float) -> str:
    """Ищет КП по площади."""
    import os, re
    kp_dir = os.path.join(BASE_DIR, "kp_all")
    if not os.path.exists(kp_dir):
        return None
    
    for f in os.listdir(kp_dir):
        if not f.endswith(".jpg"):
            continue
        match = re.match(r"kp_([\d.]+)m_", f)
        if match:
            file_area = float(match.group(1))
            if abs(file_area - area) < 0.05:
                return os.path.join(kp_dir, f)
    return None


def get_kp_from_files() -> List[Dict[str, Any]]:
    """Получает список КП из файлов, добавляет цены из базы."""
    kp_list = []
    kp_dir = os.path.join(BASE_DIR, "kp_all")
    
    if not os.path.exists(kp_dir):
        return []
    
    for f in os.listdir(kp_dir):
        if not f.endswith(".jpg"):
            continue
        match = re.match(r"kp_([\d.]+)m_\w+_(.+)\.jpg", f)
        if match:
            area = float(match.group(1))
            code = match.group(2)
            kp_list.append({
                "code": code, 
                "area": area, 
                "filepath": os.path.join(kp_dir, f)
            })
    
    # Добавляем цены из базы
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for kp in kp_list:
            cur.execute("""
                SELECT price_rub, building FROM units 
                WHERE code = ? AND ABS(area_m2 - ?) < 0.5
            """, (kp["code"], kp["area"]))
            row = cur.fetchone()
            if row:
                kp["price"] = row[0]
                kp["building"] = row[1]
            else:
                kp["price"] = 0
                kp["building"] = 0
        conn.close()
    
    return [k for k in kp_list if k["price"] > 0]


def get_lots_by_area_range(min_area: float, max_area: float) -> List[Dict[str, Any]]:
    """Получает лоты по диапазону площади — ТОЛЬКО с КП."""
    all_kp = get_kp_from_files()
    return sorted(
        [k for k in all_kp if min_area <= k["area"] <= max_area],
        key=lambda x: (x["area"], x["price"])
    )


def get_lots_by_budget_range(min_budget: int, max_budget: int) -> List[Dict[str, Any]]:
    """Получает лоты по диапазону бюджета — ТОЛЬКО с КП."""
    all_kp = get_kp_from_files()
    return sorted(
        [k for k in all_kp if min_budget <= k["price"] <= max_budget],
        key=lambda x: (x["price"], x["area"])
    )

def get_kp_from_files() -> List[Dict[str, Any]]:
    """Получает список КП из файлов, добавляет цены из базы."""
    import re
    kp_list = []
    kp_dir = os.path.join(BASE_DIR, "kp_all")
    
    if not os.path.exists(kp_dir):
        return []
    
    for f in os.listdir(kp_dir):
        if not f.endswith(".jpg"):
            continue
        match = re.match(r"kp_([\d.]+)m_\w+_(.+)\.jpg", f)
        if match:
            area = float(match.group(1))
            code = match.group(2)
            kp_list.append({
                "code": code, 
                "area": area, 
                "filepath": os.path.join(kp_dir, f)
            })
    
    # Добавляем цены из базы
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for kp in kp_list:
            cur.execute("""
                SELECT price_rub, building FROM units 
                WHERE code = ? AND ABS(area_m2 - ?) < 0.5
            """, (kp["code"], kp["area"]))
            row = cur.fetchone()
            if row:
                kp["price"] = row[0]
                kp["building"] = row[1]
            else:
                kp["price"] = 0
                kp["building"] = 0
        conn.close()
    
    return [k for k in kp_list if k["price"] > 0]


def get_lots_by_area_range(min_area: float, max_area: float) -> List[Dict[str, Any]]:
    """Получает лоты по диапазону площади — ТОЛЬКО с КП."""
    all_kp = get_kp_from_files()
    return sorted(
        [k for k in all_kp if min_area <= k["area"] <= max_area],
        key=lambda x: (x["area"], x["price"])
    )


def get_lots_by_budget_range(min_budget: int, max_budget: int) -> List[Dict[str, Any]]:
    """Получает лоты по диапазону бюджета — ТОЛЬКО с КП."""
    all_kp = get_kp_from_files()
    return sorted(
        [k for k in all_kp if min_budget <= k["price"] <= max_budget],
        key=lambda x: (x["price"], x["area"])
    )







def normalize_code(code: str) -> str:
    """Нормализует код лота."""
    if not code:
        return ""
    code = str(code).strip().upper()
    table = str.maketrans({"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "S", "Т": "T"})
    return code.translate(table)


def format_price_short(price: int) -> str:
    """Форматирует цену кратко: 15.2 млн"""
    return f"{price / 1_000_000:.1f} млн"


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
    """Показывает лоты по диапазону площади."""
    lots = get_lots_by_area_range(min_area, max_area)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ КП на {min_area}-{max_area} м² не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "kp_by_area"}]]
        )
        return
    
    display_lots = lots[:8]
    
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    text = f"📋 <b>КП на {area_text} м²</b> ({len(lots)} лотов):\n"
    
    inline_buttons = []
    
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_send_{int(lot['area']*10)}"}])
    
    if len(lots) > 1:
        inline_buttons.append([{"text": f"📤 Отправить все ({len(lots)} шт.)", "callback_data": f"kp_all_area_{int(min_area)}_{int(max_area)}"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "kp_by_area"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_budget_range(chat_id: int, min_budget: int, max_budget: int):
    """Показывает лоты по диапазону бюджета."""
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ КП на {min_budget}-{max_budget} млн не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "kp_by_budget"}]]
        )
        return
    
    display_lots = lots[:8]
    
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    text = f"📋 <b>КП на {budget_text} млн</b> ({len(lots)} лотов):\n"
    
    inline_buttons = []
    
    for lot in display_lots:
        btn_text = f"{lot['code']} — {lot['area']} м² — {format_price_short(lot['price'])}"
        inline_buttons.append([{"text": btn_text, "callback_data": f"kp_send_{int(lot['area']*10)}"}])
    
    if len(lots) > 1:
        inline_buttons.append([{"text": f"📤 Отправить все ({len(lots)} шт.)", "callback_data": f"kp_all_budget_{min_budget}_{max_budget}"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "kp_by_budget"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_kp_send_one(chat_id: int, unit_code: str = "", area: float = 0):
    """Отправляет одно КП по площади."""
    filepath = find_kp_by_area(area) if area > 0 else None
    
    if filepath:
        info = get_kp_info_from_filename(filepath)
        caption = f"📋 КП: {info['code']} ({info['area']} м²)"
        await send_photo(chat_id, filepath, caption)
        
        inline_buttons = [
            [
                {"text": "📋 Ещё КП", "callback_data": "kp_menu"},
                {"text": "🔥 Записаться на показ", "callback_data": "online_show"}
            ]
        ]
        await send_message_inline(chat_id, "Хотите посмотреть другие варианты?", inline_buttons)
    else:
        await send_message(chat_id, f"❌ КП для лота {unit_code} не найдено.")


async def handle_kp_send_all_area(chat_id: int, min_area: float, max_area: float):
    """Отправляет все КП по диапазону площади."""
    lots = get_lots_by_area_range(min_area, max_area)
    
    if not lots:
        await send_message(chat_id, "❌ КП не найдены.")
        return
    
    filepaths = [lot["filepath"] for lot in lots]
    area_text = f"{int(min_area)}-{int(max_area)}" if max_area < 900 else f"{int(min_area)}+"
    
    if len(filepaths) <= 10:
        await send_media_group(chat_id, filepaths, f"📋 КП на {area_text} м² ({len(filepaths)} шт.)")
    else:
        for i in range(0, len(filepaths), 10):
            batch = filepaths[i:i+10]
            caption = f"📋 КП на {area_text} м² (часть {i//10 + 1})" if i > 0 else f"📋 КП на {area_text} м² ({len(filepaths)} шт.)"
            await send_media_group(chat_id, batch, caption)
    
    inline_buttons = [
        [
            {"text": "📋 Ещё КП", "callback_data": "kp_menu"},
            {"text": "🔥 Записаться на показ", "callback_data": "online_show"}
        ]
    ]
    await send_message_inline(chat_id, "Хотите посмотреть другие варианты?", inline_buttons)


async def handle_kp_send_all_budget(chat_id: int, min_budget: int, max_budget: int):
    """Отправляет все КП по диапазону бюджета."""
    lots = get_lots_by_budget_range(min_budget * 1_000_000, max_budget * 1_000_000)
    
    if not lots:
        await send_message(chat_id, "❌ КП не найдены.")
        return
    
    filepaths = [lot["filepath"] for lot in lots]
    budget_text = f"{min_budget}-{max_budget}" if max_budget < 900 else f"{min_budget}+"
    
    if len(filepaths) <= 10:
        await send_media_group(chat_id, filepaths, f"📋 КП на {budget_text} млн ({len(filepaths)} шт.)")
    else:
        for i in range(0, len(filepaths), 10):
            batch = filepaths[i:i+10]
            caption = f"📋 КП на {budget_text} млн (часть {i//10 + 1})" if i > 0 else f"📋 КП на {budget_text} млн ({len(filepaths)} шт.)"
            await send_media_group(chat_id, batch, caption)
    
    inline_buttons = [
        [
            {"text": "📋 Ещё КП", "callback_data": "kp_menu"},
            {"text": "🔥 Записаться на показ", "callback_data": "online_show"}
        ]
    ]
    await send_message_inline(chat_id, "Хотите посмотреть другие варианты?", inline_buttons)


async def handle_kp_request(chat_id: int, text: str):
    """Обрабатывает текстовый запрос на КП (для AI)."""
    code_match = re.search(r"[аaвb]\d{3,4}", text, re.IGNORECASE)
    if code_match:
        await handle_kp_send_one(chat_id, code_match.group())
        return
    
    await handle_kp_menu(chat_id)
