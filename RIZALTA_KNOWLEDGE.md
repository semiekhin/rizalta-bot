# RIZALTA BOT — База знаний

## Быстрый старт
```bash
# SSH на сервер
ssh -p 2222 root@72.56.64.91

# Пути
cd /opt/bot        # PROD
cd /opt/bot-dev    # DEV

# Логи
journalctl -u rizalta-bot -f        # PROD
journalctl -u rizalta-bot-dev -f    # DEV

# Перезапуск
systemctl restart rizalta-bot       # PROD
systemctl restart rizalta-bot-dev   # DEV
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

**PROD:** webhook через uvicorn (app.py)
**DEV:** polling через run_polling.py

---

## Ключевые решения (24.12.2025)

### 1. Пагинация вместо noop
**Проблема:** Кнопка "... ещё N лотов" с callback_data="noop" ничего не делала
**Решение:** 
- Кеш `_search_cache[chat_id]` хранит lots, offset, back_callback
- Кнопка "📋 Показать ещё N лотов" с callback_data="kp_show_more"
- Функция handle_show_more() добавляет следующую порцию

### 2. Часовые пояса
**Проблема:** Напоминания приходили по времени Алтая всем
**Решение:**
- Таблица `users` с полем timezone (INTEGER, default 3)
- 11 зон: UTC+2 (Калининград) — UTC+12 (Камчатка)
- reminder_loop() проверяет timezone каждого пользователя
- Кнопка смены в меню секретаря

### 3. Фоновая задача вместо cron
**Проблема:** Cron запускал отдельный процесс каждую минуту
**Решение:**
- asyncio.create_task(reminder_loop()) в startup_event
- Работает внутри бота, нет накладных расходов
- Если бот упал — systemd перезапустит

### 4. Поиск по бюджету ±10%
**Проблема:** "за 20 млн" показывало все от 0 до 20 млн
**Решение:**
```python
if budget:
    min_price = int(budget * 0.9)
    max_price = int(budget * 1.1)
```

### 5. Обработка дублей кодов
**Проблема:** 70 лотов имеют одинаковые коды в обоих корпусах
**Решение:** При поиске по коду показывается inline-меню выбора корпуса

---

## Частые команды
```bash
# Проверка синтаксиса
python3 -c "import app; print('OK')"

# Проверка различий DEV/PROD
diff /opt/bot-dev/app.py /opt/bot/app.py | head -30

# Посмотреть структуру БД
sqlite3 /opt/bot/secretary.db ".schema"
sqlite3 /opt/bot/properties.db "SELECT COUNT(*) FROM units"

# Тест отправки сообщения
python3 -c "
import asyncio
from services.monitoring import send_daily_report
asyncio.run(send_daily_report())
"

# Grep по коду
grep -rn "handle_kp_floor" handlers/
grep -n "def reminder_loop" run_polling.py

# Cron задачи
crontab -l

# Статус сервисов
systemctl status rizalta-bot
systemctl status rizalta-bot-dev
```

---

## Типичные ошибки и решения

### 1. NameError: name 'asyncio' is not defined
**Причина:** Забыли import asyncio в app.py
**Решение:** `sed -i '1i import asyncio' /opt/bot/app.py`

### 2. ModuleNotFoundError: No module named 'psutil'
**Причина:** Пакет установлен в другой venv
**Решение:** 
```bash
/opt/bot/venv/bin/pip install psutil
/opt/bot-dev/venv/bin/pip install psutil
```

### 3. ImportError: cannot import name 'handle_xxx'
**Причина:** Функция не экспортирована в handlers/__init__.py
**Решение:** Добавить в __init__.py

### 4. IndentationError после sed
**Причина:** sed добавил строку с неправильным отступом
**Решение:** Проверить `sed -n 'N,Mp' file.py` и исправить вручную

### 5. DEV venv ссылается на PROD
**Причина:** venv создан неправильно
**Решение:**
```bash
cd /opt/bot-dev
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # или нужные пакеты
```

---

## Деплой процедура

1. **Изменения в DEV**
2. **Тест в DEV боте** (@rizaltatestdevop_bot)
3. **Коммит DEV:**
```bash
   cd /opt/bot-dev
   git add -A
   git commit -m "описание"
   git push origin main
```
4. **Копирование в PROD:**
```bash
   cp /opt/bot-dev/file.py /opt/bot/
```
5. **Исправление путей:**
```bash
   sed -i 's|/opt/bot-dev|/opt/bot|g' /opt/bot/file.py
```
6. **Проверка + рестарт:**
```bash
   cd /opt/bot
   python3 -c "import app; print('OK')"
   systemctl restart rizalta-bot
```
7. **Коммит PROD:**
```bash
   cd /opt/bot
   git add -A
   git commit -m "описание"
   git push origin main
```

---

## Мониторинг

### Пороги алертов
- >30 запросов/мин → уведомление
- RAM >50% → уведомление
- Ежедневный отчёт в 20:00

### Логирование
```python
from services.monitoring import log_request
log_request(chat_id, "message")  # В webhook handler
```

### Проверка статистики
```bash
sqlite3 /opt/bot/monitoring.db "SELECT COUNT(*) FROM stats"
sqlite3 /opt/bot/monitoring.db "SELECT * FROM stats ORDER BY id DESC LIMIT 10"
```

---

## Масштабирование (TODO)

### До 500 users — текущий сервер ОК

### 500-2000 users
- Увеличить сервер: 4 CPU, 8 GB RAM
- Redis для кеширования GPT ответов
- ~3000-5000 ₽/мес

### 2000-10000 users
- PostgreSQL вместо SQLite
- Очередь задач (Celery) для PDF
- ~10000-15000 ₽/мес

### Узкое место: OpenAI API
- Кеширование частых ответов
- Batch API для несрочных запросов
- Несколько API ключей

---

## Контакты

- **Сервер:** 72.56.64.91:2222
- **PROD бот:** @RealtMeAI_bot
- **DEV бот:** @rizaltatestdevop_bot
- **Admin chat_id:** 512319063
