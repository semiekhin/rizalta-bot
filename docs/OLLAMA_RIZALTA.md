# OLLAMA_RIZALTA.md
# Контекст проекта RIZALTA для локальных AI-моделей
# Версия: 1.1.0 | Дата: 16.01.2026

---

## 🎯 КАК ИСПОЛЬЗОВАТЬ ЭТОТ ФАЙЛ

**Перед началом работы** скопируй содержимое этого файла в чат с моделью.

**Приоритет моделей:**
1. `gpt-oss:120b` — сложные задачи, архитектура, рефакторинг
2. `deepseek-r1:32b` — reasoning, планирование, анализ
3. `gpt-oss:20b` — ежедневные задачи
4. `qwen2.5-coder:32b` — быстрые фиксы, простой код

**Формат работы:** Браузер (Open WebUI или аналог)

---

## ⚠️ КРИТИЧЕСКОЕ ПРАВИЛО

```
╔══════════════════════════════════════════════════════════════╗
║           PROD НЕ ТРОГАТЬ! РАБОТАТЬ ТОЛЬКО В DEV!            ║
╠══════════════════════════════════════════════════════════════╣
║  DEV:  /opt/bot-dev  →  @rizaltatestdevop_bot (polling)      ║
║  PROD: /opt/bot      →  @RealtMeAI_bot (webhook)             ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 📋 О ПРОЕКТЕ

**RIZALTA AI System v2.4.2** — Telegram-бот AI-консультант для риэлторов.
Продаёт инвестиционную недвижимость RIZALTA Resort Belokurikha (Алтай).

### Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91`
- **DEV:** `/opt/bot-dev` (polling, тестирование)
- **PROD:** `/opt/bot` (webhook :8000, боевой)
- **Mini App:** `/opt/miniapp` → https://rizalta-miniapp.vercel.app

### Стек
Python 3.12 · FastAPI · GPT-4o-mini · Whisper · SQLite · Cloudflare Tunnel

### Репозитории
- DEV: github.com/semiekhin/rizalta-bot-dev
- PROD: github.com/semiekhin/rizalta-bot
- Mini App: github.com/semiekhin/rizalta-miniapp

---

## 🌐 СЕТЕВАЯ ИНФРАСТРУКТУРА

### Схема сети

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ИНТЕРНЕТ                                       │
└─────────────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │   Telegram API            │   │   Vercel (Mini App)       │
    │   api.telegram.org        │   │   rizalta-miniapp.vercel  │
    └───────────────────────────┘   └───────────────────────────┘
                    │                           │
                    │ webhook                   │ proxy
                    ▼                           ▼
    ┌───────────────────────────────────────────────────────────┐
    │              CLOUDFLARE TUNNELS                            │
    │  ┌─────────────────────┐   ┌─────────────────────────┐    │
    │  │ api.rizaltaservice.ru│   │ dev.rizaltaservice.ru  │    │
    │  │ (rizalta-prod)      │   │ (rizalta-dev)          │    │
    │  └─────────────────────┘   └─────────────────────────┘    │
    └───────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
    ┌───────────────────────────────────────────────────────────┐
    │              СЕРВЕР 72.56.64.91                           │
    │  ┌─────────────────────┐   ┌─────────────────────────┐    │
    │  │ :8000 (PROD)        │   │ :8002 (DEV API)         │    │
    │  │ uvicorn webhook     │   │ uvicorn + polling       │    │
    │  └─────────────────────┘   └─────────────────────────┘    │
    └───────────────────────────────────────────────────────────┘
