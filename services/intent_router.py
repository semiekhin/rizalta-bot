"""
Единый GPT Intent Router для RIZALTA Bot.
Классифицирует ВСЕ входящие сообщения (текст и голос) в намерения.

Версия: 2.1.0
- Добавлены параметры building, floor для фильтрации
- Улучшено распознавание кодов лотов
- Поддержка "верхние этажи", "нижние этажи"
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

=== ПРОЕКТ RIZALTA ===
- 2 корпуса: Корпус 1 "Family", Корпус 2 "Business"
- Этажи: 1-9 в каждом корпусе
- ~350 лотов в продаже
- Коды лотов: буква (А/A или В/B) + цифры, например: В708, А101, B215

=== ПРАВИЛА ПРИОРИТЕТОВ ===
1. Код лота (В708, А101, B215) → get_kp
2. Этаж, корпус, бюджет, площадь → get_kp  
3. Только слово "шахматка" → open_shahmatka
4. Задача + дата/время → create_task
5. Любой запрос про лоты/квартиры → get_kp

=== ВСЕ ФУНКЦИИ БОТА ===

📋 КП (Коммерческие предложения):
• get_kp — отправить КП на лот
  Параметры: 
    - code (код лота, например "В708", "A101")
    - area (площадь в м²)
    - budget (бюджет в рублях)
    - building (корпус: 1 или 2)
    - floor (этаж: число или "верхние"/"нижние"/"средние")
  Триггеры: "КП", "коммерческое предложение", "КП на В708", "предложение на 15 млн"
  Примеры:
    - "КП на В708" → get_kp, code="В708"
    - "покажи что есть за 20 млн на 4 этаже 2го корпуса" → get_kp, building=2, floor=4, budget=20000000
    - "КП на верхних этажах до 30 млн" → get_kp, floor="верхние", budget=30000000
    - "что есть на 5 этаже" → get_kp, floor=5
    - "что есть на пятом этаже" → get_kp, floor=5
    - "покажи лоты на верхних этажах" → get_kp, floor="верхние"
    - "что на нижних этажах" → get_kp, floor="нижние"
    - "лоты 2 корпуса" → get_kp, building=2
    - "свободные лоты" → get_kp (без параметров)
    - "что в наличии" → get_kp (без параметров)
    - "что есть в корпусе бизнес" → get_kp, building=2

💰 Расчёты:
• calculate_roi — расчёт доходности/ROI
  Параметры: area, code, building, floor, budget
  Триггеры: "доходность", "ROI", "сколько заработаю", "рентабельность"

• show_installment — рассрочка и ипотека
  Параметры: area, code, building, floor
  Триггеры: "рассрочка", "ипотека", "как оплатить", "варианты оплаты"

• compare_deposit — сравнение RIZALTA с банковским депозитом
  Параметры: amount (сумма в рублях)
  Триггеры: "сравни с депозитом", "депозит или RIZALTA", "что выгоднее"

📌 Фиксация и шахматка:
• open_fixation — зафиксировать клиента за риэлтором
  Триггеры: "фиксация", "зафиксировать клиента", "закрепить клиента"

• open_shahmatka — открыть ВНЕШНЮЮ ссылку на таблицу шахматки
  Триггеры: ТОЛЬКО "шахматка", "открой шахматку", "ссылка на шахматку"
  ⚠️ НЕ использовать если упоминается: этаж, корпус, бюджет, площадь — это get_kp

📅 Записи:
• book_showing — записать на онлайн-показ
  Триггеры: "записаться на показ", "созвон с менеджером", "консультация"

📄 Документы:
• send_documents — отправить договоры
  Параметры: doc_type (ddu, arenda, all)
  Триггеры: "договор", "ДДУ", "договор аренды", "документы"

• send_presentation — презентация проекта
  Триггеры: "презентация", "презу скинь", "материалы о проекте"

🎬 Медиа:
• show_media — видео и медиа материалы
  Триггеры: "видео", "ролики", "медиа"

🗓 Секретарь (личные задачи):
• create_task — создать задачу/напоминание
  Параметры: task, date (YYYY-MM-DD), time (HH:MM), client_name, priority
  Триггеры: "напомни", "завтра позвонить", "встреча в 15:00"
  ВАЖНО: должно быть ДЕЙСТВИЕ + ВРЕМЯ

• show_schedule — показать расписание
  Параметры: period (today, tomorrow, week)
  Триггеры: "что на сегодня", "мои задачи", "план на неделю"

📰 Информация:
• show_news — новости, курсы, погода
  Параметры: type (currency, weather, flights, digest)
  Триггеры: "курс доллара", "погода", "новости", "авиабилеты"

💬 Общение:
• chat — вопросы о проекте, не попадающие в другие категории

🏠 Навигация:
• main_menu — вернуться в меню
  Триггеры: "меню", "назад", "в начало"

=== ПРАВИЛА КЛАССИФИКАЦИИ ===

1. ПРИОРИТЕТ ДЕЙСТВИЙ НАД ЗАДАЧАМИ:
   - "открой шахматку" → open_shahmatka (НЕ create_task!)
   - "покажи КП на В708" → get_kp (НЕ create_task!)

2. РАСПОЗНАВАНИЕ КОДОВ ЛОТОВ:
   - Буква (А, A, В, B) + цифры = код лота
   - "В708", "B708", "в708" — всё это лот В708
   - "А101", "A101" — лот А101
   - ВСЕГДА извлекай код в параметр code

3. РАСПОЗНАВАНИЕ КОРПУСОВ:
   - "корпус 1", "1 корпус", "первый корпус", "1-й корпус" → building=1
   - "корпус 2", "2 корпус", "второй корпус" → building=2
   - "фэмили", "family" → building=1
   - "бизнес", "business" → building=2

4. РАСПОЗНАВАНИЕ ЭТАЖЕЙ:
   - "4 этаж", "на 4 этаже", "четвёртый этаж" → floor=4
   - "верхние этажи", "наверху" → floor="верхние" (7-9)
   - "нижние этажи", "внизу" → floor="нижние" (1-3)
   - "средние этажи" → floor="средние" (4-6)

5. РАСПОЗНАВАНИЕ БЮДЖЕТА:
   - "20 млн", "20 миллионов", "20000000" → budget=20000000
   - "до 25 млн" → budget=25000000 (max)
   - "от 15 до 20 млн" → budget=20000000 (берём max)

6. ГОЛОСОВЫЕ ОШИБКИ (Whisper):
   - "напомню" = "напомни" → create_task
   - "кипи" = "КП" → get_kp
   - "корпус один" = "корпус 1"

=== ФОРМАТ ОТВЕТА ===

Ответь ТОЛЬКО валидным JSON (без markdown):
{{"intent": "название_функции", "params": {{"code": "В708", "building": 2, "floor": 4, "budget": 20000000}}, "confidence": 0.95}}

confidence — уверенность от 0 до 1

ВАЖНО: Всегда извлекай ВСЕ параметры из запроса!
"""


