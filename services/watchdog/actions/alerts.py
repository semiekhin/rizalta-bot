"""
Telegram алерты для Watchdog
"""
import urllib.request
import urllib.error
import json
import os
from typing import Optional
from datetime import datetime


def send_telegram_alert(
    message: str,
    chat_id: int,
    bot_token: str,
    parse_mode: str = "HTML"
) -> bool:
    """
    Отправляет алерт в Telegram
    Returns: success
    """
    if not bot_token:
        print(f"[ALERT] No bot token, message: {message}")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }).encode('utf-8')
        
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.getcode() == 200
    except Exception as e:
        print(f"[ALERT] Failed to send: {e}")
        return False


def format_service_alert(service: str, status: str, action_taken: str = None) -> str:
    """Форматирует алерт о сервисе"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    msg = f"🚨 <b>WATCHDOG ALERT</b>\n\n"
    msg += f"⏰ {timestamp}\n"
    msg += f"🔧 Сервис: <code>{service}</code>\n"
    msg += f"❌ Статус: {status}\n"
    if action_taken:
        msg += f"⚡ Действие: {action_taken}\n"
    return msg


def format_health_alert(endpoint: str, url: str, status_code: int, message: str) -> str:
    """Форматирует алерт о health check"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    msg = f"🚨 <b>HEALTH CHECK FAILED</b>\n\n"
    msg += f"⏰ {timestamp}\n"
    msg += f"🌐 Endpoint: <code>{endpoint}</code>\n"
    msg += f"🔗 URL: {url}\n"
    msg += f"📊 Status: {status_code}\n"
    msg += f"💬 {message[:100]}\n"
    return msg


def format_resource_alert(resource: str, value: float, threshold: float, level: str) -> str:
    """Форматирует алерт о ресурсах"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = "⚠️" if level == "warning" else "🔴"
    msg = f"{emoji} <b>RESOURCE {level.upper()}</b>\n\n"
    msg += f"⏰ {timestamp}\n"
    msg += f"📊 {resource}: <b>{value:.1f}%</b>\n"
    msg += f"🎯 Порог: {threshold}%\n"
    return msg


def format_billing_alert(service: str, balance: float, currency: str, threshold: float, level: str) -> str:
    """Форматирует алерт о биллинге"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = "⚠️" if level == "warning" else "🔴"
    msg = f"{emoji} <b>BILLING {level.upper()}</b>\n\n"
    msg += f"⏰ {timestamp}\n"
    msg += f"💳 {service}: <b>{balance:.2f} {currency}</b>\n"
    msg += f"🎯 Порог: {threshold} {currency}\n"
    return msg


def format_recovery_alert(service: str, attempts: int) -> str:
    """Форматирует алерт об успешном восстановлении"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    msg = f"✅ <b>SERVICE RECOVERED</b>\n\n"
    msg += f"⏰ {timestamp}\n"
    msg += f"🔧 Сервис: <code>{service}</code>\n"
    msg += f"🔄 Попыток: {attempts}\n"
    return msg


def format_status_report(services: dict, resources: dict, billing: dict) -> str:
    """Форматирует полный отчёт о статусе"""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    msg = f"📊 <b>WATCHDOG STATUS</b>\n"
    msg += f"⏰ {timestamp}\n\n"
    
    # Сервисы
    msg += "<b>Сервисы:</b>\n"
    for name, data in services.items():
        emoji = "✅" if data.get("active") else "❌"
        msg += f"  {emoji} {name}\n"
    
    # Ресурсы
    msg += "\n<b>Ресурсы:</b>\n"
    if "memory" in resources:
        msg += f"  💾 RAM: {resources['memory'].get('percent', 0):.0f}%\n"
    if "cpu" in resources:
        msg += f"  ⚡ CPU: {resources['cpu'].get('percent', 0):.0f}%\n"
    if "disk" in resources:
        msg += f"  💿 Disk: {resources['disk'].get('percent', 0):.0f}%\n"
    
    # Биллинг
    msg += "\n<b>Биллинг:</b>\n"
    if "timeweb" in billing and billing["timeweb"].get("success"):
        msg += f"  🌐 Timeweb: {billing['timeweb']['balance']:.0f} ₽\n"
    
    return msg


if __name__ == "__main__":
    # Тест форматирования
    print(format_service_alert("rizalta-bot", "inactive", "restart attempted"))
    print()
    print(format_resource_alert("RAM", 85.5, 80, "warning"))
