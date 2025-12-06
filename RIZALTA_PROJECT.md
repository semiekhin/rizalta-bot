# RIZALTA BOT — Полная документация

> **Для Claude:** Если пользователь пишет "обнови текущую задачу для нового чата" — обнови файл `RIZALTA_CURRENT_TASK.md` с итогами работы, текущим состоянием и следующими задачами, затем дай пользователю обновлённый файл для загрузки в GitHub.

---

## 🎯 Что это за бот

AI-консультант для инвестиционного проекта **RIZALTA Resort Belokurikha** (Белокуриха, Алтай).

**Telegram:** @rizaboris_bot

### Возможности:

- 🤖 AI-консультант на GPT-4o-mini с Function Calling
- 📋 Коммерческие предложения (КП) — поиск по площади/бюджету, отправка JPG
- 💰 Расчёт доходности и ROI по гостиничный номерам
- 💳 Калькулятор рассрочки и ипотеки
- 📊 Подбор инвестиционного портфеля под бюджет
- 🔥 Запись на онлайн-показ
- 📧 Email и Telegram уведомления менеджерам
- 📎 Отправка планировок (PDF)
- 📌 Фиксация клиента (внешняя ссылка)
- 🏠 Шахматка (внешняя ссылка)
- 🎬 Медиа-материалы (презентации, видео)

---

## 🖥 Сервер

| Параметр | Значение |
|----------|----------|
| IP | `72.56.64.91` |
| OS | Ubuntu 24 |
| Путь к боту | `/opt/bot/` |
| Порт | 8000 |
| Python | 3.10+ (venv) |

### SSH доступ:
```bash
ssh root@72.56.64.91
```

---

## 📁 Структура проекта

```
/opt/bot/
├── app.py                    # Главный файл (FastAPI + webhook)
├── .env                      # Секреты (НЕ в git!)
├── .env.example              # Шаблон секретов
├── properties.db             # SQLite база (375 гостиничных номеров)
├── requirements.txt          # Python зависимости
│
├── config/
│   ├── settings.py           # Настройки, пути, константы
│   └── instructions.txt      # Системный промпт для AI
│
├── handlers/
│   ├── __init__.py
│   ├── ai_chat.py            # AI-консультант + Function Calling
│   ├── booking.py            # Запись на показ
│   ├── calc_dynamic.py       # Динамические расчёты ROI/рассрочка
│   ├── docs.py               # Договоры (ДДУ, аренда)
│   ├── kp.py                 # Коммерческие предложения
│   ├── media.py              # Медиа-материалы (NEW v1.4)
│   ├── menu.py               # Меню и навигация
│   └── units.py              # Расчёты ROI, рассрочка
│
├── services/
│   ├── __init__.py
│   ├── ai_chat.py            # OpenAI клиент
│   ├── calculations.py       # Финансовые расчёты (1195 строк)
│   ├── data_loader.py        # Загрузка JSON/TXT
│   ├── kp_search.py          # Поиск КП файлов
│   ├── notifications.py      # Email уведомления
│   └── telegram.py           # Telegram API (send_photo, send_media_group)
│
├── models/
│   └── state.py              # Состояния диалогов
│
├── data/
│   ├── rizalta_finance.json  # Финансовые сценарии
│   ├── units.json            # 69 лотов
│   ├── rizalta_knowledge_base.txt
│   ├── text_why_rizalta.md
│   ├── text_why_belokuricha.md
│   └── text_architect.md
│
├── kp_all/                   # 69 JPG коммерческих предложений
│   ├── kp_24.5m_business_А209.jpg
│   ├── kp_113.3m_family_В904.jpg
│   └── ...
│
├── docs/                     # Документы (66 MB)
│   ├── ddu.pdf               # Договор ДДУ
│   └── arenda.pdf            # Договор аренды
│
├── media/                    # Медиа-материалы (NEW v1.4)
│   └── presentation_rizalta.pdf
│
└── kp_generator.py           # Генератор HTML→JPG КП
```

---

## 📱 Главное меню (v1.4.0)

```
┌─────────────────┬─────────────────┐
│  📖 О проекте   │   💰 Расчёты    │
├─────────────────┼─────────────────┤
│  📋 КП (JPG)    │  📄 Договоры    │
├─────────────────┼─────────────────┤
│📌 Фиксация      │  🏠 Шахматка    │
│   клиента       │                 │
├─────────────────┴─────────────────┤
│           🎬 Медиа                │
├───────────────────────────────────┤
│  🔥 Записаться на онлайн-показ    │
└───────────────────────────────────┘
```

