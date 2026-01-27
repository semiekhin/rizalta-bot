"""
Модуль новостей и инвест-дайджеста.
Курсы валют, погода, авиабилеты, новости региона и рынка.
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import re

from services.telegram import send_message, send_message_inline


# ==================== КУРСЫ ВАЛЮТ (ЦБ РФ) ====================

async def get_currency_rates() -> Dict[str, float]:
    """Получает курсы валют с ЦБ РФ."""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    return {
                        "USD": data["Valute"]["USD"]["Value"],
                        "USD_prev": data["Valute"]["USD"]["Previous"],
                        "EUR": data["Valute"]["EUR"]["Value"],
                        "EUR_prev": data["Valute"]["EUR"]["Previous"],
                        "CNY": data["Valute"]["CNY"]["Value"],
                        "CNY_prev": data["Valute"]["CNY"]["Previous"],
                        "date": data["Date"][:10]
                    }
    except Exception as e:
        print(f"[NEWS] Ошибка получения курсов: {e}")
    
    return {}


def format_currency_change(current: float, previous: float) -> str:
    """Форматирует изменение курса."""
    diff = current - previous
    if diff > 0:
        return f"↑{diff:.2f}"
    elif diff < 0:
        return f"↓{abs(diff):.2f}"
    else:
        return "—"


async def handle_currency_rates(chat_id: int):
    """Показывает курсы валют."""
    rates = await get_currency_rates()
    
    if not rates:
        await send_message(chat_id, "❌ Не удалось получить курсы валют. Попробуйте позже.")
        return
    
    usd_change = format_currency_change(rates["USD"], rates["USD_prev"])
    eur_change = format_currency_change(rates["EUR"], rates["EUR_prev"])
    cny_change = format_currency_change(rates["CNY"], rates["CNY_prev"])
    
    text = f"""💵 <b>Курсы валют ЦБ РФ</b>
<i>на {rates['date']}</i>

🇺🇸 Доллар США: <b>{rates['USD']:.2f} ₽</b> ({usd_change})
🇪🇺 Евро: <b>{rates['EUR']:.2f} ₽</b> ({eur_change})
🇨🇳 Юань: <b>{rates['CNY']:.2f} ₽</b> ({cny_change})

💡 <i>Недвижимость — надёжная защита от валютных колебаний</i>"""
    
    inline_buttons = [
        [{"text": "🔄 Обновить", "callback_data": "news_currency"}],
        [{"text": "🔙 Назад", "callback_data": "news_menu"}]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons, disable_web_page_preview=True)


# ==================== ПОГОДА (Open-Meteo, бесплатно) ====================

BELOKURIKHA_LAT = 51.996
BELOKURIKHA_LON = 84.993

# WMO Weather codes
WEATHER_CODES = {
    0: ("☀️", "ясно"),
    1: ("🌤", "малооблачно"),
    2: ("⛅", "переменная облачность"),
    3: ("☁️", "облачно"),
    45: ("🌫", "туман"),
    48: ("🌫", "изморозь"),
    51: ("🌧", "морось"),
    53: ("🌧", "морось"),
    55: ("🌧", "морось"),
    61: ("🌧", "дождь"),
    63: ("🌧", "дождь"),
    65: ("🌧", "сильный дождь"),
    71: ("❄️", "снег"),
    73: ("❄️", "снег"),
    75: ("❄️", "сильный снег"),
    77: ("❄️", "снежная крупа"),
    80: ("🌦", "ливень"),
    81: ("🌦", "ливень"),
    82: ("🌦", "сильный ливень"),
    85: ("🌨", "снегопад"),
    86: ("🌨", "сильный снегопад"),
    95: ("⛈", "гроза"),
    96: ("⛈", "гроза с градом"),
    99: ("⛈", "гроза с градом"),
}


async def get_weather() -> Optional[Dict]:
    """Получает погоду и прогноз в Белокурихе через Open-Meteo API."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={BELOKURIKHA_LAT}&longitude={BELOKURIKHA_LON}&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m&hourly=temperature_2m,weather_code&timezone=Asia/Barnaul&forecast_hours=4"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    current = data.get("current", {})
                    hourly = data.get("hourly", {})
                    
                    weather_code = current.get("weather_code", 0)
                    icon, description = WEATHER_CODES.get(weather_code, ("🌤", "переменно"))
                    
                    # Прогноз на ближайшие часы
                    forecast = []
                    times = hourly.get("time", [])
                    temps = hourly.get("temperature_2m", [])
                    codes = hourly.get("weather_code", [])
                    
                    for i in range(1, min(4, len(times))):  # +1, +2, +3 часа
                        hour = times[i].split("T")[1][:5] if "T" in times[i] else times[i]
                        temp = temps[i] if i < len(temps) else 0
                        code = codes[i] if i < len(codes) else 0
                        fc_icon, _ = WEATHER_CODES.get(code, ("🌤", ""))
                        forecast.append({"hour": hour, "temp": temp, "icon": fc_icon})
                    
                    return {
                        "temp": current.get("temperature_2m", 0),
                        "humidity": current.get("relative_humidity_2m", 0),
                        "wind": round(current.get("wind_speed_10m", 0) / 3.6, 1),
                        "description": description,
                        "icon": icon,
                        "forecast": forecast
                    }
    except Exception as e:
        print(f"[NEWS] Ошибка получения погоды: {e}")
    
    return None


