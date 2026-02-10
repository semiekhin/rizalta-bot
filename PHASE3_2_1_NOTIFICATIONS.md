# Phase 3.2.1 — Отправка заявок (Telegram + Email)

## КОНТЕКСТ

Рабочая директория: `/opt/webapp` (порт 8003)
Ветка: `webapp`
Текущая версия: v0.6.0

### КРИТИЧЕСКИ ВАЖНО — НЕ ТРОГАТЬ
- `/opt/bot` (порт 8000) — PROD бот, НИКОГДА не редактировать
- `/opt/bot-dev` (порт 8002) — DEV бот, НИКОГДА не редактировать
- `/opt/bot/properties.db` — читаем, НЕ пишем
- Файлы .env бота — ТОЛЬКО ЧИТАЕМ для копирования значений

### Что делаем
Сейчас `POST /api/book-showing` просто делает `print()` — заявка никуда не уходит.
Нужно: реальная отправка уведомлений менеджерам через Telegram Bot API + email (SMTP).

---

## ЗАДАЧА 1: Создать `.env` для webapp

Файл: `/opt/webapp/backend/.env`

Скопировать значения из `/opt/bot/.env` (ТОЛЬКО ЧИТАТЬ этот файл!):

```bash
# Прочитать нужные значения:
grep -E "^(TELEGRAM_BOT_TOKEN|MANAGER_CHAT_ID|MANAGER_EMAIL|BOT_EMAIL|SMTP_HOST|SMTP_PORT|SMTP_USER|SMTP_PASSWORD)=" /opt/bot/.env
```

Создать `/opt/webapp/backend/.env` с этими значениями:
```
# Telegram notifications
TELEGRAM_BOT_TOKEN=<значение из /opt/bot/.env>
MANAGER_CHAT_ID=<значение из /opt/bot/.env>

# Email notifications  
SMTP_HOST=<значение из /opt/bot/.env>
SMTP_PORT=<значение из /opt/bot/.env>
SMTP_USER=<значение из /opt/bot/.env>
SMTP_PASSWORD=<значение из /opt/bot/.env>
MANAGER_EMAIL=<значение из /opt/bot/.env>
BOT_EMAIL=<значение из /opt/bot/.env>
```

Также добавить `.env` в `/opt/webapp/.gitignore` если его там нет.

---

## ЗАДАЧА 2: Создать notification service

Файл: `/opt/webapp/backend/services/notifications.py`

```python
"""
Notification service — отправка заявок менеджерам через Telegram и Email.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID", "")  # Может быть через запятую: "123,456"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Email config
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "")
BOT_EMAIL = os.getenv("BOT_EMAIL", "")


def get_manager_chat_ids() -> list[int]:
    """Парсит MANAGER_CHAT_ID (может быть через запятую)."""
    if not MANAGER_CHAT_ID:
        return []
    return [int(cid.strip()) for cid in MANAGER_CHAT_ID.split(",") if cid.strip()]


async def send_telegram_message(chat_id: int, text: str) -> bool:
    """Отправка сообщения через Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram notification")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                }
            )
            if resp.status_code == 200 and resp.json().get("ok"):
                return True
            else:
                logger.error(f"Telegram API error: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def send_telegram_to_managers(text: str) -> int:
    """Отправка сообщения всем менеджерам. Возвращает кол-во успешных."""
    chat_ids = get_manager_chat_ids()
    if not chat_ids:
        logger.warning("No MANAGER_CHAT_ID configured")
        return 0
    
    success = 0
    for cid in chat_ids:
        if await send_telegram_message(cid, text):
            success += 1
    return success


def send_email(to: str, subject: str, body_html: str) -> bool:
    """Отправка email через SMTP."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, to]):
        logger.warning("Email config incomplete, skipping email notification")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = BOT_EMAIL or SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


async def notify_showing_request(
    name: str, 
    phone: str, 
    lot_code: str = "", 
    comment: str = "",
    source: str = "webapp"
) -> dict:
    """
    Отправка заявки на показ менеджерам (Telegram + Email).
    Возвращает статус отправки.
    """
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Формируем сообщение для Telegram
    lot_info = f"\n🏢 <b>Лот:</b> {lot_code}" if lot_code else ""
    comment_info = f"\n💬 <b>Комментарий:</b> {comment}" if comment else ""
    
    tg_text = (
        f"📋 <b>Новая заявка на показ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"📱 <b>Телефон:</b> {phone}"
        f"{lot_info}"
        f"{comment_info}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🌐 Источник: {source}\n"
        f"🕐 {now}"
    )

    # Формируем email
    email_subject = f"RIZALTA — Заявка на показ от {name}"
    email_body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #263524;">📋 Новая заявка на показ</h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><b>👤 Имя</b></td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{name}</td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><b>📱 Телефон</b></td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{phone}</td></tr>
        {"<tr><td style='padding: 8px; border-bottom: 1px solid #eee;'><b>🏢 Лот</b></td><td style='padding: 8px; border-bottom: 1px solid #eee;'>" + lot_code + "</td></tr>" if lot_code else ""}
        {"<tr><td style='padding: 8px; border-bottom: 1px solid #eee;'><b>💬 Комментарий</b></td><td style='padding: 8px; border-bottom: 1px solid #eee;'>" + comment + "</td></tr>" if comment else ""}
    </table>
    <p style="color: #888; font-size: 12px; margin-top: 20px;">
        Источник: {source} | {now}
    </p>
    </body></html>
    """

    # Отправляем
    tg_count = await send_telegram_to_managers(tg_text)
    email_ok = send_email(MANAGER_EMAIL, email_subject, email_body)

    result = {
        "telegram_sent": tg_count,
        "telegram_total": len(get_manager_chat_ids()),
        "email_sent": email_ok,
    }
    
    logger.info(f"[SHOWING] {name} / {phone} / {lot_code} → TG: {tg_count}, Email: {email_ok}")
    return result
```