```

### Сервер

| Параметр | Значение |
|----------|----------|
| IP | 72.56.64.91 |
| SSH порт | 2222 |
| OS | Ubuntu 24.04.3 LTS |
| Kernel | Linux 6.8.0-88-generic |
| CPU | 2 vCPU (KVM) |
| RAM | 4 GB |
| Disk | 48 GB (использовано ~13 GB) |
| Хостинг | Timeweb Cloud |

### Порты

| Порт | Сервис | Описание |
|------|--------|----------|
| 2222 | SSH | Вход на сервер |
| 8000 | PROD | FastAPI webhook |
| 8002 | DEV | FastAPI API для Mini App |
| 51820 | WireGuard | VPN (wg0: 10.8.0.1/24) |

### Cloudflare Tunnels (Named)

| Туннель | UUID | Домен | Порт |
|---------|------|-------|------|
| rizalta-prod | 2d4a575c-883b-4361-9ee3-b3efe1a0847f | api.rizaltaservice.ru | 8000 |
| rizalta-dev | f77474f6-e2f6-40b6-bf3c-f23edf03cb72 | dev.rizaltaservice.ru | 8002 |

**Конфиги туннелей:**
- PROD: `/root/.cloudflared/config.yml`
- DEV: `/root/.cloudflared/config-dev.yml`

**Credentials:**
- PROD: `/root/.cloudflared/2d4a575c-883b-4361-9ee3-b3efe1a0847f.json`
- DEV: `/root/.cloudflared/f77474f6-e2f6-40b6-bf3c-f23edf03cb72.json`

### Telegram Webhook

```
URL: https://api.rizaltaservice.ru/telegram/webhook
IP: 188.114.96.0 (Cloudflare)
Max connections: 40
```

### Mini App Proxy (Vercel)

**Файл:** `/opt/miniapp/vercel.json`

```json
{
  "rewrites": [
    {"source": "/api-dev/:path*", "destination": "https://dev.rizaltaservice.ru/api/:path*"},
    {"source": "/api/:path*", "destination": "https://api.rizaltaservice.ru/api/:path*"}
  ]
}
```

**Зачем:** `*.trycloudflare.com` блокируется в РФ, Vercel — нет.

### Firewall (UFW)

```
51820/udp  ALLOW  — WireGuard VPN
2222/tcp   ALLOW  — SSH
```

⚠️ Порты 8000, 8002 НЕ открыты наружу — доступ только через Cloudflare Tunnel!

---

## 🖥️ SYSTEMD СЕРВИСЫ

### Список сервисов

| Сервис | Описание | Порт |
|--------|----------|------|
| rizalta-bot | PROD бот (webhook) | 8000 |
| rizalta-bot-dev | DEV бот (polling) | — |
| rizalta-dev-api | DEV API для Mini App | 8002 |
| cloudflare-rizalta | Туннель PROD | — |
| rizalta-dev-tunnel | Туннель DEV | — |
| rizalta-watchdog | Мониторинг и авторестарт | — |

### Конфиги сервисов

**PROD бот:** `/etc/systemd/system/rizalta-bot.service`
```ini
[Service]
WorkingDirectory=/opt/bot
ExecStart=/opt/bot/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
```

**DEV бот:** `/etc/systemd/system/rizalta-bot-dev.service`
```ini
[Service]
WorkingDirectory=/opt/bot-dev
ExecStart=/opt/bot-dev/venv/bin/python3 run_polling.py
Restart=always
```

**DEV API:** `/etc/systemd/system/rizalta-dev-api.service`
```ini
[Service]
WorkingDirectory=/opt/bot-dev
ExecStart=/opt/bot-dev/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8002
Restart=always
```

**Туннель PROD:** `/etc/systemd/system/cloudflare-rizalta.service`
```ini
[Service]
ExecStart=/usr/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
Restart=always
```

**Туннель DEV:** `/etc/systemd/system/rizalta-dev-tunnel.service`
```ini
[Service]
ExecStart=/usr/bin/cloudflared tunnel --config /root/.cloudflared/config-dev.yml run
Restart=always
After=rizalta-dev-api.service
```

**Watchdog:** `/etc/systemd/system/rizalta-watchdog.service`
```ini
[Service]
WorkingDirectory=/opt/bot
ExecStart=/opt/bot/venv/bin/python -m services.watchdog.watchdog
EnvironmentFile=/opt/bot/.env
Restart=always
```

### Команды управления

```bash
# Статус всех сервисов
systemctl status rizalta-bot rizalta-bot-dev rizalta-dev-api cloudflare-rizalta rizalta-dev-tunnel rizalta-watchdog

