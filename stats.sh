#!/bin/bash
DATE_FMT=$(date +%d/%b/%Y)
DATE_RUS=$(date +%d.%m.%Y)

users=$(journalctl -u rizalta-bot --since today --no-pager | grep -oP "'id': \d+" | sort -u | wc -l)
bot=$(journalctl -u rizalta-bot --since today --no-pager | grep -c "WEBHOOK")
mini=$(grep "$DATE_FMT" /var/log/nginx/access.log 2>/dev/null | grep -c 'miniapp-action\|/api/lots\|/api/lot')
web=$(grep "$DATE_FMT" /var/log/nginx/access.log 2>/dev/null | grep -c 'webapp\|8003\|8004')
health=$(grep "$DATE_FMT" /var/log/nginx/access.log 2>/dev/null | grep -c 'health\|GET / \|HEAD')
scanners=$(grep "$DATE_FMT" /var/log/nginx/access.log 2>/dev/null | grep -c '\.env')

echo "📊 Статистика RIZALTA за $DATE_RUS"
echo "---"
echo "👥 Уникальных пользователей: $users"
echo "🤖 Бот (webhook): $bot"
echo "📱 Mini App: $mini"
echo "🌐 WebApp: $web"
echo "🏥 Health checks: $health"
echo "⚠️ Сканеры (.env): $scanners"
echo "---"
echo "📈 Полезная нагрузка: $((bot + mini + web))"
