# RIZALTA Bot

## Что это
AI-консультант для риэлторов. Инвестиционная недвижимость RIZALTA Resort Belokurikha (Алтай).

## Боты
- Prod: @RealtMeAI_bot
- Dev: @rizaltatestdevop_bot

## Сервер
```bash
ssh -p 2222 root@72.56.64.91
```
- `/opt/bot` — prod (порт 8000, webhook)
- `/opt/bot-dev` — dev (polling)

## Стек
Python 3.12 · FastAPI · OpenAI GPT-4o-mini · Whisper · SQLite · Cloudflare Tunnel

## Ключевые файлы
- `app.py` — webhook, роутинг
- `handlers/` — команды бота
- `services/` — бизнес-логика
- `services/calc_xlsx_generator.py` — Excel ROI калькулятор
- `data/rizalta_knowledge_base.txt` — база знаний AI

## Версия: 1.9.2

## Последняя сессия: 18.12.2025
- ✅ OpenAI API ключ обновлён (старый истёк)
- ✅ daily_check.sh — скрипт ежедневной проверки системы
- ✅ Запланирована фича: сравнение депозитов vs RIZALTA

## Предыдущая сессия: 11-12.12.2025
- ✅ Excel генератор ROI (значения вместо формул — работает везде)
- ✅ SSH безопасность (порт 2222, вход только по ключу)
- ✅ Токены Telegram перевыпущены (были в git-истории)
- ✅ Health check мониторинг (каждые 5 мин, Telegram-алерт)
- ✅ Документация упорядочена (6 файлов вместо 9)
- ✅ Создан стандарт разработчика (github.com/semiekhin/developer-standards)

## TODO
- [ ] **Сравнение депозит vs RIZALTA** — парсер ставок банков, 3 сценария (высокая/средняя/низкая ставка ЦБ), налог на депозит
- [ ] Специалисты для календаря (реальные ФИО, telegram_id)
- [ ] UptimeRobot (внешний мониторинг)
- [ ] GitHub 2FA

## Важные правила
- Токены НЕ коммитить (только в .env)
- Ставки аренды: база 26.8 м² (не 22!)
- Excel: значения, не формулы (для совместимости)
- Бэкапы: ежедневно 03:00 на email
- После деплоя: `fuser -k 8000/tcp && systemctl restart rizalta-bot`
- **Всегда синхронизировать оба репо (dev + prod)**

## Документация
- `PROJECT_HISTORY.md` — история проекта
- `RIZALTA_KNOWLEDGE.md` — база знаний о недвижимости
- `SECURITY_OPERATIONS.md` — безопасность и операции
- `SESSION_HANDOFF.md` — инструкция для нового чата