# Перезапуск
systemctl restart rizalta-bot          # PROD (осторожно!)
systemctl restart rizalta-bot-dev      # DEV
systemctl restart rizalta-dev-api      # DEV API
systemctl restart cloudflare-rizalta   # Туннель PROD
systemctl restart rizalta-dev-tunnel   # Туннель DEV

# Логи
journalctl -u rizalta-bot -f           # PROD
journalctl -u rizalta-bot-dev -f       # DEV
journalctl -u cloudflare-rizalta -f    # Туннель PROD

# Статус одной строкой
systemctl is-active rizalta-bot rizalta-bot-dev cloudflare-rizalta
```

---

## 🛡️ WATCHDOG (Мониторинг)

### Что мониторит

| Проверка | Интервал | Действие |
|----------|----------|----------|
| Сервисы systemd | 60 сек | Авторестарт + алерт |
| HTTP health | 60 сек | Алерт |
| RAM/CPU | 5 мин | Алерт при >80% |
| Диск | 1 час | Очистка + алерт при >80% |
| Биллинг Timeweb | 6 часов | Алерт при <500₽ |

### Конфигурация

**Файл:** `/opt/bot/services/watchdog/config.py`

```python
SERVICES = [
    "rizalta-bot",
    "rizalta-bot-dev", 
    "rizalta-dev-api",
    "cloudflare-rizalta",
    "rizalta-dev-tunnel",
]

HEALTH_ENDPOINTS = {
    "prod": "http://localhost:8000/",
    "dev": "http://localhost:8002/",
}

THRESHOLDS = {
    "ram_warning": 80,
    "ram_critical": 90,
    "disk_warning": 80,
    "disk_critical": 90,
}

AUTO_ACTIONS = {
    "restart_on_failure": True,
    "max_restarts": 3,
    "cooldown_minutes": 5,
}
```

### Алерты

Отправляются в Telegram: **Chat ID 512319063**

### Ручной запуск

```bash
# Одна проверка
cd /opt/bot && /opt/bot/venv/bin/python -m services.watchdog.watchdog --once

# Логи watchdog
journalctl -u rizalta-watchdog -f
```

---

## 📦 БЭКАПЫ

### Cron расписание

```bash
crontab -l
```

| Время | Задача | Скрипт |
|-------|--------|--------|
| 3:00 ежедневно | Бэкап БД + .env | `/opt/bot/backup.sh` |
| 4:00 воскресенье | Бэкап медиа | `/opt/bot/backup_weekly.sh` |
| 3:00 ежедневно | Парсинг PROD | `parser_rclick.py` |
| 6:00 ежедневно | Парсинг DEV | `parser_rclick.py` |
| */5 минут | Health check | `/opt/bot/health_check.sh` |

### Что бэкапится

**Ежедневный (`backup.sh`):**
- `.env` — секреты
- `properties.db` — БД лотов
- `data/` — JSON конфиги

**Еженедельный (`backup_weekly.sh`):**
- `kp_all/` — картинки КП
- `media/` — презентации

**Куда:** Email на `89181011091s@mail.ru`

### Ручной бэкап

```bash
/opt/bot/backup.sh
```

---

## 🚨 ИНЦИДЕНТЫ И РЕШЕНИЯ

### ИНЦИДЕНТ 1: PROD бот не отвечает

**Симптомы:** Бот не отвечает в Telegram, webhook не получает обновления

**Диагностика:**
```bash
# 1. Проверить сервис
systemctl status rizalta-bot

# 2. Проверить порт
ss -tlnp | grep 8000

# 3. Проверить health
curl -s http://localhost:8000/

# 4. Проверить туннель
systemctl status cloudflare-rizalta
cloudflared tunnel list

