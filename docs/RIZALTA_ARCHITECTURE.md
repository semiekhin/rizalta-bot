# Архитектура RIZALTA Bot v2.6.0

> Этот файл — карта проекта для LLM-ассистента.
> Читай его ВМЕСТО изучения всего кода. Изучай код только по необходимости.

## Точки входа

| Файл | Режим | Описание |
|------|-------|----------|
| `app.py` | PROD (webhook :8000) | Главный файл: webhook, API endpoints, роутинг callbacks |
| `run_polling.py` | DEV (polling) | Запуск бота в режиме polling |

## Структура проекта

```
/opt/bot-dev/
├── app.py                  # Webhook + API + callback router
├── run_polling.py           # DEV polling
├── config/
│   └── settings.py          # Настройки, токены, пути
├── handlers/                # Обработчики команд и callback
│   ├── ai_chat.py           # Свободный AI-диалог (GPT-4o-mini)
│   ├── booking.py           # Запись на показ (старая)
│   ├── booking_calendar.py  # Календарь бронирования
│   ├── booking_fixation.py  # Фиксация брони через RClick
│   ├── calc_dynamic.py      # Расчёт доходности + варианты оплаты (навигация)
│   ├── compare.py           # Сравнение с депозитом
│   ├── corp3.py             # Корпус 3 «Digital» + whitelist
│   ├── docs.py              # Документы (ДДУ, аренда)
│   ├── domoplaner.py        # Доможилинк парсер
│   ├── kp.py                # КП: навигация по лотам, генерация PDF
│   ├── media.py             # Медиа: презентации, видео
│   ├── menu.py              # Главное меню, /start, информация о проекте
│   ├── mortgage.py          # Ипотечный калькулятор (только DEV)
│   ├── news.py              # Новости: курсы, погода, авиабилеты, дайджест
│   ├── secretary.py         # AI-секретарь: задачи, расписание
│   └── units.py             # Старые обработчики лотов (legacy)
├── services/                # Бизнес-логика и утилиты
│   ├── ai_chat.py           # OpenAI API, intent analysis
│   ├── calc_universal.py    # Универсальный расчёт ROI и рассрочки
│   ├── calc_xlsx_generator.py # Генерация Excel-отчётов
│   ├── calculations.py      # Портфельные сценарии, формулы
│   ├── compare_pdf_generator.py # PDF сравнения с депозитом
│   ├── data_loader.py       # Загрузка JSON/TXT данных
│   ├── deposit_calculator.py # Калькулятор депозита (прогноз ЦБ)
│   ├── installment_calculator.py # Калькулятор рассрочки
│   ├── intent_router.py     # Роутер намерений (quick match + classify)
│   ├── investment_calc.py   # Инвестиционный расчёт
│   ├── investment_compare.py # Сравнение RIZALTA vs депозит
│   ├── kp_pdf_generator.py  # Генерация КП в PDF
│   ├── kp_search.py         # Поиск КП по коду/площади/бюджету
│   ├── monitoring.py        # Мониторинг, алерты, статистика
│   ├── mortgage_calculator.py # Расчёт ипотеки
│   ├── mortgage_pdf_generator.py # PDF ипотечного расчёта
│   ├── notifications.py     # Уведомления менеджерам (Telegram + email)
│   ├── parser_rclick.py     # Парсер данных с сайта застройщика (cron)
│   ├── rclick_service.py    # API RClick (авторизация, бронирование)
│   ├── secretary_ai.py      # AI-логика секретаря
│   ├── secretary_db.py      # БД задач секретаря
│   ├── speech.py            # Транскрипция голосовых (Whisper)
│   ├── telegram.py          # Telegram API обёртки
│   ├── units_db.py          # Работа с БД лотов (SQLite)
│   └── user_profiles.py     # Профили пользователей, часовые пояса
└── data/
    ├── hidden_buildings.json # Скрытые корпуса {"hidden": [2]}
    ├── corp3_units.json      # Лоты Корпуса 3 (в .gitignore)
    ├── corp3_access.db       # Whitelist Корпуса 3
    └── properties.db         # БД лотов Корпусов 1-2 (SQLite WAL)
```

## Модули по функциям

