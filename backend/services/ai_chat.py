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

Ты — AI финансовый консультант RIZALTA Resort Belokurikha.
Пользователи — риэлторы и отдел продаж. Они УЖЕ общаются с клиентами.

## ТВОЯ РОЛЬ

Помогай риэлтору:
- Аргументировать преимущества RIZALTA перед депозитом/акциями/другой недвижимостью
- Отвечать на сложные финансовые вопросы клиентов
- Сравнивать варианты и давать рекомендации
- Объяснять финансовые концепции простым языком

## ДОСТУПНЫЕ ИНСТРУМЕНТЫ

- search_lots: поиск лотов по фильтрам
- get_lot_details: информация о лоте
- calculate_roi: расчёт ROI за 11 лет
- calculate_installment: варианты рассрочки
- compare_with_deposit: сравнение с депозитом

## ФОРМАТ ОТВЕТА

- Компактно: не больше 1 экрана
- Конкретные цифры (через tools)
- "лот"/"апартамент", НИКОГДА "юнит"
- НЕ предлагай связаться с отделом продаж (пользователь = отдел продаж)
- НЕ проси контакты клиента
- Капитализация: +20%/год стройка, +10%/год после сдачи

## ВАЖНО

Для стандартных отчётов есть кнопки "Фин. отчёт по лоту" и "Портфель по бюджету".
В свободном чате фокусируйся на АНАЛИЗЕ и АРГУМЕНТАЦИИ, а не на генерации отчётов.
"""


LOT_REPORT_PROMPT = """Ты — профессиональный инвестиционный аналитик RIZALTA Resort Belokurikha.

Напиши полноценный инвестиционный отчёт по апартаменту (400-600 слов). НЕ используй # заголовки, используй **жирный текст** для разделов.

Структура отчёта:

**Инвестиционный профиль** — кратко о лоте (площадь, этаж, корпус, ценовая категория)

**Ключевые инвестиционные метрики (2030)** — NOI: {noi} ₽/год, Cap Rate: {cap_rate}%, Cash-on-Cash при 100% оплате: {coc_full}%, Cash-on-Cash при рассрочке 30%: {coc_installment}%. Объясни значение этих метрик для инвестора.

**Доходность за 11 лет** — ROI {roi_pct}%, среднегодовая {avg_annual}%. Структура дохода: аренда vs капитализация. Когда окупается вложение.

**Сценарии входа** — 100% оплата (скидка 5%), рассрочка 12 мес (0%), рассрочка 18 мес (+9%). Equity Multiple для каждого варианта: {equity_multiple}x. Какой вариант оптимален.

**Стратегия покупки** — для какого профиля инвестора подходит: консервативный, сбалансированный, агрессивный. Рекомендуемый сценарий.

**Риски и ограничения** — строительный риск (до сдачи {completion}), ликвидность, зависимость от загрузки.

**Вывод** — итоговая рекомендация в 2-3 предложениях.

Используй термин "апартамент" или "лот", НИКОГДА "юнит". НЕ предлагай связаться с менеджером. Пиши для риэлтора, который покажет этот отчёт клиенту."""

PORTFOLIO_PROMPT = """Ты — профессиональный инвестиционный аналитик RIZALTA Resort Belokurikha.

Напиши полноценный портфельный анализ для бюджета {budget} ₽ (500-800 слов). НЕ используй # заголовки, используй **жирный текст** для разделов.

Структура:

**Профиль клиента** — бюджет, возможности (100% оплата vs рассрочка), инвестиционный горизонт 11 лет.

**Стратегия A: 100% оплата** — какие лоты доступны, скидка 5%, мгновенный доход от аренды. Cap Rate и Cash-on-Cash лучших вариантов.

**Стратегия B: Рассрочка 30%** — какие лоты доступны при ПВ = бюджет, больший выбор, финансовый рычаг. Cash-on-Cash при рассрочке.

**Сравнительная таблица стратегий** — кратко: преимущества и недостатки каждой.

**Сценарии доходности** — базовый (60% загрузка), оптимистичный (70%), консервативный (50%). Как меняется доходность.

**RIZALTA vs Депозит** — сравни доходность RIZALTA с банковским вкладом на те же 11 лет. Где выше доходность, где выше риски.

**Рекомендация** — оптимальная стратегия для этого бюджета, обоснование.

Используй термин "апартамент" или "лот", НИКОГДА "юнит". НЕ предлагай связаться с менеджером. Пиши для риэлтора, который покажет этот анализ клиенту."""


PORTFOLIO_PROMPT_V2 = """Ты — профессиональный инвестиционный аналитик RIZALTA Resort Belokurikha.

Напиши портфельный анализ для бюджета {budget} ₽ по 3 сценариям (500-800 слов). НЕ используй # заголовки, используй **жирный текст** для разделов. НЕ используй markdown таблицы с |---|.

Структура:

**Инвестиционный профиль** — бюджет клиента, горизонт 11 лет, три стратегии от консервативной до агрессивной.

