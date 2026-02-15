# RIZALTA WebApp — Карта задач для 1Code

## ТЕКУЩИЙ СТАТУС: v0.8.5 (16.02.2026)

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

### Сессия 15.02.2026 (v0.8.0 → v0.8.4) — Фиксы + поиск
- **Фикс Excel для К3:** encodeURIComponent на фронте + normalize_lot_code на бэке + поиск в corp3_units.json по building=3
- **PDF "Варианты оплаты":** Новый endpoint /api/payment-pdf + payment_pdf_generator.py + кнопка в модалке
- **Поиск по коду лота:** GET /api/lots/search ищет в К1+К2 (properties.db) + К3 (JSON), выбор корпуса при дублях (А200 есть в К1 и К2)
- **Фикс планировки К3 через поиск:** layout_url с токеном whitelist, без дублирования ?token=

### Сессия 16.02.2026 (v0.8.4 → v0.8.5) — DevOps pipeline
- **DEV-окружение:** /opt/webapp-dev, порт 8004, systemd (webapp-dev.service), nginx + SSL
- **Оранжевый favicon:** визуальное отличие DEV от PROD
- **Пути в .env:** WEBAPP_DB, DIST_PATH, PROPERTIES_DB, CORP3_DATA_PATH и др. → os.getenv() в app.py + сервисах
- **GitHub webhook:** webhook_receiver.py (порт 9001) + webhook-webapp.service → auto-deploy DEV за 2-3 сек
- **deploy-to-prod.sh:** деплой одной командой с проверкой health + автооткатом

---

## 🔜 БЭКЛОГ (Phase 3.3+)

### Приоритет 🔴 — DevOps автоматизация

1. **Автосинхронизация данных бот↔webapp** — rizalta_finance.json, instructions.txt (cron/inotify)
2. **session-end.sh** — один скрипт: обновление docs + коммит 3 репо + push

### Приоритет 🔴 — Функциональность

3. **Function calling в AI чате** — инструменты: расчёт ROI, поиск лота, бронирование из чата
4. **"Взять" → секретарь** — автоматическое создание задачи при взятии заявки (бот-сайд, webapp не может)

### Приоритет 🟡

5. **Миграция на российский LLM** (DeepSeek/YandexGPT) — снизить зависимость от OpenAI
6. **Cloudflare DNS миграция** — убрать зависимость для webapp
7. **История чата** — сохранение сессий (сейчас browser-only)
8. **Push-уведомления** — для задач секретаря
9. **Тюнинг rclick_service.py** — формат запросов/ответов может требовать адаптации
10. **К3 в открытую продажу** — убрать whitelist когда корпус выходит в продажу

### Приоритет 🟢

11. **Админ-панель** — управление лотами, статусами, whitelist
12. **Offline-режим** — Service Worker для базовой работы без сети

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
| v0.8.5-env-paths | Пути в .env |
| v0.8.5-devops-pipeline | Webhook + deploy скрипт |

---

## ⚠️ ДЕПЛОЙ WEBAPP

### Стандартный workflow (после push 1Code)
1. Push в GitHub → webhook автоматически обновляет DEV (2-3 сек)
2. Проверка: https://dev-webapp.rizaltaservice.ru
3. Деплой в PROD: `bash /opt/webapp-dev/deploy-to-prod.sh`

### Ручной деплой DEV (если webhook не сработал)
```bash
cd /opt/webapp-dev && git pull origin webapp
npm run build --prefix frontend
systemctl restart webapp-dev.service
curl -s http://localhost:8004/api/health
```

### После обновления AI (если менялись данные бота)
```bash
cp /opt/bot/data/rizalta_finance.json /opt/webapp/backend/data/
cp /opt/bot/data/rizalta_finance.json /opt/webapp-dev/backend/data/
cp /opt/bot/config/instructions.txt /opt/webapp/backend/config/
cp /opt/bot/config/instructions.txt /opt/webapp-dev/backend/config/
systemctl restart webapp.service webapp-dev.service
```

### Откат
```bash
cd /opt/webapp-dev
git reset --hard v0.8.5-devops-pipeline  # или другой тег
npm run build --prefix frontend
systemctl restart webapp-dev.service
# Затем деплой: bash /opt/webapp-dev/deploy-to-prod.sh
```

---

## 📝 ВАЖНЫЕ ЗАМЕЧАНИЯ

- WebApp ЧИТАЕТ `/opt/bot/properties.db` (К1+К2, 358 лотов)
- WebApp ЧИТАЕТ `/opt/bot-dev/data/corp3_units.json` (К3, 282 лота)
- WebApp ПИШЕТ INSERT в `properties.db` таблицу bookings (кнопка "Взять")
- `rizalta_finance.json` и `instructions.txt` — копии из бота, NOT in git
- Разработка webapp параллельна с ботом — docs интегрируем, не затираем!
- 1Code запускается на Mac: `cd ~/1code && bun run dev`
- 1Code работает с клоном репо в `~/.21st/worktrees/`
