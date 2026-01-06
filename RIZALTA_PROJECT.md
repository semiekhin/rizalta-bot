# RIZALTA Bot — Описание проекта

## О проекте
AI-консультант для риэлторов. Инвестиционная недвижимость RIZALTA Resort Belokurikha (Алтай).

**Часть экосистемы RIZALTA AI PLATFORM:**
- ✅ **RIZALTA BOT** — цифровой отдел продаж 24/7 (готов)
- ✅ **Mini App Шахматка** — визуальный выбор лотов (готов, v2.3.0)
- 🔜 **RealtMy Mini App** — управление контентом Telegram-каналов
- 🔜 **Контент-завод** — AI-медиацентр автогенерации

## Боты
- **Prod:** @RealtMeAI_bot (webhook, порт 8000)
- **Dev:** @rizaltatestdevop_bot (polling, API порт 8002)

## Сервер
```bash
ssh -p 2222 root@72.56.64.91
```
- `/opt/bot` — prod
- `/opt/bot-dev` — dev
- `/opt/miniapp` — Mini App (React)

## Стек
Python 3.12 · FastAPI · OpenAI GPT-4o-mini · Whisper · SQLite · Cloudflare Tunnel · React · Vite · Tailwind CSS · Vercel

---

## Структура проекта
```
/opt/bot/
├── app.py                    # Главный файл (webhook, роутинг, API endpoints)
├── run_polling.py            # Dev режим (polling, reminder_loop, monitoring_loop)
├── config/
│   └── settings.py           # Константы, кнопки меню, SHOWS_GROUP_ID
├── handlers/
│   ├── __init__.py           # Экспорты
│   ├── menu.py               # Главное меню
│   ├── ai_chat.py            # AI диалоги
│   ├── booking.py            # Онлайн-показы
│   ├── booking_fixation.py   # Фиксация клиентов ri.rclick.ru
│   ├── booking_calendar.py   # Календарь + групповые заявки (v2.1.2)
│   ├── compare.py            # Депозит vs RIZALTA
│   ├── kp.py                 # КП + универсальная навигация + пагинация
│   ├── calc_dynamic.py       # Расчёты ROI
│   ├── secretary.py          # AI-секретарь + timezone
│   ├── docs.py               # Документы
│   ├── news.py               # Новости/дайджест
│   ├── media.py              # Медиа
│   └── units.py              # Работа с лотами
├── services/
│   ├── telegram.py           # API Telegram + edit_message_inline
│   ├── notifications.py      # Уведомления + notify_shows_group
│   ├── ai_chat.py            # OpenAI интеграция
│   ├── calculations.py       # Финансовые расчёты
│   ├── monitoring.py         # Мониторинг нагрузки
│   ├── secretary_db.py       # БД секретаря + timezone
│   ├── intent_router.py      # GPT Intent Router + open_lots_app
│   ├── rclick_service.py     # API ri.rclick.ru
│   ├── units_db.py           # Работа с БД лотов (348 лотов)
│   ├── kp_pdf_generator.py   # PDF КП
│   └── kp_resources/         # Логотип, шрифты
├── data/
│   ├── rizalta_knowledge_base.txt # База знаний AI
│   ├── units.json            # Данные лотов
│   └── rizalta_finance.json  # Финансовые данные
├── properties.db             # 348 лотов + bookings
├── secretary.db              # Задачи + users (timezone)
└── monitoring.db             # Статистика запросов

/opt/miniapp/
├── src/
│   └── App.jsx               # React компонент Mini App
├── dist/                     # Собранная статика (Vercel)
├── vite.config.js            # base: '/'
├── vercel.json               # Rewrites для PROD/DEV API
├── package.json
└── README.md
```

---

## Функциональность

