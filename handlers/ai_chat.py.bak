"""
Обработчик свободного текста — AI-консультант с Function Calling.
"""

from config.settings import LINK_FIXATION, LINK_SHAHMATKA
from services.telegram import send_message, send_message_inline
from services.ai_chat import analyze_user_intent, ask_ai_about_project
from services.data_loader import load_finance
from services.calculations import (
    suggest_units_for_budget, 
    normalize_unit_code, 
    fmt_rub,
    get_unit_by_code,
    compute_rent_cashflow,
    get_finance_defaults
)
from models.state import save_budget, clear_dialog_state, set_dialog_state, DialogStates


def format_finance_unit_answer(finance: dict, unit_code: str) -> str:
    """
    Формирует текст с расчётом доходности по юниту.
    """
    u = get_unit_by_code(finance, unit_code)
    if not u:
        return (
            f"Пока нет готового инвест-расчёта по юниту {unit_code}. "
            "Лучше подключить менеджера проекта и посчитать сценарий под ваш бюджет. 💬"
        )
    
    title = u.get("title") or f"Гостиничный номер {unit_code}"
    area = u.get("area_m2")
    price = float(u.get("price_rub", 0) or 0)
    defaults = get_finance_defaults(finance)
    
    rent = compute_rent_cashflow(u, defaults)
    
    cap = u.get("capitalization_projection", {}) or {}
    price_2027 = cap.get("price_2027_rub", 0)
    price_2029 = cap.get("price_2029_rub", 0)
    
    lines = []
    lines.append(f"📊 Расчёт доходности по гостиничному номеру {unit_code}")
    lines.append("")
    lines.append("🏡 <b>Объект</b>")
    lines.append(f"• {title}")
    if area:
        lines.append(f"• Площадь: {area} м²")
    lines.append(f"• Цена по договору: {fmt_rub(price)}")
    lines.append("")
    
    lines.append("🏨 <b>Арендный поток (базовый сценарий)</b>")
    lines.append(f"• Валовая выручка/год: ~{fmt_rub(rent['gross_year_rub'])}")
    lines.append(f"• Чистый доход/год: ~{fmt_rub(rent['net_year_rub'])}")
    lines.append(f"• ROI по аренде: ~{rent['roi_year_pct']:.1f}% годовых")
    lines.append("")
    
    if price_2027 or price_2029:
        lines.append("📈 <b>Прогноз роста стоимости</b>")
        if price_2027:
            growth = ((price_2027 - price) / price * 100)
            lines.append(f"• 2027 (сдача): {fmt_rub(price_2027)} (+{growth:.0f}%)")
        if price_2029:
            growth = ((price_2029 - price) / price * 100)
            lines.append(f"• 2029: {fmt_rub(price_2029)} (+{growth:.0f}%)")
        lines.append("")
    
    lines.append("💡 Хотите подобрать портфель под ваш бюджет?")
    
    return "\n".join(lines)


