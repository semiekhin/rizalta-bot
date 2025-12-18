"""
Обработчики сравнения: Депозит vs RIZALTA

Функции:
- Выбор лота по площади или бюджету
- Сравнение на разных сроках (1, 3, 5, 11 лет)
- Три сценария ключевой ставки
- Генерация PDF отчёта
"""

from typing import Optional, List, Dict, Any
from services.telegram import send_message, send_message_inline, send_document
from services.investment_compare import (
    compare_investments,
    format_comparison_short,
    format_comparison_full,
    format_comparison_table,
    ComparisonResult,
)
from services.units_db import (
    get_lots_by_area, get_lots_by_budget
)

# Дефолтная сумма для примера
DEFAULT_AMOUNT = 15_000_000

# Диапазоны площадей
AREA_RANGES = [
    (25, 30, "25-30 м²"),
    (30, 35, "30-35 м²"),
    (35, 40, "35-40 м²"),
    (40, 50, "40-50 м²"),
    (50, 70, "50-70 м²"),
]

# Диапазоны бюджетов
BUDGET_RANGES = [
    (15_000_000, 20_000_000, "15-20 млн"),
    (20_000_000, 25_000_000, "20-25 млн"),
    (25_000_000, 30_000_000, "25-30 млн"),
    (30_000_000, 40_000_000, "30-40 млн"),
    (40_000_000, 60_000_000, "40-60 млн"),
]


def fmt(value: float) -> str:
    """Форматирует число с пробелами."""
    return f"{int(round(value)):,}".replace(",", " ")


