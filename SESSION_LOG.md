# SESSION_LOG — Последние сессии

## 16.03.2026 — YandexGPT миграция + RAG + Траншевая ипотека

**Сделано:**
- Полная миграция ai_chat.py: OpenAI Responses API → YandexGPT Chat Completions API (OpenAI-compatible)
- Модель: gpt-oss-120b/latest — без модерации, function calling, streaming
- RAG сервис (rag_service.py): PyMuPDF + TF-IDF, ddu.pdf + arenda.pdf, 487 чанков
- `_needs_documents()` + `_build_rag_context()` — автопоиск по документам
- Фикс `_needs_tools()`: парные ключевые слова вместо точных подстрок
- Фикс intent_router: вопросы о содержании документов → чат/RAG, а не навигация
- Траншевая ипотека: калькулятор + PDF + модалка в LotDetail (4 сценария ПВ)
- Редизайн меню лота: grid 2×5, 3D-эффект, уникальные иконки
- YandexGPT для свободного чата (Путь 3), GPT-5.2 оставлен в env

**Файлы:** ai_chat.py, rag_service.py, intent_router.py, yandex_chat.py, tranche_mortgage_calculator.py, tranche_mortgage_pdf_generator.py, LotDetail.jsx, app.py

**Решения:**
- gpt-oss-120b лучше yandexgpt/latest (без модерации юридических тем)
- OpenAI-compatible endpoint лучше нативного (меньше модерации)
- Один клиент get_client() для всех 4 путей

**Следующий шаг:** стабилизация YandexGPT, RAG расширение, деплой v0.9.8 в PROD

---

## 11.03.2026 — Инвестиционная сводка по лоту

**Сделано:**
- Модалка "Инвестиционная сводка" в LotDetail.jsx — фронтенд-агрегация (Promise.all × 5 API)
- lot_summary_pdf_generator.py: PDF в dark RIZALTA branding (#263524/#D4A84B)
- POST /api/lot-summary-pdf endpoint
- RFC 5987 filename encoding (фикс кириллицы в Content-Disposition)
- Chat.jsx cleanup: удалены кнопки "Фин. отчёт" и "Портфель" (-96 строк)

**Файлы:** LotDetail.jsx, lot_summary_pdf_generator.py, app.py, Chat.jsx

**Решения:** портфельный экран деприоритизирован — менеджеры составляют портфели вручную

**Следующий шаг:** траншевая ипотека, YandexGPT интеграция

---

## 02.03.2026 (parts 1-4) — AI agentic loop + Reports + Метрики + Portfolio

**Сделано:**
- ai_chat.py: 3 пути (navigation / reports / agentic loop с GPT-5.2 + 5 tools)
- report_builder.py: сбор данных из БД без AI (build_lot_report_data, build_portfolio_data_v2)
- tool_definitions.py: 5 OpenAI tools (search, details, ROI, installment, deposit)
- strategy_pdf_generator.py: full rewrite, 4-страничные PDF с RIZALTA branding
- Инвестиционные метрики: NOI, Cap Rate, Cash-on-Cash, Equity Multiple
- 3 сценария портфеля: premium / portfolio 100% / max leverage (round-robin)
- AI selector удалён → Python round-robin подбор (-392 строки)
- portfolio_pdf_generator.py: PDF в стиле чат-карточек
- UI: LotReportCard, PortfolioReportCardV2, MetricCell, renderText()

**Файлы:** ai_chat.py, report_builder.py, tool_definitions.py, strategy_pdf_generator.py, calculator.py, Chat.jsx, app.py

**Решения:**
- Python подбирает лоты (не AI) — надёжнее и дешевле
- Разделение: чат = консьерж, портфель = отдельный экран, сводка лота = отдельный экран

**Следующий шаг:** инвестиционная сводка по лоту (модалка + PDF)
