"""
RIZALTA Telegram Bot
Главный файл приложения.

Модульная архитектура:
- config/     - настройки
- models/     - состояния
- services/   - бизнес-логика
- handlers/   - обработчики событий
"""

from fastapi import FastAPI, Request
from typing import Dict, Any, List

# Конфигурация
from config.settings import (
    TELEGRAM_BOT_TOKEN,
    MAIN_MENU_BUTTONS,
    MAIN_MENU_TRIGGER_TEXTS,
    LINK_FIXATION,
    LINK_SHAHMATKA,
)

# Состояния
from models.state import (
    get_dialog_state,
    set_dialog_state,
    clear_dialog_state,
    clear_user_state,
    get_budget,
    save_budget,
    is_in_booking_flow,
    DialogStates,
)

# Сервисы
from services.telegram import send_message, send_message_inline, answer_callback_query
from services.calculations import normalize_unit_code

# Обработчики
from handlers import (
    # Динамические расчёты
    handle_calculations_menu_new,
    handle_calc_roi_menu,
    handle_calc_roi_by_area_menu,
    handle_calc_roi_by_budget_menu,
    handle_calc_roi_area_range,
    handle_calc_roi_budget_range,
    handle_calc_roi_lot,
    handle_calc_finance_menu,
    handle_calc_finance_by_area_menu,
    handle_calc_finance_by_budget_menu,
    handle_calc_finance_area_range,
    handle_calc_finance_budget_range,
    handle_calc_finance_lot,
    # Меню
    handle_start,
    handle_help,
    handle_back,
    handle_about_project,
    handle_calculations_menu,
    handle_why_rizalta,
    handle_why_altai,
    handle_architect,
    handle_choose_unit_for_roi,
    handle_choose_unit_for_finance,
    handle_choose_unit_for_layout,
    handle_main_menu,
    
    # Юниты
    handle_base_roi,
    handle_unit_roi,
    handle_finance_overview,
    handle_layouts,
    handle_select_lot,
    handle_budget_input,
    handle_format_input,
    handle_download_pdf,
    
    # Запись на показ
    handle_online_show_start,
    handle_call_manager,
    handle_contact_shared,
    handle_quick_contact,
    handle_booking_step,
    
    # AI
    handle_free_text,
    
    # КП
    handle_kp_menu,
    handle_kp_request,
    
    # Медиа
    handle_media_menu,
    handle_send_presentation,
)


app = FastAPI(title="RIZALTA Bot")


# ====== Health check ======

@app.get("/")
async def health():
    """Health check."""
    return {"ok": True, "bot": "RIZALTA"}


