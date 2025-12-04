"""
Сервисы бота.
"""

from .data_loader import (
    load_units,
    load_finance,
    load_instructions,
    load_knowledge_base,
    load_why_rizalta_text,
    get_finance_defaults,
    get_finance_units,
    get_min_lot,
    get_installment_programs,
    get_mortgage_programs,
    get_investment_scenarios,
)

from .telegram import (
    send_message,
    send_message_inline,
    send_document,
    answer_callback_query,
)

from .calculations import (
    fmt_rub,
    normalize_unit_code,
    get_unit_by_code,
    compute_rent_cashflow,
    format_growth_projection,
    get_entry_ratio,
    calc_entry_point,
    build_portfolio_scenarios,
    suggest_units_for_budget,
    format_lot_recommendation,
    generate_finance_text,
    generate_investment_plan,
    generate_investment_pdf,
)

from .notifications import (
    notify_managers_telegram,
    notify_managers_email,
    send_booking_notification,
)

from .ai_chat import (
    ask_ai_about_project,
    build_finance_system_context,
)
