# RIZALTA WebApp — Claude Code Context

## Версия
**v0.8.4** (Phase 3.2.2 complete + search & PDF fixes)

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

## Рабочая директория
`/opt/webapp` (порт 8003)

## Структура
```
/opt/webapp/
├── backend/
│   ├── .env                          # Secrets (NOT in git)
│   ├── .env.example                  # Template
│   ├── app.py                        # FastAPI, порт 8003, lifespan, 42 endpoints
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
│       ├── payment_pdf_generator.py # PDF вариантов оплаты (NEW v0.8.4)
│       ├── calc_xlsx_generator.py   # Excel ROI (+ Corp3 JSON support)
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
│   │       ├── Catalog.jsx           # Шахматка К1+К2 + поиск по коду (NEW v0.8.4)
│   │       ├── Corp3.jsx             # Шахматка К3 (282 лота, whitelist)
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

## API (42 endpoints, v0.8.4)
```
# Общие
GET  /api/health                      # version: "0.8.4"
GET  /api/lots                        # прокси к PROD боту :8000
GET  /api/lots/search                 # Поиск по коду (К1+К2+К3) — NEW v0.8.4

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
GET  /api/download-xlsx/{code}        # ?building= для К3 — NEW v0.8.4
GET  /api/download-compare-pdf        # ?amount=X&years=11&area=26.8
GET  /api/payment-pdf                 # ?price=&code= — NEW v0.8.4

# Заявки (реальные уведомления TG + Email)
POST /api/book-showing                # {name, phone, lot_code, comment}

# Файлы (whitelist)
GET  /api/files/presentations/{key}   # PDF презентации
GET  /api/files/documents/{key}       # PDF договоры
GET  /api/files/videos/{key}          # Видео (streaming)

# Whitelist / Corp3
GET  /api/access/check                # Header: X-Access-Token → {level}
GET  /api/corp3/lots                  # Whitelist only, 282 лота
GET  /api/corp3/layout/{code}         # Whitelist only, JPG планировки

# Новости (4 вкладки)
GET  /api/news/currency               # USD/EUR/CNY через cbr-xml-daily.ru
GET  /api/news/weather                # Погода Белокуриха (Open-Meteo)
GET  /api/news/flights                # Авиабилеты (Aviasales)
GET  /api/news/digest                 # RSS: Ведомости, Коммерсантъ, РБК (10-15 новостей)

# AI Чат (Phase 3.2.2)
POST /api/chat                        # SSE stream + action JSON, rate limited

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
- **К1+К2**: `/opt/bot/properties.db` таблица `units` (358 лотов)
- **К3**: `/opt/bot-dev/data/corp3_units.json` (282 лота)
- Планировки К3: `/opt/bot-dev/data/corp3_layouts/`
- Поиск `/api/lots/search` ищет в обоих источниках

## Env переменные (backend/.env)
```
TELEGRAM_BOT_TOKEN    # Токен бота (для уведомлений)
MANAGER_EMAIL         # Email менеджеров
BOT_EMAIL             # Email отправителя
SMTP_HOST             # SMTP сервер
SMTP_PORT             # SMTP порт
SMTP_USER             # SMTP логин
SMTP_PASSWORD         # SMTP пароль
MANAGER_CHAT_ID       # ID чата менеджера в Telegram
OPENAI_API_KEY        # Ключ OpenAI (тот же что у бота)
OPENAI_MODEL          # gpt-4o-mini
OPENAI_MAX_TOKENS     # 2000
SHOWS_GROUP_ID        # ID Telegram группы показов
```

## Whitelist система (Phase 3.1)
- Токен передаётся через URL: `?token=XXXXX` → сохраняется в localStorage
- Backend проверяет через `X-Access-Token` header или `?token=` query param
- `webapp.db` → таблица `access_tokens` (token, name, level, created_at)
- `init_webapp_db()` + `seed_token()` вызываются в lifespan при старте
- Frontend: `utils/auth.js` — captureTokenFromURL, verifyAccess, authFetch, getToken
- Home.jsx показывает кнопку "Корпус 3" только при `accessLevel === 'white'`
- Corp3.jsx загружает данные через authFetch, показывает 403 если нет доступа
- LotDetail.jsx: для К3 планировок добавляет ?token= (если его нет в URL)
- Токен К3: MkKGpwCAsq6IF3RtRH7bvg

## Git теги
- `v0.5.0-stable` — Phase 3.1 (whitelist)
- `v0.6.1-pre-phase322` — точка отката до Phase 3.2.2
- `v0.8.0-stable` — Phase 3.2.2 завершена
- `v0.8.2-xlsx-fix` — фикс Excel для К3
- `v0.8.3-payment-pdf` — PDF вариантов оплаты
- `v0.8.4-search-complete` — поиск по коду лота

## Команды
```bash
# Backend
sudo systemctl restart webapp.service
sudo systemctl status webapp.service
sudo journalctl -u webapp.service -n 50 --no-pager

# Frontend build
cd /opt/webapp/frontend && npm run build

# Полный деплой
cd /opt/webapp && git pull && npm run build --prefix frontend && systemctl restart webapp

# Тесты
curl -s http://127.0.0.1:8003/api/health
curl -s "http://127.0.0.1:8003/api/lots/search?code=А200"
curl -s "http://127.0.0.1:8003/api/download-xlsx/В800?building=3" -o /tmp/test.xlsx
```

## TODO (Phase 3.3+)
1. Function calling в AI чате (инструменты: расчёт, поиск лота, бронирование)
2. Когда К3 выходит в продажу — убрать проверку токена
3. История чата (сохранение сессий)
4. Push-уведомления для задач секретаря
5. "Взять" → автосоздание задачи в секретаре (бот-сайд)

## ⚠️ ПРАВИЛА РАЗРАБОТКИ

### Завершение сессии — ОБЯЗАТЕЛЬНЫЙ ЧЕКЛИСТ
1. Обновить docs: CLAUDE.md, TASK_MAP.md, RIZALTA_CURRENT.md, RIZALTA_TASKS.md, RIZALTA_CONTEXT.md
2. Общие docs (bot-dev/docs/) — ДОПОЛНЯТЬ, не затирать (параллельный бот-чат)
3. Коммит + push webapp: `cd /opt/webapp && git add -A && git commit && git push origin webapp`
4. Коммит + push bot-dev: `cd /opt/bot-dev && git add docs/ && git commit && git push`
5. Копировать в PROD: `cp /opt/bot-dev/docs/RIZALTA_*.md /opt/bot/docs/`
6. Коммит + push PROD: `cd /opt/bot && git add docs/ && git commit && git push`
7. Выдать полный промпт для нового чата (по шаблону SESSION_END_TEMPLATE.md)

### Шаблон завершения
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/SESSION_END_TEMPLATE.md
