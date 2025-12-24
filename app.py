import asyncio
"""
RIZALTA Telegram Bot v2.1.0
Главный файл приложения с GPT Intent Router.

Изменения v2.1.0:
- Показ ВСЕХ 348 актуальных лотов (вместо 69 уникальных)
- UI: Корпус → Этаж → Лоты
- Голосовое управление с параметрами building, floor, code
- Нормализация кодов А↔A, В↔B

Изменения v2.0:
- Убраны regex паттерны
- Добавлен GPT Intent Router
- Убран режим секретаря (не нужен)
- Голосовые сообщения через GPT-роутинг
"""

from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from typing import Dict, Any

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
from services.telegram import send_message, send_message_inline, answer_callback_query, send_document
from services.calculations import normalize_unit_code

# Intent Router (NEW!)
from services.intent_router import classify_intent

# Обработчики
from handlers import (
    handle_secretary_menu,
    handle_secretary_day,
    handle_secretary_week,
    handle_secretary_task_detail,
    handle_secretary_done,
    handle_secretary_undone,
    handle_secretary_delete,
    handle_secretary_move_menu,
    handle_secretary_move_to,
    handle_secretary_add_prompt,
    process_secretary_input,
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
    handle_myid,
    
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
    handle_send_presentation_file,
    handle_video_menu,
    handle_send_video,
)


app = FastAPI(title="RIZALTA Bot v2.1.0")


# ====== Фоновая задача напоминаний ======

async def reminder_loop():
    import os
    """Проверяет и отправляет напоминания каждую минуту."""
    import sqlite3
    import aiohttp
    from datetime import datetime, timedelta
    from pathlib import Path
    
    DB_PATH = Path("/opt/bot/secretary.db")
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    ALTAI_OFFSET = 4
    
    while True:
        try:
            if DB_PATH.exists():
                conn = sqlite3.connect(str(DB_PATH))
                cursor = conn.cursor()
                
                now_msk = datetime.now()
                now_altai = now_msk + timedelta(hours=ALTAI_OFFSET)
                remind_time = now_altai + timedelta(minutes=15)
                
                today = now_altai.strftime("%Y-%m-%d")
                current_time = now_altai.strftime("%H:%M")
                remind_time_str = remind_time.strftime("%H:%M")
                
                cursor.execute("""
                    SELECT id, user_id, task_text, due_date, due_time, client_name
                    FROM tasks 
                    WHERE status = 'pending' 
                    AND reminder_sent = 0
                    AND due_date = ?
                    AND due_time IS NOT NULL
                    AND due_time <= ?
                    AND due_time > ?
                """, (today, remind_time_str, current_time))
                
                tasks = cursor.fetchall()
                
                for task in tasks:
                    task_id, user_id, task_text, due_date, due_time, client_name = task
                    
                    client_info = f"\n👤 Клиент: {client_name}" if client_name else ""
                    message = f"""⏰ <b>Напоминание!</b>

📋 {task_text}{client_info}
🕐 Через 15 минут ({due_time})"""
                    
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {
                        "chat_id": user_id,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_notification": False
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload) as resp:
                            result = await resp.json()
                            if result.get("ok"):
                                cursor.execute("UPDATE tasks SET reminder_sent = 1 WHERE id = ?", (task_id,))
                                conn.commit()
                                print(f"[REMINDER] ✅ {user_id}: {task_text}")
                            else:
                                print(f"[REMINDER] ❌ {user_id}: {result}")
                
                conn.close()
        except Exception as e:
            print(f"[REMINDER] Error: {e}")
        
        await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    """Запуск фоновых задач при старте бота."""
    asyncio.create_task(reminder_loop())
    print("[DEV] Фоновая задача напоминаний запущена")


# ====== Health check ======

