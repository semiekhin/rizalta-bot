"""AI Chat service — OpenAI streaming for RIZALTA webapp."""

import os
import json
import logging
from openai import OpenAI

from services.data_loader import load_finance, load_instructions
from services.intent_router import classify_intent

logger = logging.getLogger(__name__)

# Navigation intents — return JSON action immediately (open a screen)
NAVIGATION_INTENTS = {
    "open_shahmatka", "send_presentation", "show_media", "send_documents",
    "open_fixation", "show_news", "show_schedule", "create_task",
}

# Intent → action buttons mapping (used for both navigation and enriched intents)
INTENT_ACTIONS = {
    "calculate_roi": lambda p: [
        {"label": "Посмотреть ROI", "type": "navigate", "to": f"/catalog/{p['unit_code']}?modal=roi"} if p.get("unit_code") else
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ],
    "show_installment": lambda p: [
        {"label": "Рассрочка", "type": "navigate", "to": f"/catalog/{p['unit_code']}?modal=deposit"} if p.get("unit_code") else
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ],
    "compare_deposit": lambda p: [
        {"label": "Сравнить с депозитом", "type": "navigate", "to": f"/catalog/{p['unit_code']}?modal=deposit"} if p.get("unit_code") else
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ],
    "book_showing": lambda _: [
        {"label": "Записаться на показ", "type": "navigate", "to": "/booking"},
    ],
    "show_layouts": lambda p: [
        {"label": "Посмотреть планировку", "type": "navigate", "to": f"/catalog/{p['unit_code']}"} if p.get("unit_code") else
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ],
    "get_commercial_proposal": lambda p: [
        {"label": "Скачать КП", "type": "navigate", "to": f"/catalog/{p['unit_code']}"} if p.get("unit_code") else
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ],
    "send_presentation": lambda _: [
        {"label": "Открыть презентации", "type": "navigate", "to": "/presentations"},
    ],
    "open_fixation": lambda _: [
        {"label": "Открыть фиксацию", "type": "navigate", "to": "/fixation"},
    ],
    "open_shahmatka": lambda _: [
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ],
    "send_documents": lambda _: [
        {"label": "Открыть документы", "type": "navigate", "to": "/documents"},
    ],
    "show_media": lambda _: [
        {"label": "Открыть видео", "type": "navigate", "to": "/media"},
    ],
    "show_news": lambda _: [
        {"label": "Курсы валют", "type": "navigate", "to": "/news"},
    ],
    "build_portfolio": lambda _: [
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ],
    "create_task": lambda _: [
        {"label": "Открыть секретарь", "type": "navigate", "to": "/secretary"},
    ],
    "show_schedule": lambda _: [
        {"label": "Открыть секретарь", "type": "navigate", "to": "/secretary"},
    ],
}

