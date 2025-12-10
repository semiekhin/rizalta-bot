# Восстановление RIZALTA Bot с нуля

## 1. Клонирование
```bash
cd /opt
git clone git@github.com:semiekhin/rizalta-bot.git bot
cd /opt/bot
```

## 2. Виртуальное окружение
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install
```

## 3. База данных
```bash
python3 services/parser_rclick.py
```

## 4. Файл .env
```bash
cat > .env << 'ENVEOF'
TELEGRAM_BOT_TOKEN=<получить у @BotFather>
OPENAI_API_KEY=<получить на platform.openai.com>
VECTOR_STORE_ID=<из OpenAI Assistants>
ASSISTANT_ID=<из OpenAI Assistants>
ENVEOF
```

**Секреты хранятся отдельно — запросить у владельца проекта**

## 5. Systemd сервис
```bash
cat > /etc/systemd/system/rizalta-bot.service << 'SVCEOF'
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
SVCEOF

systemctl daemon-reload
systemctl enable rizalta-bot
systemctl start rizalta-bot
```

## 6. Webhook
```bash
chmod +x update_webhook.sh
./update_webhook.sh
```

## 7. Cron задачи
```bash
crontab -e
# Добавить:
0 3 * * * /opt/bot/backup.sh >> /var/log/backup.log 2>&1
0 4 * * 0 /opt/bot/backup_weekly.sh >> /var/log/backup.log 2>&1
0 3 * * * cd /opt/bot && /opt/bot/venv/bin/python3 services/parser_rclick.py >> /var/log/rizalta_parser.log 2>&1
```

## 8. Проверка
```bash
systemctl status rizalta-bot
```
