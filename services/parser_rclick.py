#!/usr/bin/env python3
"""
Парсер данных с сайта застройщика ri.rclick.ru
"""

import re
import requests
import sqlite3
from typing import List, Dict, Any
from pathlib import Path

BASE_URL = "https://ri.rclick.ru"
CATALOG_ID = 340


def fetch_page(page: int) -> str:
    """Загружает одну страницу каталога."""
    url = f"{BASE_URL}/catalog/more/"
    data = {"id": CATALOG_ID, "page": page}
    
    resp = requests.post(url, data=data, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_cards(html: str) -> List[Dict[str, Any]]:
    """Парсит карточки квартир из HTML."""
    cards = []
    
    # Паттерн для карточки
    card_pattern = r'<a class="f_card" href="/flat/(\d+)/"[^>]*>.*?</a>'
    card_matches = re.findall(card_pattern, html, re.DOTALL)
    
    # Более детальный парсинг
    card_blocks = re.split(r'<a class="f_card"', html)[1:]
    
    for block in card_blocks:
        try:
            card = {}
            
            # ID квартиры
            id_match = re.search(r'href="/flat/(\d+)/"', block)
            card['id'] = int(id_match.group(1)) if id_match else None
            
            # Корпус и номер квартиры
            house_match = re.search(r'f_card-micro--house">([^<]+)<', block)
            if house_match:
                house_text = house_match.group(1).strip()
                # "Корпус 1, кв. №В227"
                corp_match = re.search(r'Корпус\s*(\d+)', house_text)
                card['building'] = int(corp_match.group(1)) if corp_match else None
                
                code_match = re.search(r'№\s*([А-Яа-яA-Za-z0-9]+)', house_text)
                card['code'] = code_match.group(1) if code_match else None
            
            # Комнаты и площадь
            name_match = re.search(r'f_card-name">([^<]+)<sup>2</sup>', block)
            if name_match:
                name_text = name_match.group(1).strip()
                # "1 комн., 22 м"
                rooms_match = re.search(r'(\d+)\s*комн', name_text)
                card['rooms'] = int(rooms_match.group(1)) if rooms_match else 1
                
                area_match = re.search(r'([\d.,]+)\s*м', name_text)
                card['area_m2'] = float(area_match.group(1).replace(',', '.')) if area_match else None
            
            # Цена
            price_match = re.search(r'f_card-price">([^<]+)<', block)
            if price_match:
                price_text = price_match.group(1).strip()
                price_clean = re.sub(r'[^\d]', '', price_text)
                card['price_rub'] = int(price_clean) if price_clean else None
            
            # Цена за м²
            price_m2_match = re.search(r'([\d\s]+)\s*руб\.\s*за\s*м', block)
            if price_m2_match:
                price_m2_text = price_m2_match.group(1).strip()
                price_m2_clean = re.sub(r'[^\d]', '', price_m2_text)
                card['price_per_m2_rub'] = int(price_m2_clean) if price_m2_clean else None
            
            # Этаж
            floor_match = re.search(r'>(\d+)\s*этаж<', block)
            card['floor'] = int(floor_match.group(1)) if floor_match else None
            
            # Срок сдачи
            completion_match = re.search(r'date_finish.*?f_card-micro">([^<]+)<', block, re.DOTALL)
            card['completion'] = completion_match.group(1).strip() if completion_match else None
            
            # URL планировки
            img_match = re.search(r'f_card-wrap-img">\s*<img src="([^"]+)"', block)
            card['layout_url'] = img_match.group(1) if img_match else None
            
            # URL страницы
            card['page_url'] = f"{BASE_URL}/flat/{card['id']}/" if card['id'] else None
            
            if card.get('id') and card.get('price_rub'):
                cards.append(card)
                
        except Exception as e:
            print(f"[PARSER] Ошибка парсинга карточки: {e}")
            continue
    
    return cards


def fetch_all_units() -> List[Dict[str, Any]]:
    """Загружает все квартиры со всех страниц."""
    all_units = []
    page = 1
    
    while True:
        print(f"[PARSER] Загружаем страницу {page}...")
        html = fetch_page(page)
        cards = parse_cards(html)
        
        if not cards:
            break
        
        all_units.extend(cards)
        print(f"[PARSER] Найдено {len(cards)} квартир, всего {len(all_units)}")
        
        # Проверяем есть ли ещё страницы
        if len(cards) < 8:
            break
        
        page += 1
        
        # Защита от бесконечного цикла
        if page > 100:
            break
    
    return all_units


def update_database(units: List[Dict[str, Any]], db_path: str):
    """Обновляет базу данных."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаём таблицу если нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY,
            code TEXT,
            project TEXT DEFAULT 'Rizalta',
            building INTEGER,
            floor INTEGER,
            rooms INTEGER,
            area_m2 REAL,
            price_rub INTEGER,
            price_per_m2_rub INTEGER,
            completion TEXT,
            layout_url TEXT,
            page_url TEXT,
            status TEXT DEFAULT 'available',
            block_section INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Очищаем старые данные
    cursor.execute('DELETE FROM units')
    
    # Вставляем новые
    for unit in units:
        # block_section: 1 = Корпус 2 (А), 2 = Корпус 1 (В) — по логике бота
        block_section = 2 if unit.get('building') == 1 else 1
        
        cursor.execute('''
            INSERT INTO units (id, code, building, floor, rooms, area_m2, 
                              price_rub, price_per_m2_rub, completion, 
                              layout_url, page_url, block_section)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            unit.get('id'),
            unit.get('code'),
            unit.get('building'),
            unit.get('floor'),
            unit.get('rooms'),
            unit.get('area_m2'),
            unit.get('price_rub'),
            unit.get('price_per_m2_rub'),
            unit.get('completion'),
            unit.get('layout_url'),
            unit.get('page_url'),
            block_section
        ))
    
    conn.commit()
    conn.close()
    print(f"[PARSER] База обновлена: {len(units)} записей")


def sync_from_rclick(db_path: str = None):
    """Главная функция синхронизации."""
    if db_path is None:
        db_path = Path(__file__).parent.parent / "properties.db"
    
    print("[PARSER] Начинаем синхронизацию с ri.rclick.ru...")
    
    units = fetch_all_units()
    print(f"[PARSER] Загружено {len(units)} квартир")
    
    if units:
        update_database(units, str(db_path))
        print("[PARSER] ✅ Синхронизация завершена!")
    else:
        print("[PARSER] ❌ Не удалось загрузить данные")
    
    return units


if __name__ == "__main__":
    sync_from_rclick()