# 5. Проверить webhook
curl -s "https://api.telegram.org/bot$(grep TELEGRAM_BOT_TOKEN /opt/bot/.env | cut -d'=' -f2)/getWebhookInfo"
```

**Решения:**
```bash
# Перезапустить бота
systemctl restart rizalta-bot

# Перезапустить туннель
systemctl restart cloudflare-rizalta

# Переустановить webhook (если URL изменился)
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://api.rizaltaservice.ru/telegram/webhook"
```

---

### ИНЦИДЕНТ 2: Туннель Cloudflare упал

**Симптомы:** api.rizaltaservice.ru недоступен, 502/504 ошибки

**Диагностика:**
```bash
# Проверить статус
systemctl status cloudflare-rizalta
journalctl -u cloudflare-rizalta -n 50

# Проверить соединения
cloudflared tunnel list
```

**Решения:**
```bash
# Перезапустить туннель
systemctl restart cloudflare-rizalta

# Если не помогает — проверить credentials
ls -la /root/.cloudflared/
cat /root/.cloudflared/config.yml

# Пересоздать туннель (крайний случай)
cloudflared tunnel delete rizalta-prod
cloudflared tunnel create rizalta-prod
cloudflared tunnel route dns rizalta-prod api.rizaltaservice.ru
```

---

### ИНЦИДЕНТ 3: Mini App не работает

**Симптомы:** Шахматка/выбор лотов не загружается

**Диагностика:**
```bash
# 1. DEV API работает?
curl -s http://localhost:8002/
systemctl status rizalta-dev-api

# 2. DEV туннель работает?
systemctl status rizalta-dev-tunnel
curl -s https://dev.rizaltaservice.ru/

# 3. Vercel proxy настроен?
cat /opt/miniapp/vercel.json
```

**Решения:**
```bash
# Перезапустить DEV API
systemctl restart rizalta-dev-api

# Перезапустить туннель
systemctl restart rizalta-dev-tunnel

# Передеплоить Mini App (если изменился URL)
cd /opt/miniapp && vercel --prod
```

---

### ИНЦИДЕНТ 4: Ошибки в логах / бот падает

**Диагностика:**
```bash
# Смотреть логи
journalctl -u rizalta-bot -f
journalctl -u rizalta-bot -n 100 | grep -E "ERROR|Exception|Traceback"

# Проверить синтаксис
cd /opt/bot && python3 -c "import app; print('OK')"
```

**Частые ошибки:**

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ImportError: cannot import name` | Не скопирован `__init__.py` | `cp handlers/__init__.py` |
| `ModuleNotFoundError` | Не тот venv | `source venv/bin/activate` |
| `sqlite3.OperationalError: database is locked` | Параллельные записи | Включить WAL mode |
| `ConnectionError` | Нет интернета | Проверить DNS, сеть |

---

### ИНЦИДЕНТ 5: Диск заполнен

**Диагностика:**
```bash
df -h
du -sh /opt/bot/* | sort -h
du -sh /var/log/* | sort -h
```

**Решения:**
```bash
# Очистить логи
journalctl --vacuum-time=7d

# Очистить __pycache__
find /opt -name "__pycache__" -type d -exec rm -rf {} +

# Очистить старые бэкапы
rm -f /tmp/rizalta_backup_*.tar.gz
```

---

### ИНЦИДЕНТ 6: Память (RAM) заполнена

**Диагностика:**
```bash
free -h
ps aux --sort=-%mem | head -10
```

**Решения:**
```bash
# Перезапустить сервисы
systemctl restart rizalta-bot rizalta-bot-dev

# Очистить кеш (осторожно)
sync; echo 3 > /proc/sys/vm/drop_caches
```

---

### ИНЦИДЕНТ 7: Парсер не обновляет данные

**Диагностика:**
```bash
# Лог парсера
tail -50 /var/log/rizalta_parser.log

# Проверить сайт застройщика
curl -s -X POST "https://ri.rclick.ru/catalog/more/" -d "id=340&page=1" | head -100

# Проверить БД
sqlite3 /opt/bot/properties.db "SELECT COUNT(*) FROM units;"
```