@app.get("/")
async def health():
    """Health check."""
    return {"ok": True, "bot": "RIZALTA", "version": "2.1.0"}


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
    
    # Обработка голосового сообщения
    voice = msg.get("voice")
    if voice:
        await process_voice_message(chat_id, voice, msg.get("from", {}))
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
    user_info = from_user
    
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
        from handlers.booking_calendar import handle_booking_start
        await handle_booking_start(chat_id)
    
    elif data == "calculate_roi":
        await handle_choose_unit_for_roi(chat_id)
    
    elif data == "get_layouts":
        from handlers.docs import handle_documents_menu
        await handle_documents_menu(chat_id)
    
    elif data.startswith("roi_xlsx_"):
        area_x10 = int(data.replace("roi_xlsx_", ""))
        area = area_x10 / 10
        await send_message(chat_id, f"⏳ Создаю Excel для {area} м²...")
        from services.calc_xlsx_generator import generate_roi_xlsx
        xlsx_path = generate_roi_xlsx(area=area)
        if xlsx_path:
            await send_document(chat_id, xlsx_path, f"ROI_{area}m2.xlsx")
        else:
            await send_message(chat_id, f"❌ Ошибка создания Excel")

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
    elif data.startswith("pres_"):
        await handle_send_presentation_file(chat_id, data)
    elif data == "media_video":
        await handle_video_menu(chat_id)
    
    # === AI-Секретарь ===
    elif data == "secretary_menu":
        await handle_secretary_menu(chat_id)
    elif data.startswith("sec_day_"):
        date_str = data.replace("sec_day_", "")
        await handle_secretary_day(chat_id, date_str)
    elif data.startswith("sec_week_"):
        date_str = data.replace("sec_week_", "")
        await handle_secretary_week(chat_id, date_str)
    elif data.startswith("sec_task_"):
        task_id = int(data.replace("sec_task_", ""))
        await handle_secretary_task_detail(chat_id, task_id)
    elif data.startswith("sec_done_"):
        task_id = int(data.replace("sec_done_", ""))
        await handle_secretary_done(chat_id, task_id)
    elif data.startswith("sec_undone_"):
        task_id = int(data.replace("sec_undone_", ""))
        await handle_secretary_undone(chat_id, task_id)
    elif data.startswith("sec_del_"):
        task_id = int(data.replace("sec_del_", ""))
        await handle_secretary_delete(chat_id, task_id)
    elif data.startswith("sec_move_") and not data.startswith("sec_moveto_"):
        task_id = int(data.replace("sec_move_", ""))
        await handle_secretary_move_menu(chat_id, task_id)
    elif data.startswith("sec_moveto_"):
        parts = data.replace("sec_moveto_", "").split("_")
        task_id = int(parts[0])
        new_date = parts[1]
        await handle_secretary_move_to(chat_id, task_id, new_date)
    elif data == "sec_add":
        await handle_secretary_add_prompt(chat_id)
    elif data.startswith("sec_add_"):
        preset_date = data.replace("sec_add_", "")
        await handle_secretary_add_prompt(chat_id, preset_date)
    elif data.startswith("video_"):
        await handle_send_video(chat_id, data)
    
    elif data == "back_to_menu":
        await handle_main_menu(chat_id)
    
    # ===== КП v2.1.0 - НОВЫЕ CALLBACK'И =====
    
    elif data == "kp_menu":
        from handlers.kp import handle_kp_menu
        await handle_kp_menu(chat_id)
    
    elif data == "kp_refine":
        from handlers.kp import handle_kp_menu
        await handle_kp_menu(chat_id)
    
    elif data == "kp_by_building":
        from handlers.kp import handle_kp_by_building_menu
        await handle_kp_by_building_menu(chat_id)
    
    elif data.startswith("kp_building_all_"):
        from handlers.kp import handle_kp_building_all
        building = int(data.replace("kp_building_all_", ""))
        await handle_kp_building_all(chat_id, building)
    
    elif data.startswith("kp_building_"):
        from handlers.kp import handle_kp_building
        building = int(data.replace("kp_building_", ""))
        await handle_kp_building(chat_id, building)
    
    elif data.startswith("kp_floors_"):
        from handlers.kp import handle_kp_floors_range
        parts = data.replace("kp_floors_", "").split("_")
        building = int(parts[0])
        floor_range = parts[1]  # "upper", "lower", "middle"
        await handle_kp_floors_range(chat_id, building, floor_range)
    
    elif data.startswith("kp_floor_all_"):
        from handlers.kp import handle_kp_floor
        parts = data.replace("kp_floor_all_", "").split("_")
        building = int(parts[0])
        floor = int(parts[1])
        await handle_kp_floor(chat_id, building, floor)
    
    elif data.startswith("kp_floor_"):
        from handlers.kp import handle_kp_floor
        parts = data.replace("kp_floor_", "").split("_")
        building = int(parts[0])
        floor = int(parts[1])
        await handle_kp_floor(chat_id, building, floor)
    
    elif data.startswith("kp_lot_"):
        from handlers.kp import handle_kp_lot
        parts = data.replace("kp_lot_", "").split("_")
        code = parts[0]
        building = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        await handle_kp_lot(chat_id, code, building)
    
    elif data.startswith("kp_gen_"):
        from handlers.kp import handle_kp_generate
        # Формат: kp_gen_{code}_{building}_{mode} или kp_gen_{code}_{mode}
        raw = data.replace("kp_gen_", "")
        parts = raw.rsplit("_", 1)  # Отделяем mode от остального
        if len(parts) == 2:
            code_part = parts[0]  # Может быть "В708" или "В708_1"
            mode = parts[1]       # "100", "12", "full"
            await handle_kp_generate(chat_id, code_part, mode)
    
    elif data == "kp_by_code":
        from handlers.kp import handle_kp_by_code_menu
        await handle_kp_by_code_menu(chat_id)
    
    elif data == "kp_show_more":
        from handlers.kp import handle_kp_show_more
        await handle_kp_show_more(chat_id)
    
    # ===== Расчёты через универсальную навигацию =====
    
    elif data == "calc_nav_menu":
        from handlers.kp import handle_nav_menu
        await handle_nav_menu(chat_id, mode="calc")
    
    elif data == "calc_nav_by_building":
        from handlers.kp import handle_nav_by_building_menu
        await handle_nav_by_building_menu(chat_id, mode="calc")
    
    elif data == "calc_nav_by_area":
        from handlers.kp import handle_kp_by_area_menu
        await handle_kp_by_area_menu(chat_id)
    
    elif data == "calc_nav_by_budget":
        from handlers.kp import handle_kp_by_budget_menu
        await handle_kp_by_budget_menu(chat_id)
    
    elif data == "calc_nav_by_code":
        from handlers.kp import handle_kp_by_code_menu
        await handle_kp_by_code_menu(chat_id)
    
    elif data.startswith("calc_nav_building_all_"):
        from handlers.kp import handle_kp_building_all
        building = int(data.replace("calc_nav_building_all_", ""))
        await handle_kp_building_all(chat_id, building)
    
    elif data.startswith("calc_nav_building_"):
        from handlers.kp import handle_nav_building
        building = int(data.replace("calc_nav_building_", ""))
        await handle_nav_building(chat_id, building, mode="calc")
    
    elif data.startswith("calc_nav_floors_"):
        from handlers.kp import handle_kp_floors_range
        parts = data.replace("calc_nav_floors_", "").split("_")
        building = int(parts[0])
        floor_range = parts[1]
        await handle_kp_floors_range(chat_id, building, floor_range)
    
    elif data.startswith("calc_nav_floor_"):
        from handlers.kp import handle_nav_floor
        parts = data.replace("calc_nav_floor_", "").split("_")
        building = int(parts[0])
        floor = int(parts[1])
        await handle_nav_floor(chat_id, building, floor, mode="calc")
    
    elif data.startswith("calc_nav_lot_"):
        from handlers.kp import handle_nav_lot
        parts = data.replace("calc_nav_lot_", "").split("_")
        code = parts[0]
        building = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        await handle_nav_lot(chat_id, code, building, mode="calc")
    
    # ===== Сравнение через универсальную навигацию =====
    
    elif data == "compare_nav_menu":
        from handlers.kp import handle_nav_menu
        await handle_nav_menu(chat_id, mode="compare")
    
    elif data == "compare_nav_by_building":
        from handlers.kp import handle_nav_by_building_menu
        await handle_nav_by_building_menu(chat_id, mode="compare")
    
    elif data == "compare_nav_by_area":
        from handlers.kp import handle_kp_by_area_menu
        await handle_kp_by_area_menu(chat_id)
    
    elif data == "compare_nav_by_budget":
        from handlers.kp import handle_kp_by_budget_menu
        await handle_kp_by_budget_menu(chat_id)
    
    elif data == "compare_nav_by_code":
        from handlers.kp import handle_kp_by_code_menu
        await handle_kp_by_code_menu(chat_id)
    
    elif data.startswith("compare_nav_building_all_"):
        from handlers.kp import handle_kp_building_all
        building = int(data.replace("compare_nav_building_all_", ""))
        await handle_kp_building_all(chat_id, building)
    
    elif data.startswith("compare_nav_building_"):
        from handlers.kp import handle_nav_building
        building = int(data.replace("compare_nav_building_", ""))
        await handle_nav_building(chat_id, building, mode="compare")
    
    elif data.startswith("compare_nav_floors_"):
        from handlers.kp import handle_kp_floors_range
        parts = data.replace("compare_nav_floors_", "").split("_")
        building = int(parts[0])
        floor_range = parts[1]
        await handle_kp_floors_range(chat_id, building, floor_range)
    
    elif data.startswith("compare_nav_floor_"):
        from handlers.kp import handle_nav_floor
        parts = data.replace("compare_nav_floor_", "").split("_")
        building = int(parts[0])
        floor = int(parts[1])
        await handle_nav_floor(chat_id, building, floor, mode="compare")
    
    elif data.startswith("compare_nav_lot_"):
        from handlers.kp import handle_nav_lot
        parts = data.replace("compare_nav_lot_", "").split("_")
        code = parts[0]
        building = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        await handle_nav_lot(chat_id, code, building, mode="compare")
    
    elif data == "kp_by_area":
        from handlers.kp import handle_kp_by_area_menu
        await handle_kp_by_area_menu(chat_id)
    
    elif data == "kp_by_budget":
        from handlers.kp import handle_kp_by_budget_menu
        await handle_kp_by_budget_menu(chat_id)
    
    elif data.startswith("kp_area_"):
        from handlers.kp import handle_kp_area_range
        parts = data.replace("kp_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_kp_area_range(chat_id, min_area, max_area)
    
    elif data.startswith("kp_budget_"):
        from handlers.kp import handle_kp_budget_range
        parts = data.replace("kp_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_kp_budget_range(chat_id, min_budget, max_budget)
    
    elif data.startswith("kp_send_"):
        from handlers.kp import handle_kp_send_one
        area_str = data.replace("kp_send_", "")
        area = int(area_str) / 10.0 if area_str.isdigit() else 0
        await handle_kp_send_one(chat_id, area=area)
    
    elif data.startswith("kp_show_area_"):
        from handlers.kp import handle_kp_show_all_area
        parts = data.replace("kp_show_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_kp_show_all_area(chat_id, min_area, max_area)
    
    elif data.startswith("kp_show_budget_"):
        from handlers.kp import handle_kp_show_all_budget
        parts = data.replace("kp_show_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_kp_show_all_budget(chat_id, min_budget, max_budget)

    elif data.startswith("kp_select_"):
        from handlers.kp import handle_kp_select_lot
        area_x10 = int(data.replace("kp_select_", ""))
        await handle_kp_select_lot(chat_id, area_x10)

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
        from handlers.kp import handle_nav_menu
        await handle_nav_menu(chat_id, mode="calc")

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

    elif data.startswith("calc_roi_show_area_"):
        from handlers.calc_dynamic import handle_calc_roi_show_all_area
        parts = data.replace("calc_roi_show_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_calc_roi_show_all_area(chat_id, min_area, max_area)

    elif data.startswith("calc_roi_show_budget_"):
        from handlers.calc_dynamic import handle_calc_roi_show_all_budget
        parts = data.replace("calc_roi_show_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_calc_roi_show_all_budget(chat_id, min_budget, max_budget)

    elif data.startswith("calc_fin_show_area_"):
        from handlers.calc_dynamic import handle_calc_finance_show_all_area
        parts = data.replace("calc_fin_show_area_", "").split("_")
        min_area, max_area = float(parts[0]), float(parts[1])
        await handle_calc_finance_show_all_area(chat_id, min_area, max_area)

    elif data.startswith("calc_fin_show_budget_"):
        from handlers.calc_dynamic import handle_calc_finance_show_all_budget
        parts = data.replace("calc_fin_show_budget_", "").split("_")
        min_budget, max_budget = int(parts[0]), int(parts[1])
        await handle_calc_finance_show_all_budget(chat_id, min_budget, max_budget)

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

    # ===== Календарь бронирования =====

    elif data == "booking_calendar":
        from handlers.booking_calendar import handle_booking_start
        await handle_booking_start(chat_id)

    elif data.startswith("book_spec_"):
        from handlers.booking_calendar import handle_select_specialist
        spec_id = int(data.replace("book_spec_", ""))
        await handle_select_specialist(chat_id, spec_id)

    elif data == "book_back_specialist":
        from handlers.booking_calendar import handle_booking_start
        await handle_booking_start(chat_id)

    elif data.startswith("book_date_"):
        from handlers.booking_calendar import handle_select_date
        date_str = data.replace("book_date_", "")
        await handle_select_date(chat_id, date_str)

    elif data.startswith("book_time_"):
        from handlers.booking_calendar import handle_select_time
        time_str = data.replace("book_time_", "")
        await handle_select_time(chat_id, time_str, username)

    elif data.startswith("book_confirm_"):
        from handlers.booking_calendar import handle_confirm_booking
        booking_id = int(data.replace("book_confirm_", ""))
        await handle_confirm_booking(chat_id, booking_id)

    elif data.startswith("book_decline_"):
        from handlers.booking_calendar import handle_decline_booking
        booking_id = int(data.replace("book_decline_", ""))
        await handle_decline_booking(chat_id, booking_id)

    # ===== Domoplaner =====
    elif data == "domo_all":
        flats = domoplaner_cache.get(chat_id, [])
        if not flats:
            await send_message(chat_id, "❌ Подборка не найдена. Отправьте ссылку заново.")
        else:
            await send_message(chat_id, f"⏳ Генерирую {len(flats)} КП...")
            from services.kp_pdf_generator import generate_kp_pdf
            success = 0
            for flat in flats:
                pdf_path = generate_kp_pdf(code=flat["code"], include_18m=True)
                if pdf_path:
                    await send_document(chat_id, pdf_path, f"КП_{flat['code']}.pdf")
                    success += 1
            await send_message(chat_id, f"✅ Создано {success} из {len(flats)} КП")


    elif data.startswith("domo_"):
        lot_code = data.replace("domo_", "")
        await send_message(chat_id, f"⏳ Генерирую КП для {lot_code}...")
        from services.kp_pdf_generator import generate_kp_pdf
        pdf_path = generate_kp_pdf(code=lot_code, include_18m=True)
        if pdf_path:
            await send_document(chat_id, pdf_path, f"КП_{lot_code}.pdf")
        else:
            await send_message(chat_id, f"❌ Лот {lot_code} не найден в базе.")

    # ===== Новости =====

    elif data == "news_menu":
        from handlers.news import handle_news_menu
        await handle_news_menu(chat_id)

    elif data == "news_currency":
        from handlers.news import handle_currency_rates
        await handle_currency_rates(chat_id)

    elif data == "news_weather":
        from handlers.news import handle_weather
        await handle_weather(chat_id)

    elif data == "news_digest":
        from handlers.news import handle_news_digest
        await handle_news_digest(chat_id)

    elif data == "news_flights":
        from handlers.news import handle_flights
        await handle_flights(chat_id)

    # ===== Сравнение депозит vs RIZALTA =====

    elif data == "compare_menu":
        from handlers.kp import handle_nav_menu
        await handle_nav_menu(chat_id, mode="compare")

    elif data == "compare_by_area":
        from handlers.compare import handle_compare_by_area_menu
        await handle_compare_by_area_menu(chat_id)

    elif data == "compare_by_budget":
        from handlers.compare import handle_compare_by_budget_menu
        await handle_compare_by_budget_menu(chat_id)

    elif data == "compare_quick":
        from handlers.compare import handle_compare_quick
        await handle_compare_quick(chat_id)

    elif data.startswith("compare_area_"):
        from handlers.compare import handle_compare_area_range
        parts = data.split("_")
        min_area = float(parts[2])
        max_area = float(parts[3])
        await handle_compare_area_range(chat_id, min_area, max_area)

    elif data.startswith("compare_budget_"):
        from handlers.compare import handle_compare_budget_range
        parts = data.split("_")
        min_budget = int(parts[2]) * 1_000_000
        max_budget = int(parts[3]) * 1_000_000
        await handle_compare_budget_range(chat_id, min_budget, max_budget)

    elif data.startswith("compare_lot_back_"):
        from handlers.compare import handle_compare_lot
        amount = int(data.split("_")[3])
        await handle_compare_lot(chat_id, "выбранный", amount)

    elif data.startswith("compare_lot_"):
        from handlers.compare import handle_compare_lot
        parts = data.split("_")
        lot_code = parts[2]
        price = int(parts[3]) * 1000
        await handle_compare_lot(chat_id, lot_code, price)

    elif data.startswith("compare_table_"):
        from handlers.compare import handle_compare_table
        amount = int(data.split("_")[2])
        await handle_compare_table(chat_id, amount)

    elif data == "compare_table":
        from handlers.compare import handle_compare_table
        await handle_compare_table(chat_id)

    elif data.startswith("compare_period_"):
        from handlers.compare import handle_compare_period
        parts = data.split("_")
        years = int(parts[2])
        amount = int(parts[3]) if len(parts) > 3 else 15_000_000
        await handle_compare_period(chat_id, years, amount)

    elif data.startswith("compare_full_"):
        from handlers.compare import handle_compare_full
        parts = data.split("_")
        years = int(parts[2])
        amount = int(parts[3]) if len(parts) > 3 else 15_000_000
        await handle_compare_full(chat_id, years, amount)

    elif data.startswith("compare_amount_"):
        from handlers.compare import handle_compare_amount_menu
        context = data.split("_")[2]
        await handle_compare_amount_menu(chat_id, context)

    elif data.startswith("compare_sum_"):
        from handlers.compare import handle_compare_with_amount
        parts = data.split("_")
        amount_mln = int(parts[2])
        context = parts[3]
        await handle_compare_with_amount(chat_id, amount_mln, context)

    elif data.startswith("compare_pdf_"):
        from handlers.compare import handle_compare_pdf
        parts = data.split("_")
        years = int(parts[2])
        amount = int(parts[3])
        await handle_compare_pdf(chat_id, years, amount, username)


    elif data == "booking_menu":
        from handlers.booking_fixation import handle_booking_menu
        await handle_booking_menu(chat_id, user_info.get("id", chat_id))

    elif data == "booking_auth":
        from handlers.booking_fixation import handle_booking_auth_start
        await handle_booking_auth_start(chat_id, from_user.get("id", chat_id))

    elif data == "booking_reauth":
        from handlers.booking_fixation import handle_booking_reauth
        await handle_booking_reauth(chat_id, from_user.get("id", chat_id))

    elif data == "booking_new":
        from handlers.booking_fixation import handle_booking_new
        await handle_booking_new(chat_id, from_user.get("id", chat_id))

    elif data == "booking_cancel":
        from handlers.booking_fixation import handle_booking_cancel
        await handle_booking_cancel(chat_id, from_user.get("id", chat_id))

    elif data == "booking_skip_comment":
        from handlers.booking_fixation import handle_booking_skip_comment
        await handle_booking_skip_comment(chat_id, from_user.get("id", chat_id))


# Кеш подборок domoplaner
domoplaner_cache = {}


async def handle_domoplaner_link(chat_id: int, url: str):
    """Обрабатывает ссылку на подборку domoplaner."""
    from services.domoplaner_parser import parse_domoplaner_set
    
    await send_message(chat_id, "⏳ Загружаю подборку...")
    
    flats = parse_domoplaner_set(url)
    
    if not flats:
        await send_message(chat_id, "❌ Не удалось загрузить подборку. Проверьте ссылку.")
        return
    
    domoplaner_cache[chat_id] = flats
    
    buttons = []
    for flat in flats:
        price_mln = flat["price"] / 1_000_000
        btn_text = f"{flat['code']} — {flat['area']} м² — {price_mln:.1f} млн"
        callback = f"domo_{flat['code']}"
        buttons.append([{"text": btn_text, "callback_data": callback}])
    
    buttons.append([{"text": f"📦 Создать {len(flats)} КП", "callback_data": "domo_all"}])
    buttons.append([{"text": "🔙 Отмена", "callback_data": "main_menu"}])
    
    text = f"📋 Подборка от менеджера\n\nНайдено {len(flats)} квартир.\nВыберите для генерации КП:"
    
    await send_message_inline(chat_id, text, buttons)


# ====== GPT INTENT HANDLER ======

async def handle_intent(chat_id: int, intent_result: Dict[str, Any], user_info: Dict[str, Any]):
    """
    Диспетчер намерений — направляет на нужный handler.
    v2.1.0: Добавлена поддержка building, floor, code для КП.
    """
    intent = intent_result.get("intent", "chat")
    params = intent_result.get("params", {})
    original_text = intent_result.get("original_text", "")
    
    print(f"[ROUTER] Intent: {intent}, Params: {params}")
    
    # === НАВИГАЦИЯ ===
    
    if intent == "start":
        await handle_start(chat_id, "/start", user_info)
        return
    
    if intent == "help":
        await handle_help(chat_id)
        return
    
    if intent == "myid":
        await handle_myid(chat_id, user_info)
        return
    
    if intent in ("back", "main_menu"):
        await handle_main_menu(chat_id)
        return
    
    if intent == "about_project":
        await handle_about_project(chat_id)
        return
    
    if intent == "calculations_menu":
        from handlers.kp import handle_nav_menu
        await handle_nav_menu(chat_id, mode="calc")
        return
    
    # === КП v2.1.0 - ОБНОВЛЁННАЯ ЛОГИКА ===
    
    if intent in ("kp_menu", "get_kp"):
        from handlers.kp import (
            handle_kp_menu, 
            handle_kp_smart_search,
            handle_kp_lot,
        )
        
        # Извлекаем параметры
        code = params.get("code")
        building = params.get("building")
        floor = params.get("floor")
        budget = params.get("budget")
        area = params.get("area")
        
        # Если есть любые параметры — используем умный поиск
        if code or building or floor or budget or area:
            await handle_kp_smart_search(
                chat_id, 
                code=code, 
                building=building, 
                floor=floor, 
                budget=budget, 
                area=area
            )
        else:
            # Без параметров — главное меню КП
            await handle_kp_menu(chat_id)
        return
    
    # === РАСЧЁТЫ ===
    
    if intent == "calculate_roi":
        area = params.get("area")
        unit_code = params.get("unit_code")
        
        if area:
            await handle_calc_roi_lot(chat_id, area)
        elif unit_code:
            await handle_base_roi(chat_id, unit_code=unit_code)
        else:
            await handle_calc_roi_menu(chat_id)
        return
    
    if intent == "show_installment":
        area = params.get("area")
        unit_code = params.get("unit_code")
        
        if area:
            await handle_calc_finance_lot(chat_id, area)
        elif unit_code:
            await handle_finance_overview(chat_id, unit_code=unit_code)
        else:
            await handle_calc_finance_menu(chat_id)
        return
    
    if intent in ("compare_deposit", "compare_menu"):
        from handlers.kp import handle_nav_menu
        await handle_nav_menu(chat_id, mode="compare")
        return
    
    # === ФИКСАЦИЯ И ШАХМАТКА ===
    
    if intent == "open_fixation":
        from handlers.booking_fixation import handle_booking_menu
        await handle_booking_menu(chat_id, user_info.get("id", chat_id))
        return
    
    if intent == "open_shahmatka":
        inline_buttons = [
            [{"text": "🏠 Открыть шахматку", "url": LINK_SHAHMATKA}],
            [{"text": "🔙 В меню", "callback_data": "back_to_menu"}]
        ]
        await send_message_inline(
            chat_id,
            "🏠 <b>Шахматка</b>\n\nАктуальная шахматка с доступными лотами:",
            inline_buttons
        )
        return
    
    # === ЗАПИСИ ===
    
    if intent == "book_showing":
        from handlers.booking_calendar import handle_booking_start
        await handle_booking_start(chat_id)
        return
    
    # === ДОКУМЕНТЫ И МЕДИА ===
    
    if intent == "documents_menu":
        from handlers.docs import handle_documents_menu
        await handle_documents_menu(chat_id)
        return
    
    if intent == "send_documents":
        from handlers.docs import handle_send_ddu, handle_send_arenda, handle_send_all_docs
        
        doc_type = params.get("doc_type", "all")
        if doc_type == "ddu":
            await handle_send_ddu(chat_id)
        elif doc_type == "arenda":
            await handle_send_arenda(chat_id)
        else:
            await handle_send_all_docs(chat_id)
        return
    
    if intent == "send_presentation":
        await handle_send_presentation(chat_id)
        return
    
    if intent == "show_media":
        await handle_media_menu(chat_id)
        return
    
    # === СЕКРЕТАРЬ ===
    
    if intent == "secretary_menu":
        await handle_secretary_menu(chat_id)
        return
    
    if intent == "create_task":
        from services.secretary_db import add_task, count_tasks_for_date
        from services.secretary_ai import analyze_workload
        from handlers.secretary import format_date_ru
        
        task_text = params.get("task", "Задача без описания")
        task_date = params.get("date")
        task_time = params.get("time")
        client_name = params.get("client_name")
        priority = params.get("priority", "normal")
        
        task_id = add_task(
            user_id=chat_id,
            task_text=task_text,
            due_date=task_date,
            due_time=task_time,
            client_name=client_name,
            priority=priority
        )
        
        warning = None
        if task_date:
            stats = count_tasks_for_date(chat_id, task_date)
            warning = analyze_workload(stats["total"], priority in ("urgent", "high"))
        
        date_str = format_date_ru(task_date) if task_date else "без даты"
        time_str = f" в {task_time}" if task_time else ""
        
        response = f"✅ <b>Задача создана!</b>\n\n"
        response += f"📌 {task_text}\n"
        response += f"📅 {date_str}{time_str}"
        
        if client_name:
            response += f"\n👤 {client_name}"
        
        if warning:
            response += f"\n\n{warning}"
        
        inline_buttons = [
            [{"text": "📋 Посмотреть", "callback_data": f"sec_task_{task_id}"}],
            [{"text": "📅 К расписанию", "callback_data": f"sec_day_{task_date or datetime.now().strftime('%Y-%m-%d')}"}],
        ]
        
        await send_message_inline(chat_id, response, inline_buttons)
        return
    
    if intent == "show_schedule":
        period = params.get("period", "today")
        
        if period == "week":
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            await handle_secretary_week(chat_id, monday.strftime("%Y-%m-%d"))
        elif period == "tomorrow":
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            await handle_secretary_day(chat_id, tomorrow)
        else:
            await handle_secretary_day(chat_id, datetime.now().strftime("%Y-%m-%d"))
        return
    
    # === НОВОСТИ ===
    
    if intent == "show_news":
        from handlers.news import (
            handle_news_menu, handle_currency_rates, 
            handle_weather, handle_flights, handle_news_digest
        )
        
        news_type = params.get("type")
        
        if news_type == "currency":
            await handle_currency_rates(chat_id)
        elif news_type == "weather":
            await handle_weather(chat_id)
        elif news_type == "flights":
            await handle_flights(chat_id)
        elif news_type == "digest":
            await handle_news_digest(chat_id)
        else:
            await handle_news_menu(chat_id)
        return
    
    # === FALLBACK: AI CHAT ===
    await handle_free_text(chat_id, original_text)


# ====== ГЛАВНЫЙ РОУТЕР СООБЩЕНИЙ (v2.1) ======

async def process_message(chat_id: int, text: str, user_info: Dict[str, Any]):
    """
    Новый роутер сообщений с GPT Intent Classification.
    Версия 2.1 — поддержка корпусов, этажей, кодов лотов.
    """
    
    # === Обработка диалоговых состояний (фиксация) ===
    from handlers.booking_fixation import handle_booking_input, has_active_booking_state
    if has_active_booking_state(user_info.get("id", chat_id)):
        user_id = user_info.get("id", chat_id)
        handled = await handle_booking_input(chat_id, user_id, text)
        if handled:
            return
    
    # === Обработка других активных состояний ===
    state = get_dialog_state(chat_id)
    
    if state == DialogStates.CHOOSE_UNIT_ASK_BUDGET:
        await handle_budget_input(chat_id, text)
        return
    
    if state == DialogStates.CHOOSE_UNIT_ASK_FORMAT:
        await handle_format_input(chat_id, text)
        return
    
    if state == DialogStates.ASK_CONTACT_FOR_CALLBACK:
        if text == "✍️ Ввести вручную":
            await send_message(chat_id, "Напишите ваш телефон или @username:")
            return
        await handle_quick_contact(chat_id, text)
        return
    
    if is_in_booking_flow(chat_id):
        await handle_booking_step(chat_id, text)
        return
    
    if state == DialogStates.AWAIT_KP_REQUEST:
        await handle_kp_request(chat_id, text)
        return
    
    # === Ссылки domoplaner ===
    from services.domoplaner_parser import is_domoplaner_link
    domo_url = is_domoplaner_link(text)
    if domo_url:
        await handle_domoplaner_link(chat_id, domo_url)
        return
    
    # === GPT INTENT CLASSIFICATION ===
    intent_result = classify_intent(text)
    intent_result["original_text"] = text
    
    # Сбрасываем состояние при уверенной классификации
    if intent_result.get("confidence", 0) > 0.7:
        clear_dialog_state(chat_id)
    
    # Направляем на handler
    await handle_intent(chat_id, intent_result, user_info)


async def process_voice_message(chat_id: int, voice: Dict[str, Any], user_info: Dict[str, Any]):
    """
    Обработка голосового сообщения через GPT-роутинг.
    """
    from services.telegram import download_file
    from services.speech import transcribe_voice
    
    file_id = voice.get("file_id")
    if not file_id:
        return
    
    await send_message(chat_id, "🎤 Распознаю голосовое сообщение...")
    
    save_path = f"/tmp/voice_{chat_id}_{file_id}.ogg"
    downloaded = await download_file(file_id, save_path)
    
    if not downloaded:
        await send_message(chat_id, "❌ Не удалось обработать голосовое сообщение. Попробуйте ещё раз.")
        return
    
    text = transcribe_voice(save_path)
    
    if not text:
        await send_message(chat_id, "❌ Не удалось распознать речь. Попробуйте ещё раз или напишите текстом.")
        return
    
    await send_message(chat_id, f"📝 Распознано: <i>{text}</i>")
    
    # Обрабатываем через GPT-роутер
    await process_message(chat_id, text, user_info)


# ====== Запуск ======

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
