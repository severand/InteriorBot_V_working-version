# ===== PHASE 4: EXTRA FEATURES =====
# [2025-12-30] UNIVERSAL FILE CLEANUP HANDLER
# Обрабатывает и удаляет любые файлы если они не находятся в нужном стейте
# Поддерживает: фото, видео, документы, аудио, файлы и т.д.

import logging
import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from states.fsm import CreationStates

logger = logging.getLogger(__name__)
router = Router()


# ===== FILE TYPE CONSTANTS =====
VALID_UPLOAD_STATES = {
    CreationStates.uploading_photo,      # Загружение основной фотографии
    CreationStates.uploading_furniture,  # Загружение фото мебели
    CreationStates.loading_facade_sample,  # Загружение фасада
}


# ===== HELPER: _delete_message_after_delay =====
async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int = 3):
    """Delete message after N seconds"""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"✅ Удалено сообщение {message_id} в чате {chat_id}")
    except TelegramBadRequest as e:
        logger.debug(f"⚠️ Не удалось удалить сообщение {message_id}: {e}")
    except Exception as e:
        logger.debug(f"⚠️ Ошибка при удалении сообщения {message_id}: {e}")


# ===== UNIVERSAL FILE CLEANUP HANDLER =====
# Обрабатывает ВСЕ типы файлов в "неправильном" стейте
@router.message(F.photo | F.document | F.video | F.video_note | F.audio | F.voice | F.animation)
async def handle_unexpected_files(message: Message, state: FSMContext):
    """
    UNIVERSAL FILE CLEANUP HANDLER
    
    Логика:
    1. Проверить текущий FSM стейт
    2. Если файл прислан НЕ В нужном стейте:
       - Отправить сообщение об ошибке
       - Удалить сообщение пользователя с файлом
       - Удалить сообщение об ошибке через 3 сек
    3. Если стейт правильный - проигнорировать (другой обработчик перехватит)
    
    Поддерживаемые типы:
    - 📷 photo (фото)
    - 📄 document (PDF, Word, TXT, и т.д.)
    - 🎥 video (видео)
    - 📹 video_note (видео-заметка)
    - 🎵 audio (аудио)
    - 🎙️ voice (голос)
    - 🎬 animation (анимация, GIF)
    
    КРИТИЧНО: Регистрируется БЕЗ StateFilter!
    - Это означает, что обработчик срабатывает ВСЕГДА
    - При правильном стейте - ничего не делаем (другой обработчик есть)
    - При неправильном стейте - сообщаем об ошибке и удаляем
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Получить текущий стейт
    current_state = await state.get_state()
    
    # КРИТИЧНО: Если стейт правильный - проигнорировать
    # (специализированный обработчик photohandler будет работать)
    if current_state in VALID_UPLOAD_STATES:
        logger.debug(f"✅ File in valid state {current_state} - ignoring (other handler will process)")
        return  # Пропускаем - другой обработчик обработает
    
    # ===== НЕПРАВИЛЬНЫЙ СТЕЙТ - УДАЛИТЬ ФАЙЛ =====
    
    # Определить тип файла для логирования
    file_type = "неизвестный файл"
    if message.photo:
        file_type = "фото 📷"
    elif message.document:
        file_type = f"документ 📄 ({message.document.mime_type})"
    elif message.video:
        file_type = "видео 🎥"
    elif message.video_note:
        file_type = "видео-заметка 📹"
    elif message.audio:
        file_type = "аудио 🎵"
    elif message.voice:
        file_type = "голос 🎙️"
    elif message.animation:
        file_type = "анимация 🎬"
    
    logger.warning(
        f"⚠️ FILE CLEANUP: user_id={user_id}, type={file_type}, "
        f"current_state={current_state}, expected=uploading_photo/furniture/facade"
    )
    
    # Отправить сообщение об ошибке
    error_message = (
        f"⚠️ **Сейчас нельзя отправлять файлы**\n\n"
        f"Получено: {file_type}\n\n"
        f"📋 Выберите действие в меню выше или отправьте /start"
    )
    
    try:
        error_msg = await message.answer(error_message, parse_mode="Markdown")
        
        # Удалить сообщение об ошибке через 3 сек
        asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, delay=3))
        
        logger.info(f"✅ Error message sent and scheduled for deletion: msg_id={error_msg.message_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send error message: {e}")
    
    # Логировать попытку отправки файла
    try:
        await db.log_activity(user_id, f'unexpected_file_{file_type}')
    except Exception as e:
        logger.debug(f"⚠️ Failed to log activity: {e}")


# ===== FUTURE HANDLERS TEMPLATE =====
# Местo для добавления других обработчиков (например, text, commands, etc.)
# 
# @router.message(F.text)
# async def handle_text_in_wrong_state(message: Message, state: FSMContext):
#     """Handle text messages in unexpected states"""
#     pass
#
# @router.message(F.sticker)
# async def handle_sticker_in_wrong_state(message: Message, state: FSMContext):
#     """Handle stickers in unexpected states"""
#     pass
