# RIZALTA BOT — Инструкция для нового чата

## Проект

**RIZALTA Telegram Bot** — AI-консультант для риэлторов по продаже курортной недвижимости в Белокурихе (Алтай).

- Telegram: @RealtMeAI_bot
- Сервер: 72.56.64.91 (Timeweb, Ubuntu 24.04)
- GitHub: https://github.com/semiekhin/rizalta-bot

---

## Ссылки на все файлы (GitHub)

### Документация
- [RIZALTA_PROJECT.md](https://github.com/semiekhin/rizalta-bot/blob/main/RIZALTA_PROJECT.md) — описание проекта
- [RIZALTA_CURRENT_TASK.md](https://github.com/semiekhin/rizalta-bot/blob/main/RIZALTA_CURRENT_TASK.md) — текущие задачи
- [RIZALTA_KNOWLEDGE.md](https://github.com/semiekhin/rizalta-bot/blob/main/RIZALTA_KNOWLEDGE.md) — техническая база
- [RIZALTA_INSTRUCTION.md](https://github.com/semiekhin/rizalta-bot/blob/main/RIZALTA_INSTRUCTION.md) — эта инструкция
- [README.md](https://github.com/semiekhin/rizalta-bot/blob/main/README.md)

### Главные файлы
- [app.py](https://github.com/semiekhin/rizalta-bot/blob/main/app.py) — главный файл, webhook, роутинг
- [requirements.txt](https://github.com/semiekhin/rizalta-bot/blob/main/requirements.txt) — зависимости
- [.env.example](https://github.com/semiekhin/rizalta-bot/blob/main/.env.example) — пример конфигурации

### config/
- [config/settings.py](https://github.com/semiekhin/rizalta-bot/blob/main/config/settings.py) — настройки

### handlers/
- [handlers/__init__.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/__init__.py) — экспорт обработчиков
- [handlers/menu.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/menu.py) — главное меню
- [handlers/ai_chat.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/ai_chat.py) — AI консультант
- [handlers/booking.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/booking.py) — старая запись
- [handlers/booking_calendar.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/booking_calendar.py) — календарь бронирования
- [handlers/calc_dynamic.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/calc_dynamic.py) — расчёты ROI/рассрочки
- [handlers/docs.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/docs.py) — документы
- [handlers/kp.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/kp.py) — коммерческие предложения
- [handlers/media.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/media.py) — медиа-материалы
- [handlers/units.py](https://github.com/semiekhin/rizalta-bot/blob/main/handlers/units.py) — работа с лотами

### services/
- [services/telegram.py](https://github.com/semiekhin/rizalta-bot/blob/main/services/telegram.py) — Telegram API
- [services/ai_chat.py](https://github.com/semiekhin/rizalta-bot/blob/main/services/ai_chat.py) — OpenAI API + Function Calling
- [services/speech.py](https://github.com/semiekhin/rizalta-bot/blob/main/services/speech.py) — Whisper API (голос)
- [services/calculations.py](https://github.com/semiekhin/rizalta-bot/blob/main/services/calculations.py) — финансовые расчёты
- [services/kp_generator.py](https://github.com/semiekhin/rizalta-bot/blob/main/services/kp_generator.py) — генерация КП
- [services/kp_search.py](https://github.com/semiekhin/rizalta-bot/blob/main/services/kp_search.py) — поиск КП

### models/
- [models/state.py](https://github.com/semiekhin/rizalta-bot/blob/main/models/state.py) — состояния диалогов

### data/
- [data/units.json](https://github.com/semiekhin/rizalta-bot/blob/main/data/units.json) — 69 лотов
- [data/rizalta_finance.json](https://github.com/semiekhin/rizalta-bot/blob/main/data/rizalta_finance.json) — финансовые сценарии
- [data/rizalta_knowledge_base.txt](https://github.com/semiekhin/rizalta-bot/blob/main/data/rizalta_knowledge_base.txt) — база знаний AI

### Скрипты
- [backup.sh](https://github.com/semiekhin/rizalta-bot/blob/main/backup.sh) — ежедневный бэкап
- [backup_weekly.sh](https://github.com/semiekhin/rizalta-bot/blob/main/backup_weekly.sh) — еженедельный бэкап
- [update_webhook.sh](https://github.com/semiekhin/rizalta-bot/blob/main/update_webhook.sh) — автообновление webhook

---

## Подключение к серверу

```bash
ssh root@72.56.64.91
cd /opt/bot
```

---

## Документация (прочитай перед началом)

В репозитории есть 3 файла документации:

1. **RIZALTA_PROJECT.md** — описание проекта, структура, технологии
2. **RIZALTA_CURRENT_TASK.md** — текущие задачи, что сделано, что осталось
3. **RIZALTA_KNOWLEDGE.md** — техническая база знаний, как что работает

---

## Структура проекта

```
/opt/bot/
├── app.py                    # Главный файл, webhook, роутинг
├── .env                      # Секреты (токены, API ключи)
├── properties.db             # SQLite база данных
│
├── config/
│   └── settings.py           # Конфигурация
│
├── handlers/
│   ├── __init__.py           # Экспорт обработчиков
│   ├── menu.py               # Главное меню
│   ├── ai_chat.py            # AI консультант + Function Calling
│   ├── booking.py            # Старая запись на показ
│   ├── booking_calendar.py   # Календарь бронирования (новый)
│   ├── calc_dynamic.py       # Расчёты ROI/рассрочки
│   ├── docs.py               # Документы (ДДУ, аренда)
│   ├── kp.py                 # Коммерческие предложения
│   ├── media.py              # Медиа-материалы
│   └── units.py              # Работа с лотами
│
├── services/
│   ├── telegram.py           # Telegram API
│   ├── ai_chat.py            # OpenAI API + Function Calling
│   ├── speech.py             # Whisper API (голос)
│   ├── calculations.py       # Финансовые расчёты
│   ├── kp_generator.py       # Генерация КП
│   └── kp_search.py          # Поиск КП
│
├── models/
│   └── state.py              # Состояния диалогов
│
├── data/                     # JSON данные, база знаний
├── kp_all/                   # 69 КП (JPG)
├── media/                    # Презентация, документы
│
├── backup.sh                 # Ежедневный бэкап (3:00 UTC)
├── backup_weekly.sh          # Еженедельный бэкап (Вс 4:00)
└── update_webhook.sh         # Автообновление webhook
```

---

## Полезные команды

```bash
# Логи бота
journalctl -u rizalta-bot -f

# Перезапуск
systemctl restart rizalta-bot

# Статус
systemctl status rizalta-bot --no-pager

# Все сервисы
systemctl status rizalta-bot cloudflare-rizalta --no-pager
```

---

## Текущие задачи (на 07.12.2025)

### Высокий приоритет

1. **Данные специалистов для календаря**
   - Получить: ФИО, Telegram chat_id, Email
   - Обновить в handlers/booking_calendar.py → SPECIALISTS
   - Добавить команду /myid в бота

### Средний приоритет (на продакшене)

2. **Усиление безопасности SSH**
   - Сменить порт 22 → 2222
   - Отключить root по паролю
   - Автообновления безопасности

---

## Что уже сделано

### Функционал
- ✅ AI консультант с базой знаний
- ✅ AI Function Calling (10 функций)
- ✅ 69 коммерческих предложений (поиск по площади/бюджету)
- ✅ Расчёты ROI и рассрочки для всех лотов
- ✅ Календарь бронирования с подтверждением специалистом
- ✅ Голосовое управление (Whisper API)
- ✅ Документы и медиа-материалы

### Безопасность
- ✅ Swap 1GB
- ✅ fail2ban
- ✅ Автобэкапы на email (ежедневно + еженедельно)
- ✅ Systemd автозапуск (4 сервиса)
- ✅ Cloudflare Tunnel
- ✅ Автообновление webhook

### Сервер
- ✅ 2 CPU, 4GB RAM, 50GB диск, 1 Гбит/с

---

## Деплой изменений

```bash
# Локально (Mac)
scp файл.py root@72.56.64.91:/opt/bot/handlers/

# На сервере
cd /opt/bot
systemctl restart rizalta-bot
journalctl -u rizalta-bot -f

# Git push
git add .
git commit -m "описание"
git push origin main
```

---

## Контакты

- Email бэкапов: 89181011091s@mail.ru
- Email бота: rizalta-bot@mail.ru
