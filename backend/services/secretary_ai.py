"""Secretary AI — parse tasks from natural language using GPT."""

import os
import json
import logging
from datetime import datetime, timedelta
from openai import OpenAI

logger = logging.getLogger(__name__)


def parse_task_with_ai(text: str) -> dict:
    """Parse a free-text task description into structured data.

    Returns: {task, date, time, client_name, priority}
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback: return raw text as task for today
        return {
            "task": text,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": None,
            "client_name": None,
            "priority": "normal",
        }

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    system_prompt = f"""Ты парсер задач. Из текста на русском извлеки структуру задачи.
Сегодня: {today.strftime("%Y-%m-%d")} ({today.strftime("%A")})
Завтра: {tomorrow.strftime("%Y-%m-%d")}

Верни JSON:
{{
  "task": "описание задачи (кратко)",
  "date": "YYYY-MM-DD",
  "time": "HH:MM" или null,
  "client_name": "имя клиента" или null,
  "priority": "high" | "normal" | "low"
}}

Правила:
- Если дата не указана — ставь сегодня
- "завтра" = {tomorrow.strftime("%Y-%m-%d")}
- "послезавтра" = {(today + timedelta(days=2)).strftime("%Y-%m-%d")}
- "через неделю" = {(today + timedelta(days=7)).strftime("%Y-%m-%d")}
- Если указан день недели — найди ближайший
- "срочно" или "важно" → priority: "high"
- Имена клиентов выделяй в client_name"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=200,
            temperature=0,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)

        # Validate date format
        try:
            datetime.strptime(result.get("date", ""), "%Y-%m-%d")
        except ValueError:
            result["date"] = today.strftime("%Y-%m-%d")

        # Validate time format
        time_val = result.get("time")
        if time_val:
            try:
                datetime.strptime(time_val, "%H:%M")
            except ValueError:
                result["time"] = None

        return {
            "task": result.get("task", text),
            "date": result.get("date", today.strftime("%Y-%m-%d")),
            "time": result.get("time"),
            "client_name": result.get("client_name"),
            "priority": result.get("priority", "normal"),
        }

    except Exception as e:
        logger.error(f"[SECRETARY AI] Parse error: {e}")
        return {
            "task": text,
            "date": today.strftime("%Y-%m-%d"),
            "time": None,
            "client_name": None,
            "priority": "normal",
        }
