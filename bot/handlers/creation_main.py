# bot/handlers/creation_main.py
# ===== PHASE 1: MAIN ENTRY POINT + PHOTO UPLOAD =====
# [2025-12-29] НОВЫЙ ФАЙЛ: Часть 1 рефакторинга creation.py
# Содержит: select_mode (SCREEN 1), set_work_mode, photo_handler (SCREEN 2)
# + старые handlers для обратной совместимости (what_is_in_photo)
# [2025-12-29 21:18] Исправлены вызовы add_balance_and_mode_to_text - удален work_mode
# [2025-12-29 22:30] HOTFIX: Исправлена функция select_mode() - передан параметр current_mode_is_pro
# [2025-12-29 22:55] FIX: Исправлена логика главного меню - select_mode теперь показывает 5 режимов
# [2025-12-29 23:10] FIX: Убрано дублирование footer на экране выбора режима работы
# [2025-12-29 23:14] FIX: Убрано дублирование footer на экране загружения фото - НЕ добавляем footer для UPLOADING_PHOTO
# [2025-12-29 23:24] CRITICAL FIX: сохраняем menu_message_id в FSM state не только в БД - теперь photo_handler получит menu_message_id из FSM
# [2025-12-29 23:35] FIX: удаляем несуществующий вызов db.save_photo() - фото сохраняется через FSM state
# [2025-12-29 23:40] FIX: добавляем автоматическое удаление сообщений об ошибке через 3 сек + улучшена обработка ошибок при редактировании меню
# [2025-12-29 23:45] CRITICAL FIX: НЕ УДАЛЯЕМ ФОТО! Оно остается в чате и будет редактироваться через edit_message_media()
# [2025-12-30 00:05] BUGFIX: ФОТО ДОЛЖНО БЫТЬ НАД МЕНЮ! Отправляем фото ДО меню с кнопками
# [2025-12-30 00:17] CRITICAL FIX: Удалено дублирование отправки фото - использу edit_message_media()
# [2025-12-30 00:38] CRITICAL FIX: Восстановлена edit_menu() для работы кнопок - edit_menu() генерирует ТОЛЬКО edit_message_text
# [2025-12-30 00:45] 🔍 DEBUG: Добавлено ДЕТАЛЬНОЕ логирование отправки фото для поиска источника дубликата
# [2025-12-30 16:35] НОВЫЙ FIX: Поснавляно единственно create_design в user_start.py – теперь SCREEN 1 от там
# [2025-12-30 15:29] 🔧 BUGFIX: Удалена вызов edit_menu() из set_work_mode() - это вызывало дублирование фото
# [2025-12-30 15:37] 🔧 HOTFIX: Восстановлена edit_menu() в set_work_mode() - для обновления экрана пользователя
# [2025-12-30 15:47] 🔴 CRITICAL BUG FOUND: edit_menu() в set_work_mode() создает ДВЕ фотки!
#   ПРОБЛЕМА: edit_menu() -> edit_message_text() обновляет текст
#             photo_handler() -> edit_message_media() добавляет фото
#             Telegram показывает ОБА - в одном сообщении!
#   РЕШЕНИЕ: НЕ вызываем edit_menu() - photo_handler() сам создаст сообщение с фото + кнопками
#   РЕЗУЛЬТАТ: Одна фотография, кнопки прикреплены к ней (как и показано на скрине)

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
# [2025-12-30 15:47] 🔴 CRITICAL FIX: НЕ вызываем edit_menu()!
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
    
    CRITICAL FIX: [2025-12-30 15:47]
    - REMOVED edit_menu() call - это вызывало двойное редактирование фото!
    - photo_handler() сам создаст сообщение с фото + кнопками
    
    Why this works:
    1. set_work_mode() saves mode to FSM state ✅
    2. photo_handler() will create NEW message with photo + buttons ✅
    3. Result: ONE message with photo and buttons (как на скрине) ✅
    
    Why it was broken before:
    1. Old code called edit_menu() - редактировало текст
    2. photo_handler() called edit_message_media() - добавляло фото
    3. Telegram показывал обе версии - одно за другим!
    4. Решение: photo_handler() создает НОВОЕ сообщение с фото + кнопками
    
    CRITICAL FIX: [2025-12-29 23:24]
    - Save menu_message_id IN FSM state (in addition to DB)
    - Then photo_handler can get menu_message_id from FSM
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id  # Get menu ID

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
        
        # ✅ Save state for photo_handler
        await state.update_data(
            work_mode=work_mode.value,
            menu_message_id=menu_message_id  # SAVE for photo_handler
        )
        await state.set_state(CreationStates.uploading_photo)
        
        # ❌ REMOVED: edit_menu() call - это вызывало дублирование фото!
        # photo_handler() сам создаст сообщение с фото + кнопками
        
        # Also save to DB (backup)
        await db.save_chat_menu(
            chat_id,
            user_id,
            menu_message_id,
            'uploading_photo'
        )
        
        logger.info(f"[V3] {work_mode.value.upper()}+MODE_SELECTED - mode saved to FSM, user_id={user_id}, awaiting photo...")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SET_WORK_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе режима", show_alert=True)


