# RIZALTA WebApp — Claude Code Context

## Версия
**v0.9.7** (Инвестиционная сводка по лоту + PDF + Chat cleanup)

## Цель проекта
Standalone веб-приложение дублирующее функциональность Telegram-бота RIZALTA.
Причина: замедление Telegram в РФ, нужна альтернатива без VPN.

## Доступ к серверу
```bash
ssh -p 2222 root@72.56.64.91
```

## КРИТИЧЕСКИ ВАЖНО — НЕ ТРОГАТЬ
- `/opt/bot` (порт 8000) — PROD бот, НИКОГДА не редактировать
- `/opt/bot-dev` (порт 8002) — DEV бот, НИКОГДА не редактировать
- `/opt/bot/properties.db` — читаем + INSERT в таблицу bookings (только для кнопки "Взять")
- Два процесса (бот + webapp) пишут в bookings — при текущей нагрузке безопасно
- `/opt/webapp` — PROD webapp, НИКОГДА не редактировать напрямую (только деплой из dev)

## Среды разработки

| | DEV | PROD |
|---|---|---|
| URL | https://dev-webapp.rizaltaservice.ru | https://webapp.rizaltaservice.ru |
| Путь | `/opt/webapp-dev` | `/opt/webapp` |
| Порт | 8004 | 8003 |
| Systemd | `webapp-dev.service` | `webapp.service` |
| Favicon | зелёный (DEV) | золотой (PROD) |

## DevOps Pipeline

### Auto-deploy DEV
- `webhook_receiver.py` на порту 9001 (systemd: `webhook-webapp.service`)
- GitHub webhook → push в `webapp` → git pull + build + restart (2-3 сек)
- nginx: `/webhook` → 127.0.0.1:9001

### Deploy PROD
```bash
bash /opt/webapp-dev/deploy-to-prod.sh
```
Скрипт: проверка DEV health → git pull → build → restart → health check → автооткат при ошибке

### Session end
```bash
bash /opt/webapp-dev/session-end.sh
```

### Workflow для 1Code

⚠️ **ОБЯЗАТЕЛЬНО перед началом работы:**
```bash
git checkout webapp && git pull origin webapp
```

1. 1Code делает `git pull` → получает актуальный код
2. 1Code пишет код → commit → push в GitHub (ветка `webapp`)
3. Webhook автоматически: git pull + build + restart DEV (2-3 сек)
4. Проверка: https://dev-webapp.rizaltaservice.ru
5. Деплой в prod: `bash /opt/webapp-dev/deploy-to-prod.sh` (только после одобрения)

⚠️ **ПОСЛЕ ЗАВЕРШЕНИЯ:**
```bash
git add -A && git commit -m "описание" && git push origin webapp
```

**НИКОГДА не деплоить напрямую в /opt/webapp — только через dev!**

