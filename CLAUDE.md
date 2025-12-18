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
- `services/deposit_calculator.py` — калькулятор депозита (данные ЦБ)
- `services/investment_compare.py` — сравнение инвестиций
- `services/compare_pdf_generator.py` — PDF отчёт сравнения
- `services/calc_xlsx_generator.py` — Excel ROI калькулятор
- `services/kp_pdf_generator.py` — PDF коммерческое предложение
- `data/rizalta_knowledge_base.txt` — база знаний AI

## Версия: 1.9.4

## Последняя сессия: 18.12.2025
- ✅ Фиксация клиентов через ri.rclick.ru
  - Авторизация риэлтора (телефон + пароль → токен)
  - Токен хранится 90 дней в SQLite
  - Фиксация без перехода на сайт
- ✅ Сравнение депозит vs RIZALTA (данные ЦБ РФ)
  - 3 сценария ключевой ставки
  - PDF генератор
  - Выбор лота по площади/бюджету
- ✅ Улучшения КП (логотип, чёткость, цена без рассрочки)

## Предыдущие сессии
- 11-12.12.2025: Excel генератор, SSH безопасность, мониторинг

## TODO
- [ ] Специалисты для календаря (реальные ФИО, telegram_id)
- [ ] UptimeRobot (внешний мониторинг)
- [ ] GitHub 2FA
- [ ] Синхронизация данных (properties.db, rizalta_finance.json, units.json)

## Фиксация клиентов
- Endpoint авторизации: POST https://ri.rclick.ru/auth/login/
- Endpoint фиксации: POST https://ri.rclick.ru/notice/newbooking/
- Токен в cookie: rClick_token (срок ~100 дней)
- project_id = 340 (RIZALTA)

## Важные правила
- Токены НЕ коммитить (только в .env)
- Ставки аренды: база 26.8 м² (не 22!)
- start_year = 2026 в калькуляторах