### 📋 КП и навигация по лотам
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/kp.py` | `handle_kp_menu`, `handle_kp_building`, `handle_kp_building_all`, `handle_kp_floor`, `handle_kp_lot`, `handle_kp_generate` | Навигация: корпус → этаж → лот → PDF |
| `handlers/kp.py` | `handle_nav_menu`, `handle_nav_building`, `handle_nav_floor`, `handle_nav_lot` | Универсальная навигация (mode=kp/calc/compare) |
| `services/kp_pdf_generator.py` | `generate_kp_pdf` | Генерация HTML→PDF коммерческого предложения |
| `services/units_db.py` | `get_lots_by_building`, `get_lots_by_floor`, `get_lot_by_code`, `get_lots_filtered` | Запросы к БД лотов |

### 📊 Расчёт доходности
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/calc_dynamic.py` | `handle_calc_roi_by_code`, `handle_calc_roi_lot`, `handle_calc_finance_by_code` | Навигация к расчётам |
| `services/calc_universal.py` | `calculate_roi_for_lot`, `calculate_installment_for_lot` | Расчёт ROI и рассрочки |
| `services/calc_xlsx_generator.py` | `generate_roi_xlsx` | Excel-отчёт доходности |

### 📈 Сравнение с депозитом
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/compare.py` | `handle_compare_lot`, `handle_compare_period`, `handle_compare_pdf` | UI сравнения |
| `services/investment_compare.py` | `compare_investments`, `calculate_rizalta` | Расчёт: RIZALTA vs депозит |
| `services/deposit_calculator.py` | `calculate_deposit` | Калькулятор депозита с прогнозом ставки ЦБ |
| `services/compare_pdf_generator.py` | `generate_compare_pdf` | PDF сравнения |

### 🏢 Корпус 3
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/corp3.py` | `handle_corp3_callback`, `handle_corp3_lot_detail`, `handle_corp3_generate_kp` | Навигация + КП для К3 |
| Данные: `data/corp3_units.json` | — | JSON с лотами (не в БД!) |
| Доступ: `data/corp3_access.db` | — | Whitelist (SQLite) |

### 🏦 Ипотека (только DEV)
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/mortgage.py
- **handlers/mgp.py** — расчёт МГП (номерной + коммерческий), текст + PDF` | `handle_mortgage_menu`, `handle_mortgage_pdf` | UI ипотечного калькулятора |
| `services/mortgage_calculator.py
- **services/mgp_calculator.py** — calc_mgp(), format_mgp_text(), generate_mgp_pdf()` | `calc_mortgage` | Расчёт аннуитета |
| `services/mortgage_pdf_generator.py` | `generate_mortgage_pdf` | PDF ипотечного расчёта |

### 📅 Бронирование
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/booking_calendar.py` | `handle_booking_start`, `handle_select_date`, `handle_submit_booking` | Календарь + запись |
| `handlers/booking_fixation.py` | `handle_booking_menu`, `send_booking` | Фиксация через RClick |
| `services/rclick_service.py` | `login_rclick`, `create_booking` | API застройщика |
| `services/notifications.py` | `send_booking_notification` | Уведомления менеджерам |

### 🤖 AI-диалог
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/ai_chat.py` | `handle_free_text` | Обработка свободного текста |
| `services/ai_chat.py` | `ask_ai_about_project` | Вызов GPT-4o-mini |
| `services/intent_router.py` | `try_quick_match`, `classify_intent` | Определение намерения |

### 📰 Новости и утилиты
| Файл | Ключевые функции | Описание |
|------|-----------------|----------|
| `handlers/news.py` | `handle_currency_rates`, `handle_weather`, `handle_flights`, `handle_news_digest` | Курсы, погода, билеты, RSS |
| `handlers/secretary.py` | `handle_secretary_menu`, `process_secretary_input` | AI-секретарь |
| `handlers/media.py` | `handle_media_menu`, `handle_send_presentation` | Презентации и видео |
| `handlers/docs.py` | `handle_documents_menu` | Документы ДДУ/аренда |

## Потоки данных (callback chains)

### КП: Выбор лота → Генерация PDF
```
/start → handle_start (menu.py)
  → 📋 КП и расчёты → handle_kp_menu (kp.py)
    → По корпусу → handle_kp_by_building_menu
      → Корпус 1 → handle_kp_building (kp_building_{N})
        → 5 эт. → handle_kp_floor (kp_floor_{b}_{f})
          → Лот А508 → handle_kp_lot (kp_lot_{code})
            → 📄 КП 100% → handle_kp_generate (kp_gen_{code}_{b}_{mode})
              → generate_kp_pdf() → sendDocument
