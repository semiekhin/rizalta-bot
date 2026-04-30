#!/usr/bin/env python3
"""Рассылка уведомления о перелогине в ri.rclick.ru.

Аудитория (вариант B, 62 получателя):
  - rclick_tokens.db (40) — риэлторы с активным токеном rclick
  - secretary.db tasks (10) — пользователи личного секретаря
  - старый список из send_update_notification.py (22) — собран из логов 24.12.2025

Запуск:
  python3 send_rclick_update_notification.py          # dry-run (только список)
  python3 send_rclick_update_notification.py --send   # реальная отправка
"""

import argparse
import asyncio
import os
import sqlite3
import sys
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

BOT_ID = 8343378629

MESSAGE = """🔐 <b>Обновление бота RIZALTA</b>

В связи с обновлением протоколов безопасности на сайте ri.rclick.ru проведена синхронизация с новыми требованиями авторизации.

<b>Что нужно сделать каждому один раз:</b>

Зайти в раздел 📌 Фиксация и перелогиниться: ввести телефон и пароль от вашего кабинета ri.rclick.ru.

После этого фиксация клиентов заработает как раньше."""


def collect_recipients():
    """Возвращает dict {chat_id: [source1, source2, ...]} из 3 источников."""
    recipients = {}

    def add(cid, source):
        if cid == BOT_ID:
            return
        recipients.setdefault(cid, []).append(source)

    conn = sqlite3.connect("/opt/bot/rclick_tokens.db")
    for (tid,) in conn.execute("SELECT telegram_id FROM rclick_tokens"):
        add(tid, "rclick")
    conn.close()

    conn = sqlite3.connect("/opt/bot/secretary.db")
    for (uid,) in conn.execute("SELECT DISTINCT user_id FROM tasks"):
        add(uid, "secretary")
    conn.close()

    old_list = [
        512319063, 1218114843, 1270008981, 1283324880, 1500100952,
        297862179, 452809137, 6098350326, 6148570013, 622666056,
        6320054340, 633076420, 7119175741, 7441583528, 7617252773,
        8000703751, 824528864, 8352242683, 8583875204, 868791592,
        949370329, 996436036,
    ]
    for cid in old_list:
        add(cid, "old_list")

    return recipients


def load_phones():
    """Возвращает {telegram_id: phone} для тех, кто есть в rclick_tokens."""
    conn = sqlite3.connect("/opt/bot/rclick_tokens.db")
    phones = {tid: phone for tid, phone in
              conn.execute("SELECT telegram_id, phone FROM rclick_tokens")}
    conn.close()
    return phones


async def send_one(session, token, chat_id):
    """Отправляет сообщение. Возвращает (ok: bool, description: str)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": MESSAGE,
        "parse_mode": "HTML",
        "disable_notification": True,
    }
    try:
        async with session.post(url, json=payload, timeout=15) as resp:
            data = await resp.json()
            if data.get("ok"):
                return True, "ok"
            return False, data.get("description", str(data))
    except Exception as e:
        return False, f"exception: {e}"


async def broadcast(token, recipients):
    delivered = []
    failed = []
    async with aiohttp.ClientSession() as session:
        for i, cid in enumerate(recipients, 1):
            ok, desc = await send_one(session, token, cid)
            mark = "✅" if ok else "❌"
            print(f"[{i:2d}/{len(recipients)}] {mark} {cid}: {desc}")
            (delivered if ok else failed).append((cid, desc))
            await asyncio.sleep(0.5)
    return delivered, failed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Реальная отправка (иначе только список)")
    parser.add_argument("--only", type=str, default="", help="Отправить только этим chat_id (через запятую)")
    parser.add_argument("--exclude", type=str, default="", help="Исключить эти chat_id (через запятую)")
    args = parser.parse_args()

    only_ids = {int(x) for x in args.only.split(",") if x.strip()}
    exclude_ids = {int(x) for x in args.exclude.split(",") if x.strip()}

    load_dotenv("/opt/bot/.env")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN не найден в /opt/bot/.env", file=sys.stderr)
        sys.exit(1)

    recipients = collect_recipients()
    phones = load_phones()

    all_ids = sorted(recipients.keys())
    if only_ids:
        sorted_ids = [cid for cid in all_ids if cid in only_ids]
        missing = only_ids - set(all_ids)
        if missing:
            print(f"WARNING: --only содержит ID не из базы: {sorted(missing)}")
            for cid in sorted(missing):
                recipients[cid] = ["manual"]
                sorted_ids.append(cid)
            sorted_ids = sorted(set(sorted_ids))
    else:
        sorted_ids = [cid for cid in all_ids if cid not in exclude_ids]

    if exclude_ids and not only_ids:
        print(f"ИСКЛЮЧЕНО: {sorted(exclude_ids)}")
    print(f"Всего уникальных получателей: {len(sorted_ids)}")
    print(f"Токен PROD-бота: ...{token[-6:]}  (id: {token.split(':')[0]})")
    print()
    print(f"{'CHAT_ID':>12}  {'PHONE':<15}  SOURCES")
    print("-" * 60)
    for cid in sorted_ids:
        phone = phones.get(cid, "—")
        srcs = "+".join(recipients[cid])
        print(f"{cid:>12}  {phone:<15}  {srcs}")

    if not args.send:
        print()
        print("DRY-RUN. Для реальной отправки запустить с флагом --send")
        return

    print()
    print("=" * 60)
    print("НАЧИНАЮ РАССЫЛКУ")
    print("=" * 60)

    delivered, failed = asyncio.run(broadcast(token, sorted_ids))

    print()
    print("=" * 60)
    print(f"ИТОГО: доставлено {len(delivered)} / упало {len(failed)} из {len(sorted_ids)}")
    print("=" * 60)
    if failed:
        print("\nУпавшие:")
        for cid, desc in failed:
            print(f"  {cid}: {desc}")


if __name__ == "__main__":
    main()
