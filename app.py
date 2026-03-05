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
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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
from services.monitoring import log_request, monitoring_loop
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
    handle_timezone_menu,
    handle_set_timezone,
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

# CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздаём Mini App
app.mount("/app", StaticFiles(directory="/opt/miniapp/dist", html=True), name="miniapp")


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
    asyncio.create_task(monitoring_loop())
    print("[PROD] Фоновые задачи запущены")


# ====== Health check ======

@app.get("/")
async def health():
    """Health check."""
    return {"ok": True, "bot": "RIZALTA", "version": "2.4.0"}



# ====== API для Mini App ======

@app.get("/api/lots")
async def api_get_lots(building: int = None, floor: int = None, status: str = None):
    """API для Mini App — список лотов."""
    import sqlite3
    
    conn = sqlite3.connect("/opt/bot/properties.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT code, building, floor, area_m2, price_rub, COALESCE(status, 'available') as status, layout_url FROM units WHERE 1=1"
    params = []
    
    # Фильтр скрытых корпусов
    import json
    try:
        with open("/opt/bot/data/hidden_buildings.json") as f:
            hidden = json.load(f).get("hidden", [])
        if hidden:
            placeholders = ",".join("?" * len(hidden))
            query += f" AND building NOT IN ({placeholders})"
            params.extend(hidden)
    except:
        pass

    if building:
        query += " AND building = ?"
        params.append(building)
    if floor:
        query += " AND floor = ?"
        params.append(floor)
    if status:
        query += " AND COALESCE(status, 'available') = ?"
        params.append(status)
    
    query += " ORDER BY building, floor DESC, code"
    cursor.execute(query, params)
    
    lots = [{
        "code": r["code"],
        "building": r["building"],
        "buildingName": "Family" if r["building"] == 1 else "Business",
        "floor": r["floor"],
        "area": float(r["area_m2"]) if r["area_m2"] else 0,
        "price": int(r["price_rub"]) if r["price_rub"] else 0,
        "status": r["status"] or "available",
        "layout_url": r["layout_url"] or "",
    } for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "ok": True,
        "lots": lots,
        "stats": {
            "total": len(lots),
            "available": len([l for l in lots if l["status"] == "available"]),
            "booked": len([l for l in lots if l["status"] == "booked"]),
            "sold": len([l for l in lots if l["status"] == "sold"]),
        }
    }



@app.post("/api/miniapp-action")
async def api_miniapp_action(request: Request):
    """API для Mini App — передаёт выбранный лот в бота."""
    try:
        data = await request.json()
    except:
        return {"ok": False, "error": "Invalid JSON"}
    
    lot = data.get("lot", {})
    user_id = data.get("user_id")
    
    if not lot.get("code"):
        return {"ok": False, "error": "Missing lot code"}
    
    if not user_id:
        return {"ok": False, "error": "Missing user_id"}
    
    code = lot.get("code")
    building = lot.get("building")
    
    print(f"[MINIAPP] Lot: {code}, Building: {building}, User: {user_id}")
    
    try:
        from handlers.kp import handle_nav_lot
        await handle_nav_lot(user_id, code, building, mode="kp")
        return {"ok": True}
    
    except Exception as e:
        print(f"[MINIAPP] Error: {e}")
        return {"ok": False, "error": str(e)}

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
    
    # Игнорируем сообщения из групповых чатов (бот отвечает только в личных)
    chat_type = msg["chat"].get("type", "private")
    if chat_type != "private":
        return {"ok": True}
    
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
    
    # Обработка документа (Excel актуализация К3, только админ)
    document = msg.get("document")
    if document and chat_id in [512319063, 8000703751]:
        file_name = document.get("file_name", "")
        if file_name.endswith((".xlsx", ".xls")):
            await handle_corp3_excel_update(chat_id, document)
            return {"ok": True}
    
    if not text:
        return {"ok": True}
    
    user_info = msg.get("from", {})
    
    import time as _t
    _start = _t.time()
    await process_message(chat_id, text, user_info)
    duration = int((_t.time() - _start) * 1000)
    print(f"[TIMING] Response time: {duration} ms")
    log_request(chat_id, "message", duration)
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

    # ===== Корпус 3 (whitelist) =====
    if data.startswith("c3_"):
        from handlers.corp3 import handle_corp3_callback
        await handle_corp3_callback(chat_id, data)
        return
    
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
    
    elif data.startswith("roi_xlsx_code_"):
        parts = data.replace("roi_xlsx_code_", "").rsplit("_", 1)
        code, building = parts[0], int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        from services.units_db import get_lot_by_code
        lot = get_lot_by_code(code, building)
        if lot:
            await send_message(chat_id, f"⏳ Создаю Excel для {lot['code']}...")
            from services.calc_xlsx_generator import generate_roi_xlsx
            xlsx_path = generate_roi_xlsx(unit_code=lot['code'], building=lot['building'])
            if xlsx_path:
                await send_document(chat_id, xlsx_path, f"ROI_{lot['code']}.xlsx")
            else:
                await send_message(chat_id, f"❌ Ошибка создания Excel")
        else:
            await send_message(chat_id, f"❌ Лот {code} не найден")

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
    
    elif data == "sec_timezone":
        await handle_timezone_menu(chat_id)
    
    elif data.startswith("sec_set_tz_"):
        tz = int(data.replace("sec_set_tz_", ""))
        await handle_set_timezone(chat_id, tz)
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
        parts = data.replace("kp_lot_", "").split("_")
        code = parts[0]
        building = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        from handlers.kp import handle_kp_lot
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
        offset = int(parts[2]) if len(parts) > 2 else 0
        await handle_kp_show_all_area(chat_id, min_area, max_area, offset)
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

    elif data.startswith("calc_roi_code_"):
        parts = data.replace("calc_roi_code_", "").rsplit("_", 1)
        code, building = parts[0], int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        from handlers.calc_dynamic import handle_calc_roi_by_code
        await handle_calc_roi_by_code(chat_id, code, building)

    elif data.startswith("mgp_pdf_"):
        # mgp_pdf_{code}_{building}_{area10}
        parts = data.replace("mgp_pdf_", "").rsplit("_", 2)
        code, building, area10 = parts[0], int(parts[1]), int(parts[2])
        area = area10 / 10.0
        from handlers.mgp import handle_mgp_pdf
        await handle_mgp_pdf(chat_id, code, area, building if building > 0 else None)

    elif data.startswith("mgp_calc_"):
        # mgp_calc_{code}_{building}_{area10}
        parts = data.replace("mgp_calc_", "").rsplit("_", 2)
        code, building, area10 = parts[0], int(parts[1]), int(parts[2])
        area = area10 / 10.0
        from handlers.mgp import handle_mgp_calc
        await handle_mgp_calc(chat_id, code, area, building if building > 0 else None)

    elif data.startswith("calc_finance_code_"):
        parts = data.replace("calc_finance_code_", "").rsplit("_", 1)
        code, building = parts[0], int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        from handlers.calc_dynamic import handle_calc_finance_by_code
        await handle_calc_finance_by_code(chat_id, code, building)

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


    elif data.startswith("book_date_"):
        from handlers.booking_calendar import handle_select_date
        date_str = data.replace("book_date_", "")
        await handle_select_date(chat_id, date_str)

    elif data == "book_tz_moscow":
        from handlers.booking_calendar import handle_select_timezone
        await handle_select_timezone(chat_id, "moscow")

    elif data == "book_tz_altai":
        from handlers.booking_calendar import handle_select_timezone
        await handle_select_timezone(chat_id, "altai")

    elif data == "book_time_confirmed":
        from handlers.booking_calendar import handle_time_confirmed
        await handle_time_confirmed(chat_id, from_user)

    elif data.startswith("book_time_"):
        from handlers.booking_calendar import handle_select_time
        time_str = data.replace("book_time_", "")
        await handle_select_time(chat_id, time_str, username)

    elif data.startswith("book_take_"):
        from handlers.booking_calendar import handle_take_booking
        booking_id = int(data.replace("book_take_", ""))
        await handle_take_booking(chat_id, booking_id, from_user)

    elif data == "book_change_tz":
        from handlers.booking_calendar import handle_change_timezone
        await handle_change_timezone(chat_id)

    elif data.startswith("book_set_tz_"):
        from handlers.booking_calendar import handle_set_timezone
        tz = data.replace("book_set_tz_", "")
        await handle_set_timezone(chat_id, tz)

    elif data == "book_add_phone":
        from handlers.booking_calendar import handle_request_phone
        await handle_request_phone(chat_id)

    elif data == "book_submit":
        from handlers.booking_calendar import handle_submit_booking
        await handle_submit_booking(chat_id, from_user)

    elif data == "book_edit_menu":
        from handlers.booking_calendar import handle_edit_menu
        await handle_edit_menu(chat_id)

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

    # === MORTGAGE (Ипотека) ===
    elif data.startswith("mort_pdf_"):
        # mort_pdf_{code}_{building}_{dp}_{tariff}_{term}
        from handlers.mortgage import handle_mortgage_pdf
        parts = data.replace("mort_pdf_", "").split("_")
        code = parts[0]
        building = int(parts[1])
        dp = int(parts[2])
        tariff = parts[3]
        term = int(parts[4])
        await handle_mortgage_pdf(chat_id, code, building, dp, tariff, term)

    elif data.startswith("mortgage_"):
        # mortgage_{code}_{building} - начальный вызов
        from handlers.mortgage import handle_mortgage_menu
        parts = data.replace("mortgage_", "").split("_")
        code = parts[0]
        building = int(parts[1])
        await handle_mortgage_menu(chat_id, code, building)

    elif data.startswith("mort_"):
        # mort_{code}_{building}_{dp}_{tariff}_{term} - смена параметров
        from handlers.mortgage import handle_mortgage_menu
        parts = data.replace("mort_", "").split("_")
        code = parts[0]
        building = int(parts[1])
        dp = int(parts[2])
        tariff = parts[3]
        term = int(parts[4])
        await handle_mortgage_menu(chat_id, code, building, dp, tariff, term)

    # === TRANCHE MORTGAGE (Траншевая ипотека) ===
    elif data.startswith("tmort_pdf_"):
        # tmort_pdf_{code}_{building}
        from handlers.tranche_mortgage import handle_tranche_mortgage_pdf
        parts = data.replace("tmort_pdf_", "").split("_")
        code = parts[0]
        building = int(parts[1])
        await handle_tranche_mortgage_pdf(chat_id, code, building)

    elif data.startswith("tmort_"):
        # tmort_{code}_{building}
        from handlers.tranche_mortgage import handle_tranche_mortgage_menu
        parts = data.replace("tmort_", "").split("_")
        code = parts[0]
        building = int(parts[1])
        await handle_tranche_mortgage_menu(chat_id, code, building)

    elif data.startswith("compare_lot_back_"):
        from handlers.compare import handle_compare_lot
        parts = data.split("_")
        amount = int(parts[3])
        area_m2 = int(parts[4]) / 10 if len(parts) > 4 else 26.8
        await handle_compare_lot(chat_id, "выбранный", amount, area_m2)

    elif data.startswith("compare_lot_"):
        from handlers.compare import handle_compare_lot
        parts = data.split("_")
        lot_code = parts[2]
        building = int(parts[3])
        price = int(parts[4]) * 1000 if len(parts) > 4 else int(parts[3]) * 1000
        area_m2 = int(parts[5]) / 10 if len(parts) > 5 else 26.8
        await handle_compare_lot(chat_id, lot_code, price, area_m2)

    elif data.startswith("compare_table_"):
        from handlers.compare import handle_compare_table
        parts = data.split("_")
        amount = int(parts[2])
        area_m2 = int(parts[3]) / 10 if len(parts) > 3 else 26.8
        await handle_compare_table(chat_id, amount, area_m2)

    elif data == "compare_table":
        from handlers.compare import handle_compare_table
        await handle_compare_table(chat_id)

    elif data.startswith("compare_period_"):
        from handlers.compare import handle_compare_period
        parts = data.split("_")
        years = int(parts[2])
        amount = int(parts[3]) if len(parts) > 3 else 15_000_000
        area_m2 = int(parts[4]) / 10 if len(parts) > 4 else 26.8
        await handle_compare_period(chat_id, years, amount, area_m2)

    elif data.startswith("compare_full_"):
        from handlers.compare import handle_compare_full
        parts = data.split("_")
        years = int(parts[2])
        amount = int(parts[3]) if len(parts) > 3 else 15_000_000
        area_m2 = int(parts[4]) / 10 if len(parts) > 4 else 26.8
        await handle_compare_full(chat_id, years, amount, area_m2)

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
        area_m2 = int(parts[4]) / 10 if len(parts) > 4 else 26.8
        await handle_compare_pdf(chat_id, years, amount, username, area_m2)


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

    if intent == "open_lots_app":
        inline_buttons = [
            [{"text": "🏢 Открыть выбор лотов", "web_app": {"url": "https://rizalta-miniapp.vercel.app"}}],
            [{"text": "🔙 В меню", "callback_data": "back_to_menu"}]
        ]
        await send_message_inline(
            chat_id,
            "🏢 <b>Выбор лота</b>\n\nИнтерактивная шахматка с фильтрами:",
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
    await handle_free_text(chat_id, original_text, user_info)


# ====== ГЛАВНЫЙ РОУТЕР СООБЩЕНИЙ (v2.1) ======



async def handle_corp3_excel_update(chat_id: int, document: dict):
    """Обновление статусов К3 из Excel файла."""
    import json
    import openpyxl
    import io
    from services.telegram import download_file, send_message

    file_id = document.get("file_id")
    file_name = document.get("file_name", "unknown.xlsx")
    
    await send_message(chat_id, f"📥 Получен файл: {file_name}\n⏳ Обрабатываю...")
    
    try:
        # Скачиваем файл
        save_path = f"/tmp/corp3_update_{chat_id}.xlsx"
        result = await download_file(file_id, save_path)
        if not result:
            await send_message(chat_id, "❌ Не удалось скачать файл")
            return
        
        # Читаем Excel — все коды лотов = sold
        wb = openpyxl.load_workbook(save_path)
        ws = wb.active
        
        excel_codes = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            code = row[6]  # Колонка G — Номер
            if code and isinstance(code, str):
                excel_codes.add(code.strip())
        
        if not excel_codes:
            await send_message(chat_id, "❌ Не найдены коды лотов в колонке G")
            return
        
        # Обновляем оба окружения
        report_lines = [f"📊 <b>Актуализация К3</b>\n"]
        report_lines.append(f"📁 Файл: {file_name}")
        report_lines.append(f"📋 Лотов в Excel: {len(excel_codes)}\n")
        
        for env, path in [("PROD", "data/corp3_units.json"), ("DEV", "/opt/bot-dev/data/corp3_units.json")]:
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                to_sold = []
                to_available = []
                
                for unit in data['units']:
                    code = unit['code']
                    old_status = unit.get('status', 'available')
                    
                    if code in excel_codes and old_status != 'sold':
                        unit['status'] = 'sold'
                        to_sold.append(code)
                    elif code not in excel_codes and old_status != 'available':
                        unit['status'] = 'available'
                        to_available.append(code)
                
                with open(path, 'w') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                sold_total = sum(1 for u in data['units'] if u.get('status') == 'sold')
                avail_total = sum(1 for u in data['units'] if u.get('status') == 'available')
                
                report_lines.append(f"<b>{env}:</b> sold={sold_total}, available={avail_total}")
            except Exception as e:
                report_lines.append(f"<b>{env}:</b> ❌ ошибка: {e}")
        
        if to_sold:
            report_lines.append(f"\n🔴 Проданы ({len(to_sold)}): {', '.join(sorted(to_sold))}")
        if to_available:
            report_lines.append(f"\n🟢 Освободились ({len(to_available)}): {', '.join(sorted(to_available))}")
        if not to_sold and not to_available:
            report_lines.append(f"\n✅ Изменений нет — всё актуально")
        
        await send_message(chat_id, "\n".join(report_lines))
        
        # Удаляем временный файл
        import os
        os.remove(save_path)
        
    except Exception as e:
        await send_message(chat_id, f"❌ Ошибка обработки: {e}")


async def handle_whitelist_command(chat_id: int, text: str):
    """Управление whitelist Корпуса 3: /wl list | add | remove"""
    import sqlite3
    db_path = "properties.db"
    parts = text.strip().split(maxsplit=2)
    cmd = parts[1] if len(parts) > 1 else "help"
    
    if cmd == "list":
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, name, added_at FROM corp3_whitelist ORDER BY added_at")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            await send_message(chat_id, "📋 Whitelist пуст.")
            return
        lines = ["📋 <b>Whitelist Корпуса 3:</b>", ""]
        for i, (cid, name, added) in enumerate(rows, 1):
            lines.append(f"{i}. <code>{cid}</code> — {name or "без имени"}")
        lines.append(f"\n<i>Всего: {len(rows)}</i>")
        await send_message(chat_id, "\n".join(lines))
    
    elif cmd == "add" and len(parts) >= 2:
        try:
            add_parts = parts[2].split(maxsplit=1) if len(parts) > 2 else []
            new_id = int(add_parts[0])
            name = add_parts[1] if len(add_parts) > 1 else None
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO corp3_whitelist (chat_id, name) VALUES (?, ?)", (new_id, name))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            if affected:
                await send_message(chat_id, f"✅ Добавлен: <code>{new_id}</code> — {name or "без имени"}")
            else:
                await send_message(chat_id, f"⚠️ <code>{new_id}</code> уже в whitelist.")
        except (ValueError, IndexError):
            await send_message(chat_id, "❌ Формат: /wl add 123456789 Имя")
    
    elif cmd == "remove" and len(parts) >= 3:
        try:
            del_id = int(parts[2])
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM corp3_whitelist WHERE chat_id = ?", (del_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            if affected:
                await send_message(chat_id, f"✅ Удалён: <code>{del_id}</code>")
            else:
                await send_message(chat_id, f"⚠️ <code>{del_id}</code> не найден в whitelist.")
        except ValueError:
            await send_message(chat_id, "❌ Формат: /wl remove 123456789")
    
    else:
        await send_message(chat_id, """📋 <b>Команды whitelist:</b>

/wl list — показать всех
/wl add 123456789 Имя — добавить
/wl remove 123456789 — удалить""")


async def handle_corp3_admin_command(chat_id: int, text: str):
    """Управление лотами Корпуса 3: /ca list | hide | show"""
    import json
    json_path = "data/corp3_units.json"
    parts = text.strip().split(maxsplit=2)
    cmd = parts[1] if len(parts) > 1 else "help"
    
    # Загружаем данные
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if cmd == "list":
        sold = [u['code'] for u in data['units'] if u.get('status') == 'sold']
        if not sold:
            await send_message(chat_id, "📋 Все лоты Корпуса 3 доступны (нет скрытых).")
            return
        sold_sorted = sorted(sold)
        lines = ["📋 <b>Скрытые лоты Корпуса 3:</b>", ""]
        lines.append(", ".join(sold_sorted[:50]))
        if len(sold_sorted) > 50:
            lines.append(f"... и ещё {len(sold_sorted) - 50}")
        lines.append(f"\n<i>Всего скрыто: {len(sold)}</i>")
        await send_message(chat_id, "\n".join(lines))
    
    elif cmd == "hide" and len(parts) >= 3:
        code = parts[2].strip().upper().replace('A', 'А').replace('B', 'В')
        found = False
        for unit in data['units']:
            if unit['code'].upper() == code:
                if unit.get('status') == 'sold':
                    await send_message(chat_id, f"⚠️ Лот <code>{code}</code> уже скрыт.")
                    return
                unit['status'] = 'sold'
                found = True
                break
        if found:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            from handlers.corp3 import _units_cache
            _units_cache.clear()
            await send_message(chat_id, f"✅ Лот <code>{code}</code> скрыт (sold).")
        else:
            await send_message(chat_id, f"❌ Лот <code>{code}</code> не найден в Корпусе 3.")
    
    elif cmd == "show" and len(parts) >= 3:
        code = parts[2].strip().upper().replace('A', 'А').replace('B', 'В')
        found = False
        for unit in data['units']:
            if unit['code'].upper() == code:
                if unit.get('status') == 'available':
                    await send_message(chat_id, f"⚠️ Лот <code>{code}</code> уже доступен.")
                    return
                unit['status'] = 'available'
                found = True
                break
        if found:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            from handlers.corp3 import _units_cache
            _units_cache.clear()
            await send_message(chat_id, f"✅ Лот <code>{code}</code> открыт (available).")
        else:
            await send_message(chat_id, f"❌ Лот <code>{code}</code> не найден в Корпусе 3.")
    
    else:
        await send_message(chat_id, """📋 <b>Управление лотами Корпуса 3:</b>\n\n/ca list — показать скрытые лоты\n/ca hide А300 — скрыть лот\n/ca show А300 — показать лот""")


async def process_message(chat_id: int, text: str, user_info: Dict[str, Any]):
    """
    Новый роутер сообщений с GPT Intent Classification.
    Версия 2.1 — поддержка корпусов, этажей, кодов лотов.
    """
    
    # === Проверка состояния бронирования ===
    from handlers.booking_calendar import handle_booking_text_input
    if await handle_booking_text_input(chat_id, text, user_info):
        return
    
    # === Проверка состояния поиска по коду в Корпусе 3 ===
    from handlers.corp3 import handle_corp3_text
    if await handle_corp3_text(chat_id, text):
        return
    
    # === Админ-команда /parse ===
    ADMIN_IDS = [512319063, 8000703751]

    # === Админ-команда /stats ===
    if text == "/stats" and chat_id in ADMIN_IDS:
        import subprocess
        try:
            result = subprocess.run(
                ["/bin/bash", "/opt/bot/stats.sh"],
                capture_output=True, text=True, timeout=30
            )
            await send_message(chat_id, f"<pre>{result.stdout}</pre>")
        except Exception as e:
            await send_message(chat_id, f"❌ Ошибка: {e}")
        return

    # === Команда /corp3 (whitelist) ===
    if text == "/corp3":
        from handlers.corp3 import handle_corp3_start
        await handle_corp3_start(chat_id)
        return
    # === Команда /wl (whitelist управление, только админ) ===
    if text.startswith("/wl") and chat_id in ADMIN_IDS:
        await handle_whitelist_command(chat_id, text)
        return
    # === Команда /ca (управление лотами Корпуса 3, только админ) ===
    if text.startswith("/ca") and chat_id in ADMIN_IDS:
        await handle_corp3_admin_command(chat_id, text)
        return
    if text == "/parse" and chat_id in ADMIN_IDS:
        import subprocess
        await send_message(chat_id, "⏳ Запускаю парсер...")
        try:
            result = subprocess.run(
                ["/opt/bot/venv/bin/python3", "services/parser_rclick.py"],
                cwd="/opt/bot",
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                await send_message(chat_id, f"✅ Парсер завершён успешно:\n<pre>{result.stdout[-1000:] if result.stdout else 'OK'}</pre>")
            else:
                await send_message(chat_id, f"❌ Ошибка парсера:\n<pre>{result.stderr[-500:]}</pre>")
        except subprocess.TimeoutExpired:
            await send_message(chat_id, "❌ Таймаут парсера (>120 сек)")
        except Exception as e:
            await send_message(chat_id, f"❌ Ошибка: {e}")
        return
    
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
