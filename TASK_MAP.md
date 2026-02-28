# RIZALTA WebApp — Карта задач для 1Code

## ТЕКУЩИЙ СТАТУС: v0.9.1 (28.02.2026)

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

### Сессия 16.02.2026 (v0.8.4 → v0.8.5) — DevOps
- **DEV-окружение:** /opt/webapp-dev, порт 8004, systemd, nginx, SSL
- **Favicon оранжевая "D"** для визуального отличия dev/prod
- **Пути вынесены в .env** (WEBAPP_DB, DIST_PATH, PROPERTIES_DB и др.)
- **GitHub webhook auto-deploy** на DEV (webhook-webapp.service)
- **deploy-to-prod.sh** — деплой одной командой с автооткатом
- **session-end.sh** — скрипт коммита 3 репо

### Сессия 24.02.2026 (v0.8.5 → v0.9.0) — Интеграция К3
- **Corp3.jsx удалён** — К3 в штатном каталоге (3 вкладки: К1 Family, К2 Business, К3 Digital)
- **Поиск только через properties.db** (убран поиск по corp3_units.json)
- **КП/Excel:** building передаётся явно (фикс дублей кодов между корпусами)
- **kp_pdf_generator.py:** get_building_name() знает 3 корпуса
- **Whitelist-код закомментирован** с TODO для К4

### Сессия 28.02.2026 (v0.9.0 → v0.9.1) — Claude-оркестратор
- **Эндпоинт `/api/docs/file`** — чтение файлов проекта через HTTP для Claude
- **SESSION_END_TEMPLATE_WEBAPP.md** — свой шаблон завершения для webapp-чата
- **Новый workflow** — ссылки вместо копипасты, актуальный контекст с сервера
- **OpenAI API ключ** обновлён (новый аккаунт)

---

## 🔜 БЭКЛОГ (Phase 3.3+)

### Приоритет 🔴

1. **Function calling в AI чате** — инструменты: расчёт ROI, поиск лота, бронирование из чата
2. **Автосинхронизация данных бот↔webapp** — rizalta_finance.json, instructions.txt (через .env пути, без копий)

### Приоритет 🟡

3. **Миграция на российский LLM** (DeepSeek/YandexGPT)
4. **История чата** — сохранение сессий (сейчас browser-only)
5. **Push-уведомления** — для задач секретаря
6. **К4 whitelist** — переиспользовать код whitelist при появлении нового корпуса

### Приоритет 🟢

7. **Админ-панель** — управление лотами, статусами, whitelist
8. **"Взять" → секретарь** — автосоздание задачи (бот-сайд)

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
| v0.9.0-corp3-unified | К3 в штатном каталоге |
| v0.9.1-claude-orchestrator | Эндпоинт /api/docs/file |

---

## ⚠️ ДЕПЛОЙ WEBAPP

### Стандартный деплой
```bash
bash /opt/webapp-dev/deploy-to-prod.sh
```

### Откат
```bash
cd /opt/webapp
git reset --hard v0.9.1-claude-orchestrator  # или другой тег
npm run build --prefix frontend
systemctl restart webapp.service
```

---

## 📝 ВАЖНЫЕ ЗАМЕЧАНИЯ

- WebApp ЧИТАЕТ `/opt/bot/properties.db` (К1+К2+К3, все лоты)
- WebApp ПИШЕТ INSERT в `properties.db` таблицу bookings (кнопка "Взять")
- `rizalta_finance.json` и `instructions.txt` — копии из бота, NOT in git (TODO: автосинхронизация)
- Разработка webapp параллельна с ботом — docs интегрируем, не затираем!
- Claude читает код через `/api/docs/file` — не нужен копипаст
