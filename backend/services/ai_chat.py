"""AI Chat service — OpenAI streaming for RIZALTA webapp."""

import os
import json
import logging
from openai import OpenAI

from services.data_loader import load_finance, load_instructions
from services.intent_router import classify_intent

logger = logging.getLogger(__name__)

# Intent → webapp action mapping
INTENT_ACTIONS = {
    "calculate_roi": {
        "message": "Вот расчёт доходности{unit_suffix}:",
        "actions": lambda p: [
            {"label": "Посмотреть ROI", "type": "navigate", "to": f"/catalog/{p['unit_code']}?modal=roi"} if p.get("unit_code") else
            {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
        ],
    },
    "show_installment": {
        "message": "Варианты рассрочки{unit_suffix}:",
        "actions": lambda p: [
            {"label": "Рассрочка", "type": "navigate", "to": f"/catalog/{p['unit_code']}?modal=deposit"} if p.get("unit_code") else
            {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
        ],
    },
    "compare_deposit": {
        "message": "Сравнение с банковским депозитом:",
        "actions": lambda p: [
            {"label": "Сравнить с депозитом", "type": "navigate", "to": f"/catalog/{p['unit_code']}?modal=deposit"} if p.get("unit_code") else
            {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
        ],
    },
    "book_showing": {
        "message": "Запишитесь на онлайн-показ апартаментов:",
        "actions": lambda _: [
            {"label": "Записаться на показ", "type": "navigate", "to": "/booking"},
        ],
    },
    "show_layouts": {
        "message": "Планировки апартаментов{unit_suffix}:",
        "actions": lambda p: [
            {"label": "Посмотреть планировку", "type": "navigate", "to": f"/catalog/{p['unit_code']}"} if p.get("unit_code") else
            {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
        ],
    },
    "get_commercial_proposal": {
        "message": "Коммерческое предложение{unit_suffix}:",
        "actions": lambda p: [
            {"label": "Скачать КП", "type": "navigate", "to": f"/catalog/{p['unit_code']}"} if p.get("unit_code") else
            {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
        ],
    },
    "send_presentation": {
        "message": "Презентации проекта RIZALTA:",
        "actions": lambda _: [
            {"label": "Открыть презентации", "type": "navigate", "to": "/presentations"},
        ],
    },
    "open_fixation": {
        "message": "Для фиксации клиента за вами перейдите в раздел Фиксация:",
        "actions": lambda _: [
            {"label": "Открыть фиксацию", "type": "navigate", "to": "/fixation"},
        ],
    },
    "open_shahmatka": {
        "message": "Каталог апартаментов RIZALTA:",
        "actions": lambda _: [
            {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
        ],
    },
    "send_documents": {
        "message": "Документы проекта RIZALTA:",
        "actions": lambda _: [
            {"label": "Открыть документы", "type": "navigate", "to": "/documents"},
        ],
    },
    "show_media": {
        "message": "Видеоматериалы о проекте:",
        "actions": lambda _: [
            {"label": "Открыть видео", "type": "navigate", "to": "/media"},
        ],
    },
    "show_news": {
        "message": "Актуальные курсы валют:",
        "actions": lambda _: [
            {"label": "Курсы валют", "type": "navigate", "to": "/news"},
        ],
    },
    "build_portfolio": {
        "message": "Подбор апартаментов{budget_suffix}:",
        "actions": lambda _: [
            {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
        ],
    },
    "create_task": {
        "message": "Задача создана. Откройте секретарь для просмотра:",
        "actions": lambda _: [
            {"label": "Открыть секретарь", "type": "navigate", "to": "/secretary"},
        ],
    },
    "show_schedule": {
        "message": "Ваше расписание и задачи:",
        "actions": lambda _: [
            {"label": "Открыть секретарь", "type": "navigate", "to": "/secretary"},
        ],
    },
}

# OpenAI client (initialized lazily)
_client = None


def get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in .env")
        _client = OpenAI(api_key=api_key)
    return _client


def build_finance_system_context(finance_data: dict) -> str:
    """Build financial context string from rizalta_finance.json for system prompt."""
    if not finance_data:
        return ""

    parts = []

    # General project info
    if "project" in finance_data:
        proj = finance_data["project"]
        parts.append(f"Проект: {proj.get('name', 'RIZALTA')}")
        if "location" in proj:
            parts.append(f"Локация: {proj['location']}")
        if "description" in proj:
            parts.append(f"Описание: {proj['description']}")

    # Buildings info
    if "buildings" in finance_data:
        for b in finance_data["buildings"]:
            name = b.get("name", "")
            total = b.get("total_units", "")
            parts.append(f"{name}: {total} юнитов")

    # Financial parameters
    if "financial" in finance_data:
        fin = finance_data["financial"]
        if "rental_yield" in fin:
            parts.append(f"Арендная доходность: {fin['rental_yield']}")
        if "occupancy_rate" in fin:
            parts.append(f"Загрузка: {fin['occupancy_rate']}")
        if "price_growth" in fin:
            parts.append(f"Рост стоимости: {fin['price_growth']}")
        if "management_fee" in fin:
            parts.append(f"Комиссия УК: {fin['management_fee']}")

    # Installment plans
    if "installment" in finance_data:
        inst = finance_data["installment"]
        plans = []
        for plan in inst if isinstance(inst, list) else [inst]:
            if isinstance(plan, dict):
                plans.append(f"  - {plan.get('name', '')}: {plan.get('description', '')}")
        if plans:
            parts.append("Варианты оплаты:\n" + "\n".join(plans))

    # Price ranges
    if "price_ranges" in finance_data:
        ranges = finance_data["price_ranges"]
        for r in ranges if isinstance(ranges, list) else [ranges]:
            if isinstance(r, dict):
                parts.append(f"Цены {r.get('type', '')}: от {r.get('min', '')} до {r.get('max', '')} руб.")

    if not parts:
        # Fallback: dump the whole thing as context (truncated)
        raw = json.dumps(finance_data, ensure_ascii=False, indent=None)
        if len(raw) > 4000:
            raw = raw[:4000] + "..."
        return f"\n\nФинансовые данные проекта:\n{raw}"

    return "\n\nФинансовые данные проекта:\n" + "\n".join(parts)


def build_system_prompt() -> str:
    """Build full system prompt = instructions + finance context."""
    instructions = load_instructions()
    finance = load_finance()
    context = build_finance_system_context(finance)
    return instructions + context


def stream_chat_response(message: str, history: list[dict]):
    """Generator that yields SSE events from OpenAI streaming response.

    Yields strings in SSE format: 'data: {"type": "token", "content": "..."}\n\n'
    """
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

    # Build messages array
    system_prompt = build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    # Add history (limit to last 20 messages)
    if history:
        messages.extend(history[-20:])

    # Add current user message
    messages.append({"role": "user", "content": message})

    try:
        client = get_client()
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield f'data: {json.dumps({"type": "token", "content": token}, ensure_ascii=False)}\n\n'

        yield f'data: {json.dumps({"type": "done", "content": ""})}\n\n'

    except Exception as e:
        logger.error(f"[AI CHAT] OpenAI error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "AI временно недоступен, попробуйте позже"}, ensure_ascii=False)}\n\n'


def analyze_user_intent(message: str) -> dict | None:
    """Analyze message intent. Returns action dict if actionable, None for chat."""
    intent, params = classify_intent(message)

    if intent == "chat" or intent not in INTENT_ACTIONS:
        return None

    mapping = INTENT_ACTIONS[intent]

    # Build message with substitutions
    unit_suffix = f" по юниту {params['unit_code']}" if params.get("unit_code") else ""
    budget_suffix = f" на бюджет {params['budget']:,} руб.".replace(",", " ") if params.get("budget") else ""
    msg_text = mapping["message"].format(
        unit_suffix=unit_suffix,
        budget_suffix=budget_suffix,
    )

    # Build actions
    actions = mapping["actions"](params)

    return {
        "type": "action",
        "intent": intent,
        "params": params,
        "message": msg_text,
        "actions": actions,
    }
