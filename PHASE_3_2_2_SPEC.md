# RIZALTA WebApp — Phase 3.2.2: AI Чат + Секретарь + Фиксация

---

## КРИТИЧЕСКИ ВАЖНО — НЕ ТРОГАТЬ

- `/opt/bot` (порт 8000) — PROD бот, НИКОГДА не редактировать
- `/opt/bot-dev` (порт 8002) — DEV бот, НИКОГДА не редактировать
- `/opt/bot/properties.db` — читаем, НЕ пишем
- Файлы .env бота — ТОЛЬКО ЧИТАЕМ для копирования значений
- Существующие endpoints и страницы webapp — не ломать
- `notifications.py`, `compare_pdf_generator.py` — не менять

**Версия:** v0.6.1-synced → v0.7.0
**Дата:** 11.02.2026

---

## Общий контекст

WebApp — альтернатива Telegram-боту для российских риэлторов. В боте уже работает AI-консультант (OpenAI gpt-4o-mini), система секретаря (задачи/расписание) и фиксация клиентов (ri.rclick.ru). Задача — перенести весь этот функционал в webapp, заменив Telegram-кнопки на веб-интерфейс.

### Инфраструктура
- Сервер: `ssh -p 2222 root@72.56.64.91`
- WebApp: `/opt/webapp` (port 8003, systemd webapp.service)
- PROD бот: `/opt/bot` — **ТОЛЬКО ЧИТАТЬ**, не модифицировать
- DEV бот: `/opt/bot-dev` — **ТОЛЬКО ЧИТАТЬ**
- Frontend: Preact + Tailwind CSS 4 + Vite 7
- Backend: FastAPI + Python 3.12 (uvicorn)

### Ключевые файлы бота (ИСТОЧНИКИ для копирования/адаптации)
- `/opt/bot/services/ai_chat.py` — AI с function calling (11 функций)
- `/opt/bot/services/intent_router.py` — классификация намерений (quick patterns + GPT)
- `/opt/bot/services/secretary_ai.py` — парсинг задач, classify intent TASK/SCHEDULE/OTHER
- `/opt/bot/services/secretary_db.py` — SQLite БД секретаря
- `/opt/bot/handlers/ai_chat.py` — handler: intent → действие (Telegram-специфичный)
- `/opt/bot/handlers/secretary.py` — handler секретаря (меню, задачи, перенос)
- `/opt/bot/handlers/booking_fixation.py` — фиксация клиентов (авторизация rclick)
- `/opt/bot/services/rclick_service.py` — API интеграция с ri.rclick.ru
- `/opt/bot/config/instructions.txt` — system prompt для AI
- `/opt/bot/data/rizalta_finance.json` — финансовые данные (958 строк)
- `/opt/bot/config/settings.py` — OPENAI_API_KEY и прочие настройки

### Принципы адаптации бот → webapp
1. **Telegram send_message** → SSE streaming в браузер
2. **Telegram inline_buttons** → кликабельные кнопки/ссылки в чате или навигация по webapp
3. **Telegram callback_data** → фронтенд-навигация (router) или действия в UI
4. **Уведомления** → по-прежнему летят в Telegram группу (система из Phase 3.2.1)
5. **OpenAI API** — используем тот же ключ и ту же модель (gpt-4o-mini), смена модели — техдолг

---

## Разбивка на подфазы

### Phase 3.2.2a — AI Chat движок (SSE streaming)
### Phase 3.2.2b — Function calling + интерактивные ответы
### Phase 3.2.2c — Секретарь (задачи, расписание)
### Phase 3.2.2d — Фиксация клиентов (rclick)

Делать **строго последовательно**. Каждая фаза — отдельный коммит с тегом.

---

## Phase 3.2.2a — AI Chat движок (MVP)

**Цель:** рабочий AI-чат со стримингом ответов, без function calling.

### Backend

#### 1. Новые файлы

**`backend/services/ai_chat.py`** — адаптация из `/opt/bot/services/ai_chat.py`:
- Скопировать `build_finance_system_context()` — без изменений
- Скопировать `ask_ai_about_project()` — адаптировать для streaming
- `load_finance()` и `load_instructions()` — реализовать чтение из скопированных файлов
- **НЕ копировать** `analyze_user_intent()` и `AVAILABLE_FUNCTIONS` — это Phase 3.2.2b

**`backend/services/data_loader.py`** — загрузчик данных:
- Скопировать `/opt/bot/data/rizalta_finance.json` → `/opt/webapp/backend/data/rizalta_finance.json`
- Скопировать `/opt/bot/config/instructions.txt` → `/opt/webapp/backend/config/instructions.txt`
- Реализовать `load_finance()` и `load_instructions()` по аналогии с ботом

#### 2. Переменные окружения

