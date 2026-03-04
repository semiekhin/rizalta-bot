# Текущий статус RIZALTA

📅 **Последняя сессия:** 01.03.2026
🏷️ **Версия:** 2.7.1
🏷️ **Версия webapp:** 0.9.5

## ✅ Что сделано (01.03.2026)

### OpenAI API ключ
- Заменён в обоих окружениях (DEV + PROD) — новый аккаунт OpenAI
- VECTOR_STORE_ID и ASSISTANT_ID не используются (нигде в коде) — можно удалить из .env

### Custom Installment: фикс для Корпуса 3
- **Проблема:** CUSTOM_INSTALLMENT_UNITS содержит коды (В327, В615 и др.) которые совпадают между К1 и К3 — лоты К3 ошибочно получали ограниченное КП (только 50% ПВ)
- **Решение:** добавлена проверка building==1 во все 3 места (kp_pdf_generator.py:231, kp.py:230, kp.py:733)
- **Файлы:** services/kp_pdf_generator.py, handlers/kp.py

### Фильтр status=available во всех запросах units_db.py
- **Проблема:** только get_building_stats() фильтровал по status — остальные 8 функций возвращали все лоты включая sold
- **Решение:** добавлен AND status='available' в 9 SQL-запросов (get_all_available_lots, get_lots_by_building, get_lots_by_floor, get_lots_filtered, get_lot_by_code x2, get_lots_by_code, get_lot_by_area, get_available_floors)
- **Файл:** services/units_db.py

### Пагинация и сортировка
- **Баг 1:** Кнопка "ещё N лотов" в handle_kp_floors_range (Верхние/Нижние/Средние) имела callback_data="noop" — не работала пагинация
- **Решение:** заменено на _search_cache + kp_show_more (как в других обработчиках)
- **Баг 2:** handle_kp_building_all (Все лоты корпуса) сортировал по floor,code вместо area_m2,price_rub
- **Решение:** ORDER BY area_m2, price_rub в get_lots_by_building()
- **Файлы:** handlers/kp.py, services/units_db.py

### Временные изменения (раскомментировать в понедельник 03.03)
- ⚠️ Крон парсера закомментирован (DEV 6:00 + PROD 3:00) — crontab -e раскомментировать
- 4 лота К3 вручную sold: В121, В123, В327, В427 — парсер перезапишет при включении

## 🔄 Текущее состояние

- **PROD:** работает ✅ v2.7.1
- **DEV:** работает ✅ v2.7.1
- **Корпус 1 «Family»:** ~256 лотов (properties.db, building=1)
- **Корпус 2 «Business»:** ~104 лота (properties.db, building=2), скрыт
- **Корпус 3 «Digital»:** ~116 available / 4 sold вручную (properties.db, building=3) — ✅ ШТАТНЫЙ РЕЖИМ
- **Mini App Vercel:** работает ✅
- **WebApp:** webapp.rizaltaservice.ru ✅
- **⚠️ Крон парсера:** ОТКЛЮЧЁН до понедельника 03.03

## ✅ Что сделано (24.02.2026)

### Интеграция Корпуса 3 «Digital» в штатный режим
- К3 полностью унифицирован с К1/К2 — единый flow через handlers/kp.py
- Парсер rclick уже подхватывал К3 (120 лотов) — запущен для DEV и PROD
- Убраны все костыли: hardcoded кнопки К3 с whitelist, fallback на corp3 JSON, переадресация на corp3 handler
- КП PDF: исправлено отображение названия корпуса (building вместо block_section)
- Mini App: перезапущен DEV API — корректное меню лотов К3
- Добавлен отсутствующий mortgage_pdf_generator.py в PROD
- Whitelist инфраструктура сохранена для будущего К4

### Изменённые файлы (6 шт)
- services/units_db.py — добавлено имя "Digital", убран fallback на corp3 JSON
- handlers/kp.py — убраны 2 hardcoded кнопки К3 с whitelist
- handlers/calc_dynamic.py — убран corp3 fallback
- handlers/mgp.py — унифицирован callback для всех корпусов
- app.py — убрана переадресация К3 лотов на corp3 handler
- services/kp_pdf_generator.py — get_building_name() по building вместо block_section

## 🔄 Текущее состояние