**Решения:**
```bash
# Запустить вручную
cd /opt/bot && /opt/bot/venv/bin/python3 services/parser_rclick.py

# Проверить cron
crontab -l | grep parser
```

---

## 🔧 ДИАГНОСТИЧЕСКИЕ КОМАНДЫ

### Быстрая проверка всего

```bash
# Все сервисы одной командой
systemctl is-active rizalta-bot rizalta-bot-dev rizalta-dev-api cloudflare-rizalta rizalta-dev-tunnel rizalta-watchdog

# Порты
ss -tlnp | grep -E "8000|8002"

# Health check
curl -s http://localhost:8000/ && echo " PROD OK"
curl -s http://localhost:8002/ && echo " DEV OK"

# Диск и память
df -h / && free -h
```

### Полная диагностика

```bash
echo "=== SERVICES ===" && \
systemctl status rizalta-bot rizalta-bot-dev cloudflare-rizalta --no-pager | grep -E "Active:|●" && \
echo "=== PORTS ===" && \
ss -tlnp | grep -E "8000|8002" && \
echo "=== TUNNELS ===" && \
cloudflared tunnel list && \
echo "=== RESOURCES ===" && \
df -h / | tail -1 && free -h | grep Mem && \
echo "=== DB ===" && \
sqlite3 /opt/bot/properties.db "SELECT COUNT(*) || ' lots' FROM units;"
```

---

## 📁 СТРУКТУРА ПРОЕКТА

```
/opt/bot-dev/
├── app.py                      # Главный файл (роутинг, webhook, API)
├── run_polling.py              # DEV режим
├── properties.db               # БД лотов (350 записей)
├── secretary.db                # БД секретаря
│
├── config/
│   └── settings.py             # Константы, кнопки меню
│
├── data/
│   ├── installment_config.json # ⭐ ЕДИНЫЙ ИСТОЧНИК рассрочки
│   ├── units.json              # Данные лотов (legacy, для AI)
│   └── rizalta_finance.json    # Финансовые параметры
│
├── handlers/                   # Обработчики callback'ов
│   ├── kp.py                   # КП + навигация + пагинация
│   ├── calc_dynamic.py         # Расчёты ROI
│   ├── booking.py              # Онлайн-показы
│   ├── secretary.py            # AI-секретарь
│   └── ...
│
├── services/                   # Бизнес-логика
│   ├── installment_calculator.py  # ⭐ Расчёты рассрочки (SSOT)
│   ├── kp_pdf_generator.py     # PDF генератор КП
│   ├── units_db.py             # Работа с БД лотов
│   ├── parser_rclick.py        # Парсер сайта застройщика
│   ├── investment_calc.py      # Расчёты ROI
│   ├── intent_router.py        # GPT Intent Router
│   ├── watchdog/               # Мониторинг
│   └── ...
│
└── docs/                       # Документация
    ├── RIZALTA_CONTEXT.md
    ├── RIZALTA_CURRENT.md
    ├── RIZALTA_ARCHITECTURE.md
    ├── RIZALTA_KNOWLEDGE.md
    ├── RIZALTA_TASKS.md
    └── OLLAMA_RIZALTA.md       # Этот файл
```

---

## 🗄️ БАЗА ДАННЫХ

### properties.db — лоты недвижимости (350 записей)

```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY,
    code TEXT,              -- "В708", "А101"
    project TEXT DEFAULT 'Rizalta',
    building INTEGER,       -- 1 = Family, 2 = Business
    floor INTEGER,
    rooms INTEGER,
    area_m2 REAL,
    price_rub INTEGER,
    price_per_m2_rub INTEGER,
    completion TEXT,        -- срок сдачи
    layout_url TEXT,
    page_url TEXT,
    status TEXT DEFAULT 'available',
    block_section INTEGER,
    updated_at TIMESTAMP
);
```

