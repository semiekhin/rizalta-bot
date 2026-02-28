"""Tool definitions for OpenAI Function Calling in RIZALTA AI chat."""

import os
import json
import sqlite3
import logging
from typing import Any

from services.calculator import calculate_roi as calc_roi_service

logger = logging.getLogger(__name__)

# --- OpenAI Tools Schema (passed to API) ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_lots",
            "description": (
                "Поиск апартаментов в RIZALTA Resort Belokurikha. "
                "Ищет по коду лота, корпусу, диапазону площади или цены. "
                "Возвращает список подходящих лотов со статусом, ценой, площадью."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Код лота (например А209, В712). Необязательный."
                    },
                    "building": {
                        "type": "integer",
                        "enum": [1, 2, 3],
                        "description": "Номер корпуса: 1=Family, 2=Business, 3=Digital. Необязательный."
                    },
                    "min_area": {
                        "type": "number",
                        "description": "Минимальная площадь в м². Необязательный."
                    },
                    "max_area": {
                        "type": "number",
                        "description": "Максимальная площадь в м². Необязательный."
                    },
                    "min_price": {
                        "type": "integer",
                        "description": "Минимальная цена в рублях. Необязательный."
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "Максимальная цена в рублях. Необязательный."
                    },
                    "status": {
                        "type": "string",
                        "enum": ["available", "booked", "sold"],
                        "description": "Фильтр по статусу. По умолчанию available."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимум результатов (по умолчанию 10, макс 20)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_lot_details",
            "description": (
                "Получить полную информацию об апартаменте по коду. "
                "Возвращает: площадь, цена, цена за м², этаж, корпус, статус, "
                "количество комнат, URL планировки."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Код лота (например А209, В712)"
                    },
                    "building": {
                        "type": "integer",
                        "enum": [1, 2, 3],
                        "description": "Корпус (если код дублируется между корпусами)"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_roi",
            "description": (
                "Рассчитать инвестиционную доходность (ROI) апартамента RIZALTA. "
                "Можно передать код лота (тогда данные берутся из БД) или area+price напрямую. "
                "Возвращает: ROI %, среднюю годовую доходность, доход от аренды, "
                "рост стоимости, итоговую стоимость за 11 лет (2025-2035)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Код лота. Если указан — area и price берутся из БД."
                    },
                    "building": {
                        "type": "integer",
                        "enum": [1, 2, 3],
                        "description": "Корпус (если код дублируется)"
                    },
                    "area": {
                        "type": "number",
                        "description": "Площадь в м² (если code не указан)"
                    },
                    "price": {
                        "type": "integer",
                        "description": "Цена в рублях (если code не указан)"
                    }
                },
                "required": []
            }
        }
    }
]


# --- Helpers ---

_LAT_TO_CYR = str.maketrans({
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н',
    'K': 'К', 'M': 'М', 'O': 'О', 'P': 'Р', 'S': 'С', 'T': 'Т',
})


def _normalize_code(code: str) -> str:
    return code.strip().upper().translate(_LAT_TO_CYR)


def _get_db_path() -> str:
    return os.getenv("PROPERTIES_DB", "/opt/bot/properties.db")


def _query_db(query: str, params: tuple = ()) -> list[dict]:
    """Execute query and return list of dicts."""
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# --- Tool Executors ---

BUILDING_NAMES = {1: "К1 Family", 2: "К2 Business", 3: "К3 Digital"}


def execute_search_lots(args: dict) -> str:
    """Search lots in properties.db with filters."""
    conditions = []
    params = []

    if args.get("code"):
        code = _normalize_code(args["code"])
        conditions.append("code = ?")
        params.append(code)

    if args.get("building"):
        conditions.append("building = ?")
        params.append(args["building"])

    if args.get("min_area"):
        conditions.append("area_m2 >= ?")
        params.append(args["min_area"])

    if args.get("max_area"):
        conditions.append("area_m2 <= ?")
        params.append(args["max_area"])

    if args.get("min_price"):
        conditions.append("price_rub >= ?")
        params.append(args["min_price"])

    if args.get("max_price"):
        conditions.append("price_rub <= ?")
        params.append(args["max_price"])

    status = args.get("status", "available")
    if status:
        conditions.append("status = ?")
        params.append(status)

    limit = min(args.get("limit", 10), 20)

    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"""
        SELECT code, building, floor, rooms, area_m2, price_rub,
               price_per_m2_rub, status, layout_url
        FROM units
        WHERE {where}
        ORDER BY price_rub ASC
        LIMIT ?
    """
    params.append(limit)

    rows = _query_db(query, tuple(params))

    if not rows:
        return json.dumps({"found": 0, "message": "Лоты по заданным критериям не найдены"}, ensure_ascii=False)

    lots = []
    for r in rows:
        lots.append({
            "code": r["code"],
            "building": BUILDING_NAMES.get(r["building"], f"К{r['building']}"),
            "floor": r["floor"],
            "rooms": r["rooms"],
            "area_m2": r["area_m2"],
            "price_rub": r["price_rub"],
            "price_per_m2": r["price_per_m2_rub"],
            "status": r["status"] or "available",
        })

    return json.dumps({"found": len(lots), "lots": lots}, ensure_ascii=False)


