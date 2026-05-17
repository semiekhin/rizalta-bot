# SESSION_LOG — Последние сессии

## 17.05.2026 — Дашборд: Итого над списком (mobile) + кликабельное «Из них с бронью»; разведка справочника агентств

**Сделано:**
- **Группа A — разведка справочника агентств** (только чтение). Снят полный distinct по `realtor_agency` в PROD `shows.db` (24 уникальных значения, 71 показ). Подтверждены три параллельных написания `ПроСторе Сочи` (13) / `Простор` (8) / `Простор Сочи` (2), `Рич` (1), отсутствие `КП Реал Эстейт`. Дополнительно вскрыты 9 free-text названий вне `AGENCIES` (`Лехто ИП`, `Домрил` vs `ДомРил`, `АН Самолёт г. Самара`, `Блэкаут`, `ИП Лехто`, `ИП Панченко`, `ИП Самсонова Л.Ю. Краснодар`, `Лето` vs `Лето Недвижимость`, `Сириус` vs `Сириус Групп`) + 4 показа с пустым `realtor_agency`. План мерджа отложен в отдельную сессию (см. BACKLOG P2).
- **Группа B — Итого на мобильном + кликабельное «Из них с бронью»** (v0.9.13). `ShowsDashboard.jsx`: карточка Итого перенесена в начало мобильной секции «Сводка» (золотая рамка через `highlight`); `ManagerCard` расширен пропсом `bookedClickable` — в режиме Итого все цифры приглушены (`text-rz-cream-muted`), кроме «из них с бронью» — золотая, кликабельная, с hover + active feedback. Заголовок «Итого» некликабелен. Desktop-таблица не двигалась: Итого осталась последней строкой, onClick + cursor-pointer + hover навешан ровно на `<td>` с `completed_booked`. При `completed_booked === 0` ячейка приглушена и не кликабельна. `openDrilldown` принимает `value=null` (Итого без фильтра), guard `value === 'Итого'` снят; useEffect drill-down не сериализует `filter_manager/filter_agency` при пустом value; `BreakdownSheet` показывает «Все · По агентствам» / «Все · По менеджерам» когда value пустой.
- **Деплой v0.9.12 → v0.9.13 в PROD** через `deploy-to-prod.sh`. Бэкап `shows-manual-2026-05-17_2314-pre-deploy-0913.db.gz` (5439 b, gunzip -t OK). Post-deploy: count 71/5/23 идентичен baseline, `/stats` и `/list` 200, логи без stack trace.

**Файлы:** frontend/src/pages/ShowsDashboard.jsx (+44/-21), backend/app.py (bump 2 строки)

**Коммиты:** ef8effc (фича), 8d7a49d (bump)

**Решения:**
- **Расширили `ManagerCard` пропсом `bookedClickable` вместо нового `TotalsCard`** — компонент уже параметризован (`highlight`, `clickable`, `defaultSort`), per-cell логика добавилась 4 строками. Отдельный компонент дал бы дублирование 30-строчного grid'а без выгоды.
- **`openDrilldown(value, sortBy)` принимает `value=null`** — семантика `drilldown.dimension` («измерение карточки») не сломалась: для Итого это всё то же противоположное измерение в sheet, просто без `filter_X` в запросе. Старый guard `value === 'Итого'` стал активной помехой и снят.
- **Desktop Итого: onClick на конкретной `<td>`, не на `<tr>`** — hover, отличающийся от row-hover остальных строк, работает как правильный визуальный сигнал «кликабельна только эта цифра». Симметрия с mobile сохранена через одну общую `openDrilldown(null, 'completed_booked')`.
- **При `completed_booked === 0` цифра приглушена и не кликабельна** — нет смысла открывать пустой sheet. Логика в одном месте (`Number(s.completed_booked) > 0`) и на mobile, и на desktop.
- **Tap-feedback на тач:** `active:bg-rz-green-mid/40` параллельно с `hover:` — те же классы что у обычных кликабельных ячеек, без отдельной ветки.