- **PROD:** работает ✅ v2.7.0
- **DEV:** работает ✅ v2.7.0
- **Корпус 1 «Family»:** 256 лотов (properties.db, building=1)
- **Корпус 2 «Business»:** 104 лота (properties.db, building=2), скрыт
- **Корпус 3 «Digital»:** 120 лотов (properties.db, building=3) — ✅ ШТАТНЫЙ РЕЖИМ
- **Mini App Vercel:** работает ✅
- **WebApp:** webapp.rizaltaservice.ru ✅

## ✅ Что сделано (11.02.2026)

### МГП калькулятор (Минимальный Гарантированный Платёж)
- Две модели расчёта: номерной фонд и коммерческое использование (делитель 42 717,4 м² для обеих)
- Текстовая выдача + генерация PDF (wkhtmltopdf)
- Кнопка «📊 Расчёт МГП» в меню лота — корпуса 1/2 (kp.py) и корпус 3 (corp3.py)
- **Новые файлы:** services/mgp_calculator.py, handlers/mgp.py
- **Изменённые файлы:** config/settings.py, handlers/kp.py, handlers/corp3.py, app.py

### Обновление статусов Корпуса 3
- Источник: Excel выгрузка от 09.02.2026
- 12 новых sold: А404, А615, В403, В405, В407, В409, В605, В612, В615, В617, В618, В807
- 1 освободился: А604 (sold → available)
- Итого 09.02: **150 sold / 132 available** (было 139/143)
- **12.02:** Скрытие 3 лотов (В203, В610, В621). Итого: **153 sold / 129 available**

### Замена презентации RIZALTA
- Новый PDF (43 MB) загружен в DEV и PROD
- Путь: presentations/presentation_ru.pdf

### Web App кнопка в главном меню (только DEV)
- «🌐 Web App (beta)» в первой строке рядом с «Купи себе отель!»
- Whitelist-пользователи получают URL с токеном Корпуса 3
- **Изменённый файл:** handlers/menu.py
- **⚠️ НЕ задеплоено в PROD**

### Ипотечный калькулятор — подготовка к деплою
- Код и конфиг скопированы в PROD, но кнопка скрыта
- Для включения: добавить строку с кнопкой в /opt/bot/handlers/kp.py
- **⚠️ Кнопка показывается только в DEV**

### 🔴 Критический фикс: DB_PATH /opt/bot-dev → /opt/bot (7 файлов в PROD)
- PROD читал DEV данные: whitelist, бронирования, презентации, мониторинг, hidden_buildings
- Затронуты: corp3.py, booking_calendar.py, media.py, menu.py, monitoring.py, app.py (2 места)
- Решение: `sed -i 's|/opt/bot-dev/|/opt/bot/|g'` по всем файлам
- Проверка: `grep -rn "/opt/bot-dev" /opt/bot/` — должно быть пусто

## ✅ Что сделано (09-10.02.2026)

### Критический фикс: handle_kp_building_all (500 ошибка)
- Кнопка «📋 Все лоты корпуса» вызывала ImportError — функция не была написана
- Написана handle_kp_building_all в handlers/kp.py

### Документация: ARCHITECTURE.md + CALLBACKS.md
- RIZALTA_ARCHITECTURE.md — карта проекта для LLM-ассистента
- RIZALTA_CALLBACKS.md — полный индекс ~120 callback паттернов

### WebApp: Phase 1-2 завершены (09-10.02.2026)
- Полный аудит webapp v0.3.0: codebase, gap-анализ vs бот, техдолг
- Фирменный стиль RIZALTA применён: палитра #263524/#F2EBD9/#D4A84B, Montserrat, лого
- UI/UX переделка: 10 экранов вместо 4, навбар 3 кнопки
- 6 новых страниц + 4 backend endpoints
- Версия webapp: v0.5.0

### WebApp: Phase 3.1 — Белый список + Корпус 3 + systemd (10.02.2026)
- Белый список (токен): webapp.db + access_tokens, общий токен через URL (?token=XXX)
- Корпус 3 в webapp: Corp3.jsx (шахматка, фильтры)
- systemd: webapp.service (автозапуск, Restart=always)
- Версия webapp: v0.6.0

### WebApp: Phase 3.2.1 — Уведомления + Compare PDF + фиксы (10.02.2026)
- Уведомления заявок: Telegram (группа «Показы Rizalta») + Email
- Compare PDF: генерация PDF «Депозит vs RIZALTA»
- Фикс скачиваний и модалок
- Версия webapp: v0.6.1

