"""
AI-консультант на базе OpenAI с Function Calling.
"""

import json
import re
from typing import Dict, Any, List, Optional

from openai import OpenAI

from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS
from services.data_loader import load_finance, load_instructions


# Инициализация клиента
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# === ФУНКЦИИ ДЛЯ AI (Function Calling) ===

AVAILABLE_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "build_portfolio",
            "description": "Подобрать инвестиционный портфель под бюджет пользователя. Вызывай когда пользователь говорит про бюджет, хочет собрать портфель, подобрать лот, узнать что можно купить на определённую сумму.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget": {
                        "type": "number",
                        "description": "Бюджет в рублях. Например: 15000000 для 15 млн, 5000000 для 5 млн."
                    }
                },
                "required": ["budget"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_roi",
            "description": "Рассчитать доходность конкретного гостиничный номера. Вызывай когда пользователь спрашивает про доходность, ROI, сколько можно заработать на конкретном юните.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit_code": {
                        "type": "string",
                        "enum": ["A209", "B210", "A305"],
                        "description": "Код гостиничный номера: A209 (студия), B210 (стандарт), A305 (люкс)"
                    }
                },
                "required": ["unit_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_installment",
            "description": "Показать варианты рассрочки и ипотеки. Вызывай когда пользователь спрашивает про рассрочку, ипотеку, как оплатить, варианты оплаты.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit_code": {
                        "type": "string",
                        "enum": ["A209", "B210", "A305"],
                        "description": "Код гостиничный номера (опционально)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_showing",
            "description": "Записать на онлайн-показ гостиничных номеров. Вызывай когда пользователь хочет записаться на показ, посмотреть гостиничные номера, связаться с менеджером, получить консультацию.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_layouts",
            "description": "Показать планировки гостиничных номеров. Вызывай когда пользователь просит планировку, схему, план квартиры.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit_code": {
                        "type": "string",
                        "enum": ["A209", "B210", "A305"],
                        "description": "Код гостиничный номера (опционально)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_commercial_proposal",
            "description": "Получить коммерческое предложение (КП) на гостиничный номер. Вызывай когда пользователь просит КП, коммерческое предложение, презентацию по лоту, предложение на конкретную площадь или бюджет.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit_code": {
                        "type": "string",
                        "description": "Код гостиничный номера (например А209, В415)"
                    },
                    "area": {
                        "type": "number",
                        "description": "Площадь в м² (например 25, 30.5)"
                    },
                    "budget": {
                        "type": "number",
                        "description": "Бюджет в рублях"
                    },
                    "floor": {
                        "type": "integer",
                        "description": "Этаж"
                    },
                    "block_section": {
                        "type": "integer",
                        "enum": [1, 2],
                        "description": "Корпус: 1 = корпус 2 (А), 2 = корпус 1 (В)"
                    }
                },
                "required": []
            }
        }
    }
]


