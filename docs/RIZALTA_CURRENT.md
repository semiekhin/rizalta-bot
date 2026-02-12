# Текущий статус RIZALTA

📅 **Последняя сессия:** 12.02.2026
🏷️ **Версия:** 2.6.0

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
- **WebApp:** работает ✅ v0.6.1 (webapp.rizaltaservice.ru)

## 🔜 Следующие задачи

1. 🟡 **Деплой ипотечного калькулятора** — код в PROD, кнопка скрыта
2. 🟡 **Деплой Web App кнопки в PROD** — готово в DEV
3. 🟡 **МГП + Ипотека в WebApp** — скопировать калькуляторы из бота, добавить endpoints и кнопки в LotDetail
4. 🟡 **Вопрос "11 лет / полный цикл"** — уточнить (2035 vs 2036)
4. 🟡 **Админ-панель**
5. 🟡 Миграция на российский сервер
6. 🟡 Модульные README (handlers/, services/)
7. 🔴 **WebApp Phase 3.2.2** — AI чат (DeepSeek V3.2), секретарь/фиксация

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
