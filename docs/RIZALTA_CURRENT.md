# Текущий статус RIZALTA

📅 **Последняя сессия:** 03.02.2026 (вечер)
🏷️ **Версия:** 2.5.6

## ✅ Что сделано (03.02.2026, вечерняя сессия)

### Деплой скрытия Корпуса 2 в PROD
- Скопированы из DEV: `hidden_buildings.json`, `units_db.py`
- В PROD `app.py` добавлен фильтр скрытых корпусов в `/api/lots` endpoint
- Путь к конфигу в PROD: `/opt/bot/data/hidden_buildings.json`
- **Корпус 2 скрыт в PROD** ✅ — бот, API, Mini App
- Бэкап PROD перед деплоем: `/opt/bot/data/backup_20260203_prod/`

### Mini App — передеплой на Vercel
- `npx vercel --prod` — новый билд `index-DedzvG5B.js`
- Старый хардкод `[1,2]` заменён на динамические табы из API
- Mini App автоматически показывает только доступные корпуса

### Фикс DEV /api/lots — путь к БД
- Было: `/opt/bot/properties.db` (PROD БД!)
- Стало: `/opt/bot-dev/properties.db` (DEV БД)
- Сервис `rizalta-dev-api` перезапущен

### Git коммиты
- DEV: `fix: DEV /api/lots now reads DEV database instead of PROD`
- PROD: `feat: hide Building 2 via hidden_buildings.json config`
- Mini App: ранее закоммичено (dynamic tabs + API_PATH fix)

## ✅ Что сделано (03.02.2026, дневная сессия)

### Система скрытия корпусов (DEV)
- Реализован механизм скрытия целых корпусов через `data/hidden_buildings.json`
- Фильтрация работает в: меню бота, поиск по площади/бюджету/коду, API для Mini App
- Mini App: динамические табы корпусов (вместо хардкода [1,2])
- Mini App: исправлен баг — DEV использовал PROD API endpoint

### Обновление статусов Корпуса 3
- 8 лотов закрыты: А617, А615, В605, В607, В609, В613, В425, В627
- Было: 154 available / 128 sold → Стало: 146 available / 136 sold

### Расширение CUSTOM_INSTALLMENT_UNITS
- Добавлены лоты ≤22.1 м²: В217, В225, В317, В417

### Фикс счётчика корпусов
- `get_building_stats()` теперь считает только `status='available'`

## 🔄 Текущее состояние

- **PROD:** работает ✅ (Корпус 2 СКРЫТ ✅)
- **DEV:** работает ✅ (Корпус 2 СКРЫТ ✅)
- **DEV API (uvicorn :8002):** работает ✅ (читает DEV БД ✅)
- **Mini App Vercel:** обновлена ✅ (динамические табы)
- **Watchdog:** работает ✅
- **Клон (Амстердам):** RIZALTA сервисы отключены ✅

## Как вернуть Корпус 2

Когда новые цены будут готовы:
1. Отредактировать `/opt/bot/data/hidden_buildings.json`: `{"hidden": []}`
2. `sudo systemctl restart rizalta-bot`
3. Корпус 2 появится в боте и Mini App автоматически
4. Аналогично в DEV: `/opt/bot-dev/data/hidden_buildings.json`

## 🔜 Следующие задачи

1. 🟡 **Деплой ипотечного калькулятора** — готов в DEV, ждёт проверки расчётов
2. 🟡 **Админ-панель** — типовые операции (скрыть/показать корпус, обновить цены и т.д.)
3. 🟡 Миграция на российский сервер
4. 🟡 Новый бот @RIZALTA_AI_BOT
