#!/usr/bin/env python3
"""
DEV режим — polling вместо webhook.
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Импортируем обработчики из app.py
from app import process_callback, process_message, process_voice_message, handle_contact_shared

async def get_updates(session, offset=None, timeout=30):
    """Получает обновления через long polling."""
    url = f"{TG_API}/getUpdates"
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        return data.get("result", [])

async def delete_webhook(session):
    """Удаляет webhook перед запуском polling."""
    url = f"{TG_API}/deleteWebhook"
    async with session.post(url) as resp:
        result = await resp.json()
        print(f"[DEV] Webhook deleted: {result.get('ok')}")

async def handle_update(upd):
    """Обработка одного update — копия логики из webhook."""
    
    # Callback Query (inline-кнопки)
    callback_query = upd.get("callback_query")
    if callback_query:
        await process_callback(callback_query)
        return
    
    # Message
    msg = upd.get("message") or upd.get("edited_message")
    if not msg:
        return
    
    chat_id = msg["chat"]["id"]
    text = (msg.get("text") or "").strip()
    
    # Контакт
    contact_data = msg.get("contact")
    if contact_data:
        await handle_contact_shared(chat_id, contact_data)
        return
    
    # Голосовое сообщение
    voice = msg.get("voice")
    if voice:
        await process_voice_message(chat_id, voice, msg.get("from", {}))
        return
    
    if not text:
        return
    
    user_info = msg.get("from", {})
    await process_message(chat_id, text, user_info)

async def main():
    print("[DEV] RIZALTA Bot — режим polling")
    print("[DEV] Ctrl+C для остановки")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        await delete_webhook(session)
        
        offset = None
        while True:
            try:
                updates = await get_updates(session, offset)
                for update in updates:
                    offset = update["update_id"] + 1
                    print(f"[DEV] update: {update}")
                    try:
                        await handle_update(update)
                    except Exception as e:
                        print(f"[DEV] Ошибка обработки: {e}")
                        import traceback
                        traceback.print_exc()
            except asyncio.CancelledError:
                print("\n[DEV] Остановка...")
                break
            except Exception as e:
                print(f"[DEV] Ошибка polling: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
