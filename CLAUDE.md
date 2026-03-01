# RIZALTA WebApp — Claude Code Context

## Версия
**v0.9.3** (AI Chat v2 — три режима)

## Цель проекта
Standalone веб-приложение дублирующее функциональность Telegram-бота RIZALTA.
Причина: замедление Telegram в РФ, нужна альтернатива без VPN.

## Доступ к серверу
```bash
ssh -p 2222 root@72.56.64.91
```

## Claude-оркестратор (v0.9.1)

### Эндпоинт `/api/docs/file`
Claude читает файлы проекта напрямую с сервера через HTTP:
```
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=CLAUDE.md
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=backend/app.py
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=backend/services/ai_chat.py
```

Безопасность: path traversal заблокирован, `.env`/`.db` не отдаются, только разрешённые расширения.

### Генерация ссылок
```bash
# Все Python-файлы бэкенда
find /opt/webapp-dev/backend -name "*.py" | sed 's|/opt/webapp-dev/|https://dev-webapp.rizaltaservice.ru/api/docs/file?path=|'

# Все JSX фронтенда
find /opt/webapp-dev/frontend/src -name "*.jsx" | sed 's|/opt/webapp-dev/|https://dev-webapp.rizaltaservice.ru/api/docs/file?path=|'
```

### Env
```
WEBAPP_ROOT=/opt/webapp-dev   # DEV
WEBAPP_ROOT=/opt/webapp       # PROD
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
| Favicon | 🟠 оранжевая "D" | стандартный Vite |

## DevOps Pipeline (v0.8.5)

### Auto-deploy DEV
- `webhook_receiver.py` на порту 9001 (systemd: `webhook-webapp.service`)
- GitHub webhook → push в `webapp` → git pull + build + restart (2-3 сек)
- nginx: `/webhook` → 127.0.0.1:9001

### Deploy PROD
```bash
bash /opt/webapp-dev/deploy-to-prod.sh
```
Скрипт: проверка DEV health → git pull → build → restart → health check → автооткат при ошибке

### DEV/PROD
- Работаем ТОЛЬКО в DEV (/opt/webapp-dev)
- В PROD деплоим ТОЛЬКО при полной работоспособности: bash /opt/webapp-dev/deploy-to-prod.sh
- НИКОГДА не редактировать /opt/webapp напрямую

### Workflow для 1Code

1. 1Code запускается: `cd ~/1code && bun run dev` (Mac)
2. 1Code автоматически пулит актуальный код перед задачей
3. 1Code пишет код → автоматически commit + push в GitHub (ветка `webapp`)
4. Webhook автоматически: git pull + build + restart DEV (2-3 сек)
5. Claude проверяет результат через `web_fetch` + `/api/docs/file`
6. Деплой в prod: `bash /opt/webapp-dev/deploy-to-prod.sh` (только после одобрения)

**НИКОГДА не деплоить напрямую в /opt/webapp — только через dev!**

## Рабочая директория
`/opt/webapp` (порт 8003)

## Структура
```
/opt/webapp/
├── CLAUDE.md                         # Контекст для Claude (этот файл)
├── TASK_MAP.md                       # Карта задач для 1Code
├── SESSION_END_TEMPLATE_WEBAPP.md    # Шаблон завершения сессии (v0.9.1)
├── backend/
│   ├── .env                          # Secrets + пути (NOT in git)
│   ├── .env.example                  # Template
│   ├── app.py                        # FastAPI, порт 8003, lifespan, 43+ endpoints
│   ├── webapp.db                     # Whitelist tokens (NOT in git)
│   ├── secretary.db                  # Secretary tasks (NOT in git)
│   ├── config/
│   │   └── instructions.txt          # AI system prompt (копия из бота)
│   ├── data/
│   │   ├── README.md                 # Note to copy rizalta_finance.json
│   │   ├── installment_config.json   # Конфиг рассрочки
│   │   ├── mortgage_config.json      # Конфиг ипотеки Совкомбанк
│   │   └── rizalta_finance.json      # Финансовые данные (NOT in git, копия из бота)
│   └── services/
│       ├── ai_chat.py               # OpenAI streaming SSE + intent actions
│       ├── data_loader.py           # Loads finance data + instructions
│       ├── intent_router.py         # Quick patterns + GPT classification (16 intents)
│       ├── secretary_db.py          # SQLite CRUD for tasks (secretary.db)
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
│       ├── payment_pdf_generator.py # PDF вариантов оплаты (v0.8.4)
│       ├── calc_xlsx_generator.py   # Excel ROI (+ Corp3 JSON support)
│       ├── investment_calc.py       # Investment calculations
│       ├── calc_universal.py        # Universal calculator
│       └── calculations.py          # Base calculations
├── frontend/                         # Preact + Tailwind CSS 4 + Vite 7
│   ├── src/
│   │   ├── App.jsx                   # Роутер (11 screens) + навигация + auth
│   │   ├── main.jsx                  # Entry point
│   │   ├── utils/
│   │   │   └── auth.js               # Token capture, verify, authFetch, getToken
│   │   └── pages/
│   │       ├── Home.jsx              # Меню 2x4 + условная кнопка К3
│   │       ├── Catalog.jsx           # Шахматка К1+К2+К3, 3 вкладки, поиск по коду
│   │       ├── LotDetail.jsx         # Карточка лота + модалки (ROI, МГП, ипотека, PDF оплаты)
│   │       ├── Chat.jsx              # AI чат (SSE streaming + action buttons)
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
└── venv/
```

## Стек
- **Frontend**: Preact (via @preact/preset-vite with react alias), Tailwind CSS 4, Vite 7
- **Backend**: Python 3.12, FastAPI 0.109, uvicorn, python-dotenv
- **БД**: SQLite `/opt/bot/properties.db` (read + INSERT bookings) + `/opt/webapp/backend/webapp.db` (whitelist tokens) + `/opt/webapp/backend/secretary.db` (tasks)
- **PDF**: wkhtmltopdf (KP, compare, МГП, ипотека, варианты оплаты)
- **AI**: OpenAI API gpt-4o-mini (streaming SSE) — chat, intent routing, task parsing
- **Уведомления**: Telegram Bot API (httpx) + SMTP email
- **Nginx**: proxy /api/ → 127.0.0.1:8003, static из frontend/dist

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

## API (43+ endpoints, v0.9.1)
```
# Общие
GET  /api/health                      # version: "0.9.0"
GET  /api/lots                        # прокси к PROD боту :8000
GET  /api/lots/search                 # Поиск по коду (К1+К2+К3)
GET  /api/docs/file                   # Claude-оркестратор: чтение файлов проекта (v0.9.1)

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

