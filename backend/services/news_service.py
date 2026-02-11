"""News service — weather, flights, RSS digest for RIZALTA webapp."""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ==================== ПОГОДА (Open-Meteo) ====================

BELOKURIKHA_LAT = 51.996
BELOKURIKHA_LON = 84.993

WEATHER_CODES = {
    0: ("☀️", "ясно"), 1: ("🌤", "малооблачно"), 2: ("⛅", "переменная облачность"),
    3: ("☁️", "облачно"), 45: ("🌫", "туман"), 48: ("🌫", "изморозь"),
    51: ("🌧", "морось"), 53: ("🌧", "морось"), 55: ("🌧", "морось"),
    61: ("🌧", "дождь"), 63: ("🌧", "дождь"), 65: ("🌧", "сильный дождь"),
    71: ("❄️", "снег"), 73: ("❄️", "снег"), 75: ("❄️", "сильный снег"),
    77: ("❄️", "снежная крупа"), 80: ("🌦", "ливень"), 81: ("🌦", "ливень"),
    82: ("🌦", "сильный ливень"), 85: ("🌨", "снегопад"), 86: ("🌨", "сильный снегопад"),
    95: ("⛈", "гроза"), 96: ("⛈", "гроза с градом"), 99: ("⛈", "гроза с градом"),
}


