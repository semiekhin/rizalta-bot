"""
Обработчик медиа-материалов: презентации, видео, документы.
"""

from services.telegram import send_message, send_message_inline, send_document

MEDIA_DIR = "/opt/bot/media"


async def handle_media_menu(chat_id: int):
    """Показывает меню медиа-материалов."""
    
    text = """🎬 <b>Медиа-материалы RIZALTA</b>

Здесь собраны презентации и видеоматериалы о проекте:"""

    inline_buttons = [
        [{"text": "📊 Презентация проекта", "callback_data": "media_presentation"}],
        [{"text": "🔙 Назад в меню", "callback_data": "back_to_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_send_presentation(chat_id: int):
    """Отправляет презентацию проекта."""
    filepath = f"{MEDIA_DIR}/presentation_rizalta.pdf"
    caption = "📊 Презентация RIZALTA RESORT BELOKURIKHA"
    
    await send_message(chat_id, "📤 Отправляю презентацию...")
    
    success = await send_document(chat_id, filepath, caption)
    if not success:
        await send_message(chat_id, "⚠️ Не удалось отправить презентацию. Попробуйте позже.")
    else:
        inline_buttons = [
            [
                {"text": "🎬 Ещё материалы", "callback_data": "media_menu"},
                {"text": "🔥 Записаться на показ", "callback_data": "online_show"}
            ]
        ]
        await send_message_inline(chat_id, "✅ Презентация отправлена!", inline_buttons)
