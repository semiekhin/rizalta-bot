"""
AI-парсер для извлечения задач из естественного языка.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from openai import OpenAI
from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

TASK_PARSER_PROMPT = """Ты — AI-секретарь. Извлеки данные из текста.

Сегодня: {today}, {weekday}

Извлеки:
- task: что сделать (ОБЯЗАТЕЛЬНО включи имя клиента если упомянут, например "Позвонить Иванову")
- date: YYYY-MM-DD или null
- time: HH:MM или null  
- client_name: имя клиента или null
- priority: urgent/high/normal/low
- description: детали или null

Даты: "сегодня"={today}, "завтра"={tomorrow}, "послезавтра"={day_after}
Приоритет: "срочно/важно"=high, "критично"=urgent, иначе normal

Ответь ТОЛЬКО JSON без markdown:
{{"task":"...","date":"...","time":"...","client_name":"...","priority":"...","description":"..."}}"""


INTENT_CLASSIFIER_PROMPT = """Определи намерение пользователя. Ответь ОДНИМ словом:
- TASK — если это задача, напоминание, дело (позвонить, отправить, встреча, сделать и т.п.)
- SCHEDULE — если спрашивает расписание (что на сегодня, план на неделю, мои задачи)
- OTHER — всё остальное (вопросы, информация, разговор)

Примеры TASK: "завтра позвонить Иванову", "напомни отправить КП", "встреча в 15:00"
Примеры SCHEDULE: "что на сегодня", "план на завтра", "мои задачи"
Примеры OTHER: "какая погода", "расскажи про проект", "сколько стоит"

Сообщение: {text}

Ответ (одно слово):"""


def get_weekday_name(dt):
    days = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"]
    return days[dt.weekday()]


def classify_intent(text: str) -> str:
    """Классифицирует намерение: TASK, SCHEDULE или OTHER."""
    text_lower = text.lower()
    
    # Если есть временные маркеры + действие = скорее всего задача
    time_markers = ["завтра", "сегодня", "послезавтра", "в понедельник", "во вторник",
                    "в среду", "в четверг", "в пятницу", "через", "на неделе", 
                    "в 10", "в 11", "в 12", "в 13", "в 14", "в 15", "в 16", "в 17", "в 18",
                    "утром", "вечером", "днём"]
    action_markers = ["отправить", "позвонить", "написать", "сделать", "подготовить",
                      "напомни", "напомнить", "встреча", "созвон"]
    
    has_time = any(t in text_lower for t in time_markers)
    has_action = any(a in text_lower for a in action_markers)
    
    # Если есть и время и действие - это задача
    if has_time and has_action:
        return "TASK"
    
    # Простые команды бота (без времени и действия)
    bot_commands = ["фиксация", "зафиксировать клиента", "презентация", "медиа", 
                    "видео", "договор", "шахматка", "депозит", "сравнение",
                    "покажи кп", "открой кп", "меню кп"]
    if any(cmd in text_lower for cmd in bot_commands):
        return "OTHER"
    
    # Запросы расписания
    schedule_queries = ["что на сегодня", "что на завтра", "что на неделю", 
                        "мои задачи", "план на", "расписание"]
    if any(q in text_lower for q in schedule_queries):
        return "SCHEDULE"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": INTENT_CLASSIFIER_PROMPT.format(text=text)}
            ],
            temperature=0,
            max_tokens=10
        )
        intent = response.choices[0].message.content.strip().upper()
        if intent in ("TASK", "SCHEDULE", "OTHER"):
            return intent
        return "OTHER"
    except Exception as e:
        print(f"[SECRETARY AI] Ошибка классификации: {e}")
        return "OTHER"


def parse_task_with_ai(text):
    """Парсит текст и извлекает структуру задачи."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    
    prompt = TASK_PARSER_PROMPT.format(
        today=today.strftime("%Y-%m-%d"),
        weekday=get_weekday_name(today),
        tomorrow=tomorrow.strftime("%Y-%m-%d"),
        day_after=day_after.strftime("%Y-%m-%d")
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=500
        )
        result_text = response.choices[0].message.content.strip()
        if result_text.startswith("```"):
            result_text = re.sub(r"^```json?\n?", "", result_text)
            result_text = re.sub(r"\n?```$", "", result_text)
        return json.loads(result_text)
    except Exception as e:
        print(f"[SECRETARY AI] Ошибка парсинга: {e}")
        return None


def is_task_request(text: str) -> bool:
    """Это запрос на создание задачи? (через GPT)"""
    return classify_intent(text) == "TASK"


def is_schedule_query(text: str) -> bool:
    """Это запрос расписания? (через GPT)"""
    return classify_intent(text) == "SCHEDULE"


def get_intent(text: str) -> str:
    """Получает намерение (для оптимизации — один вызов)."""
    return classify_intent(text)


def analyze_workload(count, is_urgent=False):
    """Анализ загрузки."""
    if count >= 7:
        return "⚠️ На этот день уже 7+ задач. Перегруз!"
    elif count >= 5:
        return "📊 На этот день уже 5 задач. Плотный график."
    return None


def generate_morning_digest(tasks, date_str):
    """Утренний дайджест."""
    if not tasks:
        return "🌅 Доброе утро! Сегодня задач нет. Свободный день!"
    
    with_time = sorted([t for t in tasks if t.get("due_time")], key=lambda x: x["due_time"])
    without_time = [t for t in tasks if not t.get("due_time")]
    urgent = sum(1 for t in tasks if t["priority"] in ("urgent","high"))
    
    lines = ["🌅 <b>Доброе утро! План на сегодня:</b>", ""]
    for t in with_time:
        icon = "🔴" if t["priority"] in ("urgent","high") else "⏰"
        lines.append(f"{icon} {t['due_time']} — {t['task_text']}")
    if without_time:
        lines.append("")
        lines.append("📌 <b>Без времени:</b>")
        for t in without_time:
            lines.append(f"• {t['task_text']}")
    lines.append("")
    lines.append(f"📊 Всего: {len(tasks)} задач" + (f" (🔴 {urgent} срочных)" if urgent else ""))
    lines.append("")
    lines.append("💪 Продуктивного дня!")
    return "\n".join(lines)
