# 🏁 ШАБЛОН ЗАВЕРШЕНИЯ СЕССИИ — WEBAPP

При команде "ЗАВЕРШАЕМ СЕССИЮ" или "Переходим в новый чат" Claude должен:

## 📝 ШАГ 1: Обновить документацию

Обновить docs/*.md:
- `WEBAPP_CURRENT.md` — текущий статус, версия, что сделано
- `WEBAPP_TASKS.md` — бэклог (добавить/убрать задачи)
- `WEBAPP_CONTEXT.md` — если менялся контекст

---

## 📦 ШАГ 2: Коммит и пуш
```bash
cd /opt/webapp
git add -A && git commit -m "docs: session [ДАТА] - [краткое описание]"
git push
```

---

## 📋 ШАГ 3: Выдать блок для нового чата

Сформировать инструкцию из WEBAPP_CONTEXT.md + WEBAPP_CURRENT.md

---

## ⚠️ КРИТИЧЕСКИЕ ПРАВИЛА
```
PROD /opt/bot (8000) — НЕ ТРОГАТЬ!
DEV /opt/bot-dev (8002) — НЕ ТРОГАТЬ!
Работаем ТОЛЬКО в /opt/webapp/
```

---

## 📎 Ссылки GitHub (ветка webapp)

**Документация:**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/docs/WEBAPP_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/docs/WEBAPP_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/docs/WEBAPP_TASKS.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/webapp/docs/SESSION_END_TEMPLATE.md

**Репозиторий:**
- https://github.com/semiekhin/rizalta-bot/tree/webapp

**Сервер:**
```
ssh -p 2222 root@72.56.64.91
```

**URL:**
- https://webapp.rizaltaservice.ru/

---

## ✅ Итоги сессии [ДАТА]

**Версия:** [X.X.X]

**Что сделано:**
- [ ] ...

**Обновлены файлы:**
- [ ] WEBAPP_CURRENT.md
- [ ] WEBAPP_TASKS.md
- [ ] ...
