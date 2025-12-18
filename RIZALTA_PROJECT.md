# RIZALTA Bot — Описание проекта

## О проекте
AI-консультант для риэлторов. Инвестиционная недвижимость RIZALTA Resort Belokurikha (Алтай).

## Боты
- **Prod:** @RealtMeAI_bot (webhook, порт 8000)
- **Dev:** @rizaltatestdevop_bot (polling)

## Сервер
```bash
ssh -p 2222 root@72.56.64.91
```
- `/opt/bot` — prod
- `/opt/bot-dev` — dev

## Стек
Python 3.12 · FastAPI · OpenAI GPT-4o-mini · Whisper · SQLite · Cloudflare Tunnel

---

## Структура проекта
```
/opt/bot/
├── app.py                    # Главный файл (webhook, роутинг)
├── run_polling.py            # Dev режим
├── config/
│   └── settings.py           # Константы, кнопки меню
├── handlers/
│   ├── __init__.py           # Экспорты
│   ├── menu.py               # Главное меню
│   ├── ai_chat.py            # AI диалоги
│   ├── booking.py            # Онлайн-показы
│   ├── booking_fixation.py   # Фиксация клиентов ri.rclick.ru
│   ├── booking_calendar.py   # Календарь бронирования
│   ├── compare.py            # Депозит vs RIZALTA
│   ├── kp.py                 # Коммерческие предложения
│   ├── calc_dynamic.py       # Расчёты ROI
│   ├── docs.py               # Документы
│   ├── news.py               # Новости/дайджест
│   ├── media.py              # Медиа
│   └── units.py              # Работа с лотами
├── services/
│   ├── telegram.py           # API Telegram
│   ├── ai_chat.py            # OpenAI интеграция
│   ├── calculations.py       # Финансовые расчёты
│   ├── rclick_service.py     # API ri.rclick.ru
│   ├── deposit_calculator.py # Калькулятор депозита ЦБ
│   ├── investment_compare.py # Сравнение инвестиций
│   ├── compare_pdf_generator.py # PDF сравнения
│   ├── kp_pdf_generator.py   # PDF КП
│   ├── calc_xlsx_generator.py # Excel ROI
│   ├── units_db.py           # Работа с БД лотов
│   └── kp_resources/         # Логотип, шрифты
├── data/
│   ├── rizalta_knowledge_base.txt # База знаний AI
│   ├── units.json            # Данные лотов
│   └── rizalta_finance.json  # Финансовые данные
└── *.db                      # SQLite базы
```

---

## Функциональность

### 1. КП (Коммерческие предложения)
- **3 варианта:** 100% оплата, 12 мес, 12+24 мес
- Выбор лота по площади/бюджету
- PDF с логотипом, планировкой, расчётами
- Скидка 5% при 100% оплате

### 2. Фиксация клиентов
- Интеграция с ri.rclick.ru (reverse engineering)
- Авторизация риэлтора (токен 90 дней)
- Фиксация без перехода на сайт

### 3. Сравнение депозит vs RIZALTA
- Данные ЦБ РФ (ключевая ставка)
- 3 сценария (базовый, оптимист, пессимист)
- PDF отчёт

### 4. Расчёты ROI
- Динамический калькулятор
- Excel генератор
- Прогноз до 2029

### 5. AI консультант
- GPT-4o-mini
- База знаний проекта
- Голосовой ввод (Whisper)

### 6. Календарь показов
- Выбор специалиста
- Бронирование времени

---

## API интеграции

### ri.rclick.ru (reverse engineering)
- `POST /auth/login/` — авторизация → rClick_token
- `POST /notice/newbooking/` — фиксация клиента
- project_id = 340

### ЦБ РФ
- Ключевая ставка
- Прогноз ставок

### Другие
- Open-Meteo (погода)
- Aviasales (перелёты)
- RSS (новости недвижимости)

---

## История изменений

| Версия | Дата | Описание |
|--------|------|----------|
| 1.9.5 | 18.12.2025 | КП 3 варианта, фиксация ri.rclick.ru, депозит vs RIZALTA |
| 1.9.2 | 18.12.2025 | Обновление OpenAI ключа, daily_check.sh |
| 1.9.1 | 12.12.2025 | Fix Excel (значения вместо формул) |
| 1.9 | 11-12.12.2025 | Excel ROI, безопасность SSH, документация |
| 1.8 | 10.12.2025 | Фикс КП, метазнания |
| 1.7 | 09-10.12.2025 | PDF КП с логотипом, календарь |
| 1.6 | 09.12.2025 | Dev-окружение, парсер ri.rclick.ru |

---

## Важные правила
- Токены НЕ коммитить (только в .env)
- Ставки аренды: база 26.8 м² (не 22!)
- start_year = 2026 в калькуляторах
- Формула скидки: price * 0.95
