# RIZALTA WebApp — Карта доработок для 1Code

## ОБЗОР ИЗМЕНЕНИЙ

Переделка UI/UX: из минимального приложения (4 экрана) в полноценный клон бота RIZALTA.
Главный экран — меню-навигация (как в боте). Подвал — 3 кнопки.

**КРИТИЧНО:** Код в /opt/bot и /opt/bot-dev НЕ ТРОГАЕМ. Только читаем файлы.

---

## 1. СТРУКТУРА НАВИГАЦИИ

### Главный экран (Home.jsx) — Меню
```
[Hero: лого + заголовок]

🏢 Лоты                    📸 Презентации
💬 Чат с AI                 🗓 Секретарь  
📄 Договоры                 🎬 Медиа
📌 Фиксация                📰 Новости
        ✅ Записаться на онлайн-показ
```

### Нижняя навигация (3 кнопки)
```
🏠 Главная  |  💬 Чат с AI  |  🏢 Лоты
```

---

## 2. ЗАДАЧИ ПО ФАЙЛАМ

### 2.1 App.jsx — Рефакторинг роутинга

**Было:** 4 экрана (home, catalog, lot, chat), 4 кнопки в навбаре  
**Стало:** 10 экранов, 3 кнопки в навбаре

Экраны:
- `home` — главное меню
- `lots` — каталог/шахматка (бывший catalog)
- `lot` — карточка лота (бывший lot detail)
- `chat` — AI чат
- `presentations` — список презентаций
- `documents` — договоры
- `media` — видео и медиа
- `secretary` — AI секретарь
- `fixation` — фиксация клиента
- `news` — новости, курсы валют
- `booking` — запись на показ

Навбар:
```jsx
const NAV_ITEMS = [
  { id: 'home', icon: '🏠', label: 'Главная' },
  { id: 'chat', icon: '💬', label: 'Чат с AI' },
  { id: 'lots', icon: '🏢', label: 'Лоты' },
]
```

### 2.2 Home.jsx — Меню-навигация

**Было:** Hero + 3 quick actions + статистика  
**Стало:** Hero (золотой, компактнее) + сетка 2×4 меню + кнопка показа

```jsx
// Hero: золотой фон, зелёное лого, компактный
// Сетка меню 2 колонки:
const MENU_ITEMS = [
  { id: 'lots', icon: '🏢', label: 'Лоты' },
  { id: 'presentations', icon: '📸', label: 'Презентации' },
  { id: 'chat', icon: '💬', label: 'Чат с AI' },
  { id: 'secretary', icon: '🗓', label: 'Секретарь' },
  { id: 'documents', icon: '📄', label: 'Договоры' },
  { id: 'media', icon: '🎬', label: 'Медиа' },
  { id: 'fixation', icon: '📌', label: 'Фиксация' },
  { id: 'news', icon: '📰', label: 'Новости' },
]
// Полноширинная кнопка: "✅ Записаться на онлайн-показ"
// Мини-статистика: X свободно | Y бронь | Z продано
```

### 2.3 Catalog.jsx → Lots.jsx — Добавить фильтры

**Было:** Фильтр только по статусу (все/свободно/бронь/продано)  
**Стало:** + фильтр по площади + фильтр по цене

UI фильтров (компактная панель над шахматкой):
```
[Статус ▼] [Площадь: от __ до __ м²] [Цена: от __ до __ млн]  [✕ Сброс]
```

Реализация:
- Два поля ввода min/max для площади (м²)
- Два поля ввода min/max для цены (млн ₽)
- Кнопка сброса фильтров
- Фильтрация на клиенте (данные уже загружены)
- Показать количество найденных: "Найдено: 45 из 358"
- Когда фильтр активен — подсвечивать кнопку фильтра золотым

### 2.4 НОВЫЕ СТРАНИЦЫ

#### Presentations.jsx — Презентации
Список PDF для скачивания. Файлы на сервере, отдаём через backend.

```
📕 Презентация RIZALTA (RU)        [Скачать]
📗 Презентация RIZALTA (ENG)       [Скачать]  
🏨 ZONT Hotel Group                [Скачать]
🏛 Pergaev Bureau                  [Скачать]
📊 Аналитика CoreXP                [Скачать]
```

Endpoint: `GET /api/files/presentations/{filename}`

#### Documents.jsx — Договоры
```
📋 Договор ДДУ                     [Скачать]
📋 Договор с отельным оператором   [Скачать]
📚 Скачать оба                     [Скачать]
```

Endpoint: `GET /api/files/documents/{filename}`

#### Media.jsx — Медиа
Два раздела: Презентации (ссылка на presentations) и Видео.

```
🎬 Видеоматериалы RIZALTA

▶️ Нереально                       [Смотреть]
▶️ Вести Курорт                    [Смотреть]
▶️ Большой Алтай                   [Смотреть]
▶️ Правило 30×30                   [Смотреть]
▶️ Вести тур поток                 [Смотреть]
▶️ Михалкова — Алтай               [Смотреть]
```

