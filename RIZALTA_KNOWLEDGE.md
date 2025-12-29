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

## Ключевые решения

### v2.1.2 (29.12.2025)

#### 1. Групповые заявки с кнопкой "Взять"
**Проблема:** Заявки на показ приходили админу лично
**Решение:**
- Заявка отправляется в группу RIZALTA Показы (-1003301897674)
- Кнопка "🙋 Взять заявку" — кто первый нажал, тот забрал
- Сообщение обновляется: "✅ Заявка взята — Имя Фамилия"
- Автоматически создаётся задача в секретаре специалиста

**Файлы:**
- `services/telegram.py` — send_message_inline_return_id(), edit_message_inline()
- `handlers/booking_calendar.py` — handle_take_booking()
- `app.py` — callback `book_take_`
- БД: bookings.taken_by_id, taken_by_name, group_message_id

#### 2. Стратегия Mini App
**Решение:** RealtMy (мобильное приложение) → Telegram Mini App
- Экономия: 500-800 тыс ₽
- Срок: 3-4 недели вместо 2-3 месяцев
- Архитектура: Mini App = только UI, бот = вся логика

### v2.1.1 (24.12.2025)

#### 1. Пагинация вместо noop
**Проблема:** Кнопка "... ещё N лотов" с callback_data="noop" ничего не делала
**Решение:** 
- Кеш `_search_cache[chat_id]` хранит lots, offset, back_callback
- Кнопка "📋 Показать ещё N лотов" с callback_data="kp_show_more"
- Функция handle_show_more() добавляет следующую порцию

#### 2. Часовые пояса
**Проблема:** Напоминания приходили по времени Алтая всем
**Решение:**
- Таблица `users` с полем timezone (INTEGER, default 3)
- 11 зон: UTC+2 (Калининград) — UTC+12 (Камчатка)
- reminder_loop() проверяет timezone каждого пользователя
- Кнопка смены в меню секретаря

#### 3. Фоновая задача вместо cron
**Проблема:** Cron запускал отдельный процесс каждую минуту
**Решение:**
- asyncio.create_task(reminder_loop()) в startup_event
- Работает внутри бота, нет накладных расходов
- Если бот упал — systemd перезапустит

#### 4. Поиск по бюджету ±10%
**Проблема:** "за 20 млн" показывало все от 0 до 20 млн
**Решение:**
```python
if budget:
    min_price = int(budget * 0.9)
    max_price = int(budget * 1.1)
```

#### 5. Обработка дублей кодов
**Проблема:** 70 лотов имеют одинаковые коды в обоих корпусах
**Решение:** При поиске по коду показывается inline-меню выбора корпуса

---

## Mini App — Стратегия и UI

### Архитектура Mini App + Bot
```
User → Mini App (React) → Bot API → Existing handlers
              ↓
         /api/lots endpoint (новый)
```
Bot продолжает всю логику, Mini App — только визуальный интерфейс.

### Интеграция шахматки (план)
1. Добавить `/api/lots` в app.py (30 мин)
2. React Mini App на Vercel (2-3 дня)
3. Регистрация в BotFather (5 мин)
4. Кнопка "🏠 Шахматка" в меню (10 мин)

### UI стиль Mini App (образец)
```jsx
// Цветовая схема
colors: {
  background: 'bg-slate-900',
  card: 'bg-slate-800', 
  accent: 'amber-500',
  text: 'text-white',
  muted: 'text-slate-400'
}

// Статусы лотов
status: {
  available: 'bg-emerald-500',  // Свободно
  booked: 'bg-amber-500',       // Бронь
  sold: 'bg-gray-600'           // Продано
}

// Кнопки
button: {
  primary: 'bg-amber-500 text-black font-semibold',
  secondary: 'bg-slate-700 text-white'
}
```

---

## OpenAI vs Claude — Масштабирование

### Текущее использование
- GPT-4o-mini: Intent Router + AI консультант
- Whisper: голосовой ввод
- Стоимость: ~$10-50/мес

### При 500+ пользователях
| Модель | Input $/1M | Output $/1M | Особенность |
|--------|-----------|-------------|-------------|
| GPT-4o-mini | $0.15 | $0.60 | Нет кеширования |
| Claude Haiku | $0.80 | $4.00 | Prompt caching -90% |

### Prompt Caching (ключевое)
System prompt = ~2000 токенов (база знаний)
- 20k запросов/день без кеша: $6 (OpenAI) vs $32 (Claude)
- 20k запросов/день с кешем: $6 (OpenAI) vs **$3.20** (Claude)

### Рекомендация
- **<500 users:** оставить OpenAI GPT-4o-mini
- **500+ users:** мигрировать на Claude Haiku + prompt caching
- **Экономия:** ~30% + лучшее качество ответов
- **Whisper:** оставить (у Claude нет аналога)

---

## Частые команды
```bash
# Проверка синтаксиса
cd /opt/bot && source venv/bin/activate
python3 -c "import app; print('OK')"

# Проверка различий DEV/PROD
diff /opt/bot-dev/app.py /opt/bot/app.py | head -30

# Посмотреть структуру БД
sqlite3 /opt/bot/secretary.db ".schema"
sqlite3 /opt/bot/properties.db "SELECT COUNT(*) FROM units"
sqlite3 /opt/bot/properties.db ".schema bookings"

# Статистика мониторинга
sqlite3 /opt/bot/monitoring.db "SELECT COUNT(*) FROM stats WHERE timestamp LIKE '$(date +%Y-%m-%d)%'"

# Grep по коду
grep -rn "handle_take_booking" handlers/
grep -n "def reminder_loop" run_polling.py

# Статус сервисов
systemctl status rizalta-bot
systemctl status rizalta-bot-dev

# Git коммит
cd /opt/bot && git add -A && git commit -m "описание" && git push
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
pip install -r requirements.txt
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

### Проверка статистики
```bash
sqlite3 /opt/bot/monitoring.db "SELECT COUNT(*) FROM stats"
sqlite3 /opt/bot/monitoring.db "SELECT * FROM stats ORDER BY id DESC LIMIT 10"
```

---

## Контакты

- **Сервер:** 72.56.64.91:2222
- **PROD бот:** @RealtMeAI_bot
- **DEV бот:** @rizaltatestdevop_bot
- **Admin chat_id:** 512319063
- **Группа показов:** -1003301897674
