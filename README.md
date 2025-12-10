# RIZALTA Bot — Модульная версия

## Структура проекта

```
rizalta_bot/
├── app.py                  # Главный файл (FastAPI + webhook)
│
├── config/
│   ├── __init__.py
│   ├── settings.py         # Все настройки и константы
│   └── instructions.txt    # Системный промпт для AI
│
├── models/
│   ├── __init__.py
│   └── state.py            # Состояния диалогов (in-memory)
│
├── services/
│   ├── __init__.py
│   ├── data_loader.py      # Загрузка JSON/текстов
│   ├── telegram.py         # Отправка сообщений в TG
│   ├── calculations.py     # ROI, подбор лота, портфели
│   ├── notifications.py    # Уведомления (TG + Email)
│   └── ai_chat.py          # OpenAI интеграция
│
├── handlers/
│   ├── __init__.py
│   ├── menu.py             # Навигация, меню
│   ├── units.py            # ROI, рассрочка, планировки
│   ├── booking.py          # Запись на показ
│   └── ai_chat.py          # Свободный текст → AI
│
└── data/
    ├── rizalta_finance.json
    ├── units.json
    ├── rizalta_knowledge_base.txt
    ├── text_why_rizalta.md
    ├── text_why_belokuricha.md
    └── layouts/            # PDF планировки
```

## Что сохранено из монолита

✅ **Полная логика подбора лота** (`suggest_units_for_budget`)
- Расчёт точки входа по entry_ratio
- Сравнение бюджета с точкой входа
- Прогноз совокупной доходности по годам

✅ **Портфельные сценарии** (`build_portfolio_scenarios`)
- 1× / 2× каждого юнита
- Комбинации: 1×A209 + 1×B210, ...
- Фильтрация по бюджету (+10% допуск)

✅ **Готовые тексты для юнитов** (ROI_TEXTS, FINANCE_TEXTS)
- A209, B210, A305
- С акцентом на гарантии
- С вариантами рассрочки/ипотеки

✅ **Динамический расчёт ROI** (`handle_unit_roi`)
- Из rizalta_finance.json
- С капитализацией по годам

✅ **Отправка планировок** (`handle_layouts`)
- Фильтрация по unit_code
- Inline-кнопки после отправки

✅ **Многошаговая запись на показ**
- Поделиться контактом (request_contact)
- Ввод вручную
- Уведомления в TG + Email

✅ **AI-консультант**
- База знаний из текстового файла
- Финансовый контекст в промпт

✅ **Правильная обработка состояний**
- Кнопки меню сбрасывают диалог
- /start очищает ВСЕ состояния
- Кириллица/латиница в кодах юнитов

## Как запустить

### Локально (для разработки)

```bash
cd rizalta_bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install fastapi uvicorn openai python-dotenv httpx requests

# Создайте .env с переменными
uvicorn app:app --reload --port 8000
```

### На сервере

```bash
# Скопировать в /opt/bot/
scp -r rizalta_bot/* root@SERVER:/opt/bot/

# Настроить systemd сервис (как для монолита)
systemctl restart realtmeai-bot
```

## Переменные окружения (.env)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=<токен бота>

# Менеджеры (ID через запятую)
MANAGER_CHAT_ID=123456789,987654321

# OpenAI
OPENAI_API_KEY=<ключ API>
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=800

# Email
MANAGER_EMAIL=manager@example.com,sales@example.com
BOT_EMAIL=bot@rizalta.ru
SMTP_HOST=smtp.mail.ru
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<пароль>

# Пути (опционально)
BOT_BASE_DIR=/opt/bot
```

## Как добавлять новые фичи

### Новый юнит (например, C410)

1. Добавить в `data/rizalta_finance.json` → `units[]`
2. Добавить тексты в `handlers/units.py`:
   - `ROI_TEXTS["C410"] = "..."`
   - `FINANCE_TEXTS["C410"] = "..."`
3. Добавить в `config/settings.py` → `TARGET_UNIT_CODES`

### Новый раздел меню

1. Добавить кнопку в `config/settings.py` → `MAIN_MENU_BUTTONS`
2. Создать handler в `handlers/menu.py`
3. Добавить роутинг в `app.py` → `process_message()`

### Новое состояние диалога

1. Добавить в `models/state.py` → `DialogStates`
2. Добавить обработку в соответствующем handler
3. Добавить роутинг в `app.py`

## Отличия от монолита

| Аспект | Монолит | Модули |
|--------|---------|--------|
| Строк кода | 2765 | 3021 |
| Файлов | 1 | 16 |
| Поиск кода | Ctrl+F | По файлам |
| Редактирование | Осторожно | Изолированно |
| Тестирование | Сложно | По модулям |
| Расширение | В конец файла | Новый handler |

## Важные замечания

1. **Webhook endpoint**: `/telegram/webhook` (как в монолите)

2. **Нормализация кодов**: Кириллица → латиница (А→A, В→B)

3. **Приоритет данных**: `rizalta_finance.json` → `units.json`

4. **Состояния**: in-memory, сбрасываются при перезапуске

---

*Создано: 28 ноября 2025*
*Версия: modular-1.0*

## После клонирования
```bash
# 1. Установить зависимости
pip install -r requirements.txt
npm install

# 2. Создать базу данных
python3 services/parser_rclick.py

# 3. Настроить .env (скопировать из .env.example)
cp .env.example .env
```
