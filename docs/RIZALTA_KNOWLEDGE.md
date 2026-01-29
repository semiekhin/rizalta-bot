# RIZALTA_KNOWLEDGE.md

## 🧠 Важные нюансы проекта

### Архитектура GPT Intent Router (v2.0)

**Как работает:**
```
Сообщение (голос/текст) → GPT Intent Router → Handler
```

**Где живёт:**
- `services/intent_router.py` — метазнания + классификатор
- Функция `classify_intent(text)` → `{"intent": str, "params": dict, "confidence": float}`

**15+ intent'ов:**
- `get_kp`, `calculate_roi`, `show_installment`, `compare_deposit`
- `open_fixation`, `open_shahmatka`, `book_showing`
- `send_documents`, `send_presentation`, `show_media`
- `create_task`, `show_schedule` (секретарь)
- `show_news`, `chat`, `main_menu`

**Правила приоритета:**
- "открой шахматку" → `open_shahmatka` (НЕ `create_task`!)
- "завтра позвонить Иванову" → `create_task`
- "напомню" (ошибка Whisper) → "напомни" → `create_task`

### AI-Секретарь

**Файлы:**
- `handlers/secretary.py` — UI, навигация, callback'и
- `services/secretary_ai.py` — GPT парсинг задач
- `services/secretary_db.py` — SQLite операции

**База данных:**
```
Dev:  /opt/bot-dev/secretary.db
Prod: /opt/bot/secretary.db
```

**Таблица tasks:**
```sql
id, user_id, task_text, due_date, due_time, client_name,
priority, status, description, reminder_sent, created_at, completed_at
```

**⚠️ Напоминания НЕ работают** — нужен APScheduler

### Рассрочка (v2.0.1)

**Текущие проценты (dev):**
| ПВ | Удорожание | Срок |
|----|------------|------|
| 30% | +9% | 18 мес |
| 40% | +7% | 18 мес |
| 50% | +4% | 18 мес |

**Старые проценты (prod):**
| ПВ | Удорожание | Срок |
|----|------------|------|
| 30% | +12% | 24 мес |
| 40% | +9% | 24 мес |
| 50% | +6% | 24 мес |

**Файлы расчётов:**
- `services/kp_pdf_generator.py` — PDF генерация КП
- `services/calc_universal.py` — расчёты для UI "Расчёты"→"Рассрочка"
- `services/calculations.py` — общие финансовые расчёты

### Два репозитория

| Репо | Путь | Бот | Режим |
|------|------|-----|-------|
| rizalta-bot-dev | /opt/bot-dev | @rizaltatestdevop_bot | polling |
| rizalta-bot | /opt/bot | @RealtMeAI_bot | webhook |

**Правило:** Всегда тестируем в dev, потом деплоим в prod.

---

## 🔧 Частые команды

### Сервер
```bash
ssh -p 2222 root@72.56.64.91
```

### Dev
```bash
cd /opt/bot-dev
source venv/bin/activate
systemctl restart rizalta-bot-dev
journalctl -u rizalta-bot-dev -f
journalctl -u rizalta-bot-dev -f | grep -E "\[INTENT\]|\[ROUTER\]"
```

### Prod
```bash
cd /opt/bot
source venv/bin/activate
systemctl restart rizalta-bot
journalctl -u rizalta-bot -f
```

### Git
```bash
cd /opt/bot-dev
git add -A && git commit -m "vX.X.X: описание" && git push

cd /opt/bot
git add -A && git commit -m "vX.X.X: описание" && git push
```

### Тест КП
```bash
cd /opt/bot-dev
source venv/bin/activate
python3 -c "from services.kp_pdf_generator import generate_kp_pdf; print(generate_kp_pdf(code='В101', include_18m=True, output_dir='/tmp'))"
```

### SQLite секретарь
```bash
sqlite3 /opt/bot/secretary.db "SELECT * FROM tasks ORDER BY id DESC LIMIT 5;"
```

---

## 🐛 Решённые проблемы

### 1. Голос создавал задачу вместо действия
**Проблема:** "открой шахматку" → создавалась задача
**Причина:** Режим секретаря перехватывал все сообщения
**Решение:** GPT Intent Router с правилами приоритета

### 2. ImportError при деплое в prod
**Проблема:** `cannot import name 'handle_secretary_menu'`
**Причина:** Не скопирован `handlers/__init__.py`
**Решение:** Копировать ВСЕ изменённые файлы

### 3. TypeError: unexpected keyword argument 'include_24m'
**Проблема:** Параметр переименован, но handlers не обновлены
**Причина:** Частичное обновление файлов
**Решение:** 
```bash
sed -i 's/include_24m/include_18m/g' handlers/kp.py handlers/domoplaner.py app.py
```

