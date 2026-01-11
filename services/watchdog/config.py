"""
Watchdog Configuration
Конфигурация системы мониторинга и самовосстановления
"""

# Telegram алерты
ALERT_CHAT_ID = 512319063
ALERT_BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"  # из .env

# Интервалы проверок (секунды)
INTERVALS = {
    "services": 60,      # Проверка systemd сервисов
    "health": 60,        # HTTP health check
    "resources": 300,    # RAM, CPU (5 мин)
    "disk": 3600,        # Диск (1 час)
    "billing": 21600,    # Биллинг (6 часов)
}

# Сервисы для мониторинга
SERVICES = [
    "rizalta-bot",
    "rizalta-bot-dev",
    "rizalta-dev-api",
    "cloudflare-rizalta",
    "rizalta-dev-tunnel",
]

# Health endpoints (корневой "/" возвращает {"ok":true})
HEALTH_ENDPOINTS = {
    "prod": "http://localhost:8000/",
    "dev": "http://localhost:8002/",
}

# Пороги ресурсов (%)
THRESHOLDS = {
    "ram_warning": 80,
    "ram_critical": 90,
    "cpu_warning": 80,
    "cpu_critical": 95,
    "disk_warning": 80,
    "disk_critical": 90,
    "sqlite_max_mb": 500,
}

# Пороги биллинга
BILLING = {
    "openai_warning": 10,    # $
    "openai_critical": 3,    # $
    "timeweb_warning": 500,  # ₽
    "timeweb_critical": 100, # ₽
}

# Timeweb API
TIMEWEB_API_URL = "https://api.timeweb.cloud/api/v1/account/finances"
TIMEWEB_TOKEN_ENV = "TIMEWEB_API_TOKEN"  # из .env

# Автодействия
AUTO_ACTIONS = {
    "restart_on_failure": True,
    "max_restarts": 3,
    "cooldown_minutes": 5,
    "cleanup_on_disk_critical": True,
}

# Безопасные команды для рестарта
SAFE_RESTART_COMMANDS = [
    "systemctl restart rizalta-bot",
    "systemctl restart rizalta-bot-dev",
    "systemctl restart rizalta-dev-api",
    "systemctl restart cloudflare-rizalta",
    "systemctl restart rizalta-dev-tunnel",
]

# Пути для очистки при нехватке диска
CLEANUP_PATHS = [
    "/tmp",
    "/opt/bot/services/__pycache__",
    "/opt/bot-dev/services/__pycache__",
]

# SQLite базы для мониторинга размера (актуальные пути)
SQLITE_DATABASES = [
    "/opt/bot/properties.db",
    "/opt/bot/secretary.db",
    "/opt/bot/monitoring.db",
    "/opt/bot-dev/properties.db",
    "/opt/bot-dev/secretary.db",
]
