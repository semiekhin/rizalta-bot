"""
Мониторинг системных ресурсов: RAM, CPU, Disk, SQLite
"""
import os
import subprocess
from typing import Dict, List


def get_memory_usage() -> Dict[str, float]:
    """
    Получает использование RAM
    Returns: {"total_mb": x, "used_mb": x, "percent": x}
    """
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_info = {}
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(':')
                value = int(parts[1])  # в kB
                mem_info[key] = value
        
        total = mem_info.get('MemTotal', 0) / 1024  # MB
        available = mem_info.get('MemAvailable', 0) / 1024  # MB
        used = total - available
        percent = (used / total * 100) if total > 0 else 0
        
        return {
            "total_mb": round(total, 1),
            "used_mb": round(used, 1),
            "available_mb": round(available, 1),
            "percent": round(percent, 1)
        }
    except Exception as e:
        return {"error": str(e), "percent": 0}


def get_cpu_usage() -> Dict[str, float]:
    """
    Получает загрузку CPU (load average)
    Returns: {"load_1m": x, "load_5m": x, "load_15m": x, "percent": x}
    """
    try:
        with open('/proc/loadavg', 'r') as f:
            parts = f.read().split()
        
        load_1m = float(parts[0])
        load_5m = float(parts[1])
        load_15m = float(parts[2])
        
        # Количество CPU
        cpu_count = os.cpu_count() or 1
        # Процент от максимума (load 1.0 на 1 CPU = 100%)
        percent = (load_1m / cpu_count) * 100
        
        return {
            "load_1m": load_1m,
            "load_5m": load_5m,
            "load_15m": load_15m,
            "cpu_count": cpu_count,
            "percent": round(min(percent, 100), 1)
        }
    except Exception as e:
        return {"error": str(e), "percent": 0}


def get_disk_usage(path: str = "/") -> Dict[str, float]:
    """
    Получает использование диска
    Returns: {"total_gb": x, "used_gb": x, "free_gb": x, "percent": x}
    """
    try:
        stat = os.statvfs(path)
        total = (stat.f_blocks * stat.f_frsize) / (1024**3)  # GB
        free = (stat.f_bavail * stat.f_frsize) / (1024**3)   # GB
        used = total - free
        percent = (used / total * 100) if total > 0 else 0
        
        return {
            "total_gb": round(total, 1),
            "used_gb": round(used, 1),
            "free_gb": round(free, 1),
            "percent": round(percent, 1)
        }
    except Exception as e:
        return {"error": str(e), "percent": 0}


def get_sqlite_sizes(db_paths: List[str]) -> Dict[str, float]:
    """
    Получает размеры SQLite баз
    Returns: {path: size_mb}
    """
    results = {}
    for path in db_paths:
        try:
            if os.path.exists(path):
                size_bytes = os.path.getsize(path)
                results[path] = round(size_bytes / (1024**2), 2)  # MB
            else:
                results[path] = 0
        except Exception as e:
            results[path] = -1  # Ошибка
    return results


def get_all_resources(sqlite_paths: List[str] = None) -> Dict[str, dict]:
    """Собирает все метрики ресурсов"""
    return {
        "memory": get_memory_usage(),
        "cpu": get_cpu_usage(),
        "disk": get_disk_usage("/"),
        "sqlite": get_sqlite_sizes(sqlite_paths or [])
    }


if __name__ == "__main__":
    # Тест
    resources = get_all_resources([
        "/opt/bot/data/properties.db",
        "/opt/bot/data/secretary.db"
    ])
    
    mem = resources["memory"]
    print(f"RAM: {mem['used_mb']:.0f}/{mem['total_mb']:.0f} MB ({mem['percent']}%)")
    
    cpu = resources["cpu"]
    print(f"CPU: load {cpu['load_1m']} ({cpu['percent']}%)")
    
    disk = resources["disk"]
    print(f"Disk: {disk['used_gb']:.1f}/{disk['total_gb']:.1f} GB ({disk['percent']}%)")
    
    for path, size in resources["sqlite"].items():
        print(f"SQLite {os.path.basename(path)}: {size} MB")
