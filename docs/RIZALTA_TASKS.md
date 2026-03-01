# Задачи RIZALTA

## ✅ Выполнено

### 24.02.2026: Интеграция Корпуса 3 «Digital» в штатный режим
- К3 полностью унифицирован с К1/К2 через общий flow (kp.py, units_db.py)
- Парсер rclick подхватывает К3 автоматически (120 лотов в properties.db)
- Убраны костыли: hardcoded кнопки, corp3 fallback, переадресация в app.py
- КП PDF: building вместо block_section для названия корпуса
- mortgage_pdf_generator.py добавлен в PROD
- Whitelist сохранён для будущего К4
- 6 файлов изменено, задеплоено в DEV + PROD
- Версия: 2.7.0

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
- **Статус:** ✅ ВЫПОЛНЕНО (v0.8.0)

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

### ✅ 11.02.2026: WebApp Phase 3.2.2 (v0.6.1 → v0.8.0)
- AI чат: OpenAI gpt-4o-mini, SSE streaming, 16 intents, action кнопки
- Секретарь: полный CRUD + AI-парсинг задач (8 endpoints)
- Фиксация: авторизация rclick.ru + формы (4 endpoints)
- МГП калькулятор + Ипотечный калькулятор + PDF генерация
- Новости: 4 вкладки (валюты, погода, авиабилеты, RSS)
- Версия webapp: v0.8.0

### ✅ 15.02.2026: WebApp v0.8.0 → v0.8.4 (фиксы + поиск)
- **Фикс Excel для К3:** encodeURIComponent + normalize_lot_code + поиск в corp3_units.json
- **PDF "Варианты оплаты":** новый endpoint + payment_pdf_generator.py + кнопка в модалке
- **Поиск по коду лота:** GET /api/lots/search по всем корпусам, выбор при дублях
- **Фикс планировки К3 через поиск:** whitelist токен в layout_url
- Теги: v0.8.2-xlsx-fix, v0.8.3-payment-pdf, v0.8.4-search-complete
- Версия webapp: v0.8.4

### ✅ 16.02.2026: WebApp DEV/PROD разделение
- /opt/webapp-dev на порту 8004 + webapp-dev.service + nginx + SSL
- dev-webapp.rizaltaservice.ru — полный клон prod с оранжевым favicon
- CLAUDE.md обновлён с dev-инфо для 1Code
- Версия webapp: v0.8.4 (без изменений кода, инфраструктурная сессия)

### 🟡 WebApp: GitHub webhook автодеплой на DEV
- Описание: 1Code push → GitHub webhook → сервер автоматически git pull + build + restart
- Порт 9001, проверка подписи, systemd сервис
- Статус: файлы подготовлены, не установлены

### 🟡 WebApp: deploy-to-prod.sh
- Описание: скрипт деплоя из /opt/webapp-dev в /opt/webapp
- Статус: не создан

### 🟡 Cloudflare DNS зависимость
- webapp.rizaltaservice.ru резолвится через Cloudflare NS
- Если Cloudflare заблокируют в РФ — DNS перестанет работать
- Варианты: перенос NS на reg.ru (ломает Named Tunnels бота) или отдельный домен для webapp

---

## 📅 WebApp задачи (обновлено 16.02.2026)

### ✅ Выполнено (сессия 16.02.2026)
- DEV-окружение: /opt/webapp-dev, порт 8004, systemd, nginx, SSL
- Хардкоженные пути → .env (WEBAPP_DB, DIST_PATH, PROPERTIES_DB и др.)
- GitHub webhook auto-deploy на DEV (webhook_receiver.py, порт 9001)
- deploy-to-prod.sh с автооткатом

### 🔴 Ближайшие задачи
1. **Единый источник данных** — автосинхронизация бот↔webapp
   - rizalta_finance.json, instructions.txt
   - cron/inotify watcher при изменении → копия + restart
2. **session-end.sh** — один скрипт для обновления всех docs + коммит 3 репо
3. **Цель:** актуальная единая информация в любую секунду

### 🟡 Бэклог WebApp
4. Function calling в AI чате
5. Cloudflare DNS миграция
6. Миграция на российский LLM (DeepSeek/YandexGPT)
7. История чата (сохранение сессий)

## 🔜 WebApp бэклог (Phase 3.3+)

### 🔴 Ближайшие
1. **Автосинхронизация данных бот↔webapp** — rizalta_finance.json, instructions.txt (cron/inotify)
2. **session-end.sh** — один скрипт: docs + коммит 3 репо + push
3. **Function calling в AI чате** — инструменты: расчёт ROI, поиск лота, бронирование

### 🟡 Средний приоритет
4. Миграция на российский LLM (DeepSeek/YandexGPT)
5. Cloudflare DNS миграция
6. История чата (сохранение сессий)

### 🟢 Nice-to-have
7. Push-уведомления для секретаря
8. Админ-панель

### 16.02.2026: Аудит whitelist + актуализация К3 + Excel авто-обновление
- Аудит whitelist: 22 пользователя синхронизированы DEV↔PROD
- Актуализация К3: 154 sold / 128 available (7 изменений)
- **Новая функция:** отправка Excel боту → автообновление статусов К3
- Файлы: app.py, run_polling.py
- Версия: 2.6.1

