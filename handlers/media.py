"""
Обработчик медиа-материалов: презентации, видео, документы.
"""

from services.telegram import send_message, send_message_inline, send_document, send_video

MEDIA_DIR = "/opt/bot/media"


async def handle_media_menu(chat_id: int):
    """Показывает меню медиа-материалов."""
    
    text = """🎬 <b>Медиа-материалы RIZALTA</b>

Здесь собраны презентации и видеоматериалы о проекте:"""

    inline_buttons = [
        [{"text": "📊 Презентация проекта", "callback_data": "media_presentation"}],
        [{"text": "🎬 Видео про Алтай", "callback_data": "media_video"}],
        [{"text": "🔙 Назад в меню", "callback_data": "back_to_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_send_presentation(chat_id: int):
    """Показывает меню выбора презентации."""
    text = "📊 <b>Презентации проекта</b>\n\nВыберите документ:"

    
    inline_buttons = [
        [{"text": "🏗 О застройщике", "callback_data": "pres_developer"}],
        [{"text": "🏨 ZONT Hotel Group", "callback_data": "pres_zont"}],
        [{"text": "🏛 Архитектор Пергаев", "callback_data": "pres_pergaev"}],
        [{"text": "📊 Аналитика от CoreXP", "callback_data": "pres_corexp"}],
        [{"text": "📕 Презентация RIZALTA", "callback_data": "pres_rizalta_ru"}],
        [{"text": "📗 Презентация RIZALTA (ENG)", "callback_data": "pres_rizalta_eng"}],
        [{"text": "🔙 Назад", "callback_data": "media_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


PRESENTATIONS_DIR = "/opt/bot/presentations"

PRESENTATIONS = {
    "pres_rizalta_ru": ("presentation_ru.pdf", "📕 Презентация RIZALTA RESORT BELOKURIKHA"),
    "pres_rizalta_eng": ("presentation_eng.pdf", "📗 Презентация RIZALTA RESORT BELOKURIKHA (ENG)"),
    "pres_developer": ("about_developer.pdf", "🏗 О застройщике"),
    "pres_corexp": ("analytics_corexp.pdf", "📊 Аналитика проекта RIZALTA от CoreXP"),
    "pres_pergaev": ("architect_pergaev.pdf", "🏛 PERGAEV BUREAU — Архитектор проекта"),
    "pres_zont": ("zont_hotel.pdf", "🏨 ZONT Hotel Group — Управляющая компания"),
}

VIDEOS_DIR = "/opt/bot/videos"

VIDEOS = {
    "video_nerealno": ("nerealno.mp4", "🎬 Нереально"),
    "video_vesti_kurort": ("vesti_kurort.mp4", "📺 Вести Курорт"),
    "video_bolshoy_altai": ("bolshoy_altai.mp4", "🏔 Большой Алтай"),
    "video_pravilo_30x30": ("pravilo_30x30.mp4", "📐 Правило 30 х 30"),
    "video_vesti_turpotok": ("vesti_turpotok.mp4", "📺 Вести тур поток"),
    "video_sluhi_rizalta": ("sluhi_rizalta.mp4", "🗣 Слухи о RIZALTA"),
    "video_mihalkova": ("mihalkova_altai.mov", "🌟 Михалкова в Алтае"),
    "video_chto_belokuriha": ("chto_takoe_belokuriha.mp4", "❓ Что такое Белокуриха"),
    "video_chem_zanyatsya": ("chem_zanyatsya_belokuriha.mp4", "🎯 Чем заняться в Белокурихе"),
}


async def handle_video_menu(chat_id: int):
    """Показывает меню выбора видео."""
    text = "🎬 <b>Видео про Алтай</b>\n\nВыберите видео:"
    
    inline_buttons = [
        [{"text": "🎬 Нереально", "callback_data": "video_nerealno"}],
        [{"text": "📺 Вести Курорт", "callback_data": "video_vesti_kurort"}],
        [{"text": "🏔 Большой Алтай", "callback_data": "video_bolshoy_altai"}],
        [{"text": "📐 Правило 30 х 30", "callback_data": "video_pravilo_30x30"}],
        [{"text": "📺 Вести тур поток", "callback_data": "video_vesti_turpotok"}],
        [{"text": "🗣 Слухи о RIZALTA", "callback_data": "video_sluhi_rizalta"}],
        [{"text": "🌟 Михалкова в Алтае", "callback_data": "video_mihalkova"}],
        [{"text": "❓ Что такое Белокуриха", "callback_data": "video_chto_belokuriha"}],
        [{"text": "🎯 Чем заняться в Белокурихе", "callback_data": "video_chem_zanyatsya"}],
        [{"text": "🔙 Назад", "callback_data": "media_menu"}],
    ]
    
    await send_message_inline(chat_id, text, inline_buttons)


async def handle_send_video(chat_id: int, video_key: str):
    """Отправляет выбранное видео."""
    if video_key not in VIDEOS:
        await send_message(chat_id, "⚠️ Видео не найдено.")
        return
    
    filename, caption = VIDEOS[video_key]
    filepath = f"{VIDEOS_DIR}/{filename}"
    
    await send_message(chat_id, "📤 Отправляю видео...")
    
    success = await send_video(chat_id, filepath, caption)
    if not success:
        await send_message(chat_id, "⚠️ Не удалось отправить видео. Попробуйте позже.")
    else:
        inline_buttons = [
            [{"text": "🎬 Другие видео", "callback_data": "media_video"}],
            [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        ]
        await send_message_inline(chat_id, "✅ Видео отправлено!", inline_buttons)



async def handle_send_presentation_file(chat_id: int, pres_key: str):
    """Отправляет выбранную презентацию."""
    if pres_key not in PRESENTATIONS:
        await send_message(chat_id, "⚠️ Презентация не найдена.")
        return
    
    filename, caption = PRESENTATIONS[pres_key]
    filepath = f"{PRESENTATIONS_DIR}/{filename}"
    
    await send_message(chat_id, "📤 Отправляю документ...")
    
    success = await send_document(chat_id, filepath, caption)
    if not success:
        await send_message(chat_id, "⚠️ Не удалось отправить документ. Попробуйте позже.")
    else:
        inline_buttons = [
            [{"text": "📚 Другие презентации", "callback_data": "media_presentation"}],
            [{"text": "🔥 Записаться на показ", "callback_data": "online_show"}],
        ]
        await send_message_inline(chat_id, "✅ Документ отправлен!", inline_buttons)
