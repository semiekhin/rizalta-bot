# RIZALTA WebApp — Claude Code Context

## Версия
**v0.6.1** (Phase 3.2.1 complete)

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
│   ├── .env.example                  # Template
│   ├── app.py                        # FastAPI, порт 8003, lifespan
│   ├── webapp.db                     # Whitelist tokens (NOT in git)
│   └── services/
│       ├── calculator.py             # ROI расчёт
│       ├── installment_calculator.py # Варианты рассрочки
│       ├── deposit_calculator.py     # Депозит сценарии (base/opt/pess)
│       ├── investment_compare.py     # RIZALTA vs Депозит расчёт
│       ├── compare_pdf_generator.py  # PDF сравнения (wkhtmltopdf)
│       ├── kp_pdf_generator.py       # PDF КП (wkhtmltopdf)
│       ├── calc_xlsx_generator.py    # Excel ROI
│       ├── notifications.py          # Telegram + Email уведомления
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
│   │       ├── Chat.jsx              # AI чат (заглушка)
│   │       ├── Presentations.jsx     # PDF презентации
│   │       ├── Documents.jsx         # Договоры
│   │       ├── Media.jsx             # Видео
│   │       ├── Booking.jsx           # Запись на показ (с валидацией)
│   │       ├── News.jsx              # Курсы валют ЦБ
│   │       ├── Secretary.jsx         # Заглушка → бот
│   │       └── Fixation.jsx          # Заглушка → бот
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
- **БД**: SQLite `/opt/bot/properties.db` (PROD, read-only) + `/opt/webapp/backend/webapp.db` (whitelist tokens)
- **PDF**: wkhtmltopdf (KP + compare)
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

## API (все endpoints v0.6.1)
```
# Общие
GET  /api/health                      # version: "0.6.1"
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

## TODO (Phase 3.2.2+)
1. Chat.jsx → полноценный AI чат с SSE streaming (DeepSeek V3.2 через OpenRouter)
2. Function calling в AI чате
3. Когда К3 выходит в продажу — убрать проверку токена
