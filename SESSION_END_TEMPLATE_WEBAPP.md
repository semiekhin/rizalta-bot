# 🏁 ШАБЛОН ЗАВЕРШЕНИЯ СЕССИИ — WEBAPP

При команде "ЗАВЕРШАЕМ СЕССИЮ" или "НОВЫЙ ЧАТ" Claude должен:

---

## 📝 ШАГ 1: Обновить документацию

### 1.1 Webapp-специфичные docs (ветка `webapp`):

**`/opt/webapp-dev/CLAUDE.md`** — обновить:
- Версию webapp
- Структуру (если менялись файлы)
- API endpoints (если добавлялись/менялись)
- Env переменные (если добавлялись)
- Git теги (если создавались)
- TODO (актуализировать)

**`/opt/webapp-dev/TASK_MAP.md`** — обновить:
- Версию в шапке
- Перенести выполненное в ✅ ВЫПОЛНЕНО
- Актуализировать 🔜 БЭКЛОГ
- Обновить GIT ТЕГИ

### 1.2 Общие docs (bot-dev/docs/) — ⚠️ ДОПОЛНЯТЬ, НЕ ЗАТИРАТЬ:

**`/opt/bot-dev/docs/RIZALTA_CURRENT.md`** — добавить секцию webapp:
- Версия, что сделано в этой сессии

**`/opt/bot-dev/docs/RIZALTA_TASKS.md`** — обновить webapp-задачи:
- Выполненные, новые, изменённые приоритеты

**`/opt/bot-dev/docs/RIZALTA_CONTEXT.md`** — если менялся контекст проекта

⚠️ Эти файлы редактирует и бот-чат — дополняем свою секцию, чужое НЕ трогаем!

---

## 📤 ШАГ 2: Скопировать общие docs в PROD

```bash
cp /opt/bot-dev/docs/RIZALTA_CURRENT.md /opt/bot/docs/
cp /opt/bot-dev/docs/RIZALTA_TASKS.md /opt/bot/docs/
cp /opt/bot-dev/docs/RIZALTA_CONTEXT.md /opt/bot/docs/
```

---

## 📦 ШАГ 3: Коммит 3 репо

Запустить скрипт или вручную:

```bash
bash /opt/webapp-dev/session-end.sh
```

Или вручную:

```bash
# 1. WebApp (ветка webapp)
cd /opt/webapp-dev
git add -A
git commit -m "docs: session [ДАТА] - [краткое описание]"
git push origin webapp

# 2. Bot DEV (общие docs)
cd /opt/bot-dev
git add docs/
git commit -m "docs: webapp session [ДАТА] - [краткое описание]"
git push

# 3. Bot PROD (копия общих docs)
cd /opt/bot
git add docs/
git commit -m "docs: webapp session [ДАТА] - [краткое описание]"
git push
```

---

## 📋 ШАГ 4: Выдать промпт для нового webapp-чата

Формат промпта (СТРОГО, не менять):
```
# ⚠️ ВНИМАНИЕ: Два параллельных чата!
# Этот чат = WEBAPP (/opt/webapp, /opt/webapp-dev)
# Соседний чат = БОТ (/opt/bot, /opt/bot-dev)
# Общие docs (bot-dev/docs/) — ДОПОЛНЯТЬ, НЕ затирать!
# Claude chat = архитектор, 1Code = реализация
# ⚠️ НЕ ПИШИ КОД И НЕ ВНОСИ ИЗМЕНЕНИЯ если не уверен на 100%!
# ⚠️ Работаем ТОЛЬКО в DEV. В PROD деплоим только при полной работоспособности!

---

Прочитай документацию проекта:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=CLAUDE.md
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=TASK_MAP.md

Шаблон завершения сессии:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=SESSION_END_TEMPLATE_WEBAPP.md

При команде "завершаем сессию" или "новый чат" — ОБЯЗАТЕЛЬНО:
1. Скачать SESSION_END_TEMPLATE_WEBAPP.md
2. Обновить ВСЕ docs (дополнять, НЕ затирать)
3. Коммит: bash /opt/webapp-dev/session-end.sh
4. Выдать ПОЛНЫЙ промпт для нового чата

---

Первая задача — [описание следующей задачи].
```

⚠️ НЕ добавлять в промпт версии, инфраструктуру, стек, бэклог, теги — всё это уже в CLAUDE.md и TASK_MAP.md. Claude читает их по ссылкам с сервера (через /api/docs/file, НЕ через GitHub CDN — чтобы избежать кэширования).

---

## ✅ Чеклист сессии [ДАТА]

**Версия:** v[X.X.X] → v[X.X.X]

**Что сделано:**
- [ ] ...

**Обновлены docs:**
- [ ] CLAUDE.md
- [ ] TASK_MAP.md
- [ ] RIZALTA_CURRENT.md (дополнено)
- [ ] RIZALTA_TASKS.md (дополнено)
- [ ] RIZALTA_CONTEXT.md (если нужно)

**Коммиты:**
- [ ] webapp (ветка webapp)
- [ ] bot-dev (docs/)
- [ ] bot PROD (docs/)

**Промпт для нового чата выдан:** [ ]