## Структура
```
/opt/webapp-dev/
├── backend/
│   ├── .env                          # Secrets + пути (NOT in git)
│   ├── .env.example                  # Template
│   ├── app.py                        # FastAPI, порт 8003/8004, lifespan, endpoints
│   ├── webapp.db                     # Whitelist tokens (NOT in git)
│   ├── secretary.db                  # Secretary tasks (NOT in git)
│   ├── config/
│   │   └── instructions.txt          # AI system prompt (копия из бота)
│   ├── data/
│   │   ├── installment_config.json   # Конфиг рассрочки
│   │   ├── mortgage_config.json      # Конфиг ипотеки Совкомбанк
│   │   └── rizalta_finance.json      # Финансовые данные (NOT in git)
│   ├── resources/                    # Шрифты и ресурсы для PDF
│   │   ├── montserrat_regular_base64.txt
│   │   ├── montserrat_medium_base64.txt
│   │   └── montserrat_semibold_base64.txt
│   └── services/
│       ├── ai_chat.py               # AI чат: 3 пути (navigation, reports, agentic loop)
│       ├── report_builder.py         # Сбор данных из БД для отчётов (0 AI токенов)
│       ├── strategy_pdf_generator.py # PDF инвестиционных отчётов (RIZALTA branding)
│       ├── tool_definitions.py       # 5 OpenAI tools (search_lots, get_lot_details, calculate_roi, calculate_installment, compare_with_deposit)
│       ├── data_loader.py           # Loads finance data + instructions
│       ├── intent_router.py         # Quick patterns + GPT classification (16 intents)
│       ├── secretary_db.py          # SQLite CRUD for tasks
│       ├── secretary_ai.py          # GPT task parsing from text
│       ├── rclick_service.py        # rclick.ru auth + fixation
│       ├── mgp_calculator.py        # МГП расчёт + PDF (wkhtmltopdf)
│       ├── mortgage_calculator.py   # Ипотека Sovcombank + PDF
│       ├── news_service.py          # Погода, авиабилеты, RSS дайджест
│       ├── notifications.py         # Telegram + Email + кнопка "Взять"
│       ├── calculator.py            # ROI расчёт
│       ├── installment_calculator.py # Варианты рассрочки
│       ├── deposit_calculator.py    # Депозит сценарии (base/opt/pess)
│       ├── investment_compare.py    # RIZALTA vs Депозит расчёт
│       ├── compare_pdf_generator.py # PDF сравнения (wkhtmltopdf)
│       ├── kp_pdf_generator.py      # PDF КП (wkhtmltopdf)
│       ├── payment_pdf_generator.py # PDF вариантов оплаты
│       ├── lot_summary_pdf_generator.py # PDF инвест-сводки по лоту (dark branding: #263524/#D4A84B)
│       ├── calc_xlsx_generator.py   # Excel ROI
│       ├── investment_calc.py       # Investment calculations
│       ├── calc_universal.py        # Universal calculator
│       └── calculations.py          # Base calculations
├── frontend/                         # Preact + Tailwind CSS 4 + Vite 7
│   ├── src/
│   │   ├── App.jsx                   # Роутер (12 screens) + навигация + auth
│   │   ├── main.jsx                  # Entry point
│   │   ├── utils/
│   │   │   └── auth.js               # Token capture, verify, authFetch, getToken
│   │   └── pages/
│   │       ├── Home.jsx              # Меню 2x4 + условная кнопка К3
│   │       ├── Catalog.jsx           # Шахматка К1+К2+К3 (3 вкладки) + поиск
│   │       ├── LotDetail.jsx         # Карточка лота + модалки (ROI, МГП, ипотека, PDF)
│   │       ├── Chat.jsx              # AI чат (SSE streaming + кнопки отчётов + PDF download)
│   │       ├── Secretary.jsx         # Календарь + управление задачами + AI парсинг
│   │       ├── Fixation.jsx          # rclick авторизация + формы фиксации
│   │       ├── News.jsx              # 4 вкладки: валюты, погода, авиабилеты, RSS
│   │       ├── Booking.jsx           # Запись на показ (с валидацией)
│   │       ├── Presentations.jsx     # PDF презентации
│   │       ├── Documents.jsx         # Договоры
│   │       └── Media.jsx             # Видео
│   ├── public/
│   │   ├── fonts/                    # Montserrat Regular, Medium, SemiBold (.ttf)
│   │   └── images/
│   │       ├── logo.png
│   │       └── logo-green.svg        # Зелёное лого для золотого hero
│   └── vite.config.js                # Preact aliases, Tailwind plugin
├── webhook_receiver.py               # GitHub webhook auto-deploy (порт 9001)
├── deploy-to-prod.sh                 # Деплой dev → prod с автооткатом
├── session-end.sh                    # Коммит 3 репо
├── CLAUDE.md                         # Этот файл
├── TASK_MAP.md                       # Карта задач
└── SESSION_END_TEMPLATE_WEBAPP.md    # Шаблон завершения
```

## Стек
- **Frontend**: Preact (via @preact/preset-vite), Tailwind CSS 4, Vite 7
- **Backend**: Python 3.12, FastAPI, uvicorn, python-dotenv
- **БД**: SQLite — properties.db (read + INSERT bookings), webapp.db (whitelist), secretary.db (tasks)
- **PDF**: wkhtmltopdf (KP, compare, МГП, ипотека, оплата, инвест-отчёты)
- **AI**: OpenAI GPT-5.2 Responses API (agentic loop + 5 tools) + gpt-4o-mini (простой чат, секретарь)
- **Уведомления**: Telegram Bot API (httpx) + SMTP email
- **Nginx**: proxy /api/ → 127.0.0.1:8003/8004, static из frontend/dist

