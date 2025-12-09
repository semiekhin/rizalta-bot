#!/bin/bash
# ============================================
# RIZALTA BOT — Настройка DEV-окружения
# ============================================

set -e

PROD_DIR="/opt/bot"
DEV_DIR="/opt/bot-dev"
DEV_SERVICE="rizalta-bot-dev"

echo "🚀 Создание DEV-версии RIZALTA Bot"
echo "=================================="

# 1. Проверяем существование prod
if [ ! -d "$PROD_DIR" ]; then
    echo "❌ Prod-директория не найдена: $PROD_DIR"
    exit 1
fi

# 2. Останавливаем dev если уже есть
if systemctl is-active --quiet $DEV_SERVICE 2>/dev/null; then
    echo "⏹ Останавливаем существующий dev-сервис..."
    systemctl stop $DEV_SERVICE
fi

# 3. Удаляем старую dev-версию если есть
if [ -d "$DEV_DIR" ]; then
    echo "🗑 Удаляем старую dev-версию..."
    rm -rf "$DEV_DIR"
fi

# 4. Копируем prod → dev
echo "📦 Копируем $PROD_DIR → $DEV_DIR..."
cp -r "$PROD_DIR" "$DEV_DIR"

# 5. Создаём systemd сервис для dev
echo "⚙️ Создаём systemd сервис..."
cat > /etc/systemd/system/$DEV_SERVICE.service << 'EOF'
[Unit]
Description=RIZALTA Bot DEV
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bot-dev
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 6. Перезагружаем systemd
systemctl daemon-reload

# 7. Показываем структуру
echo ""
echo "📁 Структура DEV-версии:"
ls -la "$DEV_DIR"

echo ""
echo "============================================"
echo "✅ DEV-окружение готово!"
echo ""
echo "⚠️ ВАЖНО: Для запуска dev-бота нужен ОТДЕЛЬНЫЙ"
echo "   Telegram токен, иначе будет конфликт с prod!"
echo "============================================"