# Заявки (реальные уведомления TG + Email)
POST /api/book-showing                # {name, phone, lot_code, comment}

# Файлы (whitelist)
GET  /api/files/presentations/{key}   # PDF презентации
GET  /api/files/documents/{key}       # PDF договоры
GET  /api/files/videos/{key}          # Видео (streaming)

# Whitelist / Corp3 (деактивированы v0.9.0, оставлены для К4)
GET  /api/access/check                # Header: X-Access-Token → {level}
GET  /api/corp3/lots                  # ДЕАКТИВИРОВАН (К3 теперь в штатном каталоге)
GET  /api/corp3/layout/{code}         # ДЕАКТИВИРОВАН

# Новости (4 вкладки)
GET  /api/news/currency               # USD/EUR/CNY через cbr-xml-daily.ru
GET  /api/news/weather                # Погода Белокуриха (Open-Meteo)
GET  /api/news/flights                # Авиабилеты (Aviasales)
GET  /api/news/digest                 # RSS: Ведомости, Коммерсантъ, РБК (10-15 новостей)

# AI Чат (Phase 3.2.2)
POST /api/chat                        # SSE stream + action JSON + strategy_data, rate limited
POST /api/strategy-pdf                # PDF генерация инвестиционного отчёта (NEW v0.9.3)

