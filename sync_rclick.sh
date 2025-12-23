#!/bin/bash
# sync_rclick.sh — Автосинхронизация базы данных с ri.rclick.ru
# Запускать через cron раз в день

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/rizalta-sync.log"
LOCK_FILE="/tmp/rizalta-sync.lock"

# Проверка на дублирующий запуск
if [ -f "$LOCK_FILE" ]; then
    echo "$(date): Sync already running, skipping" >> "$LOG_FILE"
    exit 0
fi

touch "$LOCK_FILE"

echo "========================================" >> "$LOG_FILE"
echo "$(date): Starting sync" >> "$LOG_FILE"

# Синхронизация DEV
cd /opt/bot-dev
source venv/bin/activate
python3 services/parser_rclick.py >> "$LOG_FILE" 2>&1
DEV_COUNT=$(sqlite3 properties.db "SELECT COUNT(*) FROM units;")
echo "$(date): DEV synced: $DEV_COUNT lots" >> "$LOG_FILE"

# Синхронизация PROD (копируем базу из DEV)
cp /opt/bot-dev/properties.db /opt/bot/properties.db
echo "$(date): PROD database updated from DEV" >> "$LOG_FILE"

# Перезапуск ботов для применения новых данных
systemctl restart rizalta-bot-dev
systemctl restart rizalta-bot

echo "$(date): Bots restarted" >> "$LOG_FILE"
echo "$(date): Sync completed successfully" >> "$LOG_FILE"

rm -f "$LOCK_FILE"
