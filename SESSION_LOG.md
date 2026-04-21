# SESSION_LOG — Последние сессии

## 21.04.2026 — RCLICK fix (PHPSESSID + auto-relogin) + пересборка DEV venv

**Сделано:**
- `services/rclick_service.py`: переписан под новый API rclick.ru — связка `rClick_token + PHPSESSID`, multipart/form-data, браузерные headers (UA/Origin/Referer), телефон `8 (XXX) XXX-XX-XX`, обязательные пустые поля `agentLastName/FirstName/Phone + pasImage[]`, project=340, manager=2
- Fernet-шифрование пароля → авто-релогин при мёртвой PHP-сессии (HTTP 500 + empty body), rate-limit 30с на session_id
- `init_rclick_table()`: идемпотентная миграция (`CREATE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN` с try/except). Убран деструктивный `DROP TABLE IF EXISTS` — раньше терял сессии при каждом рестарте. Новые колонки: `token`, `phpsessid`, `encrypted_password`, `session_refreshed_at`
- `pages/Fixation.jsx`: на `{reauth_required: true}` возврат на форму логина с серверным сообщением (было: красная плашка над формой фиксации)
- `.env` (DEV + PROD): добавлен `RCLICK_ENCRYPTION_KEY` (Fernet.generate_key, одинаковый ключ на обоих)
- `requirements.txt`: `cryptography>=42.0`
- DEV venv пересобран с нуля: старый имел `uvicorn` с шебангом на PROD venv python (`/opt/webapp/venv/bin/python3.12`) — DEV сервис де-факто работал на PROD python + PROD site-packages, из-за чего новые пакеты в DEV не подхватывались. Новый venv: freeze PROD (33 пакета) + cryptography, шебанги корректные. Бэкап: `/opt/webapp-dev/venv.backup-20260421_1012`
- `CLAUDE.md`: убрана устаревшая заметка про сломанный шебанг, добавлена инструкция `/opt/webapp-dev/venv/bin/python -m pip install`
- Задеплоено в PROD: cryptography в `/opt/webapp/venv`, `RCLICK_ENCRYPTION_KEY` в PROD `.env`, бэкап PROD БД (`webapp.db.bak-20260421_1020`), миграция идемпотентна — прошла чисто

**Файлы:** backend/services/rclick_service.py, backend/requirements.txt, backend/.env (DEV+PROD), frontend/src/pages/Fixation.jsx, CLAUDE.md

**Решения:**
- Архитектура webapp сохранена (`httpx.AsyncClient` async, `session_id` как cookie, общая `webapp.db`) — код бота (sync requests, keyed by `telegram_id`) не скопирован слепо, портирована только бизнес-логика
- Ключ шифрования одинаковый DEV/PROD — иначе при миграции PROD сессий они бы расшифровывались некорректно. PROD rclick_sessions был пуст → никому перелогиниваться не пришлось
- Пересборка DEV venv вместо PYTHONPATH-хака (Вариант 3 из трёх предложенных) — инфра чище, шебанги теперь всегда правильные
- Колонка `cookies` в rclick_sessions оставлена как NULL-наследие (не удалена) — SQLite DROP COLUMN требует пересоздания таблицы, не нужно

**Следующий шаг:** наблюдение PROD с реальным риелтором; удаление бэкапов после 28.04.2026

---

## 12.04.2026 — Срок сдачи К3/К4 → 2 кв. 2028 + фикс deploy script

**Сделано:**
- `rizalta_finance.json`: добавлен `completion_by_building` (К1/К2: Q4 2027, К3/К4: Q2 2028); плоские поля сохранены как fallback
- Новый `services/finance_config.py`: `get_completion(building)`, `get_min_completion_year()`, `format_completion_grouped()`
- KP PDF (`kp_pdf_generator.py:215`) и Strategy PDF (`strategy_pdf_generator.py:280`): строка «Сдача» учитывает корпус
- `report_builder.py` (3 точки): двухполевая схема `completion` (int) + `completion_display` (str). Для lot-report — per-building, для портфельных — min-year + grouped string
- `ai_chat.py`: system prompt показывает grouped срок сдачи; per-building completion прокидывается в lot-report через report_builder автоматически
- `deploy-to-prod.sh`: фикс гонки health-check (`sleep 2 + curl` → retry-loop до 20с) — раньше ловил окно connection refused при холодном старте PROD (~3-5с с RAG init)
- Bump version 0.9.6 → 0.9.7
- Задеплоено в PROD

**Файлы:** rizalta_finance.json, finance_config.py (new), kp_pdf_generator.py, strategy_pdf_generator.py, report_builder.py, ai_chat.py, app.py, deploy-to-prod.sh, BACKLOG.md

**Решения:**
- Минимальный фикс: только display + LLM-контекст. Финансовые модели (calculations.py, calc_universal.py и др.) НЕ тронуты — годы аренды/роста зашиты в формулы; для К3/К4 они продолжают считать по модели «сдача 2027». Это сознательный долг, занесён в BACKLOG P2.
- Двухполевая схема (`completion` int + `completion_display` str) вместо смены типа — defensive, не ломает существующих потребителей `proj['completion']` в `ai_chat.py:325/557`.
- Ключи lot dict неоднозначны: `tool_definitions.execute_get_lot_details` → `building_num` (int), `kp_pdf_generator.get_lot_from_db` → `building` (int). Использован правильный ключ в каждом файле.
- Бот идёт тем же путём (`completion_by_building` в финансах + grouped в LLM), но в боте есть незакрытый кейс с К4 в KP — у нас покрыт через мапу.

**Следующий шаг:** наблюдение за PROD; при необходимости — сдвиг финмодели для К3/К4 (P2)

---

## 01.04.2026 — Убрано удорожание ипотеки Совкомбанк

**Сделано:**
- mortgage_config.json: markup_pct обнулён (6/9/12% → 0%) для ПВ 30/40/50%
- mortgage_calculator.py: убрана строка «Удорожание» из PDF-шаблона
- Задеплоено в PROD (git pull + restart, deploy-скрипт пропустил из-за совпадения версий)

**Файлы:** backend/data/mortgage_config.json, backend/services/mortgage_calculator.py

**Решения:** калькулятор не трогали — при markup_pct=0 формула корректна. Синхронизация с изменениями в Rizalta MAX.

**Следующий шаг:** стабилизация YandexGPT, RAG расширение

---

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