def build_finance_system_context(finance: Dict[str, Any]) -> str:
    """
    Строит полный контекст с финансовыми данными для AI.
    """
    completion = finance.get("completion_year", 2027)
    project = finance.get("project", "RIZALTA Resort Belokurikha")
    defaults = finance.get("defaults", {})
    installments = finance.get("installment_programs", [])
    mortgages = finance.get("mortgage_programs", [])
    units = finance.get("units", [])
    extra_notes = finance.get("extra_notes", {})
    installment_notes = finance.get("installment_notes", {})
    
    lines: List[str] = []
    lines.append("=== ФИНАНСОВЫЕ ДАННЫЕ ПРОЕКТА (используй только эти цифры) ===")
    lines.append("")
    lines.append(f"Проект: {project}")
    lines.append(f"Срок сдачи: Q4 {completion} года")
    lines.append("")
    
    # === ВСЕ ЮНИТЫ ===
    lines.append("=== АПАРТАМЕНТЫ ===")
    for u in units:
        code = u.get("unit_code", "")
        title = u.get("title", code)
        area = u.get("area_m2", 0)
        price = u.get("price_rub", 0)
        daily = u.get("daily_rate_rub", defaults.get("daily_rate_rub", 15000))
        occ = u.get("occupancy_pct", defaults.get("occupancy_pct", 60))
        exp = u.get("expenses_pct", defaults.get("expenses_pct", 50))
        
        gross_year = daily * 365 * (occ / 100)
        net_year = gross_year * (1 - exp / 100)
        roi_pct = (net_year / price * 100) if price > 0 else 0
        
        cap = u.get("capitalization_projection", {})
        price_2027 = cap.get("price_2027_rub", 0)
        price_2029 = cap.get("price_2029_rub", 0)
        
        lines.append(f"• {title} ({area} м²):")
        lines.append(f"  Цена: {price:,.0f} ₽")
        lines.append(f"  Точка входа (ПВ 30%): ~{price * 0.3:,.0f} ₽")
        lines.append(f"  Доход от аренды: ~{net_year:,.0f} ₽/год ({roi_pct:.1f}% годовых)")
        if price_2027:
            growth_2027 = ((price_2027 - price) / price * 100)
            lines.append(f"  Прогноз 2027: {price_2027:,.0f} ₽ (+{growth_2027:.0f}%)")
        if price_2029:
            growth_2029 = ((price_2029 - price) / price * 100)
            lines.append(f"  Прогноз 2029: {price_2029:,.0f} ₽ (+{growth_2029:.0f}%)")
        lines.append("")
    
    # === БАЗОВЫЕ ДОПУЩЕНИЯ ===
    lines.append("=== БАЗОВЫЕ ДОПУЩЕНИЯ ===")
    daily = defaults.get("daily_rate_rub", 15000)
    occ = defaults.get("occupancy_pct", 60)
    exp = defaults.get("expenses_pct", 50)
    lines.append(f"• Ставка аренды: {daily:,} ₽/сутки")
    lines.append(f"• Загрузка: {occ}%")
    lines.append(f"• Операционные расходы: {exp}% от выручки")
    lines.append("")
    
    # === РАССРОЧКА ===
    lines.append("=== ПРОГРАММЫ РАССРОЧКИ ===")
    for inst in installments:
        name = inst.get("name", "")
        pv = inst.get("first_payment_pct", 30)
        months = inst.get("months", 12)
        rate = inst.get("rate_pct", 0)
        lines.append(f"• {name}: ПВ {pv}%, срок {months} мес, ставка {rate}%")
    lines.append("")
    
    # === ИПОТЕКА ===
    lines.append("=== ИПОТЕКА ===")
    for m in mortgages:
        name = m.get("name", "Ипотека")
        pv_pct = m.get("first_payment_pct", 30)
        grace = m.get("grace_period_months", 12)
        reduced = m.get("reduced_payment_rub", 0)
        promo_rate = m.get("promo_rate_pct", 0)
        lines.append(f"• {name}: ПВ {pv_pct:.1f}%, льготный период {grace} мес, платёж {reduced:,.0f} ₽/мес (ставка {promo_rate}%)")
    lines.append("")
    
    return "\n".join(lines)


def analyze_user_intent(user_text: str) -> Dict[str, Any]:
    """
    Анализирует намерение пользователя через OpenAI Function Calling.
    Возвращает: {"intent": "function_name", "params": {...}} или {"intent": "chat", "response": "..."}
    """
    if not client:
        return {"intent": "chat", "response": None}
    
    instructions = load_instructions()
    finance = load_finance()
    if finance:
        instructions = instructions + "\n\n" + build_finance_system_context(finance)
    
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_text}
    ]
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=AVAILABLE_FUNCTIONS,
            tool_choice="auto",
            max_tokens=OPENAI_MAX_TOKENS
        )
        
        message = response.choices[0].message
        
        # Если AI решил вызвать функцию
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            
            return {
                "intent": function_name,
                "params": arguments
            }
        
        # Обычный текстовый ответ
        return {
            "intent": "chat",
            "response": message.content
        }
        
    except Exception as e:
        print(f"[AI] Error in analyze_user_intent: {e}")
        return {"intent": "chat", "response": None}


def ask_ai_about_project(user_text: str) -> str:
    """
    Обычный AI ответ (без function calling).
    Используется как fallback.
    """
    if not client:
        return (
            "ИИ-сервис временно недоступен. "
            "Предлагаю подключить менеджера для консультации."
        )
    
    instructions = load_instructions()
    finance = load_finance()
    if finance:
        instructions = instructions + "\n\n" + build_finance_system_context(finance)
    
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_text}
    ]
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=OPENAI_MAX_TOKENS
        )
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"[AI] Error: {e}")
        return (
            "Сейчас ИИ-сервис временно недоступен. "
            "Предлагаю подключить менеджера застройщика."
        )
