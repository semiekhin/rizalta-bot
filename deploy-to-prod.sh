#!/bin/bash
set -e

DEV_PORT=8004
PROD_PORT=8003
PROD_DIR="/opt/webapp"
BRANCH="webapp"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}✓ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }

echo "=== RIZALTA WebApp: Deploy DEV → PROD ==="
echo ""

# 1. Проверить DEV
echo "→ Checking DEV health..."
DEV_HEALTH=$(curl -sf http://127.0.0.1:$DEV_PORT/api/health 2>/dev/null) || fail "DEV is not healthy!"
DEV_VER=$(echo "$DEV_HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
log "DEV healthy (v${DEV_VER})"

# 2. Проверить PROD до деплоя
PROD_HEALTH=$(curl -sf http://127.0.0.1:$PROD_PORT/api/health 2>/dev/null) || warn "PROD not responding (will deploy anyway)"
PROD_VER=$(echo "$PROD_HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "unknown")
echo "   PROD current: v${PROD_VER}"

if [ "$DEV_VER" = "$PROD_VER" ]; then
    warn "Versions match — nothing to deploy?"
    read -p "   Continue anyway? (y/N): " confirm
    [ "$confirm" = "y" ] || exit 0
fi

# 3. Сохранить точку отката
cd "$PROD_DIR"
ROLLBACK_HASH=$(git rev-parse HEAD)
log "Rollback point: ${ROLLBACK_HASH:0:8}"

# 4. Git pull
echo "→ git pull..."
git pull origin "$BRANCH" || fail "git pull failed"
log "git pull ok"

# 5. Build frontend
echo "→ npm build..."
npm run build --prefix frontend || {
    warn "Build failed — rolling back"
    git reset --hard "$ROLLBACK_HASH"
    fail "Deploy aborted (rolled back)"
}
log "npm build ok"

# 6. Restart
echo "→ restarting webapp..."
systemctl restart webapp || fail "restart failed"
sleep 2

# 7. Health check
NEW_HEALTH=$(curl -sf http://127.0.0.1:$PROD_PORT/api/health 2>/dev/null) || {
    warn "PROD not healthy after deploy — rolling back!"
    git reset --hard "$ROLLBACK_HASH"
    npm run build --prefix frontend
    systemctl restart webapp
    fail "Deploy failed — rolled back to ${ROLLBACK_HASH:0:8}"
}
NEW_VER=$(echo "$NEW_HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null)

echo ""
echo "=== Deploy complete ==="
log "PROD: v${PROD_VER} → v${NEW_VER}"
