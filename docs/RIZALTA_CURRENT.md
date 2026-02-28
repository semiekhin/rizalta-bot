# Текущий статус RIZALTA

📅 **Последняя сессия:** 24.02.2026
🏷️ **Версия:** 2.7.0
🏷️ **Версия webapp:** 0.8.5

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
