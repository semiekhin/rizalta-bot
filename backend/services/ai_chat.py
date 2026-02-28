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


ADVISOR_INSTRUCTION = """

Ты — AI финансовый советник RIZALTA Resort Belokurikha.
Твоя задача — помочь риэлтору подобрать оптимальную инвестиционную стратегию для клиента.

## ДОСТУПНЫЕ ИНСТРУМЕНТЫ

- search_lots: поиск лотов по фильтрам (корпус, площадь, цена, статус)
- get_lot_details: полная информация о конкретном лоте
- calculate_roi: расчёт ROI за 11 лет (2025-2035)
- calculate_installment: варианты рассрочки (12 мес 0%, 18 мес с удорожанием)
- compare_with_deposit: сравнение RIZALTA vs банковский депозит

## СТРАТЕГИЧЕСКИЙ ПОДХОД

При запросе "портфель на X млн" или "бюджет X" — ОБЯЗАТЕЛЬНО:

1. **Найди подходящие лоты** (search_lots с фильтрами)
2. **Рассмотри минимум 2 стратегии:**
   - Стратегия A: Один лот за 100% → остаток на депозит
   - Стратегия B: Два лота в рассрочку (ПВ 30%) → cash flow анализ
   - Стратегия C (если бюджет позволяет): Три лота с минимальным ПВ
3. **Для каждой стратегии рассчитай:**
   - ROI каждого лота (calculate_roi)
   - Условия рассрочки (calculate_installment)
   - Сравнение с депозитом (compare_with_deposit)
   - Cash flow: ежемесячные расходы до 2028 vs арендный доход с 2028
   - Точку безубыточности
4. **Дай рекомендацию** с обоснованием

## CASH FLOW АНАЛИЗ

- До Q4 2027: только расходы (рассрочка) — дом строится
- С 2028: начинается аренда (загрузка 40% первый год, 60-70% далее)
- Расходы на эксплуатацию: 50% от валового дохода
- Рассрочка 12 мес: платежи заканчиваются через год
- Рассрочка 18 мес: платежи до середины 2027

## ФОРМАТ ОТВЕТА

Отвечай структурированно:
- Используй заголовки: **Стратегия 1**, **Стратегия 2**
- Указывай конкретные цифры с форматированием: 14 300 000 ₽
- В конце — чёткая рекомендация
- НЕ используй эмодзи в финансовых отчётах
- При расчёте ROI для нескольких лотов — показывай совокупный ROI портфеля

## ПРАВИЛА

1. ВСЕГДА используй tools для получения данных — НЕ выдумывай цифры
2. Цены и площади — только из БД через tools
3. Если код лота дублируется — уточни корпус
4. Форматируй цены с пробелами: 14 300 000 ₽
5. При бюджете инвестора — рассмотри комбинации, не только одиночные лоты
"""


def stream_chat_with_tools(message: str, history: list[dict]):
    """Generator yielding SSE events. GPT-5.2 Responses API with agentic loop.

    Flow: up to MAX_ROUNDS of tool calls, then stream final text answer.

    SSE event types:
    - {"type": "token", "content": "..."}
    - {"type": "thinking", "tool": "...", "label": "..."}
    - {"type": "actions", "actions": [...]}
    - {"type": "strategy_data", "data": {...}}   — data for PDF
    - {"type": "done"}
    - {"type": "error", "content": "..."}
    """
    model = os.getenv("OPENAI_MODEL", "gpt-5.2")
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))

    system_prompt = build_system_prompt() + ADVISOR_INSTRUCTION

    input_messages = []
    if history:
        input_messages.extend(history[-20:])
    input_messages.append({"role": "user", "content": message})

    strategy_data = {"tools_used": [], "results": {}}

    try:
        client = get_client()

        # === AGENTIC LOOP — up to 5 rounds of tool calls ===
        MAX_ROUNDS = 5
        current_input = list(input_messages)
        tool_calls = []

        for round_num in range(MAX_ROUNDS):
            response = client.responses.create(
                model=model,
                instructions=system_prompt,
                input=current_input,
                tools=TOOLS,
                reasoning={"effort": "high"},
                max_output_tokens=max_tokens,
            )

            tool_calls = [item for item in response.output if item.type == "function_call"]

            if not tool_calls:
                # No tool calls — model is ready to answer
                break

            # Execute tool calls, append to current_input
            for item in response.output:
                current_input.append(item)
                if item.type == "function_call":
                    thinking_labels = {
                        "search_lots": "Ищу подходящие лоты...",
                        "get_lot_details": "Загружаю информацию о лоте...",
                        "calculate_roi": "Считаю доходность...",
                        "calculate_installment": "Рассчитываю варианты рассрочки...",
                        "compare_with_deposit": "Сравниваю с депозитом...",
                    }
                    label = thinking_labels.get(item.name, f"Выполняю {item.name}...")
                    yield f'data: {json.dumps({"type": "thinking", "tool": item.name, "label": label}, ensure_ascii=False)}\n\n'

                    result = execute_tool(item.name, item.arguments)

                    strategy_data["tools_used"].append(item.name)
                    try:
                        strategy_data["results"][f"{item.name}_{len(strategy_data['results'])}"] = json.loads(result)
                    except Exception:
                        pass

                    current_input.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": result,
                    })

        # === FINAL streaming response ===
        if response.output_text and not tool_calls:
            # Last response already has text (no tool calls) — send it
            text = response.output_text
            chunk_size = 4
            for i in range(0, len(text), chunk_size):
                yield f'data: {json.dumps({"type": "token", "content": text[i:i+chunk_size]}, ensure_ascii=False)}\n\n'
        else:
            # Hint to model: stop calling tools, write text response
            current_input.append({
                "role": "user",
                "content": "Все данные собраны. Сформируй финальный инвестиционный отчёт на основе полученных данных. Отвечай текстом, не вызывай инструменты."
            })

            # Stream final answer WITHOUT tools (so model only responds)
            stream = client.responses.create(
                model=model,
                instructions=system_prompt,
                input=current_input,
                reasoning={"effort": "high"},
                max_output_tokens=max_tokens,
                stream=True,
            )

            full_response_text = ""
            for event in stream:
                if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                    full_response_text += event.delta
                    yield f'data: {json.dumps({"type": "token", "content": event.delta}, ensure_ascii=False)}\n\n'

            if full_response_text:
                strategy_data["response_text"] = full_response_text

        # Strategy data for PDF
        strategy_data["user_query"] = message
        if len(strategy_data["tools_used"]) >= 2:
            yield f'data: {json.dumps({"type": "strategy_data", "data": strategy_data}, ensure_ascii=False)}\n\n'

        # Actions — collect all function_call items from current_input
        all_tool_items = [item for item in current_input if hasattr(item, 'type') and getattr(item, 'type', '') == 'function_call']
        actions = _generate_context_actions(all_tool_items)
        if actions:
            yield f'data: {json.dumps({"type": "actions", "actions": actions}, ensure_ascii=False)}\n\n'

        yield f'data: {json.dumps({"type": "done", "content": ""})}\n\n'

    except Exception as e:
        logger.error(f"[AI CHAT] GPT-5.2 error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "AI временно недоступен, попробуйте позже"}, ensure_ascii=False)}\n\n'


def _generate_context_actions(tool_items: list) -> list[dict]:
    """Generate action buttons based on which tools were used."""
    actions = []

    for item in tool_items:
        name = item.name
        try:
            args = json.loads(item.arguments) if isinstance(item.arguments, str) else {}
        except Exception:
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
        if a["to"] not in seen:
            seen.add(a["to"])
            unique.append(a)

    return unique[:3]
