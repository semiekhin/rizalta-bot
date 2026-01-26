"""
Настройки и константы бота RIZALTA.
"""

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List

# ====== Пути ======
# Автоматически определяем корень проекта (где лежит config/)
_THIS_FILE = os.path.abspath(__file__)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_FILE))

BASE_DIR = os.getenv("BOT_BASE_DIR", _PROJECT_ROOT)
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEDIA_DIR = os.path.join(BASE_DIR, "media")

# Файлы данных
UNITS_PATH = os.path.join(DATA_DIR, "units.json")
FINANCE_PATH = os.path.join(DATA_DIR, "rizalta_finance.json")
INSTRUCTIONS_PATH = os.path.join(CONFIG_DIR, "instructions.txt")
TEXT_WHY_RIZALTA_PATH = os.path.join(DATA_DIR, "text_why_rizalta.md")
KNOWLEDGE_BASE_PATH = os.path.join(DATA_DIR, "rizalta_knowledge_base.txt")

# Документы
RIZALTA_LAYOUTS_DIR = os.path.join(DOCS_DIR, "rizalta", "layouts")
ARCHITECT_PDF_PATH = os.path.join(DOCS_DIR, "rizalta", "marketing", "architect_rizalta.pdf")

# ====== Telegram ======
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Менеджеры (ID через запятую)
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID", "").strip()

def get_manager_ids() -> List[int]:
    """Возвращает список ID менеджеров для уведомлений."""
    if not MANAGER_CHAT_ID:
        return []
    return [int(id.strip()) for id in MANAGER_CHAT_ID.split(",") if id.strip()]

# ====== OpenAI ======
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "800"))

# ====== Email ======
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "").strip()
BOT_EMAIL = os.getenv("BOT_EMAIL", "bot@rizalta.ru")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mail.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()

# ====== Внешние ссылки ======
LINK_FIXATION = "https://ri.rclick.ru/notice/"
LINK_SHAHMATKA = "https://ri.rclick.ru/"

# ====== Клавиатуры ======
# Главное меню: кнопки по 2 в ряд, последняя на весь ряд
MAIN_MENU_BUTTONS = [
    ["🔥Купи себе отель!"],
    ["🏢 Лоты", "📸 Презентации"],
    ["📋 КП и расчёты", "🗓 Секретарь"],
    ["📄 Договоры", "🎬 Медиа"],
    ["📌 Фиксация", "📰 Новости"],
    ["✅ Записаться на онлайн-показ"],
]

ABOUT_PROJECT_BUTTONS = [
    ["🏔 Почему Алтай", "✨ Почему RIZALTA"],
    ["🔙 Назад"],
]

CALCULATIONS_BUTTONS = [
    ["📊 Рентабельность/доходность"],
    ["💳 Рассрочка и ипотека"],
    ["🔙 Назад"],
]

UNIT_SELECT_BUTTONS = [
    ["A209", "B210", "A305"],
    ["🔙 Назад"],
]

MEDIA_BUTTONS = [
    ["📊 Презентация"],
    ["🔙 Назад"],
]

# Кнопки, при нажатии на которые сбрасывается состояние диалога
MAIN_MENU_TRIGGER_TEXTS = [
    "🔥Купи себе отель!",
    "🏢 Лоты",
    "📋 КП и расчёты",
    "📸 Презентации",
    "📄 Договоры",
    "🎬 Медиа",
    "📌 Фиксация",
    "🗓 Секретарь",
    "📰 Новости",
    "✅ Записаться на онлайн-показ",
    "🔙 Назад",
]

# ====== Юниты ======
TARGET_UNIT_CODES = {"A209", "B210", "A305"}

# Группа для уведомлений о показах
SHOWS_GROUP_ID = -1003301897674


# ====== Whitelist Корпуса 3 ======
CORP3_WHITELIST = {
    7441583528,  # Марина Rizalta
    1410775223,  # Светлана
    7523301379,  # Евгения Оазис
    996436036,  # Дарья
    297862179,  # Алексей
    8000703751,  # Евгения, Жилищная Инициатива
    512319063,  # Sergio
}