# Navigation intent messages (short, for JSON-only responses)
NAVIGATION_MESSAGES = {
    "open_shahmatka": "Каталог апартаментов RIZALTA:",
    "send_presentation": "Презентации проекта RIZALTA:",
    "show_media": "Видеоматериалы о проекте:",
    "send_documents": "Документы проекта RIZALTA:",
    "open_fixation": "Для фиксации клиента перейдите в раздел Фиксация:",
    "show_news": "Актуальные курсы валют:",
    "show_schedule": "Ваше расписание и задачи:",
    "create_task": "Задача создана. Откройте секретарь для просмотра:",
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


def build_finance_system_context(finance: dict) -> str:
    """Build financial context from rizalta_finance.json for the system prompt.

    Real JSON structure: project(str), completion_year(int), defaults(dict),
    units(list), installment_programs(list), mortgage_programs(list),
    investment_scenarios(list), extra_notes(dict), installment_notes(dict).
    """
    if not finance:
        return ""

    completion = finance.get("completion_year", 2027)
    project = finance.get("project", "RIZALTA Resort Belokurikha")
    defaults = finance.get("defaults", {})
    installments = finance.get("installment_programs", [])
    mortgages = finance.get("mortgage_programs", [])
    units = finance.get("units", [])
    extra_notes = finance.get("extra_notes", {})
    installment_notes = finance.get("installment_notes", {})

    lines = []
    lines.append("=== ФИНАНСОВЫЕ ДАННЫЕ ПРОЕКТА (используй только эти цифры) ===")
    lines.append("")
    lines.append(f"Проект: {project}")
    lines.append(f"Срок сдачи: Q4 {completion} года")
    lines.append("")

    # === Units ===
    lines.append("=== АПАРТАМЕНТЫ ===")
    for u in units:
        code = u.get("unit_code", "")
        title = u.get("title", code)
        area = u.get("area_m2", 0)
        price = u.get("price_rub", 0)
        daily = u.get("daily_rate_rub", defaults.get("daily_rate_rub", 15000))
        occ = u.get("occupancy_pct", defaults.get("occupancy_pct", 60))
        exp = u.get("expenses_pct", defaults.get("expenses_pct", 50))

        gross_year = daily * 365 * (occ / 100)
        net_year = gross_year * (1 - exp / 100)
        roi_pct = (net_year / price * 100) if price > 0 else 0

        cap = u.get("capitalization_projection", {})
        price_2027 = cap.get("price_2027_rub", 0)
        price_2029 = cap.get("price_2029_rub", 0)

        lines.append(f"• {title} ({area} м²):")
        lines.append(f"  Цена: {price:,.0f} ₽")
        lines.append(f"  Точка входа (ПВ 30%): ~{price * 0.3:,.0f} ₽")
        lines.append(f"  Доход от аренды: ~{net_year:,.0f} ₽/год ({roi_pct:.1f}% годовых)")
        if price_2027:
            growth_2027 = ((price_2027 - price) / price * 100)
            lines.append(f"  Прогноз 2027: {price_2027:,.0f} ₽ (+{growth_2027:.0f}%)")
        if price_2029:
            growth_2029 = ((price_2029 - price) / price * 100)
            lines.append(f"  Прогноз 2029: {price_2029:,.0f} ₽ (+{growth_2029:.0f}%)")
        lines.append("")

    # === Installment programs ===
    if installments:
        lines.append("=== ПРОГРАММЫ РАССРОЧКИ ===")
        for p in installments:
            name = p.get("name", "")
            pv = p.get("first_payment_pct", 0)
            months = p.get("months", 0)
            rate = p.get("rate_pct", 0)
            comment = p.get("comment", "")
            lines.append(f"• {name}: ПВ {pv}%, {months} мес, ставка {rate}%")
            if comment:
                lines.append(f"  ({comment})")
        if installment_notes:
            q = installment_notes.get("quarterly_option", "")
            fp = installment_notes.get("full_payment_discount", "")
            if q:
                lines.append(f"  Поквартальная оплата: {q}")
            if fp:
                lines.append(f"  Скидка за 100% оплату: {fp}")
        lines.append("")

    # === Mortgage ===
    if mortgages:
        lines.append("=== ИПОТЕКА ===")
        for m in mortgages:
            lines.append(f"• {m.get('name', '')}")
            lines.append(f"  Стоимость: {m.get('object_price_rub', 0):,.0f} ₽")
            lines.append(f"  ПВ: {m.get('first_payment_rub', 0):,.0f} ₽ ({m.get('first_payment_pct', 0)}%)")
            lines.append(f"  Сумма кредита: {m.get('credit_amount_rub', 0):,.0f} ₽")
            lines.append(f"  Срок: {m.get('term_months', 0)} мес")
        lines.append("")

    # === Extra notes ===
    if extra_notes:
        lines.append("=== ДОПОЛНИТЕЛЬНО ===")
        for key, val in extra_notes.items():
            if isinstance(val, str):
                lines.append(f"• {val}")
        lines.append("")

    return "\n\n" + "\n".join(lines)


def build_system_prompt() -> str:
    """Build full system prompt = instructions + finance context."""
    instructions = load_instructions()
    finance = load_finance()
    context = build_finance_system_context(finance)
    return instructions + context


def stream_chat_response(message: str, history: list[dict], actions: list[dict] | None = None):
    """Generator that yields SSE events from OpenAI streaming response.

    Yields strings in SSE format: 'data: {"type": "token", "content": "..."}\n\n'
    If actions are provided, yields them as a final "actions" event after streaming.
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

        # Append action buttons after streaming completes
        if actions:
            yield f'data: {json.dumps({"type": "actions", "actions": actions}, ensure_ascii=False)}\n\n'

        yield f'data: {json.dumps({"type": "done", "content": ""})}\n\n'

    except Exception as e:
        logger.error(f"[AI CHAT] OpenAI error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "AI временно недоступен, попробуйте позже"}, ensure_ascii=False)}\n\n'


def analyze_user_intent(message: str) -> dict | None:
    """Analyze message intent and classify it.

    Returns:
    - For navigation intents: dict with type="action" (JSON response)
    - For enriched intents: dict with type="enriched" + actions list (stream AI + buttons)
    - None: pure chat, no intent detected
    """
    intent, params = classify_intent(message)

    if intent == "chat" or intent not in INTENT_ACTIONS:
        return None

    actions = INTENT_ACTIONS[intent](params)

    # Navigation intents → return JSON immediately
    if intent in NAVIGATION_INTENTS:
        msg_text = NAVIGATION_MESSAGES.get(intent, "")
        return {
            "type": "action",
            "intent": intent,
            "params": params,
            "message": msg_text,
            "actions": actions,
        }

    # Enriched intents → stream AI response + append action buttons
    return {
        "type": "enriched",
        "intent": intent,
        "params": params,
        "actions": actions,
    }
