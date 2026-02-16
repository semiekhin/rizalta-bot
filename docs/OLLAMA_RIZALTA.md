# OLLAMA RIZALTA — База знаний для оффлайн разработки

## Назначение

Этот документ содержит решения типовых задач и инцидентов для использования с локальными LLM (Ollama) когда нет доступа к Claude.

---

## ТИПОВЫЕ ЗАДАЧИ

### ЗАДАЧА 1: Добавление Корпуса 3 (whitelist, КП-only патч)

**Контекст:** Корпус 3 ещё не появился на ri.rclick.ru, но нужно дать доступ избранным пользователям.

**Файлы:**
- `handlers/corp3.py` — новый handler
- `data/corp3_units.json` — данные лотов из Excel
- `data/corp3_layouts/` — планировки (JPG)
- `config/settings.py` — CORP3_WHITELIST
- `handlers/__init__.py` — импорт
- `handlers/kp.py` — кнопка в меню
- `app.py` — роутинг callbacks и команды

**Шаги:**

1. Конвертировать Excel в JSON:
```python
# Структура corp3_units.json
{
  "building_name": "Корпус 3",
  "total_units": 282,
  "units": [
    {
      "id": 620913,
      "code": "А200",
      "building": 3,
      "section": 1,
      "floor": 2,
      "rooms": 1,
      "area": 24.7,
      "price": 15067000,
      "status": "Резерв",
      "layout_path": "/opt/bot-dev/data/corp3_layouts/2 ЭТАЖ/A_200.jpg",
      "block_section": 3
    }
  ]
}
```

2. Добавить whitelist в settings.py:
```python
CORP3_WHITELIST = {
    512319063,  # Sergio
}
```

3. Добавить импорт в handlers/__init__.py:
```python
from .corp3 import (
    handle_corp3_start,
    handle_corp3_callback,
    handle_corp3_text,
    is_whitelisted as is_corp3_whitelisted,
)
```

4. Добавить роутинг в app.py:
```python
# В process_callback, в начале:
if data.startswith("c3_"):
    from handlers.corp3 import handle_corp3_callback
    await handle_corp3_callback(chat_id, data)
    return

# В process_message, перед GPT:
if text == "/corp3":
    from handlers.corp3 import handle_corp3_start
    await handle_corp3_start(chat_id)
    return
```

5. Добавить кнопку в handlers/kp.py (в handle_kp_by_building_menu):
```python
# После цикла for s in stats:
from config.settings import CORP3_WHITELIST
if chat_id in CORP3_WHITELIST:
    inline_buttons.append([{"text": "🔒 Корпус 3 (282 лота)", "callback_data": "c3_menu"}])
```

**Проверка:**
```bash
cd /opt/bot-dev
source venv/bin/activate
python3 -c "from handlers.corp3 import load_units; print(f'Лотов: {len(load_units())}')"
python3 -c "import app; print('Синтаксис OK')"
systemctl restart rizalta-bot-dev
# В Telegram: /corp3
```

---

### ЗАДАЧА 2: Добавить пользователя в whitelist Корпуса 3

**Шаги:**

1. Узнать chat_id пользователя:
```
# В боте: /myid
```

2. Добавить в whitelist:
```bash
# DEV
sed -i 's/CORP3_WHITELIST = {/CORP3_WHITELIST = {\n    CHAT_ID,  # Имя/' /opt/bot-dev/config/settings.py

# PROD
sed -i 's/CORP3_WHITELIST = {/CORP3_WHITELIST = {\n    CHAT_ID,  # Имя/' /opt/bot/config/settings.py

# Перезапуск
systemctl restart rizalta-bot-dev
systemctl restart rizalta-bot
```

---

### ЗАДАЧА 3: Фильтрация лотов по площади в Корпусе 3

**Файл:** `handlers/corp3.py`

**Изменение в функции load_units():**
```python
# Было:
_units_cache = data.get("units", [])

# Стало (фильтр >= 23.5 м²):
_units_cache = [u for u in data.get("units", []) if u.get('area', 0) >= 23.5]
```

---

## ИНЦИДЕНТЫ И РЕШЕНИЯ

### ИНЦИДЕНТ 1: Медленная генерация КП для Корпуса 3

**Симптомы:** КП генерируется 5-10 секунд вместо 2-3

**Причина:** Планировки Корпуса 3 тяжёлые (~600KB vs ~100KB у корпусов 1-2)

