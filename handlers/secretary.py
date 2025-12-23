"""
AI-Секретарь — личный ежедневник с голосовым вводом.
Версия 2.0 — без режима секретаря (GPT-роутинг делает это ненужным)
"""

from datetime import datetime, timedelta
from services.telegram import send_message, send_message_inline
from services.secretary_db import (
    add_task, get_tasks_for_date, get_tasks_for_week, get_task_by_id,
    update_task_status, update_task_date, delete_task, count_tasks_for_date
)
from services.secretary_ai import analyze_workload


WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def format_date_ru(date_str):
    """Форматирует дату: 5 января (Пн)"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.day} {MONTHS[dt.month]} ({WEEKDAYS[dt.weekday()]})"


def get_status_icon(task):
    """Иконка статуса задачи."""
    if task["status"] == "done":
        return "✅"
    elif task["priority"] in ("urgent", "high"):
        return "🔴"
    elif task.get("due_time"):
        return "⏰"
    return "📌"


async def handle_secretary_menu(chat_id: int):
    """Главное меню секретаря."""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    monday_current = today - timedelta(days=today.weekday())
    monday_next = monday_current + timedelta(days=7)
    
    stats = count_tasks_for_date(chat_id, today_str)
    
    # НЕ включаем режим секретаря — GPT-роутинг сам разберётся
    
    text = f"""🗓 <b>AI-Секретарь</b>

Сегодня: <b>{format_date_ru(today_str)}</b>
Задач на сегодня: <b>{stats['total']}</b>""" + (f" (🔴 {stats['urgent']} срочных)" if stats['urgent'] else "") + f"""
Выполнено: <b>{stats['done']}</b>

💡 Просто скажите или напишите задачу:
<i>«Завтра позвонить Иванову в 15:00»</i>

