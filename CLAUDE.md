# RIZALTA WebApp — Claude Code Context

## Версия
**v0.7.0** (Phase 3.2.2 complete)

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
- `/opt/bot/properties.db` — читаем, но НЕ пишем

## Рабочая директория
`/opt/webapp` (порт 8003)

## Структура
```
/opt/webapp/
├── backend/
│   ├── .env                          # Secrets (NOT in git)
│   ├── .env.example                  # Template (+OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS)
│   ├── app.py                        # FastAPI, порт 8003, lifespan, ~580+ lines
│   ├── webapp.db                     # Whitelist tokens (NOT in git)
│   ├── secretary.db                  # Secretary tasks (NOT in git)
│   ├── config/
│   │   └── instructions.txt          # AI system prompt
│   ├── data/
│   │   └── README.md                 # Note to copy rizalta_finance.json
│   └── services/
│       ├── calculator.py             # ROI расчёт
│       ├── installment_calculator.py # Варианты рассрочки
│       ├── deposit_calculator.py     # Депозит сценарии (base/opt/pess)
│       ├── investment_compare.py     # RIZALTA vs Депозит расчёт
│       ├── compare_pdf_generator.py  # PDF сравнения (wkhtmltopdf)
│       ├── kp_pdf_generator.py       # PDF КП (wkhtmltopdf)
│       ├── calc_xlsx_generator.py    # Excel ROI
│       ├── notifications.py          # Telegram + Email уведомления
│       ├── ai_chat.py               # AI chat with OpenAI streaming
│       ├── data_loader.py           # Loads finance data + instructions
│       ├── intent_router.py         # Intent classification (quick patterns + GPT)
│       ├── secretary_db.py          # SQLite CRUD for tasks (secretary.db)
│       ├── secretary_ai.py          # GPT task parsing
│       ├── rclick_service.py        # rclick.ru auth + fixation
│       ├── calc_universal.py
│       └── calculations.py
├── frontend/                         # Preact + Tailwind CSS 4 + Vite 7
│   ├── src/
│   │   ├── App.jsx                   # Роутер (11 screens) + навигация + auth
│   │   ├── main.jsx                  # Entry point
│   │   ├── utils/
│   │   │   └── auth.js               # Token capture, verify, authFetch
│   │   └── pages/
│   │       ├── Home.jsx              # Меню 2x4 + условная кнопка К3
│   │       ├── Catalog.jsx           # Шахматка К1+К2 (358 лотов)
│   │       ├── Corp3.jsx             # Шахматка К3 (282 лота, whitelist)
│   │       ├── LotDetail.jsx         # Карточка лота + 5 модалок
│   │       ├── Chat.jsx              # AI чат (SSE streaming + action buttons)
│   │       ├── Presentations.jsx     # PDF презентации
│   │       ├── Documents.jsx         # Договоры
│   │       ├── Media.jsx             # Видео
│   │       ├── Booking.jsx           # Запись на показ (с валидацией)
│   │       ├── News.jsx              # Курсы валют ЦБ
│   │       ├── Secretary.jsx         # Календарь + управление задачами + AI парсинг
│   │       └── Fixation.jsx          # rclick авторизация + формы фиксации
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
- **БД**: SQLite `/opt/bot/properties.db` (PROD, read-only) + `/opt/webapp/backend/webapp.db` (whitelist tokens) + `/opt/webapp/backend/secretary.db` (tasks)
- **PDF**: wkhtmltopdf (KP + compare)
- **AI**: OpenAI API (streaming SSE) — chat, intent routing, task parsing
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

## API (все endpoints v0.7.0)
```
# Общие
GET  /api/health                      # version: "0.7.0"
GET  /api/lots                        # прокси к PROD боту :8000

# Калькуляторы
POST /api/calculate-roi               # {area, price}
POST /api/installment                 # {price}
POST /api/compare-deposit             # {amount, years, scenario}

# Генерация документов
POST /api/generate-kp                 # {code, include_18m, full_payment}
POST /api/generate-xlsx               # {code}
GET  /api/download-kp/{code}          # ?type=100|12m|full
GET  /api/download-xlsx/{code}
GET  /api/download-compare-pdf        # ?amount=X&years=11&area=26.8

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

# Курсы валют
GET  /api/news/currency               # USD/EUR/CNY через cbr-xml-daily.ru

