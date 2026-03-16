# RIZALTA WebApp — Карта задач для 1Code

## ТЕКУЩИЙ СТАТУС: v0.9.7 (16.03.2026)

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
- **Поиск по коду лота:** GET /api/lots/search ищет в К1+К2 (properties.db) + К3 (JSON), выбор корпуса при дублях

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

### Сессия 02.03.2026 (v0.9.1 → v0.9.3) — AI Reports + Agentic Loop
- **ai_chat.py:** 3 пути — navigation intents (0 AI), reports (report_builder + 1 GPT-5.2), agentic loop (GPT-5.2 + 5 tools)
- **report_builder.py:** build_lot_report_data(), build_portfolio_data() — данные из БД без AI
- **tool_definitions.py:** 5 OpenAI tools (search_lots, get_lot_details, calculate_roi, calculate_installment, compare_with_deposit)
- **strategy_pdf_generator.py:** Full rewrite — RIZALTA branding (Montserrat, green/gold/cream), 4-page lot/portfolio reports
- **strategy_data SSE fix (f2042b4):** Кнопка "Скачать PDF" появляется во всех 3 режимах
- **Chat.jsx:** Кнопки "Фин. отчёт по лоту" и "Портфель по бюджету" с UI вводом + PDF download
- **WEBAPP_ROOT env:** DEV корректно читает ресурсы из /opt/webapp-dev
- **POST /api/strategy-pdf:** Эндпоинт генерации инвестиционного PDF
- **Git tags:** v0.9.2 (AI agentic loop + tools), v0.9.3 (PDF reports + SSE fix)

---


### Сессия 02.03.2026 part 4 (v0.9.5 → v0.9.6) — Python Portfolio + UX
- **AI selector удалён** — Python round-robin подбор для всех 3 сценариев (-392 строки)
- **Единые метрики** во всех сценариях: NOI, Cap Rate, ROI, CoC
- **Human-readable labels** для всех метрик
- **Ежемесячные платежи** в сценарии 3 (рассрочка)
- **portfolio_pdf_generator.py** — PDF в стиле чат-карточек
- **POST /api/portfolio-pdf** — эндпоинт портфельного PDF
- **GPT-5.2 fix** — max_tokens → max_completion_tokens
- **Архитектурное решение:** разделение на 3 экрана (портфель, сводка лота, чат-консьерж)


### Сессия 02.03.2026 part 4 (v0.9.5 → v0.9.6) — Python Portfolio
- **AI selector удалён:** Python round-robin подбирает лоты (-392 строки ai-кода)
- **3 сценария:** premium (самый дорогой в бюджете), portfolio_full (round-robin ASC), max_leverage (ПВ 30%)
- **Единые метрики:** NOI, Cap Rate, ROI, CoC + human-readable labels во всех сценариях
- **portfolio_pdf_generator.py:** PDF в стиле чат-карточек
- **POST /api/portfolio-pdf:** новый эндпоинт
- **GPT-5.2 fix:** max_tokens → max_completion_tokens
- **Git tag:** v0.9.6