### 19.02.2026: Фикс контактов в заявках группы показов
- get_booking_by_id: добавлены realtor_name, realtor_phone
- Сообщение "ВЗЯТА": полные контакты клиента
- handle_select_time: контакты в первом flow
- Версия: 2.6.2

### 🔴 НОВАЯ ЗАДАЧА: Интеграция Корпуса 3 в штатный режим
- **Приоритет:** ВЫСОКИЙ
- **Описание:** К3 ("Digital") появился на ri.rclick.ru. Нужна полная унификация с К1/К2
- **Объём работ:**
  1. Парсер parser_rclick.py — проверить что К3 подхватывается (building=3)
  2. Миграция данных: corp3_units.json → properties.db (building=3)
  3. Унификация хендлеров: К3 через общие handlers/kp.py вместо handlers/corp3.py
  4. Все функции: КП, MGP, доходность, депозит — должны работать одинаково для К3
  5. Планировки К3 — интеграция в общую схему
  6. sync_rclick.sh / cron — К3 в ночном парсинге
  7. Тестирование каждого этапа в DEV
- **Не трогаем:** whitelist (для будущего К4), команды /ca
- **Статус:** Планирование

---

## 🌐 WebApp бэклог (24.02.2026)

### ✅ Выполнено
- Интеграция К3 в штатный каталог (v0.9.0)

### 🔴 Ближайшие
1. Автосинхронизация данных бот↔webapp (rizalta_finance.json, instructions.txt)
2. Function calling в AI чате
3. session-end.sh доработка — перенести в /opt/webapp-dev/

### 🟡 Средний приоритет
4. Миграция на российский LLM (DeepSeek/YandexGPT)
5. История чата (сохранение сессий)

---

## 🌐 WebApp задачи

### ✅ Выполнено (01.03.2026)
- Function calling в AI чате (v0.9.2) — 5 tools, agentic loop, GPT-5.2
- Strategy PDF generator

### 🔜 Бэклог WebApp
1. 🔴 Деплой v0.9.2 на PROD
2. 🔴 Мониторинг стоимости GPT-5.2
3. 🟡 Миграция на российский LLM (DeepSeek/YandexGPT)
4. 🟡 История чата (сохранение сессий)
5. 🟢 К4 whitelist
6. 🟢 Админ-панель

## 🌐 WebApp задачи (обновлено 02.03.2026)

### ✅ Выполнено (02.03.2026)
- AI Chat v2 — три режима (v0.9.3): report_builder + кнопки + оптимизация скорости
- Reasoning low + max_output_tokens 4000 + slim JSON

### 🔜 Бэклог WebApp
1. 🔴 PDF инвест-отчёт в стиле RIZALTA + кнопка "Скачать PDF" в чате
2. 🔴 Деплой v0.9.3 на PROD
3. 🟡 Формат B — полный Investment Memo (IRR, NPV, Sensitivity Analysis)
4. 🟡 Мониторинг стоимости GPT-5.2
5. 🟡 Миграция на российский LLM (DeepSeek/YandexGPT)
6. 🟡 История чата (сохранение сессий)
7. 🟢 К4 whitelist
8. 🟢 Админ-панель

## WebApp бэклог (02.03.2026)
- 🔴 Исправить AI промпты отчётов (нечитаемый ответ с переменными)
- 🔴 Адаптировать PDF генератор под report_builder данные
- 🔴 Починить портфельный PDF (не скачивается)
## WebApp (v0.9.3, обновлено 02.03.2026)

### ✅ Выполнено (webapp)

#### 02.03.2026: AI Reports + Agentic Loop (v0.9.1 → v0.9.3)
- ai_chat.py — 3 пути (navigation/reports/agentic loop)
- report_builder.py — данные из БД для отчётов
- tool_definitions.py — 5 OpenAI tools
- strategy_pdf_generator.py — PDF с RIZALTA branding
- strategy_data SSE fix — кнопка PDF во всех режимах
- Chat.jsx — кнопки отчётов + PDF download

#### 28.02.2026: Claude-оркестратор (v0.9.0 → v0.9.1)
- /api/docs/file — чтение файлов проекта для Claude
- SESSION_END_TEMPLATE_WEBAPP.md

#### 24.02.2026: Интеграция К3 (v0.8.5 → v0.9.0)
- К3 в штатном каталоге (3 вкладки)
- Whitelist-код закомментирован для К4

### 🔴 Ближайшие задачи (webapp)

1. Исправить AI промпты отчётов (LOT_REPORT_PROMPT, PORTFOLIO_PROMPT)
2. Адаптировать strategy_pdf_generator.py под данные report_builder
3. Починить портфельный PDF

### 🟡 Средний приоритет (webapp)

4. Function calling в AI чате
5. "Взять" → секретарь (автосоздание задачи)
6. История чата

### 🟢 Nice-to-have (webapp)

7. Push-уведомления для секретаря
8. К4 whitelist
9. Миграция на российский LLM