```

### Сравнение с депозитом
```
Карточка лота → 📈 Сравнить с депозитом
  → compare_lot_{code}_{building}_{price}_{area10}    # app.py → handle_compare_lot
    → compare_period_{years}_{amount}_{area10}         # → handle_compare_period
      → compare_investments(amount, years, area_m2)    # services/investment_compare.py
        → 📄 Создать PDF → compare_pdf_{years}_{amount}_{area10}
          → generate_compare_pdf()                     # services/compare_pdf_generator.py
```

### Расчёт доходности
```
Карточка лота → 📊 Расчёт доходности
  → calc_roi_code_{code}_{building}    # app.py → handle_calc_roi_by_code
    → calculate_roi_for_lot()          # services/calc_universal.py
    → 📥 Скачать Excel → roi_xlsx_code_{code}_{building}
      → generate_roi_xlsx()            # services/calc_xlsx_generator.py
```

### Корпус 3
```
c3_menu → handle_corp3_start (corp3.py)
  → c3_by_floor / c3_by_rooms / c3_by_area
    → c3_floor_{N}_{offset} → handle_corp3_show_list
      → c3_lot_{code} → handle_corp3_lot_detail
        → c3_kp12_{code} / c3_kp18_{code} → handle_corp3_generate_kp
```

## Данные

### Корпуса 1-2: SQLite (`data/properties.db`)
- Таблица `properties`: code, building, floor, area, price, status, layout_url...
- Обновляется парсером `parser_rclick.py` (cron 03:00/06:00)
- Доступ через `services/units_db.py`
- `get_building_stats()` имеет `WHERE status='available'` фильтр

### Корпус 3: JSON (`data/corp3_units.json`)
- Отдельный файл, не в БД
- Whitelist: `data/corp3_access.db`
- Обработка через `handlers/corp3.py`

### Видимость корпусов
- Конфиг: `data/hidden_buildings.json` → `{"hidden": [2]}`
- Фильтрация: `units_db.py` (бот) + `app.py /api/lots` (Mini App)
- Парсер продолжает обновлять скрытые корпуса в БД

## Ограничения Telegram
- Callback data: max **64 байта** → кодирование: `area10 = int(area_m2 * 10)`
- Inline buttons: max **100 кнопок** на сообщение → пагинация (PAGE_SIZE=50, MAX_BUTTONS=20)
- `_search_cache[chat_id]` для пагинации "Показать ещё"

## Быстрый поиск (grep-индекс)

```bash
# Все callback handlers в app.py
grep -n "elif data.startswith\|elif data ==" app.py

# Все функции в файле
grep -n "^async def \|^def " handlers/kp.py

# Где используется конкретный callback
grep -rn "kp_building_all" handlers/ app.py

# Формулы расчёта
grep -rn "def calculate_\|def calc_" services/

# Все кнопки с определённым текстом
grep -rn "Сравнить с депозитом\|compare_lot" handlers/

# Импорты в конкретном handler
head -30 handlers/compare.py

# Все PDF-генераторы
grep -rn "def generate_.*pdf" services/

# Где вызывается конкретная функция из services
grep -rn "from services.units_db import\|from services.investment" handlers/ app.py
```

## Сервисы (systemd)

| Сервис | Unit | Описание |
|--------|------|----------|
| PROD бот | `rizalta-bot` | webhook :8000 |
| DEV бот | `rizalta-bot-dev` | polling |
| DEV API | `rizalta-dev-api` | uvicorn :8002 (Mini App) |
| Watchdog | `rizalta-watchdog` | мониторинг |

## Типовые операции

```bash
# Рестарт DEV
systemctl restart rizalta-bot-dev

# Рестарт PROD
systemctl restart rizalta-bot

# Логи PROD (последние)
journalctl -u rizalta-bot --since "5 min ago" --no-pager

# Проверка ошибок
journalctl -u rizalta-bot --since "today" | grep -E "Error|error|500|Exception"

# Проверка синтаксиса перед деплоем
python3 -c "import py_compile; py_compile.compile('handlers/kp.py', doraise=True)"

# Git commit
cd /opt/bot-dev && git add -A && git commit -m "описание"
cd /opt/bot && git add -A && git commit -m "описание"
```
