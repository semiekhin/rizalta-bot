"""
Модели состояний диалогов пользователей.

Все состояния хранятся in-memory (в словарях).
При перезапуске бота состояния сбрасываются.
"""

from typing import Dict, Any, Optional

# ====== Состояния диалогов ======

# Текущее состояние диалога: chat_id -> state_name или dict
DIALOG_STATE: Dict[int, Any] = {}

# Последний известный бюджет: chat_id -> сумма в рублях
LAST_KNOWN_BUDGET: Dict[int, int] = {}

# Последний известный формат оплаты: chat_id -> "ипотека" | "рассрочка"
LAST_KNOWN_FORMAT: Dict[int, str] = {}

# Состояние многошаговой записи на показ: chat_id -> {stage, name, contact, time}
ONLINE_BOOKING_STATE: Dict[int, Dict[str, Any]] = {}


# ====== Константы состояний ======

class DialogStates:
    """Возможные состояния диалога."""
    
    # Подбор лота
    CHOOSE_UNIT_ASK_BUDGET = "choose_unit_ask_budget"
    CHOOSE_UNIT_ASK_FORMAT = "choose_unit_ask_format"
    AWAIT_BUDGET = "await_budget"
    AWAIT_FORMAT = "await_format"
    
    # Выбор юнита для расчётов
    CHOOSE_ROI_UNIT = "choose_roi_unit"
    CHOOSE_FINANCE_UNIT = "choose_finance_unit"
    CHOOSE_PLAN_UNIT = "choose_plan_unit"
    
    # Контакт для связи
    ASK_CONTACT_FOR_CALLBACK = "ask_contact_for_callback"
    
    # Многошаговая запись на показ
    BOOKING_ASK_NAME = "ask_name"
    BOOKING_ASK_CONTACT = "ask_contact"
    BOOKING_ASK_TIME = "ask_time"
    
    # Коммерческие предложения
    AWAIT_KP_REQUEST = "await_kp_request"


# ====== Функции управления состояниями ======

def clear_user_state(chat_id: int) -> None:
    """Полностью очищает все состояния пользователя."""
    DIALOG_STATE.pop(chat_id, None)
    LAST_KNOWN_BUDGET.pop(chat_id, None)
    LAST_KNOWN_FORMAT.pop(chat_id, None)
    ONLINE_BOOKING_STATE.pop(chat_id, None)


def get_dialog_state(chat_id: int) -> Optional[Any]:
    """Возвращает текущее состояние диалога."""
    return DIALOG_STATE.get(chat_id)


def set_dialog_state(chat_id: int, state: Any) -> None:
    """Устанавливает состояние диалога."""
    DIALOG_STATE[chat_id] = state


def clear_dialog_state(chat_id: int) -> None:
    """Очищает только состояние диалога (не бюджет и формат)."""
    DIALOG_STATE.pop(chat_id, None)


def save_budget(chat_id: int, budget: int) -> None:
    """Сохраняет бюджет пользователя."""
    LAST_KNOWN_BUDGET[chat_id] = budget


def get_budget(chat_id: int) -> Optional[int]:
    """Возвращает сохранённый бюджет."""
    return LAST_KNOWN_BUDGET.get(chat_id)


def save_format(chat_id: int, pay_format: str) -> None:
    """Сохраняет формат оплаты."""
    LAST_KNOWN_FORMAT[chat_id] = pay_format


def get_format(chat_id: int) -> Optional[str]:
    """Возвращает сохранённый формат оплаты."""
    return LAST_KNOWN_FORMAT.get(chat_id)


# ====== Многошаговая запись на показ ======

def start_booking(chat_id: int) -> None:
    """Начинает процесс записи на показ."""
    ONLINE_BOOKING_STATE[chat_id] = {"stage": DialogStates.BOOKING_ASK_NAME}


def get_booking_state(chat_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает состояние записи на показ."""
    return ONLINE_BOOKING_STATE.get(chat_id)


def update_booking_state(chat_id: int, **kwargs) -> None:
    """Обновляет данные записи на показ."""
    if chat_id in ONLINE_BOOKING_STATE:
        ONLINE_BOOKING_STATE[chat_id].update(kwargs)


def clear_booking_state(chat_id: int) -> None:
    """Очищает состояние записи на показ."""
    ONLINE_BOOKING_STATE.pop(chat_id, None)


def is_in_booking_flow(chat_id: int) -> bool:
    """Проверяет, находится ли пользователь в процессе записи."""
    return chat_id in ONLINE_BOOKING_STATE
