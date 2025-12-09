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

- GitHub: https://github.com/semiekhin/rizalta-bot
- Сервер: 72.56.64.91
- Telegram: @RealtMeAI_bot

---

## Ключевые решения и почему

### Cloudflare Tunnel вместо открытого порта
**Почему:** Скрывает реальный IP сервера, бесплатный SSL, защита от DDoS.
**Нюанс:** При каждом перезапуске создаётся новый URL, поэтому нужен скрипт update_webhook.sh.

### Hybrid подход (Regex + AI)
**Почему:** Regex быстрый и бесплатный для очевидных команд ("скинь презу"). AI дорогой, используем только для сложных запросов.
**Реализация:** Сначала проверяем regex в handlers/ai_chat.py, если не сработал — вызываем OpenAI.

### SQLite вместо PostgreSQL
**Почему:** Простота, не нужен отдельный сервер, достаточно для текущей нагрузки.
**Файл:** /opt/bot/properties.db

### Systemd вместо nohup
**Почему:** Автозапуск при перезагрузке, автоматический рестарт при падении, удобные логи через journalctl.

---

## Частые ошибки и решения

### "Address already in use" (порт 8000 занят)
```bash
fuser -k 8000/tcp
sleep 2
systemctl start rizalta-bot
```

### "ProxyError: Unable to connect to proxy"
Удалить строку HTTPS_PROXY из .env:
```bash
sed -i '/HTTPS_PROXY/d' /opt/bot/.env
systemctl restart rizalta-bot
```

### Git push rejected (remote contains work)
```bash
git push --force origin main
```
⚠️ Только если уверен что твоя версия правильная!

### Webhook не обновился после перезапуска
Проверить URL туннеля и обновить вручную:
```bash
journalctl -u cloudflare-rizalta --no-pager | grep trycloudflare
# Скопировать URL
source /opt/bot/.env
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=НОВЫЙ_URL/telegram/webhook"
```

### Бот не отвечает после апгрейда сервера
После миграции на новую ноду может появиться прокси. Проверить:
```bash
grep -i proxy /opt/bot/.env
# Если есть HTTPS_PROXY — удалить
```

---

## Полезные команды (часто используемые)

```bash
# Логи в реальном времени
journalctl -u rizalta-bot -f

# Последние 50 строк логов
journalctl -u rizalta-bot --no-pager -n 50

# Статус всех сервисов
systemctl status rizalta-bot cloudflare-rizalta --no-pager

# Проверка RAM и диска
free -m && df -h

# Проверка забаненных IP
fail2ban-client status sshd

# Ручной запуск бэкапа
/opt/bot/backup.sh

# Проверка webhook
source /opt/bot/.env
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

---

## Нюансы для следующего чата

1. **Специалисты в календаре** — сейчас все указывают на один telegram_id (512319063). Нужно получить реальные данные.

2. **OAZIS Bot** — на том же сервере, порт 8001. Не трогать если не просят.

3. **Бэкапы** — приходят на 89181011091s@mail.ru. Ежедневный ~100KB, еженедельный ~80MB.

4. **При изменении app.py** — обязательно перезапустить: `systemctl restart rizalta-bot`

5. **GitHub репо** — semiekhin (с "e"), не semukhin!

---

## Модуль новостей (handlers/news.py)

### API ключи и эндпоинты
```python
# Aviasales (бесплатный)
AVIASALES_TOKEN = "9d268d3a67128df02ab46acf3fa764fa"
# https://api.travelpayouts.com/aviasales/v3/prices_for_dates

# Курсы валют ЦБ РФ (бесплатный, без ключа)
# https://www.cbr-xml-daily.ru/daily_json.js

# Погода Open-Meteo (бесплатный, без ключа)
# https://api.open-meteo.com/v1/forecast
# Координаты Белокурихи: 51.996, 84.993
```

### RSS источники
```python
RSS_SOURCES = [
    "https://ria.ru/export/rss2/archive/index.xml",      # РИА Новости
    "https://www.kommersant.ru/rss/main.xml",            # Коммерсант
    "https://lenta.ru/rss",                               # Lenta.ru
    "https://www.vedomosti.ru/rss/news",                 # Ведомости
    "https://tass.ru/rss/v2.xml",                        # ТАСС
]
```

### Частые проблемы

**CBR API возвращает application/javascript:**
```python
# Решение: content_type=None
await response.json(content_type=None)
```

**Превью ссылки Aviasales в сообщении:**
```python
# Решение: добавить параметр
await send_message_inline(chat_id, text, buttons, disable_web_page_preview=True)
```

### Callback'и в app.py
```python
# Строки ~455-478
elif data == "news_menu": ...
elif data == "news_currency": ...
elif data == "news_weather": ...
elif data == "news_digest": ...
elif data == "news_flights": ...
```

### Текстовый обработчик
```python
# Строка ~613 в app.py
if "📰 Новости" in text:
    from handlers.news import handle_news_menu
    await handle_news_menu(chat_id)
    return
