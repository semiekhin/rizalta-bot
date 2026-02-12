# ⚠️ PROD НЕ ТРОГАТЬ! РАБОТАТЬ ТОЛЬКО В DEV! ⚠️

# RIZALTA AI System v2.6.0

📅 **Последняя сессия:** 12.02.2026

AI-консультант для риэлторов. Инвестиционная недвижимость RIZALTA Resort Belokurikha (Алтай).

## Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91` (Timeweb, 4 vCPU, 8 GB RAM)
- **DEV:** `/opt/bot-dev` (@rizaltatestdevop_bot, polling)
- **DEV API:** `/opt/bot-dev` (uvicorn :8002, сервис `rizalta-dev-api`)
- **PROD:** `/opt/bot` (@RealtMeAI_bot, webhook :8000)
- **Mini App:** `/opt/miniapp` → https://rizalta-miniapp.vercel.app
- **WebApp:** `/opt/webapp` → https://webapp.rizaltaservice.ru (v0.6.1)

## Репозитории
- **PROD:** github.com/semiekhin/rizalta-bot
- **DEV:** github.com/semiekhin/rizalta-bot-dev
- **Mini App:** github.com/semiekhin/rizalta-miniapp
- **WebApp:** github.com/semiekhin/rizalta-webapp

## Стек
- Python/FastAPI, SQLite (WAL mode), Telegram Bot API, OpenAI GPT-4o-mini
- Mini App: React/Vite/Tailwind → Vercel
- WebApp: React/Vite/Tailwind → systemd + nginx

## Корпуса
- **Корпус 1 «Family»:** 255 лотов (properties.db)
- **Корпус 2 «Business»:** 103 лота (properties.db) — **СКРЫТ** (hidden_buildings.json, ценовая пауза)
- **Корпус 3 «Digital»:** 129 available / 153 sold (corp3_units.json, whitelist)

## Управление видимостью корпусов
- **Конфиг:** `data/hidden_buildings.json` → `{"hidden": [2]}`
- **Вернуть корпус:** изменить на `{"hidden": []}` + перезапустить сервис
- **Фильтрация:** units_db.py (бот) + app.py /api/lots (Mini App)

## Ключевые сервисы (systemd)
| Сервис | Unit | Описание |
|--------|------|----------|
| PROD бот | rizalta-bot | webhook :8000 |
| DEV бот | rizalta-bot-dev | polling |
| DEV API | rizalta-dev-api | uvicorn :8002 (Mini App API) |
| WebApp | webapp | backend :8003 |
| Watchdog | rizalta-watchdog | мониторинг |

## Cron задачи
| Время | Задача |
|-------|--------|
| 03:00 | Бэкап + PROD парсер (parser_rclick.py) |
| 04:00 (вс) | Еженедельный бэкап |
| 06:00 | DEV парсер (parser_rclick.py) |
| */5 мин | Health check |

## Ключевые файлы
- `data/hidden_buildings.json` — скрытие корпусов
- `data/corp3_units.json` — лоты Корпуса 3 (в .gitignore)
- `data/mortgage_config.json` — конфиг ипотеки
- `services/units_db.py` — работа с БД лотов
- `services/kp_pdf_generator.py` — генерация КП (PDF)
- `services/mgp_calculator.py` — расчёт МГП (номерной + коммерческий)
- `services/mortgage_calculator.py` — ипотечный калькулятор
- `services/parser_rclick.py` — парсер данных с сайта застройщика (cron)
- `handlers/kp.py` — навигация по лотам
- `handlers/corp3.py` — Корпус 3 + whitelist
- `handlers/mgp.py` — обработчик МГП
- `handlers/mortgage.py` — ипотечный калькулятор
- `handlers/menu.py` — главное меню (DEV: с Web App кнопкой)
- `app.py` — главный файл (webhook, API, callbacks)

## ⚠️ Различия DEV vs PROD
| Файл | DEV | PROD |
|------|-----|------|
| app.py | Mini App URL с `?env=dev` | Mini App URL без параметра |
| handlers/menu.py | Web App кнопка есть | Web App кнопки нет |
| handlers/kp.py | Кнопка ипотеки есть | Кнопки ипотеки нет |

## ⚠️ ДЕПЛОЙ: чеклист
1. **НЕ копировать слепо** — проверять зависимости каждого файла
2. **app.py:** после копирования `sed -i 's|?env=dev||' /opt/bot/app.py`
3. **menu.py:** убрать Web App кнопку если не нужна в PROD
4. **kp.py:** убрать строку ипотеки `sed -i '/🏦 Ипотека/d' /opt/bot/handlers/kp.py`
5. **Новые handlers:** проверить что services + data файлы тоже скопированы
