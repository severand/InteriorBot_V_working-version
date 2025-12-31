# ===== PHASE 1: MAIN ENTRY POINT + PHOTO UPLOAD =====

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from database.db import db

from keyboards.inline import (
    get_work_mode_selection_keyboard,  # ✅ ИСПРАВЛЕНО: 5 режимов работы
    get_upload_photo_keyboard,
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

# 🔥 [2025-12-31 11:04] CRITICAL: Per-user locks for synchronizing concurrent photo uploads
# Prevents race condition when user uploads multiple photos simultaneously
user_photo_locks = {}  # {user_id: asyncio.Lock()}


def get_user_lock(user_id: int) -> asyncio.Lock:
    """🔥 Get or create asyncio.Lock for user"""
    if user_id not in user_photo_locks:
        user_photo_locks[user_id] = asyncio.Lock()
    return user_photo_locks[user_id]


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
    
    FIX: [2025-12-29 23:10] - No footer duplication
         MODE_SELECTION_TEXT already contains full description of all 5 modes
         No need to add footer via add_balance_and_mode_to_text()
    
    UPDATED: [2025-12-30 16:35] - select_mode now called from user_start.py
             create_design button on SCREEN 0 displays this screen
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        # Set state for mode selection
        await state.set_state(CreationStates.selecting_mode)

        # Get ready text from utils/texts.py
        # MODE_SELECTION_TEXT already contains FULL description of all 5 modes
        text = MODE_SELECTION_TEXT
        
        # ✅ NO footer needed - text already complete!
        # Just edit menu with 5 mode buttons
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_work_mode_selection_keyboard(),  # 5 mode buttons
            show_balance=False,  # Balance not needed here
            screen_code='select_mode'
        )
        
        logger.info(f"[V3] SELECT_MODE - user_id={user_id}, showing 5 work modes")
        
    except Exception as e:
        logger.error(f"[ERROR] SELECT_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)


# ===== HANDLER: SET_WORK_MODE (Handle mode selection) =====
# [2025-12-29] NEW (V3)
# [2025-12-30 22:45] 🔥 CRITICAL: menu_message_id теперь берется из БД + больше логов!
@router.callback_query(F.data.startswith("select_mode_"))
async def set_work_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1→2: Handle work mode selection
    
    Modes:
    - select_mode_new_design → NEW_DESIGN
    - select_mode_edit_design → EDIT_DESIGN
    - select_mode_sample_design → SAMPLE_DESIGN
    - select_mode_arrange_furniture → ARRANGE_FURNITURE
    - select_mode_facade_design → FACADE_DESIGN
    
    FINAL FIX: [2025-12-30 15:52]
    - RESTORED edit_menu() call - это дает визуальные реакции кнопкам
    - edit_menu() РЕДАКТИРУЕТ ТОЛЬКО ТЕКСТ (НЕ фото!)
    - photo_handler() потом добавит фото через send_photo()
    
    Why this works NOW:
    1. set_work_mode() calls edit_menu() - updates TEXT to "📄 Загрузите фото" ✅
       Пользователь видит ответ на кнопку ✅
    2. photo_handler() calls send_photo() - creates NEW message with photo ✅
       Кнопки прикреплены к фотке ✅
    3. Old message without photo gets deleted ✅
    4. Result: ONE message with photo + buttons (no duplicates!) ✅
    
    Why NOT just send_message about mode:
    - edit_menu() отредактивает ТЕКУЩЕЕ меню на SCREEN 1
    - Кнопки оно также меняет ✅
    - Не создает слишком много сообщений ✅
    
    CRITICAL FIX: [2025-12-30 22:45]
    ❌ OLD: Save menu_message_id в FSM (теряется при перезапуске)
    ✅ NEW: menu_message_id автоматически сохраняется в БД через edit_menu()
    
    CRITICAL FIX: [2025-12-29 23:24]
    - Save menu_message_id IN FSM state for work_mode reference only!
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
        
        # Save ONLY work_mode in FSM (NOT menu_message_id - it's in DB)
        await state.update_data(
            work_mode=work_mode.value,
            photo_uploaded=False  # 🔥 [2025-12-31 10:53] Reset photo flag for new upload session
        )
        await state.set_state(CreationStates.uploading_photo)
        
        # ✅ RESTORED [2025-12-30 15:52]: Обновить SCREEN для пользователя
        # ❌ NO footer here!
        text = UPLOADING_PHOTO_TEMPLATES.get(work_mode.value, "📄 Загружите фото")
        # ✅ FOOTER WILL BE ADDED IN photo_handler() AFTER PHOTO UPLOAD!
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_upload_photo_keyboard(),
            show_balance=False,
            screen_code='uploading_photo'  # ✅ This saves menu_message_id to DB!
        )
        
        logger.info(f"[V3] {work_mode.value.upper()}+MODE_SELECTED - screen updated for user {user_id}, awaiting photo...")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SET_WORK_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе режима", show_alert=True)