## Архитектура AI чата (v0.9.2+)

Три пути в `/api/chat`:

### Путь 1: Navigation intents → JSON action (0 AI)
Мгновенный ответ для навигации (open_shahmatka, send_presentation и т.д.)

### Путь 2: stream_lot_report / stream_portfolio_report
- `report_builder.py` собирает данные напрямую из БД (0 AI токенов)
- `build_lot_report_data(code)` — лот, ROI, рассрочка, депозит
- `build_portfolio_data(budget)` — лоты в бюджете, стратегии A/B
- 1 вызов GPT-5.2 форматирует отчёт для человека
- SSE `strategy_data` → кнопка "Скачать PDF отчёт"

### Путь 3: stream_chat_response (agentic loop)
- GPT-5.2 Responses API с 5 tools
- Tools: search_lots, get_lot_details, calculate_roi, calculate_installment, compare_with_deposit
- Agentic loop: AI вызывает tools → получает результаты → формирует ответ
- SSE `strategy_data` → кнопка PDF (если были финансовые расчёты)

### Ключевые файлы AI:
- `backend/services/ai_chat.py` — все 3 пути
- `backend/services/report_builder.py` — build_lot_report_data(), build_portfolio_data()
- `backend/services/strategy_pdf_generator.py` — ~800 строк, PDF генерация (RIZALTA branding)
- `backend/services/tool_definitions.py` — 5 OpenAI tools + execute_* функции

### Фронтенд AI:
- `frontend/src/pages/Chat.jsx` — SSE обработка, кнопки "Фин. отчёт по лоту" и "Портфель по бюджету", PDF download

## Фирменный стиль RIZALTA
### Цвета (применены в index.css через @theme)
```
--color-rz-green:       #263524   /* основной фон */
--color-rz-green-dark:  #1A2619   /* hover, darker */
--color-rz-green-light: #2F4A2D   /* карточки */
--color-rz-green-mid:   #1C2A1B   /* inputs, secondary */
--color-rz-cream:       #F2EBD9   /* основной текст */
--color-rz-cream-dark:  #C8BBAA   /* secondary текст */
--color-rz-cream-muted: #A89880   /* muted текст */
--color-rz-gold:        #D4A84B   /* CTA кнопки, hero */
--color-rz-gold-light:  #DEAF58   /* hover gold */
--color-rz-gold-dark:   #C09940   /* darker gold */
--color-rz-white:       #FAFAF5   /* off-white */
--color-rz-success:     #5B8C5A
--color-rz-error:       #D4544E
```
### Шрифт: Montserrat (Regular 400, Medium 500, SemiBold 600)
### PDF branding: зелёный header (#313D20), золотой title bar (#DCB764), cream фон (#F6F0E3)

## API endpoints