## 🔄 Текущее состояние

- **PROD:** работает ✅ v2.6.0
- **DEV:** работает ✅ v2.6.0
- **Корпус 1 «Family»:** 255 лотов (properties.db)
- **Корпус 2 «Business»:** 103 лота (properties.db), скрыт
- **Корпус 3 «Digital»:** 129 available / 153 sold (corp3_units.json, whitelist)
- **Mini App Vercel:** работает ✅
- **Watchdog:** работает ✅
- **WebApp:** работает ✅ v0.8.4 (webapp.rizaltaservice.ru)

## 🔜 Следующие задачи

1. 🟡 **Деплой ипотечного калькулятора** — код в PROD, кнопка скрыта
2. 🟡 **Деплой Web App кнопки в PROD** — готово в DEV
3. ✅ ~~МГП + Ипотека в WebApp~~ — сделано в v0.8.0
4. 🟡 **Вопрос "11 лет / полный цикл"** — уточнить (2035 vs 2036)
4. 🟡 **Админ-панель**
5. 🟡 Миграция на российский сервер
6. 🟡 Модульные README (handlers/, services/)
7. ✅ ~~WebApp Phase 3.2.2~~ — AI чат, секретарь, фиксация, МГП, ипотека, новости (v0.8.0)

## ⚠️ ДЕПЛОЙ: особенности PROD

### Файлы которые РАЗЛИЧАЮТСЯ между DEV и PROD:
- **app.py** — Mini App URL: DEV `?env=dev`, PROD без параметра
- **handlers/menu.py** — DEV имеет Web App кнопку, PROD нет
- **handlers/kp.py** — DEV имеет кнопку ипотеки, PROD нет

### При деплое app.py из DEV в PROD:
```bash
cp /opt/bot-dev/app.py /opt/bot/app.py
sed -i 's|https://rizalta-miniapp.vercel.app?env=dev|https://rizalta-miniapp.vercel.app|' /opt/bot/app.py
```

### При деплое kp.py — убрать строку ипотеки:
```bash
# Удалить строки с 🏦 Ипотека
sed -i '/🏦 Ипотека/d' /opt/bot/handlers/kp.py
```

### При деплое menu.py — убрать Web App или оставить:
- Если Web App не нужен в PROD: использовать MAIN_MENU_BUTTONS напрямую

### НИКОГДА не копировать слепо — проверять зависимости:
- handlers/mortgage.py → нужен services/mortgage_calculator.py + data/mortgage_config.json
- handlers/mgp.py → нужен services/mgp_calculator.py + константы в settings.py

### После деплоя ОБЯЗАТЕЛЬНО:
```bash
grep -rn "/opt/bot-dev" /opt/bot/ --include="*.py" | grep -v __pycache__
# Должно быть пусто!
```

## ✅ Что сделано (15.02.2026) — WebApp

### WebApp v0.8.0 → v0.8.4

**Фикс Excel для К3:**
- Кириллица в URL: encodeURIComponent на фронте + normalize_lot_code (Latin→Cyrillic) на бэке
- Поиск лотов К3: calc_xlsx_generator.py ищет в corp3_units.json когда building=3
- Теги: v0.8.2-xlsx-fix

**PDF "Варианты оплаты":**
- Новый endpoint GET /api/payment-pdf?price=&code=
- Новый файл: services/payment_pdf_generator.py (wkhtmltopdf)
- Кнопка "Скачать PDF" в модалке вариантов оплаты
- Теги: v0.8.3-payment-pdf

**Поиск лота по коду:**
- Новый endpoint GET /api/lots/search?code=
- Поиск по всем корпусам: К1+К2 (properties.db) + К3 (corp3_units.json)
- Выбор корпуса при дублях (А200 есть в К1 и К2 — показывает оба)
- Нормализация: латиница→кириллица (B→В, A→А)
- Кнопка 🔍 в Catalog.jsx
- Теги: v0.8.4-search-complete

**Фикс планировки К3 через поиск:**
- layout_url для К3 передаёт whitelist токен
- Проверка на дублирование ?token= (если уже есть — не добавлять)

