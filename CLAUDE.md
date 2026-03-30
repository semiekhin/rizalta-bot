# RIZALTA WebApp v0.9.8 — Контекст для Claude

## ⛔ НИКОГДА НЕ ТРОГАТЬ

- `/opt/webapp` (PROD) — деплой ТОЛЬКО через `deploy-to-prod.sh`
- `/opt/bot`, `/opt/bot-dev`, `/opt/bot-max-dev` — чужие сервисы, НЕ редактировать
- `/opt/bot/properties.db` — общая БД экосистемы, схему НЕ менять
- Вся работа ТОЛЬКО в `/opt/webapp-dev` (DEV)
- venv pip шебанг сломан — ставить через `python3 -m pip install --break-system-packages`

## Экосистема RIZALTA

Три параллельных сервиса на одном сервере (72.56.64.91:2222):

| Сервис | DEV | PROD | Назначение |
|--------|-----|------|-------------|
| Rizalta Bot | /opt/bot-dev :8002 | /opt/bot :8000 | Telegram-бот |
| Rizalta MAX | /opt/bot-max-dev | — | MAX messenger бот |
| Rizalta WebApp | /opt/webapp-dev :8004 | /opt/webapp :8003 | Веб-приложение (этот проект) |

**Общая БД:** `/opt/bot/properties.db` — единый каталог лотов. Все 3 сервиса ЧИТАЮТ. WebApp также делает INSERT в таблицу `bookings`.

**Общие ресурсы** (менять осторожно — зависят другие сервисы):
- `/opt/bot-dev/docs/` — ddu.pdf, arenda.pdf (RAG документы)
- `/opt/bot-dev/presentations/`, `/opt/bot-dev/videos/`
- `/opt/bot/docs/` — документы для скачивания

## Проект

Standalone веб-приложение, дублирующее функциональность Telegram-бота RIZALTA. Причина: замедление Telegram в РФ. Целевая аудитория — риелторы и менеджеры по продажам (НЕ клиенты).

## Инфраструктура

| | DEV | PROD |
|---|---|---|
| URL | https://dev-webapp.rizaltaservice.ru | https://webapp.rizaltaservice.ru |
| Путь | /opt/webapp-dev | /opt/webapp |
| Порт | 8004 | 8003 |
| Systemd | webapp-dev.service | webapp.service |
| Favicon | зелёный (DEV) | золотой (PROD) |

## Сервисы (systemd)

| Сервис | Порт | Команда |
|--------|------|---------|
| webapp.service | 8003 | uvicorn app:app --host 127.0.0.1 --port 8003 |
| webapp-dev.service | 8004 | uvicorn app:app --host 127.0.0.1 --port 8004 |
| webhook-webapp.service | 9001 | webhook_receiver.py (GitHub auto-deploy) |

Nginx: `/api/` → backend, `/` → frontend/dist (SPA fallback), `/webhook` → 9001 (только dev).

## Стек

- **Frontend:** Preact + Tailwind CSS 4 + Vite 7
- **Backend:** Python 3.12, FastAPI, uvicorn
- **БД:** SQLite — properties.db (лоты + bookings), webapp.db (whitelist), secretary.db (задачи)
- **AI:** YandexGPT gpt-oss-120b (OpenAI-compatible API) — agentic loop, reports, RAG
- **RAG:** PyMuPDF + scikit-learn TF-IDF (ddu.pdf 11стр, arenda.pdf 54стр, 487 чанков)
- **PDF:** wkhtmltopdf (КП, сравнение, МГП, ипотека, оплата, инвест-отчёты)
- **Уведомления:** Telegram Bot API (httpx) + SMTP email
- **Шрифт:** Montserrat (400/500/600)

## Архитектура

### Backend (backend/)

**app.py** — FastAPI, 40+ эндпоинтов, lifespan (init webapp.db, secretary.db, rclick, RAG), CORS(*), GZip, rate limiter (10 req/min на chat).

**services/ai_chat.py** — 4 пути в `/api/chat`:
1. **Navigation** (0 AI) — regex паттерны → JSON action (open_shahmatka, send_presentation, ...)
2. **Простой чат** (YandexGPT) — общие вопросы, финансовые концепции, стриминг по 4 символа
3. **Agentic loop** (YandexGPT + 5 tools) — лот-коды, ROI, рассрочка. Max 5 раундов tool calling
4. **RAG** — вопросы о договорах (дду, аренда, штраф, неустойка) → TF-IDF поиск → inject в system prompt

