# ===== PHASE 4: EXTRA FEATURES =====
# [2025-12-30] UNIVERSAL FILE CLEANUP HANDLER
# Обрабатывает и удаляет любые файлы если они не находятся в нужном стейте
# Поддерживает: фото, видео, документы, аудио, файлы и т.д.
# [2025-12-30 22:04] УЛУЧШЕНО: Добавлено детальное логирование (файл, функция, строка, ошибка)

import logging
import asyncio
import inspect
import traceback

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from states.fsm import CreationStates

logger = logging.getLogger(__name__)
router = Router()


# ===== HELPER: Detailed logging formatter =====
def log_with_context(level: str, message: str, error: Exception = None):
    """
    Log message with detailed context:
    - 📄 File name
    - 🔧 Function name
    - 📍 Line number
    - ❌ Error details (if provided)
    
    Example output:
    🔴 [creation_extras.py:handle_unexpected_files:85] Error: Division by zero
    """
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename.split('/')[-1]  # Only filename, not full path
    function_name = frame.f_code.co_name
    line_number = frame.f_lineno
    
    # Format: [file:function:line]
    context = f"[{filename}:{function_name}:{line_number}]"
    
    if level == "DEBUG":
        if error:
            logger.debug(f"🔵 {context} {message} | Error: {error}")
        else:
            logger.debug(f"🔵 {context} {message}")
    elif level == "INFO":
        if error:
            logger.info(f"ℹ️  {context} {message} | Error: {error}")
        else:
            logger.info(f"ℹ️  {context} {message}")
    elif level == "WARNING":
        if error:
            logger.warning(f"⚠️  {context} {message} | Error: {error}")
        else:
            logger.warning(f"⚠️  {context} {message}")
    elif level == "ERROR":
        if error:
            logger.error(f"🔴 {context} {message} | Error: {error}")
            logger.error(f"   Traceback: {traceback.format_exc()}")
        else:
            logger.error(f"🔴 {context} {message}")
            logger.error(f"   Traceback: {traceback.format_exc()}")


# ===== FILE TYPE CONSTANTS =====
VALID_UPLOAD_STATES = {
    CreationStates.uploading_photo,      # Загружение основной фотографии
    CreationStates.uploading_furniture,  # Загружение фото мебели
    CreationStates.loading_facade_sample,  # Загружение фасада
}


# ===== HELPER: _delete_message_after_delay =====
async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int = 3):
    """
    Delete message after N seconds
    
    Logs:
    - ✅ Success: File:Function:Line - Message deleted
    - ⚠️  Bad Request: File:Function:Line - Message not found
    - 🔴 Error: File:Function:Line - Unexpected error
    """
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        log_with_context("INFO", f"Message {message_id} deleted from chat {chat_id}")
    except TelegramBadRequest as e:
        # Message already deleted or not found - not a critical error
        log_with_context("WARNING", f"Cannot delete message {message_id}", e)
    except Exception as e:
        log_with_context("ERROR", f"Error deleting message {message_id}", e)


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
    
    ЛОГИРОВАНИЕ:
    Все действия логируются с указанием:
    - 📄 Имя файла (creation_extras.py)
    - 🔧 Имя функции (handle_unexpected_files)
    - 📍 Номер строки (где произошло событие)
    - ❌ Ошибка (если есть)
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.message_id
    
    try:
        # Получить текущий стейт
        current_state = await state.get_state()
        log_with_context("DEBUG", f"Handler triggered - user_id={user_id}, chat_id={chat_id}, state={current_state}")
        
        # КРИТИЧНО: Если стейт правильный - проигнорировать
        if current_state in VALID_UPLOAD_STATES:
            log_with_context("DEBUG", f"Valid state detected {current_state} - skipping (other handler will process)")
            return
        
        # ===== НЕПРАВИЛЬНЫЙ СТЕЙТ - УДАЛИТЬ ФАЙЛ =====
        
        # Определить тип файла для логирования
        file_type = "unknown_file"
        if message.photo:
            file_type = "photo_📷"
        elif message.document:
            mime_type = message.document.mime_type or "unknown"
            file_type = f"document_📄({mime_type})"
        elif message.video:
            file_type = "video_🎥"
        elif message.video_note:
            file_type = "video_note_📹"
        elif message.audio:
            file_type = "audio_🎵"
        elif message.voice:
            file_type = "voice_🎙️"
        elif message.animation:
            file_type = "animation_🎬"
        
        log_with_context(
            "WARNING",
            f"Unexpected file received - user_id={user_id}, chat_id={chat_id}, "
            f"type={file_type}, current_state={current_state}, expected_states=[uploading_photo, uploading_furniture, loading_facade]"
        )
        
        # Отправить сообщение об ошибке
        error_message = (
            f"⚠️ **Сейчас нельзя отправлять файлы**\n\n"
            f"Получено: {file_type}\n\n"
            f"📋 Выберите действие в меню выше или отправьте /start"
        )
        
        try:
            error_msg = await message.answer(error_message, parse_mode="Markdown")
            log_with_context("INFO", f"Error message sent - error_msg_id={error_msg.message_id}")
            
            # Удалить сообщение об ошибке через 3 сек
            asyncio.create_task(
                _delete_message_after_delay(
                    message.bot,
                    chat_id,
                    error_msg.message_id,
                    delay=3
                )
            )
            log_with_context("INFO", f"Message scheduled for deletion - user_id={user_id}, delay=3s")
            
        except Exception as send_error:
            log_with_context("ERROR", f"Failed to send error message to user_id={user_id}", send_error)
        
        # Логировать попытку отправки файла в БД
        try:
            await db.log_activity(user_id, f'unexpected_file_{file_type}')
            log_with_context("INFO", f"Activity logged - user_id={user_id}, file_type={file_type}")
        except Exception as db_error:
            log_with_context("ERROR", f"Failed to log activity for user_id={user_id}", db_error)
    
    except Exception as e:
        log_with_context("ERROR", f"Critical error in handle_unexpected_files - user_id={user_id}", e)


# ===== FUTURE HANDLERS TEMPLATE =====
# Местo для добавления других обработчиков (например, text, commands, etc.)
# 
# @router.message(F.text)
# async def handle_text_in_wrong_state(message: Message, state: FSMContext):
#     """Handle text messages in unexpected states"""
#     try:
#         log_with_context("DEBUG", "Text handler triggered")
#         # Your code here
#     except Exception as e:
#         log_with_context("ERROR", "Error in handle_text_in_wrong_state", e)
#
# @router.message(F.sticker)
# async def handle_sticker_in_wrong_state(message: Message, state: FSMContext):
#     """Handle stickers in unexpected states"""
#     try:
#         log_with_context("DEBUG", "Sticker handler triggered")
#         # Your code here
#     except Exception as e:
#         log_with_context("ERROR", "Error in handle_sticker_in_wrong_state", e)