### Сессия 11.03.2026 (v0.9.6 → v0.9.7) — Инвестиционная сводка по лоту
- **Модалка "📊 Инвестиционная сводка"** в LotDetail.jsx — фронтенд-агрегация Promise.all × 5 API
- **lot_summary_pdf_generator.py:** PDF в dark RIZALTA branding (#263524 / #D4A84B)
- **POST /api/lot-summary-pdf:** эндпоинт сводки лота
- **RFC 5987 filename encoding:** Фикс кириллицы в Content-Disposition
- **Chat.jsx cleanup:** Удалены кнопки "Фин. отчёт по лоту" и "Портфель по бюджету" (-96 строк)
- **Git tag:** v0.9.7-lot-summary

## 🔜 БЭКЛОГ (актуализирован 02.03.2026 part 4)

### Приоритет 🔴 — Этап 1: Портфельный калькулятор

1. **Portfolio.jsx** — новый экран, ввод бюджета → 3 сценария (Python)
2. Перенос карточек из Chat.jsx (PortfolioReportCardV2, ScenarioCard, MetricCell)
3. Кнопка "Инвестиционный портфель" в Home.jsx
4. PDF → /api/portfolio-pdf
5. Убрать портфельные кнопки из Chat.jsx

### Приоритет 🟡 — Этап 2: Инвестиционная сводка по лоту

6. LotSummary — все калькуляторы на одной странице
7. Кнопка в LotDetail.jsx
8. PDF полной сводки

### Приоритет 🟡 — Этап 3: Чат-консьерж

9. System prompt: ДДУ + договор аренды + RIZALTA_KNOWLEDGE.md
10. Статистика лотов в реальном времени
11. Убрать отчётные функции из чата

### Приоритет 🟢 (nice-to-have)

12. К4 whitelist
13. Миграция на российский LLM
14. Деплой v0.9.6 в PROD
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
| v0.9.2 | AI agentic loop + tools + report_builder |
| v0.9.3 | PDF investment reports + strategy_data SSE fix |
| v0.9.4 | Investment metrics (NOI, Cap Rate, CoC, Equity Multiple) |
| v0.9.5 | AI-driven portfolio + 3 scenarios + budget guard |
| v0.9.6 | Python portfolio selection + unified metrics + portfolio PDF |
| v0.9.7-lot-summary | Инвестиционная сводка по лоту (modal + PDF) + Chat cleanup |
| v0.9.4 | Investment metrics (NOI, Cap Rate, CoC, Equity Multiple) |
| v0.9.5 | AI-driven portfolio + 3 scenarios + budget guard |
| v0.9.6 | Python portfolio selection + unified metrics + portfolio PDF |

---

## ⚠️ ДЕПЛОЙ WEBAPP

### Стандартный деплой
```bash
bash /opt/webapp-dev/deploy-to-prod.sh
```

### Откат
```bash
cd /opt/webapp-dev
git reset --hard v0.9.3  # или другой тег
cd frontend && npm run build
sudo systemctl restart webapp-dev.service
```

---

## 📝 ВАЖНЫЕ ЗАМЕЧАНИЯ

- WebApp ЧИТАЕТ `/opt/bot/properties.db` (все лоты в единой БД)
- WebApp ПИШЕТ INSERT в `properties.db` таблицу bookings (кнопка "Взять")
- `rizalta_finance.json` и `instructions.txt` — копии из бота, NOT in git
- Разработка webapp параллельна с ботом — docs дополняем, не затираем!
- Claude читает код через `/api/docs/file` — не нужен копипаст
- AI: GPT-5.2 для отчётов и agentic loop, gpt-4o-mini для простого чата

### Сессия 02.03.2026 part 2 (v0.9.3+)
- **Report Cards:** LotReportCard, PortfolioReportCard — UI-компоненты в чате
- **report_card SSE event** — данные из report_builder до AI
- **format_lot_summary / format_portfolio_summary** — pre-format
- **marked удалён** — карточки вместо markdown

### Сессия 02.03.2026 part 3 (v0.9.3 → v0.9.5) — Инвест-метрики + AI Portfolio
- **Инвестиционные метрики:** NOI, Cap Rate, Cash-on-Cash (100%/30%), Equity Multiple в calculator.py
- **Report Builder v2:** 3 сценария (1 премиальный лот / портфель 100% / макс. плечо 30%), оптимизация расчётов
- **AI-driven Portfolio (Level 3):** gpt-4o-mini selector выбирает лоты → Python считает → GPT-5.2 пишет аналитику
- **AI промпты:** полноценный 7-секционный анализ (400-800 слов) вместо 2-3 предложений
- **UI карточки:** MetricCell, LotReportCard (2x3 метрики), PortfolioReportCardV2 (3 сценария + reasoning + vs deposit)
- **renderText():** лёгкий markdown рендеринг (**bold** → <strong>) в чате
- **PDF v2:** 4-страничный портфельный PDF с 3 сценариями + сравнительная таблица
- **Budget guard:** Python валидация бюджета после AI selection
- **INVESTMENT_METHODOLOGY.md:** документация формул и методики