🎤 Голосовые сообщения работают из любого места!"""

    inline_buttons = [
        [{"text": "📅 Сегодня", "callback_data": f"sec_day_{today_str}"},
         {"text": "📅 Завтра", "callback_data": f"sec_day_{tomorrow_str}"}],
        [{"text": "📆 Текущая неделя", "callback_data": f"sec_week_{monday_current.strftime('%Y-%m-%d')}"}],
        [{"text": "📆 Следующая неделя", "callback_data": f"sec_week_{monday_next.strftime('%Y-%m-%d')}"}],
        [{"text": "➕ Добавить задачу", "callback_data": "sec_add"}],
        [{"text": "🔙 Главное меню", "callback_data": "back_to_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_secretary_day(chat_id: int, date_str: str):
    """Показывает задачи на день."""
    tasks = get_tasks_for_date(chat_id, date_str)
    
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    if date_str == today:
        day_label = "Сегодня"
    elif date_str == tomorrow:
        day_label = "Завтра"
    else:
        day_label = format_date_ru(date_str)
    
    if not tasks:
        text = f"📅 <b>{day_label}</b>\n\nЗадач нет 🎉\n\n<i>Добавить — просто скажите или напишите</i>"
    else:
        done = sum(1 for t in tasks if t["status"] == "done")
        urgent = sum(1 for t in tasks if t["priority"] in ("urgent", "high") and t["status"] != "done")
        
        lines = [f"📅 <b>{day_label}</b>", ""]
        
        for t in tasks:
            icon = get_status_icon(t)
            time_str = f"{t['due_time']} — " if t.get("due_time") else ""
            strike = "<s>" if t["status"] == "done" else ""
            strike_end = "</s>" if t["status"] == "done" else ""
            lines.append(f"{icon} {time_str}{strike}{t['task_text']}{strike_end}")
        
        lines.append("")
        lines.append(f"Выполнено: {done} из {len(tasks)}" + (f" • 🔴 {urgent} срочных" if urgent else ""))
        text = "\n".join(lines)
    
    prev_date = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    inline_buttons = []
    
    for t in tasks[:5]:
        btn_text = get_status_icon(t) + " " + (t["task_text"][:25] + "..." if len(t["task_text"]) > 25 else t["task_text"])
        inline_buttons.append([{"text": btn_text, "callback_data": f"sec_task_{t['id']}"}])
    
    if len(tasks) > 5:
        inline_buttons.append([{"text": f"... ещё {len(tasks) - 5} задач", "callback_data": "noop"}])
    
    inline_buttons.append([
        {"text": "◀️", "callback_data": f"sec_day_{prev_date}"},
        {"text": "📆 Неделя", "callback_data": f"sec_week_{date_str}"},
        {"text": "▶️", "callback_data": f"sec_day_{next_date}"}
    ])
    inline_buttons.append([
        {"text": "➕ Добавить", "callback_data": f"sec_add_{date_str}"},
        {"text": "🔙 Меню", "callback_data": "secretary_menu"}
    ])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_secretary_week(chat_id: int, start_date: str):
    """Показывает неделю."""
    dt = datetime.strptime(start_date, "%Y-%m-%d")
    monday = dt - timedelta(days=dt.weekday())
    
    week_tasks = get_tasks_for_week(chat_id, monday.strftime("%Y-%m-%d"))
    
    total = sum(len(tasks) for tasks in week_tasks.values())
    
    sunday = monday + timedelta(days=6)
    week_label = f"{monday.day} {MONTHS[monday.month]} — {sunday.day} {MONTHS[sunday.month]}"
    
    lines = [f"📆 <b>Неделя: {week_label}</b>", "", f"Всего задач: <b>{total}</b>", ""]
    
    inline_buttons = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for i in range(7):
        day_dt = monday + timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        day_tasks = week_tasks.get(day_str, [])
        
        day_name = WEEKDAYS[i]
        day_num = day_dt.day
        
        urgent = sum(1 for t in day_tasks if t["priority"] in ("urgent", "high"))
        
        if day_str == today:
            day_label = f"▶️ {day_name} {day_num}"
        else:
            day_label = f"{day_name} {day_num}"
        
        if day_tasks:
            count_text = f"{len(day_tasks)} задач" + (" 🔴" if urgent else "")
            btn_text = f"{day_label} — {count_text}"
        else:
            btn_text = f"{day_label} — "
        
        inline_buttons.append([{"text": btn_text, "callback_data": f"sec_day_{day_str}"}])
    
    prev_week = (monday - timedelta(days=7)).strftime("%Y-%m-%d")
    next_week = (monday + timedelta(days=7)).strftime("%Y-%m-%d")
    
    inline_buttons.append([
        {"text": "◀️ Пред.", "callback_data": f"sec_week_{prev_week}"},
        {"text": "След. ▶️", "callback_data": f"sec_week_{next_week}"}
    ])
    inline_buttons.append([{"text": "🔙 Меню секретаря", "callback_data": "secretary_menu"}])
    
    text = "\n".join(lines)
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_secretary_task_detail(chat_id: int, task_id: int):
    """Показывает детали задачи."""
    task = get_task_by_id(task_id)
    
    if not task:
        await send_message(chat_id, "❌ Задача не найдена")
        return
    
    icon = get_status_icon(task)
    status_text = "✅ Выполнено" if task["status"] == "done" else "⏳ В работе"
    priority_text = {"urgent": "🔴 Критично", "high": "🔴 Срочно", "normal": "📌 Обычный", "low": "📎 Низкий"}.get(task["priority"], "📌")
    
    date_text = format_date_ru(task["due_date"]) if task.get("due_date") else "Без даты"
    time_text = task.get("due_time") or "Без времени"
    
    lines = [
        f"{icon} <b>{task['task_text']}</b>",
        "",
        f"📅 {date_text}, {time_text}",
        f"{priority_text}",
        f"{status_text}",
    ]
    
    if task.get("client_name"):
        lines.append(f"👤 Клиент: {task['client_name']}")
    
    if task.get("description"):
        lines.append("")
        lines.append(f"📝 {task['description']}")
    
    text = "\n".join(lines)
    
    inline_buttons = []
    
    if task["status"] != "done":
        inline_buttons.append([{"text": "✅ Выполнено", "callback_data": f"sec_done_{task_id}"}])
    else:
        inline_buttons.append([{"text": "🔄 Вернуть в работу", "callback_data": f"sec_undone_{task_id}"}])
    
    inline_buttons.append([
        {"text": "📅 Перенести", "callback_data": f"sec_move_{task_id}"},
        {"text": "🗑 Удалить", "callback_data": f"sec_del_{task_id}"}
    ])
    
    back_date = task.get("due_date") or datetime.now().strftime("%Y-%m-%d")
    inline_buttons.append([{"text": "◀️ Назад к дню", "callback_data": f"sec_day_{back_date}"}])
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_secretary_done(chat_id: int, task_id: int):
    """Отмечает задачу выполненной."""
    update_task_status(task_id, "done")
    await send_message(chat_id, "✅ Задача выполнена!")
    await handle_secretary_task_detail(chat_id, task_id)


async def handle_secretary_undone(chat_id: int, task_id: int):
    """Возвращает задачу в работу."""
    update_task_status(task_id, "pending")
    await send_message(chat_id, "🔄 Задача возвращена в работу")
    await handle_secretary_task_detail(chat_id, task_id)


async def handle_secretary_delete(chat_id: int, task_id: int):
    """Удаляет задачу."""
    task = get_task_by_id(task_id)
    back_date = task.get("due_date") if task else datetime.now().strftime("%Y-%m-%d")
    
    delete_task(task_id)
    await send_message(chat_id, "🗑 Задача удалена")
    await handle_secretary_day(chat_id, back_date)


async def handle_secretary_move_menu(chat_id: int, task_id: int):
    """Меню переноса задачи."""
    task = get_task_by_id(task_id)
    if not task:
        await send_message(chat_id, "❌ Задача не найдена")
        return
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    next_week = today + timedelta(days=7)
    
    text = f"📅 Перенести: <b>{task['task_text']}</b>\n\nВыберите новую дату:"
    
    inline_buttons = [
        [{"text": f"Завтра ({tomorrow.day} {MONTHS[tomorrow.month]})", 
          "callback_data": f"sec_moveto_{task_id}_{tomorrow.strftime('%Y-%m-%d')}"}],
        [{"text": f"Послезавтра ({day_after.day} {MONTHS[day_after.month]})", 
          "callback_data": f"sec_moveto_{task_id}_{day_after.strftime('%Y-%m-%d')}"}],
        [{"text": f"Через неделю ({next_week.day} {MONTHS[next_week.month]})", 
          "callback_data": f"sec_moveto_{task_id}_{next_week.strftime('%Y-%m-%d')}"}],
        [{"text": "❌ Отмена", "callback_data": f"sec_task_{task_id}"}]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_secretary_move_to(chat_id: int, task_id: int, new_date: str):
    """Переносит задачу на новую дату."""
    update_task_date(task_id, new_date)
    await send_message(chat_id, f"📅 Задача перенесена на {format_date_ru(new_date)}")
    await handle_secretary_task_detail(chat_id, task_id)


async def handle_secretary_add_prompt(chat_id: int, preset_date: str = None):
    """Промпт для добавления задачи."""
    text = "➕ <b>Новая задача</b>\n\n"
    
    if preset_date:
        text += f"📅 Дата: {format_date_ru(preset_date)}\n\n"
    
    text += "Просто напишите или скажите голосом:\n"
    text += "<i>«Позвонить Иванову в 15:00»</i>\n"
    text += "<i>«Срочно отправить КП клиенту»</i>\n\n"
    text += "🎤 Голос работает из любого места бота!"
    
    inline_buttons = [[{"text": "❌ Отмена", "callback_data": "secretary_menu"}]]
    await send_message_inline(chat_id, text, inline_buttons)


# DEPRECATED: process_secretary_input больше не нужен
# GPT-роутинг обрабатывает все сообщения централизованно
async def process_secretary_input(chat_id: int, text: str) -> bool:
    """
    DEPRECATED: Эта функция больше не используется.
    GPT Intent Router в app.py обрабатывает create_task напрямую.
    Оставлена для обратной совместимости.
    """
    return False
