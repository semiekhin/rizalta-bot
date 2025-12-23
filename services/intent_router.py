"""
Единый GPT Intent Router для RIZALTA Bot.
Классифицирует ВСЕ входящие сообщения (текст и голос) в намерения.
Заменяет regex-паттерны и режим секретаря.

Версия: 2.0.0
"""

import json
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI
from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# === МЕТАЗНАНИЯ О БОТЕ ===

INTENT_SYSTEM_PROMPT = """Ты — классификатор намерений для Telegram-бота RIZALTA.
Бот помогает риэлторам продавать инвестиционную недвижимость RIZALTA Resort Belokurikha (Алтай).

Сегодня: {today}, {weekday}

=== ВСЕ ФУНКЦИИ БОТА ===

📋 КП (Коммерческие предложения):
• get_kp — отправить КП на лот
  Параметры: area (м²), budget (рубли), code (например В415)
  Триггеры: "КП", "коммерческое предложение", "КП на 25 метров", "предложение на 15 млн"

💰 Расчёты:
• calculate_roi — расчёт доходности/ROI
  Параметры: area (м²) или unit_code
  Триггеры: "доходность", "ROI", "сколько заработаю", "рентабельность"

• show_installment — рассрочка и ипотека
  Параметры: area (м²) или unit_code
  Триггеры: "рассрочка", "ипотека", "как оплатить", "варианты оплаты"

• compare_deposit — сравнение RIZALTA с банковским депозитом
  Параметры: amount (сумма в рублях)
  Триггеры: "сравни с депозитом", "депозит или RIZALTA", "что выгоднее"

📌 Фиксация и шахматка:
• open_fixation — зафиксировать клиента за риэлтором
  Триггеры: "фиксация", "зафиксировать клиента", "закрепить клиента"

• open_shahmatka — показать свободные лоты
  Триггеры: "шахматка", "свободные лоты", "что есть в наличии", "доступные номера"

📅 Записи:
• book_showing — записать на онлайн-показ
  Триггеры: "записаться на показ", "созвон с менеджером", "консультация", "связаться"

📄 Документы:
• send_documents — отправить договоры
  Параметры: doc_type (ddu, arenda, all)
  Триггеры: "договор", "ДДУ", "договор аренды", "документы"

• send_presentation — презентация проекта
  Триггеры: "презентация", "презу скинь", "материалы о проекте"

🎬 Медиа:
• show_media — видео и медиа материалы
  Триггеры: "видео", "ролики", "медиа", "покажи видео"

🗓 Секретарь (личные задачи риэлтора):
• create_task — создать задачу/напоминание
  Параметры: task (текст), date (YYYY-MM-DD), time (HH:MM), client_name
  Триггеры: "напомни", "завтра позвонить", "встреча в 15:00", "записать задачу"
  ВАЖНО: должно быть ДЕЙСТВИЕ (позвонить, отправить, встретиться) + опционально ВРЕМЯ

• show_schedule — показать расписание
  Параметры: period (today, tomorrow, week)
  Триггеры: "что на сегодня", "мои задачи", "план на неделю", "расписание"

📰 Информация:
• show_news — новости, курсы, погода
  Параметры: type (currency, weather, flights, digest)
  Триггеры: "курс доллара", "погода в Белокурихе", "новости", "авиабилеты"

💬 Общение:
• chat — вопросы о проекте, не попадающие в другие категории
  Триггеры: "расскажи о проекте", "кто застройщик", вопросы об Алтае

🏠 Навигация:
• main_menu — вернуться в главное меню
  Триггеры: "меню", "назад", "в начало"

=== ПРАВИЛА КЛАССИФИКАЦИИ ===

1. ПРИОРИТЕТ ДЕЙСТВИЙ НАД ЗАДАЧАМИ:
   - "открой шахматку" → open_shahmatka (НЕ create_task!)
   - "покажи КП" → get_kp (НЕ create_task!)
   - "скинь презентацию" → send_presentation (НЕ create_task!)

2. КОГДА create_task:
   - Есть ДЕЙСТВИЕ + ВРЕМЯ/ДАТА: "завтра позвонить Иванову"
   - Есть слово "напомни/напомнить": "напомни отправить КП"
   - Явная задача: "записать: встреча с клиентом"

3. ГОЛОСОВЫЕ ОШИБКИ (Whisper):
   - "напомню" = "напомни" → create_task
   - "позвоните" = "позвонить" → возможно create_task
   - "кипи" = "КП" → get_kp

4. ПРИ СОМНЕНИИ:
   - Если можно выполнить сейчас → выбирай action
   - Если на будущее → create_task

5. ИЗВЛЕЧЕНИЕ ПАРАМЕТРОВ:
   - "КП на 25 метров" → get_kp, area=25
   - "15 млн" или "15000000" → budget=15000000
   - "завтра в 10" → date={tomorrow}, time="10:00"
   - "В415" или "А209" → code="В415" или unit_code="A209"

=== ФОРМАТ ОТВЕТА ===

Ответь ТОЛЬКО валидным JSON (без markdown):
{{"intent": "название_функции", "params": {{"param1": "value1"}}, "confidence": 0.95}}

confidence — уверенность от 0 до 1
"""


