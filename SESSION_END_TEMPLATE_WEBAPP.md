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
- Добавить секцию сессии

**`/opt/webapp-dev/TASK_MAP.md`** — обновить:
- Версию в шапке
- Перенести выполненное в ✅ ВЫПОЛНЕНО
- Актуализировать 🔜 БЭКЛОГ
- Обновить GIT ТЕГИ

### 1.2 Общие docs (bot-dev/docs/) — ⚠️ ДОПОЛНЯТЬ, НЕ ЗАТИРАТЬ:

**`/opt/bot-dev/docs/RIZALTA_CURRENT.md`** — добавить/обновить секцию `## WebApp`:
- Версия, что сделано в этой сессии

**`/opt/bot-dev/docs/RIZALTA_TASKS.md`** — добавить/обновить секцию `## WebApp`:
- Выполненные, новые, изменённые приоритеты

⚠️ Эти файлы редактирует и бот-чат — дополняем свою секцию, чужое НЕ трогаем!

---

## 📤 ШАГ 2: Скопировать общие docs в PROD

```bash
cp /opt/bot-dev/docs/RIZALTA_CURRENT.md /opt/bot/docs/
cp /opt/bot-dev/docs/RIZALTA_TASKS.md /opt/bot/docs/
```

---

## 📦 ШАГ 3: Коммит 3 репо

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

## 📋 ШАГ 4: Выдать КОМПАКТНЫЙ промпт для нового webapp-чата

⚠️ Промпт — КОМПАКТНЫЙ. Вся детальная информация в CLAUDE.md и TASK_MAP.md на сервере.
Claude в новом чате сам прочитает их через API.

```
# ⚠️ ВНИМАНИЕ: Два параллельных чата!
# Этот чат = WEBAPP, Claude = архитектор, 1Code = реализация
# ⚠️ ЧИТАЙ ДОКУМЕНТАЦИЮ С СЕРВЕРА, НЕ ПРИДУМЫВАЙ!

Подтяни контекст:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=CLAUDE.md
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=TASK_MAP.md

Шаблон завершения:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=SESSION_END_TEMPLATE_WEBAPP.md

[⚠️ Если доки не обновились — описать что нужно обновить]

Первая задача — [описание следующей задачи].

[Ссылки на код для анализа, если нужно:]
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=путь/к/файлу
```

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

**Коммиты:**
- [ ] webapp (ветка webapp)
- [ ] bot-dev (docs/)
- [ ] bot PROD (docs/)

**Промпт для нового чата выдан:** [ ]