**Решение (отложено):** Сжать все JPG:
```bash
cd /opt/bot-dev/data/corp3_layouts
find . -name "*.jpg" -exec mogrify -resize 50% -quality 85 {} \;
```

---

## ДЕПЛОЙ

### Стандартный деплой DEV → PROD
```bash
# 1. Копируем изменённые файлы
cp /opt/bot-dev/handlers/corp3.py /opt/bot/handlers/
cp /opt/bot-dev/config/settings.py /opt/bot/config/
# ... другие файлы

# 2. Фикс URL Mini App (DEV → PROD)
sed -i 's|?env=dev||g' /opt/bot/app.py

# 3. Проверка синтаксиса
cd /opt/bot && source venv/bin/activate
python3 -c "import app; print('OK')"

# 4. Перезапуск
systemctl restart rizalta-bot
```

---

## СТРУКТУРА CALLBACKS КОРПУСА 3
```
c3_menu              — главное меню
c3_by_rooms          — выбор по комнатам
c3_by_floor          — выбор по этажу
c3_by_area           — выбор по площади
c3_by_code           — поиск по коду
c3_all_{page}        — все лоты с пагинацией
c3_rooms_{N}_{page}  — лоты по комнатам
c3_floor_{N}_{page}  — лоты по этажу
c3_area_{min}_{max}_{page} — лоты по площади
c3_lot_{code}        — детали лота
c3_layout_{code}     — показать планировку
c3_kp12_{code}       — КП 12 мес
c3_kp18_{code}       — КП 12+18 мес
```

---

### ЗАДАЧА 4: Онлайн-показы v2 — часовые пояса и упрощённый ввод

**Контекст:** Риэлторы из разных поясов (Москва/Сочи vs Алтай/Сибирь). Нужно показывать время в обоих поясах.

**Файлы:**
- `handlers/booking_calendar.py` — основной flow записи
- `handlers/ai_chat.py` — проверка состояния бронирования
- `handlers/booking.py` — обработка контакта
- `services/user_profiles.py` — новый модуль профилей
- `services/telegram.py` — send_message_keyboard
- `app.py` — callback обработчики

**Миграция БД:**
```sql
ALTER TABLE bookings ADD COLUMN realtor_name TEXT;
ALTER TABLE bookings ADD COLUMN realtor_phone TEXT;
ALTER TABLE bookings ADD COLUMN show_description TEXT;
ALTER TABLE bookings ADD COLUMN timezone TEXT DEFAULT 'altai';

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    timezone TEXT DEFAULT 'altai',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);
```

**Flow:**
1. Выбор часового пояса: `[Москва/Сочи]` `[Алтай/Сибирь]`
2. Выбор даты (кнопки)
3. Ввод одним сообщением: `10:30 89181011091 Сергей Меганедвижка`
4. Подтверждение с двойным временем

**Формат времени (пояс риэлтора первый):**
- Риэлтор из Москвы: `10:30 (Мск) — 14:30 (Алтай)`
- Риэлтор из Алтая: `14:30 (Алтай) — 10:30 (Мск)`

**Callbacks:**
```
book_tz_moscow       — выбран пояс Москва
book_tz_altai        — выбран пояс Алтай
book_date_{date}     — выбрана дата
book_submit          — отправить заявку
book_add_phone       — добавить телефон
```

**Проверка:**
```bash
systemctl restart rizalta-bot-dev
# В Telegram: Записаться на показ -> выбор пояса -> дата -> ввод данных
```

---

### ЗАДАЧА 5: Сортировка лотов по площади в Корпусе 3

**Файл:** `handlers/corp3.py`

**Изменение в функции handle_corp3_show_list():**
```python
# После проверки whitelist, перед if not units:
units = sorted(units, key=lambda u: u['area'])
```

**Проверка:**
```bash
systemctl restart rizalta-bot-dev
# В Telegram: /corp3 -> выбрать фильтр -> лоты идут от меньшей площади к большей
```

### ЗАДАЧА 9: Whitelist Корпуса 3 в БД + команда /wl

**Дата:** 26.01.2026

**Проблема:** Whitelist хранился в settings.py. Для добавления пользователя нужно: редактировать файл, перезапускать сервисы, коммитить.

**Решение:** Перенос в SQLite + команда /wl для управления без перезапуска.

