#!/bin/bash
# Проверка работы ботов и уведомление в Telegram

BOT_TOKEN="8343378629:AAE4OlxArGXPpju0oEzk19Wmp4ofummP788"
CHAT_ID="512319063"  # Твой Telegram ID

# Проверяем prod
if ! systemctl is-active --quiet rizalta-bot; then
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=🚨 RIZALTA PROD бот упал! Проверь: ssh -p 2222 root@72.56.64.91" > /dev/null
fi

# Проверяем dev
if ! systemctl is-active --quiet rizalta-bot-dev; then
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=⚠️ RIZALTA DEV бот упал!" > /dev/null
fi

# Проверяем MAX
if ! systemctl is-active --quiet rizalta-bot-max; then
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=🚨 RIZALTA MAX бот упал! Проверь: ssh -p 2222 root@72.56.64.91" > /dev/null
fi
