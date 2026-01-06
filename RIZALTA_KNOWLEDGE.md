# RIZALTA BOT — База знаний

## Быстрый старт
```bash
# SSH на сервер
ssh -p 2222 root@72.56.64.91

# Пути
cd /opt/bot        # PROD
cd /opt/bot-dev    # DEV
cd /opt/miniapp    # Mini App

# Логи
journalctl -u rizalta-bot -f           # PROD
journalctl -u rizalta-bot-dev -f       # DEV polling
journalctl -u rizalta-dev-api -f       # DEV API
journalctl -u rizalta-dev-tunnel -f    # DEV туннель

# Перезапуск
systemctl restart rizalta-bot          # PROD
systemctl restart rizalta-bot-dev      # DEV
systemctl restart rizalta-dev-api      # DEV API

# Деплой Mini App
cd /opt/miniapp && npm run build && vercel --prod
```

---

## Архитектура
```
┌─────────────────────────────────────────────────────────────┐
│                         PROD                                 │
│  Telegram → Cloudflare Tunnel → :8000 → FastAPI (webhook)   │
│  Туннель: enrolled-chapter-clouds-fold.trycloudflare.com    │
├─────────────────────────────────────────────────────────────┤
│                         DEV                                  │
│  Telegram → polling (run_polling.py)                        │
│  Mini App → Cloudflare Tunnel → :8002 → FastAPI (API)       │
│  Туннель: provide-resident-retain-employees.trycloudflare   │
├─────────────────────────────────────────────────────────────┤
│                      MINI APP                                │
│  Vercel: rizalta-miniapp.vercel.app                         │
│  /api/* → PROD туннель                                      │
│  /api-dev/* → DEV туннель                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Ключевые решения

### v2.3.0 (06.01.2026) — Mini App РАБОТАЕТ

#### 1. Почему tg.sendData() не работал
**Проблема:** Данные из Mini App не приходили в бота
**Причина:** `tg.sendData()` работает ТОЛЬКО с KeyboardButton (обычная клавиатура), а Mini App открывается через InlineKeyboardButton
**Решение:** Использовать `fetch()` вместо `sendData()`

#### 2. Разделение PROD/DEV
**Проблема:** fetch() всегда шёл на один туннель (из vercel.json)
**Решение:** 
- Параметр `?env=dev` в URL Mini App
- Два rewrite в vercel.json: `/api/*` (PROD) и `/api-dev/*` (DEV)
- App.jsx определяет путь по параметру

**Код в App.jsx:**
```javascript
const API_PATH = new URLSearchParams(window.location.search).get('env') === 'dev' ? '/api-dev' : '/api';
fetch(API_PATH + '/miniapp-action', {...})
```

**URL в ботах:**
- PROD: `https://rizalta-miniapp.vercel.app`
- DEV: `https://rizalta-miniapp.vercel.app?env=dev`

#### 3. Обход блокировок trycloudflare в РФ
**Проблема:** Мобильные операторы РФ блокируют `*.trycloudflare.com`
**Решение:** Vercel proxy — запросы идут через Vercel (не заблокирован), Vercel проксирует на туннель

**vercel.json:**
```json
{
  "rewrites": [
    {"source": "/api-dev/:path*", "destination": "https://DEV_TUNNEL/api/:path*"},
    {"source": "/api/:path*", "destination": "https://PROD_TUNNEL/api/:path*"}
  ]
}
```

### v2.1.2 (29.12.2025)

#### 1. Групповые заявки с кнопкой "Взять"
**Файлы:**
- `services/telegram.py` — send_message_inline_return_id(), edit_message_inline()
- `handlers/booking_calendar.py` — handle_take_booking()
- БД: bookings.taken_by_id, taken_by_name, group_message_id

### v2.1.1 (24.12.2025)

#### 1. Пагинация вместо noop
- Кеш `_search_cache[chat_id]` хранит lots, offset, back_callback
- Кнопка "📋 Показать ещё N лотов"

#### 2. Часовые пояса
- Таблица `users` с полем timezone (INTEGER, default 3)
- 11 зон: UTC+2 — UTC+12

#### 3. Поиск по бюджету ±10%
```python
min_price = int(budget * 0.9)
max_price = int(budget * 1.1)
```

---

## Mini App — Полная документация

### Деплой Mini App
```bash
cd /opt/miniapp
npm run build
vercel --prod
```

### При смене URL туннеля
```bash
# 1. Узнать новые URL
journalctl -u cloudflare-rizalta --no-pager -n 30 | grep trycloudflare  # PROD
journalctl -u rizalta-dev-tunnel --no-pager -n 30 | grep trycloudflare  # DEV

# 2. Обновить vercel.json
nano /opt/miniapp/vercel.json

# 3. Редеплой
cd /opt/miniapp && vercel --prod
```

### Текущие туннели (на 06.01.2026)
- **PROD:** `enrolled-chapter-clouds-fold.trycloudflare.com`
- **DEV:** `provide-resident-retain-employees.trycloudflare.com`

### Чеклист "Если Mini App не работает"
```bash
# 1. API PROD работает?
curl -s "https://rizalta-miniapp.vercel.app/api/lots" | head -c 100

# 2. API DEV работает?
curl -s "https://rizalta-miniapp.vercel.app/api-dev/lots" | head -c 100

# 3. Туннели живы?
systemctl status cloudflare-rizalta    # PROD
systemctl status rizalta-dev-tunnel    # DEV

# 4. URL туннелей актуальны в vercel.json?
cat /opt/miniapp/vercel.json

# 5. uvicorn DEV запущен?
systemctl status rizalta-dev-api
```

---

## Частые команды

### Проверка синтаксиса
```bash
cd /opt/bot && source venv/bin/activate
python3 -c "import app; print('OK')"
```

### Различия DEV/PROD
```bash
diff /opt/bot-dev/app.py /opt/bot/app.py | head -30
```

### Структура БД
```bash
sqlite3 /opt/bot/properties.db ".schema"
sqlite3 /opt/bot/properties.db "SELECT COUNT(*) FROM units"
```

### Git коммит
```bash
# PROD
cd /opt/bot && git add -A && git commit -m "описание" && git push

# DEV
cd /opt/bot-dev && git add -A && git commit -m "описание" && git push

# Mini App
cd /opt/miniapp && git add -A && git commit -m "описание" && git push
```

---

## Типичные ошибки и решения

### 1. Mini App данные идут не в тот бот
**Причина:** Неправильный параметр env или vercel.json
**Решение:** Проверить URL в боте и vercel.json

### 2. Mini App не работает без VPN
**Причина:** trycloudflare заблокирован оператором
**Решение:** Использовать Vercel proxy (уже настроено)

### 3. При перезапуске туннеля Mini App сломался
**Причина:** URL туннеля изменился
**Решение:** Обновить vercel.json и редеплоить

### 4. NameError: name 'asyncio' is not defined
**Решение:** `sed -i '1i import asyncio' /opt/bot/app.py`

### 5. ModuleNotFoundError
**Решение:** 
```bash
/opt/bot/venv/bin/pip install MODULE_NAME
```

---

## Деплой процедура

### Изменения в Mini App
```bash
cd /opt/miniapp
# Изменить код
npm run build
vercel --prod
git add -A && git commit -m "описание" && git push
```

### Изменения в DEV боте
```bash
cd /opt/bot-dev
# Изменить код
systemctl restart rizalta-bot-dev
git add -A && git commit -m "описание" && git push
```

### Изменения в PROD боте
```bash
cd /opt/bot
# Изменить код
python3 -c "import app; print('OK')"
systemctl restart rizalta-bot
git add -A && git commit -m "описание" && git push
```

---

## Контакты и ссылки

### Сервер
- **IP:** 72.56.64.91
- **Port:** 2222
- **User:** root
- **Auth:** SSH key (пароль отключён)

### Боты
- **PROD:** @RealtMeAI_bot
- **DEV:** @rizaltatestdevop_bot

### Репозитории
- **PROD:** github.com/semiekhin/rizalta-bot
- **DEV:** github.com/semiekhin/rizalta-bot-dev
- **Mini App:** github.com/semiekhin/rizalta-miniapp

### Mini App
- **URL:** https://rizalta-miniapp.vercel.app
- **Vercel scope:** skergs-projects-4d01ef5d

### Telegram IDs
- **Admin:** 512319063
- **Группа показов:** -1003301897674

---

## TODO (приоритеты)

### 🔴 Критично
- [ ] **Self-Healing система** — watchdog для автовосстановления
- [ ] **Named Tunnel / свой домен** — убрать зависимость от меняющихся URL

### 🟡 Важно
- [ ] **Доработка Mini App** — выбор действия (КП/ROI/Показ)
- [ ] **RealtMy Mini App** — управление контентом каналов

### 🟢 Улучшения
- [ ] Автодеплой Vercel через GitHub
- [ ] Redis кеширование при 500+ users
- [ ] PostgreSQL при 2000+ users