**Контекст:**
- **SQLite `LOWER()` не работает с кириллицей** по умолчанию — фуззи-поиск из шага 6 Группы A молча вернул пусто. На будущее для case-insensitive поиска по кириллице нужен либо `COLLATE NOCASE` (тоже работает только для ASCII), либо явный `LIKE` с обоими регистрами, либо приведение в Python. В этой сессии обошлись чтением полного distinct из шага 2 (всего 24 значения).
- В PROD `shows.db` помимо 26 значений из `AGENCIES` живут 9 free-text названий и 4 пустых — поле `realtor_agency` где-то принимает свободный ввод (предположительно input с `<datalist>` подсказками из v0.9.9, см. SESSION_LOG 06.05.2026). Это не баг — это сознательное решение «не блокировать создание показов на ранней фазе». Будущая нормализация в Группе A.
- Версия 0.9.12 → 0.9.13 — только за счёт UI-правки на дашборде, без backend-изменений; deploy-to-prod.sh прошёл без warning'а Continue anyway.

**Не трогали:**
- `shows.db` (count 71/5/23 не изменился; никаких UPDATE/DELETE)
- `AGENCIES`, `MANAGERS`, schema `shows.db`
- Backend (нулевое касание services/app.py за исключением version bump)
- `BreakdownSheet` поведение кроме одной строки title
- `/opt/bot*`, `.env`, crontab

**Следующий шаг:** Группа A — выполнение мерджа агентств: канонизация `ПроСторе Сочи` (merge 3 написаний → 23 показа), добавление `КП Реал Эстейт`, переименование `Рич` → `Рич групп`. С обязательным бэкапом PROD перед UPDATE. Параллельно решить с Сергеем что делать с 9 free-text названиями и 4 пустыми agency.

---

## 14.05.2026 — Дашборд показов: toggle + drill-down + «Показать» + сортировка; Telegram-бэкап

**Сделано:**
- **ETAP 1 — toggle «По менеджерам / По агентствам»** (v0.9.11). Бэкенд: `get_stats_by_agency` (GROUP BY агентство, `COALESCE(NULLIF(...))` → 'Без агентства', сортировка booking_rate ASC, None в конец); `/api/shows/dashboard/stats` принимает `group_by`, невалидное → fallback на manager. Фронт: toggle-капсула, заголовок секции и колонка таблицы по режиму, красные флаги только в manager-режиме.
- **ETAP 2 — drill-down** (v0.9.11). Бэкенд: `/stats` расширен `filter_manager`/`filter_agency`/`sort_by`; хелперы `_sort_stats` + `_add_conducted`; поле `conducted` в каждой строке; 400 на конфликт `filter_X`+`group_by=X`; zero-fill отключается при наличии фильтра. Фронт: `components/Modal.jsx` вынесен из `Shows.jsx` (+ опц. prop `handle`); `BreakdownSheet` — тап на цифру/имя карточки или ячейку таблицы открывает разбивку по обратному измерению, индикатор сортировки ↓, AbortController против гонки.
- **ETAP 3 — кнопка «Показать»** (v0.9.11). Список «Все показы» больше не грузится автоматически: `load()` разделён на `loadStats()`/`loadList()`; новый стейт `listLoaded`/`listSnapshot`/`listLoading`/`listError`; плашка «Фильтры изменены»; «Обновить» в шапке трогает список только если он уже был загружен.
- **ETAP 4 — выбор сортировки в режиме агентств** (v0.9.12). Дропдаун (7 опций) виден только при `groupBy === 'agency'`; `agencySortBy` переживает переключение toggle. Бэкенд не трогали — `sort_by` уже был с ETAP 2.
- **2 деплоя в PROD:** v0.9.10→0.9.11 (toggle + drill-down + «Показать»), v0.9.11→0.9.12 (сортировка). Оба с бэкапом PROD `shows.db`, smoke-тестами, count 55/5/19 не изменился.
- **`backup_shows.py` — Telegram-уведомление** ✅/❌ о статусе ежедневного бэкапа; cron перенесён 03:30 → 20:01 МСК.
- **Фикс адресата Telegram-бэкапа:** уведомление уходило в группу «Показы Rizalta» (`MANAGER_CHAT_ID`). Разведка: webapp и `/opt/bot` используют один бот `@RealtMeAI_bot` (токены идентичны). Введена env-переменная `ADMIN_CHAT_ID=512319063` (личный чат Сергея, как в `monitoring.py`), скрипт шлёт через `send_telegram_message` напрямую.
- **Инфра:** origin в `/opt/webapp-dev` переключён HTTPS → SSH (`git@github.com:...`) — `.git-credentials` был пустой, push требовал логин; ключ `~/.ssh/github_oazis` работает.

