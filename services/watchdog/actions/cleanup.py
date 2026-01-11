"""
Очистка временных файлов и кэша
"""
import os
import shutil
from typing import Dict, List, Tuple
from datetime import datetime


def cleanup_directory(path: str, dry_run: bool = False) -> Tuple[int, int]:
    """
    Очищает директорию
    Returns: (files_deleted, bytes_freed)
    """
    if not os.path.exists(path):
        return 0, 0
    
    files_deleted = 0
    bytes_freed = 0
    
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    if not dry_run:
                        os.remove(item_path)
                    files_deleted += 1
                    bytes_freed += size
                elif os.path.isdir(item_path):
                    size = get_dir_size(item_path)
                    if not dry_run:
                        shutil.rmtree(item_path)
                    files_deleted += 1
                    bytes_freed += size
            except PermissionError:
                continue
            except Exception:
                continue
    except Exception:
        pass
    
    return files_deleted, bytes_freed


def get_dir_size(path: str) -> int:
    """Получает размер директории в байтах"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total


def cleanup_pycache(base_paths: List[str], dry_run: bool = False) -> Tuple[int, int]:
    """
    Удаляет все __pycache__ директории
    Returns: (dirs_deleted, bytes_freed)
    """
    dirs_deleted = 0
    bytes_freed = 0
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
        
        for dirpath, dirnames, filenames in os.walk(base_path):
            if '__pycache__' in dirnames:
                pycache_path = os.path.join(dirpath, '__pycache__')
                size = get_dir_size(pycache_path)
                try:
                    if not dry_run:
                        shutil.rmtree(pycache_path)
                    dirs_deleted += 1
                    bytes_freed += size
                except:
                    pass
    
    return dirs_deleted, bytes_freed


def cleanup_old_logs(log_dir: str, days: int = 7, dry_run: bool = False) -> Tuple[int, int]:
    """
    Удаляет логи старше N дней
    Returns: (files_deleted, bytes_freed)
    """
    if not os.path.exists(log_dir):
        return 0, 0
    
    files_deleted = 0
    bytes_freed = 0
    cutoff = datetime.now().timestamp() - (days * 24 * 3600)
    
    try:
        for item in os.listdir(log_dir):
            item_path = os.path.join(log_dir, item)
            if os.path.isfile(item_path):
                try:
                    mtime = os.path.getmtime(item_path)
                    if mtime < cutoff:
                        size = os.path.getsize(item_path)
                        if not dry_run:
                            os.remove(item_path)
                        files_deleted += 1
                        bytes_freed += size
                except:
                    pass
    except:
        pass
    
    return files_deleted, bytes_freed


def run_cleanup(paths: List[str], dry_run: bool = False) -> Dict:
    """
    Выполняет полную очистку
    Returns: {"total_files": x, "total_bytes": x, "details": {...}}
    """
    total_files = 0
    total_bytes = 0
    details = {}
    
    for path in paths:
        if path == "/tmp":
            # Для /tmp удаляем только файлы старше 1 дня
            files, bytes_freed = 0, 0  # Упрощённая очистка
        elif "__pycache__" in path or path.endswith("__pycache__"):
            files, bytes_freed = cleanup_directory(path, dry_run)
        else:
            files, bytes_freed = cleanup_directory(path, dry_run)
        
        total_files += files
        total_bytes += bytes_freed
        details[path] = {"files": files, "bytes": bytes_freed}
    
    # Очистка pycache
    pycache_dirs, pycache_bytes = cleanup_pycache(["/opt/bot", "/opt/bot-dev"], dry_run)
    total_files += pycache_dirs
    total_bytes += pycache_bytes
    details["__pycache__"] = {"dirs": pycache_dirs, "bytes": pycache_bytes}
    
    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024**2), 2),
        "details": details,
        "dry_run": dry_run
    }


if __name__ == "__main__":
    # Тест (dry run)
    result = run_cleanup(["/tmp"], dry_run=True)
    print(f"Would clean: {result['total_files']} items, {result['total_mb']} MB")
    print(f"Details: {result['details']}")