### Внешние ссылки:
- 📌 Фиксация клиента → https://ri.rclick.ru/notice/
- 🏠 Шахматка → https://ri.rclick.ru/

---

## 🔐 Переменные окружения (.env)

```env
# Telegram
TELEGRAM_BOT_TOKEN=8343378629:AAHHacgXmIVhShhtPtdEooKEkV34ZD1t59s

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=800

# Email уведомления
MANAGER_EMAIL=89181011091s@mail.ru,dreaming2015@mail.ru
BOT_EMAIL=rizalta-bot@mail.ru
SMTP_HOST=smtp.mail.ru
SMTP_PORT=587
SMTP_USER=rizalta-bot@mail.ru
SMTP_PASSWORD=...
```

**ВАЖНО:** `.env` не хранится в git! Только `.env.example` как шаблон.

---

## 🚀 Запуск и управление

### Проверить статус:
```bash
ps aux | grep uvicorn
```

### Запустить:
```bash
cd /opt/bot
nohup /opt/bot/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 > /var/log/rizalta-bot.log 2>&1 &
```

### Остановить:
```bash
pkill -9 -f "uvicorn.*8000"
```

### Посмотреть логи:
```bash
tail -50 /var/log/rizalta-bot.log
```

### Перезапустить:
```bash
pkill -9 -f "uvicorn.*8000"
sleep 2
cd /opt/bot
nohup /opt/bot/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 > /var/log/rizalta-bot.log 2>&1 &
```

### Если порт занят:
```bash
fuser -k 8000/tcp
```

---

## 📦 Деплой новой версии

### 1. Загрузить архив на сервер:
```bash
scp rizalta_vX.X.tar.gz root@72.56.64.91:/tmp/
```

### 2. На сервере:
```bash
cd /opt/bot

# Остановить
pkill -9 -f "uvicorn.*8000"

# Бэкап (опционально)
tar -czvf /tmp/backup_$(date +%Y%m%d).tar.gz --exclude='venv' --exclude='kp_all' --exclude='docs' --exclude='media' .

# Распаковать (без перезаписи .env)
tar -xzf /tmp/rizalta_vX.X.tar.gz --exclude='.env'

# Запустить
nohup /opt/bot/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 > /var/log/rizalta-bot.log 2>&1 &
```

---

## 🗄 База данных

**Файл:** `/opt/bot/properties.db` (SQLite)

**Таблица `units`:**
- 375 гостиничных номеров
- 2 блок-секции (корпус 1 = B, корпус 2 = A)

**Поля:**
- `code` — код лота (А209, В415)
- `area_m2` — площадь
- `price_rub` — цена
- `floor` — этаж
- `block_section` — корпус (1 или 2)

### Полезные запросы:
```bash
cd /opt/bot
sqlite3 properties.db "SELECT COUNT(*) FROM units;"
sqlite3 properties.db "SELECT * FROM units LIMIT 5;"
sqlite3 properties.db "SELECT code, area_m2, price_rub FROM units WHERE area_m2 BETWEEN 22 AND 25;"
```

---

## 📋 Фича: Коммерческие предложения (КП)

### UX Flow:

```
📋 КП (JPG)
    ↓
├── 📐 По площади
│   ├── 22-30 м² | 31-40 м² | 41-50 м²
│   └── 51-70 м² | 71-90 м² | 90+ м²
│       ↓
│   [А101 — 24.4 м² — 15.2 млн]  ← кнопка
│   [А209 — 24.5 м² — 15.3 млн]  ← кнопка
│   [📤 Отправить все (4 шт.)]
│
└── 💰 По бюджету
    ├── до 15 млн | 15-18 млн | 18-22 млн
    └── 22-26 млн | 26-30 млн | 30+ млн
```

### Файлы:
- `handlers/kp.py` — обработчик
- `services/kp_search.py` — поиск JPG
- `services/telegram.py` — `send_photo()`, `send_media_group()`

### JPG файлы:
```
/opt/bot/kp_all/
├── kp_24.5m_business_А209.jpg
├── kp_113.3m_family_В904.jpg
└── ... (69 файлов)
```

Паттерн имени: `kp_{площадь}m_{тип}_{код}.jpg`