Клиент: OpenAI SDK с `base_url=https://llm.api.cloud.yandex.net/v1`, header `x-folder-id`.
Модель: `gpt-oss-120b/latest` (без модерации, function calling, streaming).

**services/tool_definitions.py** — 5 инструментов:
- `search_lots` — поиск по code/building/area/price/status
- `get_lot_details` — детали лота
- `calculate_roi` — 11-летняя проекция (2025-2035)
- `calculate_installment` — 2 программы (12 мес 0%, 18 мес +9%)
- `compare_with_deposit` — сравнение с депозитом (3 сценария)

**services/report_builder.py** — сбор данных из БД (0 AI токенов):
- `build_lot_report_data(code, building)` — лот + ROI + метрики + рассрочка + депозит
- `build_portfolio_data_v2(budget)` — 3 сценария (premium/portfolio/leverage), round-robin по корпусам

**services/rag_service.py** — PDF extraction (PyMuPDF) + TF-IDF (scikit-learn):
- Документы: ddu.pdf, arenda.pdf из RAG_DOCS_DIR
- 487 чанков (~600 символов, перекрытие 100)
- `search_documents(query, top_k=5)` — cosine similarity > 0.01
- Init при старте в lifespan (не-фатальный)

**services/intent_router.py** — 7 навигационных интентов (regex), RAG skip логика для вопросов о содержании документов.

**services/strategy_pdf_generator.py** — ~800 строк, 4-страничный PDF (Montserrat, green/gold/cream branding).

**services/tranche_mortgage_calculator.py** — 3 транша, 20 лет, SERVICE_FEE 150K, 4 варианта ПВ (20.1-50.1%).

**services/mortgage_calculator.py** — Совкомбанк, аннуитетный с grace period, 30 лет.

### Frontend (frontend/src/)

**App.jsx** — 11 экранов (Home, Catalog, LotDetail, Chat, Secretary, Fixation, News, Booking, Presentations, Documents, Media). Bottom nav: Главная / Чат / Лоты. Lazy loading + Suspense.

**pages/Home.jsx** — Menu grid 2x4, hero с логотипом, "Записаться на показ".

**pages/LotDetail.jsx** — 11 модалок (ROI, показ, КП, рассрочка, депозит, МГП, ипотека Совкомбанк, транш. ипотека Сбербанк, инвест. сводка). Grid 2x5 с 3D-эффектом.

**pages/Chat.jsx** — SSE streaming (fetch + TextDecoder), auto-scroll, textarea auto-resize.

**utils/auth.js** — token в localStorage, X-Access-Token header, verifyAccess() на сервер. Система деактивирована (готова для К4).

## БД

### properties.db (/opt/bot/ — READ + INSERT bookings)
- **units**: code, building, floor, rooms, area_m2, price_rub, layout_url, status
- **bookings**: chat_id, specialist, booking_date, status(pending), contact_info, realtor
- **projects**: code, name, description

### webapp.db (backend/)
- **access_tokens**: token, name, level(white), created_at
- **rclick_sessions**: phone, cookies, agent_name, last_used

### secretary.db (backend/)
- **tasks**: user_id(webapp), task, date, time, client, priority(normal), done, created_at. Index: (user_id, date)

## .env ключи

| Ключ | Назначение |
|------|-------------|
| TELEGRAM_BOT_TOKEN | Telegram Bot API |
| MANAGER_EMAIL | Email менеджера |
| BOT_EMAIL | Email бота (отправитель) |
| SMTP_HOST/PORT/USER/PASSWORD | Почта (mail.ru) |
| MANAGER_CHAT_ID | Telegram chat для уведомлений |
| SHOWS_GROUP_ID | Telegram группа показов |
| OPENAI_API_KEY | OpenAI (legacy, не используется) |
| OPENAI_MODEL | gpt-5.2 (legacy) |
| OPENAI_MAX_TOKENS | 16000 (legacy) |
| YANDEX_API_KEY | YandexGPT API |
| YANDEX_FOLDER_ID | Yandex Cloud folder |
| YANDEX_MODEL | gpt://folder/gpt-oss-120b/latest |
| RAG_DOCS_DIR | /opt/bot-dev/docs (PDF для RAG) |
| WEBAPP_DB | ./webapp.db |
| WEBAPP_ROOT | /opt/webapp-dev (DEV) или /opt/webapp (PROD) |
| DIST_PATH | ../frontend/dist |
| PROPERTIES_DB | /opt/bot/properties.db |
| PRESENTATIONS_DIR | /opt/bot-dev/presentations |
| DOCUMENTS_DIR | /opt/bot/docs |
| VIDEOS_DIR | /opt/bot-dev/videos |
| MAX_BOT_TOKEN | Токен MAX бота |
| MAX_WEBAPP_URL | URL webapp для MAX |

