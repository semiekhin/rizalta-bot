#!/usr/bin/env python3
"""Парсер подборок с domoplaner.ru"""

import re
import requests
from typing import List, Dict, Optional

def parse_domoplaner_set(url: str) -> Optional[List[Dict]]:
    """Парсит подборку квартир с domoplaner.ru"""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"[DOMOPLANER] Ошибка загрузки: {e}")
        return None
    
    flats = []
    flat_blocks = html.split('<div class="flat-info-area">')[1:]
    
    for block in flat_blocks:
        try:
            values = re.findall(r'<div class="fia-col-value">([^<]+)</div>', block)
            if len(values) >= 8:
                flat = {
                    "project": values[0].strip(),
                    "building": values[1].strip(),
                    "floor": int(values[2].strip()),
                    "code": values[3].strip(),
                    "rooms": int(values[4].strip()),
                    "area": float(values[5].replace(",", ".").strip()),
                    "completion": values[6].strip(),
                    "price": int(values[7].replace(" ", "").strip()),
                }
                flats.append(flat)
        except Exception as e:
            continue
    
    print(f"[DOMOPLANER] Найдено {len(flats)} квартир")
    return flats if flats else None


def is_domoplaner_link(text: str) -> Optional[str]:
    """Проверяет, является ли текст ссылкой domoplaner."""
    pattern = r'(https?://domoplaner\.ru/export/set/[a-zA-Z0-9]+/?)'
    match = re.search(pattern, text)
    return match.group(1) if match else None


if __name__ == "__main__":
    url = "https://domoplaner.ru/export/set/gnrbuumhx0/"
    flats = parse_domoplaner_set(url)
    if flats:
        for f in flats[:5]:
            print(f"{f['code']}: {f['area']} м², {f['price']:,} ₽")