**Файлы:**
- `properties.db` — новая таблица `corp3_whitelist`
- `handlers/corp3.py` — функция `is_whitelisted()` из БД
- `handlers/kp.py` — использует `is_whitelisted` из corp3
- `app.py` — команда `/wl`
- `config/settings.py` — удалён `CORP3_WHITELIST`

**Структура таблицы:**
```sql
CREATE TABLE corp3_whitelist (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Команды /wl (только админ 512319063):**
```
/wl              — справка
/wl list         — показать всех
/wl add ID Имя   — добавить (пример: /wl add 123456789 Иван)
/wl remove ID    — удалить (пример: /wl remove 123456789)
```

**Проверка:**
```bash
# Проверить таблицу
sqlite3 /opt/bot-dev/properties.db "SELECT * FROM corp3_whitelist;"

# В боте
/wl list
/wl add 123 Тест
/wl remove 123
```

**При деплое DEV → PROD:**
```bash
# Исправить путь БД
sed -i 's|/opt/bot-dev/properties.db|/opt/bot/properties.db|' /opt/bot/handlers/corp3.py
sed -i 's|/opt/bot-dev/properties.db|/opt/bot/properties.db|' /opt/bot/app.py
```

---

## СЕССИЯ 27.01.2026

### ЗАДАЧА: Фильтрация новостей (только экономика РФ)

**Файлы:** `handlers/news.py`

**Шаги:**
1. Заменить RSS источники (строки 333-350)
2. Добавить include/exclude keywords (строки 380-430)

**RSS источники:**
- Ведомости: https://www.vedomosti.ru/rss/news
- Коммерсант Экономика: https://www.kommersant.ru/RSS/section-economics.xml
- РБК Экономика: https://rssexport.rbc.ru/rbcnews/economics.rss

**Include keywords:** цб, ставк, инфляц, ввп, недвижимость, ипотек, туризм, курорт
**Exclude keywords:** путин, война, украин, убий, теракт, политик

---

### ЗАДАЧА: Команда /ca для управления лотами Корпуса 3

**Файлы:** `app.py` (после строки 1418)

**Команды:**
```
/ca list        — показать скрытые лоты
/ca hide А300   — скрыть лот (status='sold')
/ca show А300   — показать лот (status='available')
```

**Код добавляет функцию:**
```python
async def handle_corp3_admin_command(chat_id: int, text: str):
    # Парсинг команды, изменение JSON, очистка кеша
