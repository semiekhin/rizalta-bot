# 🏁 ШАБЛОН ЗАВЕРШЕНИЯ СЕССИИ

При команде "ЗАВЕРШАЕМ СЕССИЮ" Claude должен:

1. Обновить docs/*.md в DEV
2. Скопировать в PROD
3. Коммит оба репо
4. Выдать блок ниже

---

## 📋 БЛОК ДЛЯ НОВОГО ЧАТА
```
[Содержимое RIZALTA_CONTEXT.md]

---

[Содержимое RIZALTA_CURRENT.md]

---

Перед началом работы уточни: есть ли доступ к серверу?
Если нужны детали — читай документацию с сервера: cat /opt/bot-dev/docs/RIZALTA_*.md
```

---

## 📎 ОБЯЗАТЕЛЬНО: Ссылки на документы GitHub

**DEV (основные для чтения):**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_ARCHITECTURE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_KNOWLEDGE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/docs/RIZALTA_TASKS.md

**PROD:**
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CONTEXT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_CURRENT.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_ARCHITECTURE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_KNOWLEDGE.md
- https://raw.githubusercontent.com/semiekhin/rizalta-bot/main/docs/RIZALTA_TASKS.md

**Репозитории:**
- https://github.com/semiekhin/rizalta-bot
- https://github.com/semiekhin/rizalta-bot-dev
- https://github.com/semiekhin/rizalta-miniapp

---

## ✅ Итоги сессии [ДАТА]

[Список что сделано]