async def handle_compare_menu(chat_id: int):
    """Главное меню сравнения — выбор способа подбора лота."""
    text = """📊 <b>Депозит vs RIZALTA</b>

Сравните доходность банковского депозита с инвестицией в курортную недвижимость.

💡 <b>Почему RIZALTA выгоднее:</b>
• Депозит: ставки падают (ЦБ снижает ключевую)
• Депозит: налог 13-15% «съедает» доходность
• RIZALTA: рост стоимости + доход от аренды
• RIZALTA: защита от инфляции

<b>Выберите способ подбора лота:</b>"""

    inline_buttons = [
        [{"text": "📐 По площади", "callback_data": "compare_by_area"}],
        [{"text": "💰 По бюджету", "callback_data": "compare_by_budget"}],
        [{"text": "📋 Быстрое сравнение (15 млн)", "callback_data": "compare_quick"}],
        [{"text": "🔙 В меню", "callback_data": "main_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_by_area_menu(chat_id: int):
    """Меню выбора по площади."""
    text = "📐 <b>Выберите диапазон площади:</b>"
    
    inline_buttons = []
    for min_a, max_a, label in AREA_RANGES:
        lots = get_lots_by_area(min_a, max_a)
        count = len(lots) if lots else 0
        btn_text = f"{label} ({count} лотов)"
        callback = f"compare_area_{int(min_a)}_{int(max_a)}"
        inline_buttons.append([{"text": btn_text, "callback_data": callback}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "compare_menu"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_by_budget_menu(chat_id: int):
    """Меню выбора по бюджету."""
    text = "💰 <b>Выберите диапазон бюджета:</b>"
    
    inline_buttons = []
    for min_b, max_b, label in BUDGET_RANGES:
        lots = get_lots_by_budget(min_b, max_b)
        count = len(lots) if lots else 0
        btn_text = f"{label} ({count} лотов)"
        callback = f"compare_budget_{min_b // 1_000_000}_{max_b // 1_000_000}"
        inline_buttons.append([{"text": btn_text, "callback_data": callback}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "compare_menu"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_area_range(chat_id: int, min_area: float, max_area: float):
    """Показать лоты в диапазоне площади."""
    lots = get_lots_by_area(min_area, max_area)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ Лоты в диапазоне {min_area}-{max_area} м² не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "compare_by_area"}]]
        )
        return
    
    text = f"📐 <b>Лоты {min_area}-{max_area} м²</b>\n\nВыберите лот для сравнения:"
    
    inline_buttons = []
    for lot in lots[:10]:  # Максимум 10 лотов
        price_mln = lot["price"] / 1_000_000
        btn_text = f"{lot['code']} — {lot['area']} м² — {price_mln:.1f} млн"
        # Передаём цену в callback (в тысячах для сокращения)
        callback = f"compare_lot_{lot['code']}_{int(lot['price'] // 1000)}"
        inline_buttons.append([{"text": btn_text, "callback_data": callback}])
    
    if len(lots) > 10:
        inline_buttons.append([{"text": f"... ещё {len(lots) - 10} лотов", "callback_data": "noop"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "compare_by_area"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_budget_range(chat_id: int, min_budget: int, max_budget: int):
    """Показать лоты в диапазоне бюджета."""
    lots = get_lots_by_budget(min_budget, max_budget)
    
    if not lots:
        await send_message_inline(
            chat_id,
            f"❌ Лоты в диапазоне {min_budget // 1_000_000}-{max_budget // 1_000_000} млн не найдены.",
            [[{"text": "🔙 Назад", "callback_data": "compare_by_budget"}]]
        )
        return
    
    text = f"💰 <b>Лоты {min_budget // 1_000_000}-{max_budget // 1_000_000} млн</b>\n\nВыберите лот для сравнения:"
    
    inline_buttons = []
    for lot in lots[:10]:
        price_mln = lot["price"] / 1_000_000
        btn_text = f"{lot['code']} — {lot['area']} м² — {price_mln:.1f} млн"
        callback = f"compare_lot_{lot['code']}_{int(lot['price'] // 1000)}"
        inline_buttons.append([{"text": btn_text, "callback_data": callback}])
    
    if len(lots) > 10:
        inline_buttons.append([{"text": f"... ещё {len(lots) - 10} лотов", "callback_data": "noop"}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "compare_by_budget"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_lot(chat_id: int, lot_code: str, price: int):
    """Меню сравнения для конкретного лота."""
    text = f"""📊 <b>Сравнение для лота {lot_code}</b>

💰 Стоимость: <b>{fmt(price)} ₽</b>

Выберите срок инвестирования:"""

    inline_buttons = [
        [{"text": "📅 1 год", "callback_data": f"compare_period_1_{price}"}],
        [{"text": "📅 3 года", "callback_data": f"compare_period_3_{price}"}],
        [{"text": "📅 5 лет", "callback_data": f"compare_period_5_{price}"}],
        [{"text": "📅 11 лет (полный цикл)", "callback_data": f"compare_period_11_{price}"}],
        [{"text": "📋 Таблица всех периодов", "callback_data": f"compare_table_{price}"}],
        [{"text": "🔙 Выбрать другой лот", "callback_data": "compare_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_quick(chat_id: int):
    """Быстрое сравнение на 15 млн."""
    await handle_compare_lot(chat_id, "пример", DEFAULT_AMOUNT)


async def handle_compare_period(chat_id: int, years: int, amount: int = DEFAULT_AMOUNT):
    """Сравнение на заданный период."""
    result = compare_investments(amount, years)
    text = format_comparison_short(result)
    
    inline_buttons = [
        [{"text": "📄 Создать PDF", "callback_data": f"compare_pdf_{years}_{amount}"}],
        [{"text": "🔍 Подробный расчёт", "callback_data": f"compare_full_{years}_{amount}"}],
        [{"text": "📅 Другой период", "callback_data": f"compare_lot_back_{amount}"}],
        [{"text": "🔙 В меню", "callback_data": "main_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_full(chat_id: int, years: int, amount: int = DEFAULT_AMOUNT):
    """Полный отчёт сравнения."""
    result = compare_investments(amount, years)
    text = format_comparison_full(result)
    
    inline_buttons = [
        [{"text": "📄 Создать PDF", "callback_data": f"compare_pdf_{years}_{amount}"}],
        [{"text": "💰 Другая сумма", "callback_data": f"compare_amount_{years}"}],
        [{"text": "📅 Другой период", "callback_data": f"compare_lot_back_{amount}"}],
        [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        [{"text": "🔙 В меню", "callback_data": "main_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_table(chat_id: int, amount: int = DEFAULT_AMOUNT):
    """Сравнительная таблица всех периодов."""
    text = format_comparison_table(amount)
    
    text += f"""

✅ <b>Вывод:</b>
• RIZALTA выгоднее депозита на ВСЕХ сроках
• На 3 года: +31% к капиталу vs депозит
• На 11 лет: +275% к капиталу vs депозит

💡 Ставки падают — недвижимость растёт!"""

    inline_buttons = [
        [{"text": "📅 1 год", "callback_data": f"compare_period_1_{amount}"}],
        [{"text": "📅 3 года", "callback_data": f"compare_period_3_{amount}"}],
        [{"text": "📅 5 лет", "callback_data": f"compare_period_5_{amount}"}],
        [{"text": "📅 11 лет", "callback_data": f"compare_period_11_{amount}"}],
        [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        [{"text": "🔙 В меню", "callback_data": "main_menu"}],
    ]
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_amount_menu(chat_id: int, context: str = "table"):
    """Меню выбора суммы."""
    text = "💰 <b>Выберите сумму инвестиции:</b>"
    
    amounts = [10, 15, 20, 25, 30, 40, 50]
    inline_buttons = []
    
    for amt in amounts:
        btn_text = f"{amt} млн ₽"
        callback = f"compare_sum_{amt}_{context}"
        inline_buttons.append([{"text": btn_text, "callback_data": callback}])
    
    inline_buttons.append([{"text": "🔙 Назад", "callback_data": "compare_menu"}])
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_compare_with_amount(
    chat_id: int, 
    amount_mln: int, 
    context: str = "table"
):
    """Сравнение с выбранной суммой."""
    amount = amount_mln * 1_000_000
    
    if context == "table":
        await handle_compare_table(chat_id, amount)
    else:
        try:
            years = int(context)
            await handle_compare_full(chat_id, years, amount)
        except ValueError:
            await handle_compare_table(chat_id, amount)


async def handle_compare_pdf(chat_id: int, years: int, amount: int, username: str = ""):
    """Генерирует и отправляет PDF со сравнением."""
    from services.compare_pdf_generator import generate_compare_pdf
    
    await send_message(chat_id, "⏳ Создаю PDF-документ...")
    
    pdf_path = generate_compare_pdf(amount, years, username)
    
    if pdf_path:
        filename = f"RIZALTA_vs_Депозит_{years}лет_{amount // 1_000_000}млн.pdf"
        await send_document(chat_id, pdf_path, filename)
        
        # Удаляем временный файл
        import os
        os.unlink(pdf_path)
    else:
        await send_message(chat_id, "❌ Ошибка создания PDF. Попробуйте позже.")


def get_quick_comparison_text(amount: int = DEFAULT_AMOUNT) -> str:
    """
    Быстрое текстовое сравнение для использования в AI-чате.
    """
    from services.investment_compare import compare_investments
    
    result_3y = compare_investments(amount, 3)
    result_11y = compare_investments(amount, 11)
    
    dep_3y = result_3y.deposit["base"]
    dep_11y = result_11y.deposit["base"]
    riz_3y = result_3y.rizalta
    riz_11y = result_11y.rizalta
    
    return f"""📊 <b>Сравнение: депозит vs RIZALTA</b>
💰 Сумма: {fmt(amount)} ₽
<i>Источник: ЦБ РФ (cbr.ru)</i>

<b>На 3 года:</b>
• Депозит: +{fmt(dep_3y.total_net_interest)} ₽ (ROI {dep_3y.total_roi_pct:.0f}%)
• RIZALTA: +{fmt(riz_3y.total_profit)} ₽ (ROI {riz_3y.total_roi_pct:.0f}%)
• <b>RIZALTA выгоднее на {fmt(result_3y.advantage_vs_base)} ₽</b>

<b>На 11 лет:</b>
• Депозит: +{fmt(dep_11y.total_net_interest)} ₽ (ROI {dep_11y.total_roi_pct:.0f}%)
• RIZALTA: +{fmt(riz_11y.total_profit)} ₽ (ROI {riz_11y.total_roi_pct:.0f}%)
• <b>RIZALTA выгоднее на {fmt(result_11y.advantage_vs_base)} ₽</b>

💡 RIZALTA выгоднее депозита на всех сроках!"""
