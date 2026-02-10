# Текущий статус RIZALTA

📅 **Последняя сессия:** 10.02.2026
🏷️ **Версия:** 2.5.10

## ✅ Что сделано (09.02.2026)

### Критический фикс: handle_kp_building_all (500 ошибка)
- **Баг:** кнопка «📋 Все лоты корпуса» вызывала ImportError — функция не была написана
- **Симптомы:** 500 Internal Server Error, Telegram ретраил запросы 5-6 раз, пользователи видели бесконечный спиннер
- **Пострадавшие:** Дмитрий (@dimpo_krd), Елена Кузнецова (@Elena_Kuznecova_sirius)
- **Решение:** написана функция handle_kp_building_all в handlers/kp.py — показ всех лотов корпуса с пагинацией через _search_cache
- **Изменённый файл:** handlers/kp.py (DEV + PROD)

### Документация: ARCHITECTURE.md + CALLBACKS.md
- **RIZALTA_ARCHITECTURE.md** — карта проекта: структура, модули по функциям, callback chains, grep-индекс, типовые операции
- **RIZALTA_CALLBACKS.md** — полный индекс ~120 callback паттернов с обработчиками и файлами
- **Цель:** LLM-ассистент ориентируется в проекте без чтения всего кода


### WebApp: Phase 1-2 завершены (09-10.02.2026)
- **Полный аудит** webapp v0.3.0: codebase, gap-анализ vs бот, техдолг
- **Фирменный стиль RIZALTA** применён: палитра #263524/#F2EBD9/#D4A84B, Montserrat, лого
- **UI/UX переделка**: 10 экранов вместо 4, навбар 3 кнопки (Главная/Чат/Лоты)
- **Меню главная**: сетка 2×4 как в боте (Лоты, Презентации, Чат, Секретарь, Договоры, Медиа, Фиксация, Новости)
- **Фильтры в каталоге**: по площади (от/до м²) и цене (от/до млн ₽)
- **6 новых страниц**: Presentations, Documents, Media, News, Secretary (заглушка), Fixation (заглушка), Booking
- **Backend**: 4 новых endpoints (файлы презентаций/договоров/видео + курсы валют ЦБ)
- **Модалки ROI/Депозит**: таблица по годам, детализация, преимущество RIZALTA, кнопки скачивания
- **CLAUDE.md + TASK_MAP.md** в репо для Claude Code (1Code)
- **Workflow**: разработка через 1Code (Opus 4.6) → git push → git pull на сервере → npm run build
- **Версия webapp:** v0.5.0 (ветка webapp)

## 🔄 Текущее состояние

- **PROD:** работает ✅ v2.5.10
- **DEV:** работает ✅ v2.5.10
- **Корпус 1 «Family»:** 255 лотов (properties.db)
- **Корпус 2 «Business»:** 103 лота (properties.db), открыт
- **Корпус 3 «Digital»:** 282 лота (corp3_units.json, whitelist)
- **Mini App Vercel:** работает ✅
- **Watchdog:** работает ✅
- **WebApp:** работает ✅ v0.6.0 (webapp.rizaltaservice.ru)

## 🔜 Следующие задачи

1. 🟡 **Деплой ипотечного калькулятора** — готов в DEV
2. 🟡 **Вопрос "11 лет / полный цикл"** — уточнить формулировку (2035 vs 2036)
3. 🟡 **Админ-панель** — типовые операции
4. 🟡 Миграция на российский сервер
5. 🟡 **Модульные README** — handlers/README.md, services/README.md
6. 🟢 **WebApp Phase 3.1** — белый список + Корпус 3 + systemd ✅
7. 🔴 **WebApp Phase 3.2** — AI чат (DeepSeek V3.2), отправка заявок



### WebApp: Phase 3.1 — Белый список + Корпус 3 + systemd (10.02.2026)
- **Белый список (токен):** webapp.db + access_tokens, общий токен через URL (?token=XXX)
- **Корпус 3 в webapp:** Corp3.jsx (шахматка, фильтры), /api/corp3/lots, /api/corp3/layout/{code}
- **Auth система:** utils/auth.js (captureTokenFromURL, verifyAccess, authFetch)
- **Home.jsx:** условная кнопка «🏗 Корпус 3» с золотой рамкой (только для white)
- **LotDetail.jsx:** поддержка лотов К3 (маппинг полей, скрыты КП/Excel)
- **Catalog.jsx:** упрощены кнопки фильтров: [Свободно] + [Фильтры] (убраны Все/Бронь/Продано)
- **systemd:** webapp.service (автозапуск, Restart=always)
- **Версия webapp:** v0.6.0 (ветка webapp)