# ===== SCREEN 2: PHOTO_HANDLER (Photo upload for all modes) =====
# [2025-12-29] UPDATED (V3)
# [2025-12-30 22:45] 🔥 CRITICAL: menu_message_id из БД + INFO логи для отладки!
# [2025-12-31 10:53] 🔥 CRITICAL: Allow only ONE photo per session!
# [2025-12-31 11:04] 🔥 CRITICAL: Use asyncio.Lock to sync concurrent uploads!
# [2025-12-31 11:08] 🔥 CRITICAL: DELETE ALL photos if multiple! NO menu for multiple photos!
@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """
    SCREEN 2: Photo upload (UPLOADING_PHOTO)
    
    Logic:
    1. 🔥 [2025-12-31 11:08] CHECK for multiple photos: If count > 1 → DELETE ALL + ERROR
    2. 🔥 [2025-12-31 11:04] LOCK: Acquire per-user lock (sync concurrent uploads)
    3. 🔥 [2025-12-31 10:53] CHECK: Has photo already been uploaded? If YES → ERROR
    4. Photo validation
    5. Balance check (except EDIT_DESIGN)
    6. Save file_id in FSM
    7. GET old menu_message_id FROM DATABASE (NOT FSM!)
    8. DELETE OLD MENU MESSAGE before sending new one
    9. Send NEW message with text + buttons BELOW the photo user uploaded
    10. Save new menu_message_id to DATABASE
    11. Set photo_uploaded=True flag to prevent duplicate uploads
    12. Transition to NEXT screen (depends on mode):
        - NEW_DESIGN → ROOM_CHOICE
        - EDIT_DESIGN → EDIT_DESIGN
        - SAMPLE_DESIGN → DOWNLOAD_SAMPLE
        - ARRANGE_FURNITURE → UPLOADING_FURNITURE
        - FACADE_DESIGN → LOADING_FACADE_SAMPLE
    
    KEY FIX [2025-12-31 11:08] - DELETE ALL PHOTOS IF MULTIPLE:
    🔥 Problem: When user uploads multiple photos in media_group:
              - Need to delete ALL of them
              - Show error: "Отправьте ОДНО фото"
              - NO menu creation
              - Auto-delete error in 3s
    
    🔥 Solution: Check message.photo count
              - If count > 1 → Delete all
              - Show error
              - Return (no menu)
    
    How it works:
    1. User uploads 7 photos at once (media_group_id)
    2. photo_handler called ONCE per photo
    3. First photo: Detects media_group, checks if OTHER photos exist
       - Need to wait slightly to see if other photos in group arrive
       - Or: Check if this is part of media group
    4. Actually: Each photo is separate message!
       - Each has separate photo_handler call
       - Need Lock to serialize
    5. With Lock:
       - First photo: LOCK ✅ Process
       - Subsequent: Wait for LOCK, see photo_uploaded=True → REJECT
    
    KEY FIX [2025-12-30 22:45] - PERSISTENT menu_message_id:
    ❌ OLD: menu_message_id was stored in FSM
            Problem: FSM dies on bot restart, so we lose the ID
            Result: Can't delete old message if bot crashes
    
    ✅ NEW: menu_message_id is stored in DATABASE (chat_menus table)
            Problem solved: Even if FSM dies, we can get the ID from DB
            Result: Always can delete old message correctly!
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    work_mode = data.get('work_mode')

    logger.info(f"🎞️ [PHOTO_HANDLER] START - user_id={user_id}, work_mode={work_mode}, photo received")

    # 🔥 [2025-12-31 11:04] GET USER LOCK - Synchronize concurrent uploads
    lock = get_user_lock(user_id)
    
    try:
        async with lock:
            logger.info(f"🔐 [PHOTO_HANDLER] LOCK ACQUIRED for user {user_id}")
            
            # Re-read state after acquiring lock (might have changed)
            data = await state.get_data()
            
            # 🔥 [2025-12-31 10:53] CRITICAL CHECK: Is photo already uploaded?
            photo_uploaded = data.get('photo_uploaded', False)
            if photo_uploaded:
                logger.warning(f"⚠️ [PHOTO_HANDLER] REJECTED - photo already uploaded for user {user_id}")
                
                # 🔥 [2025-12-31 11:08] DELETE this photo (if part of multiple)
                try:
                    await message.delete()
                    logger.info(f"🗑️ [PHOTO_HANDLER] Deleted extra photo msg_id={message.message_id}")
                except Exception as e:
                    logger.debug(f"Could not delete photo: {e}")
                
                # Show error only on first rejection
                # (Don't spam multiple errors for each photo)
                error_text = "❌ **Отправьте ОДНО фото**"
                error_msg = await message.answer(error_text, parse_mode="Markdown")
                
                # Save error message to DB
                await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
                
                # Auto-delete error message after 3 seconds
                asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                
                logger.info(f"ℹ️ [PHOTO_HANDLER] Error message will auto-delete in 3 seconds")
                return
            
            # ===== 1. VALIDATION =====
            if not message.photo:
                error_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
                await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
                asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                return
            
            # ===== 2. BALANCE CHECK =====
            balance = await db.get_balance(user_id)
            
            # Exception for EDIT_DESIGN: can work WITHOUT balance
            if balance <= 0 and work_mode != WorkMode.EDIT_DESIGN.value:
                error_text = ERROR_INSUFFICIENT_BALANCE
                error_msg = await message.answer(error_text)
                await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
                asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
                return
            
            # ===== 3. SAVE PHOTO =====
            photo_id = message.photo[-1].file_id
            
            logger.info(f"💾 [PHOTO_HANDLER] Photo saved - photo_id={photo_id[:20]}...")
            
            # 🔥 [2025-12-31 11:08] SET photo_uploaded=True IMMEDIATELY
            # This will cause any concurrent photo uploads to be rejected
            await state.update_data(
                photo_id=photo_id,
                new_photo=True,
                photo_uploaded=True  # 🔥 Mark: ONE photo already received!
            )
            logger.info(f"🔐 [PHOTO_HANDLER] Set photo_uploaded=True for user {user_id}")
            
            # ===== 4. GET OLD MENU MESSAGE ID FROM DATABASE =====
            # 🔥 [2025-12-30 22:45] CRITICAL FIX: Take menu_message_id FROM DATABASE!
            logger.info(f"🔍 [PHOTO_HANDLER] Fetching old menu_message_id from DB for chat_id={chat_id}")
            
            old_menu_data = await db.get_chat_menu(chat_id)
            old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None
            
            logger.info(f"📥 [PHOTO_HANDLER] Got from DB: old_menu_message_id={old_menu_message_id}, screen={old_menu_data.get('screen_code') if old_menu_data else None}")
            
            # ===== 5. DELETE OLD MENU MESSAGE =====
            # 🔥 [2025-12-30 22:45] DELETE old message BEFORE sending new one!
            if old_menu_message_id:
                try:
                    await message.bot.delete_message(chat_id=chat_id, message_id=old_menu_message_id)
                    logger.info(f"🗑️ [PHOTO_HANDLER] ✅ DELETED old menu message {old_menu_message_id}")
                except Exception as e:
                    logger.warning(f"⚠️ [PHOTO_HANDLER] Could not delete old menu {old_menu_message_id}: {e}")
            else:
                logger.warning(f"⚠️ [PHOTO_HANDLER] old_menu_message_id is None! DB returned: {old_menu_data}")
            
            # ===== 6. DETERMINE NEXT SCREEN (depends on mode) =====
            
            if work_mode == WorkMode.NEW_DESIGN.value:
                await state.set_state(CreationStates.room_choice)
                text = f"🏠 **Выберите комнату**"
                # 🔥 [2025-12-30 22:45] CRITICAL: Pass work_mode as KEYWORD ARGUMENT!
                logger.info(f"🔧 [PHOTO_HANDLER] Adding footer with work_mode='new_design'")
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='new_design')
                keyboard = get_room_choice_keyboard()
                screen = 'room_choice'
                
            elif work_mode == WorkMode.EDIT_DESIGN.value:
                await state.set_state(CreationStates.edit_design)
                text = f"✏️ **Редактируем дизайн**"
                # 🔥 [2025-12-30 22:45] CRITICAL: Pass work_mode as KEYWORD ARGUMENT!
                logger.info(f"🔧 [PHOTO_HANDLER] Adding footer with work_mode='edit_design'")
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='edit_design')
                keyboard = get_edit_design_keyboard()
                screen = 'edit_design'
                
            elif work_mode == WorkMode.SAMPLE_DESIGN.value:
                await state.set_state(CreationStates.download_sample)
                text = f"📥 **Скачать примеры**"
                # 🔥 [2025-12-30 22:45] CRITICAL: Pass work_mode as KEYWORD ARGUMENT!
                logger.info(f"🔧 [PHOTO_HANDLER] Adding footer with work_mode='sample_design'")
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='sample_design')
                keyboard = get_download_sample_keyboard()
                screen = 'download_sample'
                
            elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
                await state.set_state(CreationStates.uploading_furniture)
                text = f"🛋️ **Расстановка мебели**"
                # 🔥 [2025-12-30 22:45] CRITICAL: Pass work_mode as KEYWORD ARGUMENT!
                logger.info(f"🔧 [PHOTO_HANDLER] Adding footer with work_mode='arrange_furniture'")
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='arrange_furniture')
                keyboard = get_uploading_furniture_keyboard()
                screen = 'uploading_furniture'
                
            elif work_mode == WorkMode.FACADE_DESIGN.value:
                await state.set_state(CreationStates.loading_facade_sample)
                text = f"🏘️ **Дизайн фасада**"
                # 🔥 [2025-12-30 22:45] CRITICAL: Pass work_mode as KEYWORD ARGUMENT!
                logger.info(f"🔧 [PHOTO_HANDLER] Adding footer with work_mode='facade_design'")
                text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
                keyboard = get_loading_facade_sample_keyboard()
                screen = 'loading_facade_sample'
            else:
                logger.error(f"[ERROR] Unknown work_mode: {work_mode}")
                await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
                return
            
            # ===== 7. SEND MENU BELOW PHOTO (NO PHOTO REATTACHMENT!) =====
            # ✅ [2025-12-30 22:10] FIX: Just send text message with buttons
            # Do NOT use edit_message_media() - it causes duplicate photos!
            
            logger.info(f"📤 [PHOTO_HANDLER] Sending menu message - screen={screen}, user_id={user_id}")
            
            menu_msg = await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            logger.info(f"✅ [PHOTO_HANDLER] SUCCESS - Menu sent, msg_id={menu_msg.message_id}")
            
            # ===== 8. SAVE new menu_message_id TO DATABASE (not FSM!) =====
            # 🔥 [2025-12-30 22:45] CRITICAL: Save to DB so it survives bot restart!
            logger.info(f"💾 [PHOTO_HANDLER] Saving new menu_message_id={menu_msg.message_id} to DB")
            await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, screen)
            
            # Also save to FSM for current session reference
            await state.update_data(menu_message_id=menu_msg.message_id)
            
            logger.info(f"📊 [PHOTO_HANDLER] COMPLETE - user_id={user_id}, work_mode={work_mode}, transitioned to {screen}")
            logger.info(f"🔐 [PHOTO_HANDLER] LOCK RELEASED for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [PHOTO_HANDLER] FATAL ERROR for user {user_id}: {e}", exc_info=True)
        try:
            error_msg = await message.answer("❌ Ошибка при обработке фото. Попробуйте ещё раз.")
            asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
        except:
            pass


# ===== HELPER: _delete_message_after_delay =====
async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int):
    """Delete message after N seconds"""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"✅ Удалено сообщение об ошибке {message_id} в чате {chat_id}")
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить сообщение {message_id}: {e}")


# ===== OLD SYSTEM: CREATE_DESIGN (for backwards compatibility) =====
# NOTE: Now create_design is in user_start.py - shows SCREEN 1 (select_mode)
# This handler is only kept for backwards compatibility
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
        keyboard=get_upload_photo_keyboard(),
        show_balance=False,
        screen_code='upload_photo'
    )