def execute_get_lot_details(args: dict) -> str:
    """Get full details for a specific lot."""
    code = _normalize_code(args["code"])
    building = args.get("building")

    if building:
        rows = _query_db(
            "SELECT * FROM units WHERE code = ? AND building = ?",
            (code, building)
        )
    else:
        rows = _query_db("SELECT * FROM units WHERE code = ?", (code,))

    if not rows:
        return json.dumps({"error": f"Лот {code} не найден"}, ensure_ascii=False)

    if len(rows) > 1:
        options = [{"code": r["code"], "building": r["building"]} for r in rows]
        return json.dumps({
            "multiple": True,
            "message": f"Код {code} найден в нескольких корпусах. Уточните корпус.",
            "options": options
        }, ensure_ascii=False)

    r = rows[0]
    result = {
        "code": r["code"],
        "building": BUILDING_NAMES.get(r["building"], f"К{r['building']}"),
        "building_num": r["building"],
        "floor": r["floor"],
        "rooms": r["rooms"],
        "area_m2": r["area_m2"],
        "price_rub": r["price_rub"],
        "price_per_m2": r["price_per_m2_rub"],
        "status": r["status"] or "available",
        "layout_url": r.get("layout_url", ""),
    }

    return json.dumps(result, ensure_ascii=False)


def execute_calculate_roi(args: dict) -> str:
    """Calculate ROI — by lot code or by area+price."""
    area = args.get("area")
    price = args.get("price")

    if args.get("code"):
        code = _normalize_code(args["code"])
        building = args.get("building")

        if building:
            rows = _query_db(
                "SELECT area_m2, price_rub, code, building FROM units WHERE code = ? AND building = ?",
                (code, building)
            )
        else:
            rows = _query_db(
                "SELECT area_m2, price_rub, code, building FROM units WHERE code = ?",
                (code,)
            )

        if not rows:
            return json.dumps({"error": f"Лот {code} не найден"}, ensure_ascii=False)

        if len(rows) > 1:
            options = [{"code": r["code"], "building": r["building"]} for r in rows]
            return json.dumps({
                "multiple": True,
                "message": f"Код {code} есть в нескольких корпусах. Уточните.",
                "options": options
            }, ensure_ascii=False)

        area = rows[0]["area_m2"]
        price = rows[0]["price_rub"]

    if not area or not price:
        return json.dumps({"error": "Нужно указать code или area+price"}, ensure_ascii=False)

    result = calc_roi_service(area, price)

    summary = {
        "area_m2": result["area"],
        "price_rub": result["price"],
        "price_per_m2": result["price_m2"],
        "total_profit_rub": result["total_profit"],
        "total_rental_income": result["total_rental"],
        "total_growth": result["total_growth"],
        "final_value_rub": result["final_value"],
        "roi_pct": result["roi_pct"],
        "avg_annual_pct": result["avg_annual_pct"],
        "period": "2025-2035 (11 лет)",
        "highlights": {
            "2028": next((y for y in result["years"] if y["year"] == 2028), None),
            "2030": next((y for y in result["years"] if y["year"] == 2030), None),
            "2035": next((y for y in result["years"] if y["year"] == 2035), None),
        }
    }

    return json.dumps(summary, ensure_ascii=False)


# --- Dispatcher ---

TOOL_EXECUTORS = {
    "search_lots": execute_search_lots,
    "get_lot_details": execute_get_lot_details,
    "calculate_roi": execute_calculate_roi,
}


def execute_tool(name: str, arguments: str) -> str:
    """Parse arguments JSON and execute the named tool."""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)

    try:
        args = json.loads(arguments) if isinstance(arguments, str) else arguments
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid arguments: {e}"}, ensure_ascii=False)

    try:
        return executor(args)
    except Exception as e:
        logger.error(f"[TOOL] {name} error: {e}")
        return json.dumps({"error": f"Ошибка выполнения {name}: {str(e)}"}, ensure_ascii=False)
