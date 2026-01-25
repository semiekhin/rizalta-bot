# ⚠️ PROD/DEV НЕ ТРОГАТЬ! РАБОТАЕМ ТОЛЬКО В /opt/webapp/ ⚠️

# RIZALTA Web App v0.2.0
Standalone веб-приложение — fallback если Telegram упадёт.

## Статус: РАБОТАЕТ ✅

**https://webapp.rizaltaservice.ru/** — работает БЕЗ VPN из РФ

## Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91`
- **WebApp:** `/opt/webapp` (отдельно от бота!)
- **Frontend:** Preact + Vite + Tailwind (build в /frontend/dist/)
- **Backend:** Nginx проксирует /api/ к PROD боту (localhost:8000)
- **SSL:** Let's Encrypt (автопродление)
- **PROD бот:** `/opt/bot` (НЕ ТРОГАТЬ)
- **DEV бот:** `/opt/bot-dev` (НЕ ТРОГАТЬ)

## Архитектура
```
Браузер (РФ) → webapp.rizaltaservice.ru → Сервер NL (72.56.64.91)
                                              ↓
                                         Nginx (443)
                                         ├── /assets/* → статика
                                         └── /api/* → localhost:8000 (PROD API)
```

**Cloudflare НЕ используется для webapp** — только DNS запись (серое облако).

## Почему так

| Вариант | Результат |
|---------|-----------|
| Cloudflare Tunnel | Нестабильно для статики |
| Cloudflare Proxy | Заблокирован из РФ |
| Vercel | Нужен VPN из РФ |
| **Напрямую на сервер** | ✅ Работает |

## DNS (Cloudflare)
```
webapp.rizaltaservice.ru → A → 72.56.64.91 (Proxy OFF, серое облако)
api.rizaltaservice.ru    → CNAME → туннель PROD (работает для бота)
dev.rizaltaservice.ru    → CNAME → туннель DEV (работает для бота)
```

## 📋 ЗАДАЧИ

### ✅ Решено
| # | Задача | Статус |
|---|--------|--------|
| 1 | Деплой webapp.rizaltaservice.ru | ✅ работает |

### ⬜ В работе
| # | Задача | Статус |
|---|--------|--------|
| 2 | GPT в чат | ⬜ |
| 3 | Кнопка "Получить КП" | ⬜ |
| 4 | Кнопка "Расчёт ROI" | ⬜ |
| 5 | Кнопка "Записаться на показ" | ⬜ |

## Структура
```
/opt/webapp/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── pages/
│   │       ├── Home.jsx
│   │       ├── Catalog.jsx
│   │       ├── LotDetail.jsx
│   │       └── Chat.jsx
│   ├── dist/            # Production build
│   └── vite.config.js
├── backend/             # Не используется
│   └── app.py
├── venv/
└── docs/
    ├── PROJECT_PLAN.md
    ├── WEBAPP_CONTEXT.md
    └── NEW_CHAT_INSTRUCTION.md
```

## Команды
```bash
# Пересборка фронтенда
cd /opt/webapp/frontend && npm run build

# Перезагрузка nginx
nginx -t && nginx -s reload

# Проверка
curl -sI https://webapp.rizaltaservice.ru/ | head -5

# Логи nginx
tail -f /var/log/nginx/error.log
```

## Полезные файлы в боте (для копирования)
- `/opt/bot/services/ai_chat.py` — GPT чат
- `/opt/bot/services/kp_pdf_generator.py` — генерация КП
- `/opt/bot/services/calc_universal.py` — расчёты рассрочки
- `/opt/bot/handlers/calc_dynamic.py` — ROI расчёты
- `/opt/bot/services/intent_router.py` — GPT роутер

## Firewall (UFW)
```
80/tcp   — HTTP (редирект на HTTPS)
443/tcp  — HTTPS (webapp)
2222/tcp — SSH
```
