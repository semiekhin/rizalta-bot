"""
Сервис отправки сообщений в Telegram.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional

import requests

from config.settings import TELEGRAM_BOT_TOKEN, TG_API


def get_token() -> str:
    """Получает токен бота."""
    return TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_TOKEN", "")


async def send_message(
    chat_id: int,
    text: str,
    with_keyboard: bool = False,
    buttons: Optional[List[List[Any]]] = None,
    parse_mode: str = "HTML",
) -> bool:
    """
    Отправляет сообщение в Telegram.
    
    Args:
        chat_id: ID чата
        text: Текст сообщения
        with_keyboard: Добавить reply keyboard
        buttons: Кнопки клавиатуры (простые строки или dict с параметрами)
        parse_mode: HTML или Markdown
    
    Returns:
        True если отправлено успешно
    """
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    
    # Добавляем клавиатуру
    if with_keyboard and buttons:
        reply_markup: Dict[str, Any] = {"resize_keyboard": True}
        
        keyboard_rows = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                if isinstance(button, dict):
                    # Уже словарь (например, с request_contact)
                    keyboard_row.append(button)
                else:
                    # Простая строка
                    keyboard_row.append({"text": button})
            keyboard_rows.append(keyboard_row)
        
        reply_markup["keyboard"] = keyboard_rows
        payload["reply_markup"] = json.dumps(reply_markup)
    elif with_keyboard:
        # Пустая клавиатура — показываем дефолтную
        payload["reply_markup"] = json.dumps({"resize_keyboard": True})
    
    try:
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                r = requests.post(url, json=payload, timeout=10)
                r.raise_for_status()
                return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки в Telegram: {e}")
                return False
        
        return await loop.run_in_executor(None, _post)
    except Exception as e:
        print(f"⚠️ Общая ошибка в send_message: {e}")
        return False


async def send_message_inline(
    chat_id: int,
    text: str,
    inline_buttons: Optional[List[List[Dict[str, str]]]] = None,
    parse_mode: str = "HTML",
) -> bool:
    """
    Отправляет сообщение с inline-кнопками.
    
    Args:
        chat_id: ID чата
        text: Текст сообщения
        inline_buttons: Inline-кнопки [
            [{"text": "Текст", "callback_data": "action"}],
            ...
        ]
        parse_mode: HTML или Markdown
    """
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    
    if inline_buttons:
        reply_markup = {"inline_keyboard": inline_buttons}
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                r = requests.post(url, json=payload, timeout=10)
                r.raise_for_status()
                return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки inline в Telegram: {e}")
                return False
        
        return await loop.run_in_executor(None, _post)
    except Exception as e:
        print(f"⚠️ Общая ошибка в send_message_inline: {e}")
        return False


async def send_document(
    chat_id: int,
    filepath: str,
    caption: Optional[str] = None,
) -> bool:
    """
    Отправляет документ (PDF и т.д.).
    
    Args:
        chat_id: ID чата
        filepath: Путь к файлу
        caption: Подпись (опционально)
    """
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    if not os.path.exists(filepath):
        print(f"⚠️ Файл не найден: {filepath}")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    filename = os.path.basename(filepath)
    
    try:
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                with open(filepath, "rb") as f:
                    data = {"chat_id": chat_id}
                    if caption:
                        data["caption"] = caption
                    
                    r = requests.post(
                        url,
                        data=data,
                        files={"document": (filename, f, "application/pdf")},
                        timeout=60,
                    )
                    r.raise_for_status()
                    print(f"[TG] sendDocument {filename} status={r.status_code}")
                    return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки документа: {e}")
                return False
        
        return await loop.run_in_executor(None, _post)
    except Exception as e:
        print(f"⚠️ Общая ошибка в send_document: {e}")
        return False


async def answer_callback_query(callback_id: str, text: Optional[str] = None) -> bool:
    """
    Отвечает на callback query (убирает часики на кнопке).
    
    Args:
        callback_id: ID callback query
        text: Текст уведомления (опционально)
    """
    token = get_token()
    if not token:
        return False
    
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    
    payload: Dict[str, Any] = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    
    try:
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                r = requests.post(url, json=payload, timeout=5)
                return r.status_code == 200
            except Exception as e:
                print(f"[CALLBACK] Error: {e}")
                return False
        
        return await loop.run_in_executor(None, _post)
    except Exception:
        return False


async def send_photo(
    chat_id: int,
    filepath: str,
    caption: Optional[str] = None,
) -> bool:
    """
    Отправляет фото (JPG/PNG).
    
    Args:
        chat_id: ID чата
        filepath: Путь к файлу
        caption: Подпись (опционально)
    """
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    if not os.path.exists(filepath):
        print(f"⚠️ Файл не найден: {filepath}")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    filename = os.path.basename(filepath)
    
    try:
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                with open(filepath, "rb") as f:
                    data = {"chat_id": chat_id, "parse_mode": "HTML"}
                    if caption:
                        data["caption"] = caption
                    
                    r = requests.post(
                        url,
                        data=data,
                        files={"photo": (filename, f, "image/jpeg")},
                        timeout=60,
                    )
                    r.raise_for_status()
                    print(f"[TG] sendPhoto {filename} status={r.status_code}")
                    return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки фото: {e}")
                return False
        
        return await loop.run_in_executor(None, _post)
    except Exception as e:
        print(f"⚠️ Общая ошибка в send_photo: {e}")
        return False


async def send_media_group(
    chat_id: int,
    filepaths: List[str],
    caption: Optional[str] = None,
) -> bool:
    """
    Отправляет альбом фото (до 10 штук).
    
    Args:
        chat_id: ID чата
        filepaths: Список путей к файлам
        caption: Подпись к первому фото (опционально)
    """
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    if not filepaths:
        return False
    
    # Telegram ограничивает альбом до 10 фото
    filepaths = filepaths[:10]
    
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    
    try:
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                files = {}
                media = []
                
                for i, filepath in enumerate(filepaths):
                    if not os.path.exists(filepath):
                        print(f"⚠️ Файл не найден: {filepath}")
                        continue
                    
                    attach_name = f"photo{i}"
                    files[attach_name] = open(filepath, "rb")
                    
                    item = {
                        "type": "photo",
                        "media": f"attach://{attach_name}",
                    }
                    
                    # Подпись только к первому фото
                    if i == 0 and caption:
                        item["caption"] = caption
                        item["parse_mode"] = "HTML"
                    
                    media.append(item)
                
                if not media:
                    return False
                
                data = {
                    "chat_id": chat_id,
                    "media": json.dumps(media),
                }
                
                r = requests.post(url, data=data, files=files, timeout=120)
                
                # Закрываем файлы
                for f in files.values():
                    f.close()
                
                r.raise_for_status()
                print(f"[TG] sendMediaGroup {len(media)} photos, status={r.status_code}")
                return True
                
            except Exception as e:
                print(f"⚠️ Ошибка отправки альбома: {e}")
                return False
        
        return await loop.run_in_executor(None, _post)
    except Exception as e:
        print(f"⚠️ Общая ошибка в send_media_group: {e}")
        return False


# ====== Алиасы для совместимости ======

# Короткие имена для удобства использования в handlers
_send_tg = send_message
_send_tg_inline = send_message_inline


async def send_document(chat_id: int, filepath: str, caption: str = "") -> bool:
    """Отправляет документ (PDF) в чат."""
    import os
    
    if not os.path.exists(filepath):
        print(f"[TG] Document not found: {filepath}")
        return False
    
    url = f"{TG_API}/sendDocument"
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(filepath, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('chat_id', str(chat_id))
                data.add_field('document', f, filename=os.path.basename(filepath))
                if caption:
                    data.add_field('caption', caption)
                    data.add_field('parse_mode', 'HTML')
                
                async with session.post(url, data=data) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        print(f"[TG] sendDocument error: {result}")
                        return False
                    return True
    except Exception as e:
        print(f"[TG] sendDocument exception: {e}")
        return False
