"""Intent router — classifies user messages into actionable intents."""

import re
import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Cyrillic lot code pattern: А119, В712, К3-А101, etc.
LOT_CODE_PATTERN = re.compile(r'[АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯа-я]{1,3}[\-]?[А-Яа-я]?\d{2,4}', re.IGNORECASE)

# Quick patterns — fast regex-based classification before GPT
QUICK_PATTERNS = [
    # Catalog / shahmatka
    (r'(шахматк|каталог|все (лоты|апартамент|квартир)|список лотов)', 'open_shahmatka', {}),
    (r'(презентаци|буклет)', 'send_presentation', {}),
    (r'(документ|договор|дду|аренд)', 'send_documents', {}),
    (r'(видео|ролик|медиа)', 'show_media', {}),
    (r'(новост|курс валют|валют)', 'show_news', {}),
    (r'(показ|запис|посмотреть (квартир|апартамент)|хочу посмотреть)', 'book_showing', {}),
    (r'(фиксац|зафиксир|закрепи)', 'open_fixation', {}),
    (r'(секретар|задач|расписани|напомн|планир)', 'show_schedule', {}),
    (r'(рассрочк|рассрочку|рассрочки|в рассрочку)', 'show_installment', {}),
    (r'(доходност|roi|окупаем|заработ|прибыл)', 'calculate_roi', {}),
    (r'(депозит|вклад|сравн.*банк|банк.*сравн)', 'compare_deposit', {}),
    (r'(планировк|план квартир|layout)', 'show_layouts', {}),
    (r'(коммерческ|кп\b|предложени)', 'get_commercial_proposal', {}),
    (r'(подбор|подобр|бюджет|портфель|за \d)', 'build_portfolio', {}),
]


def extract_lot_code(text: str) -> str | None:
    """Extract lot code from user text (e.g. А209, В712)."""
    match = LOT_CODE_PATTERN.search(text)
    return match.group(0).upper() if match else None


def extract_budget(text: str) -> int | None:
    """Extract budget amount from text like '5 млн', '5000000', '5 миллионов'."""
    # Pattern: number + млн/миллион
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(млн|миллион)', text, re.IGNORECASE)
    if m:
        return int(float(m.group(1).replace(',', '.')) * 1_000_000)

    # Pattern: raw number >= 100000
    m = re.search(r'(\d{6,})', text.replace(' ', ''))
    if m:
        return int(m.group(1))

    return None


def quick_classify(text: str) -> tuple[str | None, dict]:
    """Try to classify intent using regex patterns. Returns (intent, params) or (None, {})."""
    text_lower = text.lower().strip()

    for pattern, intent, default_params in QUICK_PATTERNS:
        if re.search(pattern, text_lower):
            params = dict(default_params)
            # Try to extract lot code
            code = extract_lot_code(text)
            if code:
                params['unit_code'] = code
            # Try to extract budget
            budget = extract_budget(text)
            if budget:
                params['budget'] = budget
            return intent, params

    return None, {}


def classify_intent_with_gpt(text: str) -> tuple[str, dict]:
    """Use GPT to classify intent when quick patterns don't match."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "chat", {}

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = """Ты классификатор намерений для RIZALTA (апартаменты в Белокурихе).
Определи intent пользователя. Верни JSON:
{"intent": "<intent>", "params": {}}

Возможные intents:
- calculate_roi — хочет узнать доходность (params: unit_code если есть)
- show_installment — хочет рассрочку (params: unit_code если есть)
- compare_deposit — сравнить с депозитом
- book_showing — записаться на показ
- show_layouts — посмотреть планировки (params: unit_code если есть)
- get_commercial_proposal — скачать КП (params: unit_code если есть)
- send_presentation — хочет презентацию
- open_fixation — фиксация клиента
- open_shahmatka — хочет каталог/шахматку
- send_documents — хочет документы/договоры
- show_media — хочет видео
- show_news — хочет новости/курсы валют
- build_portfolio — подбор апартаментов по бюджету (params: budget если есть)
- create_task — хочет создать задачу/напоминание
- show_schedule — хочет расписание/задачи
- chat — просто разговор, вопрос об объекте, или не подходит ни один intent

Если сомневаешься — верни "chat"."""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=150,
            temperature=0,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        intent = result.get("intent", "chat")
        params = result.get("params", {})

        # Also try to extract lot code from original text
        code = extract_lot_code(text)
        if code and "unit_code" not in params:
            params["unit_code"] = code

        return intent, params

    except Exception as e:
        logger.error(f"[INTENT] GPT classification error: {e}")
        return "chat", {}


def classify_intent(text: str) -> tuple[str, dict]:
    """Classify user intent: first try quick patterns, then GPT."""
    intent, params = quick_classify(text)
    if intent:
        return intent, params
    return classify_intent_with_gpt(text)
