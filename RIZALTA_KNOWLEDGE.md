# RIZALTA BOT — База знаний

## Быстрый старт

```bash
# SSH на сервер
ssh root@72.56.64.91

# Путь к боту
cd /opt/bot

# Логи
journalctl -u rizalta-bot -f

# Перезапуск
systemctl restart rizalta-bot
```

---

## Архитектура

```
Telegram → Cloudflare Tunnel → localhost:8000 → FastAPI (app.py)
                                                      ↓
                                              handlers/*.py
                                                      ↓
                                              services/*.py
```

---

## Ключевые файлы

### app.py — Главный файл

```python
# Webhook endpoint
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    ...

# Роутинг callback'ов
async def process_callback(callback: Dict):
    data = callback.get("data", "")
    
    if data == "kp_menu": ...
    elif data.startswith("book_spec_"): ...
    elif data.startswith("book_confirm_"): ...
    ...

# Обработка сообщений
async def process_message(chat_id, text, user_info):
    # 1. Кнопки меню (точное совпадение)
    # 2. Regex паттерны
    # 3. AI консультант
```

### handlers/ai_chat.py — AI консультант

```python
# Function Calling
TOOLS = [
    "get_finance_info",     # Финансы по лоту
    "get_unit_info",        # Информация о лоте
    "calculate_roi",        # Расчёт ROI
    "search_units",         # Поиск лотов
    "get_documents",        # Документы
    "send_presentation",    # Презентация
    "open_fixation",        # Фиксация клиента
    "open_shahmatka",       # Шахматка
    "send_documents",       # Отправка документов
    "show_media",           # Медиа-материалы
]

# Обработка
async def handle_free_text(chat_id, text):
    response = await get_ai_response(text)
    if response.tool_calls:
        await handle_tool_call(...)
    else:
        await send_message(chat_id, response.content)
```

### handlers/booking_calendar.py — Календарь

```python
SPECIALISTS = [
    {"id": 1, "name": "Специалист 1", "telegram_id": 512319063},
    {"id": 2, "name": "Специалист 2", "telegram_id": 512319063},
    {"id": 3, "name": "Специалист 3", "telegram_id": 512319063},
]

# Поток:
# 1. handle_booking_start() → выбор специалиста
# 2. handle_select_specialist() → выбор даты
# 3. handle_select_date() → выбор времени
# 4. handle_select_time() → заявка отправлена
# 5. handle_confirm_booking() → подтверждение
# 6. handle_decline_booking() → отклонение
```

### handlers/kp.py — Коммерческие предложения

```python
# Поиск по площади
async def handle_kp_area_range(chat_id, min_area, max_area):
    lots = get_lots_by_area_range(min_area, max_area)
    # Показывает 8 кнопок + "Показать все"

# Показать все
async def handle_kp_show_all_area(chat_id, min_area, max_area):
    # Показывает ВСЕ лоты кнопками
```

### services/speech.py — Голосовое управление

```python
from openai import OpenAI

def transcribe_voice(file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ru"
        )
    return transcript.text
```

### services/telegram.py — Telegram API

```python
async def send_message(chat_id, text, with_keyboard=False, buttons=None)
async def send_message_inline(chat_id, text, inline_buttons=None)
async def send_document(chat_id, filepath, caption=None)
async def send_photo(chat_id, filepath, caption=None)
async def send_media_group(chat_id, filepaths, caption=None)
async def download_file(file_id, save_path) -> Optional[str]
async def answer_callback_query(callback_id, text=None)
```

---

## База данных

### properties.db

```sql
-- Таблица лотов
CREATE TABLE units (
    id INTEGER PRIMARY KEY,
    code TEXT,           -- A101, B202
    building INTEGER,    -- 1, 2, 3
    floor INTEGER,
    area_m2 REAL,
    price_rub INTEGER,
    status TEXT          -- available, sold, reserved
);

-- Таблица бронирований
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    username TEXT,
    specialist_id INTEGER,
    specialist_name TEXT,
    booking_date TEXT,   -- 2025-12-09
    booking_time TEXT,   -- 14:00
    status TEXT,         -- pending, confirmed, declined
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Конфигурация (.env)

```bash
TELEGRAM_BOT_TOKEN=8343378629:AAHHacgXmIVhShht...
OPENAI_API_KEY=sk-proj-...

MANAGER_EMAIL=89181011091s@mail.ru
BOT_EMAIL=rizalta-bot@mail.ru
SMTP_HOST=smtp.mail.ru
SMTP_PORT=587
SMTP_USER=rizalta-bot@mail.ru
SMTP_PASSWORD=...
```

---

## Systemd сервисы

```bash
# Бот
/etc/systemd/system/rizalta-bot.service
ExecStart=/opt/bot/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000

# Туннель + автообновление webhook
/etc/systemd/system/cloudflare-rizalta.service
ExecStart=/usr/bin/cloudflared tunnel --url http://127.0.0.1:8000
ExecStartPost=/opt/bot/update_webhook.sh
```

---

## Автобэкапы

```bash
# Ежедневный (3:00 UTC)
/opt/bot/backup.sh
# Содержимое: .env, properties.db, data/

# Еженедельный (Вс 4:00 UTC)
/opt/bot/backup_weekly.sh
# Содержимое: kp_all/, media/

# Email: 89181011091s@mail.ru
```

---

## Частые операции

### Добавить новую кнопку

1. В `app.py` → `process_callback()` добавить обработчик
2. В `handlers/*.py` создать функцию
3. В `handlers/__init__.py` добавить импорт

### Добавить AI-функцию

1. В `services/ai_chat.py` → TOOLS добавить описание
2. В `handlers/ai_chat.py` добавить обработку tool_call

### Изменить специалистов

```python
# handlers/booking_calendar.py
SPECIALISTS = [
    {"id": 1, "name": "Иван Петров", "telegram_id": 123456789, "email": "..."},
    ...
]
```

### Деплой изменений

```bash
# Локально
scp файл.py root@72.56.64.91:/opt/bot/handlers/

# На сервере
systemctl restart rizalta-bot
journalctl -u rizalta-bot -f
```

---

## Ссылки

- GitHub: https://github.com/semukhin/RIZALTA_BOT
- Сервер: 72.56.64.91
- Telegram: @RealtMeAI_bot