**Полезные запросы:**
```bash
# Все лоты
sqlite3 /opt/bot-dev/properties.db "SELECT COUNT(*) FROM units;"

# Лоты по корпусу
sqlite3 /opt/bot-dev/properties.db "SELECT code, area_m2, price_rub FROM units WHERE building=1 LIMIT 10;"

# Найти по коду
sqlite3 /opt/bot-dev/properties.db "SELECT * FROM units WHERE code='В708';"

# Статистика цен
sqlite3 /opt/bot-dev/properties.db "SELECT MIN(price_rub), MAX(price_rub), AVG(price_rub) FROM units;"
```

---

## 📝 ТИПОВЫЕ ЗАДАЧИ С РЕШЕНИЯМИ

---

### ЗАДАЧА 1: Изменить параметры рассрочки

**Файл:** `/opt/bot-dev/data/installment_config.json`

**Структура конфига:**
```json
{
  "programs": {
    "12_months": {
      "duration_months": 12,
      "markup_percent": 0,
      "variants": [
        {"down_payment_percent": 30, "description": "12 равных платежей"},
        {"down_payment_percent": 40, "description": "11×200К + остаток"},
        {"down_payment_percent": 50, "description": "11×100К + остаток"}
      ]
    },
    "18_months": {
      "duration_months": 18,
      "variants": [
        {"down_payment_percent": 30, "markup_percent": 9},
        {"down_payment_percent": 40, "markup_percent": 7},
        {"down_payment_percent": 50, "markup_percent": 4}
      ]
    }
  }
}
```

**Шаги:**
1. Редактировать `/opt/bot-dev/data/installment_config.json`
2. Перезапустить: `systemctl restart rizalta-bot-dev`
3. Протестировать в @rizaltatestdevop_bot
4. Скопировать в PROD: `cp /opt/bot-dev/data/installment_config.json /opt/bot/data/`
5. Перезапустить PROD: `systemctl restart rizalta-bot`

---

### ЗАДАЧА 2: Добавить лот в Custom Installment (спец-условия)

**Файл:** `/opt/bot-dev/services/kp_pdf_generator.py`

**Найти:**
```python
CUSTOM_INSTALLMENT_UNITS = ['В615', 'В527', 'В517', 'В617', 'В525', 'В625', 'А101']
```

**Добавить код лота в список.**

**Быстрая команда:**
```bash
sed -i "s/CUSTOM_INSTALLMENT_UNITS = \[/CUSTOM_INSTALLMENT_UNITS = ['В700', /" /opt/bot-dev/services/kp_pdf_generator.py
```

---

### ЗАДАЧА 3: Обновить (спарсить) базу данных лотов

```bash
# DEV
cd /opt/bot-dev && python3 services/parser_rclick.py

# PROD
cd /opt/bot && /opt/bot/venv/bin/python3 services/parser_rclick.py

# Проверка
sqlite3 /opt/bot/properties.db "SELECT COUNT(*) FROM units;"
```

---

### ЗАДАЧА 4: Закрыть/открыть лот из доступа

```bash
# Закрыть лот
sqlite3 /opt/bot-dev/properties.db "UPDATE units SET status='sold' WHERE code='В708';"

# Открыть лот
sqlite3 /opt/bot-dev/properties.db "UPDATE units SET status='available' WHERE code='В708';"
```

---

### ЗАДАЧА 5: Изменить дизайн PDF КП

**Файл:** `/opt/bot-dev/services/kp_pdf_generator.py`

**Тестирование:**
```bash
cd /opt/bot-dev && source venv/bin/activate
python3 -c "
from services.kp_pdf_generator import generate_kp_pdf
path = generate_kp_pdf(code='В101', include_18m=True, output_dir='/tmp')
print(f'PDF создан: {path}')
"
```

---

### ЗАДАЧА 6: Изменить расчёты ROI

**Файл:** `/opt/bot-dev/services/investment_calc.py`

**Ключевые параметры:**
```python
ANNUAL_YIELD = 0.12      # 12% годовых
OCCUPANCY_RATE = 0.75    # 75% заполняемость
MANAGEMENT_FEE = 0.20    # 20% УК
TAX_RATE = 0.06          # 6% налог
```

