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
- `services/` — бизнес-логика
- `services/deposit_calculator.py` — калькулятор депозита (данные ЦБ)
- `services/investment_compare.py` — сравнение инвестиций
- `services/compare_pdf_generator.py` — PDF отчёт сравнения
- `services/calc_xlsx_generator.py` — Excel ROI калькулятор
- `services/kp_pdf_generator.py` — PDF коммерческое предложение
- `services/kp_resources/` — ресурсы КП (логотип, шрифты)
- `data/rizalta_knowledge_base.txt` — база знаний AI

## Версия: 1.9.3

## Последняя сессия: 18.12.2025
- ✅ Сравнение депозит vs RIZALTA (данные ЦБ РФ)
  - 3 сценария ключевой ставки (базовый, оптимист, пессимист)
  - Налог на депозит 13-15%
  - Прогноз ЦБ: ставка 14% → 7% к 2030
- ✅ PDF генератор для сравнения
- ✅ Выбор лота по площади/бюджету для сравнения
- ✅ Новый логотип в КП (PNG с прозрачным фоном)
- ✅ Чёткие надписи в КП (убран opacity)
- ✅ Строка "Стоимость лота без рассрочки" в КП
- ✅ Расчёты с 2026 года (start_year = 2026)
- ✅ Склонение "год/года/лет" в отчётах

## Предыдущая сессия: 18.12.2025 (утро)
- ✅ OpenAI API ключ обновлён (старый истёк)
- ✅ daily_check.sh — скрипт ежедневной проверки системы

## Сессия 11-12.12.2025
- ✅ Excel генератор ROI (значения вместо формул)
- ✅ SSH безопасность (порт 2222, ключ)
- ✅ Токены Telegram перевыпущены
- ✅ Health check мониторинг (5 мин, Telegram-алерт)

## TODO
- [ ] Специалисты для календаря (реальные ФИО, telegram_id)
- [ ] UptimeRobot (внешний мониторинг)
- [ ] GitHub 2FA
- [ ] Синхронизация данных (properties.db, rizalta_finance.json, units.json)

## Расчёты RIZALTA
Коэффициенты роста (из таблицы застройщика):
- 2025: 18%
- 2026: 20%
- 2027: 20%
- 2028: 10% + аренда
- 2029+: 8.8% + аренда

Аренда с 2028 года:
- Occupancy: 40% → 60% → 70%
- Expenses: 50% от дохода

## Важные правила
- Токены НЕ коммитить (только в .env)
- Ставки аренды: база 26.8 м² (не 22!)
- start_year = 2026 в калькуляторах
