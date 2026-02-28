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

## 📋 ШАГ 4: Выдать ПОЛНЫЙ промпт для нового webapp-чата

Формат промпта:

```
# ⚠️ ВНИМАНИЕ: Два параллельных чата!
# Этот чат = WEBAPP (/opt/webapp, /opt/webapp-dev)
# Соседний чат = БОТ (/opt/bot, /opt/bot-dev)
# Общие docs (bot-dev/docs/) — ДОПОЛНЯТЬ, НЕ затирать!
# Claude chat = архитектор, 1Code = реализация
# ⚠️ НЕ ПИШИ КОД И НЕ ВНОСИ ИЗМЕНЕНИЯ если не уверен на 100%!

---

# RIZALTA WebApp — контекст сессии

## Сервер
ssh -p 2222 root@72.56.64.91

## Версии
- **WebApp:** v[X.X.X]
- **Бот:** v[X.X.X] (не трогаем)

## Среды
[таблица DEV/PROD: URL, путь, порт, systemd, favicon]

## DevOps Pipeline
[webhook, deploy-to-prod.sh, session-end.sh]

## Репозитории
[3 репо: webapp ветка, bot-dev, bot-prod]

## Стек
[Frontend, Backend, AI, PDF, БД]

## Критически важно — НЕ ТРОГАТЬ
[/opt/bot, /opt/bot-dev, /opt/webapp PROD, properties.db]

## Что сделано (последние сессии)
[2-3 последние сессии с датами и ключевыми изменениями]

## Бэклог (актуализирован [ДАТА])
[🔴 Ближайшие, 🟡 Средний приоритет, 🟢 Nice-to-have]

## Workflow разработки
1. Claude chat — архитектура, ТЗ, анализ
2. 1Code (Mac: cd ~/1code && bun run dev) — реализация
3. Push → GitHub → DEV auto-deploy (webhook)
4. Проверка на DEV
5. Деплой: bash /opt/webapp-dev/deploy-to-prod.sh

## Git теги
[все теги с описаниями]

## Документация

### GitHub DEV:
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_ARCHITECTURE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_KNOWLEDGE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_TASKS.md

### GitHub PROD:
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_TASKS.md

### WebApp:
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/CLAUDE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/TASK_MAP.md

### Шаблон завершения сессии:
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/SESSION_END_TEMPLATE_WEBAPP.md

---

При команде "завершаем сессию" или "новый чат" — ОБЯЗАТЕЛЬНО:
1. Скачать SESSION_END_TEMPLATE_WEBAPP.md
2. Обновить ВСЕ docs (дополнять, НЕ затирать)
3. Коммит: bash /opt/webapp-dev/session-end.sh
4. Выдать ПОЛНЫЙ промпт для нового чата

---

Перед началом работы прочитай CLAUDE.md и TASK_MAP.md.
Первая задача — [описание следующей задачи].
```

---

## 📎 Ссылки на документы GitHub

**WebApp (ветка webapp):**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/CLAUDE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/TASK_MAP.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/SESSION_END_TEMPLATE_WEBAPP.md

**Общие docs DEV:**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_TASKS.md

**Общие docs PROD:**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_TASKS.md

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