# Секретарь (Phase 3.2.2)
GET  /api/secretary/tasks             # Задачи по дате
GET  /api/secretary/tasks/week        # Задачи за неделю
POST /api/secretary/tasks             # Создать задачу
PUT  /api/secretary/tasks/{id}/done   # Отметить выполненной
PUT  /api/secretary/tasks/{id}/undone # Отметить невыполненной
PUT  /api/secretary/tasks/{id}/move   # Перенести дату
DELETE /api/secretary/tasks/{id}      # Удалить задачу
POST /api/secretary/parse             # AI парсинг текста в задачу

# Фиксация (Phase 3.2.2)
POST /api/fixation/auth               # rclick.ru логин (телефон или email)
GET  /api/fixation/status             # Проверка авторизации
POST /api/fixation/create             # Создать фиксацию
POST /api/fixation/logout             # Выход

# Catch-all (SPA)
GET  /{full_path:path}                # → index.html
```

## Источники данных лотов
- **К1+К2+К3**: `/opt/bot/properties.db` таблица `units` (640 лотов, все 3 корпуса)
- Планировки К3: `/opt/bot-dev/data/corp3_layouts/`

## Env переменные (backend/.env)
```
# Secrets
TELEGRAM_BOT_TOKEN    # Токен бота (для уведомлений)
MANAGER_EMAIL         # Email менеджеров
BOT_EMAIL             # Email отправителя
SMTP_HOST             # SMTP сервер
SMTP_PORT             # SMTP порт
SMTP_USER             # SMTP логин
SMTP_PASSWORD         # SMTP пароль
MANAGER_CHAT_ID       # ID чата менеджера в Telegram
OPENAI_API_KEY        # Ключ OpenAI
OPENAI_MODEL          # gpt-4o-mini
OPENAI_MAX_TOKENS     # 2000
SHOWS_GROUP_ID        # ID Telegram группы показов
WEBAPP_ROOT           # Корневая директория webapp (DEV: /opt/webapp-dev)

# Пути (v0.8.5)
WEBAPP_DB=./webapp.db
DIST_PATH=../frontend/dist
PROPERTIES_DB=/opt/bot/properties.db
CORP3_LAYOUTS_DIR=/opt/bot-dev/data/corp3_layouts
PRESENTATIONS_DIR=/opt/bot-dev/presentations
DOCUMENTS_DIR=/opt/bot/docs
VIDEOS_DIR=/opt/bot-dev/videos
WEBAPP_ROOT=/opt/webapp-dev          # для /api/docs/file (v0.9.1)
```

## Whitelist система (Phase 3.1, деактивирована v0.9.0)
- Код закомментирован с `// TODO: reuse for Corp4`
- Оставлено для К4: /api/access/check, webapp.db, utils/auth.js
- Токен К3: MkKGpwCAsq6IF3RtRH7bvg

## Git теги
- `v0.9.3` — PDF investment reports + strategy_data SSE fix
- `v0.5.0-stable` — Phase 3.1 (whitelist)
- `v0.6.1-pre-phase322` — точка отката до Phase 3.2.2
- `v0.8.0-stable` — Phase 3.2.2 завершена
- `v0.8.2-xlsx-fix` — фикс Excel для К3
- `v0.8.3-payment-pdf` — PDF вариантов оплаты
- `v0.8.4-search-complete` — поиск по коду лота
- `v0.8.5-env-paths` — пути в .env
- `v0.8.5-devops-pipeline` — webhook + deploy скрипт
- `v0.9.0-corp3-unified` — К3 в штатном каталоге
- `v0.9.1-claude-orchestrator` — эндпоинт /api/docs/file

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
sudo journalctl -u webhook-webapp.service -n 20 --no-pager

# Frontend build
cd /opt/webapp/frontend && npm run build

# Деплой в PROD (из dev)
bash /opt/webapp-dev/deploy-to-prod.sh

