# RIZALTA WebApp v2.0 — Спецификация миграции

## GAP-анализ: Бот vs WebApp

### Реализовано в WebApp ✅
- Каталог лотов (шахматка по этажам, фильтры по статусу)
- ROI расчёт (модалка с прибылью за 11 лет)
- Варианты рассрочки (12/18 мес, 3 варианта ПВ)
- Сравнение с депозитом (3 сценария)
- PDF КП генерация (3 варианта)
- Excel ROI выгрузка
- Форма записи на показ (только UI)

### НЕ реализовано ❌
- AI-чат с function calling (заглушка)
- Intent Router (классификация намерений)
- Подбор портфеля под бюджет
- Отправка заявок (TG/email)
- Фирменный стиль RIZALTA
- systemd сервис
- Собственная БД (сейчас shared с PROD)

## Фирменный стиль
Цвета: тёмно-зелёный #2D3B2D + кремовый #F0E6D3
Шрифт: Montserrat (Regular, Medium, SemiBold)
Лого: public/images/logo.png

## LLM
DeepSeek V3.2 через OpenRouter API
Endpoint: https://openrouter.ai/api/v1/chat/completions
Формат: OpenAI-совместимый, поддержка function calling
