# RIZALTA Web App

Standalone веб-приложение (независимое от Telegram бота)

## Статус: MVP в разработке (23.01.2026)

## Структура
```
/opt/webapp/
├── frontend/          # React + Vite + Tailwind
│   └── src/
│       ├── App.jsx
│       └── pages/
│           ├── Home.jsx
│           ├── Catalog.jsx
│           ├── LotDetail.jsx
│           └── Chat.jsx
├── backend/           # FastAPI
│   └── app.py         # Проксирует /api/lots к PROD
├── venv/              # Python venv
└── README.md
```

## Запуск

### Backend (порт 8003)
```bash
cd /opt/webapp/backend
source /opt/webapp/venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8003
```

### Frontend (порт 5173/5174)
```bash
cd /opt/webapp/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

## Следующие шаги
1. [ ] Systemd сервисы для webapp
2. [ ] Cloudflare туннель app.rizaltaservice.ru → :8003
3. [ ] Прокси nginx (фронт + бэк на одном домене)
4. [ ] Подключить GPT к чату
5. [ ] Авторизация (телефон + SMS)
6. [ ] Генерация КП (копировать из /opt/bot/services/)

## Связь с PROD
- Читает данные: GET https://api.rizaltaservice.ru/api/lots
- Не модифицирует PROD/DEV код