```
# Общие
GET  /api/health                      # version
GET  /api/lots                        # прокси к PROD боту :8000
GET  /api/lots/search                 # Поиск по коду (К1+К2+К3)
GET  /api/docs/file                   # Чтение файлов проекта (для Claude)

# Калькуляторы
POST /api/calculate-roi               # {area, price}
POST /api/installment                 # {price}
POST /api/compare-deposit             # {amount, years, scenario}

# МГП калькулятор
GET  /api/mgp/calculate               # Расчёт МГП (15 лет, 2 модели)
GET  /api/mgp/pdf                     # PDF скачивание МГП

# Ипотечный калькулятор (Совкомбанк)
GET  /api/mortgage/options             # Доступные тарифы
POST /api/mortgage/calculate           # {price, dp_percent, tariff, term}
GET  /api/mortgage/pdf                 # PDF скачивание ипотеки

# Генерация документов
POST /api/generate-kp                 # {code, include_18m, full_payment}
POST /api/generate-xlsx               # {code}
GET  /api/download-kp/{code}          # ?type=100|12m|full
GET  /api/download-xlsx/{code}        # ?building= для К3
GET  /api/download-compare-pdf        # ?amount=X&years=11&area=26.8
GET  /api/payment-pdf                 # ?price=&code=
POST /api/strategy-pdf                # PDF инвестиционного отчёта (из strategy_data)
POST /api/lot-summary-pdf             # PDF инвестиционной сводки по лоту (RFC 5987 filename)

# Заявки (реальные уведомления TG + Email)
POST /api/book-showing                # {name, phone, lot_code, comment}

# Файлы (whitelist)
GET  /api/files/presentations/{key}   # PDF презентации
GET  /api/files/documents/{key}       # PDF договоры
GET  /api/files/videos/{key}          # Видео (streaming)

# Whitelist / Corp3 (деактивированы, готовы для К4)
GET  /api/access/check                # Header: X-Access-Token → {level}

# Новости (4 вкладки)
GET  /api/news/currency               # USD/EUR/CNY через cbr-xml-daily.ru
GET  /api/news/weather                # Погода Белокуриха (Open-Meteo)
GET  /api/news/flights                # Авиабилеты (Aviasales)
GET  /api/news/digest                 # RSS: Ведомости, Коммерсантъ, РБК

# AI Чат
POST /api/chat                        # SSE stream (3 пути: navigation/reports/agentic)

# Секретарь
GET  /api/secretary/tasks             # Задачи по дате
GET  /api/secretary/tasks/week        # Задачи за неделю
POST /api/secretary/tasks             # Создать задачу
PUT  /api/secretary/tasks/{id}/done   # Отметить выполненной
PUT  /api/secretary/tasks/{id}/undone # Отметить невыполненной
PUT  /api/secretary/tasks/{id}/move   # Перенести дату
DELETE /api/secretary/tasks/{id}      # Удалить задачу
POST /api/secretary/parse             # AI парсинг текста в задачу

# Фиксация
POST /api/fixation/auth               # rclick.ru логин
GET  /api/fixation/status             # Проверка авторизации
POST /api/fixation/create             # Создать фиксацию
POST /api/fixation/logout             # Выход

# Catch-all (SPA)
GET  /{full_path:path}                # → index.html
```

## Источники данных лотов
- **К1+К2+К3**: `/opt/bot/properties.db` таблица `units` (все лоты в единой БД)
- Планировки: из properties.db
- Поиск `/api/lots/search` ищет в properties.db

## Env переменные (backend/.env)
```
# Secrets
TELEGRAM_BOT_TOKEN
MANAGER_EMAIL
BOT_EMAIL
SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD
MANAGER_CHAT_ID
OPENAI_API_KEY
OPENAI_MODEL          # gpt-5.2 (для отчётов и agentic), gpt-4o-mini (для чата)
OPENAI_MAX_TOKENS
SHOWS_GROUP_ID

# Пути
WEBAPP_DB=./webapp.db
WEBAPP_ROOT=.         # Корень webapp (для strategy_pdf — DEV: /opt/webapp-dev, PROD: /opt/webapp)
DIST_PATH=../frontend/dist
PROPERTIES_DB=/opt/bot/properties.db
PRESENTATIONS_DIR=/opt/bot-dev/presentations
DOCUMENTS_DIR=/opt/bot/docs
VIDEOS_DIR=/opt/bot-dev/videos
```

## API чтения файлов проекта (для Claude)
```
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=<относительный_путь>
```
Примеры:
- `?path=backend/services/ai_chat.py`
- `?path=backend/app.py`
- `?path=frontend/src/pages/Chat.jsx`
- `?path=CLAUDE.md`

⚠️ Файлы могут обрезаться. Если нужен полный файл — запрашивай конкретные строки на сервере.

## Whitelist система (деактивирована, готова для К4)
- Код закомментирован с `// TODO: reuse for Corp4`
- webapp.db, access_tokens, utils/auth.js — оставлены
- Токен К3: MkKGpwCAsq6IF3RtRH7bvg

