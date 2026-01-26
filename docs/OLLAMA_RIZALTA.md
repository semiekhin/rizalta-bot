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