## Фирменный стиль

### Цвета (index.css @theme)
- **Зелёный:** #263524 (фон), #1A2619 (hover), #2F4A2D (карточки), #1C2A1B (inputs)
- **Cream:** #F2EBD9 (текст), #C8BBAA (вторичный), #A89880 (muted)
- **Золото:** #D4A84B (CTA), #DEAF58 (hover), #C09940 (dark)
- **Статус:** #5B8C5A (success), #D4544E (error), #FAFAF5 (white)

### PDF branding
- Header: #313D20 (зелёный), title bar: #DCB764 (золото), фон: #F6F0E3 (cream)
- Dark branding (lot summary): #263524 фон, #D4A84B золото

## Правила

### Деплой workflow
1. Код в `/opt/webapp-dev` → commit → push в `webapp` ветку
2. Webhook автоматически: git pull + build + restart DEV (2-3 сек)
3. Проверка: https://dev-webapp.rizaltaservice.ru
4. Деплой в prod: `bash /opt/webapp-dev/deploy-to-prod.sh` (только после одобрения)

### Что нельзя трогать
- PROD `/opt/webapp/` — только через deploy скрипт
- `/opt/bot/properties.db` — схема НЕ меняется
- `/opt/bot/`, `/opt/bot-dev/`, `/opt/bot-max-dev/` — чужие сервисы

### Уроки из ошибок
- **venv pip шебанг:** указывает на PROD. Ставить через `python3 -m pip install --break-system-packages`
- **GPT-5.2 + reasoning:** max_tokens → max_completion_tokens (иначе ошибка)
- **YandexGPT модерация:** нативный API модерирует жёстче чем OpenAI-compatible. Использовать только OpenAI-compatible endpoint
- **gpt-oss-120b:** без модерации, streaming, function calling, tool role — лучший выбор
- **SSE streaming headers:** nginx должен пропускать (proxy_buffering off)
- **RFC 5987 filename:** для кириллицы в Content-Disposition (lot_summary_pdf_generator.py)
- **Нормализация лот-кодов:** Latin → Cyrillic (A→А, B→В) в tool_definitions.py

## DevOps

### Auto-deploy DEV
`webhook_receiver.py` на порту 9001. GitHub webhook → HMAC SHA-256 проверка → git pull + npm run build + systemctl restart (120s timeout).

### Деплой PROD
```bash
bash /opt/webapp-dev/deploy-to-prod.sh
```
Проверка DEV health → git pull в /opt/webapp → build → restart → health check → автооткат при ошибке.

### Команды
```bash
# DEV
sudo systemctl restart webapp-dev.service
sudo journalctl -u webapp-dev.service -n 50 --no-pager
curl -s http://127.0.0.1:8004/api/health

# PROD
sudo systemctl restart webapp.service
curl -s http://127.0.0.1:8003/api/health

# Frontend build
cd /opt/webapp-dev/frontend && npm run build

# Webhook
sudo systemctl status webhook-webapp.service
```

## Workflow

- **Claude.ai** = архитектор (ТЗ, анализ, спецификации)
- **Claude Code** = исполнитель (код прямо на сервере)
- Git: ветка `webapp`, push → webhook автоупдейт DEV
- Frontend build: `cd frontend && npm run build`
- Health check: `curl -s http://127.0.0.1:8004/api/health`

### Завершение сессии
1. Обновить CLAUDE.md, SESSION_LOG.md, BACKLOG.md
2. Commit + push в `webapp`
3. Выдать компактный промпт для нового чата
