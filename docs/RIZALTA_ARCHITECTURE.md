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

## Сервер (Timeweb)

| Параметр | Значение |
|----------|----------|
| IP | 72.56.64.91 (SSH порт 2222) |
| Локация | Амстердам |
| CPU | 4 vCPU (3.3 ГГц) |
| RAM | 8 GB |
| Диск | 80 GB NVMe |
| SQLite | WAL mode включен |
| Клон | Создан 27.01.2026 (резерв) |


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
│   ├── media.py              # Медиа/презентации
│   ├── corp3.py              # Корпус 3 + whitelist
│   └── mortgage.py           # Ипотечный калькулятор (DEV)
├── services/
│   ├── intent_router.py      # GPT Intent Router
│   ├── telegram.py           # API Telegram
│   ├── notifications.py      # Уведомления
│   ├── units_db.py           # БД лотов (348 лотов)
│   ├── kp_pdf_generator.py   # PDF КП
│   ├── calc_universal.py     # Расчёты рассрочки
│   ├── secretary_db.py       # БД секретаря
│   ├── mortgage_calculator.py # Расчёты ипотеки (DEV)
│   └── mortgage_pdf_generator.py # PDF ипотеки (DEV)
├── data/
│   ├── units.json            # Данные лотов
│   ├── rizalta_finance.json  # Финансовые данные
│   ├── corp3_units.json      # Лоты Корпуса 3 (.gitignore)
│   ├── hidden_buildings.json # Скрытие корпусов
│   └── mortgage_config.json  # Конфиг ипотеки (DEV)
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

### properties.db — 355 лотов
- Корпус 1 «Family»: 253 лота
- Корпус 2 «Business»: 102 лота (СКРЫТ в DEV и PROD через hidden_buildings.json)
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

## 📈 Масштабирование

### Текущие метрики (10.01.2026)
- **Пользователей:** 13 уникальных
- **Запросов:** 282
- **Лотов в базе:** 345
- **WAL mode:** выключен (delete)

### Лимиты текущего стека
| Компонент | Лимит | Действие при достижении |
|-----------|-------|------------------------|
| SQLite | ~200 активных | Включить WAL mode |
| SQLite + WAL | ~500 активных | Мигрировать на Redis |
| Redis | ~2000 активных | Мигрировать на PostgreSQL |
| RAM (8GB) | ~1000 активных | Увеличить RAM или оптимизировать |

### Команда для включения WAL
```bash
sqlite3 /opt/bot/properties.db "PRAGMA journal_mode=WAL;"
sqlite3 /opt/bot/secretary.db "PRAGMA journal_mode=WAL;"
sqlite3 /opt/bot/monitoring.db "PRAGMA journal_mode=WAL;"
```

## 🌐 Cloudflare Named Tunnels

### Конфигурация (обновлено 11.01.2026)

| Туннель | Домен | Порт | Конфиг |
|---------|-------|------|--------|
| rizalta-prod | api.rizaltaservice.ru | 8000 | /root/.cloudflared/config.yml |
| rizalta-dev | dev.rizaltaservice.ru | 8002 | /root/.cloudflared/config-dev.yml |

### Преимущества Named Tunnel:
- URL статический (не меняется при перезапуске)
- Не блокируется провайдерами в РФ
- Не нужны скрипты автообновления webhook

### Команды управления:
```bash
# Список туннелей
cloudflared tunnel list

# Логи
journalctl -u cloudflare-rizalta -f      # PROD
journalctl -u rizalta-dev-tunnel -f      # DEV
```

### Credentials:
- PROD: /root/.cloudflared/2d4a575c-883b-4361-9ee3-b3efe1a0847f.json
- DEV: /root/.cloudflared/f77474f6-e2f6-40b6-bf3c-f23edf03cb72.json
- Cert: /root/.cloudflared/cert.pem