# === БЫСТРЫЕ ПАТТЕРНЫ (без GPT) ===
# Для очевидных случаев экономим токены

QUICK_PATTERNS = {
    # Точные совпадения кнопок меню
    "📖 О проекте": {"intent": "about_project", "params": {}},
    "💰 Расчёты": {"intent": "calculations_menu", "params": {}},
    "📋 КП (.pdf)": {"intent": "kp_menu", "params": {}},
    "📄 Договоры": {"intent": "documents_menu", "params": {}},
    "📊 Сравнение": {"intent": "compare_menu", "params": {}},
    "🎬 Медиа": {"intent": "show_media", "params": {}},
    "📌 Фиксация": {"intent": "open_fixation", "params": {}},
    "🏠 Шахматка": {"intent": "open_shahmatka", "params": {}},
    "🗓 Секретарь": {"intent": "secretary_menu", "params": {}},
    "📰 Новости": {"intent": "show_news", "params": {}},
    "🔥 Записаться на онлайн-показ": {"intent": "book_showing", "params": {}},
    "🔙 Назад": {"intent": "back", "params": {}},
    
    # Команды
    "/start": {"intent": "start", "params": {}},
    "/help": {"intent": "help", "params": {}},
    "/myid": {"intent": "myid", "params": {}},
}


def get_weekday_name(dt: datetime) -> str:
    """Возвращает день недели на русском."""
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    return days[dt.weekday()]


def try_quick_match(text: str) -> Optional[Dict[str, Any]]:
    """
    Пытается быстро определить intent без GPT.
    Возвращает None если нужен GPT.
    """
    # Точное совпадение с кнопками меню
    if text in QUICK_PATTERNS:
        result = QUICK_PATTERNS[text].copy()
        result["confidence"] = 1.0
        result["source"] = "quick_match"
        return result
    
    # Команды с параметрами
    if text.startswith("/start"):
        return {"intent": "start", "params": {}, "confidence": 1.0, "source": "quick_match"}
    
    return None