### 1. Mini App Шахматка (v2.3.0) ✅ NEW
```
🏢 Лоты → Открыть выбор лотов
├─ Визуальная шахматка всех 348 лотов
├─ Фильтры: корпус, этаж, статус
├─ Цветовая индикация: свободно/бронь/продано
└─ Кнопка "В работу" → КП в боте
```
- **URL:** https://rizalta-miniapp.vercel.app
- **PROD:** без параметров → /api/* → PROD туннель
- **DEV:** ?env=dev → /api-dev/* → DEV туннель
- **Обход блокировок РФ:** через Vercel proxy

### 2. КП (Коммерческие предложения)
```
📋 Коммерческие предложения
├─ 🏢 По корпусу → Этаж → Лоты
├─ 📐 По площади
├─ 💰 По бюджету (±10% от суммы)
└─ 🔍 По номеру лота
```
- **3 варианта:** 100% оплата, 12 мес, 12+18 мес
- PDF с логотипом, планировкой, расчётами
- Скидка 5% при 100% оплате

### 3. Расчёты доходности
- Динамический калькулятор ROI
- Excel генератор
- Рассрочка 12 и 18 месяцев

### 4. Сравнение депозит vs RIZALTA
- Данные ЦБ РФ (ключевая ставка)
- 3 сценария (базовый, оптимист, пессимист)
- PDF отчёт

### 5. AI-секретарь
- Создание задач голосом/текстом
- Напоминания за 15 минут
- 11 часовых поясов России (UTC+2 — UTC+12)

### 6. AI консультант
- GPT-4o-mini с Intent Router
- База знаний проекта
- Голосовой ввод (Whisper)

### 7. Фиксация клиентов
- Интеграция с ri.rclick.ru
- Авторизация риэлтора (токен 90 дней)

### 8. Групповые заявки на показ (v2.1.2)
- Заявка в группу с кнопкой "🙋 Взять заявку"
- Автоматическая задача в секретаре

### 9. Мониторинг
- Алерт >30 запросов/мин
- Алерт RAM >50%
- Ежедневный отчёт 20:00

---

## Архитектура Mini App

### Разделение PROD/DEV
```
┌─────────────────────────────────────────────────────────────┐
│                     MINI APP (Vercel)                        │
│              https://rizalta-miniapp.vercel.app              │
│                                                              │
│  URL без параметров:                                         │
│    fetch('/api/...') → PROD туннель → :8000                 │
│                                                              │
│  URL с ?env=dev:                                             │
│    fetch('/api-dev/...') → DEV туннель → :8002              │
└─────────────────────────────────────────────────────────────┘
```

### vercel.json
```json
{
  "rewrites": [
    {"source": "/api-dev/:path*", "destination": "https://DEV_TUNNEL/api/:path*"},
    {"source": "/api/:path*", "destination": "https://PROD_TUNNEL/api/:path*"}
  ]
}
```

### Почему Vercel proxy?
- `*.trycloudflare.com` блокируется мобильными операторами в РФ
- Vercel.app НЕ блокируется
- Запросы: Telegram → Vercel → Cloudflare Tunnel → Сервер

---

## База данных

### properties.db — 348 лотов
- Корпус 1 «Family»: 244 лота
- Корпус 2 «Business»: 104 лота
- 70 дублей кодов (А200, А202 и др.)
- Таблица `bookings`: taken_by_id, taken_by_name, group_message_id

### secretary.db
- `tasks` — задачи пользователей
- `users` — timezone пользователей (default: 3 = Москва)

### monitoring.db
- `stats` — timestamp, user_id, request_type, response_time_ms

---

## Systemd сервисы

### PROD
```
rizalta-bot.service         — uvicorn :8000 (webhook)
cloudflare-rizalta.service  — туннель PROD
```

### DEV
```
rizalta-bot-dev.service     — polling (Telegram)
rizalta-dev-api.service     — uvicorn :8002 (API для Mini App)
rizalta-dev-tunnel.service  — туннель DEV + auto-update vercel.json
```

---

## История изменений

### v2.3.0 (06.01.2026)
- **Mini App полностью работает!**
- Разделение PROD/DEV через параметр ?env=dev
- Обход блокировок РФ через Vercel proxy
- Два rewrite в vercel.json (PROD + DEV)

### v2.2.0 (06.01.2026)
- Mini App интеграция (код добавлен)
- Systemd сервисы для DEV
- Git репозиторий rizalta-miniapp

### v2.1.2 (29.12.2025)
- Групповые заявки на показ с кнопкой "Взять"
- Интеграция заявок с AI-секретарём
- Прототип Mini App шахматки
- Стратегическое решение: RealtMy → Mini App

### v2.1.1 (24.12.2025)
- Мониторинг нагрузки с алертами
- Часовые пояса для секретаря (11 зон)
- Напоминания через фоновую задачу

### v2.1.0 (24.12.2025)
- 348 лотов вместо 69
- Универсальная навигация Корпус → Этаж → Лоты
- Пагинация "Показать ещё"
- GPT Intent Router с приоритетами

### v1.9.6 (19.12.2025)
- Новый дизайн КП при 100% оплате
- 6 презентаций проекта
- 9 видео про Алтай