## Git теги
| Тег | Описание |
|-----|----------|
| v0.5.0-stable | Phase 3.1 (whitelist) |
| v0.6.1-pre-phase322 | Точка отката до Phase 3.2.2 |
| v0.8.0-stable | Phase 3.2.2 завершена |
| v0.8.2-xlsx-fix | Фикс Excel для К3 |
| v0.8.3-payment-pdf | PDF вариантов оплаты |
| v0.8.4-search-complete | Поиск по коду лота |
| v0.8.5-env-paths | Пути в .env |
| v0.8.5-devops-pipeline | Webhook + deploy скрипт |
| v0.9.0-corp3-unified | К3 в штатном каталоге |
| v0.9.1-claude-orchestrator | Эндпоинт /api/docs/file |
| v0.9.2 | AI agentic loop + tools + report_builder |
| v0.9.3 | PDF investment reports + strategy_data SSE fix |
| v0.9.4 | Investment metrics (NOI, Cap Rate, CoC, Equity Multiple) |
| v0.9.5 | AI-driven portfolio + 3 scenarios + budget guard |
| v0.9.6 | Python portfolio selection + unified metrics + portfolio PDF |
| v0.9.7 | Инвестиционная сводка по лоту (modal + PDF) + Chat cleanup |

## Команды
```bash
# Backend
sudo systemctl restart webapp.service
sudo systemctl status webapp.service
sudo journalctl -u webapp.service -n 50 --no-pager

# DEV
sudo systemctl restart webapp-dev.service
sudo journalctl -u webapp-dev.service -n 50 --no-pager

# Webhook
sudo systemctl status webhook-webapp.service

# Frontend build
cd /opt/webapp-dev/frontend && npm run build

# Деплой в PROD
bash /opt/webapp-dev/deploy-to-prod.sh

# Session end
bash /opt/webapp-dev/session-end.sh

# Тесты
curl -s http://127.0.0.1:8003/api/health
curl -s http://127.0.0.1:8004/api/health
```

## TODO (актуализировано 02.03.2026 part 4)

