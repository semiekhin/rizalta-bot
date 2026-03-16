"""YandexGPT chat service for RIZALTA webapp."""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


def call_yandex_gpt(system_prompt: str, messages: list[dict], model_uri: str | None = None) -> str:
    """Call YandexGPT API and return response text.

    Args:
        system_prompt: System instruction text.
        messages: List of {"role": "user"/"assistant", "content": "..."}.
        model_uri: Optional model URI override (e.g. gpt://folder/yandexgpt-5-pro/latest).

    Returns:
        Response text from YandexGPT.
    """
    api_key = os.getenv("YANDEX_API_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")

    if not api_key or not folder_id:
        raise RuntimeError("YANDEX_API_KEY or YANDEX_FOLDER_ID not set in .env")

    if not model_uri:
        model_uri = f"gpt://{folder_id}/yandexgpt"

    yandex_messages = [{"role": "system", "text": system_prompt}]
    for msg in messages:
        yandex_messages.append({
            "role": msg["role"],
            "text": msg.get("content", ""),
        })

    payload = {
        "modelUri": model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000",
        },
        "messages": yandex_messages,
    }

    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json",
    }

    response = httpx.post(
        YANDEX_API_URL,
        json=payload,
        headers=headers,
        timeout=30.0,
    )
    response.raise_for_status()

    data = response.json()
    text = data["result"]["alternatives"][0]["message"]["text"]
    logger.info(f"[YANDEX] Response: {len(text)} chars")
    return text