**Сценарий 1: Один премиальный лот** — описание лота, скидка 5% при полной оплате, NOI и Cap Rate, ROI за 11 лет. Плюсы: простота управления, лучшее качество. Минусы: весь капитал в одном активе.

**Сценарий 2: Портфель 100% оплата** — сколько лотов уместилось, средний ROI, суммарный NOI. Плюсы: диверсификация, скидка 5% на каждый лот. Минусы: более дешёвые лоты.

**Сценарий 3: Максимальное плечо (рассрочка)** — сколько лотов при 30% ПВ, финансовый рычаг, суммарный портфель, переплата по рассрочке, чистая прибыль за вычетом переплаты. Плюсы: максимум активов, высокий CoC. Минусы: обязательства по рассрочке.

**Сравнение сценариев** — кратко: вложено, количество лотов, суммарный NOI, прибыль за 11 лет, выгода vs депозит для каждого.

**RIZALTA vs Депозит** — депозит на 11 лет для сравнения. Преимущество лучшего сценария.

**Рекомендация** — для какого профиля инвестора оптимален каждый сценарий: консервативный (сценарий 1), сбалансированный (сценарий 2), агрессивный (сценарий 3).

Используй термин "апартамент" или "лот", НИКОГДА "юнит". НЕ предлагай связаться с менеджером. Пиши для риэлтора, который покажет этот анализ клиенту."""


# ---------------------------------------------------------------------------
# Level 3: AI-driven portfolio selection
# ---------------------------------------------------------------------------

AI_PORTFOLIO_SELECTOR_PROMPT = """Ты — инвестиционный аналитик RIZALTA Resort Belokurikha.

Клиент хочет инвестировать {budget} ₽. Отранжируй лоты для 3 инвестиционных сценариев.

{lots_table}

⚠️ НЕ СЧИТАЙ БЮДЖЕТ. Не складывай цены. Просто расставь лоты по приоритету — от лучшего к худшему. Бюджетом займётся Python.

## Критерии ранжирования:

### Сценарий 1 — «Один премиальный лот» (100% оплата, скидка 5%)
- Один лучший лот для единичной покупки
- Приоритет: большая площадь > высокий этаж > корпус К1/К2 > высокий Cap Rate

### Сценарий 2 — «Портфель 100%» (несколько лотов, 100% оплата)
- Приоритет: ДИВЕРСИФИКАЦИЯ (разные корпуса, этажи, площади)
- НЕ ставь рядом 2 лота с одинаковой площадью и ценой
- Чередуй корпуса: К1, К2, К3, К1, К2...
- Предпочитай лоты с высоким Cap Rate

### Сценарий 3 — «Максимальное плечо» (рассрочка, ПВ 30%)
- Приоритет: максимум разных лотов, диверсификация
- Чередуй корпуса и этажи
- Предпочитай лоты с высоким CoC30%

## Формат ответа — СТРОГО JSON, ничего кроме JSON:

{{
  "scenario_1": {{
    "lots": ["ЛУЧШИЙ_КОД"],
    "reasoning": "Почему именно этот лот (1-2 предложения)"
  }},
  "scenario_2": {{
    "lots": ["КОД1", "КОД2", "КОД3", "КОД4", "КОД5", "..."],
    "reasoning": "Логика ранжирования (1-2 предложения)"
  }},
  "scenario_3": {{
    "lots": ["КОД1", "КОД2", "КОД3", "КОД4", "КОД5", "КОД6", "..."],
    "reasoning": "Логика ранжирования (1-2 предложения)"
  }}
}}

ВАЖНО: В сценариях 2 и 3 перечисли ВСЕ подходящие лоты (до 20), отсортированные от лучшего к худшему. Python сам отберёт сколько влезет в бюджет.
"""


PORTFOLIO_PROMPT_V3 = """Ты — профессиональный инвестиционный аналитик RIZALTA Resort Belokurikha.

AI-аналитик подобрал оптимальные лоты для бюджета {budget} ₽ по 3 сценариям. Напиши инвестиционную стратегию (500-800 слов). НЕ используй # заголовки, используй **жирный текст** для разделов. НЕ используй markdown таблицы с |---|.

Структура:

**Инвестиционный профиль** — бюджет клиента, горизонт 11 лет, три стратегии от консервативной до агрессивной.

**Сценарий 1: Один премиальный лот** — описание лота, ПОЧЕМУ выбран именно этот лот (используй reasoning из данных). Скидка 5% при полной оплате, NOI и Cap Rate, ROI за 11 лет. Плюсы: простота управления. Минусы: весь капитал в одном активе.

**Сценарий 2: Портфель 100% оплата** — какие лоты выбраны и ПОЧЕМУ именно эти (используй reasoning). Диверсификация по корпусам/этажам. Средний ROI, суммарный NOI. Плюсы: разнообразие активов. Минусы: меньшие лоты.

**Сценарий 3: Максимальное плечо (рассрочка)** — сколько лотов при 30% ПВ, ПОЧЕМУ выбраны эти (reasoning). Финансовый рычаг, суммарный портфель, переплата по рассрочке, чистая прибыль. Плюсы: максимум активов, высокий CoC. Минусы: обязательства по рассрочке.

