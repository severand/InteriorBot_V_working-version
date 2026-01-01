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
    get_work_mode_selection_keyboard,
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

# 🔥 [2025-12-31 15:06] Tracking альбомов для параллельного удаления
# Structure: {user_id: {media_group_id: {'message_ids': [7435, 7436, 7437], 'collected': True}}}
media_group_cache = {}


async def collect_all_media_group_photos(user_id: int, media_group_id: str, message_id: int):
    """
    🔥 [2025-12-31 15:06] СОБРАТЬ ВСЕ ФОТО АЛЬБОМА ЗА 1 СЕКУНДУ
    
    Когда приходит первое фото:
    1. Регистрируем его
    2. ЖДЁМ 1000мс
    3. За это время приходят ВСЕ остальные фото
    4. Возвращаем ВСЕ message_ids
    
    Все остальные handlers видят что уже collected=True → выходят
    """
    if user_id not in media_group_cache:
        media_group_cache[user_id] = {}
    
    # Если первое фото - создаём запись
    if media_group_id not in media_group_cache[user_id]:
        media_group_cache[user_id][media_group_id] = {
            'message_ids': [message_id],
            'collected': False
        }
        logger.info(f"📸 [COLLECT] user={user_id}, group={media_group_id}, photo #1 registered")
        
        # ЖДЁМ 1 СЕКУНДУ для прихода остальных фото
        await asyncio.sleep(1.0)
        
        # Помечаем что собрали
        media_group_cache[user_id][media_group_id]['collected'] = True
        
        final_ids = media_group_cache[user_id][media_group_id]['message_ids'].copy()
        logger.info(f"📸 [COLLECT] user={user_id}, group={media_group_id}, COLLECTED {len(final_ids)} photos")
        return final_ids
    else:
        # Если уже идёт сбор - добавляем фото к существующему
        if not media_group_cache[user_id][media_group_id]['collected']:
            media_group_cache[user_id][media_group_id]['message_ids'].append(message_id)
            count = len(media_group_cache[user_id][media_group_id]['message_ids'])
            logger.info(f"📸 [COLLECT] user={user_id}, group={media_group_id}, photo #{count} added")
        
        return None  # Не первое фото - не нужно собирать


# ===== SCREEN 0: MAIN MENU =====
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Return to main menu"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'main_menu')
    await show_main_menu(callback, state, admins)
    await callback.answer()


# ===== SCREEN 1: SELECT_MODE (Work mode selection) =====
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
        mode_str = callback.data.replace("select_mode_", "")
        
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
        
        await state.update_data(
            work_mode=work_mode.value,
            photo_uploaded=False
        )
        await state.set_state(CreationStates.uploading_photo)
        
        text = UPLOADING_PHOTO_TEMPLATES.get(work_mode.value, "📄 Загрузите фото")
        
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
    
    [2025-12-31 15:06] 🔥 УДАЛЯЕМ ВСЕ ФОТО АЛЬБОМА ОДНОВРЕМЕННО!
    
    ЛОГИКА:
    1. Фото приходит → если media_group_id:
       - Собираем ВСЕ фото за 1сек
       - УДАЛЯЕМ ВСЕ ОДНОВРЕМЕННО (параллельно)
       - RETURN (не показываем ничего)
    2. Если одиночное фото → обрабатываем нормально
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 🔥 [2025-12-31 15:06] АЛЬБОМ - УДАЛИТЬ ВСЕ ФОТО
    if message.media_group_id:
        logger.info(f"📸 [ALBUM] Detected media_group_id={message.media_group_id}")
        
        # СОБРАТЬ ВСЕ ФОТО за 1сек
        collected_ids = await collect_all_media_group_photos(
            user_id,
            message.media_group_id,
            message.message_id
        )
        
        # Если это ПЕРВОЕ фото в альбоме - collected_ids будут
        if collected_ids:
            logger.warning(f"❌ ALBUM with {len(collected_ids)} photos detected!")
            
            # 🔥 УДАЛИТЬ ВСЕ ФОТО ОДНОВРЕМЕННО (параллельно)
            delete_tasks = []
            for msg_id in collected_ids:
                delete_tasks.append(
                    message.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                )
            
            # Жди пока все удалятся
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"🗑️ [DELETE] Deleted {success_count}/{len(collected_ids)} photos")
        
        # ВЫХОД - не обрабатываем альбом дальше
        return
    
    # 🔥 ОДИНОЧНОЕ ФОТО - обрабатываем нормально
    logger.info(f"📸 [SINGLE] Single photo detected")
    
    data = await state.get_data()
    work_mode = data.get('work_mode')
    
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
            logger.debug(f"⚠️ Could not delete old menu: {e}")
    
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
