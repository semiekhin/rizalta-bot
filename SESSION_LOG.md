# SESSION_LOG — Последние сессии

## 30.03.2026 — Система управления контекстом

**Сделано:**
- CLAUDE.md переписан с нуля (534→230 строк): экосистема, архитектура из кода, БД схемы, уроки из ошибок
- SESSION_LOG.md создан: последние 3 сессии в компактном формате
- BACKLOG.md создан: невыполненные задачи P0–P3
- Добавлена секция «Промпты для Claude Code» — критерии готовности задач
- Совместимо со скриптом start-session.sh (собирает 3 файла в буфер)

**Файлы:** CLAUDE.md, SESSION_LOG.md, BACKLOG.md

**Решения:** старый CLAUDE.md заменён полностью (дублирование сессий, 534→230 строк). TASK_MAP.md и SESSION_END_TEMPLATE_WEBAPP.md оставлены как архив.

**Следующий шаг:** деплой v0.9.8 в PROD, стабилизация YandexGPT

---

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

