"""
RIZALTA Watchdog - Система мониторинга и самовосстановления
Главный цикл мониторинга
"""
import os
import sys
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.watchdog.config import (
    ALERT_CHAT_ID, ALERT_BOT_TOKEN_ENV,
    INTERVALS, SERVICES, HEALTH_ENDPOINTS,
    THRESHOLDS, BILLING, AUTO_ACTIONS,
    SAFE_RESTART_COMMANDS, CLEANUP_PATHS, SQLITE_DATABASES,
    TIMEWEB_TOKEN_ENV
)
from services.watchdog.checks import (
    check_all_services, check_all_endpoints,
    get_all_resources, check_all_billing
)
from services.watchdog.actions import (
    send_telegram_alert, attempt_restart, run_cleanup,
    format_service_alert, format_health_alert,
    format_resource_alert, format_billing_alert,
    format_recovery_alert, format_status_report
)


class Watchdog:
    """Главный класс Watchdog"""
    
    def __init__(self):
        self.bot_token = os.getenv(ALERT_BOT_TOKEN_ENV, "")
        self.timeweb_token = os.getenv(TIMEWEB_TOKEN_ENV, "")
        self.chat_id = ALERT_CHAT_ID
        
        # Timestamps последних проверок
        self.last_check: Dict[str, datetime] = {}
        
        # Состояние алертов (чтобы не спамить)
        self.alerted: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=30)
        
        # Статистика
        self.stats = {
            "started": datetime.now(),
            "checks": 0,
            "alerts_sent": 0,
            "restarts_attempted": 0
        }
    
    def should_check(self, check_type: str) -> bool:
        """Проверяет нужно ли выполнять проверку по интервалу"""
        interval = INTERVALS.get(check_type, 60)
        last = self.last_check.get(check_type)
        
        if last is None:
            return True
        
        return (datetime.now() - last).total_seconds() >= interval
    
    def mark_checked(self, check_type: str):
        """Отмечает проверку выполненной"""
        self.last_check[check_type] = datetime.now()
    
    def should_alert(self, alert_key: str) -> bool:
        """Проверяет можно ли отправить алерт (cooldown)"""
        last_alert = self.alerted.get(alert_key)
        if last_alert is None:
            return True
        return (datetime.now() - last_alert) > self.alert_cooldown
    
    def send_alert(self, message: str, alert_key: str):
        """Отправляет алерт с учётом cooldown"""
        if not self.should_alert(alert_key):
            print(f"[WATCHDOG] Alert suppressed (cooldown): {alert_key}")
            return
        
        success = send_telegram_alert(message, self.chat_id, self.bot_token)
        if success:
            self.alerted[alert_key] = datetime.now()
            self.stats["alerts_sent"] += 1
            print(f"[WATCHDOG] Alert sent: {alert_key}")
        else:
            print(f"[WATCHDOG] Alert failed: {alert_key}")
    
    def check_services(self):
        """Проверка systemd сервисов"""
        if not self.should_check("services"):
            return
        
        print(f"[WATCHDOG] Checking services...")
        results = check_all_services(SERVICES)
        
        for service, data in results.items():
            if not data["active"]:
                print(f"[WATCHDOG] Service down: {service}")
                
                # Попытка авторестарта
                if AUTO_ACTIONS["restart_on_failure"]:
                    success, message, attempted = attempt_restart(
                        service,
                        SAFE_RESTART_COMMANDS,
                        AUTO_ACTIONS["max_restarts"],
                        AUTO_ACTIONS["cooldown_minutes"]
                    )
                    self.stats["restarts_attempted"] += 1 if attempted else 0
                    
                    if success:
                        # Успешное восстановление
                        alert_msg = format_recovery_alert(service, 1)
                        self.send_alert(alert_msg, f"recovery_{service}")
                    else:
                        # Не удалось восстановить
                        alert_msg = format_service_alert(service, data["status"], message)
                        self.send_alert(alert_msg, f"service_{service}")
                else:
                    alert_msg = format_service_alert(service, data["status"])
                    self.send_alert(alert_msg, f"service_{service}")
        
        self.mark_checked("services")
        self.stats["checks"] += 1
    
    def check_health(self):
        """Проверка HTTP health endpoints"""
        if not self.should_check("health"):
            return
        
        print(f"[WATCHDOG] Checking health endpoints...")
        results = check_all_endpoints(HEALTH_ENDPOINTS)
        
        for name, data in results.items():
            if not data["healthy"]:
                print(f"[WATCHDOG] Health check failed: {name}")
                alert_msg = format_health_alert(
                    name, data["url"], data["status_code"], data["message"]
                )
                self.send_alert(alert_msg, f"health_{name}")
        
        self.mark_checked("health")
        self.stats["checks"] += 1
    
    def check_resources(self):
        """Проверка системных ресурсов"""
        if not self.should_check("resources"):
            return
        
        print(f"[WATCHDOG] Checking resources...")
        resources = get_all_resources(SQLITE_DATABASES)
        
        # RAM
        ram_pct = resources["memory"].get("percent", 0)
        if ram_pct >= THRESHOLDS["ram_critical"]:
            alert_msg = format_resource_alert("RAM", ram_pct, THRESHOLDS["ram_critical"], "critical")
            self.send_alert(alert_msg, "ram_critical")
        elif ram_pct >= THRESHOLDS["ram_warning"]:
            alert_msg = format_resource_alert("RAM", ram_pct, THRESHOLDS["ram_warning"], "warning")
            self.send_alert(alert_msg, "ram_warning")
        
        # CPU
        cpu_pct = resources["cpu"].get("percent", 0)
        if cpu_pct >= THRESHOLDS["cpu_critical"]:
            alert_msg = format_resource_alert("CPU", cpu_pct, THRESHOLDS["cpu_critical"], "critical")
            self.send_alert(alert_msg, "cpu_critical")
        elif cpu_pct >= THRESHOLDS["cpu_warning"]:
            alert_msg = format_resource_alert("CPU", cpu_pct, THRESHOLDS["cpu_warning"], "warning")
            self.send_alert(alert_msg, "cpu_warning")
        
        self.mark_checked("resources")
        self.stats["checks"] += 1
    
    def check_disk(self):
        """Проверка диска"""
        if not self.should_check("disk"):
            return
        
        print(f"[WATCHDOG] Checking disk...")
        resources = get_all_resources(SQLITE_DATABASES)
        
        disk_pct = resources["disk"].get("percent", 0)
        if disk_pct >= THRESHOLDS["disk_critical"]:
            # Автоочистка
            if AUTO_ACTIONS["cleanup_on_disk_critical"]:
                cleanup_result = run_cleanup(CLEANUP_PATHS)
                print(f"[WATCHDOG] Cleanup: freed {cleanup_result['total_mb']} MB")
            
            alert_msg = format_resource_alert("Disk", disk_pct, THRESHOLDS["disk_critical"], "critical")
            self.send_alert(alert_msg, "disk_critical")
        elif disk_pct >= THRESHOLDS["disk_warning"]:
            alert_msg = format_resource_alert("Disk", disk_pct, THRESHOLDS["disk_warning"], "warning")
            self.send_alert(alert_msg, "disk_warning")
        
        self.mark_checked("disk")
        self.stats["checks"] += 1
    
    def check_billing(self):
        """Проверка балансов"""
        if not self.should_check("billing"):
            return
        
        print(f"[WATCHDOG] Checking billing...")
        billing = check_all_billing(self.timeweb_token)
        
        # Timeweb
        tw = billing.get("timeweb", {})
        if tw.get("success") and tw.get("balance", 999999) <= BILLING["timeweb_critical"]:
            alert_msg = format_billing_alert("Timeweb", tw["balance"], "₽", BILLING["timeweb_critical"], "critical")
            self.send_alert(alert_msg, "billing_timeweb_critical")
        elif tw.get("success") and tw.get("balance", 999999) <= BILLING["timeweb_warning"]:
            alert_msg = format_billing_alert("Timeweb", tw["balance"], "₽", BILLING["timeweb_warning"], "warning")
            self.send_alert(alert_msg, "billing_timeweb_warning")
        
        self.mark_checked("billing")
        self.stats["checks"] += 1
    
    def run_once(self):
        """Выполняет один цикл всех проверок"""
        self.check_services()
        self.check_health()
        self.check_resources()
        self.check_disk()
        self.check_billing()
    
    def run_forever(self, min_interval: int = 10):
        """Запускает бесконечный цикл мониторинга"""
        print(f"[WATCHDOG] Starting... Chat ID: {self.chat_id}")
        print(f"[WATCHDOG] Bot token: {'set' if self.bot_token else 'NOT SET'}")
        print(f"[WATCHDOG] Timeweb token: {'set' if self.timeweb_token else 'NOT SET'}")
        
        # Стартовое уведомление
        start_msg = "🟢 <b>WATCHDOG STARTED</b>\n\n"
        start_msg += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        start_msg += f"🔧 Services: {', '.join(SERVICES)}\n"
        send_telegram_alert(start_msg, self.chat_id, self.bot_token)
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                print(f"[WATCHDOG] Error in check cycle: {e}")
            
            time.sleep(min_interval)
    
    def get_status(self) -> Dict:
        """Возвращает текущий статус watchdog"""
        return {
            "uptime_seconds": (datetime.now() - self.stats["started"]).total_seconds(),
            "checks": self.stats["checks"],
            "alerts_sent": self.stats["alerts_sent"],
            "restarts_attempted": self.stats["restarts_attempted"],
            "last_checks": {k: v.isoformat() for k, v in self.last_check.items()}
        }


def main():
    """Entry point"""
    watchdog = Watchdog()
    
    # Если передан аргумент --once, выполняем один цикл
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print("[WATCHDOG] Running single check cycle...")
        watchdog.run_once()
        print(f"[WATCHDOG] Status: {watchdog.get_status()}")
    else:
        watchdog.run_forever()


if __name__ == "__main__":
    main()
