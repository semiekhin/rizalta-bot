"""AI Chat service — OpenAI streaming with function calling for RIZALTA webapp."""

import os
import json
import logging
from openai import OpenAI

from services.data_loader import load_finance, load_instructions
from services.tool_definitions import TOOLS, execute_tool

logger = logging.getLogger(__name__)

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
    """Build financial context from rizalta_finance.json for the system prompt."""
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

    if mortgages:
        lines.append("=== ИПОТЕКА ===")
        for m in mortgages:
            lines.append(f"• {m.get('name', '')}")
            lines.append(f"  Стоимость: {m.get('object_price_rub', 0):,.0f} ₽")
            lines.append(f"  ПВ: {m.get('first_payment_rub', 0):,.0f} ₽ ({m.get('first_payment_pct', 0)}%)")
            lines.append(f"  Сумма кредита: {m.get('credit_amount_rub', 0):,.0f} ₽")
            lines.append(f"  Срок: {m.get('term_months', 0)} мес")
        lines.append("")

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


TOOL_INSTRUCTION = """

Ты имеешь доступ к инструментам (tools) для работы с базой данных RIZALTA:
- search_lots: поиск лотов по фильтрам (корпус, площадь, цена, статус)
- get_lot_details: полная информация о конкретном лоте
- calculate_roi: расчёт инвестиционной доходности

ПРАВИЛА ИСПОЛЬЗОВАНИЯ TOOLS:
1. Если пользователь спрашивает о конкретном лоте — вызови get_lot_details
2. Если спрашивает "что есть" / "какие лоты" / фильтрует — вызови search_lots
3. Если спрашивает о доходности — вызови calculate_roi
4. Если просто разговаривает или задаёт общий вопрос — отвечай без tools
5. Используй данные из tools для ТОЧНОГО ответа. НЕ выдумывай цифры.
6. Форматируй цены с пробелами: 5 000 000 ₽
"""


def stream_chat_with_tools(message: str, history: list[dict]):
    """Generator yielding SSE events. Supports OpenAI function calling.

    SSE event types:
    - {"type": "token", "content": "..."}      — text chunk
    - {"type": "thinking", "tool": "..."}       — tool is being called
    - {"type": "actions", "actions": [...]}     — action buttons
    - {"type": "done"}                          — stream complete
    - {"type": "error", "content": "..."}       — error
    """
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

    system_prompt = build_system_prompt() + TOOL_INSTRUCTION

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(history[-20:])

    messages.append({"role": "user", "content": message})

    try:
        client = get_client()

        # === FIRST call — with tools ===
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            tools=TOOLS,
            tool_choice="auto",
            stream=True,
        )

        collected_tool_calls = {}  # index → {id, name, arguments}
        has_tool_calls = False

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Text content — stream immediately
            if delta.content:
                yield f'data: {json.dumps({"type": "token", "content": delta.content}, ensure_ascii=False)}\n\n'

            # Tool calls — accumulate
            if delta.tool_calls:
                has_tool_calls = True
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in collected_tool_calls:
                        collected_tool_calls[idx] = {
                            "id": tc.id or "",
                            "name": tc.function.name or "",
                            "arguments": ""
                        }
                    if tc.id:
                        collected_tool_calls[idx]["id"] = tc.id
                    if tc.function.name:
                        collected_tool_calls[idx]["name"] = tc.function.name
                    if tc.function.arguments:
                        collected_tool_calls[idx]["arguments"] += tc.function.arguments

        # === If tool calls — execute and make SECOND call ===
        if has_tool_calls and collected_tool_calls:

            tool_calls_for_message = []
            for idx in sorted(collected_tool_calls.keys()):
                tc = collected_tool_calls[idx]
                tool_calls_for_message.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                })

            messages.append({
                "role": "assistant",
                "tool_calls": tool_calls_for_message,
            })

            # Execute each tool call
            for tc in tool_calls_for_message:
                tool_name = tc["function"]["name"]

                thinking_labels = {
                    "search_lots": "Ищу лоты...",
                    "get_lot_details": "Загружаю информацию о лоте...",
                    "calculate_roi": "Считаю доходность...",
                }
                label = thinking_labels.get(tool_name, f"Выполняю {tool_name}...")
                yield f'data: {json.dumps({"type": "thinking", "tool": tool_name, "label": label}, ensure_ascii=False)}\n\n'

                result = execute_tool(tool_name, tc["function"]["arguments"])

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

            # === SECOND call — stream final answer ===
            response2 = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                stream=True,
            )

            for chunk in response2:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    yield f'data: {json.dumps({"type": "token", "content": token}, ensure_ascii=False)}\n\n'

        # === Generate action buttons based on context ===
        actions = _generate_context_actions(collected_tool_calls if has_tool_calls else {})
        if actions:
            yield f'data: {json.dumps({"type": "actions", "actions": actions}, ensure_ascii=False)}\n\n'

        yield f'data: {json.dumps({"type": "done", "content": ""})}\n\n'

    except Exception as e:
        logger.error(f"[AI CHAT] Error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "AI временно недоступен, попробуйте позже"}, ensure_ascii=False)}\n\n'


def _generate_context_actions(tool_calls: dict) -> list[dict]:
    """Generate action buttons based on which tools were used."""
    actions = []

    for idx, tc in tool_calls.items():
        name = tc.get("name", "")
        try:
            args = json.loads(tc.get("arguments", "{}"))
        except json.JSONDecodeError:
            args = {}

        if name == "get_lot_details" and args.get("code"):
            code = args["code"]
            building_param = f"&building={args['building']}" if args.get("building") else ""
            actions.append({
                "label": f"Открыть {code}",
                "type": "navigate",
                "to": f"/lots/{code}?from=chat{building_param}"
            })

        elif name == "search_lots":
            actions.append({
                "label": "Открыть каталог",
                "type": "navigate",
                "to": "/lots"
            })

        elif name == "calculate_roi" and args.get("code"):
            code = args["code"]
            actions.append({
                "label": f"Подробный расчёт {code}",
                "type": "navigate",
                "to": f"/lots/{code}?modal=roi"
            })

    # Deduplicate
    seen = set()
    unique = []
    for a in actions:
        key = a["to"]
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:3]
