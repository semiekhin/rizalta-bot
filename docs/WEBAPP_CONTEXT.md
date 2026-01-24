# ⚠️ PROD/DEV НЕ ТРОГАТЬ! РАБОТАЕМ ТОЛЬКО В /opt/webapp/ ⚠️

# RIZALTA Web App v0.1.3
Standalone веб-приложение — fallback если Telegram упадёт.

## Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91`
- **WebApp:** `/opt/webapp` (отдельно от бота!)
- **Frontend:** React + Vite + Tailwind (build в /frontend/dist/)
- **Backend:** FastAPI → порт 8003
- **PROD бот:** `/opt/bot` (НЕ ТРОГАТЬ)
- **DEV бот:** `/opt/bot-dev` (НЕ ТРОГАТЬ)

## Текущий статус (24.01.2026)

### ✅ Работает:
- Frontend: 4 страницы готовы (Home, Catalog, LotDetail, Chat)
- Backend: FastAPI проксирует /api/lots к PROD
- Production build: /opt/webapp/frontend/dist/
- **Vercel:** https://rizalta-webapp.vercel.app/ (нужен VPN из РФ)
- **Cloudflare Pages:** https://rizalta-webapp.semiekhin.workers.dev/

### ❌ НЕ работает:
- **webapp.rizaltaservice.ru** — ERR_HTTP2_PING_FAILED

## 🔴 КРИТИЧЕСКИЙ БЛОКЕР

### Проблема
JS файл (209KB) не загружается через любой путь Cloudflare. Ошибка: `ERR_HTTP2_PING_FAILED`

### Что пробовали (2 сессии, ~4 часа):

| Вариант | Результат |
|---------|-----------|
| Cloudflare Tunnel → FastAPI | JS застревает в pending |
| Cloudflare Tunnel → nginx (gzip) | JS застревает в pending |
| Vercel + Cloudflare Proxy OFF | IP Vercel недоступен (Initial connection 11 min) |
| Vercel + Cloudflare Proxy ON | ERR_HTTP2_PING_FAILED |
| Cloudflare Pages + домен | ERR_HTTP2_PING_FAILED |

### Диагностика
- curl с сервера — всё отдаёт за 0.1 сек, статус 200
- curl с Mac — работает
- Браузер (Chrome, Safari) — НЕ работает
- Ошибка в Network → Timing: "Initial connection" зависает

### Почему важен .ru домен
- Vercel может быть заблокирован в РФ (нужен VPN)
- workers.dev — не российская зона
- rizaltaservice.ru — российский домен, нужен для fallback

## 📋 ЗАДАЧИ

### 🔴 Критично (блокер)
| # | Задача | Статус |
|---|--------|--------|
| 1 | Починить webapp.rizaltaservice.ru | ❌ блокер |

### Варианты решения (не проверены)
1. Отключить HTTP/2 в Cloudflare (если возможно)
2. Code splitting — разбить JS на куски < 50KB
3. Купить отдельный домен (rizalta.ru) без Cloudflare
4. Российский хостинг статики

### 🟡 После решения блокера
| # | Задача | Статус |
|---|--------|--------|
| 2 | GPT в чат | заглушка |
| 3 | Кнопка "Получить КП" | нет |
| 4 | Кнопка "Расчёт ROI" | нет |
| 5 | Кнопка "Записаться на показ" | нет |

## Структура
```
/opt/webapp/
├── frontend/
│   ├── src/pages/       # Home, Catalog, LotDetail, Chat
│   ├── dist/            # Production build
│   └── vite.config.js
├── backend/
│   └── app.py           # API + статика
├── venv/
└── docs/
```

## DNS записи (Cloudflare)
```
api.rizaltaservice.ru    → CNAME → туннель PROD (работает)
dev.rizaltaservice.ru    → CNAME → туннель DEV (работает)
webapp.rizaltaservice.ru → Worker → rizalta-webapp (НЕ РАБОТАЕТ)
```

## Запуск локально (работает!)
```bash
cd /opt/webapp/backend && source /opt/webapp/venv/bin/activate
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8003 > /tmp/webapp-backend.log 2>&1 &

# Проверка
curl http://127.0.0.1:8003/              # HTML
curl http://127.0.0.1:8003/api/lots      # JSON
```

## Полезные файлы в боте (для копирования)
- `/opt/bot/services/kp_pdf_generator.py` — генерация КП
- `/opt/bot/services/calc_universal.py` — расчёты рассрочки
- `/opt/bot/services/intent_router.py` — GPT роутер
- `/opt/bot/handlers/calc_dynamic.py` — ROI расчёты
- `/opt/bot/services/ai_chat.py` — AI чат
