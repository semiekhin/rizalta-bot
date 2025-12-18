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
- `handlers/compare.py` — сравнение депозит vs RIZALTA
- `handlers/booking_fixation.py` — фиксация клиентов через ri.rclick.ru
- `services/` — бизнес-логика
- `services/rclick_service.py` — интеграция с ri.rclick.ru
- `services/kp_pdf_generator.py` — PDF коммерческое предложение
- `services/compare_pdf_generator.py` — PDF отчёт сравнения
- `data/rizalta_knowledge_base.txt` — база знаний AI

## Версия: 1.9.5

## Последняя сессия: 18.12.2025
- ✅ КП: 3 варианта (100% оплата, 12 мес, 12+24 мес)
- ✅ КП: "Гостиничный номер" вместо "Лот"
- ✅ КП: Скидка 5% при 100% оплате (от price - 150000)
- ✅ КП: "11 мес. ×" и "24 мес. ×" в рассрочке
- ✅ Фиксация клиентов через ri.rclick.ru
- ✅ Сравнение депозит vs RIZALTA (данные ЦБ РФ)

## Предыдущие сессии
- 11-12.12.2025: Excel генератор, SSH безопасность, мониторинг

## TODO
- [ ] Специалисты для календаря (реальные ФИО, telegram_id)
- [ ] UptimeRobot (внешний мониторинг)
- [ ] Синхронизация данных (properties.db, rizalta_finance.json, units.json)

## КП варианты
- **100% оплата** — планировка крупно, без рассрочки, скидка 5%
- **12 месяцев** — рассрочка 0% на 12 мес
- **12+24 месяца** — обе рассрочки

## Формула скидки
`(price - 150000) * 0.95`

## Важные правила
- Токены НЕ коммитить (только в .env)
- Ставки аренды: база 26.8 м² (не 22!)
- start_year = 2026 в калькуляторах
