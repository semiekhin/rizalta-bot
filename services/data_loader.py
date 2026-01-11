"""
Загрузка данных из JSON и текстовых файлов.
"""

import json
import os
from typing import Dict, Any, List, Optional

from config.settings import (
    UNITS_PATH,
    FINANCE_PATH,
    INSTRUCTIONS_PATH,
    TEXT_WHY_RIZALTA_PATH,
    KNOWLEDGE_BASE_PATH,
)


def load_json_file(path: str) -> Optional[Any]:
    """Загружает JSON файл."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[DATA] File not found: {path}")
    except json.JSONDecodeError as e:
        print(f"[DATA] JSON parse error in {path}: {e}")
    except Exception as e:
        print(f"[DATA] Error loading {path}: {e}")
    return None


def load_text_file(path: str, default: str = "") -> str:
    """Загружает текстовый файл."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"[DATA] File not found: {path}")
    except Exception as e:
        print(f"[DATA] Error loading {path}: {e}")
    return default


# ====== Загрузка юнитов ======

def load_units() -> List[Dict[str, Any]]:
    """
    Загружает units.json.
    Поддерживает форматы:
    - [ {...}, {...} ]
    - { "units": [ {...}, {...} ] }
    """
    data = load_json_file(UNITS_PATH)
    if data is None:
        return []
    
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        units = data.get("units")
        if isinstance(units, list):
            return units
    return []


# ====== Загрузка финансовых данных ======

def load_finance() -> Optional[Dict[str, Any]]:
    """Загружает rizalta_finance.json."""
    return load_json_file(FINANCE_PATH)


def get_finance_defaults(finance: Dict[str, Any]) -> Dict[str, Any]:
    """Возвращает дефолтные параметры из finance."""
    return finance.get("defaults", {}) or {}


def get_finance_units(finance: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Возвращает список юнитов из finance."""
    return finance.get("units", []) or []


def get_min_lot(finance: Dict[str, Any]) -> Dict[str, Any]:
    """Возвращает минимальный лот из finance."""
    return finance.get("min_lot", {}) or {}


def get_installment_programs(finance: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Возвращает программы рассрочки."""
    return finance.get("installment_programs", []) or []


def get_mortgage_programs(finance: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Возвращает ипотечные программы."""
    return finance.get("mortgage_programs", []) or []


def get_investment_scenarios(finance: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Возвращает инвестиционные сценарии."""
    return finance.get("investment_scenarios", []) or []


# ====== Загрузка текстов ======

def load_knowledge_base() -> str:
    """Загружает базу знаний для AI."""
    kb = load_text_file(KNOWLEDGE_BASE_PATH)
    if kb:
        print(f"[KB] Loaded knowledge base ({len(kb)} chars)")
    else:
        print("[KB] Knowledge base not found or empty")
    return kb


def load_instructions() -> str:
    """
    Загружает инструкции для AI и добавляет базу знаний.
    """
    # Базовые инструкции
    base = load_text_file(INSTRUCTIONS_PATH)
    
    if not base:
        base = (
            "Ты — онлайн-консультант по проекту RIZALTA Resort Belokurikha. "
            "Отвечаешь по-русски, простым человеческим языком, без канцелярита. "
            "Объясняешь выгоды для клиента.\n\n"
            
            "ВАЖНО: Если пользователь задаёт короткий вопрос (1-3 слова), интерпретируй его как полноценный вопрос. "
            "Например: 'срок сдачи' = 'Какой срок сдачи объекта?', 'цена' = 'Какая цена?', 'рассрочка' = 'Какие условия рассрочки?'\n\n"
            
            "КРИТИЧЕСКИ ВАЖНО:\n"
            "- НЕ задавай вопросы в конце ответа\n"
            "- НЕ предлагай дополнительные действия\n"
            "- Просто отвечай на вопрос четко и по делу\n"
            "- После ответа пользователь увидит кнопки для дальнейших действий\n\n"
            
            "КЛЮЧЕВАЯ ИНФОРМАЦИЯ:\n"
            "• Срок сдачи объекта: 2027 год\n"
            "• Проект: RIZALTA Resort Belokurikha на Алтае\n"
            "• Минимальный лот A209: 15 251 250 ₽ (24.5 м²)\n"
            "• Доходность первого года: ~70% годовых\n"
            "• Полная окупаемость: ~4 года\n"
            "• Рассрочка: 0% на 12 месяцев или до 9% на 18 месяцев\n"
            "• Ипотека: с льготным периодом 12 месяцев"
        )
    
    # Добавляем базу знаний
    knowledge_base = load_knowledge_base()
    if knowledge_base:
        return (
            f"{base}\n\n"
            f"{'='*60}\n"
            f"ПОЛНАЯ БАЗА ЗНАНИЙ О ПРОЕКТЕ RIZALTA\n"
            f"{'='*60}\n\n"
            f"{knowledge_base}\n\n"
            f"{'='*60}\n"
            f"ПОМНИ: НЕ задавай вопросы в конце! Пользователь увидит кнопки.\n"
            f"{'='*60}"
        )
    
    return base


def load_why_rizalta_text() -> str:
    """Загружает текст 'Почему RIZALTA'."""
    text = load_text_file(TEXT_WHY_RIZALTA_PATH)
    if not text:
        text = (
            "Скоро здесь будет подробная информация о проекте RIZALTA Resort Belokurikha. "
            "Сейчас текст в процессе обновления."
        )
    return text
