# ⚠️ PROD/DEV НЕ ТРОГАТЬ! РАБОТАЕМ ТОЛЬКО В /opt/webapp/ ⚠️

# RIZALTA Web App v0.1.0
Standalone веб-приложение — fallback если Telegram упадёт.

## Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91`
- **WebApp:** `/opt/webapp` (отдельно от бота!)
- **Frontend:** React + Vite + Tailwind (build в /frontend/dist/)
- **Backend:** FastAPI → порт 8003
- **PROD бот:** `/opt/bot` (НЕ ТРОГАТЬ)
- **DEV бот:** `/opt/bot-dev` (НЕ ТРОГАТЬ)

## Текущий статус (23.01.2026)
✅ Frontend: 4 страницы готовы (Home, Catalog, LotDetail, Chat)
✅ Backend: FastAPI проксирует /api/lots к PROD
✅ Production build: /opt/webapp/frontend/dist/
✅ Туннель создан: 2ff508f2-9445-43ac-ab0b-4e0b38d487a0
✅ DNS: webapp.rizaltaservice.ru

⚠️ ПРОБЛЕМА: ERR_HTTP2_PING_FAILED при загрузке JS/CSS через Cloudflare туннель
- Локально всё работает (curl возвращает 200)
- Через туннель файлы зависают (pending) или failed
- Возможно проблема с HTTP/2 или таймаутами Cloudflare

## Структура
```
/opt/webapp/
├── frontend/
│   ├── src/pages/       # Home, Catalog, LotDetail, Chat
│   ├── dist/            # Production build
│   └── vite.config.js
├── backend/
│   └── app.py           # FastAPI + статика
├── venv/
└── docs/
```

## Файлы конфигурации
- /root/.cloudflared/config-webapp.yml
- Tunnel ID: 2ff508f2-9445-43ac-ab0b-4e0b38d487a0

## Запуск (локальная проверка)
```bash
# Backend
cd /opt/webapp/backend && source /opt/webapp/venv/bin/activate
python3 -m uvicorn app:app --host 127.0.0.1 --port 8003 &

# Проверка
curl http://127.0.0.1:8003/              # HTML
curl http://127.0.0.1:8003/api/lots      # JSON с лотами
curl http://127.0.0.1:8003/assets/index-Rq8kIgpV.js | head -5  # JS
```

## 🔜 Следующая задача
Решить проблему с Cloudflare туннелем:
1. Попробовать nginx как reverse proxy
2. Или использовать Vercel для фронтенда (как Mini App)
3. Или другой способ раздачи статики

## Команды
```bash
# Остановить процессы
pkill -f "uvicorn.*8003"
pkill -f "config-webapp"

# Логи
cat /tmp/webapp-backend.log
cat /tmp/tunnel-webapp.log
```
