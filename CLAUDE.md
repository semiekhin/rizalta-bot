# RIZALTA WebApp — Claude Code Context

## Версия
**v0.3.0** → цель: **v2.0** (standalone web app)

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
│   ├── app.py                    # FastAPI, порт 8003
│   └── services/                 # Калькуляторы, генераторы PDF/XLSX
│       ├── calculator.py         # ROI расчёт
│       ├── installment_calculator.py
│       ├── deposit_calculator.py
│       ├── kp_pdf_generator.py   # PDF КП (wkhtmltopdf)
│       ├── calc_xlsx_generator.py # Excel ROI
│       ├── calc_universal.py
│       ├── calculations.py
│       └── investment_calc.py
├── frontend/                     # Preact + Tailwind CSS 4 + Vite 7
│   ├── src/
│   │   ├── App.jsx               # Роутер + навигация
│   │   ├── main.jsx              # Entry point
│   │   └── pages/
│   │       ├── Home.jsx
│   │       ├── Catalog.jsx       # Шахматка лотов
│   │       ├── LotDetail.jsx     # Карточка лота + модалки
│   │       └── Chat.jsx          # AI чат (ЗАГЛУШКА)
│   ├── public/
│   │   ├── fonts/                # Montserrat Regular, Medium, SemiBold
│   │   └── images/logo.png       # RIZALTA лого
│   └── vite.config.js            # Preact aliases, Tailwind plugin
└── venv/
```

## Стек
- **Frontend**: Preact (React-compatible), Tailwind CSS 4, Vite 7
- **Backend**: Python 3.12, FastAPI 0.109, uvicorn
- **LLM**: DeepSeek V3.2 через OpenRouter (для AI чата)
- **БД**: SQLite `/opt/bot/properties.db` (PROD, read-only)
- **PDF**: wkhtmltopdf
- **Nginx**: proxy /api/ → 127.0.0.1:8003, static из frontend/dist

## Фирменный стиль RIZALTA
### Цвета (из лого — тёмно-зелёный фон, кремовый текст)
```
--rizalta-green:       #2D3B2D   /* основной фон */
--rizalta-green-dark:  #1E2A1E   /* hover, darker */
--rizalta-green-light: #3D4F3D   /* карточки, lighter */
--rizalta-cream:       #F0E6D3   /* основной текст/акценты */
--rizalta-cream-dark:  #D4C4A8   /* secondary текст */
--rizalta-gold:        #C9A96E   /* CTA кнопки */
--rizalta-white:       #FAFAF5   /* off-white фоны */
--rizalta-error:       #D4544E
--rizalta-success:     #5B8C5A
```
### Шрифт: Montserrat (Regular 400, Medium 500, SemiBold 600)
### Текущий UI: slate-900 + amber-500 (НЕПРАВИЛЬНО, нужно заменить на бренд)

## БД (таблица units)
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
358 лотов, все available. Коды кириллические (А, В).

## API (текущие endpoints)
```
GET  /api/health
GET  /api/lots                    # прокси к PROD боту :8000
POST /api/calculate-roi           # {area, price}
POST /api/installment             # {price}
POST /api/compare-deposit         # {amount, years, scenario}
POST /api/generate-kp             # {code, include_18m, full_payment}
POST /api/generate-xlsx           # {code}
GET  /api/download-kp/{code}      # ?type=100|12m|full
GET  /api/download-xlsx/{code}
POST /api/book-showing            # {name, phone, lot_code} — ЗАГЛУШКА
```

## Что нужно сделать (Phase 2-3)
### Frontend (Phase 2)
1. Применить фирменный стиль (цвета, шрифты, лого) — заменить slate/amber
2. Убрать App.css (дефолтный Vite), починить react/preact конфликт в import
3. Компоненты: Layout (header+nav), Modal (единый), LotCard
4. Chat.jsx → полноценный AI чат с streaming

### Backend (Phase 3)
1. .env + config.py
2. AI chat endpoint: POST /api/chat с SSE streaming
3. LLM: DeepSeek V3.2 через OpenRouter API (OpenAI-совместимый)
4. Function calling: get_kp, calculate_roi, show_installment, compare_deposit, book_showing
5. Системный промпт: /opt/bot/config/instructions.txt + /opt/bot/data/rizalta_knowledge_base.txt
6. Отправка заявок на показ → Telegram бот + email (не просто console.log)
7. systemd сервис

## Команды
```bash
# Backend запуск
cd /opt/webapp/backend && source ../venv/bin/activate
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8003 > /var/log/webapp.log 2>&1 &

# Frontend build
cd /opt/webapp/frontend && npm run build

# Рестарт
pkill -f "uvicorn.*8003"
cd /opt/webapp/backend && source ../venv/bin/activate
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8003 > /var/log/webapp.log 2>&1 &

# Тесты
curl -s http://127.0.0.1:8003/api/health
curl -s http://127.0.0.1:8003/api/lots | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ok'], len(d.get('lots',[])))"
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