def classify_intent(text: str) -> Dict[str, Any]:
    """
    Главная функция классификации намерений.
    
    Returns:
        {
            "intent": str,           # Название функции
            "params": dict,          # Параметры для функции
            "confidence": float,     # Уверенность 0-1
            "source": str            # "quick_match" или "gpt"
        }
    """
    
    # 1. Пробуем быстрый матч
    quick_result = try_quick_match(text)
    if quick_result:
        print(f"[INTENT] Quick match: {quick_result['intent']}")
        return quick_result
    
    # 2. GPT классификация
    if not client:
        print("[INTENT] OpenAI client not available")
        return {"intent": "chat", "params": {}, "confidence": 0.5, "source": "fallback"}
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    prompt = INTENT_SYSTEM_PROMPT.format(
        today=today.strftime("%Y-%m-%d"),
        weekday=get_weekday_name(today),
        tomorrow=tomorrow.strftime("%Y-%m-%d")
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Убираем markdown если есть
        if result_text.startswith("```"):
            result_text = re.sub(r"^```json?\n?", "", result_text)
            result_text = re.sub(r"\n?```$", "", result_text)
        
        result = json.loads(result_text)
        result["source"] = "gpt"
        
        print(f"[INTENT] GPT: {result.get('intent')} (confidence: {result.get('confidence', 0)})")
        return result
        
    except json.JSONDecodeError as e:
        print(f"[INTENT] JSON parse error: {e}, raw: {result_text}")
        return {"intent": "chat", "params": {}, "confidence": 0.3, "source": "error"}
        
    except Exception as e:
        print(f"[INTENT] GPT error: {e}")
        return {"intent": "chat", "params": {}, "confidence": 0.3, "source": "error"}


def parse_task_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализует параметры задачи из GPT ответа.
    """
    result = {}
    
    # Текст задачи
    if params.get("task"):
        result["task"] = params["task"]
    
    # Дата
    if params.get("date"):
        date_str = params["date"]
        # Проверяем формат YYYY-MM-DD
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            result["date"] = date_str
        except ValueError:
            pass
    
    # Время
    if params.get("time"):
        time_str = params["time"]
        # Нормализуем формат HH:MM
        if re.match(r"^\d{1,2}:\d{2}$", time_str):
            if len(time_str.split(":")[0]) == 1:
                time_str = "0" + time_str
            result["time"] = time_str
        elif re.match(r"^\d{1,2}$", time_str):
            result["time"] = f"{int(time_str):02d}:00"
    
    # Клиент
    if params.get("client_name"):
        result["client_name"] = params["client_name"]
    
    # Приоритет
    if params.get("priority"):
        result["priority"] = params["priority"]
    
    return result


def parse_kp_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализует параметры КП из GPT ответа.
    """
    result = {}
    
    # Площадь
    if params.get("area"):
        try:
            result["area"] = float(params["area"])
        except (ValueError, TypeError):
            pass
    
    # Бюджет
    if params.get("budget"):
        try:
            budget = params["budget"]
            if isinstance(budget, str):
                # "15 млн" → 15000000
                budget = budget.lower().replace(" ", "").replace("млн", "000000").replace("м", "000000")
                budget = re.sub(r"[^\d]", "", budget)
            result["budget"] = int(budget)
        except (ValueError, TypeError):
            pass
    
    # Код лота
    if params.get("code"):
        code = params["code"].upper()
        # Нормализуем: В415 или B415 → В415
        code = code.replace("B", "В").replace("A", "А")
        result["code"] = code
    
    return result


# === ТЕСТИРОВАНИЕ ===

if __name__ == "__main__":
    test_messages = [
        # Должны быть actions
        "открой шахматку",
        "скинь презентацию",
        "покажи КП на 25 метров",
        "запиши на показ",
        
        # Должны быть tasks
        "завтра позвонить Иванову в 10",
        "напомни отправить КП клиенту",
        "встреча с Петровым в 15:00",
        
        # Расписание
        "что на сегодня",
        "мои задачи на неделю",
        
        # Голосовые ошибки
        "напомню позвонить",  # = напомни
        "кипи на 30 метров",  # = КП
    ]
    
    print("=== ТЕСТ INTENT ROUTER ===\n")
    
    for msg in test_messages:
        result = classify_intent(msg)
        print(f"'{msg}'")
        print(f"  → {result['intent']} | params: {result.get('params', {})} | conf: {result.get('confidence', 0):.2f}")
        print()
