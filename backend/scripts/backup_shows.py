"""Daily backup of shows.db.

- DEV (WEBAPP_ROOT == /opt/webapp-dev): локальный бэкап + лог в stdout, БЕЗ email.
- PROD (WEBAPP_ROOT == /opt/webapp): локальный бэкап + email на BACKUP_EMAIL
  (fallback на MANAGER_EMAIL, если BACKUP_EMAIL не задан).

Snapshot — через sqlite3 backup API (consistent под чтением/записью).
Локальная ротация — 14 дней по mtime.

PROD also sends a Telegram status notification (✅/❌) to MANAGER_CHAT_ID
at the very end — after snapshot, email and rotation. DEV does not.

Run (manual): /opt/webapp-dev/venv/bin/python /opt/webapp-dev/backend/scripts/backup_shows.py
Run (cron PROD):
  1 20 * * * /opt/webapp/venv/bin/python /opt/webapp/backend/scripts/backup_shows.py >> /var/log/backup.log 2>&1
"""

import os
import sys
import gzip
import html
import shutil
import sqlite3
import asyncio
import tempfile
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from services.notifications import send_email_with_attachment, send_telegram_to_managers  # noqa: E402

RETENTION_DAYS = 14
SHOWS_DB = os.path.join(BACKEND_DIR, "shows.db")
BACKUPS_DIR = os.path.join(BACKEND_DIR, "backups")

WEBAPP_ROOT = os.getenv("WEBAPP_ROOT", "")
IS_PROD = WEBAPP_ROOT.rstrip("/") == "/opt/webapp"
BACKUP_EMAIL = os.getenv("BACKUP_EMAIL") or os.getenv("MANAGER_EMAIL", "")


def log(msg: str) -> None:
    print(f"[BACKUP {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def make_snapshot(src_db: str) -> str:
    """sqlite3 backup API → temp file. Returns path to consistent snapshot."""
    fd, snap_path = tempfile.mkstemp(prefix="shows-snap-", suffix=".db")
    os.close(fd)
    src = sqlite3.connect(src_db)
    snap = sqlite3.connect(snap_path)
    try:
        src.backup(snap)
    finally:
        snap.close()
        src.close()
    return snap_path


def gzip_to(src_path: str, dst_path: str) -> None:
    with open(src_path, "rb") as fin, gzip.open(dst_path, "wb", compresslevel=9) as fout:
        shutil.copyfileobj(fin, fout)


def rotate(directory: str, days: int) -> int:
    """Удалить файлы shows-*.db.gz в directory старше days по mtime. Возвращает кол-во удалённых."""
    if not os.path.isdir(directory):
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    deleted = 0
    for name in os.listdir(directory):
        if not (name.startswith("shows-") and name.endswith(".db.gz")):
            continue
        path = os.path.join(directory, name)
        if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
            os.remove(path)
            deleted += 1
            log(f"Rotated out: {name}")
    return deleted


def count_shows(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM shows").fetchone()[0]
    finally:
        conn.close()


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def main() -> int:
    success = False
    error = ""
    archive_size = 0

    try:
        if not os.path.exists(SHOWS_DB):
            raise FileNotFoundError(f"shows.db not found at {SHOWS_DB}")

        os.makedirs(BACKUPS_DIR, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        archive_name = f"shows-{today}.db.gz"
        archive_path = os.path.join(BACKUPS_DIR, archive_name)

        db_size = os.path.getsize(SHOWS_DB)
        rows = count_shows(SHOWS_DB)
        log(f"Source: {SHOWS_DB} ({human_size(db_size)}, {rows} rows)")

        snap_path = make_snapshot(SHOWS_DB)
        try:
            gzip_to(snap_path, archive_path)
        finally:
            if os.path.exists(snap_path):
                os.remove(snap_path)

        archive_size = os.path.getsize(archive_path)
        log(f"Archive: {archive_path} ({human_size(archive_size)})")

        rotate(BACKUPS_DIR, RETENTION_DAYS)

        env_label = "PROD" if IS_PROD else f"DEV (WEBAPP_ROOT={WEBAPP_ROOT or '<unset>'})"
        log(f"Environment: {env_label}")

        if IS_PROD:
            if not BACKUP_EMAIL:
                raise RuntimeError("ни BACKUP_EMAIL, ни MANAGER_EMAIL не заданы на PROD")
            subject = f"RIZALTA WebApp · бэкап shows.db · {today}"
            body = (
                f"<p>Автоматический ежедневный бэкап shows.db (RIZALTA WebApp PROD).</p>"
                f"<ul>"
                f"<li>Дата: {today}</li>"
                f"<li>Размер исходной БД: {human_size(db_size)}</li>"
                f"<li>Записей в shows: {rows}</li>"
                f"<li>Attachment: {archive_name}</li>"
                f"<li>Локальная копия: {archive_path}</li>"
                f"<li>Локальная ротация: последние {RETENTION_DAYS} дней</li>"
                f"</ul>"
            )
            if not send_email_with_attachment(BACKUP_EMAIL, subject, body, archive_path):
                raise RuntimeError("email send failed")
            log(f"Email sent to {BACKUP_EMAIL}")
        else:
            log("DEV — пропускаю отправку email. Локальный бэкап сохранён.")

        success = True
    except Exception as e:
        error = str(e)
        log(f"ERROR: backup failed — {error}")

    # Telegram notification — PROD only, at the very end, wrapped in its own
    # try/except so a Telegram failure never changes the exit code. The local
    # backup and email are the important guarantees and are already done.
    if IS_PROD:
        try:
            ts = datetime.now().strftime("%d.%m.%Y %H:%M")
            if success:
                msg = (
                    f"✅ shows.db backup — {ts}\n"
                    f"Размер: {archive_size / 1024:.1f} KB"
                )
            else:
                safe_error = html.escape(error[:300])
                msg = (
                    f"❌ shows.db backup — {ts}\n"
                    f"Ошибка: {safe_error}"
                )
            sent = asyncio.run(send_telegram_to_managers(msg))
            log(f"Telegram notification sent to {sent} chat(s)")
        except Exception as e:
            log(f"WARNING: Telegram notification failed: {e}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
