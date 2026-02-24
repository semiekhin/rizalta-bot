"""Обработчики расчёта МГП."""

import os
import shutil
from services.mgp_calculator import format_mgp_text, generate_mgp_pdf
from services.telegram import send_message_inline, send_document


async def handle_mgp_calc(chat_id: int, code: str, area: float, building: int = None):
    """Показывает таблицу МГП текстом + кнопка PDF."""
    text = format_mgp_text(code, area, building)

    buttons = [
        [{"text": "📥 Скачать PDF", "callback_data": f"mgp_pdf_{code}_{building or 0}_{int(area * 10)}"}],
        [{"text": "🔙 Назад", "callback_data": f"kp_lot_{code}_{building}"}],
    ]

    await send_message_inline(chat_id, text, buttons)


async def handle_mgp_pdf(chat_id: int, code: str, area: float, building: int = None):
    """Генерирует и отправляет PDF с МГП."""
    pdf_tmp = generate_mgp_pdf(code, area, building)

    bld = f"corp{building}_" if building else ""
    filename = f"MGP_{bld}{code}.pdf"
    pdf_path = os.path.join(os.path.dirname(pdf_tmp), filename)
    shutil.move(pdf_tmp, pdf_path)

    await send_document(chat_id, pdf_path, f"📊 МГП — {code}")

    os.unlink(pdf_path)