# ====== Telegram Webhook ======

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Главный webhook для обработки сообщений от Telegram."""
    
    try:
        upd = await request.json()
    except Exception as e:
        print(f"[WEBHOOK] JSON parse error: {e}")
        return {"ok": False}
    
    print(f"[WEBHOOK] update: {upd}")
    
    # ===== Callback Query (inline-кнопки) =====
    callback_query = upd.get("callback_query")
    if callback_query:
        await process_callback(callback_query)
        return {"ok": True}
    
    # ===== Message =====
    msg = upd.get("message") or upd.get("edited_message")
    if not msg:
        return {"ok": True}
    
    chat_id = msg["chat"]["id"]
    text = (msg.get("text") or "").strip()
    
    # Обработка контакта
    contact_data = msg.get("contact")
    if contact_data:
        await handle_contact_shared(chat_id, contact_data)
        return {"ok": True}
    
    if not text:
        return {"ok": True}
    
    user_info = msg.get("from", {})
    
    await process_message(chat_id, text, user_info)
    return {"ok": True}


async def process_callback(callback: Dict[str, Any]):
    """Обработка нажатия inline-кнопки."""
    
    callback_id = callback.get("id")
    data = callback.get("data", "")
    message = callback.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    from_user = callback.get("from", {})
    username = from_user.get("username", "")
    
    if not chat_id:
        return
    
    # Убираем часики
    if callback_id:
        await answer_callback_query(callback_id)
    
    # ===== Роутинг callback_data =====
    
    if data == "download_pdf":
        await handle_download_pdf(chat_id, username)
    
    elif data == "select_lot":
        await handle_select_lot(chat_id)
    
    elif data == "call_manager" or data == "online_show":
        await handle_online_show_start(chat_id)
    
    elif data == "calculate_roi":
        await handle_choose_unit_for_roi(chat_id)
    
    elif data == "get_layouts":
        from handlers.docs import handle_documents_menu
        await handle_documents_menu(chat_id)
    
    elif data.startswith("roi_"):
        unit_code = data[4:]
        await handle_base_roi(chat_id, unit_code=unit_code)
    
    elif data.startswith("finance_"):
        unit_code = data[8:]
        await handle_finance_overview(chat_id, unit_code=unit_code)
    
    elif data.startswith("layout_"):
        unit_code = data[7:]
        await handle_layouts(chat_id, unit_code=unit_code)
    
    # ===== Медиа =====
    
    elif data == "media_menu":
        await handle_media_menu(chat_id)
    
    elif data == "media_presentation":
        await handle_send_presentation(chat_id)
    
    elif data == "back_to_menu":
        await handle_main_menu(chat_id)
    
    # ===== КП =====
    
    elif data == "kp_menu":
        await handle_kp_menu(chat_id)
    
    elif data == "kp_refine":
        await handle_kp_menu(chat_id)
    
    elif data == "kp_by_area":
        from handlers.kp import handle_kp_by_area_menu
        await handle_kp_by_area_menu(chat_id)
    
    elif data == "kp_by_budget":
        from handlers.kp import handle_kp_by_budget_menu
        await handle_kp_by_budget_menu(chat_id)
    
    elif data.startswith("kp_area_"):
        # kp_area_22_25 -> min=22, max=25
        from handlers.kp import handle_kp_area_range
        parts = data.replace("kp_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_kp_area_range(chat_id, min_area, max_area)
    
    elif data.startswith("kp_budget_"):
        # kp_budget_15_18 -> min=15, max=18
        from handlers.kp import handle_kp_budget_range
        parts = data.replace("kp_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_kp_budget_range(chat_id, min_budget, max_budget)
    
    elif data.startswith("kp_send_"):
        # kp_send_273 -> отправить КП (273 = area * 10)
        from handlers.kp import handle_kp_send_one
        area_str = data.replace("kp_send_", "")
        area = int(area_str) / 10.0 if area_str.isdigit() else 0
        await handle_kp_send_one(chat_id, area=area)
    
    elif data.startswith("kp_all_area_"):
        # kp_all_area_22_25 -> отправить все по площади
        from handlers.kp import handle_kp_send_all_area
        parts = data.replace("kp_all_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_kp_send_all_area(chat_id, min_area, max_area)
    
    elif data.startswith("kp_all_budget_"):
        # kp_all_budget_15_18 -> отправить все по бюджету
        from handlers.kp import handle_kp_send_all_budget
        parts = data.replace("kp_all_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_kp_send_all_budget(chat_id, min_budget, max_budget)

    # ===== Документы =====

    elif data == "doc_menu":
        from handlers.docs import handle_documents_menu
        await handle_documents_menu(chat_id)

    elif data == "doc_ddu":
        from handlers.docs import handle_send_ddu
        await handle_send_ddu(chat_id)

    elif data == "doc_arenda":
        from handlers.docs import handle_send_arenda
        await handle_send_arenda(chat_id)

    elif data == "doc_all":
        from handlers.docs import handle_send_all_docs
        await handle_send_all_docs(chat_id)

    # ===== Динамические расчёты =====

    elif data == "calc_main_menu":
        await handle_calculations_menu_new(chat_id)

    elif data == "calc_roi_menu":
        await handle_calc_roi_menu(chat_id)

    elif data == "calc_finance_menu":
        await handle_calc_finance_menu(chat_id)

    elif data == "calc_roi_by_area":
        await handle_calc_roi_by_area_menu(chat_id)

    elif data == "calc_roi_by_budget":
        await handle_calc_roi_by_budget_menu(chat_id)

    elif data == "calc_finance_by_area":
        await handle_calc_finance_by_area_menu(chat_id)

    elif data == "calc_finance_by_budget":
        await handle_calc_finance_by_budget_menu(chat_id)

    elif data.startswith("calc_roi_area_"):
        parts = data.replace("calc_roi_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_calc_roi_area_range(chat_id, min_area, max_area)

    elif data.startswith("calc_roi_budget_"):
        parts = data.replace("calc_roi_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_calc_roi_budget_range(chat_id, min_budget, max_budget)

    elif data.startswith("calc_fin_area_"):
        parts = data.replace("calc_fin_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_calc_finance_area_range(chat_id, min_area, max_area)

    elif data.startswith("calc_fin_budget_"):
        parts = data.replace("calc_fin_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_calc_finance_budget_range(chat_id, min_budget, max_budget)

    elif data.startswith("calc_roi_lot_"):
        area_str = data.replace("calc_roi_lot_", "")
        area = int(area_str) / 10.0 if area_str.isdigit() else 0
        await handle_calc_roi_lot(chat_id, area)

    elif data.startswith("calc_finance_lot_"):
        area_str = data.replace("calc_finance_lot_", "")
        area = int(area_str) / 10.0 if area_str.isdigit() else 0
        await handle_calc_finance_lot(chat_id, area)


async def process_message(chat_id: int, text: str, user_info: Dict[str, Any]):
    """Главный роутер текстовых сообщений."""
    
    # ===== Проверка кнопок главного меню =====
    # При нажатии сбрасываем состояния
    is_main_menu_button = any(btn in text for btn in MAIN_MENU_TRIGGER_TEXTS)
    
    if is_main_menu_button:
        clear_dialog_state(chat_id)
    
    # ===== Команды =====
    
    if text.startswith("/start"):
        await handle_start(chat_id, text, user_info)
        return
    
    if text == "/help":
        await handle_help(chat_id)
        return
    
    # ===== Кнопка Назад =====
    
    if text in ("🔙 Назад", "⬅️ Назад", "Назад"):
        await handle_back(chat_id)
        return
    
    # ===== Диалоговые состояния =====
    
    state = get_dialog_state(chat_id)
    
    # Подбор лота: ввод бюджета
    if state == DialogStates.CHOOSE_UNIT_ASK_BUDGET and not is_main_menu_button:
        await handle_budget_input(chat_id, text)
        return
    
    # Подбор лота: выбор формата
    if state == DialogStates.CHOOSE_UNIT_ASK_FORMAT and not is_main_menu_button:
        await handle_format_input(chat_id, text)
        return
    
    # Запись на показ: ввод контакта
    if state == DialogStates.ASK_CONTACT_FOR_CALLBACK and not is_main_menu_button:
        if text == "✍️ Ввести вручную":
            await send_message(chat_id, "Напишите ваш телефон или @username:")
            return
        await handle_quick_contact(chat_id, text)
        return
    
    # Многошаговая запись
    if is_in_booking_flow(chat_id) and not text.startswith("/") and not is_main_menu_button:
        await handle_booking_step(chat_id, text)
        return
    
    # Выбор юнита для ROI
    if state == DialogStates.CHOOSE_ROI_UNIT:
        normalized = normalize_unit_code(text)
        if normalized in ["A209", "B210", "A305"]:
            await handle_base_roi(chat_id, unit_code=text)
            return
    
    # Выбор юнита для рассрочки
    if state == DialogStates.CHOOSE_FINANCE_UNIT:
        normalized = normalize_unit_code(text)
        if normalized in ["A209", "B210", "A305"]:
            await handle_finance_overview(chat_id, unit_code=text)
            return
    
    # Выбор юнита для планировки
    if state == DialogStates.CHOOSE_PLAN_UNIT:
        normalized = normalize_unit_code(text)
        if normalized in ["A209", "B210", "A305"]:
            await handle_layouts(chat_id, unit_code=text)
            return
    
    # Запрос КП
    if state == DialogStates.AWAIT_KP_REQUEST and not is_main_menu_button:
        await handle_kp_request(chat_id, text)
        return
    
    # ===== Кнопки главного меню =====
    
    if "📖 О проекте" in text or text == "О проекте":
        await handle_about_project(chat_id)
        return
    
    if "💰 Расчёты" in text or text == "Расчёты":
        await handle_calculations_menu_new(chat_id)
        return
    
    if "📋 КП (JPG)" in text:
        await handle_kp_menu(chat_id)
        return
    
    if "🎯 Подобрать лот" in text or "Выбрать лот" in text or "🧩 Выбрать лот" in text:
        await handle_select_lot(chat_id)
        return
    
    if "🔥 Записаться на онлайн-показ" in text or "📅 Записаться на онлайн показ" in text:
        await handle_online_show_start(chat_id)
        return
    
    if "📄 Договоры" in text:
        from handlers.docs import handle_documents_menu
        await handle_documents_menu(chat_id)
        return
    
    # ===== Новые кнопки =====
    
    if "📌 Фиксация клиента" in text:
        inline_buttons = [
            [{"text": "🔗 Открыть форму фиксации", "url": LINK_FIXATION}]
        ]
        await send_message_inline(
            chat_id,
            "📌 <b>Фиксация клиента</b>\n\nНажмите кнопку ниже, чтобы открыть форму фиксации:",
            inline_buttons
        )
        return
    
    if "🏠 Шахматка" in text:
        inline_buttons = [
            [{"text": "🔗 Открыть шахматку", "url": LINK_SHAHMATKA}]
        ]
        await send_message_inline(
            chat_id,
            "🏠 <b>Шахматка</b>\n\nНажмите кнопку ниже, чтобы открыть шахматку с актуальными лотами:",
            inline_buttons
        )
        return
    
    if "🎬 Медиа" in text:
        await handle_media_menu(chat_id)
        return
    
    # ===== Подменю "О проекте" =====
    
    if "Почему RIZALTA" in text or "✨ Почему RIZALTA" in text:
        await handle_why_rizalta(chat_id)
        return
    
    if "Почему Алтай" in text or "🏔 Почему Алтай" in text or "ℹ️ Почему Алтай" in text:
        await handle_why_altai(chat_id)
        return
    
    if "Об архитекторе" in text or "👨‍🎨 Об архитекторе" in text:
        await handle_architect(chat_id)
        return
    
    # ===== Подменю "Расчёты" =====
    
    if "📊 Рентабельность/доходность" in text or "📊 Расчёт доходности" in text:
        await handle_choose_unit_for_roi(chat_id)
        return
    
    if "💳 Рассрочка и ипотека" in text:
        await handle_choose_unit_for_finance(chat_id)
        return
    
    # ===== Подменю "Медиа" =====
    
    if "📊 Презентация" in text:
        await handle_send_presentation(chat_id)
        return
    
    # ===== Выбор юнита по кнопкам =====
    
    if text in ["A209", "B210", "A305"]:
        state = get_dialog_state(chat_id)
        
        if state == DialogStates.CHOOSE_ROI_UNIT:
            await handle_base_roi(chat_id, unit_code=text)
            return
        
        if state == DialogStates.CHOOSE_FINANCE_UNIT:
            await handle_finance_overview(chat_id, unit_code=text)
            return
        
        if state == DialogStates.CHOOSE_PLAN_UNIT:
            await handle_layouts(chat_id, unit_code=text)
            return
        
        # Без состояния — игнорируем
        return
    
    # ===== Свободный текст → AI =====
    
    await handle_free_text(chat_id, text)


# ====== Запуск ======

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
