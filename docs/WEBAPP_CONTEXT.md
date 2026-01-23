# ⚠️ PROD/DEV НЕ ТРОГАТЬ! РАБОТАЕМ ТОЛЬКО В /opt/webapp/ ⚠️

# RIZALTA Web App v0.1.0
Standalone веб-приложение — fallback если Telegram упадёт.

## Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91`
- **WebApp:** `/opt/webapp` (отдельно от бота!)
- **Frontend:** React + Vite + Tailwind → порт 5173/5174
- **Backend:** FastAPI → порт 8003
- **PROD бот:** `/opt/bot` (НЕ ТРОГАТЬ)
- **DEV бот:** `/opt/bot-dev` (НЕ ТРОГАТЬ)

## Запуск
```bash
# Backend
cd /opt/webapp/backend && source /opt/webapp/venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8003 &

# Frontend  
cd /opt/webapp/frontend && npm run dev -- --host 0.0.0.0 --port 5173 &
```

## Структура
```
/opt/webapp/
├── frontend/src/
│   ├── App.jsx          # Роутинг, навигация
│   └── pages/
│       ├── Home.jsx     # Лендинг ✅
│       ├── Catalog.jsx  # Шахматка ✅
│       ├── LotDetail.jsx # Детали лота ✅
│       └── Chat.jsx     # AI чат (заглушка) ✅
├── backend/
│   └── app.py           # FastAPI, проксирует к PROD API
└── venv/
```

## Данные
- Читает из PROD: `GET https://api.rizaltaservice.ru/api/lots`
- 356 лотов, статистика available/booked/sold

## 📅 Сессия 23.01.2026
✅ Создана структура /opt/webapp/
✅ Backend FastAPI на :8003 (проксирует lots)
✅ Frontend React+Vite+Tailwind
✅ 4 страницы: Home, Catalog, LotDetail, Chat
✅ Mobile-first дизайн
✅ Git init, v0.1.0

## 🔜 Следующие задачи
1. Systemd сервисы (webapp-backend, webapp-frontend)
2. Cloudflare туннель → app.rizaltaservice.ru
3. GPT интеграция в чат
4. Авторизация (телефон + SMS)
5. Генерация КП (скопировать из /opt/bot/services/)
6. Production build фронтенда

## Команды
```bash
# Проверить бэкенд
curl http://localhost:8003/api/lots | jq '.stats'

# Остановить процессы
pkill -f "uvicorn.*8003"
pkill -f "vite"
```
