# ⚠️ PROD НЕ ТРОГАТЬ! РАБОТАТЬ ТОЛЬКО В DEV! ⚠️

# RIZALTA AI System v2.5.5

📅 **Последняя сессия:** 03.02.2026

AI-консультант для риэлторов. Инвестиционная недвижимость RIZALTA Resort Belokurikha (Алтай).

## Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91` (Timeweb, 4 vCPU, 8 GB RAM)
- **DEV:** `/opt/bot-dev` (@rizaltatestdevop_bot, polling)
- **DEV API:** `/opt/bot-dev` (uvicorn :8002, сервис `rizalta-dev-api`)
- **PROD:** `/opt/bot` (@RealtMeAI_bot, webhook :8000)
- **Mini App:** `/opt/miniapp` → https://rizalta-miniapp.vercel.app
- **Клон (Амстердам):** RIZALTA сервисы отключены (disabled)

## Репозитории
- **PROD:** github.com/semiekhin/rizalta-bot
- **DEV:** github.com/semiekhin/rizalta-bot-dev
- **Mini App:** github.com/semiekhin/rizalta-miniapp

## Стек
- Python/FastAPI, SQLite (WAL mode), Telegram Bot API, OpenAI GPT-4o-mini
- Mini App: React/Vite/Tailwind → Vercel

## Корпуса
- **Корпус 1 «Family»:** 253 лота (properties.db)
- **Корпус 2 «Business»:** 102 лота (properties.db) — СКРЫТ в DEV (hidden_buildings.json)
- **Корпус 3 «Digital»:** 146 available / 136 sold (corp3_units.json, whitelist)

## Ключевые сервисы (systemd)
| Сервис | Unit | Описание |
|--------|------|----------|
| PROD бот | rizalta-bot | webhook :8000 |
| DEV бот | rizalta-bot-dev | polling |
| DEV API | rizalta-dev-api | uvicorn :8002 (Mini App API) |
| Watchdog | rizalta-watchdog | мониторинг |

## Ключевые файлы
- `data/hidden_buildings.json` — скрытие корпусов
- `data/corp3_units.json` — лоты Корпуса 3 (в .gitignore)
- `services/units_db.py` — работа с БД лотов
- `services/kp_pdf_generator.py` — генерация КП (PDF)
- `handlers/kp.py` — навигация по лотам
- `handlers/corp3.py` — Корпус 3 + whitelist
- `app.py` — главный файл (webhook, API, callbacks)
