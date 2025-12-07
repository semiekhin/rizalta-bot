# RIZALTA BOT — Инструкция для нового чата

## Проект

**RIZALTA Telegram Bot** — AI-консультант для риэлторов по продаже курортной недвижимости в Белокурихе (Алтай).

- Telegram: @RealtMeAI_bot
- Сервер: 72.56.64.91 (Timeweb, Ubuntu 24.04)
- GitHub: https://github.com/semukhin/RIZALTA_BOT

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