# === БЫСТРЫЕ ПАТТЕРНЫ (без GPT) ===

QUICK_PATTERNS = {
    # Точные совпадения кнопок меню
    "🔥Купи себе отель!": {"intent": "about_project", "params": {}},
    "💰 Расчёты": {"intent": "calculations_menu", "params": {}},
    "📊 Доходность": {"intent": "calculate_roi", "params": {}},
    "💳 Рассрочка": {"intent": "show_installment", "params": {}},
    "📈 Сравнить с депозитом": {"intent": "compare_deposit", "params": {}},
    "📋 КП (.pdf)": {"intent": "kp_menu", "params": {}},
    "📄 Договоры": {"intent": "documents_menu", "params": {}},
    "📊 Сравнение": {"intent": "compare_menu", "params": {}},
    "🎬 Медиа": {"intent": "show_media", "params": {}},
    "📌 Фиксация": {"intent": "open_fixation", "params": {}},
    "🏠 Шахматка": {"intent": "open_shahmatka", "params": {}},
    "🏢 Лоты": {"intent": "open_lots_app", "params": {}},
    "🗓 Секретарь": {"intent": "secretary_menu", "params": {}},
    "📰 Новости": {"intent": "show_news", "params": {}},
    "🔥 Записаться на онлайн-показ": {"intent": "book_showing", "params": {}},
    "🔙 Назад": {"intent": "back", "params": {}},
    
    # Команды
    "/start": {"intent": "start", "params": {}},
    "/help": {"intent": "help", "params": {}},
    "/myid": {"intent": "myid", "params": {}},
}

# Быстрый паттерн для кодов лотов (без GPT)
LOT_CODE_PATTERN = re.compile(r'^[АаAaВвBb]\d{3,4}$', re.IGNORECASE)


def get_weekday_name(dt: datetime) -> str:
    """Возвращает день недели на русском."""
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    return days[dt.weekday()]