async def handle_weather(chat_id: int):
    """Показывает погоду в Белокурихе с прогнозом."""
    weather = await get_weather()
    
    if not weather:
        text = """☀️ <b>Погода в Белокурихе</b>

⚙️ <i>Не удалось получить данные. Попробуйте позже.</i>

🏔 Белокуриха — 260+ солнечных дней в году!"""
    else:
        # Формируем прогноз
        forecast_text = ""
        if weather.get("forecast"):
            forecast_text = "\n\n⏱ <b>Прогноз:</b>\n"
            for fc in weather["forecast"]:
                forecast_text += f"{fc['icon']} {fc['hour']} — {fc['temp']:.0f}°C\n"
        
        text = f"""{weather['icon']} <b>Погода в Белокурихе</b>

🌡 Сейчас: <b>{weather['temp']:.0f}°C</b>, {weather['description']}
💨 Ветер: {weather['wind']} м/с
💧 Влажность: {weather['humidity']}%{forecast_text}
🏔 <i>Белокуриха — идеальный климат для отдыха</i>"""
    
    inline_buttons = [
        [{"text": "🔄 Обновить", "callback_data": "news_weather"}],
        [{"text": "🔙 Назад", "callback_data": "news_menu"}]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons, disable_web_page_preview=True)


# ==================== АВИАБИЛЕТЫ (Aviasales API) ====================

AVIASALES_TOKEN = "9d268d3a67128df02ab46acf3fa764fa"

# Коды аэропортов
ORIGIN_CITY = "MOW"  # Москва (все аэропорты)
DESTINATION_CITY = "RGK"  # Горно-Алтайск

# Названия авиакомпаний
AIRLINES = {
    "SU": "Аэрофлот",
    "S7": "S7 Airlines",
    "U6": "Уральские авиалинии",
    "DP": "Победа",
    "Y7": "NordStar",
    "5N": "Smartavia",
    "WZ": "Red Wings",
    "I8": "Ижавиа",
    "RT": "РусЛайн",
}


async def get_flights() -> Optional[Dict]:
    """Получает цены на авиабилеты Москва - Горно-Алтайск."""
    # Ищем на текущий и следующий месяц
    now = datetime.now()
    months = [
        now.strftime("%Y-%m"),
        (now + timedelta(days=32)).strftime("%Y-%m")
    ]
    
    all_flights = []
    
    try:
        async with aiohttp.ClientSession() as session:
            for month in months:
                url = f"https://api.travelpayouts.com/aviasales/v3/prices_for_dates?origin={ORIGIN_CITY}&destination={DESTINATION_CITY}&departure_at={month}&token={AVIASALES_TOKEN}"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success") and data.get("data"):
                            all_flights.extend(data["data"])
        
        if not all_flights:
            return None
        
        # Сортируем по цене
        all_flights.sort(key=lambda x: x.get("price", 999999))
        
        # Берём топ-3 самых дешёвых
        cheapest = all_flights[:3]
        
        # Находим минимальную цену и прямой рейс
        min_price = all_flights[0]["price"]
        direct_flights = [f for f in all_flights if f.get("transfers", 1) == 0]
        min_direct = direct_flights[0] if direct_flights else None
        
        return {
            "min_price": min_price,
            "min_direct": min_direct,
            "cheapest": cheapest,
            "total_found": len(all_flights)
        }
        
    except Exception as e:
        print(f"[NEWS] Ошибка получения авиабилетов: {e}")
    
    return None


