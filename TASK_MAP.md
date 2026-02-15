# RIZALTA WebApp — Карта задач для 1Code

## ТЕКУЩИЙ СТАТУС: v0.8.4 (15.02.2026)

**КРИТИЧНО:** Код в /opt/bot и /opt/bot-dev НЕ ТРОГАЕМ. Только читаем файлы.

---

## ✅ ВЫПОЛНЕНО

### Phase 1-2 (v0.3.0 → v0.5.0) — Базовый UI
- 12 экранов: Home, Catalog, Corp3, LotDetail, Chat, Secretary, Fixation, News, Booking, Presentations, Documents, Media
- Навбар 3 кнопки (Главная / Чат с AI / Лоты)
- Фирменный стиль RIZALTA (палитра, Montserrat, лого)
- Whitelist система (Corp3 доступ по токену)
- Файловый сервер (презентации, договоры, видео)

### Phase 3.1 (v0.5.0 → v0.6.1) — Функциональность
- ROI калькулятор + Excel генерация
- КП генерация (PDF, wkhtmltopdf)
- Сравнение с депозитом + PDF
- Уведомления: Telegram + Email (POST /api/book-showing)
- Whitelist Corp3 + шахматка 282 лота

### Phase 3.2.2 (v0.6.1 → v0.8.0) — AI + Инструменты
- **AI Чат:** SSE streaming через OpenAI gpt-4o-mini, 16 intents, function calling, кнопки навигации
- **Секретарь:** Полный CRUD задач с календарём, AI-парсинг текста (8 endpoints)
- **Фиксация:** Авторизация rclick.ru (телефон/email), формы создания (4 endpoints)
- **МГП калькулятор:** 15-летний расчёт с таблицей в модалке + PDF
- **Ипотечный калькулятор:** Совкомбанк аннуитетный с grace period + PDF
- **Новости:** 4 вкладки (валюты ЦБ, погода Open-Meteo, авиабилеты Aviasales, RSS дайджест)
- **Показы:** Кнопка "Взять" → INSERT в bookings + фикс дубля сообщений

### Сессия 15.02.2026 (v0.8.0 → v0.8.4)
- **Фикс Excel для К3:** encodeURIComponent на фронте + normalize_lot_code на бэке + поиск в corp3_units.json по building=3
- **PDF "Варианты оплаты":** Новый endpoint /api/payment-pdf + payment_pdf_generator.py + кнопка в модалке
- **Поиск по коду лота:** GET /api/lots/search ищет в К1+К2 (properties.db) + К3 (JSON), выбор корпуса при дублях (А200 есть в К1 и К2)
- **Фикс планировки К3 через поиск:** layout_url с токеном whitelist, без дублирования ?token=

---

## 🔜 БЭКЛОГ (Phase 3.3+)

### Приоритет 🔴

1. **Function calling в AI чате** — инструменты: расчёт ROI, поиск лота, бронирование из чата
2. **"Взять" → секретарь** — автоматическое создание задачи при взятии заявки (бот-сайд, webapp не может)

### Приоритет 🟡

3. **История чата** — сохранение сессий (сейчас browser-only)
4. **Push-уведомления** — для задач секретаря
5. **Тюнинг rclick_service.py** — формат запросов/ответов может требовать адаптации
6. **К3 в открытую продажу** — убрать whitelist когда корпус выходит в продажу

### Приоритет 🟢

7. **Админ-панель** — управление лотами, статусами, whitelist
8. **Offline-режим** — Service Worker для базовой работы без сети

---

## 🏷️ GIT ТЕГИ

| Тег | Описание |
|-----|----------|
| v0.5.0-stable | Phase 3.1 (whitelist) |
| v0.6.1-pre-phase322 | Точка отката до Phase 3.2.2 |
| v0.8.0-stable | Phase 3.2.2 завершена |
| v0.8.2-xlsx-fix | Фикс Excel для К3 |
| v0.8.3-payment-pdf | PDF вариантов оплаты |
| v0.8.4-search-complete | Поиск по коду лота |

---

## ⚠️ ДЕПЛОЙ WEBAPP

### Стандартный деплой
```bash
cd /opt/webapp && git pull origin webapp
npm run build --prefix frontend
systemctl restart webapp.service
curl -s http://localhost:8003/api/health
```

### После обновления AI (если менялись данные бота)
```bash
cp /opt/bot/data/rizalta_finance.json /opt/webapp/backend/data/
cp /opt/bot/config/instructions.txt /opt/webapp/backend/config/
systemctl restart webapp.service
```

### Откат
```bash
cd /opt/webapp
git reset --hard v0.8.4-search-complete  # или другой тег
npm run build --prefix frontend
systemctl restart webapp.service
```

---

## 📝 ВАЖНЫЕ ЗАМЕЧАНИЯ

- WebApp ЧИТАЕТ `/opt/bot/properties.db` (К1+К2, 358 лотов)
- WebApp ЧИТАЕТ `/opt/bot-dev/data/corp3_units.json` (К3, 282 лота)
- WebApp ПИШЕТ INSERT в `properties.db` таблицу bookings (кнопка "Взять")
- `rizalta_finance.json` и `instructions.txt` — копии из бота, NOT in git
- Разработка webapp параллельна с ботом — docs интегрируем, не затираем!