### ✅ Этап 2 — Инвестиционная сводка по лоту (ВЫПОЛНЕНО v0.9.7)
- Модалка "📊 Инвестиционная сводка" в LotDetail.jsx
- Фронтенд-агрегация: Promise.all по 5 существующим API (roi, installment, compare-deposit, mgp, mortgage)
- PDF полной сводки: POST /api/lot-summary-pdf (dark RIZALTA branding: #263524 bg, #D4A84B gold)
- Cyrillic filename encoding via RFC 5987
- Chat.jsx cleanup: удалены кнопки "Фин. отчёт по лоту" и "Портфель по бюджету" (-96 строк)

### 🟡 Этап 1 — Портфельный калькулятор (отдельный экран) — ДЕПРИОРИТИЗИРОВАН
- Менеджеры предпочитают составлять портфели вручную
- Код ready: portfolio_pdf_generator.py, /api/portfolio-pdf, Python round-robin
- Можно реализовать при наличии запроса

### 🟢 Этап 3 — Чат-консьерж
10. Добавить в system prompt: ДДУ (ddu.pdf), договор аренды (arenda.pdf), RIZALTA_KNOWLEDGE.md
11. Статистика лотов в реальном времени (мин/макс цена, доступность по корпусам)
12. Убрать stream_lot_report, stream_portfolio_report, report_card из чата
13. Оставить: stream_chat_response + intent_router + навигация

### 🟢 Nice-to-have
14. К4 whitelist
15. Миграция на российский LLM
16. Деплой v0.9.6 в PROD (после тестирования)

## ⚠️ ПРАВИЛА РАЗРАБОТКИ

### Два параллельных чата
- **webapp** ветка (этот репо) — webapp разработка
- **bot-dev** — основной бот
- Общие docs (bot-dev/docs/) — ДОПОЛНЯТЬ, не затирать!

### Workflow
- **Claude chat** = архитектор (ТЗ, анализ, спецификации)
- **1Code** = реализация (код, push в GitHub)
- 1Code запускается: `cd ~/1code && bun run dev` (Mac)
- После push → webhook автоматически обновляет DEV
- PROD деплой: `bash /opt/webapp-dev/deploy-to-prod.sh`

### Завершение сессии — ОБЯЗАТЕЛЬНЫЙ ЧЕКЛИСТ
1. Прочитать SESSION_END_TEMPLATE_WEBAPP.md
2. Обновить docs: CLAUDE.md, TASK_MAP.md, RIZALTA_CURRENT.md, RIZALTA_TASKS.md
3. Общие docs — ДОПОЛНЯТЬ, не затирать
4. Коммит: `bash /opt/webapp-dev/session-end.sh`
5. Выдать компактный промпт для нового чата

### Формат промпта для нового чата (компактный)
```
# ⚠️ ВНИМАНИЕ: Два параллельных чата!
# Этот чат = WEBAPP, Claude = архитектор, 1Code = реализация
# ⚠️ ЧИТАЙ ДОКУМЕНТАЦИЮ С СЕРВЕРА, НЕ ПРИДУМЫВАЙ!

Подтяни контекст:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=CLAUDE.md
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=TASK_MAP.md

Шаблон завершения:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=SESSION_END_TEMPLATE_WEBAPP.md

Первая задача — [описание].
```

## Сессии

### Сессия 24.02.2026 (v0.8.5 → v0.9.0) — Интеграция К3
- Corp3.jsx удалён — К3 в штатном каталоге (3 вкладки)
- Поиск только через properties.db
- Whitelist-код закомментирован для К4

### Сессия 28.02.2026 (v0.9.0 → v0.9.1) — Claude-оркестратор
- Эндпоинт `/api/docs/file` — чтение файлов проекта через HTTP
- SESSION_END_TEMPLATE_WEBAPP.md
- Новый workflow — ссылки вместо копипасты

### Сессия 02.03.2026 (v0.9.1 → v0.9.3)
- **strategy_pdf_generator.py:** Full rewrite — RIZALTA branding (Montserrat, green/gold/cream), 4-page reports
- **report_builder.py:** Сбор данных из БД без AI — build_lot_report_data(), build_portfolio_data()
- **tool_definitions.py:** 5 OpenAI tools (search_lots, get_lot_details, calculate_roi, calculate_installment, compare_with_deposit)
- **ai_chat.py:** 3 пути (navigation, reports, agentic loop с GPT-5.2)
- **stream_lot_report / stream_portfolio_report:** Отчёты через report_builder + 1 вызов GPT-5.2
- **strategy_data SSE fix (f2042b4):** Кнопка "Скачать PDF" во всех 3 режимах
- **Chat.jsx:** Кнопки "Фин. отчёт по лоту" и "Портфель по бюджету" + PDF download
- **WEBAPP_ROOT env:** DEV читает файлы из /opt/webapp-dev
- **POST /api/strategy-pdf:** Эндпоинт генерации инвестиционного PDF

### Сессия 02.03.2026 part 2 (v0.9.3+)
- **Report Cards в чате:** LotReportCard, PortfolioReportCard — данные как UI-компоненты
- **report_card SSE event:** бэкенд отправляет данные ДО вызова AI
- **AI пишет только рекомендацию** — ВРЕМЕННО, нужно вернуть полноценную аналитику
- **marked удалён** — не работал, карточки заменили markdown
- **format_lot_summary / format_portfolio_summary** — pre-format данных для AI
- **Коммиты:** bbaf9a3, f97a1fe, 9bdbeb8, 9dc06b4

### Сессия 02.03.2026 part 3 (v0.9.3 → v0.9.5)
- **calculator.py:** calculate_investment_metrics() — NOI, Cap Rate, Cash-on-Cash (100%/30%), Equity Multiple
- **report_builder.py:** build_portfolio_data_v2() — 3 сценария (premium/portfolio/leverage), _enrich_lots() оптимизация
- **build_portfolio_ai_context() + _build_lots_table()** — подготовка данных для AI selector
- **_build_scenario_from_codes()** — расчёт сценария по AI-выбранным кодам лотов с budget guard
- **ai_chat.py:** AI-driven portfolio (Level 3) — gpt-4o-mini selector + GPT-5.2 analyst, fallback на v2 алгоритм
- **AI_PORTFOLIO_SELECTOR_PROMPT** — промпт для AI-подбора лотов с правилами диверсификации
- **PORTFOLIO_PROMPT_V3 + format_portfolio_summary_v3()** — 3-сценарный анализ 500-800 слов
- **LOT_REPORT_PROMPT** — полноценный 7-секционный инвестиционный анализ 400-600 слов
- **Chat.jsx:** renderText() (bold markdown), MetricCell, LotReportCard с 2x3 метриками, PortfolioReportCardV2 с ScenarioCard + reasoning + vs deposit
- **strategy_pdf_generator.py:** _generate_portfolio_report_v2() — 4-страничный PDF с 3 сценариями + сравнительная таблица
- **INVESTMENT_METHODOLOGY.md** — документация метрик (NOI, Cap Rate, CoC, Equity Multiple)
- **Коммиты:** 859c8a9, 4e17836, 8a8567d, 0e2a9e9, 0fb6b57, aa13085, b745a4f

### Сессия 02.03.2026 part 3 (v0.9.3 → v0.9.5)
- **calculator.py:** calculate_investment_metrics() — NOI, Cap Rate, Cash-on-Cash (100%/30%), Equity Multiple
- **report_builder.py:** build_portfolio_data_v2() — 3 сценария, _enrich_lots(), build_portfolio_ai_context()
- **AI-driven portfolio (Level 3):** gpt-4o-mini selector + GPT-5.2 analyst + fallback на v2
- **AI промпты:** полноценный 7-секционный анализ 400-800 слов
- **Chat.jsx:** renderText(), MetricCell, LotReportCard (2x3), PortfolioReportCardV2 (ScenarioCard + reasoning)
- **strategy_pdf_generator.py:** _generate_portfolio_report_v2() — 4 страницы
- **INVESTMENT_METHODOLOGY.md** — документация метрик
- **Budget guard** — Python валидация бюджета после AI selection
- **Коммиты:** 859c8a9, 4e17836, 8a8567d, 0e2a9e9, 0fb6b57, aa13085, b745a4f

### Сессия 02.03.2026 part 4 (v0.9.5 → v0.9.6) — Python portfolio + UX
- **AI selector удалён** — Python подбирает лоты для всех 3 сценариев (round-robin по корпусам)
- **_scenario_premium:** гарантирует самый дорогой лот в бюджете
- **_scenario_portfolio_full:** round-robin К1→К2→К3, сортировка ASC для максимума лотов
- **_scenario_max_leverage:** round-robin, ПВ 30%, ежемесячные платежи
- **GPT-5.2 fix:** max_tokens → max_completion_tokens
- **Единые метрики:** NOI, Cap Rate, ROI, CoC во всех сценариях
- **Human-readable labels:** "Чистый доход / год", "Доходность (Cap Rate)" и т.д.
- **Monthly payments:** расчёт и отображение ежемесячных платежей в сценарии 3
- **portfolio_pdf_generator.py:** новый PDF генератор в стиле чат-карточек
- **POST /api/portfolio-pdf:** эндпоинт портфельного PDF
- **Smart PDF routing:** Chat.jsx маршрутизирует lot→strategy-pdf, portfolio→portfolio-pdf
- **Архитектурное решение:** чат → консьерж, портфель → отдельный экран, сводка лота → отдельный экран
- **Удалено:** AI_PORTFOLIO_SELECTOR_PROMPT, select_portfolio_lots, _build_lots_table, _build_scenario_from_codes (-392 строки)
- **Коммиты:** d11f485, 8f35c8d, 349dae9, 6171b9a, 9c619f4

### Сессия 11.03.2026 (v0.9.6 → v0.9.7) — Инвестиционная сводка по лоту
- **LotDetail.jsx:** Модалка "📊 Инвестиционная сводка" — фронтенд-агрегация (Promise.all × 5 API)
- **lot_summary_pdf_generator.py:** PDF в dark RIZALTA branding (#263524 фон, #D4A84B золото, Montserrat)
- **POST /api/lot-summary-pdf:** Эндпоинт генерации PDF сводки лота
- **RFC 5987 filename encoding:** Фикс кириллицы в заголовке Content-Disposition
- **Chat.jsx cleanup:** Удалены кнопки "Фин. отчёт по лоту" и "Портфель по бюджету" (-96 строк)
- **Этап 1 (Portfolio screen) деприоритизирован** — менеджеры составляют портфели вручную
- **Git tag:** v0.9.7-lot-summary