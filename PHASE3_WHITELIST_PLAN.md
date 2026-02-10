# Phase 3.1 — Белый список + UI каталога для WebApp

## Контекст

**Текущее состояние каталога:**
- Корпус 1 «Family» — 255 лотов, properties.db, виден всем
- Корпус 2 «Business» — 103 лота, properties.db, виден всем (открыт после ценовой паузы)
- Корпус 3 «Digital» — 282 лота, corp3_units.json, **только для белых**

**Как работает в боте:**
- Таблица `corp3_whitelist` в properties.db: `chat_id INTEGER PRIMARY KEY, name TEXT, added_at TIMESTAMP`
- 20 пользователей в белом списке
- Функция `is_whitelisted(chat_id)` проверяет доступ перед каждым действием с К3
- Данные К3: `/opt/bot-dev/data/corp3_units.json` (282 лота, JSON)

**Проблема:** В вебе нет chat_id. Нужен другой механизм.

**Решение:** Один общий токен для всех белых пользователей, передаётся через URL.

---

## Архитектура решения

### Схема доступа

```
Обычный пользователь:
  webapp.rizaltaservice.ru → видит Корпус 1 + 2 (358 лотов)

Белый пользователь:
  webapp.rizaltaservice.ru/?token=XXXXX → токен сохраняется в localStorage
  → видит Корпус 1 + 2 + кнопка «Корпус 3» в меню → 282 лота
```

### Принцип: минимум изменений

- Существующий каталог (Корпус 1+2) НЕ трогаем (кроме UI кнопок фильтра)
- Корпус 3 — отдельная страница Corp3.jsx со своей шахматкой
- В меню Home.jsx появляется кнопка «🏗 Корпус 3» (только с токеном)
- Когда К3 выйдет в официальные продажи — убираем проверку токена

---

## Задачи по файлам

### 0. Catalog.jsx — упрощение панели фильтров

**Файл:** `frontend/src/pages/Catalog.jsx`

**Чисто косметическое изменение.** Функционал фильтрации НЕ трогаем — он работает хорошо.

**Было (4 кнопки + Фильтры справа):**
```
[ Все (103) ] [ Свободно (103) ] [ Бронь (0) ] [ Продано (0) ]     [ ⚙ Фильтры ]
```

**Стало (2 кнопки рядом):**
```
[ Свободно (103) ] [ Фильтры ]
```

Что сделать:
- Убрать кнопки «Все», «Бронь», «Продано» из JSX
- Сдвинуть кнопку «Фильтры» влево, рядом с «Свободно»
- Логика фильтрации остаётся без изменений
- Панель фильтров (площадь, цена) по-прежнему раскрывается при нажатии «Фильтры»

---

### 1. Backend: webapp.db + проверка токена

**Файл:** `backend/app.py`

#### 1.1 Создать webapp.db

```python
import sqlite3

WEBAPP_DB = "/opt/webapp/backend/webapp.db"

def init_webapp_db():
    """Создаёт таблицы webapp при старте."""
    conn = sqlite3.connect(WEBAPP_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS access_tokens (
            token TEXT PRIMARY KEY,
            name TEXT,
            level TEXT DEFAULT 'white',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
```

Вызвать `init_webapp_db()` при старте приложения (в lifespan или startup event).

#### 1.2 Вставить начальный токен

При первой инициализации БД — вставить один общий токен:

```python
import secrets

def seed_token():
    """Создаёт токен если БД пустая."""
    conn = sqlite3.connect(WEBAPP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM access_tokens")
    if cursor.fetchone()[0] == 0:
        token = secrets.token_urlsafe(16)  # ~22 символа
        cursor.execute(
            "INSERT INTO access_tokens (token, name, level) VALUES (?, ?, ?)",
            (token, "Общий белый список", "white")
        )
        conn.commit()
        print(f"[WEBAPP] Создан токен белого списка: {token}")
    conn.close()
```

**ВАЖНО:** Токен выводится в лог при первом запуске. Его нужно сохранить и раздать белым.

#### 1.3 FastAPI dependency для проверки доступа

```python
from fastapi import Request, Depends

def get_access_level(request: Request) -> str:
    """Определяет уровень доступа по токену."""
    token = request.headers.get("X-Access-Token", "")
    if not token:
        return "public"
    
    conn = sqlite3.connect(WEBAPP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT level FROM access_tokens WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else "public"
```

#### 1.4 Новые endpoints

```python
@app.get("/api/access/check")
def check_access(level: str = Depends(get_access_level)):
    """Проверяет токен, возвращает уровень доступа."""
    return {"level": level}

@app.get("/api/corp3/lots")
def get_corp3_lots(level: str = Depends(get_access_level)):
    """Отдаёт лоты Корпуса 3 (только для white)."""
    if level != "white":
        raise HTTPException(status_code=403, detail="Access denied")
    
    import json
    corp3_path = "/opt/bot-dev/data/corp3_units.json"
    
    with open(corp3_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    units = [u for u in data.get("units", []) 
             if u.get("area", 0) >= 23.5 and u.get("status") == "available"]
    
    return {
        "ok": True,
        "building_name": data.get("building_name", "Корпус 3"),
        "total": len(units),
        "lots": units
    }
```

