#!/bin/bash
set -e
echo "=== SESSION END ==="

# 1. Webapp
echo "[1/3] Webapp..."
cd /opt/webapp-dev
git add -A
git status --short
read -p "Commit message: " MSG
git commit -m "$MSG" && git push origin webapp

# 2. Bot-dev docs
echo "[2/3] Bot-dev docs..."
cd /opt/bot-dev
git add docs/
if git diff --cached --quiet; then
  echo "  No doc changes in bot-dev"
else
  git commit -m "docs: $MSG" && git push
fi

# 3. Copy to PROD + push
echo "[3/3] PROD docs..."
cp /opt/bot-dev/docs/RIZALTA_CURRENT.md /opt/bot/docs/
cp /opt/bot-dev/docs/RIZALTA_TASKS.md /opt/bot/docs/
cp /opt/bot-dev/docs/RIZALTA_CONTEXT.md /opt/bot/docs/
cd /opt/bot
git add docs/
if git diff --cached --quiet; then
  echo "  No doc changes in PROD"
else
  git commit -m "docs: $MSG" && git push
fi

sudo systemctl restart webapp-dev.service
echo "=== DONE ==="
echo "Не забудь: промпт для нового чата!"
