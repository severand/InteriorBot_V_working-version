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


# ══════════════════════════════════════════════════════════════════
# ✅ [VALID STATES] Photo uploads in expected states (pass-through)
# ══════════════════════════════════════════════════════════════════

@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def handle_photo_in_uploading_photo_state(message: Message, state: FSMContext):
    """✅ [SCREEN 2] uploading_photo - handled by creation_main.py"""
    pass


@router.message(StateFilter(CreationStates.uploading_furniture), F.photo)
async def handle_photo_in_uploading_furniture_state(message: Message, state: FSMContext):
    """✅ [SCREEN X] uploading_furniture - handled elsewhere"""
    pass


@router.message(StateFilter(CreationStates.loading_facade_sample), F.photo)
async def handle_photo_in_loading_facade_sample_state(message: Message, state: FSMContext):
    """✅ [SCREEN X] loading_facade_sample - handled elsewhere"""
    pass


@router.message(StateFilter(CreationStates.text_input), F.text)
async def handle_text_in_text_input_state(message: Message, state: FSMContext):
    """✅ [SCREEN X] text_input - handled elsewhere"""
    pass


# ══════════════════════════════════════════════════════════════════
# 🗑️ [INVALID STATES] Unexpected files - silent delete
# ══════════════════════════════════════════════════════════════════

@router.message(
    ~StateFilter(CreationStates.uploading_photo),
    ~StateFilter(CreationStates.uploading_furniture),
    ~StateFilter(CreationStates.loading_facade_sample),
    F.photo,
    F.media_group_id
)
async def handle_unexpected_media_group(message: Message, state: FSMContext):
    """🗑️ [CLEANUP] Album in wrong state - delete silently"""
    try:
        await message.delete()
        logger.info(f"🗑️ [ALBUM_DELETED] user={message.from_user.id}")
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.error(f"❌ [ALBUM_DELETE_ERROR] {e}")


@router.message(
    ~StateFilter(CreationStates.uploading_photo),
    ~StateFilter(CreationStates.uploading_furniture),
    ~StateFilter(CreationStates.loading_facade_sample),
    F.photo | F.document | F.video | F.video_note | F.audio | F.voice | F.animation,
    ~F.media_group_id
)
async def handle_unexpected_files(message: Message, state: FSMContext):
    """🗑️ [CLEANUP] File in wrong state - delete silently"""
    try:
        await message.delete()
        logger.info(f"🗑️ [FILE_DELETED] user={message.from_user.id}")
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.error(f"❌ [FILE_DELETE_ERROR] {e}")


@router.message(
    ~StateFilter(CreationStates.text_input),
    F.text
)
async def handle_unexpected_text(message: Message, state: FSMContext):
    """🗑️ [CLEANUP] Text in wrong state - delete silently"""
    try:
        await message.delete()
        logger.info(f"🗑️ [TEXT_DELETED] user={message.from_user.id}")
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.error(f"❌ [TEXT_DELETE_ERROR] {e}")