**Коммиты:**
- 6b1a2ee — Excel fix Corp3
- 6c060e0 — Payment PDF
- 4580802 — Lot search
- a9621a2 — Duplicate handling
- 00ecebe — Corp3 layout URL
- bd3ee65 — Whitelist token
- 0ac5914 — Token dedup fix

## ✅ Что сделано (16.02.2026) — WebApp

### WebApp: DEV/PROD разделение среды
- Создан `/opt/webapp-dev` (клон с GitHub, ветка webapp)
- systemd: `webapp-dev.service` на порту 8004
- nginx + SSL: https://dev-webapp.rizaltaservice.ru
- Фикс захардкоженных путей: WEBAPP_DB и DIST_PATH → /opt/webapp-dev/
- Favicon DEV: оранжевая "D" (визуальное различие)
- CLAUDE.md обновлён: секция "Среды разработки" + workflow для 1Code
- Workflow: 1Code (Mac) → push GitHub → git pull на dev → проверка → deploy в prod
- Анализ Cloudflare DNS зависимости — добавлено в техдолг
- GitHub webhook + deploy-to-prod.sh — отложены на следующую сессию

---

## 📅 Сессия WebApp: 16.02.2026
🏷️ **WebApp версия:** v0.8.5

### ✅ Что сделано

#### DEV-окружение
- `/opt/webapp-dev` — полный клон prod
- `webapp-dev.service` на порту 8004
- nginx + SSL для dev-webapp.rizaltaservice.ru
- Favicon оранжевая "D" для визуального отличия

#### Пути в .env (v0.8.5)
- Все хардкоженные пути вынесены в переменные окружения
- `app.py` + 3 сервиса: `os.getenv()` с дефолтами
- `git pull` на PROD теперь безопасен
- `.env.example` обновлён

#### Auto-deploy pipeline
- **GitHub webhook** → `webhook_receiver.py` на порту 9001
- Push в `webapp` → автоматический git pull + build + restart DEV (2-3 сек)
- `deploy-to-prod.sh` — деплой одной командой с автооткатом
- Systemd сервис `webhook-webapp.service`

### 🔄 Текущее состояние WebApp
- **DEV:** https://dev-webapp.rizaltaservice.ru ✅
- **PROD:** https://webapp.rizaltaservice.ru ✅
- **Webhook:** active (порт 9001) ✅
- **Pipeline:** 1Code push → DEV auto → `deploy-to-prod.sh` → PROD

### 🔜 Следующие задачи WebApp
1. 🔴 Автосинхронизация данных бот↔webapp (finance.json, instructions.txt)
2. 🔴 session-end.sh — автоматизация обновления docs
3. 🟡 Function calling в AI чате
4. 🟡 Cloudflare DNS миграция
5. 🟢 Миграция на российский LLM

### WebApp: актуализация docs (16.02.2026, вечер)
- CLAUDE.md актуализирован до v0.8.5 (DevOps pipeline, env пути, webhook workflow, бэклог)
- TASK_MAP.md актуализирован (сессия 16.02 в ВЫПОЛНЕНО, деплой через webhook, бэклог расширен)
- Восстановлен git pull в workflow 1Code
- Версия webapp: 0.8.5

## ✅ Что сделано (16.02.2026) — Бот

### Аудит и синхронизация whitelist К3
- Полная проверка по истории всех чатов — собраны все 22 пользователя
- DEV не хватало 4 (793408125, 799197489, 949370329, 868791592) — добавлены
- PROD был в порядке (22 записи)
- Подтверждено: никакой код не удаляет записи из corp3_whitelist автоматически

### Актуализация статусов К3 (Excel 16.02.2026)
- 7 изменений: 4 освободились (А403, В525, В607, В621), 3 проданы (А609, В205, В616)
- Итого: **154 sold / 128 available** (было 155/127)
- DEV и PROD синхронизированы

### Новая функция: Excel актуализация К3 через Telegram
- Отправляешь .xlsx файл боту → автоматическое обновление статусов
- Все коды из Excel = sold, остальные = available
- Обновляет оба окружения (DEV + PROD)
- Отчёт: какие проданы, какие освободились, итого
- Доступно: админам (512319063, 8000703751)
- **Файлы:** app.py (webhook + функция), run_polling.py (DEV polling)

### Три админ-команды с телефона:
| Команда | Что делает |
|---------|-----------|
| `/wl add ID Имя` | Добавить в whitelist К3 |
| `/ca hide/show КОД` | Скрыть/показать лот К3 |
| Отправить Excel | Автоматическая актуализация sold/available |