**Файлы:** backend/services/shows_service.py, backend/app.py, frontend/src/pages/ShowsDashboard.jsx, frontend/src/pages/Shows.jsx, frontend/src/components/Modal.jsx (новый), backend/scripts/backup_shows.py, .env (DEV+PROD: +ADMIN_CHAT_ID), crontab PROD

**Коммиты:** 08e257c, 524ac81, b9e92c9, 0dd5914, 979eedc, b1efd41, 276a4b0, e479439

**Решения:**
- `booking_rate` для агентств считается как у менеджеров — `completed_booked/(completed+completed_booked)`, не `/completed`: буквальная формула из ТЗ дала бы метрику, несопоставимую с manager-режимом.
- `Modal` вынесен в общий компонент (не дублирование) — рефактор `Shows.jsx` без смены поведения.
- Drill-down sheet НЕ закрывается при смене сортировки главных карточек — независимый контекст.
- `ADMIN_CHAT_ID` — нейтральное имя, переиспользуется для будущих инфра-уведомлений; `MANAGER_CHAT_ID` оставлен для `notify_showing_request` (группа показов — правильный адрес для заявок).
- `backup_shows.py` читает `.env` через `load_dotenv()` — рестарт `webapp.service` не нужен.
- Версия не бампилась для инфра-изменений (backup script) — `deploy-to-prod.sh` проходился через `echo y` на version-match guard.

**Контекст:**
- CLAUDE.md всё ещё указывает cron бэкапа `30 3 * * *` — устарел, реально `1 20 * * *` (см. BACKLOG P3).
- Первое автоматическое срабатывание нового cron — 14.05.2026 в 20:01 МСК.
- PROD имеет строки с NULL/'' `realtor_agency` → в agency-режиме появляется бакет «Без агентства» (в DEV таких нет).

**Не трогали:**
- `/opt/bot`, `/opt/bot-dev`, `/opt/bot-max-dev`
- `notifications.py` (переиспользованы существующие функции)
- `MANAGER_CHAT_ID`, схема `shows.db`

**Следующий шаг:** restoration drill свежего 20:01-бэкапа (15.05.2026 утром).

---

## 06.05.2026 (поздняя ночь) — Универсальная защита от 18-мес. рассрочки по площади

**Сделано:**
- **Константа `CUSTOM_INSTALLMENT_MAX_AREA = 22.1`** в `backend/services/kp_pdf_generator.py` — имя 1-в-1 с `/opt/bot-max/config/settings.py` для будущей унификации в P2.
- **`is_custom` (строка ~236) расширен:** К1 AND (код в списке OR площадь ≤ 22.1). Защита от `area is None` встроена явно (без fallback на `0`, который дал бы false positive — `0 <= 22.1`).
- **Force-блок в `generate_kp_pdf` переписан** с `is_custom_force` и детализированным `reason` в логе: warning теперь различает причину срабатывания (`по списку` vs `по площади X м² ≤ 22.1`) — критично для post-mortem.
- **7 smoke-кейсов через monkeypatch + 2 negative через curl на DEV** — все зелёные. Граничный кейс (`area=22.1` ровно) отрабатывает как small_k1.
- **Деплой коммита `4b6752b` в PROD** через `deploy-to-prod.sh` с подтверждением `Continue anyway?` (версия не бампилась — это микро-расширение фикса 0.9.10).
- **PROD smoke-тесты прошли:** триггер по списку (В225) и триггер по площади (В119, 22.0) → `_12m.pdf` без 18м; negative (В119, 27.0 м²) → `_12m_18m.pdf`.