```

**Важно:** После изменения JSON вызывать `_units_cache.clear()`

---

### ИНЦИДЕНТ: Сравнение с депозитом показывает 1000₽

**Симптомы:** Кнопка "Сравнить с депозитом" показывает цену 1000₽ вместо реальной

**Причина:** Формат callback изменился с `compare_lot_{code}_{price}` на `compare_lot_{code}_{building}_{price}`, но парсер не обновили

**Файл:** `app.py` (строки 986-993)

**Было:**
```python
lot_code = parts[2]
price = int(parts[3]) * 1000
```

**Стало:**
```python
lot_code = parts[2]
building = int(parts[3])
price = int(parts[4]) * 1000 if len(parts) > 4 else int(parts[3]) * 1000
```

**Урок:** При изменении формата callback — искать ВСЕ места парсинга:
```bash
grep -rn "compare_lot_" /opt/bot-dev/
```

---

### ЗАДАЧА: Список админов ADMIN_IDS

**Файл:** `app.py` (строка 1507)

**Было:**
```python
ADMIN_ID = 512319063
if chat_id == ADMIN_ID:
```

**Стало:**
```python
ADMIN_IDS = [512319063, 8000703751]
if chat_id in ADMIN_IDS:
```

**Команда замены:**
```bash
sed -i 's/ADMIN_ID = 512319063/ADMIN_IDS = [512319063, 8000703751]/' /opt/bot/app.py
sed -i 's/chat_id == ADMIN_ID/chat_id in ADMIN_IDS/g' /opt/bot/app.py
```

---

### ИНФРАСТРУКТУРА: Апгрейд сервера и WAL mode

**Апгрейд Timeweb:**
- 2 vCPU → 4 vCPU
- 4 GB RAM → 8 GB RAM
- Цена: 1500 → 2760 ₽/мес

**WAL mode для SQLite:**
```bash
sqlite3 /opt/bot/properties.db "PRAGMA journal_mode=WAL;"
sqlite3 /opt/bot/secretary.db "PRAGMA journal_mode=WAL;"
```

**Клонирование сервера:**
- Создан клон в Амстердаме как резервная копия
- Для миграции в РФ: создать образ → перенести в Москву → развернуть

---

## Добавлено 29.01.2026

### ИНЦИДЕНТ: Клон сервера перехватывал запросы

**Симптомы:**
- Два ежедневных отчёта (разные метрики)
- /wl add работает, но пользователь не видит Корпус 3
- Непредсказуемое поведение бота

**Диагностика:**
```bash
# На клоне — проверить что запущено
systemctl list-units --type=service --state=running | grep -E "rizalta|bot|watchdog"
```

**Причина:** Клон сервера в Амстердаме работал с теми же Cloudflare Tunnel, перехватывая часть запросов. Разные БД → рассинхронизация.

**Решение:**
```bash
# На клоне
systemctl stop rizalta-bot rizalta-bot-dev rizalta-watchdog cloudflare-rizalta rizalta-dev-tunnel rizalta-dev-api
systemctl disable rizalta-bot rizalta-bot-dev rizalta-watchdog cloudflare-rizalta rizalta-dev-tunnel rizalta-dev-api
```

### ИНЦИДЕНТ: corp3_units.json сбрасывался после git операций

**Симптомы:** Скрытые через /ca hide лоты снова становились видимыми (обычно утром).

**Диагностика:**
```bash
cd /opt/bot && git ls-files | grep corp3
git status data/corp3_units.json
```

**Причина:** Файл отслеживался git. При любом git checkout/pull — затирался версией из репо.

**Решение:**
```bash
echo "data/corp3_units.json" >> .gitignore
git rm --cached data/corp3_units.json
git commit -m "fix: исключить corp3_units.json из git"
git push
```

### ЗАДАЧА: Исправление жёстких путей к БД

**Файлы:** app.py (строки 1361, 1425)

**Проблема:** PROD бот писал в DEV базу.

**Решение:**
```bash
sed -i 's|db_path = "/opt/bot-dev/properties.db"|db_path = "properties.db"|' /opt/bot-dev/app.py
sed -i 's|json_path = "/opt/bot-dev/data/corp3_units.json"|json_path = "data/corp3_units.json"|' /opt/bot-dev/app.py
```

**Проверка:**
```bash
grep -n "db_path\|json_path" /opt/bot-dev/app.py | grep -E "1361|1425"
```

---

## Добавлено 03.02.2026

### ЗАДАЧА 10: Скрытие/показ целых корпусов (hidden_buildings)

**Контекст:** Иногда нужно временно скрыть целый корпус (ценовая пауза, смена прайса). Должно работать одновременно в боте, API и Mini App.

**Файлы:**
- `data/hidden_buildings.json` — конфиг (НОВЫЙ)
- `services/units_db.py` — функция `get_hidden_buildings()` + фильтры в 3 местах
- `app.py` — фильтр в `/api/lots` endpoint
- `/opt/miniapp/src/App.jsx` — динамические табы корпусов

**Конфиг:**
```json
{"hidden": [2], "comment": "Корпус 2 скрыт — ценовая пауза"}
```

**Чтобы скрыть корпус:**
```bash
# Редактируем конфиг
echo '{"hidden": [2], "comment": "причина"}' > /opt/bot-dev/data/hidden_buildings.json

# Перезапуск (конфиг читается при каждом запросе, но uvicorn кэширует)
systemctl restart rizalta-bot-dev
systemctl restart rizalta-dev-api
```

**Чтобы вернуть корпус:**
```bash
echo '{"hidden": [], "comment": "все корпуса открыты"}' > /opt/bot-dev/data/hidden_buildings.json
systemctl restart rizalta-bot-dev
systemctl restart rizalta-dev-api
```

**Где фильтруется:**
1. `units_db.py:get_building_stats()` — меню выбора корпуса (Python filter после SQL)
2. `units_db.py:get_lots_filtered()` — поиск по площади/бюджету (SQL: AND building NOT IN)
3. `units_db.py:get_lots_by_code()` — поиск по коду (Python filter: row[1] not in hidden)
4. `app.py:/api/lots` — API для Mini App (SQL: AND building NOT IN)

**⚠️ При деплое в PROD:**
- В `app.py` путь к конфигу захардкожен! Заменить `/opt/bot-dev/` на `/opt/bot/`
- Скопировать `hidden_buildings.json` в `/opt/bot/data/`

**Проверка:**
```bash
# Python тест
python3 -c "
from services.units_db import get_building_stats
stats = get_building_stats()
for s in stats: print(f'Корпус {s[\"building\"]}: {s[\"count\"]} лотов')
"