### Обновлённое состояние К3:
- **Корпус 3:** 128 available / 154 sold (corp3_units.json, whitelist 22 чел)

## ✅ Что сделано (19.02.2026) — Бот

### Фикс: полные контакты клиента в заявках группы «Показы Ризалта»
- **Проблема:** При создании заявки и при "Взять заявку" в группе показывалось только `@chat_id` вместо имени, телефона и Telegram клиента
- **Причина:** `get_booking_by_id()` не доставал `realtor_name`, `realtor_phone` из БД; сообщение "ВЗЯТА" использовало только `username`/`chat_id`
- **Исправлено 3 места в `handlers/booking_calendar.py`:**
  1. `get_booking_by_id()` — добавлены поля `realtor_name`, `realtor_phone` в SELECT
  2. `handle_take_booking()` — сообщение "ВЗЯТА" теперь показывает имя, телефон, telegram
  3. `handle_select_time()` — первый flow отправки в группу тоже показывает полные контакты
- **Задеплоено:** DEV + PROD ✅
- **Версия:** 2.6.2

### 🔜 Следующая задача: Интеграция Корпуса 3 в штатный режим
- К3 появился на ri.rclick.ru
- Цель: полная унификация К3 с К1/К2 (парсер, properties.db, UI/UX, все функции)
- К3 пока НЕ в properties.db (парсер подхватывает только К1=255, К2=104)
- Whitelist и команды /ca остаются (для будущего К4)
- Подробный план — в следующем чате

---

## 🌐 WebApp (24.02.2026)

🏷️ **Версия WebApp:** v0.9.0

### Интеграция К3 в штатный каталог
- К3 убран из временной схемы (JSON + whitelist) → работает через properties.db как К1/К2
- Corp3.jsx удалён, каталог: 3 вкладки — Family / Business / Digital
- КП и Excel корректно генерируются для К3 (building передаётся явно)
- Whitelist-код деактивирован, готов для К4
- Тег: `v0.9.0-corp3-unified`

---

## 🌐 WebApp: v0.9.2 (01.03.2026)

### GPT-5.2 финансовый советник
- Миграция на OpenAI Responses API (GPT-5.2)
- Agentic loop: 5 раундов, 17+ tool calls за запрос
- 5 tools: search_lots, get_lot_details, calculate_roi, calculate_installment, compare_with_deposit
- ADVISOR_INSTRUCTION: финансовый советник, 3 стратегии на бюджет
- Strategy PDF generator (POST /api/strategy-pdf)
- max_output_tokens=16000
- Git tag: v0.9.2-gpt52-advisor

### Среды
- DEV: https://dev-webapp.rizaltaservice.ru (v0.9.2)
- PROD: https://webapp.rizaltaservice.ru (v0.9.0, ожидает деплой)

## 🌐 WebApp: v0.9.3 (02.03.2026)

### AI Chat v2 — три режима
- Архитектура: бэкенд собирает JSON → 1 вызов AI (вместо 5 раундов agentic loop)
- Три режима: "Фин. отчёт по лоту" (кнопка), "Портфель по бюджету" (кнопка), свободный чат
- report_builder.py: build_lot_report_data(), build_portfolio_data()
- Ускорение: ~7 сек (было 20-30), reasoning: low, max_output_tokens: 4000
- slim_deposit(), slim_roi() — оптимизация размера JSON
- Chat.jsx: две кнопки + модалки ввода + пресеты бюджета

### Среды
- DEV: https://dev-webapp.rizaltaservice.ru (v0.9.3)
- PROD: https://webapp.rizaltaservice.ru (v0.9.0, ожидает деплой)

## WebApp v0.9.3 (02.03.2026)
- PDF инвестиционные отчёты в стиле RIZALTA (strategy_pdf_generator.py rewrite)
- report_builder.py: сбор данных напрямую из БД (0 AI токенов)
- stream_lot_report / stream_portfolio_report: быстрые отчёты через 1 вызов AI
- strategy_data SSE fix: кнопка "Скачать PDF" теперь появляется во всех режимах
- Коммиты: 1062d90, f2042b4
## WebApp

📅 **Последняя сессия:** 02.03.2026
🏷️ **Версия:** v0.9.3

