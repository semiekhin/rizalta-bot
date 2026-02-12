# Задачи RIZALTA

## ✅ Выполнено

### 11.02.2026: МГП калькулятор + обновление К3 + презентация + Web App кнопка
- МГП калькулятор: 2 модели (номерной + коммерческий), текст + PDF
- Новые файлы: services/mgp_calculator.py, handlers/mgp.py
- Обновлены статусы Корпуса 3: 150 sold / 132 available (Excel 09.02)
- Замена презентации RIZALTA (43 MB)
- Web App кнопка в DEV меню (whitelist → URL с токеном)
- Ипотека: код в PROD, кнопка скрыта (готово к включению)
- **12.02:** Скрытие 3 лотов К3 (В203, В610, В621). Итого: 153 sold / 129 available
- **12.02:** Критический фикс: 7 файлов PROD имели хардкод /opt/bot-dev/ → исправлено
- Версия: 2.6.0

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
- **Файлы:** mortgage_config.json, mortgage_calculator.py, mortgage.py + правки kp.py, app.py
- **Статус:** Код и конфиг в PROD, кнопка скрыта. Для включения: добавить строку в /opt/bot/handlers/kp.py

### МГП + Ипотека в WebApp
- **Описание:** Скопировать калькуляторы из бота в webapp backend, добавить endpoints и кнопки в LotDetail
- **Референс:** /opt/bot-dev/services/mgp_calculator.py, mortgage_calculator.py, data/mortgage_config.json
- **Статус:** Не начато

### Деплой Web App кнопки в PROD
- **Статус:** Готово в DEV, не задеплоено
- **Действие:** скопировать menu.py или добавить кнопку вручную

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

### 09-10.02.2026: WebApp Phase 1-2 (аудит + фронтенд)
- Полный аудит webapp v0.3.0, gap-анализ vs бот
- Выбор LLM: DeepSeek V3.2 через OpenRouter
- Фирменный стиль RIZALTA: палитра, Montserrat, лого
- UI/UX: 10 экранов, навбар 3 кнопки, меню-сетка 2×4
- Фильтры каталога: площадь + цена
- 6 новых страниц + 4 backend endpoints
- Модалки ROI/Депозит доработаны (таблица по годам, преимущество)
- CLAUDE.md + TASK_MAP.md в репо для Claude Code
- Версия webapp: v0.5.0

### WebApp Phase 3.2: AI чат + заявки
- **AI чат:** DeepSeek V3.2 через OpenRouter, function calling, SSE streaming
- **Секретарь/Фиксация:** полноценные страницы (сейчас заглушки)
- **Отправка заявок:** ✅ ВЫПОЛНЕНО в Phase 3.2.1 (TG группа + email)
- **Статус:** частично выполнено (заявки готовы, AI чат и секретарь — следующий этап)

### 10.02.2026: WebApp Phase 3.1 — Белый список + Корпус 3 + systemd
- Белый список: webapp.db, access_tokens, общий токен (?token=XXX → localStorage)
- Backend: /api/access/check, /api/corp3/lots (whitelist-protected), /api/corp3/layout/{code}
- Frontend: utils/auth.js, Corp3.jsx (шахматка + фильтры), условная кнопка в Home
- LotDetail: поддержка К3 (маппинг area→area_m2, price→price_rub, скрыты КП/Excel)
- Catalog: упрощены кнопки [Свободно] + [Фильтры] (убраны Все/Бронь/Продано)
- systemd: webapp.service (enabled, Restart=always)
- Токен К3: MkKGpwCAsq6IF3RtRH7bvg
- Точка отката: git tag v0.5.0-stable
- Версия webapp: v0.6.0

### 10.02.2026: WebApp Phase 3.2.1 — Уведомления + Compare PDF + фиксы
- Уведомления: POST /api/book-showing → Telegram группа (-1003301897674) + email менеджерам
- backend/.env: секреты скопированы из /opt/bot/.env + MANAGER_CHAT_ID
- services/notifications.py: httpx async Telegram + aiosmtplib email
- Compare PDF: /api/download-compare-pdf (wkhtmltopdf, HTML→PDF, 2 страницы)
- services/compare_pdf_generator.py + investment_compare.py из бота
- Фикс скачиваний: window.open(_blank) вместо Telegram.WebApp.openLink для всех файлов
- Фикс модалок ROI/Deposit: pb-24 (кнопки не перекрываются навбаром)
- Booking.jsx: валидация телефона (≥10 цифр), error display
- LotDetail.jsx: кнопка «Скачать PDF сравнение» в модалке депозита
- Presentations.jsx + Documents.jsx: window.open фикс
- .gitignore: webapp.db, __pycache__/
- Версия webapp: v0.6.1

### Следующее: WebApp Phase 3.2.2
- AI чат: DeepSeek V3.2 через OpenRouter, function calling, SSE streaming
- System prompt из /opt/bot/config/instructions.txt + rizalta_knowledge_base.txt
- Секретарь/Фиксация: полноценные страницы (сейчас заглушки)
- Inline PDF viewer (модалки вместо скачивания) — под вопросом
- Обновить CLAUDE.md и TASK_MAP.md до v0.6.x