def format_flight_date(date_str: str) -> str:
    """Форматирует дату вылета."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        months = ["", "янв", "фев", "мар", "апр", "май", "июн", 
                  "июл", "авг", "сен", "окт", "ноя", "дек"]
        return f"{dt.day} {months[dt.month]}"
    except:
        return date_str[:10]


def format_duration(minutes: int) -> str:
    """Форматирует длительность полёта."""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}ч {mins}м"
    return f"{mins}м"


async def handle_flights(chat_id: int):
    """Показывает цены на авиабилеты."""
    flights = await get_flights()
    
    if not flights:
        text = """✈️ <b>Авиабилеты Москва → Горно-Алтайск</b>

⚙️ <i>Не удалось получить данные. Попробуйте позже.</i>

🔗 <a href="https://www.aviasales.ru/search/MOW0101RGK1">Искать на Aviasales</a>"""
    else:
        text = f"""✈️ <b>Авиабилеты Москва → Горно-Алтайск</b>

💰 Минимальная цена: <b>{flights['min_price']:,} ₽</b>
"""
        
        # Добавляем прямой рейс если есть
        if flights.get("min_direct"):
            direct = flights["min_direct"]
            airline = AIRLINES.get(direct.get("airline", ""), direct.get("airline", ""))
            date = format_flight_date(direct.get("departure_at", ""))
            duration = format_duration(direct.get("duration_to", 0))
            text += f"🎯 Прямой от <b>{direct['price']:,} ₽</b> ({airline}, {date}, {duration})\n"
        
        text += "\n📋 <b>Лучшие цены:</b>\n"
        
        for i, flight in enumerate(flights["cheapest"], 1):
            airline = AIRLINES.get(flight.get("airline", ""), flight.get("airline", ""))
            date = format_flight_date(flight.get("departure_at", ""))
            transfers = flight.get("transfers", 0)
            transfer_text = "прямой" if transfers == 0 else f"{transfers} пересадка"
            
            text += f"{i}. <b>{flight['price']:,} ₽</b> — {date}, {airline}, {transfer_text}\n"
        
        text += f"""
📊 Найдено рейсов: {flights['total_found']}

🔗 <a href="https://www.aviasales.ru/search/MOW0101RGK1">Купить билет на Aviasales</a>

💡 <i>Прилетайте на осмотр объекта — мы организуем трансфер!</i>"""
    
    inline_buttons = [
        [{"text": "🔄 Обновить", "callback_data": "news_flights"}],
        [{"text": "🔙 Назад", "callback_data": "news_menu"}]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons, disable_web_page_preview=True)


# ==================== НОВОСТИ (RSS) ====================

# RSS источники (только российская экономика)
RSS_SOURCES = [
    {
        "name": "Ведомости",
        "url": "https://www.vedomosti.ru/rss/news",
        "category": "business"
    },
    {
        "name": "Коммерсант Экономика",
        "url": "https://www.kommersant.ru/rss/economics",
        "category": "business"
    },
    {
        "name": "РБК Экономика",
        "url": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss",
        "category": "business"
    },
]


async def fetch_rss(url: str, limit: int = 5) -> List[Dict]:
    """Парсит RSS-ленту."""
    items = []
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    
                    # Ищем items в разных форматах RSS
                    for item in root.findall(".//item")[:limit]:
                        title = item.find("title")
                        link = item.find("link")
                        pub_date = item.find("pubDate")
                        
                        if title is not None and link is not None:
                            items.append({
                                "title": title.text.strip() if title.text else "",
                                "link": link.text.strip() if link.text else "",
                                "date": pub_date.text if pub_date is not None else ""
                            })
    except Exception as e:
        print(f"[NEWS] Ошибка парсинга RSS {url}: {e}")
    
    return items


def filter_investment_news(items: List[Dict]) -> List[Dict]:
    """Фильтрует новости: только российская экономика, без политики и негатива."""
    
    # Включающие ключевые слова (российская экономика)
    include_keywords = [
        "цб", "ставк", "инфляц", "ввп", "минфин", "минэконом",
        "нефть", "газ", "рубл", "доллар", "евро", "курс",
        "рынок", "биржа", "акци", "облигац", "инвест", "дивиденд",
        "экономик", "бизнес", "предпринимат", "малый бизнес",
        "недвижимость", "ипотек", "банк", "кредит", "вклад", "депозит",
        "строительств", "девелоп", "жильё", "жилье", "квартир",
        "туризм", "курорт", "отел", "гостиниц",
        "ритейл", "торговл", "импорт", "экспорт",
        "it", "tech", "цифров", "технолог"
    ]
    
    # Исключающие ключевые слова (политика, негатив, другие страны)
    exclude_keywords = [
        # Политика
        "путин", "трамп", "байден", "зеленск", "лукашенк",
        "кремль", "белый дом", "госдума", "депутат", "выбор", "голосован",
        "санкци", "политик", "политич", "оппозиц", "протест", "митинг",
        # Негатив и криминал
        "убий", "убит", "погиб", "смерт", "умер", "жертв", 
        "авари", "катастроф", "крушен", "взрыв", "пожар",
        "арест", "задержан", "суд", "приговор", "тюрьм", "колони",
        "теракт", "террор", "нападен", "стрельб",
        # Война и конфликты
        "война", "военн", "всу", "сво", "фронт", "удар", "ракет", "дрон", "бпла",
        "обстрел", "атак", "наступлен", "оборон",
        # Другие страны (не экономический контекст)
        "украин", "киев", "сша", "америк", "вашингтон",
        "китай", "пекин", "европ", "брюссель", "нато",
        "иран", "израиль", "сектор газа", "ближний восток",
        "сирия", "африк", "латинск"
    ]
    
    filtered = []
    for item in items:
        title_lower = item["title"].lower()
        
        # Сначала проверяем исключения
        if any(excl in title_lower for excl in exclude_keywords):
            continue
            
        # Затем проверяем включения
        if any(incl in title_lower for incl in include_keywords):
            filtered.append(item)
    
    return filtered


async def handle_news_digest(chat_id: int):
    """Показывает инвест-дайджест."""
    
    # Получаем курсы валют для шапки
    rates = await get_currency_rates()
    
    # Получаем авиабилеты
    flights = await get_flights()
    
    # Формируем шапку
    header = f"""📊 <b>ИНВЕСТ-ДАЙДЖЕСТ</b>