# Тесты
curl -s http://127.0.0.1:8003/api/health
curl -s http://127.0.0.1:8004/api/health
curl -s "http://127.0.0.1:8004/api/docs/file?path=CLAUDE.md" | head -5
```

## TODO (Phase 3.3+)
1. **Function calling в AI чате** — инструменты: расчёт ROI, поиск лота, бронирование
2. **Автосинхронизация данных бот↔webapp** — rizalta_finance.json, instructions.txt (через .env пути)
3. Миграция на российский LLM (DeepSeek/YandexGPT)
4. История чата (сохранение сессий)
5. Push-уведомления для задач секретаря
6. "Взять" → автосоздание задачи в секретаре (бот-сайд)

## ⚠️ ПРАВИЛА РАЗРАБОТКИ

### Два параллельных чата
- **Этот репо (webapp)** — webapp разработка
- **bot-dev** — основной бот
- Общие docs (bot-dev/docs/) — ДОПОЛНЯТЬ, не затирать!


### Workflow
- **Claude chat** = архитектор (ТЗ, анализ, спецификации)
- **1Code** = реализация (код, push в GitHub)
- 1Code запускается: `cd ~/1code && bun run dev` (Mac)
- После push → webhook автоматически обновляет DEV
- Claude проверяет результат через `web_fetch` + `/api/docs/file`
- PROD деплой: `bash /opt/webapp-dev/deploy-to-prod.sh`

### Завершение сессии — ОБЯЗАТЕЛЬНЫЙ ЧЕКЛИСТ
Следовать `SESSION_END_TEMPLATE_WEBAPP.md`:
1. Обновить docs: CLAUDE.md, TASK_MAP.md + общие RIZALTA_*.md (дополнить, НЕ затирать)
2. Коммит 3 репо: webapp + bot-dev + bot PROD
3. Выдать компактный промпт со ссылками для нового чата

### Шаблон завершения
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=SESSION_END_TEMPLATE_WEBAPP.md

## Сессия 28.02.2026 (v0.9.0 → v0.9.1)

### Claude-оркестратор
- **Эндпоинт `/api/docs/file`** — чтение файлов проекта через HTTP (коммит `6ecf77f`)
- **SESSION_END_TEMPLATE_WEBAPP.md** — свой шаблон завершения для webapp-чата
- **Новый workflow** — ссылки вместо копипасты в промптах, актуальный контекст с сервера
- **OpenAI API ключ** обновлён (новый аккаунт)

## Сессия 24.02.2026 (v0.8.5 → v0.9.0)

### Интеграция К3 в штатный каталог
- **Corp3.jsx удалён** — отдельная страница К3 больше не нужна
- **Каталог:** 3 вкладки — К1 (Family), К2 (Business), К3 (Digital)
- **Поиск:** только через properties.db (убран поиск по corp3_units.json)
- **КП/Excel:** building передаётся явно (фикс дублей кодов между корпусами)
- **kp_pdf_generator.py:** get_building_name() использует building (не block_section), знает 3 корпуса
- **Whitelist-код закомментирован** с `// TODO: reuse for Corp4` — не удалён
- **Деактивировано:** /api/corp3/lots, /api/corp3/layout/{code}, CORP3_DATA_PATH
- **Оставлено для К4:** /api/access/check, webapp.db, utils/auth.js
- **Git tag:** `v0.9.0-corp3-unified`

## Сессия 01.03.2026 (v0.9.1 → v0.9.2) — GPT-5.2 финансовый советник

### GPT-5.2 Responses API
- Полная миграция с Chat Completions на Responses API
- `client.responses.create()` вместо `client.chat.completions.create()`
- `instructions=""` вместо `messages=[{role: "system"}]`
- `reasoning={"effort": "high"}` вместо `temperature`
- Streaming: `event.type == 'response.output_text.delta'` → `event.delta`

### Agentic loop
- Мульти-раундовый tool calling (до 5 раундов, 17+ вызовов за запрос)
- Tool results: `{"type": "function_call_output", "call_id": ..., "output": ...}`