async def get_weather() -> Optional[Dict]:
    """Gets weather + forecast for Belokurikha via Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={BELOKURIKHA_LAT}&longitude={BELOKURIKHA_LON}"
        f"&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"
        f"&hourly=temperature_2m,weather_code&timezone=Asia/Barnaul&forecast_hours=4"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                hourly = data.get("hourly", {})

                weather_code = current.get("weather_code", 0)
                icon, description = WEATHER_CODES.get(weather_code, ("🌤", "переменно"))

                forecast = []
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                codes = hourly.get("weather_code", [])
                for i in range(1, min(4, len(times))):
                    hour = times[i].split("T")[1][:5] if "T" in times[i] else times[i]
                    temp = temps[i] if i < len(temps) else 0
                    code = codes[i] if i < len(codes) else 0
                    fc_icon, _ = WEATHER_CODES.get(code, ("🌤", ""))
                    forecast.append({"hour": hour, "temp": round(temp), "icon": fc_icon})

                return {
                    "temp": round(current.get("temperature_2m", 0)),
                    "humidity": current.get("relative_humidity_2m", 0),
                    "wind": round(current.get("wind_speed_10m", 0) / 3.6, 1),
                    "description": description,
                    "icon": icon,
                    "forecast": forecast,
                }
    except Exception as e:
        logger.error(f"[NEWS] Weather error: {e}")
    return None


# ==================== АВИАБИЛЕТЫ (Aviasales) ====================

AVIASALES_TOKEN = "9d268d3a67128df02ab46acf3fa764fa"
ORIGIN_CITY = "MOW"
DESTINATION_CITY = "RGK"

AIRLINES = {
    "SU": "Аэрофлот", "S7": "S7 Airlines", "U6": "Уральские авиалинии",
    "DP": "Победа", "Y7": "NordStar", "5N": "Smartavia",
    "WZ": "Red Wings", "I8": "Ижавиа", "RT": "РусЛайн",
}


def _format_flight_date(date_str: str) -> str:
    months = ["", "янв", "фев", "мар", "апр", "май", "июн",
              "июл", "авг", "сен", "окт", "ноя", "дек"]
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return f"{dt.day} {months[dt.month]}"
    except Exception:
        return date_str[:10]


def _format_duration(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}ч {mins}м" if hours > 0 else f"{mins}м"


async def get_flights() -> Optional[Dict]:
    """Gets flight prices Moscow → Gorno-Altaysk via Aviasales API."""
    now = datetime.now()
    months = [now.strftime("%Y-%m"), (now + timedelta(days=32)).strftime("%Y-%m")]
    all_flights = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for month in months:
                url = (
                    f"https://api.travelpayouts.com/aviasales/v3/prices_for_dates?"
                    f"origin={ORIGIN_CITY}&destination={DESTINATION_CITY}"
                    f"&departure_at={month}&token={AVIASALES_TOKEN}"
                )
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data"):
                        all_flights.extend(data["data"])

        if not all_flights:
            return None

        all_flights.sort(key=lambda x: x.get("price", 999999))
        cheapest = []
        for f in all_flights[:5]:
            airline = AIRLINES.get(f.get("airline", ""), f.get("airline", ""))
            transfers = f.get("transfers", 0)
            cheapest.append({
                "price": f["price"],
                "date": _format_flight_date(f.get("departure_at", "")),
                "airline": airline,
                "transfers": transfers,
                "transfer_text": "прямой" if transfers == 0 else f"{transfers} пересадка",
                "duration": _format_duration(f.get("duration_to", 0)),
            })

        direct = [f for f in all_flights if f.get("transfers", 1) == 0]
        min_direct = None
        if direct:
            d = direct[0]
            min_direct = {
                "price": d["price"],
                "date": _format_flight_date(d.get("departure_at", "")),
                "airline": AIRLINES.get(d.get("airline", ""), d.get("airline", "")),
                "duration": _format_duration(d.get("duration_to", 0)),
            }

        return {
            "min_price": all_flights[0]["price"],
            "min_direct": min_direct,
            "cheapest": cheapest,
            "total_found": len(all_flights),
        }
    except Exception as e:
        logger.error(f"[NEWS] Flights error: {e}")
    return None


# ==================== RSS НОВОСТИ ====================

RSS_SOURCES = [
    {"name": "Ведомости", "url": "https://www.vedomosti.ru/rss/news", "category": "business"},
    {"name": "Коммерсант", "url": "https://www.kommersant.ru/rss/economics", "category": "business"},
    {"name": "РБК", "url": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss", "category": "business"},
]

INCLUDE_KEYWORDS = [
    "цб", "ставк", "инфляц", "ввп", "минфин", "минэконом",
    "нефть", "газ", "рубл", "доллар", "евро", "курс",
    "рынок", "биржа", "акци", "облигац", "инвест", "дивиденд",
    "экономик", "бизнес", "предпринимат", "малый бизнес",
    "недвижимость", "ипотек", "банк", "кредит", "вклад", "депозит",
    "строительств", "девелоп", "жильё", "жилье", "квартир",
    "туризм", "курорт", "отел", "гостиниц",
    "ритейл", "торговл", "импорт", "экспорт",
    "it", "tech", "цифров", "технолог",
]

EXCLUDE_KEYWORDS = [
    "путин", "трамп", "байден", "зеленск", "лукашенк",
    "кремль", "белый дом", "госдума", "депутат", "выбор", "голосован",
    "санкци", "политик", "политич", "оппозиц", "протест", "митинг",
    "убий", "убит", "погиб", "смерт", "умер", "жертв",
    "авари", "катастроф", "крушен", "взрыв", "пожар",
    "арест", "задержан", "суд", "приговор", "тюрьм", "колони",
    "теракт", "террор", "нападен", "стрельб",
    "война", "военн", "всу", "сво", "фронт", "удар", "ракет", "дрон", "бпла",
    "обстрел", "атак", "наступлен", "оборон",
    "украин", "киев", "сша", "америк", "вашингтон",
    "китай", "пекин", "европ", "брюссель", "нато",
    "иран", "израиль", "сектор газа", "ближний восток",
    "сирия", "африк", "латинск",
]


async def _fetch_rss(url: str, limit: int = 10) -> List[Dict]:
    items = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                for item in root.findall(".//item")[:limit]:
                    title_el = item.find("title")
                    link_el = item.find("link")
                    if title_el is not None and link_el is not None:
                        items.append({
                            "title": (title_el.text or "").strip(),
                            "link": (link_el.text or "").strip(),
                        })
    except Exception as e:
        logger.error(f"[NEWS] RSS error {url}: {e}")
    return items


def _filter_news(items: List[Dict]) -> List[Dict]:
    filtered = []
    for item in items:
        title_lower = item["title"].lower()
        if any(excl in title_lower for excl in EXCLUDE_KEYWORDS):
            continue
        if any(incl in title_lower for incl in INCLUDE_KEYWORDS):
            filtered.append(item)
    return filtered


async def get_news_digest() -> List[Dict]:
    """Gets filtered investment news from RSS sources."""
    all_news = []
    for source in RSS_SOURCES:
        items = await _fetch_rss(source["url"], limit=10)
        for item in items:
            item["source"] = source["name"]
        all_news.extend(items)

    return _filter_news(all_news)[:15]
