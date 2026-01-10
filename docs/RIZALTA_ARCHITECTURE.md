# Архитектура RIZALTA

## Общая схема
```
┌─────────────────────────────────────────────────────────────┐
│                         PROD                                 │
│  Telegram → Cloudflare Tunnel → :8000 → FastAPI (webhook)   │
├─────────────────────────────────────────────────────────────┤
│                         DEV                                  │
│  Telegram → polling (run_polling.py)                        │
│  Mini App → Cloudflare Tunnel → :8002 → FastAPI (API)       │
├─────────────────────────────────────────────────────────────┤
│                      MINI APP                                │
│  Vercel: rizalta-miniapp.vercel.app                         │
│  /api/* → PROD туннель                                      │
│  /api-dev/* → DEV туннель                                   │
└─────────────────────────────────────────────────────────────┘
```

## Структура проекта
```
/opt/bot-dev/
├── app.py                    # Главный файл (webhook, роутинг, API)
├── run_polling.py            # DEV режим (polling)
├── config/
│   └── settings.py           # Константы, кнопки меню
├── handlers/
│   ├── menu.py               # Главное меню
│   ├── ai_chat.py            # AI диалоги
│   ├── booking.py            # Онлайн-показы
│   ├── booking_calendar.py   # Календарь + групповые заявки
│   ├── kp.py                 # КП + навигация + пагинация
│   ├── calc_dynamic.py       # Расчёты ROI
│   ├── secretary.py          # AI-секретарь
│   └── media.py              # Медиа/презентации
├── services/
│   ├── intent_router.py      # GPT Intent Router
│   ├── telegram.py           # API Telegram
│   ├── notifications.py      # Уведомления
│   ├── units_db.py           # БД лотов (348 лотов)
│   ├── kp_pdf_generator.py   # PDF КП
│   ├── calc_universal.py     # Расчёты рассрочки
│   └── secretary_db.py       # БД секретаря
├── data/
│   ├── units.json            # Данные лотов
│   └── rizalta_finance.json  # Финансовые данные
└── *.db                      # SQLite базы
```

## Systemd сервисы
```
PROD:
├── rizalta-bot.service         (uvicorn :8000, webhook)
└── cloudflare-rizalta.service  (туннель)

DEV:
├── rizalta-bot-dev.service     (polling)
├── rizalta-dev-api.service     (uvicorn :8002)
└── rizalta-dev-tunnel.service  (туннель)
```

## База данных

### properties.db — 348 лотов
- Корпус 1 «Family»: 244 лота
- Корпус 2 «Business»: 104 лота
- Таблица `bookings`: taken_by_id, taken_by_name, group_message_id

### secretary.db
- `tasks` — задачи пользователей
- `users` — timezone (default: 3 = Москва)

## Mini App

**URL:** https://rizalta-miniapp.vercel.app
- PROD: без параметров → `/api/*` → PROD туннель
- DEV: `?env=dev` → `/api-dev/*` → DEV туннель

**Почему Vercel proxy:**
- `*.trycloudflare.com` блокируется в РФ
- Vercel.app не блокируется

**При смене URL туннеля:**
```bash
nano /opt/miniapp/vercel.json
cd /opt/miniapp && vercel --prod
```

## GPT Intent Router

Файл: `services/intent_router.py`

1. **QUICK_PATTERNS** — точные совпадения кнопок (без GPT)
2. **Regex паттерны** — коды лотов, бюджеты
3. **GPT классификация** — сложные запросы

Приоритет: кнопки → regex → GPT
