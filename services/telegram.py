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
    disable_web_page_preview: bool = False,
) -> bool:
    """Отправляет сообщение в Telegram."""
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }
    
    if with_keyboard and buttons:
        reply_markup: Dict[str, Any] = {"resize_keyboard": True}
        
        keyboard_rows = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                if isinstance(button, dict):
                    keyboard_row.append(button)
                else:
                    keyboard_row.append({"text": button})
            keyboard_rows.append(keyboard_row)
        
        reply_markup["keyboard"] = keyboard_rows
        payload["reply_markup"] = json.dumps(reply_markup)
    elif with_keyboard:
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
    disable_web_page_preview: bool = False,
) -> bool:
    """Отправляет сообщение с inline-кнопками."""
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
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
    """Отправляет документ (PDF и т.д.)."""
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
                        data["parse_mode"] = "HTML"
                    
                    r = requests.post(
                        url,
                        data=data,
                        files={"document": (filename, f, "application/pdf")},
                        timeout=120,
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




async def send_video(
    chat_id: int,
    filepath: str,
    caption: Optional[str] = None,
) -> bool:
    """Отправляет видео с превью в чате."""
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    if not os.path.exists(filepath):
        print(f"⚠️ Файл не найден: {filepath}")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    filename = os.path.basename(filepath)
    
    try:
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                with open(filepath, "rb") as f:
                    data = {"chat_id": chat_id, "supports_streaming": True}
                    if caption:
                        data["caption"] = caption
                        data["parse_mode"] = "HTML"
                    
                    r = requests.post(
                        url,
                        data=data,
                        files={"video": (filename, f)},
                        timeout=300,
                    )
                    r.raise_for_status()
                    print(f"[TG] sendVideo {filename} status={r.status_code}")
                    return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки видео: {e}")
                return False
        
        return await loop.run_in_executor(None, _post)
    except Exception as e:
        print(f"⚠️ send_video error: {e}")
        return False

async def answer_callback_query(callback_id: str, text: Optional[str] = None) -> bool:
    """Отвечает на callback query (убирает часики на кнопке)."""
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
    """Отправляет фото (JPG/PNG)."""
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
    """Отправляет альбом фото (до 10 штук)."""
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    if not filepaths:
        return False
    
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


async def download_file(file_id: str, save_path: str) -> Optional[str]:
    """
    Скачивает файл из Telegram по file_id.
    
    Args:
        file_id: ID файла в Telegram
        save_path: Путь для сохранения файла
    
    Returns:
        Путь к сохранённому файлу или None при ошибке
    """
    token = get_token()
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN не задан")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        
        def _download():
            try:
                # Получаем информацию о файле
                url = f"https://api.telegram.org/bot{token}/getFile"
                r = requests.post(url, json={"file_id": file_id}, timeout=10)
                r.raise_for_status()
                
                result = r.json()
                if not result.get("ok"):
                    print(f"[TG] getFile error: {result}")
                    return None
                
                file_path = result["result"]["file_path"]
                
                # Скачиваем файл
                download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                r = requests.get(download_url, timeout=30)
                r.raise_for_status()
                
                # Сохраняем файл
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(r.content)
                
                print(f"[TG] Downloaded file to {save_path}")
                return save_path
                
            except Exception as e:
                print(f"⚠️ Ошибка скачивания файла: {e}")
                return None
        
        return await loop.run_in_executor(None, _download)
    except Exception as e:
        print(f"⚠️ Общая ошибка в download_file: {e}")
        return None