---

## ЗАДАЧА 3: Обновить `app.py`

Файл: `/opt/webapp/backend/app.py`

### 3.1 Добавить import dotenv в начало файла

В самом начале `app.py`, ПЕРЕД другими импортами:
```python
from dotenv import load_dotenv
load_dotenv()
```

### 3.2 Добавить import notification service

После существующих импортов сервисов добавить:
```python
from services.notifications import notify_showing_request
```

### 3.3 Заменить `api_book_showing`

БЫЛО:
```python
@app.post("/api/book-showing")
async def api_book_showing(req: ShowingRequest):
    """Заявка на показ."""
    # TODO: отправка в Telegram/email
    print(f"[SHOWING] {req.name} / {req.phone} / {req.lot_code}")
    return {"ok": True, "message": "Заявка принята"}
```

СТАЛО:
```python
@app.post("/api/book-showing")
async def api_book_showing(req: ShowingRequest):
    """Заявка на показ — отправка в Telegram и Email."""
    try:
        result = await notify_showing_request(
            name=req.name,
            phone=req.phone,
            lot_code=req.lot_code,
            comment=req.comment,
            source="webapp"
        )
        
        # Заявка "принята" даже если отправка частично провалилась
        # (лучше потерять уведомление, чем отпугнуть клиента)
        return {
            "ok": True,
            "message": "Заявка принята! Мы свяжемся с вами в ближайшее время.",
            "notifications": result  # для отладки
        }
    except Exception as e:
        import logging
        logging.error(f"[SHOWING ERROR] {e}")
        # Даже при ошибке говорим клиенту что заявка принята
        return {"ok": True, "message": "Заявка принята! Мы свяжемся с вами в ближайшее время."}
```

### 3.4 Обновить версию в health endpoint

```python
@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "0.6.1"}
```

---

## ЗАДАЧА 4: Установить зависимости

```bash
cd /opt/webapp
source venv/bin/activate
pip install python-dotenv aiosmtplib
```

Проверить что `httpx` уже установлен (он используется в app.py):
```bash
pip show httpx
```

---

## ЗАДАЧА 5: Обновить Booking.jsx

Файл: `/opt/webapp/frontend/src/pages/Booking.jsx`

Минимальные улучшения:

### 5.1 Добавить валидацию телефона

В `handleSubmit`, перед `setSending(true)`:
```jsx
// Базовая валидация телефона
const phoneClean = form.phone.replace(/[\s\-\(\)]/g, '')
if (phoneClean.length < 10) {
    alert('Пожалуйста, введите корректный номер телефона')
    return
}
```

