# ===== PHASE 1: MAIN ENTRY POINT + PHOTO UPLOAD =====

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from database.db import db

from keyboards.inline import (
    get_work_mode_selection_keyboard,  # ✅ ИСПРАВЛЕНО: 5 режимов работы
    get_uploading_photo_keyboard,
    get_what_is_in_photo_keyboard,
    get_payment_keyboard,
    get_room_choice_keyboard,
    get_edit_design_keyboard,
    get_download_sample_keyboard,
    get_uploading_furniture_keyboard,
    get_loading_facade_sample_keyboard,
)

from states.fsm import CreationStates, WorkMode

from utils.texts import (
    MODE_SELECTION_TEXT,
    UPLOADING_PHOTO_TEMPLATES,
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    WHAT_IS_IN_PHOTO_TEXT,
    ERROR_INSUFFICIENT_BALANCE,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

logger = logging.getLogger(__name__)
router = Router()

# 🔥 [2025-12-31 14:00] CRITICAL: Locks for synchronizing media_group processing
# Structure: {user_id: {media_group_id: asyncio.Lock()}}
# Purpose: Ensure ONLY ONE handler processes each media_group
media_group_locks = {}

# 🔥 [2025-12-31 11:33] CRITICAL: Track media_group uploads to detect multiple photos
# Structure: {user_id: {media_group_id: {'photos': [msg_ids], 'processed': False, 'timestamp': time}}}
media_group_tracker = {}


async def get_media_group_lock(user_id: int, media_group_id: str) -> asyncio.Lock:
    """
    🔥 [2025-12-31 14:00] Get or create lock for specific media_group
    
    CRITICAL: This ensures only ONE handler processes each media_group
    When handlers 1,2,3,4 arrive for the same media_group:
    - Handler 1: acquires lock, collects ALL photos (1,2,3,4)
    - Handlers 2,3,4: wait for lock, see media_group already processed, return
    
    Without this: Each handler processes separately with incomplete photo list
    """
    if user_id not in media_group_locks:
        media_group_locks[user_id] = {}
    
    if media_group_id not in media_group_locks[user_id]:
        media_group_locks[user_id][media_group_id] = asyncio.Lock()
    
    return media_group_locks[user_id][media_group_id]


async def collect_media_group(user_id: int, media_group_id: str, message_id: int):
    """
    🔥 [2025-12-31 13:14] Collect all photos from media_group
    
    Algorithm:
    1. Register this photo in media_group
    2. Wait 1000ms for other photos to arrive (increased from 500ms)
    3. Return: (count_of_photos, message_ids)
    
    Why 1000ms?
    - When user uploads 1-2 photos: arrive within ~100-300ms
    - When user uploads 3-4+ photos: can arrive within ~500-800ms
    - 1000ms gives safe margin to collect ALL photos
    - After 1000ms, we can safely say "all photos arrived"
    
    🔧 [2025-12-31 13:14] FIX: Was missing last photos when uploading 3+
    """
    
    if user_id not in media_group_tracker:
        media_group_tracker[user_id] = {}
    
    if media_group_id not in media_group_tracker[user_id]:
        media_group_tracker[user_id][media_group_id] = {
            'photos': [],
            'processed': False,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    # Add this photo
    media_group_tracker[user_id][media_group_id]['photos'].append(message_id)
    photo_count = len(media_group_tracker[user_id][media_group_id]['photos'])
    
    logger.info(f"📸 [MEDIA_GROUP] user={user_id}, group={media_group_id}, photo #{photo_count} arrived")
    
    # Wait 1000ms (1 sec) for more photos
    await asyncio.sleep(1.0)
    
    # Get final count
    final_count = len(media_group_tracker[user_id][media_group_id]['photos'])
    message_ids = media_group_tracker[user_id][media_group_id]['photos'].copy()
    
    logger.info(f"📸 [MEDIA_GROUP] user={user_id}, group={media_group_id}, FINAL count={final_count}")
    
    return final_count, message_ids


# ===== SCREEN 0: MAIN MENU =====
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Return to main menu"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'main_menu')
    await show_main_menu(callback, state, admins)
    await callback.answer()


# ===== SCREEN 1: SELECT_MODE (Work mode selection) =====
# [2025-12-29] NEW (V3) - SCREEN WITH 5 WORK MODES
@router.callback_query(F.data == "select_mode")
async def select_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1: Select work mode (5 options)
    
    Main flow entry point:
    - 📋 Create new design (NEW_DESIGN)
    - ✏️ Edit design (EDIT_DESIGN)
    - 🎁 Try on design (SAMPLE_DESIGN)
    - 🛋️ Arrange furniture (ARRANGE_FURNITURE)
    - 🏠 Design facade (FACADE_DESIGN)
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        # Set state for mode selection
        await state.set_state(CreationStates.selecting_mode)

        text = MODE_SELECTION_TEXT
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_work_mode_selection_keyboard(),
            show_balance=False,
            screen_code='select_mode'
        )
        
        logger.info(f"[V3] SELECT_MODE - user_id={user_id}, showing 5 work modes")
        
    except Exception as e:
        logger.error(f"[ERROR] SELECT_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)


# ===== HANDLER: SET_WORK_MODE (Handle mode selection) =====
@router.callback_query(F.data.startswith("select_mode_"))
async def set_work_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1→2: Handle work mode selection
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id

    try:
        # Extract mode from callback_data
        mode_str = callback.data.replace("select_mode_", "")
        
        # Convert string to WorkMode enum
        mode_map = {
            "new_design": WorkMode.NEW_DESIGN,
            "edit_design": WorkMode.EDIT_DESIGN,
            "sample_design": WorkMode.SAMPLE_DESIGN,
            "arrange_furniture": WorkMode.ARRANGE_FURNITURE,
            "facade_design": WorkMode.FACADE_DESIGN,
        }
        
        work_mode = mode_map.get(mode_str)
        if not work_mode:
            logger.warning(f"[WARNING] Unknown mode_str: {mode_str}")
            await callback.answer("❌ Неизвестный режим", show_alert=True)
            return
        
        # Save work_mode in FSM
        await state.update_data(
            work_mode=work_mode.value,
            photo_uploaded=False
        )
        await state.set_state(CreationStates.uploading_photo)
        
        text = UPLOADING_PHOTO_TEMPLATES.get(work_mode.value, "📄 Загружите фото")
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_uploading_photo_keyboard(),
            show_balance=False,
            screen_code='uploading_photo'
        )
        
        logger.info(f"[V3] {work_mode.value.upper()}_MODE_SELECTED - screen updated for user {user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SET_WORK_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе режима", show_alert=True)


# ===== SCREEN 2: PHOTO_HANDLER (Photo upload for all modes) =====
@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """
    SCREEN 2: Photo upload (UPLOADING_PHOTO)
    
    LOGIC:
    1. ONE photo: Create menu with buttons, send
    2. MULTIPLE photos: Delete ALL photos + old menu + SEND TEXT-ONLY MESSAGE
    
    [2025-12-31 14:00] 🔥 CRITICAL FIX: Lock BEFORE collect_media_group
    - When 4 photos arrive simultaneously, all 4 handlers start
    - Without proper locking, each creates its own media_group entry
    - Solution: Get lock IMMEDIATELY, only first handler collects all photos
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    work_mode = data.get('work_mode')

    logger.info(f"🎞️ [PHOTO_HANDLER] START - user_id={user_id}, work_mode={work_mode}, photo received")

    # ===== STEP 1: DETECT MEDIA_GROUP =====
    media_group_id = message.media_group_id
    
    if media_group_id:
        logger.info(f"🔍 [PHOTO_HANDLER] Detected media_group_id={media_group_id}")
        
        # 🔥 [2025-12-31 14:00] GET LOCK IMMEDIATELY (before any processing)
        media_group_lock = await get_media_group_lock(user_id, media_group_id)
        
        async with media_group_lock:
            logger.info(f"🔐 [PHOTO_HANDLER] Acquired lock for media_group={media_group_id}")
            
            # Check if already processed by first handler
            if (user_id in media_group_tracker and 
                media_group_id in media_group_tracker[user_id] and 
                media_group_tracker[user_id][media_group_id].get('processed')):
                
                logger.info(f"⏭️ [PHOTO_HANDLER] Media group already processed, skipping handler")
                return
            
            try:
                photo_count, all_message_ids = await collect_media_group(
                    user_id, 
                    media_group_id, 
                    message.message_id
                )
                
                logger.info(f"📸 [PHOTO_HANDLER] Media group collected: count={photo_count}, msg_ids={all_message_ids}")
                
                # ===== STEP 2: CHECK IF MULTIPLE PHOTOS =====
                if photo_count > 1:
                    logger.warning(f"❌ [PHOTO_HANDLER] MULTIPLE PHOTOS DETECTED: {photo_count}")
                    
                    media_group_tracker[user_id][media_group_id]['processed'] = True
                    
                    # 🔥 [2025-12-31 14:45] PARALLEL DELETE ALL PHOTOS
                    delete_tasks = []
                    for msg_id in all_message_ids:
                        delete_tasks.append(
                            message.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                        )
                    
                    # Wait for all delete tasks to complete
                    results = await asyncio.gather(*delete_tasks, return_exceptions=True)
                    deleted_count = sum(1 for r in results if not isinstance(r, Exception))
                    logger.info(f"🗑️ [PHOTO_HANDLER] Deleted {deleted_count}/{photo_count} photos")
                    
                    # 🔥 [2025-12-31 14:45] DELETE OLD MENU
                    old_menu_data = await db.get_chat_menu(chat_id)
                    old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None
                    
                    if old_menu_message_id:
                        try:
                            await message.bot.delete_message(chat_id=chat_id, message_id=old_menu_message_id)
                            logger.info(f"✅ Удалено старое меню {old_menu_message_id}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not delete old menu: {e}")
                    
                    # 🔥 [2025-12-31 14:45] SEND TEXT-ONLY MESSAGE (NO buttons)
                    text = UPLOADING_PHOTO_TEMPLATES.get(work_mode, "📸 **Загрузите фото помещения**\n\nПожалуйста, отправьте ОДНУ фотографию.")
                    text = f"⚠️ **ПОЖАЛУЙСТА, ОДНО ФОТО!**\n\n{text}\n\n🔄 Попробуйте ещё раз - отправьте одну фотографию."
                    
                    info_msg = await message.answer(
                        text=text,
                        parse_mode="Markdown"
                        # 🔥 NO reply_markup (NO buttons)
                    )
                    logger.info(f"📨 [PHOTO_HANDLER] Text-only message sent: msg_id={info_msg.message_id}")
                    
                    logger.info(f"📊 [PHOTO_HANDLER] MULTIPLE PHOTOS: All deleted (photos + menu), text-only message sent, waiting for single photo")
                    return
                
                # ===== STEP 3: SINGLE PHOTO - PROCESS NORMALLY =====
                logger.info(f"✅ [PHOTO_HANDLER] Single photo detected, processing...")
                
                if not message.photo:
                    error_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
                    await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
                    asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                    return
                
                balance = await db.get_balance(user_id)
                if balance <= 0 and work_mode != WorkMode.EDIT_DESIGN.value:
                    error_text = ERROR_INSUFFICIENT_BALANCE
                    error_msg = await message.answer(error_text)
                    await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
                    asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                    return
                
                photo_id = message.photo[-1].file_id
                logger.info(f"💾 [PHOTO_HANDLER] Photo saved - photo_id={photo_id[:20]}...")
                
                await state.update_data(
                    photo_id=photo_id,
                    new_photo=True,
                    photo_uploaded=True
                )
                
                old_menu_data = await db.get_chat_menu(chat_id)
                old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None
                
                logger.info(f"📥 [PHOTO_HANDLER] Old menu_id={old_menu_message_id}")
                
                if old_menu_message_id:
                    try:
                        await message.bot.delete_message(chat_id=chat_id, message_id=old_menu_message_id)
                        logger.info(f"🗑️ [PHOTO_HANDLER] Deleted old menu {old_menu_message_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not delete old menu: {e}")
                
                # DETERMINE NEXT SCREEN
                if work_mode == WorkMode.NEW_DESIGN.value:
                    await state.set_state(CreationStates.room_choice)
                    text = f"🏠 **Выберите комнату**"
                    text = await add_balance_and_mode_to_text(text, user_id, work_mode='new_design')
                    keyboard = get_room_choice_keyboard()
                    screen = 'room_choice'
                    
                elif work_mode == WorkMode.EDIT_DESIGN.value:
                    await state.set_state(CreationStates.edit_design)
                    text = f"✏️ **Редактируем дизайн**"
                    text = await add_balance_and_mode_to_text(text, user_id, work_mode='edit_design')
                    keyboard = get_edit_design_keyboard()
                    screen = 'edit_design'
                    
                elif work_mode == WorkMode.SAMPLE_DESIGN.value:
                    await state.set_state(CreationStates.download_sample)
                    text = f"📥 **Скачать примеры**"
                    text = await add_balance_and_mode_to_text(text, user_id, work_mode='sample_design')
                    keyboard = get_download_sample_keyboard()
                    screen = 'download_sample'
                    
                elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
                    await state.set_state(CreationStates.uploading_furniture)
                    text = f"🛋️ **Расстановка мебели**"
                    text = await add_balance_and_mode_to_text(text, user_id, work_mode='arrange_furniture')
                    keyboard = get_uploading_furniture_keyboard()
                    screen = 'uploading_furniture'
                    
                elif work_mode == WorkMode.FACADE_DESIGN.value:
                    await state.set_state(CreationStates.loading_facade_sample)
                    text = f"🏘️ **Дизайн фасада**"
                    text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
                    keyboard = get_loading_facade_sample_keyboard()
                    screen = 'loading_facade_sample'
                else:
                    logger.error(f"[ERROR] Unknown work_mode: {work_mode}")
                    await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
                    return
                
                logger.info(f"📤 [PHOTO_HANDLER] Sending menu - screen={screen}")
                menu_msg = await message.answer(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ [PHOTO_HANDLER] Menu sent, msg_id={menu_msg.message_id}")
                
                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, screen)
                await state.update_data(menu_message_id=menu_msg.message_id)
                
                logger.info(f"📊 [PHOTO_HANDLER] COMPLETE - user_id={user_id}, transitioned to {screen}")
                
            except Exception as e:
                logger.error(f"❌ [PHOTO_HANDLER] FATAL ERROR for user {user_id}: {e}", exc_info=True)
                try:
                    error_msg = await message.answer("❌ Ошибка при обработке фото. Попробуйте ещё раз.")
                    asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                except:
                    pass
    else:
        # Single photo (no media_group_id)
        logger.info(f"✅ [PHOTO_HANDLER] Single photo (no media_group), processing directly...")
        
        try:
            if not message.photo:
                error_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
                await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
                asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                return
            
            balance = await db.get_balance(user_id)
            if balance <= 0 and work_mode != WorkMode.EDIT_DESIGN.value:
                error_text = ERROR_INSUFFICIENT_BALANCE
                error_msg = await message.answer(error_text)
                await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
                asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                return
            
            photo_id = message.photo[-1].file_id
            logger.info(f"💾 [PHOTO_HANDLER] Photo saved - photo_id={photo_id[:20]}...")
            
            await state.update_data(
                photo_id=photo_id,
                new_photo=True,
                photo_uploaded=True
            )
            
            old_menu_data = await db.get_chat_menu(chat_id)
            old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None
            
            if old_menu_message_id:
                try:
                    await message.bot.delete_message(chat_id=chat_id, message_id=old_menu_message_id)
                    logger.info(f"🗑️ [PHOTO_HANDLER] Deleted old menu {old_menu_message_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete old menu: {e}")
            
            # DETERMINE NEXT SCREEN
            if work_mode == WorkMode.NEW_DESIGN.value:
                await state.set_state(CreationStates.room_choice)
                text = f"🏠 **Выберите комнату**"
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='new_design')
                keyboard = get_room_choice_keyboard()
                screen = 'room_choice'
                
            elif work_mode == WorkMode.EDIT_DESIGN.value:
                await state.set_state(CreationStates.edit_design)
                text = f"✏️ **Редактируем дизайн**"
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='edit_design')
                keyboard = get_edit_design_keyboard()
                screen = 'edit_design'
                
            elif work_mode == WorkMode.SAMPLE_DESIGN.value:
                await state.set_state(CreationStates.download_sample)
                text = f"📥 **Скачать примеры**"
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='sample_design')
                keyboard = get_download_sample_keyboard()
                screen = 'download_sample'
                
            elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
                await state.set_state(CreationStates.uploading_furniture)
                text = f"🛋️ **Расстановка мебели**"
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='arrange_furniture')
                keyboard = get_uploading_furniture_keyboard()
                screen = 'uploading_furniture'
                
            elif work_mode == WorkMode.FACADE_DESIGN.value:
                await state.set_state(CreationStates.loading_facade_sample)
                text = f"🏘️ **Дизайн фасада**"
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
                keyboard = get_loading_facade_sample_keyboard()
                screen = 'loading_facade_sample'
            else:
                logger.error(f"[ERROR] Unknown work_mode: {work_mode}")
                await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
                return
            
            logger.info(f"📤 [PHOTO_HANDLER] Sending menu - screen={screen}")
            menu_msg = await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            logger.info(f"✅ [PHOTO_HANDLER] Menu sent, msg_id={menu_msg.message_id}")
            
            await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, screen)
            await state.update_data(menu_message_id=menu_msg.message_id)
            
            logger.info(f"📊 [PHOTO_HANDLER] COMPLETE - user_id={user_id}, transitioned to {screen}")
            
        except Exception as e:
            logger.error(f"❌ [PHOTO_HANDLER] FATAL ERROR for user {user_id}: {e}", exc_info=True)
            try:
                error_msg = await message.answer("❌ Ошибка при обработке фото. Попробуйте ещё раз.")
                asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
            except:
                pass


async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int):
    """Delete message after N seconds"""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"✅ Удалено сообщение {message_id} в чате {chat_id}")
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить сообщение {message_id}: {e}")


@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    """Start creating design (old system)"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'create_design')

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()

    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    await state.set_state(CreationStates.uploading_photo)

    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=get_uploading_photo_keyboard(),
        show_balance=False,
        screen_code='upload_photo'
    )