### 4. ModuleNotFoundError: No module named 'requests'
**Проблема:** Неправильный venv активирован
**Решение:** `source /opt/bot-dev/venv/bin/activate`

---

## 📋 Чеклист деплоя

1. [ ] Тест в dev (@rizaltatestdevop_bot)
2. [ ] `git add -A && git commit && git push` (dev)
3. [ ] Копировать файлы в /opt/bot
4. [ ] `systemctl restart rizalta-bot`
5. [ ] Проверить логи: `journalctl -u rizalta-bot -f`
6. [ ] Тест в prod (@RealtMeAI_bot)
7. [ ] `git add -A && git commit && git push` (prod)

---

## 🔮 Архитектурные решения

### Почему GPT вместо regex
- Regex не справлялся с естественным языком
- Голосовые команды содержат ошибки Whisper
- Режим секретаря создавал конфликты
- GPT понимает контекст и намерение

### Почему SQLite для секретаря
- Простота, достаточно для текущей нагрузки
- Отдельная база от properties.db
- Легко бэкапить

### Почему два репозитория
- Безопасность: prod никогда не ломается экспериментами
- Разные токены ботов
- Разные режимы (webhook vs polling)

---

## Добавлено 10.01.2026

### ⚠️ КРИТИЧЕСКИ ВАЖНО: PROD vs DEV

**ПРАВИЛО:** Все изменения ТОЛЬКО в DEV → тестирование → деплой в PROD

**Workflow:**
1. Редактировать файлы в `/opt/bot-dev/`
2. Перезапустить: `systemctl restart rizalta-bot-dev`
3. Протестировать в @rizaltatestdevop_bot
4. Копировать в PROD: `cp /opt/bot-dev/file /opt/bot/file`
5. Проверить синтаксис: `python3 -c "import app; print('OK')"`
6. Перезапустить PROD: `systemctl restart rizalta-bot`
7. Коммит в оба репо

### Mini App: почему fetch() а не tg.sendData()

**Проблема:** `tg.sendData()` молча не работает
**Причина:** `sendData()` работает ТОЛЬКО с KeyboardButton, а Mini App открывается через InlineKeyboardButton
**Решение:** Использовать `fetch()` через Vercel proxy

### Mini App: разделение PROD/DEV
```javascript
// App.jsx
const API_PATH = new URLSearchParams(window.location.search).get('env') === 'dev' 
  ? '/api-dev' 
  : '/api';
```

- PROD бот открывает: `https://rizalta-miniapp.vercel.app`
- DEV бот открывает: `https://rizalta-miniapp.vercel.app?env=dev`

### Дублирование кода рассрочки (технический долг)

Формулы рассрочки в 3 файлах — при изменении менять ВСЕ:
1. `kp_generator.py` — HTML для PDF
2. `services/kp_pdf_generator.py` — PDF генератор
3. `services/calc_universal.py` — текстовые сообщения

### Условия рассрочки (актуальные на 09.01.2026)

**12 месяцев (без удорожания):**
- 30% ПВ → 12 равных платежей
- 40% ПВ → 11×200К + 12-й остаток
- 50% ПВ → 11×100К + 12-й остаток

**18 месяцев (с удорожанием):**
- 30% ПВ +9% → 18 равных платежей
- 40% ПВ +7% → 8×250К + 9-й (10%) + 8×250К + 18-й остаток
- 50% ПВ +4% → 8×150К + 9-й (10%) + 8×150К + 18-й остаток

### PROJECT MEMORY SYSTEM v1.0 (внедрено 10.01.2026)

**Структура документации:**
```
/opt/bot-dev/docs/
├── RIZALTA_CONTEXT.md      # Статика (~500 токенов) — ВСЕГДА в чат
├── RIZALTA_CURRENT.md      # Динамика (~500 токенов) — ВСЕГДА в чат
├── RIZALTA_ARCHITECTURE.md # Детали — по запросу
├── RIZALTA_KNOWLEDGE.md    # База знаний — по запросу
└── RIZALTA_TASKS.md        # Бэклог — по запросу
```

**Экономия:** ~1000 токенов вместо ~20000 на старте чата