В `backend/.env` добавить:
```
OPENAI_API_KEY=<скопировать из /opt/bot/.env>
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
```

#### 3. Endpoint — SSE streaming

В `backend/app.py` добавить:

```
POST /api/chat
```

**Request body:**
```json
{
  "message": "Расскажи про доходность",
  "history": [
    {"role": "user", "content": "Привет"},
    {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"}
  ]
}
```

**Response:** `text/event-stream` (SSE)

Формат событий:
```
data: {"type": "token", "content": "Здрав"}
data: {"type": "token", "content": "ствуйте"}
data: {"type": "done", "content": ""}
data: {"type": "error", "content": "Ошибка OpenAI API"}
```

**Реализация:**
- Использовать `openai` Python SDK с `stream=True`
- `StreamingResponse` из FastAPI с `media_type="text/event-stream"`
- System prompt = `load_instructions()` + `build_finance_system_context(load_finance())`
- `history` из request body передаётся в messages[] между system и текущим user message
- Ограничить history до последних 20 сообщений (чтобы не превысить контекст)
- Обработка ошибок: если OpenAI недоступен → отправить event с type "error"

#### 4. Зависимости

```bash
pip install openai --break-system-packages
```

Проверить что openai не конфликтует с уже установленными пакетами.

### Frontend

#### 5. `frontend/src/pages/Chat.jsx` — полная переработка

Сейчас Chat.jsx — заглушка. Нужен полноценный чат.

**Состояние (в памяти браузера, без localStorage):**
```
messages: [{role: "user"|"assistant", content: "..."}]
input: ""
isStreaming: false
error: null
```

**UI структура:**
- Верхняя панель: заголовок "AI Консультант"
- Область сообщений: скролл, автоскролл вниз при новых сообщениях
- Пузыри сообщений: user справа (золотой фон), assistant слева (тёмный фон)
- Индикатор "печатает..." во время стриминга (три мигающие точки)
- Поле ввода внизу: textarea + кнопка отправки
- Кнопка отправки disabled во время стриминга
- Enter = отправить, Shift+Enter = новая строка
- pb-24 чтобы не перекрывался навбаром

**SSE подключение:**
```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ message: input, history: messages })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
// Парсить SSE events, накапливать токены в текущем assistant-сообщении
```