<i>{datetime.now().strftime('%d.%m.%Y %H:%M')}</i>

"""
    
    if rates:
        header += f"💵 USD: {rates['USD']:.2f} ₽ | EUR: {rates['EUR']:.2f} ₽\n"
    
    if flights:
        header += f"✈️ Москва→Алтай от {flights['min_price']:,} ₽\n"
    
    header += "\n"
    
    # Получаем новости
    all_news = []
    for source in RSS_SOURCES:
        items = await fetch_rss(source["url"], limit=10)
        for item in items:
            item["source"] = source["name"]
        all_news.extend(items)
    
    # Фильтруем релевантные
    relevant_news = filter_investment_news(all_news)[:15]
    
    if relevant_news:
        news_text = "🔥 <b>Главное сегодня:</b>\n\n"
        emojis = ["📌", "📍", "🔹", "🔸", "▪️", "📎", "🔺", "💠", "🔻", "✦", "◾", "📊", "💡", "⚡", "🌐"]
        for i, item in enumerate(relevant_news):
            emoji = emojis[i % len(emojis)]
            title = item["title"]
            link = item.get("link", "")
            source = item.get("source", "")
            
            news_text += f"{emoji} {title}\n"
            if link:
                news_text += f"    ↳ <a href=\"{link}\">{source}</a>\n\n"
            else:
                news_text += f"    ↳ <i>{source}</i>\n\n"
    else:
        news_text = "📰 <i>Новости загружаются...</i>\n"
    
    footer = """
💡 <i>Следите за рынком — инвестируйте в недвижимость вовремя!</i>"""
    
    text = header + news_text + footer
    
    inline_buttons = [
        [{"text": "🔄 Обновить", "callback_data": "news_digest"}],
        [{"text": "🔙 Назад", "callback_data": "news_menu"}]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons, disable_web_page_preview=True)


# ==================== ГЛАВНОЕ МЕНЮ НОВОСТЕЙ ====================

async def handle_news_menu(chat_id: int):
    """Показывает меню новостей."""
    text = """📰 <b>Инвест-дайджест</b>

Актуальная информация для инвестора:"""
    
    inline_buttons = [
        [{"text": "💵 Курсы валют", "callback_data": "news_currency"}],
        [{"text": "☀️ Погода в Белокурихе", "callback_data": "news_weather"}],
        [{"text": "✈️ Авиабилеты Москва-Алтай", "callback_data": "news_flights"}],
        [{"text": "📊 Полный дайджест", "callback_data": "news_digest"}],
        [{"text": "🔙 Главное меню", "callback_data": "main_menu"}]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons, disable_web_page_preview=True)
