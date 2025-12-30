# ===== PHASE 4: EXTRA FEATURES =====
# [2025-12-30] UNIVERSAL FILE CLEANUP HANDLER
# Обрабатывает и удаляет любые файлы если они не находятся в нужном стейте
# Поддерживает: фото, видео, документы, аудио, файлы и т.д.
# [2025-12-30 23:49] 🔥 CRITICAL FIX: SILENT DELETE - БЕЗ СООБЩЕНИЙ ОБ ОШИБКЕ! Просто удалить!

import logging
import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from states.fsm import CreationStates

logger = logging.getLogger(__name__)
router = Router()


# ===== CRITICAL FIX: 🔒 StateFilter for PHOTO uploads =====
# Эти хендлеры ПРОПУСКАЮТ сообщения в правильных стейтах (pass)
@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def handle_photo_in_uploading_photo_state(message: Message, state: FSMContext):
    """VALID STATE: uploading_photo - обработка в creation_main.py"""
    pass


@router.message(StateFilter(CreationStates.uploading_furniture), F.photo)
async def handle_photo_in_uploading_furniture_state(message: Message, state: FSMContext):
    """VALID STATE: uploading_furniture - обработка в других обработчиках"""
    pass


@router.message(StateFilter(CreationStates.loading_facade_sample), F.photo)
async def handle_photo_in_loading_facade_sample_state(message: Message, state: FSMContext):
    """VALID STATE: loading_facade_sample - обработка в других обработчиках"""
    pass


@router.message(StateFilter(CreationStates.text_input), F.text)
async def handle_text_in_text_input_state(message: Message, state: FSMContext):
    """VALID STATE: text_input - обработка текстового промпта в других хендлерах"""
    pass


# ===== 🔥 MEDIA GROUP (ALBUM) - SILENT DELETE =====
@router.message(
    ~StateFilter(CreationStates.uploading_photo),
    ~StateFilter(CreationStates.uploading_furniture),
    ~StateFilter(CreationStates.loading_facade_sample),
    F.photo,
    F.media_group_id
)
async def handle_unexpected_media_group(message: Message, state: FSMContext):
    """
    🔥 SILENT DELETE - Удаляем групповые фото БЕЗ СООБЩЕНИЙ!
    """
    try:
        await message.delete()
        logger.info(f"🗑️ [ALBUM_DELETED] user={message.from_user.id}, msg_id={message.message_id}")
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.error(f"❌ [ALBUM_DELETE_ERROR] {e}")


# ===== 🔥 SINGLE FILE - SILENT DELETE =====
@router.message(
    ~StateFilter(CreationStates.uploading_photo),
    ~StateFilter(CreationStates.uploading_furniture),
    ~StateFilter(CreationStates.loading_facade_sample),
    F.photo | F.document | F.video | F.video_note | F.audio | F.voice | F.animation,
    ~F.media_group_id
)
async def handle_unexpected_files(message: Message, state: FSMContext):
    """
    🔥 SILENT DELETE - Удаляем одиночные файлы БЕЗ СООБЩЕНИЙ!
    """
    try:
        await message.delete()
        logger.info(f"🗑️ [FILE_DELETED] user={message.from_user.id}, msg_id={message.message_id}")
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.error(f"❌ [FILE_DELETE_ERROR] {e}")


# ===== 🔥 TEXT - SILENT DELETE =====
@router.message(
    ~StateFilter(CreationStates.text_input),
    F.text
)
async def handle_unexpected_text(message: Message, state: FSMContext):
    """
    🔥 SILENT DELETE - Удаляем текст БЕЗ СООБЩЕНИЙ!
    """
    try:
        await message.delete()
        logger.info(f"🗑️ [TEXT_DELETED] user={message.from_user.id}, msg_id={message.message_id}")
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.error(f"❌ [TEXT_DELETE_ERROR] {e}")
