# ⚠️ PROD НЕ ТРОГАТЬ! РАБОТАТЬ ТОЛЬКО В DEV! ⚠️

# RIZALTA AI System

AI-консультант для риэлторов. Инвестиционная недвижимость RIZALTA Resort Belokurikha (Алтай).

## Инфраструктура
- **Сервер:** `ssh -p 2222 root@72.56.64.91`
- **DEV:** `/opt/bot-dev` (@rizaltatestdevop_bot, polling)
- **PROD:** `/opt/bot` (@RealtMeAI_bot, webhook :8000)
- **Mini App:** `/opt/miniapp` → https://rizalta-miniapp.vercel.app

## Репозитории
- **PROD:** github.com/semiekhin/rizalta-bot
- **DEV:** github.com/semiekhin/rizalta-bot-dev
- **Mini App:** github.com/semiekhin/rizalta-miniapp

## Стек
Python 3.12 · FastAPI · GPT-4o-mini · Whisper · SQLite · Cloudflare Tunnel · React · Vercel

## Ключевые файлы
- `app.py` — главный файл (роутинг, callbacks, API)
- `config/settings.py` — кнопки меню, константы
- `services/intent_router.py` — GPT Intent Router
- `handlers/` — обработчики (kp, booking, secretary, calc)

## Команды
```bash
# DEV
systemctl restart rizalta-bot-dev    # перезапуск
journalctl -u rizalta-bot-dev -f     # логи

# PROD (только для деплоя!)
systemctl restart rizalta-bot
journalctl -u rizalta-bot -f
```

## Документация
- `docs/RIZALTA_CURRENT.md` — текущий статус
- `docs/RIZALTA_ARCHITECTURE.md` — архитектура
- `docs/RIZALTA_KNOWLEDGE.md` — база знаний
- `docs/RIZALTA_TASKS.md` — бэклог задач
