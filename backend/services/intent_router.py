"""Intent router — quick navigation classification for RIZALTA AI chat."""

import re
import logging

logger = logging.getLogger(__name__)

# Cyrillic lot code pattern: А119, В712, К3-А101, etc.
LOT_CODE_PATTERN = re.compile(r'[АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯа-я]{1,3}[\-]?[А-Яа-я]?\d{2,4}', re.IGNORECASE)


def extract_lot_code(text: str) -> str | None:
    """Extract lot code from user text (e.g. А209, В712)."""
    match = LOT_CODE_PATTERN.search(text)
    return match.group(0).upper() if match else None


def extract_budget(text: str) -> int | None:
    """Extract budget amount from text like '5 млн', '5000000', '5 миллионов'."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(млн|миллион)', text, re.IGNORECASE)
    if m:
        return int(float(m.group(1).replace(',', '.')) * 1_000_000)

    m = re.search(r'(\d{6,})', text.replace(' ', ''))
    if m:
        return int(m.group(1))

    return None


def quick_classify_navigation(text: str) -> dict | None:
    """Try to match navigation intent via regex.

    Returns action dict for navigation intents, or None.
    Used ONLY for instant navigation (no OpenAI call needed).
    """
    NAVIGATION_PATTERNS = [
        (r'(шахматк|каталог|все (лоты|апартамент|квартир)|список лотов)', 'open_shahmatka'),
        (r'(презентаци|буклет)', 'send_presentation'),
        (r'(документ|договор|дду|аренд)', 'send_documents'),
        (r'(видео|ролик|медиа)', 'show_media'),
        (r'(новост|курс валют|валют)', 'show_news'),
        (r'(фиксац|зафиксир|закрепи)', 'open_fixation'),
        (r'(секретар|задач|расписани|напомн|планир)', 'show_schedule'),
    ]

    NAVIGATION_ACTIONS = {
        "open_shahmatka": {"message": "Каталог апартаментов RIZALTA:", "to": "/lots"},
        "send_presentation": {"message": "Презентации проекта RIZALTA:", "to": "/presentations"},
        "send_documents": {"message": "Документы проекта RIZALTA:", "to": "/documents"},
        "show_media": {"message": "Видеоматериалы о проекте:", "to": "/media"},
        "show_news": {"message": "Актуальные курсы валют:", "to": "/news"},
        "open_fixation": {"message": "Фиксация клиента:", "to": "/fixation"},
        "show_schedule": {"message": "Ваше расписание:", "to": "/secretary"},
    }

    text_lower = text.lower().strip()

    for pattern, intent in NAVIGATION_PATTERNS:
        if re.search(pattern, text_lower):
            action = NAVIGATION_ACTIONS[intent]
            return {
                "type": "action",
                "intent": intent,
                "message": action["message"],
                "actions": [{"label": action["message"].rstrip(":"), "type": "navigate", "to": action["to"]}],
            }

    return None
