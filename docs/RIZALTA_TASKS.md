# Задачи RIZALTA

## ✅ Выполнено

### 09.02.2026: Фикс handle_kp_building_all + ARCHITECTURE/CALLBACKS
- Критический баг: кнопка «Все лоты корпуса» → ImportError 500 (функция не существовала)
- Написана handle_kp_building_all в handlers/kp.py (пагинация через _search_cache)
- Создан RIZALTA_ARCHITECTURE.md — карта проекта для LLM-ассистента
- Создан RIZALTA_CALLBACKS.md — индекс ~120 callback паттернов
- Версия: 2.5.10

### 05.02.2026: Фикс аренды в "Сравнить с депозитом"
- Баг: area_m2 хардкод 26.8 → аренда одинаковая для всех лотов
- Фикс: area передаётся через callback chain как area10
- 6 файлов: compare.py, kp.py, corp3.py, app.py, compare_pdf_generator.py, investment_compare.py
- Обратная совместимость со старыми кнопками
- Версия: 2.5.9

### 03.02.2026 (вечер): Деплой скрытия Корпуса 2 в PROD
- Скопированы hidden_buildings.json и units_db.py из DEV в PROD
- Добавлен фильтр скрытых корпусов в PROD app.py (/api/lots)
- Mini App передеплоена на Vercel (динамические табы)
- Исправлен DEV /api/lots — путь к БД (PROD → DEV)
- Версия: 2.5.6

### 03.02.2026 (день): Скрытие корпусов + обновления
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
- Версия: 2.5.3

### Ранее выполнено
- Building 3 (264 юнита) + whitelist
- Named Tunnel (api.rizaltaservice.ru)
- Онлайн-показы v2 (timezone fix)
- Custom Installment для спец-апартаментов
- Self-Healing Watchdog v1.0

## 🟡 Средний приоритет

### Деплой ипотечного калькулятора
- **Файлы:** mortgage_config.json, mortgage_calculator.py, mortgage_pdf_generator.py, mortgage.py + правки kp.py, app.py
- **Статус:** Готово в DEV, ждёт проверки расчётов

### Вопрос "11 лет / полный цикл"
- **Описание:** В кнопке "11 лет (полный цикл)" расчёт до 2035, а не 2036
- **Нужно:** Уточнить что означает "полный цикл" по задумке застройщика

### Админ-панель
- **Описание:** Веб-интерфейс или бот-команды для типовых операций
- **Операции:** скрыть/показать корпус, whitelist, статистика, перезапуск
- **Статус:** Идея, требует проектирования

### Миграция на российский сервер
- Причина: возможные блокировки

### Модульные README
- handlers/README.md, services/README.md — краткое описание каждого файла
- Дополнение к ARCHITECTURE.md

### Новый бот @RIZALTA_AI_BOT
- Ребрендинг бота

## 🟢 Бэклог

### Удалить legacy код
- kp_generator.py, rizalta_v2/

### Redis кеширование
- При масштабировании до 500+ пользователей

### PostgreSQL
- При масштабировании до 2000+ пользователей

### ⚠️ Парсер: DELETE FROM units (известная особенность)
- Парсер `parser_rclick.py` делает DELETE перед INSERT
- Если корпус убран с сайта ri.rclick.ru — пропадает из БД
- На будущее: рассмотреть UPSERT вместо DELETE
