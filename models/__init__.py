"""
Модели данных бота.
"""

from .state import (
    # Словари состояний
    DIALOG_STATE,
    LAST_KNOWN_BUDGET,
    LAST_KNOWN_FORMAT,
    ONLINE_BOOKING_STATE,
    
    # Константы
    DialogStates,
    
    # Функции управления состояниями
    clear_user_state,
    get_dialog_state,
    set_dialog_state,
    clear_dialog_state,
    save_budget,
    get_budget,
    save_format,
    get_format,
    
    # Запись на показ
    start_booking,
    get_booking_state,
    update_booking_state,
    clear_booking_state,
    is_in_booking_flow,
)