```

---

## Сессия 08.12.2025 — ключевые команды
```bash
# Установка aiohttp
/opt/bot/venv/bin/pip install aiohttp

# Проверка API авиабилетов
curl -s "https://api.travelpayouts.com/aviasales/v3/prices_for_dates?origin=MOW&destination=RGK&departure_at=2025-12&token=9d268d3a67128df02ab46acf3fa764fa"

# Убить зависший процесс на порту 8000
pkill -9 -f uvicorn; sleep 2; systemctl restart rizalta-bot
```

---

## Нюансы для следующего чата (обновлено)

6. **Модуль новостей** — handlers/news.py содержит 5 функций: handle_news_menu, handle_currency_rates, handle_weather, handle_flights, handle_news_digest

7. **Aviasales токен** — 9d268d3a67128df02ab46acf3fa764fa (зарегистрирован на 89181011091s@mail.ru)

8. **RSS без ключей** — РИА, Коммерсант, Lenta, Ведомости, ТАСС работают бесплатно

9. **AI-агент (Контент-завод)** — следующая задача: парсинг → GPT рерайт → DALL-E → автопостинг

---

## Сессия 09.12.2025 — Dev-окружение и синхронизация данных

### Архитектура данных (ВАЖНО!)

**Проблема была:**
```
properties.db (375 лотов)     rizalta_finance.json (3 лота)     units.json (829 строк)
      ↓                              ↓                               ↓
   Старые цены                  Только демо                    Не используется
```

**Решение — единый источник:**
```
ri.rclick.ru (сайт застройщика)
         ↓ parser_rclick.py
properties.db (369 квартир, 70 уникальных площадей)
         ↓ units_db.py
Расчёты, КП, Шахматка
```

### Парсер ri.rclick.ru
```python
# Endpoint
POST https://ri.rclick.ru/catalog/more/
data: {"id": 340, "page": N}

# Структура ответа: 8 карточек на страницу, 47 страниц = 369 квартир
# Парсит: code, building, floor, rooms, area_m2, price_rub, layout_url, completion

# Запуск
cd /opt/bot-dev && python3 services/parser_rclick.py
```

### Сервис units_db.py
```python
from services.units_db import (
    get_unique_lots,      # 70 уникальных типов по площади
    get_all_lots,         # Все 369 квартир
    get_lots_by_area,     # Фильтр по площади
    get_lots_by_budget,   # Фильтр по бюджету
    get_lot_by_area,      # Поиск по площади
    get_lot_by_code,      # Поиск по коду (с нормализацией кириллицы)
)
```

### Нормализация кодов лотов
```python
# Кириллица → латиница
table = str.maketrans({
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M",
    "Н": "H", "О": "O", "Р": "P", "С": "S", "Т": "T", "У": "Y", "Х": "X"
})
code_latin = code.translate(table)
```

### PDF генератор КП
```bash
# Установка зависимостей
apt install fonts-montserrat wkhtmltopdf -y

# Генерация
cd /opt/bot-dev && python3 services/kp_pdf_generator.py --area 22.0
cd /opt/bot-dev && python3 services/kp_pdf_generator.py --code В227

# Результат: /tmp/KP_В227_12m_24m.pdf
```

### Dev-бот
```bash
# Токен
8454364431:AAESkhkvWlo2Y8vv4iq6n1HePZ40bv8YlbY

# Username
@rizaltatestdevop_bot

# Systemd
systemctl status rizalta-bot-dev
journalctl -u rizalta-bot-dev -f

# Режим: polling (не webhook)
```

### Корпуса в БД
```
building=1 → Корпус 1 "Family" (коды В*) → block_section=2
building=2 → Корпус 2 "Business" (коды А*) → block_section=1
```

### Ключевые команды сессии
```bash
# Создать dev-окружение
bash /opt/scripts/setup_dev_bot.sh

# Проверить данные
sqlite3 /opt/bot-dev/properties.db "SELECT COUNT(*), MIN(price_rub), MAX(price_rub) FROM units"

# Тест парсера
cd /opt/bot-dev && python3 -c "from services.units_db import get_stats; print(get_stats())"

# Скачать PDF на Mac
scp root@72.56.64.91:/tmp/KP_В227_12m_24m.pdf ~/Downloads/
```

### Нюансы для следующего чата

10. **Dev-бот** — @rizaltatestdevop_bot, polling mode, /opt/bot-dev/

11. **Парсер** — parser_rclick.py обновляет properties.db из ri.rclick.ru

12. **PDF генератор** — базовая версия работает, нужен дизайн как в оригинале (логотип, шрифты)

13. **Ресурсы для PDF** — есть в /home/claude/kp_files/:
    - montserrat_*_base64.txt (шрифты)
    - logo_mono_trim_base64.txt (логотип)
    - KP_B415_12m_24m.pdf (образец дизайна)

14. **Prod не трогали** — все изменения только в /opt/bot-dev/