# API тест
curl -s http://localhost:8002/api/lots | python3 -c "
import json,sys; data=json.load(sys.stdin)
print(set(l['building'] for l in data['lots']))
"
```

### ЗАДАЧА 11: Mini App — динамические табы корпусов

**Файл:** `/opt/miniapp/src/App.jsx`

**Что изменено:**
- Убран хардкод `[1,2].map` → `buildings.map` (из данных API)
- Добавлен `buildingNames = {1: "Family", 2: "Business", 3: "Digital"}`
- `fetch('/api/lots')` → `fetch(API_PATH + '/lots')` (DEV/PROD routing через env param)
- Автовыбор первого доступного корпуса при загрузке

**Сборка и деплой:**
```bash
cd /opt/miniapp
npm run build
git add src/App.jsx && git commit -m "описание" && git push origin main
# Vercel автодеплоит (или: npx vercel --prod)
```

### ИНЦИДЕНТ: Старый uvicorn на порту 8002 (не обновлялся)

**Симптомы:** DEV API возвращает старые данные после изменений кода.

**Причина:** На порту 8002 висел uvicorn запущенный давно, не перезапускался при `systemctl restart rizalta-bot-dev` (это polling бот, не uvicorn).

**Решение:**
```bash
# Проверить процесс
ss -tlnp | grep 8002

# Перезапустить DEV API
systemctl restart rizalta-dev-api
```

**Урок:** DEV имеет ДВА сервиса:
- `rizalta-bot-dev` — polling бот (без HTTP порта)
- `rizalta-dev-api` — uvicorn :8002 (API для Mini App)
При изменении app.py нужно перезапускать ОБА!

### ЗАДАЧА: Деплой скрытия корпуса из DEV в PROD

**Контекст:** Скрытие корпуса уже работает в DEV, нужно перенести в PROD.

**Файлы:**
- `data/hidden_buildings.json` — конфиг скрытия
- `services/units_db.py` — фильтрация в боте (get_building_stats, get_lots_filtered, get_lots_by_code)
- `app.py` — фильтрация в /api/lots endpoint (для Mini App)

**Шаги:**

1. Бэкап PROD перед изменениями:
```bash
mkdir -p /opt/bot/data/backup_$(date +%Y%m%d)_prod
cp /opt/bot/services/units_db.py /opt/bot/app.py /opt/bot/data/backup_$(date +%Y%m%d)_prod/
```

2. Копирование файлов из DEV:
```bash
cp /opt/bot-dev/data/hidden_buildings.json /opt/bot/data/
cp /opt/bot-dev/services/units_db.py /opt/bot/services/
```

3. Правка PROD app.py — добавить фильтр в /api/lots:
В endpoint `/api/lots`, после `params = []`, перед `if building:` вставить:
```python
    # Фильтр скрытых корпусов
    import json
    try:
        with open("/opt/bot/data/hidden_buildings.json") as f:
            hidden = json.load(f).get("hidden", [])
        if hidden:
            placeholders = ",".join("?" * len(hidden))
            query += f" AND building NOT IN ({placeholders})"
            params.extend(hidden)
    except:
        pass
```
⚠️ Путь ОБЯЗАТЕЛЬНО `/opt/bot/data/...` (не `/opt/bot-dev/...`!)

4. Проверка синтаксиса:
```bash
python3 -m py_compile /opt/bot/app.py && echo "OK"
python3 -m py_compile /opt/bot/services/units_db.py && echo "OK"
```

5. Рестарт и проверка:
```bash
sudo systemctl restart rizalta-bot
sleep 3
curl -s localhost:8000/api/lots | python3 -c "import sys,json; d=json.load(sys.stdin)['lots']; print('Корпуса:', sorted(set(l['building'] for l in d)), 'Лотов:', len(d))"
```

**Ожидаемый результат:** Корпуса: [1] Лотов: 253 (без скрытого корпуса)

### ЗАДАЧА: Вернуть скрытый корпус

**Контекст:** Корпус скрыт через hidden_buildings.json, нужно вернуть обратно.

**Шаги:**

1. Редактировать конфиг:
```bash
# PROD
echo '{"hidden": [], "comment": "Все корпуса открыты"}' > /opt/bot/data/hidden_buildings.json

