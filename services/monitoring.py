"""
Мониторинг нагрузки бота.
"""

import asyncio
import aiohttp
import psutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import os

# Настройки
ADMIN_CHAT_ID = 512319063
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = Path("/opt/bot/monitoring.db")

# Счётчик запросов (последние 60 секунд)
request_times = deque(maxlen=1000)

# Пороги
REQUESTS_PER_MIN_THRESHOLD = 30
RAM_THRESHOLD_PERCENT = 50


def init_db():
    """Создаёт таблицу статистики."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id INTEGER,
            request_type TEXT,
            response_time_ms INTEGER
        )
    """)
    conn.commit()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_peaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(date, metric)
        )
    """)
    conn.commit()
    conn.close()



def log_peak(metric: str, value: float):
    """Записывает пиковое значение если оно больше текущего."""
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().isoformat()
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT value FROM daily_peaks WHERE date = ? AND metric = ?",
        (today, metric)
    )
    row = cursor.fetchone()
    
    if row is None:
        cursor.execute(
            "INSERT INTO daily_peaks (date, metric, value, timestamp) VALUES (?, ?, ?, ?)",
            (today, metric, value, now)
        )
    elif value > row[0]:
        cursor.execute(
            "UPDATE daily_peaks SET value = ?, timestamp = ? WHERE date = ? AND metric = ?",
            (value, now, today, metric)
        )
    
    conn.commit()
    conn.close()


def get_daily_peaks() -> dict:
    """Возвращает пиковые значения за сегодня."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT metric, value, timestamp FROM daily_peaks WHERE date = ?",
        (today,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return {row[0]: {"value": row[1], "time": row[2].split("T")[1][:5]} for row in rows}


def log_error(user_id: int, error_type: str, error_msg: str):
    """Логирует ошибку."""
    log_request(user_id, f"error:{error_type}", 0)


def log_request(user_id: int, request_type: str = "message", response_time_ms: int = 0):
    """Логирует запрос."""
    now = datetime.now()
    request_times.append(now)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO stats (timestamp, user_id, request_type, response_time_ms) VALUES (?, ?, ?, ?)",
        (now.isoformat(), user_id, request_type, response_time_ms)
    )
    conn.commit()
    conn.close()


def get_requests_per_minute() -> int:
    """Возвращает количество запросов за последнюю минуту."""
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    return sum(1 for t in request_times if t > minute_ago)


def get_ram_usage() -> float:
    """Возвращает использование RAM в процентах."""
    return psutil.virtual_memory().percent


def get_daily_stats() -> dict:
    """Статистика за сегодня."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Всего запросов
    cursor.execute(
        "SELECT COUNT(*) FROM stats WHERE timestamp LIKE ?",
        (f"{today}%",)
    )
    total_requests = cursor.fetchone()[0]
    
    # Уникальных пользователей
    cursor.execute(
        "SELECT COUNT(DISTINCT user_id) FROM stats WHERE timestamp LIKE ?",
        (f"{today}%",)
    )
    unique_users = cursor.fetchone()[0]
    
    # Среднее время ответа
    cursor.execute(
        "SELECT AVG(response_time_ms) FROM stats WHERE timestamp LIKE ? AND response_time_ms > 0",
        (f"{today}%",)
    )
    avg_response = cursor.fetchone()[0] or 0
    
    # Количество ошибок
    cursor.execute(
        "SELECT COUNT(*) FROM stats WHERE timestamp LIKE ? AND request_type LIKE ?",
        (f"{today}%", "error:%")
    )
    errors = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_requests": total_requests,
        "unique_users": unique_users,
        "avg_response_ms": int(avg_response),
        "errors": errors
    }


async def send_alert(message: str):
    """Отправляет алерт админу."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return await resp.json()
    except Exception as e:
        print(f"[MONITOR] Alert error: {e}")


# Флаги для предотвращения спама алертов
_last_requests_alert = None
_last_ram_alert = None


