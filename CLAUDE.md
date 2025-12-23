# RIZALTA Bot — Быстрый старт

## Версия
**v2.1.0** (24.12.2024)

## Доступ к серверу
```bash
ssh -p 2222 root@72.56.64.91
```

## Структура
- `/opt/bot-dev` — DEV (@rizaltatestdevop_bot, polling)
- `/opt/bot` — PROD (@RealtMeAI_bot, webhook:8000)

## Ключевые файлы v2.1.0
- `app.py` — главный роутер
- `handlers/kp.py` — КП + универсальная навигация (Корпус→Этаж→Лоты)
- `services/intent_router.py` — GPT классификатор с приоритетами
- `services/units_db.py` — работа с 348 лотами
- `services/calc_universal.py` — рассрочка 18 мес, новые проценты
- `services/kp_pdf_generator.py` — генерация PDF с поддержкой building

## Основные фичи
1. **348 лотов** — все актуальные лоты с сайта застройщика
2. **Навигация** — По корпусу / По площади / По бюджету / По коду лота
3. **Дубли кодов** — 70 лотов есть в обоих корпусах, показывается выбор
4. **Универсальное меню** — КП, Расчёты, Сравнение используют одну навигацию
5. **Голосовое управление** — "что есть на 5 этаже 2 корпуса до 25 млн"

## Команды
```bash
# DEV
systemctl restart rizalta-bot-dev
journalctl -u rizalta-bot-dev -f

# PROD  
systemctl restart rizalta-bot
journalctl -u rizalta-bot -f

# Синхронизация базы
cd /opt/bot-dev && python3 services/parser_rclick.py
```

## Деплой DEV → PROD
```bash
cp /opt/bot-dev/{app.py,handlers/kp.py,services/*.py,properties.db} /opt/bot/
cd /opt/bot && python3 -c "import app" && systemctl restart rizalta-bot
```