# DEV (если нужно)
echo '{"hidden": [], "comment": "Все корпуса открыты"}' > /opt/bot-dev/data/hidden_buildings.json
```

2. Перезапуск:
```bash
sudo systemctl restart rizalta-bot        # PROD
sudo systemctl restart rizalta-dev-api    # DEV API
sudo systemctl restart rizalta-bot-dev    # DEV бот
```

3. Проверка:
```bash
# PROD
curl -s localhost:8000/api/lots | python3 -c "import sys,json; d=json.load(sys.stdin)['lots']; print('PROD:', sorted(set(l['building'] for l in d)), len(d))"
# DEV
curl -s localhost:8002/api/lots | python3 -c "import sys,json; d=json.load(sys.stdin)['lots']; print('DEV:', sorted(set(l['building'] for l in d)), len(d))"
```

**Ожидаемый результат:** Оба корпуса видны, Mini App обновится автоматически (динамические табы).

**Важно:** Парсер (cron 03:00) не зависит от hidden_buildings.json — он продолжает обновлять все корпуса в БД. Данные скрытого корпуса всегда актуальны.

### ЗАДАЧА: Передеплой Mini App на Vercel

**Контекст:** Vercel не всегда автоматически подхватывает push в GitHub.

**Шаги:**

1. Убедиться что код на GitHub актуальный:
```bash
cd /opt/miniapp && git log --oneline -3
```

2. Ручной деплой:
```bash
cd /opt/miniapp && npx vercel --prod
```

3. Проверка:
```bash
# Проверить что хеш JS файла изменился
curl -s https://rizalta-miniapp.vercel.app | grep -o 'index-[^"]*\.js'
```

**Альтернатива:** Ретриггернуть деплой через Vercel Dashboard.

---

### ЗАДАЧА: Фикс аренды в "Сравнить с депозитом" (передача area через callback chain)

**Контекст:** Аренда в модуле сравнения с депозитом считалась на захардкоженных 26.8 м² вместо реальной площади лота.

**Причина:** В Telegram callback_data ограничен 64 байтами. Данные передаются между шагами только через эту строку. Площадь лота терялась в цепочке callbacks.

**Файлы (6):**
- `handlers/compare.py` — функции сравнения
- `handlers/kp.py` — карточка лота К1/К2 (кнопка "Сравнить с депозитом")
- `handlers/corp3.py` — карточка лота К3
- `app.py` — парсинг callback_data
- `services/compare_pdf_generator.py` — генерация PDF
- `services/investment_compare.py` — расчёты + format_comparison_table

**Решение:** Передавать `area10 = int(area_m2 * 10)` в callback_data (41.1 м² → 411)

**Шаги:**

1. В handlers/kp.py и handlers/corp3.py — добавить area10 в callback:
```python
# Было:
f"compare_lot_{lot['code']}_{lot['building']}_{lot['price']//1000}"
# Стало:
f"compare_lot_{lot['code']}_{lot['building']}_{lot['price']//1000}_{int(lot['area']*10)}"
```

2. В handlers/compare.py — добавить area_m2 параметр во все функции:
```python
async def handle_compare_lot(chat_id: int, lot_code: str, price: int, area_m2: float = 26.8):
    area10 = int(area_m2 * 10)
    # ... и добавить _{area10} во все callback-и внутри
```

3. В app.py — парсить area10 с обратной совместимостью:
```python
elif data.startswith("compare_lot_"):
    parts = data.split("_")
    lot_code = parts[2]
    building = int(parts[3])
    price = int(parts[4]) * 1000 if len(parts) > 4 else int(parts[3]) * 1000
    area_m2 = int(parts[5]) / 10 if len(parts) > 5 else 26.8  # ← обратная совместимость
    await handle_compare_lot(chat_id, lot_code, price, area_m2)
```

4. В services/investment_compare.py — format_comparison_table:
```python
def format_comparison_table(amount: float, area_m2: float = 26.8) -> str:
    # ...
    r = compare_investments(amount, years, area_m2)