**Стилизация:** RIZALTA брендинг (зелёный #263524, крем #F2EBD9, золото #D4A84B). Шрифт Montserrat.

### Тестирование Phase 3.2.2a

```bash
# Backend test
curl -X POST http://localhost:8003/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Какая доходность у RIZALTA?", "history": []}' \
  --no-buffer

# Должен вернуть поток SSE events с токенами ответа
```

Фронтенд: открыть чат, написать "Привет", "Какая доходность?", "Расскажи про рассрочку" — ответы должны стримиться.

**Коммит:** `feat: AI chat engine with SSE streaming (Phase 3.2.2a)`
**Тег:** `v0.7.0-alpha`

---

## Phase 3.2.2b — Function calling + интерактивные ответы

**Цель:** AI определяет intent и предлагает действия кнопками внутри чата.

### Backend

#### 1. `backend/services/intent_router.py`

Скопировать из `/opt/bot/services/intent_router.py` и адаптировать:
- `QUICK_PATTERNS` — убрать Telegram-эмодзи кнопки, оставить текстовые паттерны
- `classify_intent()` — без изменений (gpt-4o-mini)
- `normalize_params()` — без изменений
- `LOT_CODE_PATTERN`, `extract_lot_code()` — без изменений

#### 2. Function calling в `ai_chat.py`

Добавить `analyze_user_intent()` из бота с `AVAILABLE_FUNCTIONS` (11 функций). Без изменений — тот же формат ответа.

#### 3. Обновить `POST /api/chat`

Логика endpoint меняется:

1. Получить message + history
2. Вызвать `analyze_user_intent(message)` 
3. **Если intent != "chat"** — вернуть structured response (не SSE):
```json
{
  "type": "action",
  "intent": "calculate_roi",
  "params": {"unit_code": "A209"},
  "message": "Вот расчёт доходности по юниту A209:",
  "actions": [
    {"label": "📊 Посмотреть ROI", "type": "navigate", "to": "/catalog/A209?modal=roi"},
    {"label": "💳 Рассрочка", "type": "navigate", "to": "/catalog/A209?modal=deposit"},
    {"label": "✅ Записаться на показ", "type": "navigate", "to": "/booking"}
  ]
}
```

4. **Если intent == "chat"** — SSE streaming как раньше

#### 4. Маппинг intent → webapp actions

Вот как каждый bot intent транслируется в webapp:

| Bot intent | Webapp action |
|---|---|
| `build_portfolio` | Текстовый ответ AI с подбором + кнопка → /catalog с фильтрами |
| `calculate_roi` | Кнопка → /catalog/{code}?modal=roi |
| `show_installment` | Кнопка → /catalog/{code}?modal=deposit |
| `book_showing` | Кнопка → /booking |
| `show_layouts` | Кнопка → /catalog/{code} (раздел планировки) |
| `get_commercial_proposal` | Кнопка → /catalog/{code} (скачать КП) |
| `send_presentation` | Кнопка → /presentations |
| `open_fixation` | Кнопка → /fixation (Phase 3.2.2d) |
| `open_shahmatka` | Кнопка → /catalog |
| `send_documents` | Кнопка → /documents |
| `show_media` | Кнопка → /media |
| `compare_deposit` | Кнопка → /catalog/{code}?modal=deposit |
| `create_task` | Передать в секретаря (Phase 3.2.2c) |
| `show_schedule` | Кнопка → /secretary (Phase 3.2.2c) |
| `show_news` | Кнопка → /news |

#### 5. Для build_portfolio — серверный расчёт

Скопировать из бота и адаптировать:
- `/opt/bot/services/calculations.py` → `backend/services/calculations.py`
- Функции: `suggest_units_for_budget()`, `compute_rent_cashflow()`, `fmt_rub()`
- AI в чате вызывает build_portfolio → backend считает → возвращает текст + кнопки

### Frontend

#### 6. Chat.jsx — поддержка actions

Обработка ответа с `type: "action"`:
- Показать `message` как пузырь assistant
- Под пузырём — ряд кнопок из `actions[]`
- Клик по кнопке с `type: "navigate"` → вызов навигации (router) на указанный путь
- Кнопки стилизовать: золотой контур, иконки, RIZALTA-стиль

**Коммит:** `feat: function calling + interactive actions (Phase 3.2.2b)`
**Тег:** `v0.7.0-beta`

---

## Phase 3.2.2c — Секретарь

**Цель:** управление задачами и расписанием через веб-интерфейс + интеграция с AI чатом.

### Backend

#### 1. `backend/services/secretary_db.py`

Скопировать из `/opt/bot/services/secretary_db.py` и адаптировать:
- Изучить структуру таблиц (tasks, users, timezones)
- БД хранить в `backend/secretary.db` (отдельная от webapp.db)
- Все CRUD операции: add_task, get_tasks_for_date, mark_done, delete_task, move_task
- Адаптировать user_id: в боте это chat_id, в webapp — пока использовать фиксированный ID или session-based

**ВАЖНО:** Изучить `/opt/bot/services/secretary_db.py` полностью перед копированием:
```bash
cat /opt/bot/services/secretary_db.py
```

#### 2. `backend/services/secretary_ai.py`

Скопировать из `/opt/bot/services/secretary_ai.py`:
- `parse_task_with_ai()` — парсинг задач из текста через GPT
- `classify_intent()` — TASK/SCHEDULE/OTHER
- `analyze_workload()` — анализ загрузки
- `generate_morning_digest()` — утренний дайджест

#### 3. API endpoints

```
GET  /api/secretary/tasks?date=2026-02-11          → задачи на дату
GET  /api/secretary/tasks/week?start=2026-02-10    → задачи на неделю
POST /api/secretary/tasks                          → создать задачу
     body: {task, date, time?, client_name?, priority?}
PUT  /api/secretary/tasks/{id}/done                → отметить выполненной
PUT  /api/secretary/tasks/{id}/undone              → снять отметку
PUT  /api/secretary/tasks/{id}/move                → перенести
     body: {new_date}
DELETE /api/secretary/tasks/{id}                   → удалить
POST /api/secretary/parse                          → AI парсинг текста в задачу
     body: {text: "завтра позвонить Иванову в 10"}
     response: {task, date, time, client_name, priority}
```

### Frontend

#### 4. `frontend/src/pages/Secretary.jsx` — полная страница

Сейчас заглушка → нужна полноценная страница.

**UI:**
- Вид по дням: календарная полоска (горизонтальный скролл дней) + список задач ниже
- Каждая задача: текст, время (если есть), приоритет (цветная метка), чекбокс выполнения
- Кнопка "+" → модалка создания задачи (текстовое поле, дата, время, приоритет)
- Или: поле ввода свободным текстом → отправка на `/api/secretary/parse` → подтверждение распарсенной задачи
- Свайп/кнопки на задаче: удалить, перенести
- Вид по неделе: сводка задач по дням

**Стилизация:** RIZALTA брендинг

#### 5. Интеграция с AI чатом

Когда AI в чате определяет intent `create_task`:
- Парсит текст через `parse_task_with_ai()`
- Возвращает action:
```json
{
  "type": "action",
  "intent": "create_task",
  "message": "✅ Задача создана: Позвонить Иванову, завтра в 10:00",
  "actions": [
    {"label": "📅 Открыть секретарь", "type": "navigate", "to": "/secretary"}
  ]
}
```

Когда intent `show_schedule`:
```json
{
  "type": "action",
  "intent": "show_schedule",
  "message": "📋 У вас 3 задачи на сегодня",
  "actions": [
    {"label": "📅 Посмотреть расписание", "type": "navigate", "to": "/secretary"}
  ]
}
```

**Коммит:** `feat: secretary — tasks management (Phase 3.2.2c)`
**Тег:** `v0.7.0-rc1`

---

## Phase 3.2.2d — Фиксация клиентов

**Цель:** форма фиксации клиента на ri.rclick.ru через webapp.

### Backend

#### 1. Изучить полностью:

```bash
cat /opt/bot/handlers/booking_fixation.py
cat /opt/bot/services/rclick_service.py
```

Понять:
- Процесс авторизации на ri.rclick.ru (логин/пароль риэлтора)
- Какие данные отправляются для фиксации (имя клиента, телефон, комментарий)
- Как хранится сессия авторизации (cookies, tokens)

#### 2. `backend/services/rclick_service.py`

Скопировать из бота и адаптировать:
- Авторизация: в боте привязана к chat_id → в webapp привязать к session/token
- Запросы к ri.rclick.ru: httpx async
- Хранение сессии: в webapp.db (таблица rclick_sessions)

#### 3. API endpoints

```
POST /api/fixation/auth            → авторизация на rclick
     body: {login, password}
     response: {ok, message}
GET  /api/fixation/status           → проверка авторизации
POST /api/fixation/create           → создать фиксацию
     body: {client_name, client_phone, comment?}
     response: {ok, message, fixation_id?}
```

### Frontend

#### 4. `frontend/src/pages/Fixation.jsx` — полная страница

Сейчас заглушка → нужна полноценная страница.

**UI — два состояния:**

**Не авторизован:**
- Форма: логин + пароль для ri.rclick.ru
- Кнопка "Войти"
- Ошибка авторизации → сообщение

**Авторизован:**
- Статус: "Вы авторизованы как [имя]"
- Кнопка "Новая фиксация" → форма:
  - ФИО клиента (обязательно)
  - Телефон клиента (обязательно, валидация ≥10 цифр)
  - Комментарий (опционально)
  - Кнопка "Отправить фиксацию"
- Статус отправки: loading → success/error
- После успеха: "Клиент зафиксирован за вами на 30 дней"
- Кнопка "Ещё фиксация"
- Кнопка "Выйти" (деавторизация)

**Стилизация:** RIZALTA брендинг

#### 5. Интеграция с AI чатом

Intent `open_fixation` в чате:
```json
{
  "type": "action",
  "intent": "open_fixation",
  "message": "Для фиксации клиента за вами перейдите в раздел Фиксация.",
  "actions": [
    {"label": "📌 Открыть фиксацию", "type": "navigate", "to": "/fixation"}
  ]
}
```

**Коммит:** `feat: client fixation via rclick (Phase 3.2.2d)`
**Тег:** `v0.7.0`

---

## Общие требования ко всем подфазам

### Безопасность
- OPENAI_API_KEY — только в .env, никогда не в git
- rclick credentials — хранить зашифрованно или в сессии
- Rate limiting на /api/chat — не более 10 запросов в минуту на IP (защита от спама)

### Обработка ошибок
- Если OpenAI API упал → пользователь видит "AI временно недоступен, попробуйте позже"
- Если rclick.ru недоступен → "Сервис фиксации временно недоступен"
- Все ошибки логировать в stdout (для journalctl)

### Документация
- После КАЖДОЙ подфазы обновлять CLAUDE.md и TASK_MAP.md
- Добавлять новые endpoints, файлы, зависимости

### Git workflow
- Каждая подфаза — отдельный коммит с понятным сообщением
- Теги на каждый milestone
- `git push origin webapp --tags` после каждой подфазы

### НЕ ТРОГАТЬ
- `/opt/bot` и `/opt/bot-dev` — только читать и копировать
- Существующие endpoints и страницы webapp — не ломать
- `notifications.py`, `compare_pdf_generator.py` — не менять

### Порядок работы для 1Code
1. Прочитать это ТЗ полностью
2. Изучить текущий код webapp: `cat /opt/webapp/CLAUDE.md`
3. Изучить исходники бота (файлы перечислены выше) — ЧИТАТЬ, не менять
4. Начать с Phase 3.2.2a
5. Протестировать, закоммитить, перейти к следующей фазе
6. Если что-то непонятно или требует решения — остановиться и спросить