### 5 Tools (flat schema, без function wrapper)
- `search_lots` — поиск лотов по фильтрам
- `get_lot_details` — детали апартамента
- `calculate_roi` — расчёт доходности
- `calculate_installment` — варианты рассрочки
- `compare_with_deposit` — сравнение с банковским депозитом
- Schema: name/description/parameters на верхнем уровне (НЕ внутри function:{})
- БЕЗ `strict: True`, БЕЗ `additionalProperties: False`

### ADVISOR_INSTRUCTION
- Финансовый советник с 3 стратегиями на бюджет клиента
- Терминология: "лот"/"апартамент" (никогда "юнит")
- Капитализация: +20%/год стройка, +10%/год после сдачи

### Strategy PDF
- `backend/services/strategy_pdf_generator.py` — PDF отчёт для инвестора
- Endpoint: `POST /api/strategy-pdf`
- `max_output_tokens=16000` для длинных финансовых отчётов

### Коммиты
- `2b94190` — Initial GPT-5.2 migration
- `77bc628` — Fix tools schema format
- `dafc3be` — Remove strict mode
- `40bb824` — Agentic loop
- `e75fda5` — Force text response
- `c0e6458` — Терминология + капитализация

## Сессия 02.03.2026 (v0.9.2 → v0.9.3) — AI Chat v2: три режима

### Архитектура AI чата v2
Три режима работы вместо единого agentic loop:

1. **Кнопка "Фин. отчёт по лоту"** — бэкенд собирает ВСЕ данные в 1 JSON (SQL + калькуляторы, 0 токенов) → 1 вызов AI → экспресс инвест-отчёт
2. **Кнопка "Портфель по бюджету"** — бэкенд подбирает лоты + ROI + рассрочка + депозит → 1 вызов AI → анализ стратегий
3. **Свободный чат** — agentic loop как раньше (для нестандартных вопросов)

### Новые файлы
- `backend/services/report_builder.py` — сборщик JSON для отчётов (build_lot_report_data, build_portfolio_data, slim_deposit, slim_roi)

### Изменённые файлы
- `backend/services/ai_chat.py`:
  - LOT_REPORT_PROMPT, PORTFOLIO_PROMPT (шаблоны для AI)
  - stream_lot_report(), stream_portfolio_report() — SSE streaming
  - ADVISOR_INSTRUCTION обновлён (компактный, для риэлтора)
  - reasoning={"effort": "low"}, max_output_tokens=4000 для отчётов
- `backend/app.py`:
  - ChatRequest: + mode, lot_code, building, budget
  - Роутинг: lot_report → stream_lot_report(), portfolio → stream_portfolio_report()
- `frontend/src/pages/Chat.jsx`:
  - Две кнопки быстрого действия (📊 Фин. отчёт / 💼 Портфель)
  - Модалка ввода кода лота
  - Модалка бюджета с пресетами (5/10/15/20/30/50 млн)
  - sendReport() + общий handleStream()

### Оптимизации скорости
- Отчёт по лоту: ~7 сек (было 20-30 сек через agentic loop) — ускорение 3-4x
- reasoning: "low" вместо "high" (данные готовы, AI только форматирует)
- max_output_tokens: 4000 вместо 16000
- slim_deposit() — убраны yearly_details из deposit_comparison
- slim_roi() — убраны highlights, только totals
- strategy_b: limit 5 лотов вместо 10

### Коммиты
- `6d54de2` — feat: AI Chat v2 — три режима
- `a70b0bb` — effort low + max_output_tokens 4000
- `0751bf1` — slim_deposit + slim_roi + limit 5

### Бэклог (после v0.9.3)
- 🔴 PDF инвест-отчёт в стиле RIZALTA (зелёный/золотой) + кнопка в чате
- 🔴 Деплой v0.9.3 на PROD
- 🟡 Формат B полный Investment Memo (IRR/NPV/Sensitivity Analysis)
- 🟡 Мониторинг стоимости GPT-5.2
- 🟡 Миграция на российский LLM