---

## 🚀 ДЕПЛОЙ DEV → PROD

### Чеклист

```bash
# 1. Тест в DEV
systemctl restart rizalta-bot-dev
# Проверить в @rizaltatestdevop_bot

# 2. Коммит DEV
cd /opt/bot-dev
git add -A && git commit -m "v2.4.x: описание" && git push

# 3. Копировать файлы
cp /opt/bot-dev/ФАЙЛ /opt/bot/ФАЙЛ

# 4. Проверить синтаксис
cd /opt/bot && python3 -c "import app; print('OK')"

# 5. Перезапустить PROD
systemctl restart rizalta-bot

# 6. Проверить логи
journalctl -u rizalta-bot -f

# 7. Тест в PROD — проверить в @RealtMeAI_bot

# 8. Коммит PROD
cd /opt/bot
git add -A && git commit -m "v2.4.x: описание" && git push
```

### ⚠️ ВАЖНО: Mini App URL

После копирования `app.py`:
```bash
# PROD должен быть БЕЗ ?env=dev
grep "rizalta-miniapp" /opt/bot/app.py

# Если есть ?env=dev — исправить:
sed -i 's|https://rizalta-miniapp.vercel.app?env=dev|https://rizalta-miniapp.vercel.app|' /opt/bot/app.py
```

---

## 🔄 ОБНОВЛЕНИЕ ЭТОГО ФАЙЛА

При решении новой задачи — добавь её в раздел "ТИПОВЫЕ ЗАДАЧИ" или "ИНЦИДЕНТЫ".

---

*Последнее обновление: 16.01.2026*
*Версия контекста: 1.1.0*

---

### ЗАДАЧА 8: ROI/Excel для лотов с одинаковым кодом в разных корпусах

**Дата:** 17.01.2026

**Проблема:** Некоторые лоты имеют одинаковый код (например А509), но находятся в разных корпусах с разной площадью и ценой. При вызове ROI или Excel из карточки лота брались данные первого найденного лота, а не того что выбрал пользователь.

**Пример:**
- А509 Корпус 1: 42.8 м², 26 964 000 ₽
- А509 Корпус 2: 24.5 м², 15 925 000 ₽

**Файлы:**
- `handlers/kp.py` — формирование callback'ов
- `handlers/calc_dynamic.py` — обработка ROI/Finance
- `app.py` — парсинг callback'ов
- `services/calc_xlsx_generator.py` — генерация Excel

**Решение:**

1. **Изменить callback'и** — добавить building:
```python
# Было:
f"calc_roi_code_{lot['code']}"

# Стало:
f"calc_roi_code_{lot['code']}_{lot['building']}"
```

2. **Парсить building в app.py:**
```python
# Было:
code = data.replace("calc_roi_code_", "")

# Стало:
parts = data.replace("calc_roi_code_", "").rsplit("_", 1)
code, building = parts[0], int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
```

3. **Передавать building в функции:**
```python
# handlers/calc_dynamic.py
async def handle_calc_roi_by_code(chat_id: int, code: str, building: int = None):
    lot = get_lot_by_code(code, building)

# services/calc_xlsx_generator.py
def generate_roi_xlsx(unit_code: str = None, area: float = None, output_dir: str = None, building: int = None):
    lot = get_lot_from_db(unit_code, building)
```

**Затронутые callback'и:**
- `calc_roi_code_` — расчёт ROI
- `calc_finance_code_` — варианты оплаты  
- `roi_xlsx_code_` — Excel файл
- `compare_lot_` — сравнение с депозитом

**Проверка:**
```bash
sqlite3 /opt/bot-dev/properties.db "SELECT code, building, area_m2, price_rub FROM units WHERE code LIKE '%509%';"
```

**Тест:**
1. Найти А509 → выбрать Корпус 2 (24.5 м²)
2. Нажать "📊 Расчёт доходности"
3. Нажать "📥 Excel"
4. В Excel должно быть 24.5 м², 15 925 000 ₽
