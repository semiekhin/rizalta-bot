#!/bin/bash
# ============================================
# RIZALTA BOT — Анализ источников данных
# ============================================

BOT_DIR="${1:-/opt/bot-dev}"

echo "🔍 АНАЛИЗ ДАННЫХ RIZALTA BOT"
echo "Директория: $BOT_DIR"
echo "============================================"

# 1. properties.db
echo ""
echo "📦 1. PROPERTIES.DB"
echo "-------------------"
DB_PATH="$BOT_DIR/properties.db"
if [ -f "$DB_PATH" ]; then
    echo "✅ Найдена: $DB_PATH"
    echo "Количество лотов:"
    sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM units;"
    echo ""
    echo "Примеры (первые 5):"
    sqlite3 -header -column "$DB_PATH" "SELECT code, floor, area_m2, price_rub FROM units LIMIT 5;"
    echo ""
    echo "Диапазон цен:"
    sqlite3 "$DB_PATH" "SELECT MIN(price_rub), MAX(price_rub) FROM units;"
else
    echo "❌ Не найдена"
    find "$BOT_DIR" -name "*.db" 2>/dev/null
fi

# 2. rizalta_finance.json
echo ""
echo "📦 2. RIZALTA_FINANCE.JSON"
echo "--------------------------"
FINANCE_PATH="$BOT_DIR/data/rizalta_finance.json"
if [ -f "$FINANCE_PATH" ]; then
    echo "✅ Найден"
    cat "$FINANCE_PATH" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for u in data.get('units', []):
    print(f\"  {u.get('unit_code')}: {u.get('price_rub'):,} руб\")
"
else
    echo "❌ Не найден"
fi

# 3. units.json
echo ""
echo "📦 3. UNITS.JSON"
echo "----------------"
UNITS_PATH="$BOT_DIR/data/units.json"
if [ -f "$UNITS_PATH" ]; then
    echo "✅ Найден"
    echo "Размер: $(wc -l < "$UNITS_PATH") строк"
else
    echo "❌ Не найден"
fi

# 4. КП
echo ""
echo "📦 4. ПАПКА КП (kp_all)"
echo "-----------------------"
KP_DIR="$BOT_DIR/kp_all"
if [ -d "$KP_DIR" ]; then
    echo "✅ Найдена"
    echo "Файлов: $(ls "$KP_DIR"/*.jpg 2>/dev/null | wc -l)"
else
    echo "❌ Не найдена"
fi

echo ""
echo "============================================"
echo "✅ Анализ завершён"