**Завершение сессии:**
1. Обновить docs/*.md в DEV
2. Скопировать в PROD
3. Коммит оба репо
4. Выдать блок для нового чата

---

## Добавлено 14.01.2026

### Custom Installment (индивидуальные условия рассрочки)

**Список апартаментов:**
```python
CUSTOM_INSTALLMENT_UNITS = ['В615', 'В527', 'В517', 'В617', 'В525', 'В625', 'А101']
```

**Где используется:**
- `services/kp_pdf_generator.py` — PDF показывает 2 колонки (только 50% ПВ)
- `handlers/kp.py` — скрывается кнопка "КП с рассрочкой 12+18 мес"

**Как добавить новый апартамент:**
1. Открыть `/opt/bot-dev/services/kp_pdf_generator.py`
2. Найти `CUSTOM_INSTALLMENT_UNITS = [...]`
3. Добавить код апартамента в список
4. Перезапустить DEV, протестировать
5. Скопировать в PROD, перезапустить

**Пример:**
```bash
# Добавить В700:
sed -i "s/CUSTOM_INSTALLMENT_UNITS = \[/CUSTOM_INSTALLMENT_UNITS = ['В700', /" /opt/bot-dev/services/kp_pdf_generator.py
```

---

## Добавлено 27.01.2026

### Изменение формата callback — ВАЖНЫЙ УРОК

**Проблема:** "Сравнить с депозитом" показывал цену 1000₽ вместо 40 млн

**Причина:** Формат callback изменился, но парсер не обновили
```python
# Было:    compare_lot_{code}_{price}
# Стало:   compare_lot_{code}_{building}_{price}
# Парсер брал parts[3] как цену, а это был building (1)
```

**Урок:** При изменении формата callback — искать ВСЕ места:
```bash
grep -rn "compare_lot_" /opt/bot-dev/
```
И обновлять как формирование, так и парсинг.

### ADMIN_IDS — список админов

**Было:** `ADMIN_ID = 512319063` (один админ)
**Стало:** `ADMIN_IDS = [512319063, 8000703751]` (список)

**Файл:** `app.py` (строка ~1507)

**Проверка:** `if chat_id in ADMIN_IDS:`

### Custom Installment — текст "Варианты оплаты"

**Файл:** `services/calc_universal.py`

Теперь для лотов из CUSTOM_INSTALLMENT_UNITS текст "Варианты оплаты" показывает только 12 мес ПВ 50% (как и КП).

**Добавлен импорт:**
```python
from services.kp_pdf_generator import CUSTOM_INSTALLMENT_UNITS
```

**В функции format_installment_text():**
```python
if calc['code'] in CUSTOM_INSTALLMENT_UNITS:
    # Показать только 12 мес ПВ 50%
```

### Watchdog — убран rizalta-dev-api

DEV работает в polling режиме, uvicorn на порту 8002 не нужен.

**Отключено:**
```bash
systemctl stop rizalta-dev-api
systemctl disable rizalta-dev-api
```

**Убрано из watchdog config.py:**
- rizalta-dev-api из SERVICES
- dev из HEALTH_ENDPOINTS
- rizalta-dev-api из RECOVERY_COMMANDS

### Дублирование сообщений в DEV

**Причина:** Два процесса — polling + uvicorn (оба получают сообщения)

**Диагностика:**
```bash
ps aux | grep bot-dev | grep -v grep
```

**Решение:** Убить лишний процесс или отключить сервис

---

## Добавлено 29.01.2026

### ⚠️ Клон сервера (Амстердам)

**Проблема:** Клон сервера работал параллельно с основным, перехватывая часть запросов через Cloudflare Tunnel.

**Симптомы:**
- Двойные ежедневные отчёты
- Whitelist "добавлен", но пользователь не видит
- Странное поведение бронирований

**Решение:**
```bash
# На клоне (6492347-hk015312)
systemctl stop rizalta-bot rizalta-bot-dev rizalta-watchdog cloudflare-rizalta rizalta-dev-tunnel rizalta-dev-api
systemctl disable rizalta-bot rizalta-bot-dev rizalta-watchdog cloudflare-rizalta rizalta-dev-tunnel rizalta-dev-api
```

**Статус:** RIZALTA сервисы на клоне отключены (disabled), Sofia работает.

### corp3_units.json в .gitignore

**Проблема:** Файл отслеживался git → при любых git операциях локальные изменения (скрытые лоты) затирались.

**Решение:**
```bash
echo "data/corp3_units.json" >> .gitignore
git rm --cached data/corp3_units.json
git commit -m "fix: исключить corp3_units.json из git"
```

### Относительные пути для БД и JSON

**Проблема:** Жёсткие пути `/opt/bot-dev/...` в коде приводили к тому, что PROD бот работал с DEV базой.

**Было:**
```python
db_path = "/opt/bot-dev/properties.db"
json_path = "/opt/bot-dev/data/corp3_units.json"
```

**Стало:**
```python
db_path = "properties.db"
json_path = "data/corp3_units.json"
```

Работает благодаря `WorkingDirectory` в systemd сервисе.