### ✅ Что сделано (02.03.2026, v0.9.1 → v0.9.3)

#### AI Reports + Agentic Loop
- **ai_chat.py:** 3 пути — navigation intents (0 AI), reports (report_builder + GPT-5.2), agentic loop (GPT-5.2 + 5 tools)
- **report_builder.py:** build_lot_report_data(), build_portfolio_data() — данные из БД без AI
- **tool_definitions.py:** 5 OpenAI tools (search_lots, get_lot_details, calculate_roi, calculate_installment, compare_with_deposit)
- **strategy_pdf_generator.py:** Full rewrite — RIZALTA branding (Montserrat, green/gold/cream), 4-page reports
- **strategy_data SSE fix:** Кнопка "Скачать PDF" во всех режимах
- **Chat.jsx:** Кнопки "Фин. отчёт по лоту" и "Портфель по бюджету" + PDF download
- **WEBAPP_ROOT env:** DEV корректно читает ресурсы
- **POST /api/strategy-pdf:** Эндпоинт генерации инвестиционного PDF

### 🔄 Текущее состояние WebApp
- **PROD:** webapp.rizaltaservice.ru ✅
- **DEV:** dev-webapp.rizaltaservice.ru ✅
- **Webhook auto-deploy:** ✅

### 🔜 Следующие задачи WebApp
1. 🔴 Исправить AI промпты отчётов (нечитаемый ответ)
2. 🔴 Адаптировать PDF генератор под данные report_builder
3. 🔴 Починить портфельный PDF

### ✅ 02.03.2026 part 2 (webapp v0.9.3+)
- Report Cards в чате (LotReportCard, PortfolioReportCard)
- report_card SSE event — данные как UI-компоненты до AI
- marked удалён — карточки заменили markdown

## WebApp v0.9.5 (02.03.2026)
- Инвестиционные метрики: NOI, Cap Rate, Cash-on-Cash, Equity Multiple
- AI-driven portfolio selection (Level 3): gpt-4o-mini selector + GPT-5.2 analyst
- 3 инвестиционных сценария: премиальный лот / портфель 100% / макс. плечо
- UI карточки с метриками и reasoning от AI
- Полноценные AI промпты 400-800 слов (7 секций)
- Markdown рендеринг в чате

## Сессия 03-04.03.2026 (v2.7.2)

### ✅ Траншевая ипотека — полный цикл
**Новые файлы:**
- `data/tranche_mortgage_config.json` — конфиг: ставки, суммы траншей по 12 сценариям (3 ценовых диапазона × 4 ПВ)
- `services/tranche_mortgage_calculator.py` — калькулятор: 3 транша по 8 мес, срок 20 лет, service_fee 150К
- `services/tranche_mortgage_pdf_generator.py` — PDF: все 4 сценария ПВ + планировка лота, CMYK→RGB конвертация
- `handlers/tranche_mortgage.py` — хендлер: текстовое сообщение + PDF генерация

**Callbacks:**
- `tmort_pdf_{code}_{building}` — генерация PDF
- `tmort_{code}_{building}` — текстовое меню со всеми 4 сценариями ПВ

**Кнопка в карточке лота:**
- `kp.py` (строки 243, 749) — «🏗 Траншевая ипотека» после кнопки обычной ипотеки

**Математическая модель:**
- Annuity recalculated: balance(P1,N,8) + P2 → new annuity(N-8), repeat for P3
- Точность ≤0.5% по 11/12 сценариям (N=240)
- Зависимость Pillow для CMYK→RGB конвертации планировок

**Конфигурационные константы:**
| Ставка | ПВ | Применение |
|--------|------|------------|
| 21.7%  | 20.1% | все диапазоны |
| 21.2%  | 30.1%, 40.1% | все диапазоны |
| 19.2%  | 50.1% | все диапазоны |

### ⚠️ Известный баг
- Планировка не отображается в PDF (Pillow установлен, CMYK→RGB работает в CLI, но в PDF не появляется) — разбор в следующей сессии

### ✅ Парсер cron
- Подтверждено: cron раскомментирован (был задизаблен 01.03.2026)

### ✅ GitHub CDN кеш
- raw.githubusercontent.com отдаёт стейл (кеш месяцами)
- Решение: использовать GitHub API `https://api.github.com/repos/.../contents/docs/FILE`