Видео: inline `<video>` плеер при клике, или ссылка на скачивание.
Endpoint: `GET /api/files/videos/{filename}`

#### News.jsx — Новости
- Курсы валют ЦБ РФ (API: cbr-xml-daily.ru)
- Возможно: погода в Белокурихе

Endpoint: `GET /api/news/currency`

#### Secretary.jsx — Секретарь (заглушка Phase 3)
Пока: заглушка с описанием функционала + ссылка на бот.
```
🗓 AI-Секретарь

Персональный ежедневник с голосовым вводом.
Полный функционал доступен в Telegram-боте.

[Открыть бот →]
```

Phase 3: полноценный секретарь с DeepSeek.

#### Fixation.jsx — Фиксация (заглушка Phase 3)
Пока: заглушка + ссылка на rclick.ru или бот.
```
📌 Фиксация клиента

Авторизация и фиксация клиентов через ri.rclick.ru.
Полный функционал доступен в Telegram-боте.

[Открыть бот →]
```

Phase 3: интеграция с rclick API.

#### Booking.jsx — Запись на показ
Форма:
```
✅ Запись на онлайн-показ RIZALTA

Имя: [____________]
Телефон: [____________]
Комментарий: [____________]  (необязательно)

[Отправить заявку]
```

Phase 2: форма + отправка на backend  
Phase 3: backend реально отправляет в Telegram + email

---

## 3. BACKEND ДОРАБОТКИ

### 3.1 Файловый сервер (Phase 2)
Отдаём файлы из директорий бота (read-only).

```python
# Новые endpoints в app.py

@app.get("/api/files/presentations/{filename}")
# Отдаёт PDF из /opt/bot-dev/presentations/

@app.get("/api/files/documents/{filename}")  
# Отдаёт PDF из /opt/bot/docs/

@app.get("/api/files/videos/{filename}")
# Отдаёт видео из /opt/bot-dev/videos/
```

Whitelist файлов (не отдавать произвольные файлы!):
```python
ALLOWED_PRESENTATIONS = {
    "presentation_ru": "presentation_ru.pdf",
    "presentation_eng": "presentation_eng.pdf", 
    "analytics_corexp": "analytics_corexp.pdf",
    "pergaev_bureau": "pergaev_bureau.pdf",
    "zont_hotel": "zont_hotel.pdf",
}

ALLOWED_DOCUMENTS = {
    "ddu": "ddu.pdf",
    "arenda": "arenda.pdf",
}

ALLOWED_VIDEOS = {
    "nerealno": "nerealno.mp4",
    "vesti_kurort": "vesti_kurort.mp4",
    "bolshoy_altai": "bolshoy_altai.mp4",
    "pravilo_30x30": "pravilo_30x30.mp4",
    "vesti_turpotok": "vesti_turpotok_fixed.mp4",
    "mihalkova": "mihalkova_altai.mp4",
}
```

### 3.2 Курсы валют (Phase 2)
```python
@app.get("/api/news/currency")
# Проксируем cbr-xml-daily.ru, возвращаем USD, EUR, CNY
```

### 3.3 AI Chat (Phase 3)
```python
@app.post("/api/chat")
# DeepSeek V3.2 через OpenRouter, SSE streaming
```

---

## 4. ПРИОРИТЕТЫ РЕАЛИЗАЦИИ

### Пакет A — Frontend рефакторинг (1Code сейчас)
1. App.jsx — новый роутинг (10 экранов) + навбар 3 кнопки
2. Home.jsx — меню-сетка
3. Catalog.jsx → переименовать мысленно в Lots, добавить фильтры
4. Presentations.jsx — новая страница
5. Documents.jsx — новая страница
6. Media.jsx — новая страница
7. Booking.jsx — вынести из LotDetail в отдельную страницу
8. News.jsx — заглушка (UI готов, ждёт backend)
9. Secretary.jsx — заглушка
10. Fixation.jsx — заглушка

### Пакет B — Backend файловый сервер (1Code или сервер)
1. Endpoints для презентаций, договоров, видео
2. Endpoint курсов валют

### Пакет C — AI Chat (Phase 3, отдельно)
1. DeepSeek integration
2. Function calling
3. Streaming
4. Secretary полноценный
5. Fixation через rclick API

---

## 5. ВАЖНЫЕ ЗАМЕЧАНИЯ

- Файлы презентаций и видео БОЛЬШИЕ (до 50MB). Видео лучше стримить, не грузить целиком.
- Whitelist файлов обязателен — нельзя отдавать произвольные пути.
- На сервере /opt/bot-dev/presentations/ и /opt/bot-dev/videos/ — читаем, не пишем.
- LotDetail.jsx — оставить как есть (KП, расчёты, рассрочка внутри карточки лота).
- "Записаться на показ" — и в меню Home, и в LotDetail (дублируется, это ок).
