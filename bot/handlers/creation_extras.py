# bot/handlers/creation_extras.py
# ===== PHASE 4: ERROR HANDLERS + MESSAGE BLOCKING =====
# [2025-12-29] НОВЫЙ ФАЙЛ: Часть 4 рефакторинга creation.py
# Содержит: Обработчики невалидных действий
# ЗУЧНО! Этот файл регистрируется ПОСЛЕДНИМ — в конце loader.py

import asyncio
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StateFilter
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message

from database.db import db
from utils.navigation import show_main_menu
from states.fsm import CreationStates

logger = logging.getLogger(__name__)
router = Router()


# ===== HANDLER: Обработка устарелых кнопок (после рестарта) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query()
async def handle_stale_creation_buttons(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    ФАЛОВАЯ КНОПКА: когда пользователь нажимает на кнопку что-то археологическое
    
    Проверка:
    1. Нежданная callback_query — Правило делать ничего
    2. Если в FSM нет photo_id — сессия устарела, вернуть в МЕНЮ
    
    МУВО: Помещаем рОУТЕР В КОНЦЕ loader.py (ПОСЛЕ всех остальных!)
    """
    user_id = callback.from_user.id
    
    try:
        # Проверяем photo_id в FSM
        data = await state.get_data()
        photo_id = data.get('photo_id')
        
        if not photo_id:
            # Сессия устарела — вернуть в МЕНЮ
            logger.info(f"⚠️ Отпустили устарелую кнопку: {callback.data}, user_id={user_id}")
            
            try:
                await callback.answer(
                    "⚠️ Сессия енства. Вернитесь в МЕНЮ.",
                    show_alert=False
                )
            except:
                pass
            
            await show_main_menu(callback, state, admins)
            return
        
        # Нормальная кнопка для меню НЕ зарегистрирована в других хандлерах
        logger.debug(f"ℹ️ Удалось по незнакомых данных: {callback.data}, user_id={user_id}")
        
        try:
            await callback.answer("❌ Команда не понята.", show_alert=False)
        except:
            pass
            
    except Exception as e:
        logger.error(f"[ERROR] HANDLE_STALE_CREATION_BUTTONS failed: {e}", exc_info=True)


# ===== HANDLERS: БЛОКИРОВКА НЕВОрОдНЫХ СООБЩЕНИЙ =====
# НУЖНО! КФО НА ОПРЕДЕЛЕННЫХ ОтАНИЯХ

# НЕОЖИДАННЫЕ ПОтО’ (invalid_photo)
@router.message(
    StateFilter(CreationStates.uploading_photo, CreationStates.waiting_for_photo),
    F.content_type != "photo"
)
async def invalid_photo(message: Message, state: FSMContext):
    """Да не то, а это! Мне нужна ФОТО!"""
    try:
        await message.delete()
    except Exception:
        pass


# ТЕКСТ НА ЭтАПЕ "CHOOSE_ROOM"
@router.message(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2, CreationStates.choose_style)
)
async def block_messages_in_choose_style(message: Message, state: FSMContext):
    """
    В этом экране работают низь кнопки, все текст блокируем
    """
    try:
        await message.delete()
    except Exception:
        pass


# НЕОжиданНыЕ ТИПЫ МЕДИА
@router.message(
    StateFilter(CreationStates.uploading_photo, CreationStates.waiting_for_photo),
    F.content_type.in_({
        "video", "audio", "voice", "document", "animation", "dice",
        "video_note", "contact", "location", "venue", "poll", "sticker"
    })
)
async def block_unexpected_media(message: Message, state: FSMContext):
    """Люди посылают документы, аудио — блокируем"""
    try:
        await message.delete()
    except Exception:
        pass


# ПО МЮГОВ ТЕКСТ: БЛОКИРОВКА ДО выбора рЕЖИМА
@router.message(
    StateFilter(CreationStates.selecting_mode)
)
async def block_messages_in_select_mode(message: Message, state: FSMContext):
    """
    На экране выбора режима — только кнопки
    """
    try:
        await message.delete()
    except Exception:
        pass


# ПО МЮГОВ ТЕКСТ: БЛОКИРОВКА ДО выбора комнаты
@router.message(
    StateFilter(CreationStates.room_choice)
)
async def block_messages_in_room_choice(message: Message, state: FSMContext):
    """
    На экране выбора комнаты — только кнопки
    """
    try:
        await message.delete()
    except Exception:
        pass


# НЕОЖИДАННЫЕ ФОТО НА ОЦЕНКЕ "ОНИ ОЦЕНИВАЮТ"
@router.message(
    StateFilter(
        CreationStates.exterior_prompt,
        CreationStates.room_description,
        CreationStates.clear_space_confirm,
        CreationStates.post_generation
    ),
    F.photo
)
async def block_unexpected_photos_on_wrong_screen(message: Message, state: FSMContext):
    """
    На этих экранах фото НЕ оридаются
    """
    try:
        await message.delete()
    except Exception:
        pass