# AI Чат (Phase 3.2.2)
POST /api/chat                        # SSE stream или action JSON, rate limited

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
POST /api/fixation/auth               # rclick.ru логин
GET  /api/fixation/status             # Проверка авторизации
POST /api/fixation/create             # Создать фиксацию
POST /api/fixation/logout             # Выход
```

## Whitelist система (Phase 3.1)
- Токен передаётся через URL: `?token=XXXXX` → сохраняется в localStorage
- Backend проверяет через `X-Access-Token` header или `?token=` query param
- `webapp.db` → таблица `access_tokens` (token, name, level, created_at)
- `init_webapp_db()` + `seed_token()` вызываются в lifespan при старте
- Frontend: `utils/auth.js` — captureTokenFromURL, verifyAccess, authFetch, getToken
- Home.jsx показывает кнопку "Корпус 3" только при `accessLevel === 'white'`
- Corp3.jsx загружает данные через authFetch, показывает 403 если нет доступа
- Corp3 данные: `/opt/bot-dev/data/corp3_units.json` (area, price, layout_path)
- Corp3 планировки: `/opt/bot-dev/data/corp3_layouts/`

## БД (таблица units в properties.db)
```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY,
    code TEXT,           -- Кириллица! А119, В712
    project TEXT,
    building INTEGER,    -- 1 или 2
    floor INTEGER,       -- 1-9
    rooms INTEGER,
    area_m2 REAL,
    price_rub INTEGER,
    price_per_m2_rub INTEGER,
    completion TEXT,
    layout_url TEXT,
    page_url TEXT,
    status TEXT DEFAULT 'available',
    block_section INTEGER DEFAULT 1
);
```
358 лотов К1+К2. Corp3 — 282 лота в JSON.

## Уведомления (Phase 3.2.1)
- `backend/services/notifications.py` — send_telegram_message, send_email, notify_showing_request
- Telegram: httpx → Bot API, поддержка нескольких chat_id через запятую
- Email: smtplib → SMTP с HTML форматированием
- Конфиг в `backend/.env` (TELEGRAM_BOT_TOKEN, MANAGER_CHAT_ID, SMTP_*)
- book-showing всегда возвращает ok=true (даже если уведомление не дошло)

## AI Чат (Phase 3.2.2)
- `backend/services/ai_chat.py` — OpenAI streaming через SSE
- `backend/services/data_loader.py` — загрузка rizalta_finance.json + instructions.txt
- `backend/services/intent_router.py` — классификация интентов (быстрые паттерны + GPT fallback)
- `backend/config/instructions.txt` — системный промпт для AI
- `backend/data/rizalta_finance.json` — финансовые данные (копировать вручную, см. README.md)
- Frontend: `Chat.jsx` — полноценный SSE streaming + кнопки действий
- Конфиг в `backend/.env` (OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS)
- Rate limiting на `/api/chat`

## Секретарь (Phase 3.2.2)
- `backend/services/secretary_db.py` — SQLite CRUD для задач (secretary.db)
- `backend/services/secretary_ai.py` — GPT парсинг текста в структурированную задачу
- `backend/secretary.db` — БД задач (NOT in git, см. .gitignore)
- Frontend: `Secretary.jsx` — лента календаря + управление задачами + AI парсинг
- 8 API endpoints для полного CRUD + AI парсинг

## Фиксация (Phase 3.2.2)
- `backend/services/rclick_service.py` — авторизация и фиксация на rclick.ru
- Frontend: `Fixation.jsx` — авторизация rclick + формы фиксации
- 4 API endpoints: auth, status, create, logout

## Команды
```bash
# Backend
sudo systemctl restart webapp.service
sudo systemctl status webapp.service
sudo journalctl -u webapp.service -n 50 --no-pager

# Frontend build
cd /opt/webapp/frontend && npm run build

# Тесты
curl -s http://127.0.0.1:8003/api/health
curl -s http://127.0.0.1:8003/api/lots | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ok'], len(d.get('lots',[])))"
curl -s "http://127.0.0.1:8003/api/download-compare-pdf?amount=5000000" -o /tmp/test.pdf && file /tmp/test.pdf
curl -s http://127.0.0.1:8003/api/secretary/tasks?date=2026-02-11
curl -s http://127.0.0.1:8003/api/fixation/status
```

## Nginx
```nginx
server {
    listen 443 ssl;
    server_name webapp.rizaltaservice.ru;
    root /opt/webapp/frontend/dist;
    location /api/ { proxy_pass http://127.0.0.1:8003; }
    location / { try_files $uri $uri/ /index.html; }
}
```

## TODO (Phase 3.3+)
1. Function calling в AI чате (инструменты: расчёт, поиск лота, бронирование)
2. Когда К3 выходит в продажу — убрать проверку токена
3. История чата (сохранение сессий)
4. Push-уведомления для задач секретаря
