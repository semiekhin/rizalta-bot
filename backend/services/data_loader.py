"""Data loader for AI chat — loads finance data and instructions."""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

_finance_cache = None
_instructions_cache = None
_knowledge_cache = None


def load_finance() -> dict:
    """Load rizalta_finance.json (cached after first read)."""
    global _finance_cache
    if _finance_cache is not None:
        return _finance_cache

    path = os.path.join(DATA_DIR, "rizalta_finance.json")
    if not os.path.exists(path):
        print(f"[AI] Warning: {path} not found. Copy from /opt/bot/data/rizalta_finance.json")
        _finance_cache = {}
        return _finance_cache

    with open(path, "r", encoding="utf-8") as f:
        _finance_cache = json.load(f)
    print(f"[AI] Loaded finance data: {len(json.dumps(_finance_cache))} chars")
    return _finance_cache


def load_instructions() -> str:
    """Load system instructions for AI chat (cached after first read)."""
    global _instructions_cache
    if _instructions_cache is not None:
        return _instructions_cache

    path = os.path.join(CONFIG_DIR, "instructions.txt")
    if not os.path.exists(path):
        print(f"[AI] Warning: {path} not found")
        _instructions_cache = "Ты — AI-консультант RIZALTA. Помогай с вопросами о проекте."
        return _instructions_cache

    with open(path, "r", encoding="utf-8") as f:
        _instructions_cache = f.read().strip()
    print(f"[AI] Loaded instructions: {len(_instructions_cache)} chars")
    return _instructions_cache


def load_project_knowledge() -> str:
    """Load fundamental product knowledge for AI chat (cached after first read)."""
    global _knowledge_cache
    if _knowledge_cache is not None:
        return _knowledge_cache

    path = os.path.join(CONFIG_DIR, "project_knowledge.txt")
    if not os.path.exists(path):
        print(f"[AI] Warning: {path} not found")
        _knowledge_cache = ""
        return _knowledge_cache

    with open(path, "r", encoding="utf-8") as f:
        _knowledge_cache = f.read().strip()
    print(f"[AI] Loaded project knowledge: {len(_knowledge_cache)} chars")
    return _knowledge_cache
