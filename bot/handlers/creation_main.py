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
# [2025-12-30 15:47] 🔴 CRITICAL BUG FOUND: edit_menu() в set_work_mode() создает ДВЕ фотки
# [2025-12-30 15:52] 🔧 FINAL FIX: Восстановлена edit_menu() БОЛЬШОЕ ЧЕМ двое! Но бережно - ТОЛЬКО редактируем ТЕКСТ, photo_handler() добавит фотку!
# [2025-12-30 22:10] 🔴 CRITICAL: DOUBLE PHOTO BUG FIX - edit_message_media() was reattaching photo! Now just send menu below user's photo

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
# [2025-12-30 15:52] 🔧 FINAL FIX: Восстановлена edit_menu() - НО ТОЛЬКО ТЕКСТ!
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
    
    CRITICAL FIX: [2025-12-29 23:24]
    - Save menu_message_id IN FSM state
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
        
        # Save state for photo_handler
        await state.update_data(
            work_mode=work_mode.value,
            menu_message_id=menu_message_id
        )
        await state.set_state(CreationStates.uploading_photo)
        
        # ✅ RESTORED [2025-12-30 15:52]: Обновить SCREEN для пользователя
        # edit_menu() редактирует ТОЛЬКО ТЕКСТ - photo_handler() добавит фото!
        text = UPLOADING_PHOTO_TEMPLATES.get(work_mode.value, "📄 Загрузите фото")
        text = await add_balance_and_mode_to_text(text, user_id)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_upload_photo_keyboard(),
            show_balance=False,
            screen_code='uploading_photo'
        )
        
        # Also save to DB
        await db.save_chat_menu(
            chat_id,
            user_id,
            menu_message_id,
            'uploading_photo'
        )
        
        logger.info(f"[V3] {work_mode.value.upper()}+MODE_SELECTED - screen updated for user {user_id}, menu_id={menu_message_id}, awaiting photo...")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SET_WORK_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе режима", show_alert=True)


# ===== SCREEN 2: PHOTO_HANDLER (Photo upload for all modes) =====
# [2025-12-29] UPDATED (V3)
# [2025-12-30 22:10] 🔴 CRITICAL FIX: Remove edit_message_media() that was creating DOUBLE photo!
#                     Now just send menu text with buttons BELOW user's uploaded photo
@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """
    SCREEN 2: Photo upload (UPLOADING_PHOTO)
    
    Logic:
    1. Photo validation
    2. Balance check (except EDIT_DESIGN)
    3. Save file_id in FSM
    4. Send NEW message with text + buttons BELOW the photo user uploaded
       (Do NOT reattach photo to existing message - this creates duplicates!)
    5. Transition to NEXT screen (depends on mode):
       - NEW_DESIGN → ROOM_CHOICE
       - EDIT_DESIGN → EDIT_DESIGN
       - SAMPLE_DESIGN → DOWNLOAD_SAMPLE
       - ARRANGE_FURNITURE → UPLOADING_FURNITURE
       - FACADE_DESIGN → LOADING_FACADE_SAMPLE
    
    KEY FIX [2025-12-30 22:10] - DOUBLE PHOTO BUG:
    ❌ OLD LOGIC: edit_message_media() tried to attach photo to menu message
                  This caused: photo1 (user) + photo2 (attached) = DOUBLE PHOTO!
    
    ✅ NEW LOGIC: Just send a NEW text message with buttons BELOW the photo
                  User's photo stays clean
                  Menu buttons appear as separate message
                  NO DUPLICATES!
    
    CRITICAL FIX: [2025-12-29 23:24]
    - Save menu_message_id IN FSM state for future reference
    
    FIX: [2025-12-29 23:35]
    - REMOVED db.save_photo() call - method doesn't exist
    - Photo saved via FSM state
    
    FIX: [2025-12-29 23:40]
    - Auto-delete error messages after 3 sec
    - Improved error handling
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    work_mode = data.get('work_mode')

    logger.info(f"🎞️ [PHOTO_HANDLER] START - user_id={user_id}, work_mode={work_mode}, photo received")

    try:
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
        
        await state.update_data(
            photo_id=photo_id,
            new_photo=True
        )
        
        # ===== 4. DETERMINE NEXT SCREEN (depends on mode) =====
        
        if work_mode == WorkMode.NEW_DESIGN.value:
            await state.set_state(CreationStates.room_choice)
            text = f"🏠 **Выберите комнату**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_room_choice_keyboard()
            screen = 'room_choice'
            
        elif work_mode == WorkMode.EDIT_DESIGN.value:
            await state.set_state(CreationStates.edit_design)
            text = f"✏️ **Редактируем дизайн**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_edit_design_keyboard()
            screen = 'edit_design'
            
        elif work_mode == WorkMode.SAMPLE_DESIGN.value:
            await state.set_state(CreationStates.download_sample)
            text = f"📥 **Скачать примеры**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_download_sample_keyboard()
            screen = 'download_sample'
            
        elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
            await state.set_state(CreationStates.uploading_furniture)
            text = f"🛋️ **Расстановка мебели**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_uploading_furniture_keyboard()
            screen = 'uploading_furniture'
            
        elif work_mode == WorkMode.FACADE_DESIGN.value:
            await state.set_state(CreationStates.loading_facade_sample)
            text = f"🏘️ **Дизайн фасада**"
            text = await add_balance_and_mode_to_text(text, user_id)
            keyboard = get_loading_facade_sample_keyboard()
            screen = 'loading_facade_sample'
        else:
            logger.error(f"[ERROR] Unknown work_mode: {work_mode}")
            await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
            return
        
        # ===== 5. SEND MENU BELOW PHOTO (NO PHOTO REATTACHMENT!) =====
        # ✅ [2025-12-30 22:10] FIX: Just send text message with buttons
        # Do NOT use edit_message_media() - it causes duplicate photos!
        
        logger.info(f"📤 [PHOTO_HANDLER] Sending menu message - screen={screen}, user_id={user_id}")
        
        menu_msg = await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ [PHOTO_HANDLER] SUCCESS - Menu sent, msg_id={menu_msg.message_id}")
        
        # Save menu message ID to FSM and DB
        await state.update_data(menu_message_id=menu_msg.message_id)
        await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, screen)
        
        logger.info(f"📊 [PHOTO_HANDLER] COMPLETE - user_id={user_id}, work_mode={work_mode}, transitioned to {screen}")
        
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