**Файлы:** backend/services/kp_pdf_generator.py, SESSION_LOG.md

**Решения:**
- **Защита по площади оставлена рядом со списком, не вместо него** (вариант B по обсуждению с Сергеем). Список — страховка от аномалий в данных (например, лот из CUSTOM-списка ошибочно импортирован с неправильной площадью). Удалить список — потеря бизнес-знания.
- **Defense in depth:** правка в двух местах (`is_custom` для layout 12-мес. секции + force-блок для отрисовки 18-мес. секции). Без второго правка списка не закрывала бы баг — это было ключевое открытие предыдущего этапа.
- **`area=None` защита: явное `is not None` вместо fallback `0`.** Fallback 0 дал бы false positive (`0 <= 22.1 = True`). Безопаснее не угадывать.
- **Имя константы `CUSTOM_INSTALLMENT_MAX_AREA = 22.1`** — 1-в-1 с bot-max. Когда P2 (унификация конфига) возьмётся в работу, переименовывать не придётся.
- **Версию не бампили:** микро-расширение фикса 0.9.10, не новая фича. На `/api/health` остаётся `0.9.10`.

**Контекст:**
- В PROD `properties.db` сейчас нет К1 ≤22.1 м² — правило срабатывает превентивно. Если такие лоты вернутся в каталог, в логах `webapp.service` появятся строки `[KP PDF] WARN принудительно отключаем 18-мес. секцию ...` — это индикатор работы защиты.
- Defensive логирование (warning при `building=None` + `reason` в force-блоке) даёт post-mortem-сигналы если ситуация повторится в неожиданной форме.

**Не трогали:**
- `.env`, crontab
- `/opt/bot`, `/opt/bot-dev`, `/opt/bot-max-dev`
- `frontend/src/pages/LotDetail.jsx` (скрытие кнопки «Полное КП» для custom — отложено в P2)
- `ShowsDashboard.jsx`
- `BACKLOG.md` — записи про унификацию бизнес-правила и про скрытие кнопки уже добавлены в предыдущем session end

