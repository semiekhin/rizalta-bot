# ЗАВЕРШЕНИЕ СЕССИИ — ОБНОВИ ДОКУМЕНТАЦИЮ ДЛЯ НОВОГО ЧАТА

Тебе нужно обновить два файла документации и запушить их на GitHub.

## 1. CLAUDE.md
ОБНОВИ секции:
```markdown
## Версия: X.X.X

## Последняя сессия: [ДАТА]
- ✅ [что сделано — каждый пункт конкретно]
- ✅ [что было → что стало]

## TODO
- [ ] [что осталось сделать]
- [ ] [известные проблемы]
```

---

## 2. PROJECT_HISTORY.md
ДОБАВЬ в секцию "Хронология разработки":
```markdown
**[ДАТА] — [Название сессии]**
- Что сделано
- Какие проблемы решили
- Архитектурные решения (если были)
```

Если были важные уроки — добавь в секцию "Уроки и принципы".

---

## 3. RIZALTA_KNOWLEDGE.md (если менялась бизнес-логика)
ДОБАВЬ:
- Новые правила расчётов
- Изменения в данных о недвижимости

---

## 4. Git push
```bash
cd /opt/bot-dev
git add -A
git commit -m "vX.X.X: краткое описание изменений"
git push

# Если нужно синхронизировать prod
cd /opt/bot
git add -A  
git commit -m "vX.X.X: краткое описание изменений"
git push
```

---

## 5. Дай мне блок для нового чата

Выведи готовый текст для копирования:
- Краткое описание что было сделано
- Что нужно делать дальше
- Ссылки на документы

---

## 6. Прикрепи ссылки на все файлы:

**GitHub репо:**
https://github.com/semiekhin/rizalta-bot-dev

**Документация:**
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/CLAUDE.md
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/PROJECT_HISTORY.md
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/RIZALTA_KNOWLEDGE.md
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/SECURITY_OPERATIONS.md
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/RESTORE.md
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/README.md

**Главный файл:**
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/app.py

**Handlers:**
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/__init__.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/ai_chat.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/booking_calendar.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/calc_dynamic.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/docs.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/kp.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/media.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/menu.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/news.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/handlers/units.py

**Services:**
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/ai_chat.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/calculations.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/calc_xlsx_generator.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/investment_calc.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/kp_pdf_generator.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/notifications.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/parser_rclick.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/speech.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/telegram.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/services/units_db.py

**Config:**
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/config/settings.py
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/config/instructions.txt

**Data:**
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/data/units.json
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/data/rizalta_finance.json
https://raw.githubusercontent.com/semiekhin/rizalta-bot-dev/main/data/rizalta_knowledge_base.txt

**Стандарт разработчика:**
https://github.com/semiekhin/developer-standards
