"""Seed shows.db (DEV only) with realistic test data for the dashboard.

Распределение по менеджерам задано явно в PROFILES, чтобы получить
гарантированно разные паттерны (high+good, high+bad, mid, low) и
проверить работу красных флагов.

Run: /opt/webapp-dev/venv/bin/python /opt/webapp-dev/backend/scripts/seed_shows_test_data.py
"""

import os
import sys
import random
import sqlite3
from datetime import datetime, timedelta

# Добавляем backend/ в sys.path, чтобы импортировать services.shows_service
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
sys.path.insert(0, BACKEND_DIR)

from services.shows_service import (  # noqa: E402
    SHOWS_DB, MANAGERS, init_shows_db, create_show, update_show,
)

# Защита от случайного запуска против PROD
if "/opt/webapp-dev/" not in os.path.abspath(SHOWS_DB):
    raise SystemExit(f"Refusing to seed: SHOWS_DB={SHOWS_DB} is not under /opt/webapp-dev/")

# ============ Конфигурация распределения ============

# Каждому менеджеру — свой паттерн. Веса нормализуются random.choices автоматически.
PROFILES = [
    {
        "name": "Дегтярева Марина",
        # high activity + хорошая конверсия (~30% броней среди проведённых)
        "count_range": (40, 50),
        "weights": {
            "planned": 0.10,
            "completed": 0.35,
            "completed_booked": 0.30,
            "rescheduled": 0.15,
            "cancelled": 0.10,
        },
    },
    {
        "name": "Шумова Дарья",
        # high activity + ПЛОХАЯ конверсия → должен попасть в красный флаг
        # booking_rate ≈ 0.08 / (0.55 + 0.08) ≈ 13% < 20%, conducted ≈ 25-32 ≥ 5
        "count_range": (40, 50),
        "weights": {
            "planned": 0.12,
            "completed": 0.55,
            "completed_booked": 0.08,
            "rescheduled": 0.15,
            "cancelled": 0.10,
        },
    },
    {
        "name": "Хватик Светлана",
        # средние показатели
        "count_range": (30, 40),
        "weights": {
            "planned": 0.13,
            "completed": 0.42,
            "completed_booked": 0.18,
            "rescheduled": 0.15,
            "cancelled": 0.12,
        },
    },
    {
        "name": "Панченко Инна",
        # низкая активность, но >= 3 (флаг низкой активности НЕ должен сработать)
        "count_range": (5, 8),
        "weights": {
            "planned": 0.20,
            "completed": 0.40,
            "completed_booked": 0.15,
            "rescheduled": 0.15,
            "cancelled": 0.10,
        },
    },
]

# Сверка с MANAGERS из shows_service — чтобы не пропустить опечатку
profile_names = {p["name"] for p in PROFILES}
service_names = set(MANAGERS)
if profile_names != service_names:
    raise SystemExit(f"PROFILES managers mismatch: profiles={profile_names} service={service_names}")

# ============ Справочники ============

AGENCIES = [
    "Этажи",
    "СамолётПлюс",
    "Метражи",
    "Жилфонд-Новосибирск",
    "Перспектива24",
    "ИнКом-Недвижимость",
    "ТСН Недвижимость",
    "Мегаполис-Сервис",
    "Авангард-Риэлт",
    "Доли.ру",
]

FIRST_NAMES_M = [
    "Александр", "Дмитрий", "Сергей", "Андрей", "Михаил",
    "Алексей", "Иван", "Никита", "Артём", "Кирилл",
]
LAST_NAMES_M = [
    "Иванов", "Петров", "Смирнов", "Кузнецов", "Соколов",
    "Попов", "Лебедев", "Козлов", "Новиков", "Морозов",
]
FIRST_NAMES_F = [
    "Анна", "Мария", "Елена", "Ольга", "Татьяна",
    "Наталья", "Юлия", "Ирина", "Светлана", "Екатерина",
]
LAST_NAMES_F = [
    "Иванова", "Петрова", "Смирнова", "Кузнецова", "Соколова",
    "Попова", "Лебедева", "Козлова", "Новикова", "Морозова",
]

COMMENTS = [
    "Клиент очень заинтересован",
    "Просили перезвонить через неделю",
    "Рассматривают ещё другие ЖК",
    "Хороший контакт, тёплый лид",
    "Просили КП и расчёт",
    "Нужна одобренная ипотека",
    "Готовы вносить аванс",
    "Думают месяц",
    "Не вышли на показ",
    "Перенесли по личным обстоятельствам",
    "Интересует только Family",
    "Бюджет ограничен",
    "Хотят с отделкой",
    "Спрашивали про рассрочку",
    "Положительный отклик",
]


