"""
Утилиты для навигации с единым меню.
Все переходы между экранами происходят через редактирование одного сообщения.
Система работает даже после перезапуска бота благодаря сохранению в БД.
"""

import logging
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from utils.helpers import add_balance_and_mode_to_text
from database.db import db

logger = logging.getLogger(__name__)


async def edit_menu(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown",
    show_balance: bool = True,
    screen_code: str = 'main_menu'
) -> bool:
    """
    Универсальная функция редактирования единого меню (FSM + БД).
    1) Берёт menu_message_id из FSM или БД.
    2) Пытается отредактировать текст; если сообщение — медиа, редактирует caption.
    3) Если не вышло — ЯВНО удаляет старое меню и создаёт новое.
    
    [2025-12-31 10:41] 🔥 CRITICAL FIX:
    - ЯВНО удаляем старое сообщение перед созданием нового
    - Логируем все операции с сообщениями
    - Предотвращаем дублирование сообщений при перезапуске бота
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # Добавляем баланс + режим при необходимости
    if show_balance:
        text = await add_balance_and_mode_to_text(text, user_id)

    # 1. menu_message_id из FSM / БД
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    if not menu_message_id:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info:
            menu_message_id = menu_info['menu_message_id']
            await state.update_data(menu_message_id=menu_message_id)
            logger.info(f"📥 [EDIT_MENU] Restored menu_id={menu_message_id} from DB for chat {chat_id}")
        else:
            logger.debug(f"[EDIT_MENU] No menu found in DB for chat {chat_id}")

    # 2. Пытаемся редактировать
    if menu_message_id:
        try:
            logger.info(f"📝 [EDIT_MENU] Attempting edit_message_text for msg_id={menu_message_id}, chat={chat_id}")
            
            await callback.message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_message_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            
            await state.update_data(menu_message_id=menu_message_id)
            await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)
            logger.info(f"✅ [EDIT_MENU] Successfully edited msg_id={menu_message_id}")
            return True

        except TelegramBadRequest as e:
            err = str(e).lower()
            # Текст не изменился — не считаем за ошибку
            if "message is not modified" in err:
                await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)
                logger.debug(f"[EDIT_MENU] Message not modified (same content)")
                return True
            # Сообщение — медиа, редактируем caption
            if "no text in the message to edit" in err:
                logger.info(f"📷 [EDIT_MENU] Message has media, attempting edit_message_caption for msg_id={menu_message_id}")
                
                try:
                    await callback.message.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=menu_message_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode=parse_mode
                    )
                    await state.update_data(menu_message_id=menu_message_id)
                    await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)
                    logger.info(f"✅ [EDIT_MENU] Successfully edited caption for msg_id={menu_message_id}")
                    return True
                except Exception as e_cap:
                    logger.warning(f"⚠️ [EDIT_MENU] Failed edit_message_caption for msg_id={menu_message_id}: {e_cap}")
            
            logger.warning(f"⚠️ [EDIT_MENU] Failed to edit msg_id={menu_message_id}: {e}")

        except Exception as e:
            logger.error(f"[EDIT_MENU] Unexpected error editing msg_id={menu_message_id}: {e}")

    # 3. FALLBACK — 🔥 ЯВНО удаляем старое меню и создаём новое
    logger.warning(f"🔄 [EDIT_MENU] FALLBACK: Creating new message (old msg_id={menu_message_id})")
    
    # 🔥 [2025-12-31 10:41] CRITICAL: Explicitly delete old message
    if menu_message_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=chat_id,
                message_id=menu_message_id
            )
            logger.info(f"🗑️ [EDIT_MENU] ✅ Deleted old menu message msg_id={menu_message_id}")
        except Exception as e_delete:
            logger.warning(f"⚠️ [EDIT_MENU] Could not delete old msg_id={menu_message_id}: {e_delete}")
            # Continue anyway - we'll create new message and update DB

    # Create new message
    try:
        logger.info(f"📤 [EDIT_MENU] Creating new menu message for user {user_id}")
        
        new_msg = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        
        logger.info(f"✅ [EDIT_MENU] Created new message msg_id={new_msg.message_id}")
        
        # 🔥 [2025-12-31 10:41] Update FSM and DB with NEW message ID
        await state.update_data(menu_message_id=new_msg.message_id)
        await db.save_chat_menu(chat_id, user_id, new_msg.message_id, screen_code)
        
        logger.info(f"💾 [EDIT_MENU] Saved new msg_id={new_msg.message_id} to DB")
        return False
        
    except Exception as e:
        logger.error(f"[EDIT_MENU] Failed to create new message: {e}")
        return False


async def show_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Показать главное меню (SCREEN 0).
    Критично: сохраняет menu_message_id перед любыми действиями.
    """
    from keyboards.inline import get_work_mode_selection_keyboard
    from utils.texts import START_TEXT
    from states.fsm import CreationStates

    user_id = callback.from_user.id

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    # Сбрасываем FSM состояние и ставим selecting_mode
    await state.clear()
    await state.set_state(CreationStates.selecting_mode)

    # Восстанавливаем menu_message_id, если было
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    await edit_menu(
        callback=callback,
        state=state,
        text=START_TEXT,
        keyboard=get_work_mode_selection_keyboard(),
        show_balance=True,
        screen_code='selecting_mode'
    )
    await callback.answer()


async def update_menu_after_photo(
    message: Message,
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup,
    parse_mode: str = "Markdown"
) -> bool:
    """
    Обновление меню после загрузки фото (используется в message handlers).
    Если сообщение — медиа, при ошибке редактируем caption.
    
    [2025-12-31 10:41] 🔥 CRITICAL:
    - Явно удаляет старое сообщение перед созданием нового
    - Логирует все операции
    """
    chat_id = message.chat.id
    user_id = message.from_user.id

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    # Пробуем восстановить из БД
    if not menu_message_id:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info:
            menu_message_id = menu_info['menu_message_id']
            await state.update_data(menu_message_id=menu_message_id)
            logger.info(f"📥 [UPDATE_AFTER_PHOTO] Restored menu_id={menu_message_id} from DB")

    if not menu_message_id:
        logger.warning(f"[UPDATE_AFTER_PHOTO] Menu ID not found for user {user_id}")
        return False

    try:
        logger.info(f"📝 [UPDATE_AFTER_PHOTO] Attempting edit_message_text for msg_id={menu_message_id}")
        
        await message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'photo_uploaded')
        logger.info(f"✅ [UPDATE_AFTER_PHOTO] Successfully edited msg_id={menu_message_id}")
        return True

    except TelegramBadRequest as e:
        err = str(e).lower()
        if "no text in the message to edit" in err:
            # Попробуем редактировать caption
            logger.info(f"📷 [UPDATE_AFTER_PHOTO] Message has media, attempting edit_message_caption")
            
            try:
                await message.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode
                )
                await db.save_chat_menu(chat_id, user_id, menu_message_id, 'photo_uploaded')
                logger.info(f"✅ [UPDATE_AFTER_PHOTO] Successfully edited caption for msg_id={menu_message_id}")
                return True
            except Exception as e_cap:
                logger.error(f"⚠️ [UPDATE_AFTER_PHOTO] Failed to update caption: {e_cap}")
        
        logger.error(f"[UPDATE_AFTER_PHOTO] Failed to update menu: {e}")
        return False

    except Exception as e:
        logger.error(f"[UPDATE_AFTER_PHOTO] Unexpected error: {e}")
        return False
