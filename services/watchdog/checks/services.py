"""
Проверка systemd сервисов
"""
import subprocess
from typing import Dict, List, Tuple


def check_service_status(service_name: str) -> Tuple[bool, str]:
    """
    Проверяет статус systemd сервиса
    Returns: (is_active, status_text)
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        status = result.stdout.strip()
        is_active = status == "active"
        return is_active, status
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {str(e)}"


def check_all_services(services: List[str]) -> Dict[str, dict]:
    """
    Проверяет все сервисы из списка
    Returns: {service_name: {"active": bool, "status": str}}
    """
    results = {}
    for service in services:
        is_active, status = check_service_status(service)
        results[service] = {
            "active": is_active,
            "status": status
        }
    return results


def get_service_logs(service_name: str, lines: int = 20) -> str:
    """Получает последние логи сервиса"""
    try:
        result = subprocess.run(
            ["journalctl", "-u", service_name, "-n", str(lines), "--no-pager"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout
    except Exception as e:
        return f"Ошибка получения логов: {e}"


if __name__ == "__main__":
    # Тест
    from config import SERVICES
    results = check_all_services(SERVICES)
    for name, data in results.items():
        emoji = "✅" if data["active"] else "❌"
        print(f"{emoji} {name}: {data['status']}")
