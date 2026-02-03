# Задачи RIZALTA

## ✅ Выполнено

### 03.02.2026: Скрытие корпусов + обновления
- Система скрытия корпусов через hidden_buildings.json
- Корпус 2 скрыт в DEV (ценовая пауза)
- Mini App: динамические табы, исправлен DEV/PROD API routing
- Обновлены статусы Корпуса 3 (146 available / 136 sold)
- Расширен CUSTOM_INSTALLMENT_UNITS (добавлены В217, В225, В317, В417)
- Фикс get_building_stats() — WHERE status='available'
- Версия: 2.5.5

### 29.01.2026: Критические исправления
- Остановлен клон сервера (перехватывал запросы)
- Исправлен баг: corp3_units.json в .gitignore
- Исправлен баг: /wl и /ca используют относительные пути
- Синхронизирован whitelist PROD (18 записей)
- UX: убрано сообщение "заявка уже обработана"
- Версия: 2.5.3

### 27.01.2026: Подготовка к запуску
- Фильтр новостей, /ca команда, fix compare депозит
- ADMIN_IDS, апгрейд сервера (8 GB RAM)
- Версия: 2.5.2

### Ранее выполнено
- Building 3 (264 юнита) + whitelist
- Named Tunnel (api.rizaltaservice.ru)
- Онлайн-показы v2 (timezone fix)
- Custom Installment для спец-апартаментов
- Self-Healing Watchdog v1.0

## 🔴 Срочные задачи

### Деплой скрытия Корпуса 2 в PROD
- **Приоритет:** Критический
- **Файлы:** hidden_buildings.json, units_db.py, app.py
- **Статус:** Готово в DEV, протестировано

### Деплой ипотечного калькулятора
- **Приоритет:** Высокий
- **Файлы:** mortgage_config.json, mortgage_calculator.py, mortgage_pdf_generator.py, mortgage.py + правки kp.py, app.py
- **Статус:** Готово в DEV, ждёт проверки расчётов

## 🟡 Средний приоритет

### Миграция на российский сервер
- Причина: возможные блокировки

### Новый бот @RIZALTA_AI_BOT
- Ребрендинг бота

### Исправить DEV /api/lots — путь к БД
- Сейчас: /opt/bot/properties.db (PROD)
- Должно: /opt/bot-dev/properties.db

## 🟢 Бэклог

### Удалить legacy код
- kp_generator.py, rizalta_v2/

### Redis кеширование
- При масштабировании до 500+ пользователей

### PostgreSQL
- При масштабировании до 2000+ пользователей
