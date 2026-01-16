# 🏁 ШАБЛОН ЗАВЕРШЕНИЯ СЕССИИ

При команде "ЗАВЕРШАЕМ СЕССИЮ" Claude должен:

## 📝 ШАГ 1: Обновить документацию

### 1.1 Обновить стандартные docs/*.md в DEV:
- `RIZALTA_CURRENT.md` — текущий статус, версия, что сделано
- `RIZALTA_TASKS.md` — бэклог (добавить/убрать задачи)
- `RIZALTA_KNOWLEDGE.md` — если были новые нюансы/решения
- `RIZALTA_ARCHITECTURE.md` — если менялась архитектура

### 1.2 ⭐ ОБЯЗАТЕЛЬНО: Обновить OLLAMA_RIZALTA.md

Добавить в файл `/opt/bot-dev/docs/OLLAMA_RIZALTA.md`:

**Если была решена новая задача** → добавить в раздел "ТИПОВЫЕ ЗАДАЧИ":
```markdown
### ЗАДАЧА N: Краткое описание

**Файлы:** какие файлы затронуты

**Шаги:**
1. ...
2. ...

**Команды:**
```bash
# команды
```

**Проверка:**
```bash
# как проверить что всё работает
```
```

**Если был инцидент** → добавить в раздел "ИНЦИДЕНТЫ И РЕШЕНИЯ":
```markdown
### ИНЦИДЕНТ N: Краткое описание

**Симптомы:** что наблюдалось

**Диагностика:**
```bash
# команды диагностики
```

**Причина:** что оказалось причиной

**Решение:**
```bash
# команды решения
```
```

**Если изменилась инфраструктура** → обновить соответствующий раздел:
- Сетевая инфраструктура
- Systemd сервисы
- Watchdog
- Бэкапы

---

## 📤 ШАГ 2: Скопировать в PROD

```bash
# Копировать обновлённые файлы
cp /opt/bot-dev/docs/RIZALTA_CURRENT.md /opt/bot/docs/
cp /opt/bot-dev/docs/RIZALTA_TASKS.md /opt/bot/docs/
cp /opt/bot-dev/docs/OLLAMA_RIZALTA.md /opt/bot/docs/
# ... и другие изменённые файлы
```

---

## 📦 ШАГ 3: Коммит оба репо

```bash
# DEV
cd /opt/bot-dev
git add -A && git commit -m "docs: session [ДАТА] - [краткое описание]" && git push

# PROD
cd /opt/bot
git add -A && git commit -m "docs: session [ДАТА] - [краткое описание]" && git push
```

---

## 📋 ШАГ 4: Выдать блок для нового чата

```
[Содержимое RIZALTA_CONTEXT.md]

---

[Содержимое RIZALTA_CURRENT.md]

---

Перед началом работы уточни: есть ли доступ к серверу?
Если нужны детали — читай документацию: cat /opt/bot-dev/docs/RIZALTA_*.md
```

---

## 📎 Ссылки на документы GitHub

**DEV (основные для чтения):**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_ARCHITECTURE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_KNOWLEDGE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_TASKS.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/OLLAMA_RIZALTA.md

**PROD:**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_ARCHITECTURE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_KNOWLEDGE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_TASKS.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/OLLAMA_RIZALTA.md

**Репозитории:**
- https://github.com/semiekhin/rizalta-bot
- https://github.com/semiekhin/rizalta-bot-dev
- https://github.com/semiekhin/rizalta-miniapp

---

## ✅ Итоги сессии [ДАТА]

**Версия:** [X.X.X]

**Что сделано:**
- [ ] Задача 1
- [ ] Задача 2

**Обновлены файлы:**
- [ ] RIZALTA_CURRENT.md
- [ ] RIZALTA_TASKS.md
- [ ] OLLAMA_RIZALTA.md
- [ ] Другие...

**Добавлено в OLLAMA_RIZALTA.md:**
- [ ] Новая задача: ...
- [ ] Новый инцидент: ...
- [ ] Изменения инфраструктуры: ...