async def handle_free_text(chat_id: int, text: str):
    """
    Обработка свободного текста через AI с Function Calling.
    AI сам определяет намерение и вызывает нужную функцию.
    """
    
    # Анализируем намерение пользователя через AI
    result = analyze_user_intent(text)
    intent = result.get("intent", "chat")
    params = result.get("params", {})
    
    print(f"[AI] Intent: {intent}, Params: {params}")
    
    # === ПОДБОР ПОРТФЕЛЯ ===
    if intent == "build_portfolio":
        budget = params.get("budget")
        if budget and budget > 0:
            budget = int(budget)
            save_budget(chat_id, budget)
            
            reply_text = suggest_units_for_budget(budget, "рассрочка")
            clear_dialog_state(chat_id)
            
            inline_buttons = [
                [
                    {"text": "📄 Скачать PDF", "callback_data": "download_pdf"},
                    {"text": "📎 Планировки", "callback_data": "get_layouts"},
                ],
                [
                    {"text": "✅ Записаться на онлайн-показ", "callback_data": "online_show"}
                ]
            ]
            
            await send_message_inline(chat_id, reply_text, inline_buttons)
            return
        else:
            # Бюджет не распознан — спрашиваем
            set_dialog_state(chat_id, DialogStates.ASK_BUDGET)
            await send_message(
                chat_id,
                "Давайте подберём портфель! 💰\n\nНапишите ваш бюджет в рублях, например: <b>15000000</b>"
            )
            return
    
    # === РАСЧЁТ ДОХОДНОСТИ ===
    if intent == "calculate_roi":
        unit_code = params.get("unit_code", "A209")
        finance = load_finance()
        
        if finance:
            answer = format_finance_unit_answer(finance, unit_code)
            inline_buttons = [
                [
                    {"text": "🎯 Подобрать лот", "callback_data": "select_lot"},
                    {"text": "💳 Рассрочка", "callback_data": f"finance_{unit_code}"}
                ],
                [
                    {"text": "✅ Записаться на показ", "callback_data": "online_show"}
                ]
            ]
            await send_message_inline(chat_id, answer, inline_buttons)
            return
    
    # === РАССРОЧКА/ИПОТЕКА ===
    if intent == "show_installment":
        unit_code = params.get("unit_code")
        
        if unit_code:
            from handlers.units import handle_finance_overview
            await handle_finance_overview(chat_id, unit_code)
            return
        else:
            inline_buttons = [
                [{"text": "Студия A209 (15.3 млн)", "callback_data": "finance_A209"}],
                [{"text": "Стандарт B210 (19.7 млн)", "callback_data": "finance_B210"}],
                [{"text": "Люкс A305 (23.7 млн)", "callback_data": "finance_A305"}]
            ]
            await send_message_inline(
                chat_id,
                "💳 <b>Рассрочка и ипотека</b>\n\nВыберите гостиничный номер для расчёта:",
                inline_buttons
            )
            return
    
    # === ЗАПИСЬ НА ПОКАЗ ===
    if intent == "book_showing":
        from handlers.booking import start_online_booking
        await start_online_booking(chat_id)
        return
    
    # === ПЛАНИРОВКИ ===
    if intent == "show_layouts":
        unit_code = params.get("unit_code")
        
        if unit_code:
            from handlers.units import handle_layouts
            await handle_layouts(chat_id, unit_code)
            return
        else:
            inline_buttons = [
                [{"text": "Студия A209", "callback_data": "layout_A209"}],
                [{"text": "Стандарт B210", "callback_data": "layout_B210"}],
                [{"text": "Люкс A305", "callback_data": "layout_A305"}]
            ]
            await send_message_inline(
                chat_id,
                "📐 <b>Планировки гостиничных номеров</b>\n\nВыберите гостиничный номер:",
                inline_buttons
            )
            return
    
    # === КОММЕРЧЕСКИЕ ПРЕДЛОЖЕНИЯ ===
    if intent == "get_commercial_proposal":
        from handlers.kp import handle_kp_menu
        from services.kp_search import find_kp_by_code, find_kp_by_area, find_kp_by_budget, find_kp_by_floor
        from services.telegram import send_photo, send_media_group
        
        unit_code = params.get("unit_code")
        area = params.get("area")
        budget = params.get("budget")
        floor = params.get("floor")
        block_section = params.get("block_section")
        
        if unit_code:
            filepath = find_kp_by_code(unit_code)
            if filepath:
                await send_photo(chat_id, filepath, f"📋 КП: {unit_code}")
                return
        
        if area:
            files = find_kp_by_area(area)
            if files:
                if len(files) == 1:
                    await send_photo(chat_id, files[0], f"📋 КП на ~{area} м²")
                else:
                    await send_media_group(chat_id, files[:10], f"📋 КП на ~{area} м²")
                return
        
        if budget:
            files = find_kp_by_budget(int(budget))
            if files:
                budget_mln = budget / 1_000_000
                if len(files) == 1:
                    await send_photo(chat_id, files[0], f"📋 КП на ~{budget_mln:.0f} млн")
                else:
                    await send_media_group(chat_id, files[:10], f"📋 КП на ~{budget_mln:.0f} млн")
                return
        
        if floor:
            files = find_kp_by_floor(floor, block_section)
            if files:
                if len(files) == 1:
                    await send_photo(chat_id, files[0], f"📋 КП {floor} этаж")
                else:
                    await send_media_group(chat_id, files[:10], f"📋 КП {floor} этаж")
                return
        
        await handle_kp_menu(chat_id)
        return
    
    # === ПРЕЗЕНТАЦИЯ (NEW) ===
    if intent == "send_presentation":
        from handlers.media import handle_send_presentation
        await handle_send_presentation(chat_id)
        return
    
    # === ФИКСАЦИЯ КЛИЕНТА (NEW) ===
    if intent == "open_fixation":
        inline_buttons = [
            [{"text": "📌 Открыть форму фиксации", "url": LINK_FIXATION}],
            [{"text": "🔙 В меню", "callback_data": "back_to_menu"}]
        ]
        await send_message_inline(
            chat_id,
            "📌 <b>Фиксация клиента</b>\n\n"
            "Для фиксации клиента за вами нажмите кнопку ниже.\n"
            "После фиксации клиент будет закреплён за вами на 30 дней.",
            inline_buttons
        )
        return
    
    # === ШАХМАТКА (NEW) ===
    if intent == "open_shahmatka":
        inline_buttons = [
            [{"text": "🏠 Открыть шахматку", "url": LINK_SHAHMATKA}],
            [{"text": "🔙 В меню", "callback_data": "back_to_menu"}]
        ]
        await send_message_inline(
            chat_id,
            "🏠 <b>Шахматка</b>\n\n"
            "Актуальная шахматка с доступными лотами.\n"
            "Нажмите кнопку ниже для просмотра:",
            inline_buttons
        )
        return
    
    # === ДОКУМЕНТЫ (NEW) ===
    if intent == "send_documents":
        doc_type = params.get("doc_type", "all")
        
        from handlers.docs import handle_send_ddu, handle_send_arenda, handle_send_all_docs, handle_documents_menu
        
        if doc_type == "ddu":
            await handle_send_ddu(chat_id)
        elif doc_type == "arenda":
            await handle_send_arenda(chat_id)
        elif doc_type == "all":
            await handle_send_all_docs(chat_id)
        else:
            await handle_documents_menu(chat_id)
        return
    
    # === МЕДИА (NEW) ===
    if intent == "show_media":
        from handlers.media import handle_media_menu
        await handle_media_menu(chat_id)
        return
    
    # === ОБЫЧНЫЙ ТЕКСТОВЫЙ ОТВЕТ ===
    response_text = result.get("response")
    if not response_text:
        response_text = ask_ai_about_project(text)
    
    inline_buttons = [
        [
            {"text": "📋 Получить КП", "callback_data": "kp_menu"},
            {"text": "✅ Записаться на показ", "callback_data": "online_show"}
        ]
    ]
    
    await send_message_inline(chat_id, response_text, inline_buttons)