# ===== SCREEN 2: PHOTO_HANDLER (Photo upload for all modes) =====
# [2025-12-29] UPDATED (V3)
# [2025-12-30 00:05] BUGFIX: send photo BEFORE menu with buttons (correct order)
# [2025-12-30 00:17] CRITICAL FIX: Removed double photo send - use edit_message_media()
# [2025-12-30 00:38] CRITICAL FIX: Restored edit_menu() - photo_handler adds photo via edit_message_media()
# [2025-12-30 00:45] 🔍 DEBUG: Added DETAILED photo send logging for tracking duplication source
# [2025-12-30 15:47] 🔴 CRITICAL: Теперь photo_handler() СОЗДАЕТ новое сообщение с фото + кнопками!
@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """
    SCREEN 2: Photo upload (UPLOADING_PHOTO)
    
    Logic:
    1. Photo validation
    2. Balance check (except EDIT_DESIGN)
    3. Save file_id in FSM and DB
    4. CREATE NEW MESSAGE with photo + buttons
       (Replaces old text-only menu message)
    5. Transition to NEXT screen (depends on mode):
       - NEW_DESIGN → ROOM_CHOICE
       - EDIT_DESIGN → EDIT_DESIGN
       - SAMPLE_DESIGN → DOWNLOAD_SAMPLE
       - ARRANGE_FURNITURE → UPLOADING_FURNITURE
       - FACADE_DESIGN → LOADING_FACADE_SAMPLE
    
    KEY CHANGE [2025-12-30 15:47]:
    - Раньше: set_work_mode() -> edit_menu() -> photo_handler() -> edit_message_media()
      Результат: ДВЕ фотографии (одна в старом сообщении, одна в новом)
    - Теперь: set_work_mode() -> (no edit_menu) -> photo_handler() -> send_photo() + кнопки
      Результат: ОДНА фотография с кнопками (как на скрине)
    
    CRITICAL FIX: [2025-12-29 23:24]
    - Get menu_message_id FROM FSM state
    - Now photo will be processed correctly
    
    FIX: [2025-12-29 23:35]
    - REMOVED db.save_photo() call - method doesn't exist
    - Photo saved via FSM state
    
    FIX: [2025-12-29 23:40]
    - Auto-delete error messages after 3 sec
    - Improved error handling on menu edit
    
    CRITICAL FIX: [2025-12-30 00:17]
    - Use edit_message_media() to add photo to existing menu
    - Photo and buttons now in ONE message
    
    DEBUG FIX: [2025-12-30 00:45]
    - DETAILED logs for tracking photo send
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    work_mode = data.get('work_mode')
    menu_message_id = data.get('menu_message_id')  # GET FROM FSM ✅

    logger.info(f"🎞️ [PHOTO_HANDLER] START - user_id={user_id}, work_mode={work_mode}, menu_id={menu_message_id}")

    try:
        # ===== 1. VALIDATION =====
        if not message.photo:
            error_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
            await state.update_data(menu_message_id=error_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
            # ✅ NEW: Delete error message after 3 sec
            asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
            return
        
        # ===== 2. BALANCE CHECK =====
        balance = await db.get_balance(user_id)
        
        # Exception for EDIT_DESIGN: can work WITHOUT balance
        if balance <= 0 and work_mode != WorkMode.EDIT_DESIGN.value:
            error_text = ERROR_INSUFFICIENT_BALANCE
            error_msg = await message.answer(error_text)
            await state.update_data(menu_message_id=error_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
            # ✅ NEW: Delete error message after 3 sec
            asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
            return
        
        # ===== 3. SAVE PHOTO =====
        photo_id = message.photo[-1].file_id
        
        logger.info(f"💾 [PHOTO_HANDLER] Saving photo_id={photo_id[:20]}... to FSM state")
        
        # ✅ FIXED: Removed db.save_photo() call - method doesn't exist
        # Photo saved via FSM state:
        
        await state.update_data(
            photo_id=photo_id,
            new_photo=True
        )
        
        # ===== 4. DETERMINE NEXT SCREEN (depends on mode) =====
        
        if work_mode == WorkMode.NEW_DESIGN.value:
            # NEW_DESIGN → ROOM_CHOICE (SCREEN 3)
            await state.set_state(CreationStates.room_choice)
            text = f"🏠 **Выберите комнату**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_room_choice_keyboard()
            screen = 'room_choice'
            
        elif work_mode == WorkMode.EDIT_DESIGN.value:
            # EDIT_DESIGN → EDIT_DESIGN (SCREEN 8)
            await state.set_state(CreationStates.edit_design)
            text = f"✏️ **Редактируем дизайн**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_edit_design_keyboard()
            screen = 'edit_design'
            
        elif work_mode == WorkMode.SAMPLE_DESIGN.value:
            # SAMPLE_DESIGN → DOWNLOAD_SAMPLE (SCREEN 10)
            await state.set_state(CreationStates.download_sample)
            text = f"📥 **Скачать примеры**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_download_sample_keyboard()
            screen = 'download_sample'
            
        elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
            # ARRANGE_FURNITURE → UPLOADING_FURNITURE (SCREEN 13)
            await state.set_state(CreationStates.uploading_furniture)
            text = f"🛋️ **Расстановка мебели**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_uploading_furniture_keyboard()
            screen = 'uploading_furniture'
            
        elif work_mode == WorkMode.FACADE_DESIGN.value:
            # FACADE_DESIGN → LOADING_FACADE_SAMPLE (SCREEN 16)
            await state.set_state(CreationStates.loading_facade_sample)
            text = f"🏘️ **Дизайн фасада**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_loading_facade_sample_keyboard()
            screen = 'loading_facade_sample'
        else:
            logger.error(f"[ERROR] Unknown work_mode: {work_mode}")
            await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
            return
        
        # ===== 5. CREATE NEW MESSAGE WITH PHOTO + BUTTONS =====
        # 🔴 CRITICAL CHANGE [2025-12-30 15:47]
        # CREATES NEW MESSAGE instead of editing old one
        # This prevents double photos!
        
        logger.info(f"📸 [PHOTO_HANDLER] CREATING NEW MESSAGE with photo + buttons - screen={screen}")
        
        # Send NEW message with photo + buttons
        new_msg = await message.bot.send_photo(
            chat_id=chat_id,
            photo=photo_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ [PHOTO_HANDLER] NEW MESSAGE CREATED - msg_id={new_msg.message_id}, screen={screen}")
        
        # Update FSM state with new message ID
        await state.update_data(menu_message_id=new_msg.message_id)
        
        # Save to DB
        await db.save_chat_menu(chat_id, user_id, new_msg.message_id, screen)
        
        # Delete old text-only message (optional - Telegram will auto-archive it)
        if menu_message_id:
            try:
                await message.bot.delete_message(chat_id=chat_id, message_id=menu_message_id)
                logger.info(f"🗑️ [PHOTO_HANDLER] Deleted old menu message {menu_message_id}")
            except Exception as e:
                logger.debug(f"⚠️ Could not delete old menu message {menu_message_id}: {e}")
        
        logger.info(f"📊 [PHOTO_HANDLER] COMPLETE - user_id={user_id}, work_mode={work_mode}, transitioned to {screen}")
        
    except Exception as e:
        logger.error(f"❌ [PHOTO_HANDLER] FATAL ERROR for user {user_id}: {e}", exc_info=True)
        try:
            error_msg = await message.answer("❌ Ошибка при обработке фото. Попробуйте ещё раз.")
            # ✅ NEW: Delete error message after 3 sec
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
