"""
MAX Bot — кнопка быстрого доступа к RIZALTA WebApp.
Запускается как отдельный сервис через systemd.
"""
import os
import logging
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
MAX_API = "https://platform-api.max.ru"
WEBAPP_URL = os.getenv("MAX_WEBAPP_URL", "https://webapp.rizaltaservice.ru")

WELCOME_TEXT = (
    "👋 Добро пожаловать в RIZALTA!\n\n"
    "Инвестиции в курортную недвижимость Белокурихи.\n\n"
    "Нажмите кнопку ниже, чтобы открыть платформу:"
)


async def send_welcome(chat_id: int):
    """Отправляет приветствие с кнопкой-ссылкой на webapp."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{MAX_API}/messages",
                headers={"Authorization": MAX_BOT_TOKEN},
                json={
                    "chat_id": chat_id,
                    "body": {"text": WELCOME_TEXT},
                    "attachments": [{
                        "type": "inline_keyboard",
                        "payload": {
                            "buttons": [[{
                                "type": "link",
                                "text": "🏔 Открыть RIZALTA",
                                "url": WEBAPP_URL
                            }]]
                        }
                    }]
                }
            )
            if resp.status_code != 200:
                logger.error(f"Send welcome error: {resp.text}")
    except Exception as e:
        logger.error(f"Send welcome failed: {e}")


async def poll():
    """Long polling для получения обновлений."""
    marker = None
    logger.info(f"MAX bot started, webapp URL: {WEBAPP_URL}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                params = {"timeout": 30, "types": "message_created"}
                if marker:
                    params["marker"] = marker

                resp = await client.get(
                    f"{MAX_API}/updates",
                    headers={"Authorization": MAX_BOT_TOKEN},
                    params=params
                )

                if resp.status_code != 200:
                    logger.error(f"Poll error: {resp.status_code} {resp.text}")
                    await asyncio.sleep(5)
                    continue

                data = resp.json()
                marker = data.get("marker", marker)

                for update in data.get("updates", []):
                    if update.get("type") == "message_created":
                        chat_id = update.get("message", {}).get("recipient", {}).get("chat_id")
                        if chat_id:
                            await send_welcome(chat_id)

            except httpx.ReadTimeout:
                continue
            except Exception as e:
                logger.error(f"Poll exception: {e}")
                await asyncio.sleep(5)


def main():
    if not MAX_BOT_TOKEN:
        logger.error("MAX_BOT_TOKEN not set!")
        return
    asyncio.run(poll())


if __name__ == "__main__":
    main()
