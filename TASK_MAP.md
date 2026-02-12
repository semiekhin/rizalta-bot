# RIZALTA WebApp — Карта задач для 1Code

## ТЕКУЩИЙ СТАТУС: v0.8.0 (Phase 3.2.2 завершена)

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

---

## 🔜 БЭКЛОГ (Phase 3.3+)

### Приоритет 🔴

1. **Function calling в AI чате** — инструменты: расчёт ROI, поиск лота, бронирование из чата
2. **"Взять" → секретарь** — автоматическое создание задачи при взятии заявки (бот-сайд, webapp не может)

### Приоритет 🟡

3. **История чата** — сохранение сессий (сейчас browser-only)
4. **Push-уведомления** — для задач секретаря
5. **Тюнинг rclick_service.py** — формат запросов/ответов может требовать адаптации
6. **Inline PDF viewer** — PDF в модалке вместо скачивания (под вопросом)
7. **К3 в открытую продажу** — убрать whitelist когда корпус выходит в продажу

### Приоритет 🟢

8. **Админ-панель** — управление лотами, статусами, whitelist
9. **Offline-режим** — Service Worker для базовой работы без сети

---

## ⚠️ ДЕПЛОЙ WEBAPP

### Стандартный деплой
```bash
cd /opt/webapp && git pull origin webapp
cd frontend && npm run build
systemctl restart webapp.service
curl -s http://localhost:8003/api/health
```

### После обновления AI (если менялись данные бота)
```bash
cp /opt/bot/data/rizalta_finance.json /opt/webapp/backend/data/
cp /opt/bot/config/instructions.txt /opt/webapp/backend/config/
systemctl restart webapp.service
```

### Env (.env должен содержать)
```
TELEGRAM_BOT_TOKEN, MANAGER_EMAIL, BOT_EMAIL
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
MANAGER_CHAT_ID, SHOWS_GROUP_ID
OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS
```

### Установка зависимостей (в venv!)
```bash
/opt/webapp/venv/bin/pip install openai openpyxl
```

### Откат
```bash
cd /opt/webapp
git reset --hard v0.8.0-stable    # или v0.6.1-pre-phase322
cd frontend && npm run build
systemctl restart webapp.service
```

---

## 📝 ВАЖНЫЕ ЗАМЕЧАНИЯ

- WebApp ЧИТАЕТ `/opt/bot/properties.db` (данные лотов)
- WebApp ПИШЕТ INSERT в `properties.db` таблицу bookings (кнопка "Взять")
- `rizalta_finance.json` и `instructions.txt` — копии из бота, NOT in git
- Видео файлы большие (до 50MB) — стримятся, не грузятся целиком
- Whitelist файлов обязателен — нельзя отдавать произвольные пути
- Разработка webapp параллельна с ботом — docs интегрируем, не затираем!
