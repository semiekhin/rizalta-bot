"""
Обработчики событий бота.
"""

# Меню и навигация
from .menu import (
    handle_myid,
    handle_start,
    handle_help,
    handle_back,
    handle_main_menu,
    handle_about_project,
    handle_why_altai,
    handle_why_rizalta,
    handle_architect,
    handle_calculations_menu,
    handle_choose_unit_for_roi,
    handle_choose_unit_for_finance,
    handle_choose_unit_for_layout,
)

# Юниты: ROI, рассрочка, планировки
from .units import (
    handle_base_roi,
    handle_unit_roi,
    handle_finance_overview,
    handle_layouts,
    handle_select_lot,
    handle_budget_input,
    handle_format_input,
    handle_download_pdf,
    ROI_TEXTS,
    FINANCE_TEXTS,
)

# Запись на показ
from .booking import (
    handle_online_show_start,
    handle_call_manager,
    handle_contact_shared,
    handle_quick_contact,
    handle_booking_step,
)

# AI чат
from .ai_chat import (
    handle_free_text,
    format_finance_unit_answer,
)

# Коммерческие предложения
from .kp import (
    handle_kp_menu,
    handle_kp_request,
    handle_kp_by_area_menu,
    handle_kp_by_budget_menu,
    handle_kp_area_range,
    handle_kp_budget_range,
    handle_kp_send_one,
    handle_kp_show_all_area,
    handle_kp_show_all_budget,
)

# Динамические расчёты для всех лотов
from .calc_dynamic import (
    handle_calculations_menu_new,
    handle_calc_roi_menu,
    handle_calc_roi_by_area_menu,
    handle_calc_roi_by_budget_menu,
    handle_calc_roi_area_range,
    handle_calc_roi_budget_range,
    handle_calc_roi_lot,
    handle_calc_finance_menu,
    handle_calc_finance_by_area_menu,
    handle_calc_finance_by_budget_menu,
    handle_calc_finance_area_range,
    handle_calc_finance_budget_range,
    handle_calc_finance_lot,
)

# Документы
from .docs import (
    handle_documents_menu,
    handle_send_ddu,
    handle_send_arenda,
    handle_send_all_docs,
)

# Медиа-материалы
from .media import (
    handle_media_menu,
    handle_send_presentation,
    handle_send_presentation_file,
    handle_video_menu,
    handle_send_video,
)

# Сравнение депозит vs RIZALTA
from .compare import (
    handle_compare_by_area_menu,
    handle_compare_by_budget_menu,
    handle_compare_area_range,
    handle_compare_budget_range,
    handle_compare_lot,
    handle_compare_quick,
    handle_compare_menu,
    handle_compare_period,
    handle_compare_full,
    handle_compare_table,
    handle_compare_amount_menu,
    handle_compare_with_amount,
    handle_compare_pdf,
)

from .booking_fixation import (
    handle_booking_menu,
    handle_booking_auth_start,
    handle_booking_reauth,
    handle_booking_new,
    handle_booking_cancel,
    handle_booking_skip_comment,
    handle_booking_input,
    has_active_booking_state,
)
