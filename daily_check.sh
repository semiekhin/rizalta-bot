#!/bin/bash
# Ежедневная проверка системы RIZALTA

echo "========================================"
echo "🔍 RIZALTA — Ежедневная проверка"
echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

echo ""
echo "=== 1. СТАТУС СЕРВИСОВ ==="
for svc in rizalta-bot rizalta-bot-dev oazis-bot sofia-bot; do
    status=$(systemctl is-active $svc 2>/dev/null || echo "не найден")
    if [ "$status" = "active" ]; then
        echo "✅ $svc: работает"
    else
        echo "❌ $svc: $status"
    fi
done

echo ""
echo "=== 2. РЕСУРСЫ СЕРВЕРА ==="
# CPU
cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs)
echo "📊 CPU нагрузка: $cpu_load"

# RAM
ram_info=$(free -h | grep Mem | awk '{print "Использовано: "$3" / "$2" ("$3/$2*100"%)" }')
ram_pct=$(free | grep Mem | awk '{printf "%.0f", $3/$2*100}')
if [ "$ram_pct" -lt 80 ]; then
    echo "✅ RAM: $(free -h | grep Mem | awk '{print $3"/"$2}')"
else
    echo "⚠️ RAM: $(free -h | grep Mem | awk '{print $3"/"$2}') (>80%!)"
fi

# Disk
disk_pct=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$disk_pct" -lt 80 ]; then
    echo "✅ Диск: ${disk_pct}% использовано"
else
    echo "⚠️ Диск: ${disk_pct}% использовано (>80%!)"
fi

echo ""
echo "=== 3. СЕТЕВАЯ ДОСТУПНОСТЬ ==="
for host in api.telegram.org api.openai.com; do
    if ping -c 1 -W 2 $host &>/dev/null; then
        echo "✅ $host — доступен"
    else
        echo "❌ $host — недоступен!"
    fi
done

echo ""
echo "=== 4. БЕЗОПАСНОСТЬ ==="
# Fail2ban
banned=$(fail2ban-client status sshd 2>/dev/null | grep "Currently banned" | awk '{print $NF}')
total_banned=$(fail2ban-client status sshd 2>/dev/null | grep "Total banned" | awk '{print $NF}')
echo "🛡️ Fail2ban: заблокировано сейчас: ${banned:-0}, всего: ${total_banned:-0}"

# Последние входы
echo "👤 Последние входы:"
last -3 | head -3

# Неудачные попытки за сегодня
failed_today=$(grep -c "Failed password" /var/log/auth.log 2>/dev/null || echo "0")
echo "🚫 Неудачных попыток входа сегодня: $failed_today"

echo ""
echo "=== 5. БЭКАПЫ ==="
last_backup=$(ls -t /tmp/rizalta_backup_*.tar.gz 2>/dev/null | head -1)
if [ -n "$last_backup" ]; then
    backup_date=$(stat -c %y "$last_backup" | cut -d' ' -f1)
    backup_size=$(du -h "$last_backup" | cut -f1)
    echo "📦 Последний бэкап: $backup_date ($backup_size)"
else
    echo "⚠️ Бэкап не найден в /tmp"
fi

# Лог бэкапов
last_backup_log=$(tail -5 /var/log/backup.log 2>/dev/null | grep -E "✅|❌" | tail -1)
echo "📋 Лог: $last_backup_log"

echo ""
echo "=== 6. ОШИБКИ В ЛОГАХ (последний час) ==="
errors=$(journalctl -u rizalta-bot --since "1 hour ago" 2>/dev/null | grep -iE "error|exception|fail" | wc -l)
if [ "$errors" -eq 0 ]; then
    echo "✅ Ошибок нет"
else
    echo "⚠️ Найдено ошибок: $errors"
    journalctl -u rizalta-bot --since "1 hour ago" 2>/dev/null | grep -iE "error|exception|fail" | tail -3
fi

echo ""
echo "=== 7. CLOUDFLARE TUNNEL ==="
cf_count=$(ps aux | grep cloudflared | grep -v grep | wc -l)
echo "🌐 Процессов cloudflared: $cf_count"

echo ""
echo "=== 8. БАЗА ДАННЫХ ==="
if [ -f /opt/bot/properties.db ]; then
    db_date=$(stat -c %y /opt/bot/properties.db | cut -d' ' -f1)
    units_count=$(sqlite3 /opt/bot/properties.db "SELECT COUNT(*) FROM units" 2>/dev/null || echo "?")
    echo "🏠 properties.db: $units_count лотов, обновлено: $db_date"
else
    echo "❌ properties.db не найден"
fi

echo ""
echo "========================================"
echo "✅ Проверка завершена"
echo "========================================"