async def check_thresholds():
    """Проверяет пороги и отправляет алерты."""
    global _last_requests_alert, _last_ram_alert
    
    now = datetime.now()
    
    # Проверка запросов
    rpm = get_requests_per_minute()
    if rpm > REQUESTS_PER_MIN_THRESHOLD:
        if _last_requests_alert is None or (now - _last_requests_alert).seconds > 300:
            await send_alert(f"⚠️ <b>Высокая нагрузка!</b>\n\n📊 Запросов/мин: <b>{rpm}</b>\n⏰ {now.strftime('%H:%M:%S')}")
            _last_requests_alert = now
    
    # Проверка RAM
    ram = get_ram_usage()
    if ram > RAM_THRESHOLD_PERCENT:
        if _last_ram_alert is None or (now - _last_ram_alert).seconds > 300:
            await send_alert(f"⚠️ <b>Высокое использование RAM!</b>\n\n💾 RAM: <b>{ram:.1f}%</b>\n⏰ {now.strftime('%H:%M:%S')}")
            _last_ram_alert = now


async def send_daily_report():
    """Отправляет ежедневный отчёт с данными watchdog и пиками."""
    stats = get_daily_stats()
    ram = get_ram_usage()
    peaks = get_daily_peaks()
    
    # Пиковые значения
    ram_peak = peaks.get("ram", {}).get("value", 0)
    ram_peak_time = peaks.get("ram", {}).get("time", "—")
    cpu_peak = peaks.get("cpu", {}).get("value", 0)
    cpu_peak_time = peaks.get("cpu", {}).get("time", "—")
    rpm_peak = peaks.get("rpm", {}).get("value", 0)
    rpm_peak_time = peaks.get("rpm", {}).get("time", "—")
    
    # Счётчик ошибок за день
    error_count = stats.get('errors', 0)
    
    # Данные от watchdog
    try:
        from services.watchdog.checks import check_all_services, get_all_resources, check_all_billing
        from services.watchdog.config import SERVICES, SQLITE_DATABASES
        import os
        
        services = check_all_services(SERVICES)
        services_ok = sum(1 for s in services.values() if s['active'])
        services_total = len(services)
        
        resources = get_all_resources(SQLITE_DATABASES)
        cpu = resources['cpu']['percent']
        disk = resources['disk']
        sqlite_total = sum(s for s in resources['sqlite'].values() if s > 0)
        
        tw_token = os.getenv('TIMEWEB_API_TOKEN', '')
        billing = check_all_billing(tw_token)
        tw_balance = billing['timeweb'].get('balance', 0) if billing['timeweb']['success'] else 0
        
        watchdog_info = f"""
🖥 CPU: <b>{cpu:.1f}%</b> (пик: {cpu_peak:.1f}% в {cpu_peak_time})
💿 Disk: <b>{disk['used_gb']:.1f}/{disk['total_gb']:.1f} GB ({disk['percent']:.0f}%)</b>
🗄 SQLite: <b>{sqlite_total:.2f} MB</b>
🔧 Сервисы: <b>{services_ok}/{services_total}</b>
💳 Timeweb: <b>{tw_balance:.0f} ₽</b>"""
    except Exception as e:
        watchdog_info = f"\n⚠️ Watchdog: ошибка ({e})"
    
    # Формируем ошибки если есть
    error_info = f"\n❌ Ошибок: <b>{error_count}</b>" if error_count > 0 else ""
    
    message = f"""📊 <b>Ежедневный отчёт</b>
{datetime.now().strftime('%d.%m.%Y')}

📨 Запросов: <b>{stats['total_requests']}</b> (пик: {rpm_peak:.0f}/мин в {rpm_peak_time})
👥 Уникальных: <b>{stats['unique_users']}</b>
⚡ Среднее время: <b>{stats['avg_response_ms']} мс</b>
💾 RAM: <b>{ram:.1f}%</b> (пик: {ram_peak:.1f}% в {ram_peak_time}){error_info}{watchdog_info}"""

    await send_alert(message)

async def monitoring_loop():
    """Фоновая задача мониторинга."""
    init_db()
    print("[MONITOR] Мониторинг запущен")
    
    last_daily_report = None
    
    while True:
        try:
            # Проверяем пороги и записываем пики каждые 10 секунд
            await check_thresholds()
            
            # Записываем пиковые значения RAM и CPU
            ram = get_ram_usage()
            log_peak("ram", ram)
            
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            log_peak("cpu", cpu)
            
            # Пик запросов в минуту
            rpm = get_requests_per_minute()
            log_peak("rpm", rpm)
            
            # Ежедневный отчёт в 20:00
            now = datetime.now()
            if now.hour == 20 and now.minute == 0:
                if last_daily_report != now.date():
                    await send_daily_report()
                    last_daily_report = now.date()
            
        except Exception as e:
            print(f"[MONITOR] Error: {e}")
        
        await asyncio.sleep(10)