---

## 🎬 Фича: Медиа-материалы (NEW v1.4)

### UX Flow:
```
🎬 Медиа
    ↓
├── 📊 Презентация проекта → PDF (25 MB)
└── 🔙 Назад в меню
```

### Файлы:
- `handlers/media.py` — обработчик
- `/opt/bot/media/presentation_rizalta.pdf` — презентация

---

## 🔧 AI Function Calling

**Файл:** `services/ai_chat.py`

**Доступные функции:**
- `build_portfolio` — подбор портфеля под бюджет
- `calculate_roi` — расчёт доходности
- `show_installment` — рассрочка/ипотека
- `book_showing` — запись на показ
- `show_layouts` — планировки
- `get_commercial_proposal` — КП

---

## 🔑 Ключевой принцип: Площадь как уникальный ключ

**Проблема:** В базе есть дубликаты кодов лотов из разных корпусов:
- А204 (корпус 1) — 27.3 м²
- А204 (корпус 2) — 45.5 м²

**Решение:** Площадь уникальна (69 уникальных значений) → используем как ключ.

**Связь данных:**
```
JPG файл: kp_24.7m_family_В201.jpg
            ↓
      площадь = 24.7
            ↓
    цена из базы по площади
            ↓
Кнопка: "В201 — 24.7 м² — 15.4 млн"
            ↓
Callback: kp_send_247 (площадь × 10)
            ↓
Находим файл и расчёт по площади
```

**Callback форматы (только площадь):**
- `kp_send_247` — КП для 24.7 м²
- `calc_roi_lot_247` — расчёт ROI для 24.7 м²
- `calc_finance_lot_247` — рассрочка для 24.7 м²

---

## 📄 Фича: Договоры

**Файлы:**
- `/opt/bot/docs/ddu.pdf` — Договор долевого участия
- `/opt/bot/docs/arenda.pdf` — Договор аренды с Зонт Хотел Групп

**Обработчик:** `handlers/docs.py`

**Меню:**
```
📄 Договоры
├── 📑 Договор ДДУ
├── 📑 Договор аренды
└── 📑 Оба документа
```

---

## 📊 Данные о лотах

| Источник | Количество | Назначение |
|----------|------------|------------|
| `kp_all/*.jpg` | 69 файлов | Источник истины |
| `units.json` | 69 записей | Данные для AI |
| `rizalta_finance.json` | 69 в units[] | Финансовая модель |
| `properties.db` | ~375 записей | Полная база (избыточна) |

**Минимальный лот:** В215 — 22.0 м² — 13 695 000 ₽

---

## 🔗 Ссылки

- **GitHub:** https://github.com/semiekhin/rizalta-bot
- **Сервер:** 72.56.64.91
- **Telegram Bot:** @rizaboris_bot
- **Фиксация клиента:** https://ri.rclick.ru/notice/
- **Шахматка:** https://ri.rclick.ru/

---

## 📝 История изменений

### v1.4.0 (06.12.2024)
- Обновлено главное меню — кнопки по 2 в ряд
- Добавлена кнопка "📌 Фиксация клиента" (внешняя ссылка)
- Добавлена кнопка "🏠 Шахматка" (внешняя ссылка)
- Добавлен раздел "🎬 Медиа" с презентацией
- Новый handler: `handlers/media.py`
- Исправлен баг с дубликатом `send_document` в telegram.py
- Обсуждена интеграция с Cal.com (в планах)

### v1.3.2 (05.12.2024)
- Исправлена проблема дубликатов лотов (А204, В904, А202)
- Переход на площадь как единственный ключ
- Сгенерирован units.json из 69 КП файлов
- AI использует актуальные данные (69 лотов)
- Добавлены договоры (ДДУ, аренда)
- Обновлены диапазоны площадей (51-70, 71-90, 90+)
- Запуск через uvicorn вместо python app.py
- Замена "апартаменты" → "гостиничные номера"

### v1.2 (04.12.2024)
- Добавлена фича КП с кнопками (по площади / по бюджету)
- Inline-кнопки для выбора конкретного лота
- Кнопка "Отправить все" для альбома

### v1.1 (04.12.2024)
- Первая версия КП через текстовый ввод
- Добавлены `send_photo()`, `send_media_group()`

### v1.0 (ноябрь 2024)
- Базовый функционал: AI-консультант, ROI, рассрочка, запись на показ
