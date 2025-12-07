# RIZALTA BOT — Полная инструкция по деплою

## Сервер

| Параметр | Значение |
|----------|----------|
| Хостинг | Timeweb Cloud |
| Тариф | Cloud NL-50 |
| IP | 72.56.64.91 |
| ОС | Ubuntu 24.04 |
| CPU | 2 x 3.3 ГГц |
| RAM | 4 GB |
| Диск | 50 GB NVMe |
| Сеть | 1 Гбит/с |
| SSH | `ssh root@72.56.64.91` |

---

## Структура на сервере

```
/opt/bot/           # RIZALTA Bot (порт 8000)
/opt/oazis/         # OAZIS Bot (порт 8001)
/var/log/           # Логи
/swapfile           # Swap 1GB
```

---

## Переменные окружения (.env)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=8343378629:AAHHacgXmIVhShhtPtdEooKEkV34ZD1t59s

# OpenAI
OPENAI_API_KEY=sk-proj-... (получить у владельца)

# Email уведомления
MANAGER_EMAIL=89181011091s@mail.ru
BOT_EMAIL=rizalta-bot@mail.ru
SMTP_HOST=smtp.mail.ru
SMTP_PORT=587
SMTP_USER=rizalta-bot@mail.ru
SMTP_PASSWORD=3QZURbnlnb7ga25PGBc7
```

---

## Systemd сервисы

### /etc/systemd/system/rizalta-bot.service

```ini
[Unit]
Description=RIZALTA Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bot
ExecStart=/opt/bot/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### /etc/systemd/system/cloudflare-rizalta.service

```ini
[Unit]
Description=Cloudflare Tunnel for RIZALTA
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/cloudflared tunnel --url http://127.0.0.1:8000
ExecStartPost=/opt/bot/update_webhook.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### /etc/systemd/system/oazis-bot.service

```ini
[Unit]
Description=OAZIS Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/oazis
ExecStart=/opt/oazis/venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### /etc/systemd/system/cloudflare-oazis.service

```ini
[Unit]
Description=Cloudflare Tunnel for OAZIS
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/cloudflared tunnel --url http://127.0.0.1:8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Команды управления

```bash
# Включить автозапуск
systemctl enable rizalta-bot cloudflare-rizalta

# Запуск/остановка/перезапуск
systemctl start rizalta-bot
systemctl stop rizalta-bot
systemctl restart rizalta-bot

# Статус
systemctl status rizalta-bot --no-pager

# Логи
journalctl -u rizalta-bot -f
```

---

## Crontab (автобэкапы)

```bash
# Редактировать: crontab -e
0 3 * * * /opt/bot/backup.sh >> /var/log/backup.log 2>&1
0 4 * * 0 /opt/bot/backup_weekly.sh >> /var/log/backup.log 2>&1
```

| Задача | Расписание | Содержимое |
|--------|------------|------------|
| Ежедневный | 3:00 UTC | .env, properties.db, data/ |
| Еженедельный | Вс 4:00 UTC | kp_all/, media/ |

Email получателя: 89181011091s@mail.ru

---

## Cloudflare Tunnel

Cloudflare Tunnel создаёт безопасный туннель без открытия портов:

```
Telegram → Cloudflare → localhost:8000 → Бот
```

При каждом запуске генерируется новый URL (xxx.trycloudflare.com).
Скрипт `/opt/bot/update_webhook.sh` автоматически обновляет webhook.

### Установка cloudflared

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/bin/cloudflared
chmod +x /usr/bin/cloudflared
```

---

## База данных (SQLite)

Файл: `/opt/bot/properties.db`

### Таблица bookings

```sql
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    username TEXT,
    specialist_id INTEGER NOT NULL,
    specialist_name TEXT NOT NULL,
    booking_date TEXT NOT NULL,      -- '2025-12-09'
    booking_time TEXT NOT NULL,      -- '14:00'
    status TEXT DEFAULT 'pending',   -- pending/confirmed/declined
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Swap (защита от OOM)

```bash
# Создание
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Автомонтирование (добавить в /etc/fstab)
/swapfile none swap sw 0 0
```

---

## fail2ban (защита от брутфорса)

```bash
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Проверка забаненных IP
fail2ban-client status sshd
```

---

## Деплой с нуля

### 1. Подготовка сервера

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl fail2ban

# Swap
fallocate -l 1G /swapfile && chmod 600 /swapfile
mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/bin/cloudflared
chmod +x /usr/bin/cloudflared
```

### 2. Клонирование репозитория

```bash
cd /opt
git clone git@github.com:semiekhin/rizalta-bot.git bot
cd bot
```

### 3. Виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Конфигурация

```bash
# Создать .env из примера
cp .env.example .env
nano .env  # заполнить токены
```

### 5. Восстановление данных из бэкапа

```bash
# Скачать бэкап из email
# Распаковать в /opt/bot/
tar -xzf backup_daily_*.tar.gz -C /opt/bot/
tar -xzf backup_weekly_*.tar.gz -C /opt/bot/
```

### 6. Systemd сервисы

```bash
# Скопировать unit файлы (см. выше)
nano /etc/systemd/system/rizalta-bot.service
nano /etc/systemd/system/cloudflare-rizalta.service

systemctl daemon-reload
systemctl enable rizalta-bot cloudflare-rizalta
systemctl start rizalta-bot cloudflare-rizalta
```

### 7. Crontab

```bash
crontab -e
# Добавить строки бэкапов (см. выше)
```

### 8. Проверка

```bash
systemctl status rizalta-bot --no-pager
journalctl -u rizalta-bot -f
# Написать боту в Telegram
```

---

## Специалисты (календарь бронирования)

Файл: `/opt/bot/handlers/booking_calendar.py`

```python
SPECIALISTS = [
    {"id": 1, "name": "Специалист 1", "telegram_id": 512319063, "email": "89181011091s@mail.ru"},
    {"id": 2, "name": "Специалист 2", "telegram_id": 512319063, "email": "89181011091s@mail.ru"},
    {"id": 3, "name": "Специалист 3", "telegram_id": 512319063, "email": "89181011091s@mail.ru"},
]
```

⚠️ Нужно заменить на реальные данные специалистов!

---

## Порты

| Сервис | Порт |
|--------|------|
| RIZALTA Bot | 8000 |
| OAZIS Bot | 8001 |
| SSH | 22 |

---

## Контакты

| Что | Значение |
|-----|----------|
| Email бэкапов | 89181011091s@mail.ru |
| Email бота | rizalta-bot@mail.ru |
| Telegram бот | @RealtMeAI_bot |
| GitHub | https://github.com/semiekhin/rizalta-bot |