def random_realtor_name() -> str:
    if random.random() < 0.5:
        return f"{random.choice(FIRST_NAMES_M)} {random.choice(LAST_NAMES_M)}"
    return f"{random.choice(FIRST_NAMES_F)} {random.choice(LAST_NAMES_F)}"


def random_show_dt(now: datetime, planned: bool) -> datetime:
    """planned → ближайшие 2 недели в будущее, остальное → прошедшие 3 месяца."""
    if planned:
        delta_days = random.randint(0, 14)
        d = now + timedelta(days=delta_days)
    else:
        delta_days = random.randint(1, 90)
        d = now - timedelta(days=delta_days)
    # Часы 10..19 со смещением к вечеру
    hours = list(range(10, 20))
    hour_weights = [1, 1, 1.5, 1.5, 2, 2.5, 3, 3, 3, 2]
    hour = random.choices(hours, weights=hour_weights, k=1)[0]
    minute = random.choice([0, 0, 0, 15, 30, 30, 45])  # чаще ровный час и :30
    return d.replace(hour=hour, minute=minute, second=0, microsecond=0)


def pick_status(weights: dict) -> str:
    statuses = list(weights.keys())
    ws = list(weights.values())
    return random.choices(statuses, weights=ws, k=1)[0]


# ============ Основной сценарий ============

def clear_shows():
    conn = sqlite3.connect(SHOWS_DB)
    n = conn.execute("SELECT COUNT(*) FROM shows").fetchone()[0]
    conn.execute("DELETE FROM shows")
    # Сброс автоинкремента, чтобы id начался с 1 — приятнее для просмотра
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'shows'")
    conn.commit()
    conn.close()
    return n


def main():
    init_shows_db()  # на случай если БД ещё не инициализирована
    print(f"[SEED] Target DB: {SHOWS_DB}")
    deleted = clear_shows()
    print(f"[SEED] Cleared {deleted} existing rows")

    now = datetime.now().replace(second=0, microsecond=0)
    summary: dict[str, dict[str, int]] = {p["name"]: {} for p in PROFILES}
    total_inserted = 0

    for profile in PROFILES:
        manager = profile["name"]
        count = random.randint(*profile["count_range"])
        for _ in range(count):
            status = pick_status(profile["weights"])
            dt = random_show_dt(now, planned=(status == "planned"))
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            agency = random.choice(AGENCIES)
            realtor = random_realtor_name()
            comment = random.choice(COMMENTS) if random.random() < 0.30 else None

            # create_show ставит status='planned' и валидирует manager
            row = create_show(
                show_datetime=dt_str,
                manager=manager,
                realtor_name=realtor,
                realtor_agency=agency,
                comment=comment,
            )
            # update_show валидирует status и применяет нужный
            if status != "planned":
                update_show(row["id"], {"status": status})

            summary[manager][status] = summary[manager].get(status, 0) + 1
            total_inserted += 1

    # ============ Печать сводки ============
    print(f"\n[SEED] Inserted: {total_inserted} shows total\n")
    headers = ["planned", "completed", "completed_booked", "rescheduled", "cancelled"]
    name_w = max(len(p["name"]) for p in PROFILES) + 2
    print(f"{'Менеджер'.ljust(name_w)} {'TOTAL':>6}  " + "  ".join(h[:9].rjust(9) for h in headers) + "   conv%")
    print("-" * (name_w + 7 + (11 * len(headers)) + 9))
    for profile in PROFILES:
        name = profile["name"]
        s = summary[name]
        total = sum(s.get(h, 0) for h in headers)
        conducted = s.get("completed", 0) + s.get("completed_booked", 0)
        conv = round(100 * s.get("completed_booked", 0) / conducted, 1) if conducted else None
        conv_str = f"{conv}%" if conv is not None else "—"
        cells = "  ".join(str(s.get(h, 0)).rjust(9) for h in headers)
        print(f"{name.ljust(name_w)} {str(total).rjust(6)}  {cells}   {conv_str}")

    # Суммы по статусам
    grand = {h: sum(summary[m].get(h, 0) for m in summary) for h in headers}
    grand_total = sum(grand.values())
    grand_conducted = grand["completed"] + grand["completed_booked"]
    grand_conv = round(100 * grand["completed_booked"] / grand_conducted, 1) if grand_conducted else None
    grand_conv_str = f"{grand_conv}%" if grand_conv is not None else "—"
    print("-" * (name_w + 7 + (11 * len(headers)) + 9))
    cells = "  ".join(str(grand[h]).rjust(9) for h in headers)
    print(f"{'ИТОГО'.ljust(name_w)} {str(grand_total).rjust(6)}  {cells}   {grand_conv_str}")


if __name__ == "__main__":
    main()
