"""Обработчик ссылок domoplaner.ru"""

import re
from services.domoplaner_parser import parse_domoplaner_set, format_flat_button

# Хранилище подборок (chat_id -> flats)
domoplaner_cache = {}


async def handle_domoplaner_link(chat_id: int, url: str, send_message, send_buttons):
    """Обрабатывает ссылку на подборку domoplaner."""
    
    await send_message(chat_id, "⏳ Загружаю подборку...")
    
    flats = parse_domoplaner_set(url)
    
    if not flats:
        await send_message(chat_id, "❌ Не удалось загрузить подборку. Проверьте ссылку.")
        return
    
    # Сохраняем в кеш
    domoplaner_cache[chat_id] = flats
    
    # Формируем кнопки
    buttons = []
    for flat in flats:
        btn_text = format_flat_button(flat)
        callback = f"domo_select_{flat['code']}"
        buttons.append([{"text": btn_text, "callback_data": callback}])
    
    buttons.append([{"text": "🔙 Отмена", "callback_data": "main_menu"}])
    
    text = f"📋 **Подборка от менеджера**\n\nНайдено {len(flats)} квартир.\nВыберите для генерации КП:"
    
    await send_buttons(chat_id, text, buttons)


async def handle_domoplaner_select(chat_id: int, lot_code: str, send_message, send_document):
    """Генерирует КП для выбранной квартиры из подборки."""
    
    flats = domoplaner_cache.get(chat_id, [])
    
    # Ищем квартиру
    flat = None
    for f in flats:
        if f["code"] == lot_code:
            flat = f
            break
    
    if not flat:
        await send_message(chat_id, "❌ Квартира не найдена. Попробуйте ещё раз.")
        return
    
    await send_message(chat_id, f"⏳ Генерирую КП для {lot_code}...")
    
    # Генерируем PDF
    from services.kp_pdf_generator import generate_kp_pdf
    
    pdf_path = generate_kp_pdf(code=lot_code, include_24m=True)
    
    if pdf_path:
        await send_document(chat_id, pdf_path, f"КП_{lot_code}.pdf")
    else:
        await send_message(chat_id, f"❌ Лот {lot_code} не найден в базе. Возможно, он ещё не добавлен.")


def is_domoplaner_link(text: str) -> str:
    """Проверяет, является ли текст ссылкой domoplaner и возвращает URL."""
    pattern = r'(https?://domoplaner\.ru/export/set/[a-zA-Z0-9]+/?)'
    match = re.search(pattern, text)
    return match.group(1) if match else None