```

5. В services/compare_pdf_generator.py:
```python
def generate_compare_pdf(amount: int, years: int, username: str = "", area_m2: float = 26.8):
    rizalta = calculate_rizalta(amount, years, area_m2)
```

**Callback chain (новый формат):**
```
compare_lot_{code}_{building}_{price_k}_{area10}
  → compare_period_{years}_{amount}_{area10}
    → compare_full_{years}_{amount}_{area10}
      → compare_pdf_{years}_{amount}_{area10}
      → compare_lot_back_{amount}_{area10}
    → compare_table_{amount}_{area10}
```

**Проверка:**
```bash
# Синтаксис
python3 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['handlers/compare.py', 'handlers/kp.py', 'handlers/corp3.py', 'app.py', 'services/compare_pdf_generator.py', 'services/investment_compare.py']]"

# Перезапуск DEV
sudo systemctl restart rizalta-bot-dev

# Тест в боте:
# 1. Лот ~25 м² → "Сравнить с депозитом" → 11 лет → записать аренду
# 2. Лот ~60 м² → аренда должна быть ~2.4x больше
```

**Ключевые строки для поиска:**
```bash
grep -rn "compare_lot_" handlers/ --include="*.py"
grep -n "def handle_compare" handlers/compare.py
grep -n "compare_investments\|calculate_rizalta" services/investment_compare.py
```


---

## Добавлено 09.02.2026

### ИНЦИДЕНТ: ImportError handle_kp_building_all — 500 на кнопке "Все лоты корпуса"

**Симптомы:** Пользователи нажимали кнопку «📋 Все лоты корпуса» в меню этажей → бесконечный спиннер. Telegram ретраил запрос 5-6 раз.

**Диагностика:**
```bash
journalctl -u rizalta-bot --since "today" | grep -E "500|Error|ImportError"
# Результат: ImportError: cannot import name 'handle_kp_building_all' from 'handlers.kp'
```

**Причина:** В app.py был роутинг `kp_building_all_` → `handle_kp_building_all`, кнопка генерировалась в `handle_kp_building`, но сама функция никогда не была написана.

**Решение:** Добавлена функция в handlers/kp.py (после handle_kp_building, перед handle_kp_floor):
```python
async def handle_kp_building_all(chat_id: int, building: int):
    """Показывает все лоты корпуса с пагинацией."""
    lots = get_lots_by_building(building)
    building_name = get_building_name(building)
    # ... стандартная пагинация через _search_cache и MAX_BUTTONS_PER_MESSAGE
```

**Проверка:**
```bash
grep -n "handle_kp_building_all" /opt/bot/handlers/kp.py
python3 -c "import py_compile; py_compile.compile('handlers/kp.py', doraise=True)"
systemctl restart rizalta-bot
journalctl -u rizalta-bot --since "1 min ago" | grep -E "500|Error"
```

**Урок:** При добавлении кнопки + роутинга — всегда проверять что целевая функция существует:
```bash
# Найти все импорты из handlers/kp.py в app.py
grep "from handlers.kp import" /opt/bot/app.py | awk '{print $NF}' | sort -u

# Проверить что все они есть
grep "^async def " /opt/bot/handlers/kp.py | awk '{print $3}' | cut -d'(' -f1 | sort -u
```

### ЗАДАЧА: Создание ARCHITECTURE.md и CALLBACKS.md

**Контекст:** Проект вырос настолько, что LLM-ассистент не может изучить весь код за раз — заканчивается контекстное окно.

**Файлы:**
- `docs/RIZALTA_ARCHITECTURE.md` — карта проекта
- `docs/RIZALTA_CALLBACKS.md` — индекс callback паттернов

**Как использовать в начале сессии:**
```bash
cat /opt/bot-dev/docs/RIZALTA_ARCHITECTURE.md
cat /opt/bot-dev/docs/RIZALTA_CALLBACKS.md
```

**Как собирать данные для обновления:**
```bash
# Все callback паттерны
grep -n "elif data.startswith\|elif data ==" /opt/bot-dev/app.py

