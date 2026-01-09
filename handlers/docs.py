"""
Обработчик документов — скачивание договоров ДДУ и аренды.
"""

from services.telegram import send_message, send_message_inline, send_document

DOCS_DIR = "/opt/bot/docs"


async def handle_documents_menu(chat_id: int):
    """Показывает меню документов."""
    
    text = """📄 <b>Документы проекта RIZALTA</b>

Здесь вы можете скачать ключевые договоры:

📋 <b>Договор ДДУ</b> — договор долевого участия с застройщиком
📋 <b>Договор аренды</b> — договор с управляющей компанией

Выберите документ:"""

    inline_buttons = [
        [{"text": "📋 Договор ДДУ", "callback_data": "doc_ddu"}],
        [{"text": "📋 Договор аренды с отельным оператором", "callback_data": "doc_arenda"}],
        [{"text": "📚 Скачать оба", "callback_data": "doc_all"}]
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_send_ddu(chat_id: int):
    """Отправляет договор ДДУ."""
    filepath = f"{DOCS_DIR}/ddu.pdf"
    caption = "📋 Договор долевого участия (ДДУ) — проект RIZALTA Resort Belokurikha"
    
    success = await send_document(chat_id, filepath, caption)
    if not success:
        await send_message(chat_id, "⚠️ Не удалось отправить документ. Попробуйте позже.")


async def handle_send_arenda(chat_id: int):
    """Отправляет договор аренды."""
    filepath = f"{DOCS_DIR}/arenda.pdf"
    caption = "📋 Договор аренды с отельным оператором ЗОНТ ХОТЕЛ ГРУПП — проект RIZALTA"
    
    success = await send_document(chat_id, filepath, caption)
    if not success:
        await send_message(chat_id, "⚠️ Не удалось отправить документ. Попробуйте позже.")


async def handle_send_all_docs(chat_id: int):
    """Отправляет оба договора."""
    await handle_send_ddu(chat_id)
    await handle_send_arenda(chat_id)