**Сравнение сценариев** — кратко: вложено, количество лотов, суммарный NOI, прибыль за 11 лет, выгода vs депозит.

**RIZALTA vs Депозит** — депозит на 11 лет для сравнения. Преимущество лучшего сценария.

**Рекомендация** — для какого профиля инвестора оптимален каждый: консервативный (1), сбалансированный (2), агрессивный (3).

Используй термин "апартамент" или "лот", НИКОГДА "юнит". НЕ предлагай связаться с менеджером. Пиши для риэлтора, который покажет этот анализ клиенту."""


def select_portfolio_lots(budget: int, lots_table: str) -> dict | None:
    """AI selector: gpt-4o-mini picks lots for 3 scenarios.

    Returns parsed JSON with scenario_1/2/3 (lots + reasoning) or None on error.
    """
    client = get_client()

    prompt = AI_PORTFOLIO_SELECTOR_PROMPT.format(
        budget=f"{budget:,}",
        lots_table=lots_table,
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты инвестиционный аналитик. Отвечай ТОЛЬКО JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        # Basic validation: must have at least one scenario with lots
        if not any(result.get(f"scenario_{i}", {}).get("lots") for i in (1, 2, 3)):
            logger.warning("[AI SELECTOR] No scenarios with lots in response")
            return None

        return result

    except Exception as e:
        logger.error(f"[AI SELECTOR] Error: {e}")
        return None


def format_lot_summary(data: dict) -> str:
    """Превращает JSON report_builder в читаемую сводку для AI."""
    lot = data["lot"]
    roi = data["roi"]
    inst = data["installment"]
    dep = data["deposit_comparison"]
    proj = data["project"]

    def fmt(v):
        return f"{int(round(v)):,}".replace(",", " ")

    code = lot.get("code", "")
    building_num = lot.get("building_num", "")
    bnames = {1: "Family", 2: "Business", 3: "Digital"}
    bname = f'Корпус {building_num} "{bnames.get(building_num, "")}"' if building_num else lot.get("building", "")
    area = lot.get("area_m2", 0)
    floor = lot.get("floor", "?")
    price = lot.get("price_rub", 0)

    # ROI fields (from execute_calculate_roi → slim_roi)
    total_rental = roi.get("total_rental_income", 0)
    total_growth = roi.get("total_growth", 0)
    total_profit = roi.get("total_profit_rub", 0)
    roi_pct = roi.get("roi_pct", 0)
    avg_annual = roi.get("avg_annual_pct", 0)
    final_value = roi.get("final_value_rub", 0)

    # Installment
    full = inst.get("full_payment", {})
    i12 = inst.get("installment_12m", {})
    i18 = inst.get("installment_18m", {})

    # Deposit
    dep_base = dep.get("base", {})

    lines = [
        f"АПАРТАМЕНТ: {code}, {bname}",
        f"Площадь: {area} м², этаж {floor}",
        f"Цена: {fmt(price)} ₽",
        f"Точка входа (ПВ 30%): {fmt(price * 0.3)} ₽",
        "",
        "ДОХОДНОСТЬ (11 лет, 2025-2035):",
        f"Аренда за 11 лет: {fmt(total_rental)} ₽",
        f"Рост стоимости за 11 лет: {fmt(total_growth)} ₽",
        f"Совокупная прибыль: {fmt(total_profit)} ₽",
        f"ROI: {roi_pct:.1f}%, среднегодовая: {avg_annual:.1f}%",
        f"Стоимость актива через 11 лет: {fmt(final_value)} ₽",
        f"Капитализация: +20%/год (стройка до {proj['completion']}), +10%/год после",
        f"Аренда: тариф {fmt(proj['daily_rate'])} ₽/сутки, загрузка {proj['occupancy']}%, расходы {proj['expenses']}%",
        "",
        "ВАРИАНТЫ ОПЛАТЫ:",
    ]

    # 100% payment
    if full:
        price_95 = int(price * 0.95)
        discount = price - price_95
        lines.append(f"100% оплата: {fmt(price_95)} ₽ (скидка 5% = {fmt(discount)} ₽)")

    # 12 month installment
    if i12:
        lines.append(f"Рассрочка 12 мес (0%): ПВ 30% = {fmt(i12.get('pv_30', 0))} ₽, платёж {fmt(i12.get('monthly_30', 0))} ₽/мес")

    # 18 month installment
    if i18:
        markup = i18.get("markup_30", 0)
        final_18 = i18.get("final_price_30", 0)
        lines.append(f"Рассрочка 18 мес (+9%): ПВ 30% = {fmt(i18.get('pv_30', 0))} ₽, платёж {fmt(i18.get('monthly_30', 0))} ₽/мес, итого {fmt(final_18)} ₽ (переплата {fmt(markup)} ₽)")

    # Investment metrics (2030)
    metrics = data.get("metrics", {})
    if metrics:
        lines.append("")
        lines.append("ИНВЕСТИЦИОННЫЕ МЕТРИКИ (стабилизированный 2030):")
        lines.append(f"NOI: {fmt(metrics.get('noi', 0))} ₽/год")
        lines.append(f"Cap Rate: {metrics.get('cap_rate', 0):.1f}%")
        lines.append(f"Cash-on-Cash (100% оплата): {metrics.get('coc_full', 0):.1f}%")
        lines.append(f"Cash-on-Cash (рассрочка 30%): {metrics.get('coc_installment', 0):.1f}%")
        lines.append(f"Equity Multiple (100%): {metrics.get('equity_multiple_full', 0):.2f}x")
        lines.append(f"Equity Multiple (рассрочка): {metrics.get('equity_multiple_installment', 0):.2f}x")

    lines.append("")
    lines.append("СРАВНЕНИЕ С ДЕПОЗИТОМ (та же сумма на вкладе, 11 лет):")
    if dep_base:
        dep_final = dep_base.get("final_balance", 0)
        dep_interest = dep_base.get("total_net_interest", 0)
        dep_roi = dep_base.get("total_roi_pct", 0)
        lines.append(f"Депозит (базовый): капитал {fmt(dep_final)} ₽, проценты {fmt(dep_interest)} ₽, ROI {dep_roi:.0f}%")
        lines.append(f"RIZALTA: прибыль {fmt(total_profit)} ₽, ROI {roi_pct:.0f}%, актив {fmt(final_value)} ₽")
        advantage = total_profit - dep_interest
        lines.append(f"Преимущество RIZALTA: +{fmt(advantage)} ₽")

    return "\n".join(lines)


def format_portfolio_summary(data: dict, budget: int) -> str:
    """Текстовая сводка для портфельного отчёта."""
    def fmt(v):
        return f"{int(round(v)):,}".replace(",", " ")

    lines = [f"БЮДЖЕТ КЛИЕНТА: {fmt(budget)} ₽", ""]

    # Стратегия A
    metrics_map = data.get("metrics", {})

    sa = data.get("strategy_a", {})
    lots_a = sa.get("lots", {}).get("lots", [])
    lines.append(f"СТРАТЕГИЯ A: {sa.get('name', '100% оплата')}")
    if lots_a:
        for lot in lots_a[:3]:
            code = lot.get("code", "")
            area = lot.get("area_m2", 0)
            price = lot.get("price_rub", 0)
            roi_data = data.get("roi", {}).get(code, {})
            roi_pct = roi_data.get("roi_pct", 0)
            m = metrics_map.get(code, {})
            cap = m.get("cap_rate", 0)
            coc = m.get("coc_full", 0)
            lines.append(f"  {code}: {area} м², {fmt(price)} ₽, ROI {roi_pct:.0f}%, Cap Rate {cap:.1f}%, CoC {coc:.1f}%")
    else:
        lines.append("  Нет подходящих лотов в этом бюджете")

    lines.append("")

    # Стратегия B
    sb = data.get("strategy_b", {})
    lots_b = sb.get("lots", {}).get("lots", [])
    lines.append(f"СТРАТЕГИЯ B: {sb.get('name', 'Рассрочка')}")
    lines.append(f"  Макс. цена лота: {fmt(sb.get('max_lot_price', 0))} ₽")
    if lots_b:
        for lot in lots_b[:3]:
            code = lot.get("code", "")
            area = lot.get("area_m2", 0)
            price = lot.get("price_rub", 0)
            roi_data = data.get("roi", {}).get(code, {})
            roi_pct = roi_data.get("roi_pct", 0)
            m = metrics_map.get(code, {})
            cap = m.get("cap_rate", 0)
            coc = m.get("coc_installment", 0)
            lines.append(f"  {code}: {area} м², {fmt(price)} ₽, ROI {roi_pct:.0f}%, Cap Rate {cap:.1f}%, CoC 30% {coc:.1f}%")
    else:
        lines.append("  Нет подходящих лотов")

    lines.append("")

    # Депозит
    dep = data.get("deposit_comparison", {})
    dep_base = dep.get("base", {})
    if dep_base:
        lines.append("ДЕПОЗИТ ДЛЯ СРАВНЕНИЯ:")
        dep_final = dep_base.get("final_balance", 0)
        dep_interest = dep_base.get("total_net_interest", 0)
        dep_roi = dep_base.get("total_roi_pct", 0)
        lines.append(f"  {fmt(budget)} ₽ на вкладе 11 лет → {fmt(dep_final)} ₽ (проценты {fmt(dep_interest)} ₽, ROI {dep_roi:.0f}%)")

    return "\n".join(lines)


def format_portfolio_summary_v2(data: dict, budget: int) -> str:
    """Text summary for v2 portfolio report (3 scenarios)."""
    def fmt(v):
        return f"{int(round(v)):,}".replace(",", " ")

    lines = [f"БЮДЖЕТ КЛИЕНТА: {fmt(budget)} ₽", ""]

    # Scenario 1: Premium
    sp = data.get("scenario_premium", {})
    lines.append(f"СЦЕНАРИЙ 1: {sp.get('name', 'Премиальный лот')}")
    lot = sp.get("lot")
    if lot:
        lines.append(f"  Лот: {lot['code']}, корпус {lot['building']}, {lot['area_m2']} м², этаж {lot['floor']}")
        lines.append(f"  Цена: {fmt(lot['price_rub'])} ₽, со скидкой 5%: {fmt(sp.get('discounted_price', 0))} ₽")
        lines.append(f"  Остаток: {fmt(sp.get('remaining_cash', 0))} ₽")
        m = sp.get("metrics", {})
        lines.append(f"  NOI: {fmt(m.get('noi', 0))} ₽/год, Cap Rate: {m.get('cap_rate', 0):.1f}%, CoC: {m.get('coc_full', 0):.1f}%")
        lines.append(f"  ROI 11 лет: {sp.get('roi_pct', 0):.1f}%, прибыль: {fmt(sp.get('total_profit', 0))} ₽")
        lines.append(f"  vs депозит: +{fmt(sp.get('vs_deposit', 0))} ₽")
    else:
        lines.append("  Нет подходящих лотов")
    lines.append("")

    # Scenario 2: Portfolio 100%
    sf = data.get("scenario_portfolio", {})
    lines.append(f"СЦЕНАРИЙ 2: {sf.get('name', 'Портфель 100%')}")
    lots_f = sf.get("lots", [])
    if lots_f:
        lines.append(f"  Лотов: {sf.get('lot_count', 0)}, вложено: {fmt(sf.get('total_invested', 0))} ₽")
        for l in lots_f[:5]:
            lines.append(f"    {l['code']}: {l['area_m2']} м², {fmt(l['price_rub'])} ₽, ROI {l['roi_pct']:.0f}%")
        lines.append(f"  Суммарный NOI: {fmt(sf.get('total_noi', 0))} ₽/год")
        lines.append(f"  Суммарная прибыль: {fmt(sf.get('total_profit', 0))} ₽, средний ROI: {sf.get('avg_roi_pct', 0):.1f}%")
        lines.append(f"  vs депозит: +{fmt(sf.get('vs_deposit', 0))} ₽")
    else:
        lines.append("  Нет подходящих лотов")
    lines.append("")

    # Scenario 3: Max leverage
    sl = data.get("scenario_leverage", {})
    lines.append(f"СЦЕНАРИЙ 3: {sl.get('name', 'Максимальное плечо')}")
    lots_l = sl.get("lots", [])
    if lots_l:
        lines.append(f"  Лотов: {sl.get('lot_count', 0)}, ПВ всего: {fmt(sl.get('total_down_payment', 0))} ₽")
        lines.append(f"  Стоимость портфеля: {fmt(sl.get('total_portfolio_value', 0))} ₽")
        for l in lots_l[:5]:
            lines.append(f"    {l['code']}: {fmt(l['price_rub'])} ₽, ПВ {fmt(l['down_payment'])} ₽, CoC {l['coc_installment']:.1f}%")
        lines.append(f"  Переплата рассрочка: {fmt(sl.get('total_markup', 0))} ₽")
        lines.append(f"  Суммарный NOI: {fmt(sl.get('total_noi', 0))} ₽/год")
        lines.append(f"  Чистая прибыль: {fmt(sl.get('net_profit', 0))} ₽")
        lines.append(f"  vs депозит: +{fmt(sl.get('vs_deposit', 0))} ₽")
    else:
        lines.append("  Нет подходящих лотов")
    lines.append("")

    # Deposit
    dep = data.get("deposit_comparison", {})
    dep_base = dep.get("base", {})
    if dep_base:
        lines.append("ДЕПОЗИТ ДЛЯ СРАВНЕНИЯ:")
        lines.append(f"  {fmt(budget)} ₽ на вкладе 11 лет → проценты {fmt(dep_base.get('total_net_interest', 0))} ₽, ROI {dep_base.get('total_roi_pct', 0):.0f}%")

    return "\n".join(lines)


def format_portfolio_summary_v3(data: dict, budget: int) -> str:
    """Text summary for v3 portfolio report (3 scenarios + AI reasoning)."""
    def fmt(v):
        return f"{int(round(v)):,}".replace(",", " ")

    lines = [f"БЮДЖЕТ КЛИЕНТА: {fmt(budget)} ₽", ""]

    # Scenario 1: Premium
    sp = data.get("scenario_premium", {})
    lines.append(f"СЦЕНАРИЙ 1: {sp.get('name', 'Премиальный лот')}")
    if sp.get("reasoning"):
        lines.append(f"  AI reasoning: {sp['reasoning']}")
    lot = sp.get("lot")
    if lot:
        lines.append(f"  Лот: {lot['code']}, К{lot.get('building', '?')}, {lot['area_m2']} м², этаж {lot.get('floor', '?')}")
        lines.append(f"  Цена: {fmt(lot['price_rub'])} ₽, со скидкой 5%: {fmt(sp.get('discounted_price', 0))} ₽")
        lines.append(f"  Остаток: {fmt(sp.get('remaining_cash', 0))} ₽")
        m = sp.get("metrics", {})
        lines.append(f"  NOI: {fmt(m.get('noi', 0))} ₽/год, Cap Rate: {m.get('cap_rate', 0):.1f}%, CoC: {m.get('coc_full', 0):.1f}%")
        lines.append(f"  ROI 11 лет: {sp.get('roi_pct', 0):.1f}%, прибыль: {fmt(sp.get('total_profit', 0))} ₽")
        lines.append(f"  vs депозит: +{fmt(sp.get('vs_deposit', 0))} ₽")
    else:
        lines.append("  Нет подходящих лотов")
    lines.append("")

    # Scenario 2: Portfolio 100%
    sf = data.get("scenario_portfolio", {})
    lines.append(f"СЦЕНАРИЙ 2: {sf.get('name', 'Портфель 100%')}")
    if sf.get("reasoning"):
        lines.append(f"  AI reasoning: {sf['reasoning']}")
    lots_f = sf.get("lots", [])
    if lots_f:
        lines.append(f"  Лотов: {sf.get('lot_count', 0)}, вложено: {fmt(sf.get('total_invested', 0))} ₽")
        for l in lots_f[:5]:
            lines.append(f"    {l['code']} К{l.get('building', '?')} эт.{l.get('floor', '?')}: {l['area_m2']} м², {fmt(l['price_rub'])} ₽, ROI {l['roi_pct']:.0f}%")
        lines.append(f"  Суммарный NOI: {fmt(sf.get('total_noi', 0))} ₽/год")
        lines.append(f"  Суммарная прибыль: {fmt(sf.get('total_profit', 0))} ₽, средний ROI: {sf.get('avg_roi_pct', 0):.1f}%")
        lines.append(f"  vs депозит: +{fmt(sf.get('vs_deposit', 0))} ₽")
    else:
        lines.append("  Нет подходящих лотов")
    lines.append("")

    # Scenario 3: Max leverage
    sl = data.get("scenario_leverage", {})
    lines.append(f"СЦЕНАРИЙ 3: {sl.get('name', 'Максимальное плечо')}")
    if sl.get("reasoning"):
        lines.append(f"  AI reasoning: {sl['reasoning']}")
    lots_l = sl.get("lots", [])
    if lots_l:
        lines.append(f"  Лотов: {sl.get('lot_count', 0)}, ПВ всего: {fmt(sl.get('total_down_payment', 0))} ₽")
        lines.append(f"  Стоимость портфеля: {fmt(sl.get('total_portfolio_value', 0))} ₽")
        for l in lots_l[:5]:
            lines.append(f"    {l['code']} К{l.get('building', '?')} эт.{l.get('floor', '?')}: {fmt(l['price_rub'])} ₽, ПВ {fmt(l['down_payment'])} ₽, CoC {l['coc_installment']:.1f}%")
        lines.append(f"  Переплата рассрочка: {fmt(sl.get('total_markup', 0))} ₽")
        lines.append(f"  Суммарный NOI: {fmt(sl.get('total_noi', 0))} ₽/год")
        lines.append(f"  Чистая прибыль: {fmt(sl.get('net_profit', 0))} ₽")
        lines.append(f"  vs депозит: +{fmt(sl.get('vs_deposit', 0))} ₽")
    else:
        lines.append("  Нет подходящих лотов")
    lines.append("")

    # Deposit
    dep = data.get("deposit_comparison", {})
    dep_base = dep.get("base", {})
    if dep_base:
        lines.append("ДЕПОЗИТ ДЛЯ СРАВНЕНИЯ:")
        lines.append(f"  {fmt(budget)} ₽ на вкладе 11 лет → проценты {fmt(dep_base.get('total_net_interest', 0))} ₽, ROI {dep_base.get('total_roi_pct', 0):.0f}%")

    return "\n".join(lines)


def stream_lot_report(code: str, building: int | None = None):
    """Быстрый фин. отчёт по лоту: 1 JSON → 1 вызов AI."""
    from services.report_builder import build_lot_report_data

    # Шаг 1: собрать данные (мгновенно, 0 токенов)
    yield f'data: {json.dumps({"type": "thinking", "tool": "report_builder", "label": "Собираю данные по лоту..."}, ensure_ascii=False)}\n\n'

    try:
        data = build_lot_report_data(code, building)
    except Exception as e:
        logger.error(f"[LOT REPORT] Data build error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "Ошибка сбора данных по лоту"}, ensure_ascii=False)}\n\n'
        return

    if "error" in data:
        err_msg = data["error"]
        yield f'data: {json.dumps({"type": "token", "content": f"Ошибка: {err_msg}"}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"type": "done"})}\n\n'
        return

    if data.get("multiple"):
        msg = data["message"]
        options = data["options"]
        text = f"{msg}\n" + "\n".join(f"- Корпус {o['building']}" for o in options)
        yield f'data: {json.dumps({"type": "token", "content": text}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"type": "done"})}\n\n'
        return

    # Шаг 2: отправить данные в карточку (мгновенно)
    yield f'data: {json.dumps({"type": "report_card", "card_type": "lot_report", "data": data}, ensure_ascii=False, default=str)}\n\n'

    # Шаг 3: AI пишет полноценный инвестиционный анализ
    yield f'data: {json.dumps({"type": "thinking", "tool": "ai", "label": "Формирую инвестиционный анализ..."}, ensure_ascii=False)}\n\n'

    model = os.getenv("OPENAI_MODEL", "gpt-5.2")

    summary = format_lot_summary(data)
    metrics = data.get("metrics", {})
    proj = data.get("project", {})
    prompt = LOT_REPORT_PROMPT.format(
        noi=f"{metrics.get('noi', 0):,}".replace(",", " "),
        cap_rate=metrics.get("cap_rate", 0),
        coc_full=metrics.get("coc_full", 0),
        coc_installment=metrics.get("coc_installment", 0),
        equity_multiple=metrics.get("equity_multiple_full", 0),
        roi_pct=metrics.get("roi_pct", 0),
        avg_annual=metrics.get("avg_annual_pct", 0),
        completion=proj.get("completion", 2027),
    ) + "\n\nСВОДКА:\n" + summary

    try:
        client = get_client()
        stream = client.responses.create(
            model=model,
            instructions="Ты финансовый аналитик RIZALTA.",
            input=[{"role": "user", "content": prompt}],
            reasoning={"effort": "low"},
            max_output_tokens=4000,
            stream=True,
        )

        for event in stream:
            if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                yield f'data: {json.dumps({"type": "token", "content": event.delta}, ensure_ascii=False)}\n\n'

    except Exception as e:
        logger.error(f"[LOT REPORT] AI error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "AI временно недоступен"}, ensure_ascii=False)}\n\n'
        return

    # Send strategy_data for PDF button
    strategy_data = {
        "tools_used": ["get_lot_details", "calculate_roi", "calculate_installment", "compare_with_deposit"],
        "results": {
            "get_lot_details_0": data.get("lot", {}),
            "calculate_roi_0": data.get("roi", {}),
        },
        "lot_data": data.get("lot", {}),
        "user_query": f"Фин. отчёт по лоту {code}",
        "report_data": data,
    }
    yield f'data: {json.dumps({"type": "strategy_data", "data": strategy_data}, ensure_ascii=False)}\n\n'

    # Кнопки
    actions = [
        {"label": f"Открыть {code}", "type": "navigate", "to": f"/lots/{code}?from=chat"},
    ]
    yield f'data: {json.dumps({"type": "actions", "actions": actions}, ensure_ascii=False)}\n\n'
    yield f'data: {json.dumps({"type": "done"})}\n\n'


def stream_portfolio_report(budget: int):
    """Level 3: AI selects lots → Python computes math → AI writes analysis.

    4 steps:
    1. Build data context (lots + metrics, 0 AI)
    2. AI selector (gpt-4o-mini) picks lots for 3 scenarios
    3. Python computes exact scenario math from selected codes
    4. AI analyst (gpt-5.2) writes investment strategy (streaming)

    Fallback: if AI selector fails → algorithmic v2 (build_portfolio_data_v2).
    """
    from services.report_builder import (
        build_portfolio_ai_context,
        build_portfolio_data_v2,
        _build_scenario_from_codes,
    )
    from services.data_loader import load_finance

    budget_fmt = f"{budget:,}".replace(",", " ")

    # ── Step 1: Build data context (instant, 0 AI tokens) ──
    yield f'data: {json.dumps({"type": "thinking", "tool": "report_builder", "label": "Загружаю данные лотов..."}, ensure_ascii=False)}\n\n'

    try:
        context = build_portfolio_ai_context(budget)
    except Exception as e:
        logger.error(f"[PORTFOLIO] Context build error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "Ошибка сбора данных для портфеля"}, ensure_ascii=False)}\n\n'
        return

    if not context["lots_enriched"]:
        yield f'data: {json.dumps({"type": "token", "content": "К сожалению, нет доступных лотов для данного бюджета."}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"type": "done"})}\n\n'
        return

    # ── Step 2: AI selector (gpt-4o-mini, ~2 sec) ──
    yield f'data: {json.dumps({"type": "thinking", "tool": "ai", "label": "AI подбирает оптимальные сценарии..."}, ensure_ascii=False)}\n\n'

    selection = select_portfolio_lots(budget, context["lots_table"])

    if not selection:
        # FALLBACK: use algorithmic v2
        logger.warning("[PORTFOLIO] AI selector failed, using algorithmic fallback")
        yield f'data: {json.dumps({"type": "thinking", "tool": "report_builder", "label": "Подбираю лоты алгоритмически..."}, ensure_ascii=False)}\n\n'
        try:
            data = build_portfolio_data_v2(budget)
        except Exception as e:
            logger.error(f"[PORTFOLIO] Fallback error: {e}")
            yield f'data: {json.dumps({"type": "error", "content": "Ошибка сбора данных для портфеля"}, ensure_ascii=False)}\n\n'
            return

        yield f'data: {json.dumps({"type": "report_card", "card_type": "portfolio_report_v2", "data": data}, ensure_ascii=False, default=str)}\n\n'
        yield f'data: {json.dumps({"type": "thinking", "tool": "ai", "label": "Формирую портфельный анализ..."}, ensure_ascii=False)}\n\n'

        summary = format_portfolio_summary_v2(data, budget)
        prompt = PORTFOLIO_PROMPT_V2.format(budget=budget_fmt) + "\n\nСВОДКА:\n" + summary
        yield from _stream_analyst(prompt, data, budget_fmt)
        return

    # ── Step 3: Python computes scenario math (instant, 0 AI tokens) ──
    yield f'data: {json.dumps({"type": "thinking", "tool": "report_builder", "label": "Рассчитываю метрики..."}, ensure_ascii=False)}\n\n'

    lots_enriched = context["lots_enriched"]
    valid_codes = {l["code"] for l in lots_enriched}

    scenario_configs = [
        ("scenario_1", "premium", "scenario_premium"),
        ("scenario_2", "full", "scenario_portfolio"),
        ("scenario_3", "installment", "scenario_leverage"),
    ]

    scenarios = {}
    for ai_key, payment_type, data_key in scenario_configs:
        ai_scenario = selection.get(ai_key, {})
        codes = [c for c in ai_scenario.get("lots", []) if c in valid_codes]
        reasoning = ai_scenario.get("reasoning", "")

        if codes:
            result = _build_scenario_from_codes(lots_enriched, codes, budget, payment_type)
            if result:
                result["reasoning"] = reasoning
                scenarios[data_key] = result
                continue

        # Empty scenario
        scenarios[data_key] = {"name": "", "error": "no_lots", "reasoning": reasoning}

    # Deposit comparison + vs_deposit
    deposit = context["deposit_raw"]
    dep_base_interest = deposit.get("base", {}).get("total_net_interest", 0) or 0

    for key in scenarios:
        s = scenarios[key]
        profit = s.get("total_profit", 0) or 0
        s["vs_deposit"] = profit - dep_base_interest

    finance = load_finance()
    data = {
        "budget": budget,
        "version": 2,
        "scenario_premium": scenarios.get("scenario_premium", {}),
        "scenario_portfolio": scenarios.get("scenario_portfolio", {}),
        "scenario_leverage": scenarios.get("scenario_leverage", {}),
        "deposit_comparison": deposit,
        "project": {
            "name": finance.get("project", "RIZALTA Resort Belokurikha"),
            "completion": finance.get("completion_year", 2027),
        },
    }

    # Send report card
    yield f'data: {json.dumps({"type": "report_card", "card_type": "portfolio_report_v2", "data": data}, ensure_ascii=False, default=str)}\n\n'

    # ── Step 4: AI analyst (gpt-5.2, streaming) ──
    yield f'data: {json.dumps({"type": "thinking", "tool": "ai", "label": "Формирую портфельный анализ..."}, ensure_ascii=False)}\n\n'

    summary = format_portfolio_summary_v3(data, budget)
    prompt = PORTFOLIO_PROMPT_V3.format(budget=budget_fmt) + "\n\nСВОДКА:\n" + summary
    yield from _stream_analyst(prompt, data, budget_fmt)


def _stream_analyst(prompt: str, data: dict, budget_fmt: str):
    """Stream AI analyst response + strategy_data + actions + done."""
    model = os.getenv("OPENAI_MODEL", "gpt-5.2")

    try:
        client = get_client()
        stream = client.responses.create(
            model=model,
            instructions="Ты финансовый аналитик RIZALTA.",
            input=[{"role": "user", "content": prompt}],
            reasoning={"effort": "low"},
            max_output_tokens=4000,
            stream=True,
        )

        for event in stream:
            if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                yield f'data: {json.dumps({"type": "token", "content": event.delta}, ensure_ascii=False)}\n\n'

    except Exception as e:
        logger.error(f"[PORTFOLIO] AI analyst error: {e}")
        yield f'data: {json.dumps({"type": "error", "content": "AI временно недоступен"}, ensure_ascii=False)}\n\n'
        return

    # Send strategy_data for PDF button
    strategy_data = {
        "tools_used": ["search_lots", "calculate_roi"],
        "results": {},
        "user_query": f"Портфель на {budget_fmt} ₽",
        "report_data": data,
    }
    yield f'data: {json.dumps({"type": "strategy_data", "data": strategy_data}, ensure_ascii=False)}\n\n'

    actions = [
        {"label": "Открыть каталог", "type": "navigate", "to": "/lots"},
    ]
    yield f'data: {json.dumps({"type": "actions", "actions": actions}, ensure_ascii=False)}\n\n'
    yield f'data: {json.dumps({"type": "done"})}\n\n'


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

        # Enrich strategy_data with lot_data for PDF generation
        if strategy_data.get("results"):
            for key, val in strategy_data["results"].items():
                if key.startswith("get_lot_details") and isinstance(val, dict) and "code" in val:
                    strategy_data["lot_data"] = val
                    break

        # Strategy data for PDF
        strategy_data["user_query"] = message
        if len(strategy_data["tools_used"]) >= 1:
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
