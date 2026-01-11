"""
Автоматический перезапуск сервисов
"""
import subprocess
import time
from typing import Tuple, Dict
from datetime import datetime, timedelta


# Хранение истории рестартов (в памяти)
_restart_history: Dict[str, list] = {}


def restart_service(service_name: str, safe_commands: list) -> Tuple[bool, str]:
    """
    Перезапускает systemd сервис
    Returns: (success, message)
    """
    command = f"systemctl restart {service_name}"
    
    # Проверка что команда в белом списке
    if command not in safe_commands:
        return False, f"Command not in safe list: {command}"
    
    try:
        result = subprocess.run(
            ["systemctl", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Ждём немного и проверяем статус
            time.sleep(2)
            status_result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.stdout.strip() == "active":
                _record_restart(service_name, True)
                return True, "Service restarted successfully"
            else:
                _record_restart(service_name, False)
                return False, f"Restart executed but service not active: {status_result.stdout.strip()}"
        else:
            _record_restart(service_name, False)
            return False, f"Restart failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Restart timeout"
    except Exception as e:
        return False, f"Restart error: {str(e)}"


def _record_restart(service_name: str, success: bool):
    """Записывает попытку рестарта в историю"""
    if service_name not in _restart_history:
        _restart_history[service_name] = []
    
    _restart_history[service_name].append({
        "time": datetime.now(),
        "success": success
    })
    
    # Храним только последние 10 записей
    _restart_history[service_name] = _restart_history[service_name][-10:]


def can_restart(service_name: str, max_restarts: int, cooldown_minutes: int) -> Tuple[bool, str]:
    """
    Проверяет можно ли перезапустить сервис (защита от restart loop)
    Returns: (can_restart, reason)
    """
    if service_name not in _restart_history:
        return True, "No previous restarts"
    
    history = _restart_history[service_name]
    cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)
    
    # Считаем рестарты за период cooldown
    recent_restarts = [r for r in history if r["time"] > cutoff_time]
    
    if len(recent_restarts) >= max_restarts:
        return False, f"Max restarts ({max_restarts}) reached in {cooldown_minutes} min"
    
    return True, f"Restarts in window: {len(recent_restarts)}/{max_restarts}"


def get_restart_stats(service_name: str) -> Dict:
    """Возвращает статистику рестартов"""
    if service_name not in _restart_history:
        return {"total": 0, "successful": 0, "failed": 0, "history": []}
    
    history = _restart_history[service_name]
    successful = sum(1 for r in history if r["success"])
    
    return {
        "total": len(history),
        "successful": successful,
        "failed": len(history) - successful,
        "history": [
            {"time": r["time"].isoformat(), "success": r["success"]}
            for r in history[-5:]  # Последние 5
        ]
    }


def attempt_restart(
    service_name: str,
    safe_commands: list,
    max_restarts: int = 3,
    cooldown_minutes: int = 5
) -> Tuple[bool, str, bool]:
    """
    Пытается перезапустить сервис с проверкой лимитов
    Returns: (success, message, was_attempted)
    """
    # Проверяем можно ли рестартить
    can_do, reason = can_restart(service_name, max_restarts, cooldown_minutes)
    
    if not can_do:
        return False, reason, False
    
    # Выполняем рестарт
    success, message = restart_service(service_name, safe_commands)
    return success, message, True


if __name__ == "__main__":
    # Тест
    safe = ["systemctl restart rizalta-bot-dev"]
    
    can, reason = can_restart("rizalta-bot-dev", 3, 5)
    print(f"Can restart: {can} - {reason}")
    
    print("\nRestart stats:", get_restart_stats("rizalta-bot-dev"))