def extract_lot_code(text: str) -> Optional[str]:
    """
    Извлекает код лота из текста.
    Возвращает нормализованный код или None.
    """
    # Паттерн: буква (А/A/В/B) + 3-4 цифры
    pattern = r'[АаAaВвBb]\s*\d{3,4}'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        code = match.group().upper().replace(" ", "")
        # Нормализуем к кириллице
        code = code.replace("A", "А").replace("B", "В")
        return code
    
    return None


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
    
    # Быстрое распознавание кода лота
    text_clean = text.strip()
    if LOT_CODE_PATTERN.match(text_clean):
        code = extract_lot_code(text_clean)
        return {
            "intent": "get_kp",
            "params": {"code": code},
            "confidence": 0.95,
            "source": "quick_match"
        }
    
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
        
        # Пост-обработка параметров
        result["params"] = normalize_params(result.get("params", {}))
        
        print(f"[INTENT] GPT: {result.get('intent')} | params: {result.get('params')} | conf: {result.get('confidence', 0)}")
        return result
        
    except json.JSONDecodeError as e:
        print(f"[INTENT] JSON parse error: {e}, raw: {result_text}")
        return {"intent": "chat", "params": {}, "confidence": 0.3, "source": "error"}
        
    except Exception as e:
        print(f"[INTENT] GPT error: {e}")
        return {"intent": "chat", "params": {}, "confidence": 0.3, "source": "error"}


def normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализует параметры из GPT ответа.
    """
    result = {}
    
    # Код лота
    if params.get("code"):
        code = str(params["code"]).upper().strip()
        # Нормализуем к кириллице
        code = code.replace("A", "А").replace("B", "В")
        result["code"] = code
    
    # Корпус
    if params.get("building"):
        try:
            result["building"] = int(params["building"])
        except (ValueError, TypeError):
            pass
    
    # Этаж
    if params.get("floor"):
        floor = params["floor"]
        if isinstance(floor, int):
            result["floor"] = floor
        elif isinstance(floor, str):
            floor_lower = floor.lower()
            if floor_lower in ("верхние", "верхних", "top"):
                result["floor"] = "верхние"
            elif floor_lower in ("нижние", "нижних", "bottom"):
                result["floor"] = "нижние"
            elif floor_lower in ("средние", "средних", "middle"):
                result["floor"] = "средние"
            else:
                try:
                    result["floor"] = int(floor)
                except ValueError:
                    result["floor"] = floor
    
    # Бюджет
    if params.get("budget"):
        try:
            budget = params["budget"]
            if isinstance(budget, str):
                # "20 млн" → 20000000
                budget = budget.lower().replace(" ", "").replace("млн", "000000").replace("м", "000000")
                budget = re.sub(r"[^\d]", "", budget)
            result["budget"] = int(budget)
        except (ValueError, TypeError):
            pass
    
    # Площадь
    if params.get("area"):
        try:
            result["area"] = float(params["area"])
        except (ValueError, TypeError):
            pass
    
    # Задачи секретаря
    if params.get("task"):
        result["task"] = params["task"]
    
    if params.get("date"):
        date_str = params["date"]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            result["date"] = date_str
        except ValueError:
            pass
    
    if params.get("time"):
        time_str = params["time"]
        if re.match(r"^\d{1,2}:\d{2}$", time_str):
            if len(time_str.split(":")[0]) == 1:
                time_str = "0" + time_str
            result["time"] = time_str
        elif re.match(r"^\d{1,2}$", time_str):
            result["time"] = f"{int(time_str):02d}:00"
    
    if params.get("client_name"):
        result["client_name"] = params["client_name"]
    
    if params.get("priority"):
        result["priority"] = params["priority"]
    
    # Новости
    if params.get("type"):
        result["type"] = params["type"]
    
    if params.get("doc_type"):
        result["doc_type"] = params["doc_type"]
    
    if params.get("period"):
        result["period"] = params["period"]
    
    if params.get("amount"):
        try:
            result["amount"] = int(params["amount"])
        except (ValueError, TypeError):
            pass
    
    return result


# === ТЕСТИРОВАНИЕ ===

if __name__ == "__main__":
    test_messages = [
        # Коды лотов
        "В708",
        "КП на А101",
        "покажи B215",
        
        # Корпуса и этажи
        "покажи что есть за 20 млн на 4 этаже 2го корпуса",
        "что есть на верхних этажах до 30 млн",
        "лоты в корпусе 1 на 5 этаже",
        
        # Бюджет
        "КП до 25 млн",
        "что есть за 15-20 миллионов",
        
        # Действия vs задачи
        "открой шахматку",
        "завтра позвонить Иванову в 10",
        "напомни отправить КП",
        
        # Голосовые ошибки
        "кипи на корпус один в семьсот восемь",
    ]
    
    print("=== ТЕСТ INTENT ROUTER v2.1.0 ===\n")
    
    for msg in test_messages:
        result = classify_intent(msg)
        print(f"'{msg}'")
        print(f"  → {result['intent']} | params: {result.get('params', {})} | conf: {result.get('confidence', 0):.2f}")
        print()