**Фильтр `area >= 23.5`** — взят из бота (corp3.py, строка load_units). Сохраняем ту же логику.

---

### 2. Frontend: Auth утилита

**Новый файл:** `frontend/src/utils/auth.js`

```javascript
const TOKEN_KEY = 'rizalta_access_token';
const LEVEL_KEY = 'rizalta_access_level';

// Проверить ?token= в URL и сохранить
export function captureTokenFromURL() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
        localStorage.setItem(TOKEN_KEY, token);
        // Убрать токен из URL (чтобы не светился)
        window.history.replaceState({}, '', window.location.pathname);
    }
}

export function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
}

export function getAccessLevel() {
    return localStorage.getItem(LEVEL_KEY) || 'public';
}

export function isWhitelisted() {
    return getAccessLevel() === 'white';
}

// Проверить токен на сервере
export async function verifyAccess() {
    const token = getToken();
    if (!token) {
        localStorage.setItem(LEVEL_KEY, 'public');
        return 'public';
    }
    
    try {
        const res = await fetch('/api/access/check', {
            headers: { 'X-Access-Token': token }
        });
        const data = await res.json();
        localStorage.setItem(LEVEL_KEY, data.level);
        return data.level;
    } catch {
        localStorage.setItem(LEVEL_KEY, 'public');
        return 'public';
    }
}

// Обёртка для fetch с токеном
export function authFetch(url, options = {}) {
    const token = getToken();
    if (token) {
        options.headers = {
            ...options.headers,
            'X-Access-Token': token,
        };
    }
    return fetch(url, options);
}
```

---

### 3. Frontend: интеграция в App.jsx

**Файл:** `frontend/src/App.jsx`

При загрузке приложения:

```javascript
import { captureTokenFromURL, verifyAccess, isWhitelisted } from './utils/auth';
import { useState, useEffect } from 'preact/hooks';

function App() {
    const [accessLevel, setAccessLevel] = useState('public');

    useEffect(() => {
        captureTokenFromURL();
        verifyAccess().then(level => setAccessLevel(level));
    }, []);
    
    // Передавать accessLevel в роутер / страницы через props или context
    // ...
}
```

Добавить роут для Corp3:
```javascript
case 'corp3':
    return <Corp3 />;
```

---

### 4. Frontend: кнопка «Корпус 3» в Home.jsx

**Файл:** `frontend/src/pages/Home.jsx`

В массив MENU_ITEMS добавить условный элемент:

```javascript
import { isWhitelisted } from '../utils/auth';

// В компоненте Home:
const menuItems = [
    { id: 'lots', icon: '🏢', label: 'Лоты' },
    { id: 'presentations', icon: '📸', label: 'Презентации' },
    { id: 'chat', icon: '💬', label: 'Чат с AI' },
    { id: 'secretary', icon: '🗓', label: 'Секретарь' },
    { id: 'documents', icon: '📄', label: 'Договоры' },
    { id: 'media', icon: '🎬', label: 'Медиа' },
    { id: 'fixation', icon: '📌', label: 'Фиксация' },
    { id: 'news', icon: '📰', label: 'Новости' },
    // Корпус 3 — только для белых
    ...(isWhitelisted() ? [{ id: 'corp3', icon: '🏗', label: 'Корпус 3' }] : []),
];
```

Сетка станет 2×4 + 1 (или 2×5 для белых). Кнопка «Корпус 3» может иметь визуальное отличие (например, золотая рамка) чтобы подчеркнуть эксклюзивность.

---

### 5. Frontend: новая страница Corp3.jsx

**Новый файл:** `frontend/src/pages/Corp3.jsx`

Страница аналогична Catalog.jsx, но:
- Данные из `GET /api/corp3/lots` (через `authFetch`)
- Заголовок: «Корпус 3 «Digital»»
- Панель фильтров: 2 кнопки ([ Свободно ] [ Фильтры ]) — как в обновлённом Catalog.jsx
- Шахматка лотов с фильтрами (площадь, цена)
- Карточка лота — при клике переход на LotDetail (нужно поддержать К3 в LotDetail)
- Если 403 — показать «Доступ ограничен»

**Структура данных К3 (из corp3_units.json):**
```json
{
    "id": 620913,
    "code": "А200",
    "building": 3,
    "section": 1,
    "floor": 2,
    "rooms": 1,
    "area": 24.7,
    "price": 15067000,
    "status": "available",
    "layout_path": "/opt/bot-dev/data/corp3_layouts/2 ЭТАЖ/A_200.jpg",
    "block_section": 3
}
```