# Все функции в handlers
for f in /opt/bot-dev/handlers/*.py; do echo "=== $(basename $f) ==="; grep -n "^async def " $f; done

# Все функции в services
for f in /opt/bot-dev/services/*.py; do echo "=== $(basename $f) ==="; grep -n "^def \|^async def " $f; done
```

---

## Добавлено 10.02.2026

### ЗАДАЧА: WebApp — Белый список + Корпус 3

**Контекст:** В webapp нет chat_id как в TG боте. Реализован доступ через токен в URL.

**Файлы:**
- `backend/app.py` — webapp.db, init_webapp_db(), seed_token(), get_access_level(), endpoints
- `frontend/src/utils/auth.js` — captureTokenFromURL, verifyAccess, authFetch, isWhitelisted
- `frontend/src/pages/Corp3.jsx` — шахматка К3
- `frontend/src/pages/Home.jsx` — условная кнопка
- `frontend/src/pages/LotDetail.jsx` — поддержка К3
- `frontend/src/pages/Catalog.jsx` — упрощённые кнопки фильтров

**Механика:**
1. Ссылка `?token=XXX` → captureTokenFromURL() → localStorage
2. verifyAccess() → /api/access/check → level: white/public
3. isWhitelisted() → показать/скрыть кнопку «Корпус 3»
4. authFetch() → X-Access-Token header в запросах к К3

**Endpoints:**
```
GET /api/access/check         — проверка токена
GET /api/corp3/lots           — лоты К3 (403 без токена)
GET /api/corp3/layout/{code}  — планировки К3 (403 без токена)
```

**Получить токен:**
```bash
sqlite3 /opt/webapp/backend/webapp.db "SELECT token FROM access_tokens"
```

**Тестирование:**
```bash
TOKEN=$(sqlite3 /opt/webapp/backend/webapp.db "SELECT token FROM access_tokens LIMIT 1")
curl -s -H "X-Access-Token: $TOKEN" http://127.0.0.1:8003/api/access/check
curl -s -H "X-Access-Token: $TOKEN" http://127.0.0.1:8003/api/corp3/lots | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total'])"
```

**Откат:**
```bash
cd /opt/webapp && git checkout v0.5.0-stable
rm -f backend/webapp.db
cd frontend && npm run build
systemctl restart webapp
```

### ИНФРАСТРУКТУРА: systemd сервис для WebApp

**Файл:** `/etc/systemd/system/webapp.service`

**Команды:**
```bash
systemctl start webapp
systemctl stop webapp
systemctl restart webapp
systemctl status webapp
journalctl -u webapp -f
```

**Было:** nohup (умирает при перезагрузке)
**Стало:** systemd (enabled, Restart=always, RestartSec=5)

### ЗАДАЧА: Excel актуализация статусов Корпуса 3

**Описание:** Админ отправляет Excel файл боту в Telegram → бот автоматически обновляет статусы лотов К3

**Файлы:** app.py (handle_corp3_excel_update + webhook роутинг), run_polling.py (роутинг + импорт)

**Логика:**
- Все коды лотов из Excel (колонка G) = sold
- Все остальные лоты в corp3_units.json = available
- Обновляет оба окружения: PROD (data/corp3_units.json) и DEV (/opt/bot-dev/data/corp3_units.json)

**Доступ:** только chat_id в [512319063, 8000703751]

**Проверка:**
```bash
# Отправить .xlsx файл боту в Telegram
# Бот ответит отчётом с изменениями
```

### ИНЦИДЕНТ: Рассинхронизация whitelist DEV↔PROD

**Симптомы:** Пользователь 868791592 добавлен 28.01.2026 но не видел К3

**Причина:** Баг с хардкодом путей (app.py db_path="/opt/bot-dev/properties.db"). PROD бот писал в DEV базу. При последующих обновлениях DEV базы записи терялись.

**Решение:** 
1. Фикс путей уже применён ранее (12.02.2026)
2. Полный аудит: собраны все ID из истории чатов
3. Синхронизация: 4 недостающих добавлены в DEV

**Диагностика:**
```bash
# Сравнить DEV и PROD whitelist
python3 -c "
import sqlite3
dev = sqlite3.connect('/opt/bot-dev/properties.db')
prod = sqlite3.connect('/opt/bot/properties.db')
dev_ids = {r[0] for r in dev.execute('SELECT chat_id FROM corp3_whitelist').fetchall()}
prod_ids = {r[0] for r in prod.execute('SELECT chat_id FROM corp3_whitelist').fetchall()}
print('Only DEV:', dev_ids - prod_ids)
print('Only PROD:', prod_ids - dev_ids)
"
```

**Профилактика:** Всегда добавлять в оба окружения. Периодически сверять.
