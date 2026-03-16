# 🏁 ШАБЛОН ЗАВЕРШЕНИЯ СЕССИИ — WEBAPP

При команде "ЗАВЕРШАЕМ СЕССИЮ" или "НОВЫЙ ЧАТ" Claude должен:

---

## 📝 ШАГ 1: Подготовить обновления документации

Claude выдаёт в чат **полный обновлённый контент** для:

### 1.1 Webapp docs (обновляет 1Code → push → webhook → DEV автоматически):

**`CLAUDE.md`** — обновить:
- Версию webapp
- Структуру (если менялись файлы)
- API endpoints (если добавлялись/менялись)
- Env переменные (если добавлялись)
- Git теги (если создавались)
- TODO (актуализировать)
- Добавить секцию сессии

**`TASK_MAP.md`** — обновить:
- Версию в шапке
- Перенести выполненное в ✅ ВЫПОЛНЕНО
- Актуализировать 🔜 БЭКЛОГ
- Обновить GIT ТЕГИ

### 1.2 Общие docs (bot-dev/docs/) — ⚠️ ДОПОЛНЯТЬ, НЕ ЗАТИРАТЬ:

**`/opt/bot-dev/docs/RIZALTA_CURRENT.md`** — добавить/обновить секцию `## WebApp`
**`/opt/bot-dev/docs/RIZALTA_TASKS.md`** — добавить/обновить секцию `## WebApp`

⚠️ Эти файлы редактирует и бот-чат — дополняем свою секцию, чужое НЕ трогаем!

---

## 📤 ШАГ 2: Sergio передаёт контент в 1Code

1. Claude выдал обновлённые CLAUDE.md и TASK_MAP.md
2. Sergio копирует контент в 1Code
3. 1Code коммитит и пушит в ветку `webapp`:
```bash
git add CLAUDE.md TASK_MAP.md
git commit -m "docs: session [ДАТА] - [краткое описание]"
git push origin webapp
```
4. Webhook автоматически обновляет `/opt/webapp-dev/` (2-3 сек)
5. Ссылки `/api/docs/file` сразу отдают актуальное

---

## 📤 ШАГ 3: Общие docs — на сервере вручную

```bash
# Обновить общие docs в bot-dev (ДОПОЛНИТЬ секцию ## WebApp)
nano /opt/bot-dev/docs/RIZALTA_CURRENT.md
nano /opt/bot-dev/docs/RIZALTA_TASKS.md

# Скопировать в PROD
cp /opt/bot-dev/docs/RIZALTA_CURRENT.md /opt/bot/docs/
cp /opt/bot-dev/docs/RIZALTA_TASKS.md /opt/bot/docs/

# Закоммитить оба репо
cd /opt/bot-dev && git add docs/ && git commit -m "docs: webapp session [ДАТА]" && git push
cd /opt/bot && git add docs/ && git commit -m "docs: webapp session [ДАТА]" && git push
```

Или: `bash /opt/webapp-dev/session-end.sh` (коммитит bot-dev + bot)

---

## 📋 ШАГ 4: Выдать КОМПАКТНЫЙ промпт для нового webapp-чата

```
# ⚠️ ВНИМАНИЕ: Два параллельных чата!
# Этот чат = WEBAPP, Claude = архитектор, 1Code = реализация
# ⚠️ ЧИТАЙ ДОКУМЕНТАЦИЮ С СЕРВЕРА, НЕ ПРИДУМЫВАЙ!

Подтяни контекст:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=CLAUDE.md
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=TASK_MAP.md

Шаблон завершения:
https://dev-webapp.rizaltaservice.ru/api/docs/file?path=SESSION_END_TEMPLATE_WEBAPP.md

Первая задача — [описание следующей задачи].
```

---

## ✅ Чеклист сессии [ДАТА]

**Версия:** v[X.X.X] → v[X.X.X]

**Что сделано:**
- [ ] ...

**Docs обновлены через 1Code (webhook → DEV):**
- [ ] CLAUDE.md
- [ ] TASK_MAP.md

**Общие docs обновлены на сервере:**
- [ ] RIZALTA_CURRENT.md (дополнено)
- [ ] RIZALTA_TASKS.md (дополнено)
- [ ] bot-dev закоммичен
- [ ] bot PROD закоммичен

**Промпт для нового чата выдан:** [ ]