**Следующий шаг:** мониторинг логов (warning'и из `kp_pdf_generator`). Через 2-3 недели — фаза 2 дашборда показов (статистика по агентствам + матрица менеджер×агентство), если данные накопятся. Параллельно — отдельная сессия по проекту бота (`/opt/bot/backup.sh` падает с превышением размера письма уже несколько дней).

---

## 06.05.2026 (вечер) — Справочник агентств (фаза 1) + bump 0.9.9

**Сделано:**
- **Константа `AGENCIES` (26 элементов) в `shows_service.py`** + новая функция `get_agencies()`. Список согласован с Сергеем: префиксы АН/ООО убраны, ёлочки у `ЭСТАДЕЛЬ` убраны, сортировка алфавитная case-insensitive. Включает обе разные организации `Интегрити` и `Интегрити 2`.
- **Новый endpoint `GET /api/shows/agencies`** — тонкая обёртка над `get_agencies()`, по паттерну `/api/shows/managers`.
- **`Shows.jsx`:** `useState(agencies)` + отдельный `useEffect` для `fetch /api/shows/agencies`. Один глобальный `<datalist id="rz-agencies-list">` на уровне компонента `Shows`. Атрибут `list="rz-agencies-list"` на input `realtor_agency` в обеих модалках (`CreateModal`, `EditModal`). Поведение: подсказки появляются при вводе, но поле принимает любой текст (свободный ввод сохранён, новые агентства не блокируются).
- **`seed_shows_test_data.py`:** удалён локальный список из 10 чужих агентств (Этажи/СамолётПлюс/...), `AGENCIES` импортируется из `shows_service` (DRY). Сид теперь генерирует тестовые данные на боевом списке.
- **Bump версии `0.9.8 → 0.9.9`** в `backend/app.py` (`FastAPI(title=..., version=...)` + `/api/health`). Поиск других hardcoded `0.9.8` в backend/frontend дал 0 совпадений вне этих двух точек.
- **Деплой коммитов `0916f4e` + `4468f88` в PROD** через `deploy-to-prod.sh` — прошёл без warning'а «Continue anyway?» (DEV `0.9.9` ≠ PROD `0.9.8`). Откат не понадобился.

**Файлы:** backend/services/shows_service.py, backend/app.py, backend/scripts/seed_shows_test_data.py, frontend/src/pages/Shows.jsx, SESSION_LOG.md, BACKLOG.md

**Решения:**
- **Хранение списка: константа в коде (вариант A)**, не JSON, не БД. Симметрично `MANAGERS`, простой деплой при добавлении нового агентства.
- **Свободный ввод сохранён** — `<datalist>` даёт подсказки, но не валидирует. Аргумент: на ранней фазе важнее не блокировать создание показов, чем чистая статистика. Нормализацию сделаем в фазе 2 если понадобится.
- **Один `<datalist>` на уровне `Shows` вместо дубликата в каждой модалке** — модалки условные (одна открыта за раз), конфликта `id` нет. Минус дублирования.
- **Bump версии перед деплоем — процессное правило**, закреплено вопросом `deploy-to-prod.sh` «Continue anyway?». Теперь версия в `/api/health` честно отражает что в проде. Добавил пункт в BACKLOG P3.
- **Бэкенд-валидацию НЕ вводили** — schema `realtor_agency TEXT` (nullable) не тронута, бэк принимает любые строки.

**Не трогали:**
- `ShowsDashboard.jsx` (фаза 2 — статистика по агентствам и матрица менеджер×агентство, через 2-3 недели после накопления данных)
- existing shows в БД (миграция не нужна)
- `.env`, `crontab`, чужие сервисы

**Следующий шаг:** накопление данных по показам в PROD; через 2-3 недели — фаза 2 задачи (статистика по агентствам + матрица менеджер×агентство).

---

## 06.05.2026 — +2 менеджера (6 итого) + ежедневный бэкап shows.db на email

**Сделано:**
- **+2 менеджера в шоу-календарь:** Васильченко Евгения, Товт Александра. `MANAGERS` в `backend/services/shows_service.py` 4 → 6, два новых `PROFILES` (средние показатели, без триггеров красных флагов) в `backend/scripts/seed_shows_test_data.py`, fallback-массив в `frontend/src/pages/Shows.jsx:154` синхронизирован. `GET /api/shows/managers` на PROD теперь возвращает 6 имён.
- **Ежедневный бэкап shows.db (новый скрипт):** `backend/scripts/backup_shows.py`. sqlite3 backup API (consistent snapshot) → gzip → `backend/backups/shows-YYYY-MM-DD.db.gz`. Локальная ротация 14 дней по mtime. Окружение определяется по `WEBAPP_ROOT`: на DEV — только локальный бэкап без email; на PROD — локальный + email с attachment. При неудаче email — `sys.exit(1)`, локальный файл сохраняется. В `services/notifications.py` добавлена `send_email_with_attachment()` рядом с существующей `send_email()`.
- **Отдельный `BACKUP_EMAIL` env-ключ с fallback на `MANAGER_EMAIL`:** `BACKUP_EMAIL = os.getenv("BACKUP_EMAIL") or os.getenv("MANAGER_EMAIL", "")`. Сделано после разведки: в `MANAGER_EMAIL` обнаружен посторонний адрес `dreaming2015@mail.ru` (происхождение неизвестно, в коде/других сервисах не упомянут, существует в `.env` минимум с 16.03.2026). Адрес продолжает получать продуктовые уведомления о заявках на показ (за последние 30 дней — 0 писем; за всю историю с 10.02.2026 — максимум 14 в feb 10–12 в тестовый период), но **не получает дамп БД**. `MANAGER_EMAIL` не тронут.
- **`.gitignore`:** `backend/backups/*` + `!backend/backups/.gitkeep` (negation для маркера папки). `git check-ignore` проверен: `.gitkeep` whitelisted, `.db.gz` ignored.
- **CLAUDE.md:** новая секция «Бэкап shows.db» — расписание, путь, ротация, процедура восстановления (4 команды).
- **Деплой в PROD** через `deploy-to-prod.sh`: `e6cea2a → 8d435a6`, версия 0.9.8 не бампилась, скрипт спросил `Continue anyway? y` (содержательно изменения есть, но пользовательски в /api/health версия не менялась). Откат не понадобился.
- **Первый ручной запуск бэкапа на PROD:** exit 0, `shows-2026-05-06.db.gz` создан (476 байт, исходная БД 20 KB / 0 строк), `gunzip -t` ok, `Email sent to 89181011091s@mail.ru`, `dreaming2015` в логах не упоминается, без `SMTPException`.

**Файлы:** backend/services/shows_service.py, backend/services/notifications.py, backend/scripts/backup_shows.py (new), backend/scripts/seed_shows_test_data.py, backend/backups/.gitkeep (new), frontend/src/pages/Shows.jsx, .gitignore, CLAUDE.md, BACKLOG.md

**Решения:**
- **Бэкап на отдельный `BACKUP_EMAIL`, не на `MANAGER_EMAIL`** — в MANAGER_EMAIL сидит посторонний `dreaming2015@mail.ru` неизвестного происхождения. Уведомления о заявках продолжают идти на оба адреса (как настроено), но тех. дамп БД не должен. Развилка через env-ключ, не правка `MANAGER_EMAIL` — не наша зона ответственности.
- **sqlite3 `src.backup(snap)`, не `gzip` живого файла** — базовая SQLite-гигиена бэкапов: при одновременной записи (которая ночью маловероятна, но возможна) gzip живого файла даст битый snapshot.
- **Cron только на PROD, не на DEV** — симметрия с ботом (`/opt/bot/backup.sh` бэкапит только PROD), DEV постоянно пересобирается seed-данными.
- **Версия 0.9.8 не бампилась** — содержательно для пользователя ничего нового (бэкап тех. процесс), 6 менеджеров — мелкая правка справочника. Бамп не нужен.
- **Захардкоженный список MANAGERS вместо БД-таблицы** — менеджеры меняются раз в полгода, валидация уже в нескольких местах (create_show, update_show, get_stats_by_manager), вынос в БД — overengineering.

**Следующий шаг:**
- Сергей применяет cron-строку на PROD (`30 3 * * * /opt/webapp/venv/bin/python /opt/webapp/backend/scripts/backup_shows.py >> /var/log/backup.log 2>&1`). После этого первое автосрабатывание — следующая ночь 03:30 МСК.
- Бонус-наблюдение (не наша территория): `/opt/bot/backup.sh` падает уже несколько дней с `(552, Message size exceeds maximum permitted)` — 86 MB архив бота не лезет в SMTP-лимит mail.ru. Передать Сергею для бот-стороны.

---

## 05.05.2026 — Календарь показов (этап 1+2) + ставки траншевой ипотеки + v0.9.8 в PROD

**Сделано:**
- **Календарь показов /shows (этап 1 MVP):** `frontend/src/pages/Shows.jsx` (601 стр), `backend/services/shows_service.py` + отдельная `shows.db`, эндпоинты `GET/POST/PUT/DELETE /api/shows`, `GET /api/shows/managers`. Упрощённая модель: 5 статусов (`planned/completed/completed_booked/rescheduled/cancelled`), минимум полей (datetime, manager, realtor_agency, realtor_name, comment). Кнопка «Создать показ» вместо плавающего FAB. Mobile-fix для нижней навигации.
- **Дашборд руководителя /shows/dashboard-84a11b0664 (этап 2):** `frontend/src/pages/ShowsDashboard.jsx` (365 стр), эндпоинты `GET /api/shows/dashboard/stats` + `/list`. Сводка по 4 менеджерам (Дегтярева/Шумова/Хватик/Панченко): всего/планируется/проведено/из них с бронью/перенесено/отменено/% броней. Пресеты периода (Сегодня/Вчера/Неделя/Месяц/Произвольный). Скрытый URL без авторизации, suffix статичен в `App.jsx` (`PATH_TO_SCREEN`). Колонки «Проведено» и «Проведено + бронь» объединены в одну с подстрокой «из них с бронью» (фикс a4e1edf).
- **Красные флаги — только для периодов ≥ 7 дней:** в `ShowsDashboard.jsx` добавлен `periodDays = round((to-from)/86400000)+1`, `flags = periodDays >= 7 ? buildFlags(stats) : []`. Существующий гейт `flags.length > 0` скрывает блок целиком (заголовок + грид). Логика: для пресетов «Сегодня»/«Вчера» (1 день) флаги бесполезны (мало данных); для «Эта неделя»/«Этот месяц»/custom ≥ 7 дней — работают как раньше (≥5 проведённых при `booking_rate < 20%`, либо `total < 3`).
- **Ставки траншевой ипотеки Сбербанк** (`backend/data/tranche_mortgage_config.json`) обновлены до соответствия боту: ПВ 20.1% 21.7→**21.2**, 30.1% 21.2→**19.7**, 40.1% 21.2→**19.7**, 50.1% 19.2→**19.0**. Размеры траншей, срок (240 мес.), период (8 мес.), сервисный сбор (150 000) НЕ трогали. Контрольные значения для лота 17 745 000 ₽: ПВ 30.1% Еп1=61 986 ₽, ПВ 50.1% Еп1=32 414 ₽ — сошлись.
- **Bump 0.9.7 → 0.9.8** (`backend/app.py`: FastAPI title + `/api/health`).
- **Деплой в PROD** через `deploy-to-prod.sh`: `8939d62 → b469ad7`, 11 файлов, +1647/-7. Restart ~5 сек. `/opt/webapp/backend/shows.db` создалась автоматически (lifespan `init_shows_db()`, `CREATE TABLE IF NOT EXISTS`). Откат не понадобился. PROD `/api/health` → v0.9.8.

**Файлы:** backend/app.py, backend/data/tranche_mortgage_config.json, backend/services/shows_service.py (new), backend/scripts/seed_shows_test_data.py (new), frontend/src/App.jsx, frontend/src/pages/Shows.jsx (new), frontend/src/pages/ShowsDashboard.jsx (new), CLAUDE.md, BACKLOG.md, .gitignore (`backend/shows.db*`)

**Решения:**
- **shows.db отдельная**, не в `properties.db` — show-это webapp-only сущность, общая БД остаётся read-only для webapp по units. `MANAGERS` — константа в коде, не в БД (4 менеджера фиксированы).
- **Скрытый URL без авторизации** (suffix `84a11b0664` в `PATH_TO_SCREEN`) — не защита, а obscurity. Дашборд внутренний, доступ контролируется ссылкой. Для публичного — нужна `auth.js` (P2 К4 whitelist).
- **Тестовые данные seed** оставлены как `backend/scripts/seed_shows_test_data.py` (детерминированная аллокация менеджеров в спеку 30-50 показов) — для DEV-проверки дашборда. Перед PROD-деплоем `DELETE FROM shows;` (БД в `.gitignore`, в PROD создалась пустой).
- **Красные флаги < 7 дней не показывать** — на коротких окнах статистика недостоверна (4 проведённых за день не значит «низкая конверсия»). Порог 7 дней совпадает с минимальным «осмысленным» периодом.
- **Точечный `git add` вместо `-A`** — в репо 1930 файлов `venv/*` уже tracked (закоммичены до того как `venv/` попал в `.gitignore`), `-A` втянул бы их в коммит. Зачистка `git rm --cached venv/` отдельной задачей в P2.

**Следующий шаг:** наблюдение PROD-дашборда; справочник агентств + матрица «менеджер × агентство» (P2)

---

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

