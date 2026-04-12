"""Хелперы для срока сдачи по корпусам.

Источник: rizalta_finance.json → completion_by_building.
К1/К2 → 4 кв. 2027, К3/К4 → 2 кв. 2028.
"""
from typing import Optional, Dict, Any, List

from services.data_loader import load_finance


_FALLBACK = {"year": 2027, "quarter": "Q4 2027", "quarter_ru": "4 кв. 2027"}


def get_completion(building: Optional[int] = None) -> Dict[str, Any]:
    """Срок сдачи для конкретного корпуса.

    Если building не задан или отсутствует в конфиге — fallback на
    плоские completion_year/completion_quarter из конфига.
    """
    finance = load_finance() or {}
    by_building = finance.get("completion_by_building", {})

    if building is not None:
        info = by_building.get(str(building))
        if info:
            return {
                "year": info.get("year", _FALLBACK["year"]),
                "quarter": info.get("quarter", _FALLBACK["quarter"]),
                "quarter_ru": info.get("quarter_ru", _FALLBACK["quarter_ru"]),
            }

    return {
        "year": finance.get("completion_year", _FALLBACK["year"]),
        "quarter": finance.get("completion_quarter", _FALLBACK["quarter"]),
        "quarter_ru": _FALLBACK["quarter_ru"],
    }


def get_min_completion_year() -> int:
    """Минимальный год сдачи по корпусам (для портфельных контекстов).

    Используется как numeric anchor в портфельных payload'ах, где
    конкретный корпус неизвестен. Fallback — плоский completion_year.
    """
    finance = load_finance() or {}
    by_building = finance.get("completion_by_building", {})
    if by_building:
        try:
            return min(int(b.get("year", _FALLBACK["year"])) for b in by_building.values())
        except (ValueError, TypeError):
            pass
    return finance.get("completion_year", _FALLBACK["year"])


def format_completion_grouped() -> str:
    """Группированная строка вида 'К1/К2: Q4 2027, К3/К4: Q2 2028'.

    Используется для общих/портфельных контекстов, где конкретный корпус
    неизвестен. Группирует корпуса с одинаковым кварталом сдачи.
    """
    finance = load_finance() or {}
    by_building = finance.get("completion_by_building", {})

    if not by_building:
        return f"Q4 {finance.get('completion_year', 2027)}"

    groups: Dict[str, List[str]] = {}
    for bnum, info in sorted(by_building.items(), key=lambda x: int(x[0])):
        q = info.get("quarter", "")
        groups.setdefault(q, []).append(f"К{bnum}")

    parts = [f"{'/'.join(blds)}: {q}" for q, blds in groups.items()]
    return ", ".join(parts)