### 5.2 Обработка ошибки от backend

Заменить try/catch в handleSubmit:
```jsx
const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Базовая валидация
    const phoneClean = form.phone.replace(/[\s\-\(\)]/g, '')
    if (phoneClean.length < 10) {
        setError('Пожалуйста, введите корректный номер телефона')
        return
    }
    
    setSending(true)
    setError('')
    try {
        const resp = await fetch('/api/book-showing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form)
        })
        const data = await resp.json()
        if (data.ok) {
            setSent(true)
        } else {
            setError('Ошибка отправки. Попробуйте ещё раз.')
        }
    } catch (err) {
        console.error(err)
        setError('Ошибка соединения. Попробуйте ещё раз.')
    }
    setSending(false)
}
```

Добавить стейт `error`:
```jsx
const [error, setError] = useState('')
```

Показать ошибку в форме (перед кнопкой submit):
```jsx
{error && (
    <p className="text-rz-error text-sm text-center">{error}</p>
)}
```

---

## ЗАДАЧА 6: Проверить LotDetail.jsx

В `LotDetail.jsx` есть кнопка «Записаться на показ». Нужно убедиться что она ведёт на тот же endpoint `/api/book-showing`. Если она вызывает навигацию на `booking` — ОК, Booking.jsx уже обновлён. Если она отправляет запрос напрямую — обновить аналогично.

Команда для проверки:
```bash
grep -n "book-showing\|booking\|Записаться" /opt/webapp/frontend/src/pages/LotDetail.jsx
```

---

## ЗАДАЧА 7: Тестирование

### 7.1 Рестарт backend
```bash
sudo systemctl restart webapp.service
sudo systemctl status webapp.service
```

### 7.2 Проверка health
```bash
curl -s http://127.0.0.1:8003/api/health
# Ожидаем: {"status":"healthy","version":"0.6.1"}
```

### 7.3 Тест отправки заявки
```bash
curl -s -X POST http://127.0.0.1:8003/api/book-showing \
  -H "Content-Type: application/json" \
  -d '{"name":"Тест WebApp","phone":"+7 999 000-00-00","lot_code":"А119","comment":"Тестовая заявка"}' | python3 -m json.tool
```

Ожидаем:
- Ответ `{"ok": true, "message": "Заявка принята!...", "notifications": {...}}`
- Менеджер получает сообщение в Telegram
- Менеджер получает email

### 7.4 Frontend build + test
```bash
cd /opt/webapp/frontend && npm run build
```

Открыть https://webapp.rizaltaservice.ru/
- Перейти в «Записаться на показ»
- Заполнить форму
- Убедиться что заявка уходит

### 7.5 Логи
```bash
sudo journalctl -u webapp.service -n 50 --no-pager
```

---

## ЗАДАЧА 8: Git commit

```bash
cd /opt/webapp
git add backend/.env.example backend/services/notifications.py backend/app.py frontend/src/pages/Booking.jsx .gitignore
git commit -m "v0.6.1: real notifications - Telegram + Email for showing requests"
git push
```

**ВАЖНО:** `.env` НЕ коммитим! Создать `.env.example` без секретов:
```
# /opt/webapp/backend/.env.example
TELEGRAM_BOT_TOKEN=
MANAGER_CHAT_ID=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
MANAGER_EMAIL=
BOT_EMAIL=
```

---

## ПОРЯДОК ВЫПОЛНЕНИЯ

1. Прочитать `.env` бота: `grep -E "^(TELEGRAM|MANAGER|SMTP|BOT_EMAIL)=" /opt/bot/.env`
2. Создать `/opt/webapp/backend/.env` с этими значениями
3. Добавить `.env` в `.gitignore`
4. Установить `python-dotenv`: `pip install python-dotenv`
5. Создать `/opt/webapp/backend/services/notifications.py`
6. Обновить `/opt/webapp/backend/app.py` (dotenv + notifications)
7. Обновить `/opt/webapp/frontend/src/pages/Booking.jsx` (валидация + error handling)
8. Проверить LotDetail.jsx
9. Рестарт: `sudo systemctl restart webapp.service`
10. Тест curl → проверить TG и email
11. Frontend build: `cd /opt/webapp/frontend && npm run build`
12. Тест в браузере
13. Создать `.env.example`, git commit + push
