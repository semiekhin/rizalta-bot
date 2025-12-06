# RIZALTA BOT — Инструкция для Claude

> **Этот файл читает Claude в начале нового чата**

---

## 🚀 НАЧАЛО НОВОГО ЧАТА

Пользователь пишет: **"продолжаем RIZALTA BOT"** и прикрепляет ссылки.

**Claude должен:**
1. Пройти по всем ссылкам через web_fetch
2. Прочитать документацию и код
3. Спросить: "Какую задачу делаем сегодня?"

---

## 🔗 ССЫЛКИ ДЛЯ НАЧАЛА ЧАТА (копировать целиком)

```
продолжаем RIZALTA BOT

GitHub репо:
https://github.com/semiekhin/rizalta-bot

Документация:
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/RIZALTA_PROJECT.md
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/RIZALTA_CURRENT_TASK.md
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/RIZALTA_KNOWLEDGE.md

Главный файл:
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/app.py

Handlers:
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/__init__.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/kp.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/calc_dynamic.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/docs.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/media.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/ai_chat.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/menu.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/booking.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/handlers/units.py

Services:
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/services/__init__.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/services/kp_search.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/services/ai_chat.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/services/telegram.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/services/calculations.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/services/data_loader.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/services/notifications.py

Config & Models:
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/config/settings.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/models/state.py

Data:
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/data/units.json
https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/data/rizalta_finance.json
```

---

## 📝 КОНЕЦ ЧАТА

Пользователь пишет: **"обнови текущую задачу для нового чата"**

**Claude должен:**

1. Обновить `RIZALTA_CURRENT_TASK.md`:
   - Допиши в "Что сделано в этом чате"
   - Обнови "Текущий статус"
   - Обнови "Следующие задачи"
   - Добавь новые баги если есть

2. Если были изменения в коде — обновить `RIZALTA_PROJECT.md`:
   - Добавь в "История изменений"
   - Обнови структуру если изменилась

3. Дать пользователю скачать обновлённые файлы

4. Напомнить команды для git push

---

## 🔑 КЛЮЧЕВАЯ ИНФОРМАЦИЯ

| Параметр | Значение |
|----------|----------|
| GitHub | https://github.com/semiekhin/rizalta-bot |
| Сервер | 72.56.64.91 |
| Путь на сервере | /opt/bot/ |
| Telegram бот | @rizaboris_bot |
| Порт | 8000 |
| Python | venv в /opt/bot/venv/ |

---

## 🛠 ЧАСТЫЕ КОМАНДЫ НА СЕРВЕРЕ

### SSH подключение:
```bash
ssh root@72.56.64.91
```

### Перезапуск бота:
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

### Посмотреть логи:
```bash
tail -50 /var/log/rizalta-bot.log
```

---

## ⚠️ ВАЖНЫЕ НЮАНСЫ

1. **dotenv** — `load_dotenv()` должен быть в начале `config/settings.py`

2. **Архивы не всегда обновляют файлы** — для критичных изменений использовать `cat > file << 'EOF'`

3. **База данных** — `properties.db` содержит 375 гостиничных номеров, 69 из них имеют готовые КП (JPG)

4. **КП файлы** — лежат в `/opt/bot/kp_all/`, паттерн: `kp_{площадь}m_{тип}_{код}.jpg`

5. **.env не в git** — секреты только на сервере

6. **Медиа файлы** — лежат в `/opt/bot/media/`

---

## 📂 СТРУКТУРА ПРОЕКТА

```
/opt/bot/
├── app.py                    # FastAPI + webhook роутер
├── .env                      # Секреты (НЕ в git!)
├── properties.db             # SQLite: 375 гостиничных номеров
│
├── config/
│   ├── settings.py           # Настройки + load_dotenv()
│   └── instructions.txt      # Системный промпт AI
│
├── handlers/
│   ├── kp.py                 # Коммерческие предложения
│   ├── ai_chat.py            # AI + Function Calling
│   ├── menu.py               # Меню и навигация
│   ├── booking.py            # Запись на показ
│   ├── docs.py               # Договоры
│   ├── media.py              # Медиа-материалы (NEW)
│   ├── calc_dynamic.py       # Расчёты ROI/рассрочка
│   └── units.py              # ROI, рассрочка
│
├── services/
│   ├── kp_search.py          # Поиск JPG файлов
│   ├── ai_chat.py            # OpenAI клиент
│   ├── telegram.py           # Telegram API
│   ├── calculations.py       # Финансы (1195 строк)
│   ├── data_loader.py        # Загрузка JSON
│   └── notifications.py      # Email
│
├── models/
│   └── state.py              # Состояния диалогов
│
├── data/                     # JSON конфиги
├── kp_all/                   # 69 JPG (не в git)
├── docs/                     # Документы (не в git)
└── media/                    # Медиа-материалы (NEW, не в git)
    └── presentation_rizalta.pdf
```

---

## 🆕 Версия v1.4.0 (06.12.2024)

### Главное меню
```
┌─────────────────┬─────────────────┐
│  📖 О проекте   │   💰 Расчёты    │
├─────────────────┼─────────────────┤
│  📋 КП (JPG)    │  📄 Договоры    │
├─────────────────┼─────────────────┤
│📌 Фиксация      │  🏠 Шахматка    │
├─────────────────┴─────────────────┤
│           🎬 Медиа                │
├───────────────────────────────────┤
│  🔥 Записаться на онлайн-показ    │
└───────────────────────────────────┘
```

### Новые кнопки
- 📌 Фиксация клиента → https://ri.rclick.ru/notice/
- 🏠 Шахматка → https://ri.rclick.ru/
- 🎬 Медиа → Презентация (PDF)

### Ключевой принцип: Площадь = ключ

**Площадь уникальна** (69 уникальных значений) — используется для связи:
- КП (JPG файлы) ↔ Расчёты ↔ AI данные

**Callback форматы:**
- `kp_send_247` — КП для 24.7 м²
- `calc_roi_lot_247` — ROI для 24.7 м²
- `calc_finance_lot_247` — рассрочка для 24.7 м²

**Минимальный лот:** В215 — 22.0 м² — 13 695 000 ₽