**ВНИМАНИЕ:** Поля отличаются от properties.db:
- `area` вместо `area_m2`
- `price` вместо `price_rub`  
- Нет `price_per_m2_rub` (считать: price / area)
- Нет `completion`, `page_url`
- Есть `layout_path` (локальный путь) — нужен endpoint для раздачи

#### 5.1 Endpoint для планировок К3

```python
@app.get("/api/corp3/layout/{code}")
def get_corp3_layout(code: str, level: str = Depends(get_access_level)):
    """Отдаёт планировку лота К3."""
    if level != "white":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти лот по коду, взять layout_path
    # Отдать FileResponse
    # ВАЖНО: валидировать путь, не отдавать произвольные файлы!
```

---

### 6. LotDetail.jsx — поддержка лотов К3

**Файл:** `frontend/src/pages/LotDetail.jsx`

Сейчас LotDetail получает данные из `/api/lots` (properties.db). Нужно:
- Определять источник лота (К1-2 из /api/lots, К3 из /api/corp3/lots)
- Маппить поля К3 → формат К1-2 (area → area_m2, price → price_rub)
- Планировка К3: из `/api/corp3/layout/{code}`
- ROI/рассрочка/депозит — должны работать (те же калькуляторы, входные данные area + price)
- КП (PDF/XLSX) — нужно проверить, поддерживает ли генератор лоты не из properties.db

**Рекомендация:** Передавать данные лота через state при навигации, чтобы не делать повторный запрос:
```javascript
navigate('lot', { lot: lotData, source: 'corp3' });
```

---

## Порядок реализации

```
Шаг 0:  Frontend — Catalog.jsx — убрать 3 кнопки       (5 мин)
Шаг 1:  Backend — webapp.db + init + seed_token          (10 мин)
Шаг 2:  Backend — /api/access/check                      (5 мин)
Шаг 3:  Backend — /api/corp3/lots                         (10 мин)
Шаг 4:  Backend — /api/corp3/layout/{code}                (10 мин)
Шаг 5:  Frontend — utils/auth.js                          (10 мин)
Шаг 6:  Frontend — App.jsx — captureToken + роут corp3    (5 мин)
Шаг 7:  Frontend — Home.jsx — условная кнопка             (5 мин)
Шаг 8:  Frontend — Corp3.jsx — шахматка                   (30 мин)
Шаг 9:  Frontend — LotDetail.jsx — поддержка К3           (20 мин)
Шаг 10: Тестирование                                      (15 мин)
```

---

## Тестирование

### Получить токен
```bash
sqlite3 /opt/webapp/backend/webapp.db "SELECT token FROM access_tokens"
```

### Проверка без токена (public)
```bash
# Должен вернуть level=public
curl -s http://127.0.0.1:8003/api/access/check | python3 -m json.tool

# Должен вернуть 403
curl -s http://127.0.0.1:8003/api/corp3/lots
```

### Проверка с токеном (white)
```bash
TOKEN="вставить_токен"

# Должен вернуть level=white
curl -s -H "X-Access-Token: $TOKEN" http://127.0.0.1:8003/api/access/check

# Должен вернуть 282 лота
curl -s -H "X-Access-Token: $TOKEN" http://127.0.0.1:8003/api/corp3/lots | python3 -c "
import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"total\"]} лотов')
"
```

### Проверка в браузере
```
# Без токена — кнопки «Корпус 3» нет в меню
https://webapp.rizaltaservice.ru/

# С токеном — кнопка появляется
https://webapp.rizaltaservice.ru/?token=XXXXX

# После активации — токен в localStorage, кнопка видна при любом заходе
https://webapp.rizaltaservice.ru/

# Каталог — должны быть 2 кнопки: [Свободно] [Фильтры]
```

---

## Безопасность

- Токен передаётся через URL только один раз (при активации), затем убирается из адресной строки
- Все запросы к К3 идут с заголовком X-Access-Token
- Backend проверяет токен в webapp.db (не в properties.db — туда не пишем)
- Планировки К3 отдаются только после проверки токена
- Путь layout_path валидируется — нельзя запросить произвольный файл

---

## Что обновить в документации

После реализации:
1. **CLAUDE.md** — добавить Corp3.jsx, utils/auth.js, webapp.db
2. **TASK_MAP.md** — отметить Phase 3.1 выполненным
3. **RIZALTA_CURRENT.md** — исправить: Корпус 2 открыт (не скрыт!)
4. **RIZALTA_TASKS.md** — обновить статус

---

## Откат

Если что-то пошло не так:
```bash
cd /opt/webapp
git checkout v0.5.0-stable
rm -f backend/webapp.db
cd frontend && npm run build
# Перезапустить backend
```
