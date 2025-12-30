# ===== PHASE 4: EXTRA FEATURES =====
# [2025-12-30] UNIVERSAL FILE CLEANUP HANDLER
# Обрабатывает и удаляет любые файлы если они не находятся в нужном стейте
# Поддерживает: фото, видео, документы, аудио, файлы и т.д.
# [2025-12-30 22:04] УЛУЧШЕНО: Добавлено детальное логирование (файл, функция, строка, ошибка)
# [2025-12-30 23:00] 🔒 CRITICAL FIX: Добавлены StateFilter на ВСЕ обработчики!
# [2025-12-30 23:05] 🐛 FIX: Исправлена ошибка Markdown разметки в сообщении об ошибке
# [2025-12-30 23:10] 🔧 FIX: Детальное логирование удаления сообщений - трекинг жизненного цикла
# [2025-12-30 23:18] 🔥 CRITICAL FIX: Исправлена отмена background task при удалении сообщений!

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

# 🔥 CRITICAL: Store background tasks to prevent garbage collection
_background_tasks = set()


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


# ===== HELPER: _delete_message_after_delay (WITH DETAILED LOGGING) =====
# [2025-12-30 23:10] 🔧 IMPROVED: Добавлено ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int = 3):
    """
    Delete message after N seconds WITH DETAILED LOGGING
    
    Жизненный цикл (для отладки):
    1. 🔔 [START] Начало ждания
    2. ⏳ [WAITING] Ожидание N секунд
    3. 🔒 [DELETING] Начало делета
    4. ✅ [SUCCESS] Мессаж удалён
    5. ⚠️  [ERROR] Ошибка
    """
    try:
        log_with_context("INFO", f"[DELETE_START] chat_id={chat_id}, msg_id={message_id}, delay={delay}s")
        
        await asyncio.sleep(delay)
        log_with_context("INFO", f"[DELETE_WAITING_DONE] chat_id={chat_id}, msg_id={message_id} - сн работает!")
        
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        log_with_context("INFO", f"[DELETE_SUCCESS] ✅ Message {message_id} successfully deleted from chat {chat_id}")
        
    except TelegramBadRequest as e:
        # Message already deleted or not found - not a critical error
        log_with_context("WARNING", f"[DELETE_BADREQUEST] Message {message_id} - {str(e)[:100]}", e)
        
    except Exception as e:
        log_with_context("ERROR", f"[DELETE_ERROR] Critical error deleting msg {message_id}", e)


# ===== CRITICAL FIX: 🔒 StateFilter for PHOTO uploads =====
# [2025-12-30 23:00] ⚠️ ВАЖНО: Обработчик может быть вызван ТОЛЬКО в нужном стейте!
@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def handle_photo_in_uploading_photo_state(message: Message, state: FSMContext):
    """
    VALID STATE: uploading_photo - обработка в creation_main.py
    """
    pass


# ===== CRITICAL FIX: 🔒 StateFilter for FURNITURE uploads =====
@router.message(StateFilter(CreationStates.uploading_furniture), F.photo)
async def handle_photo_in_uploading_furniture_state(message: Message, state: FSMContext):
    """
    VALID STATE: uploading_furniture - обработка в других обработчиках
    """
    pass


# ===== CRITICAL FIX: 🔒 StateFilter for FACADE uploads =====
@router.message(StateFilter(CreationStates.loading_facade_sample), F.photo)
async def handle_photo_in_loading_facade_sample_state(message: Message, state: FSMContext):
    """
    VALID STATE: loading_facade_sample - обработка в других обработчиках
    """
    pass


# ===== UNIVERSAL FILE CLEANUP HANDLER =====
# 🔒 CRITICAL FIX [2025-12-30 23:00]: Добавлен NEGATIVE StateFilter
@router.message(
    ~StateFilter(CreationStates.uploading_photo),
    ~StateFilter(CreationStates.uploading_furniture),
    ~StateFilter(CreationStates.loading_facade_sample),
    F.photo | F.document | F.video | F.video_note | F.audio | F.voice | F.animation
)
async def handle_unexpected_files(message: Message, state: FSMContext):
    """
    UNIVERSAL FILE CLEANUP HANDLER
    
    Логика:
    1. Проверить текущий FSM стейт
    2. Отправить сообщение об ошибке
    3. Удалить сообщение через 3 сек
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    try:
        current_state = await state.get_state()
        log_with_context("DEBUG", f"Unexpected file - user_id={user_id}, state={current_state}")
        
        # Определить тип файла
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
            f"Unexpected file received - user_id={user_id}, type={file_type}, state={current_state}"
        )
        
        # Отправить сообщение об ошибке
        error_message = (
            "⚠️ Сейчас нельзя отправлять файлы\n\n"
            f"Получено: {file_type}\n\n"
            "Выберите действие в меню выше или отправьте /start"
        )
        
        try:
            error_msg = await message.answer(error_message)
            log_with_context("INFO", f"[MSG_SENT] Отправлено msg_id={error_msg.message_id}")
            
            # 🔥 [2025-12-30 23:18] CRITICAL FIX: Правильно хранить ссылку на background task!
            # Проблема была в том, что create_task создавал задачу, но она могла быть
            # отменена garbage collector'ом если на неё нет ссылок!
            delete_task = asyncio.create_task(
                _delete_message_after_delay(
                    message.bot,
                    chat_id,
                    error_msg.message_id,
                    delay=3
                )
            )
            
            # 🔒 CRITICAL: Добавляем задачу в set чтобы она не была отменена
            _background_tasks.add(delete_task)
            # 🔒 Удаляем задачу из set когда она завершится
            delete_task.add_done_callback(_background_tasks.discard)
            
            log_with_context("INFO", f"[DELETE_SCHEDULED] От msg_id={error_msg.message_id} снесена делетная задача")
            
        except Exception as send_error:
            log_with_context("ERROR", f"Failed to send error message", send_error)
        
        # Логировать в БД
        try:
            await db.log_activity(user_id, f'unexpected_file_{file_type}')
            log_with_context("INFO", f"Activity logged - user_id={user_id}, file_type={file_type}")
        except Exception as db_error:
            log_with_context("ERROR", f"Failed to log activity", db_error)
    
    except Exception as e:
        log_with_context("ERROR", f"Critical error in handle_unexpected_files", e)


# ===== FUTURE HANDLERS TEMPLATE =====
# Место для добавления других обработчиков
