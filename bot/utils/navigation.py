"""
Утилиты для навигации с единым меню.
Все переходы между экранами происходят через редактирование одного сообщения.
Система работает даже после перезапуска бота благодаря сохранению в БД.

RESOLUTIONS
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
    parse_mode: str = "HTML",       # "Markdown",
    show_balance: bool = True,
    screen_code: str = 'main_menu'
) -> bool:
    """
    🔥 [2026-01-02 21:24] CRITICAL BUG FIX:
    
    Универсальная функция редактирования единого меню (FSM + БД).
    
    📈 ПРОБЛЕМА:
    - Старое новые callback_query салораждали текущие message_id ис бд
    - По перезагрузке старые сообщения могут быть удалены в Телеграмме
    - Мы используем старые ID из БД голаъ = "message not found"
    
    🔥 РЕШЕНИЕ:
    - ДЛЯ callback.message ВСЕГДА используем callback.message.message_id
    - НИКОГДА не лоадим старые ID из БД!
    - Каждые callback над до АГНОМ сразу работают с новым message_id
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # Добавляем баланс + режим при необходимости
    if show_balance:
        text = await add_balance_and_mode_to_text(text, user_id)

    # 🔥 CRITICAL: ОБЫЧНО используем куррентные ID
    # callback.message.message_id это куррентное сообщение
    # НЕ лоадим старые message_id из БД!
    
    menu_message_id = callback.message.message_id
    logger.info(f"📄 [EDIT_MENU] Using callback.message.message_id={menu_message_id} (current message)")

    # Обновляем FSM
    await state.update_data(menu_message_id=menu_message_id)

    # Пытаемся редактировать
    try:
        logger.info(f"📃 [EDIT_MENU] Attempting edit_message_text for msg_id={menu_message_id}, chat={chat_id}")
        
        await callback.message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        
        # Сохраняем текущие параметры в БД
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
            logger.info(f"📇 [EDIT_MENU] Message has media, attempting edit_message_caption for msg_id={menu_message_id}")
            
            try:
                await callback.message.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode
                )
                await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)
                logger.info(f"✅ [EDIT_MENU] Successfully edited caption for msg_id={menu_message_id}")
                return True
            except Exception as e_cap:
                logger.warning(f"⚠️ [EDIT_MENU] Failed edit_message_caption for msg_id={menu_message_id}: {e_cap}")
        
        logger.warning(f"⚠️ [EDIT_MENU] Failed to edit msg_id={menu_message_id}: {e}")

    except Exception as e:
        logger.error(f"[EDIT_MENU] Unexpected error editing msg_id={menu_message_id}: {e}")

    # ХОЛОДНАЯ ПОМОЩЬ — сохраняем текущие данные
    logger.info(f"📈 [EDIT_MENU] Saved current message state to DB (msg_id={menu_message_id}, screen={screen_code})")
    await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)
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
    Положение: только message.answer для текстовых сообщений.
    """
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Пытаемся восстановить из ФСМ
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    # При необходимости – от БД
    if not menu_message_id:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info:
            menu_message_id = menu_info['menu_message_id']
            await state.update_data(menu_message_id=menu_message_id)
            logger.info(f"📃 [UPDATE_AFTER_PHOTO] Restored menu_id={menu_message_id} from DB")

    if not menu_message_id:
        logger.warning(f"[UPDATE_AFTER_PHOTO] Menu ID not found for user {user_id}")
        return False

    try:
        logger.info(f"📃 [UPDATE_AFTER_PHOTO] Attempting edit_message_text for msg_id={menu_message_id}")
        
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
            logger.info(f"📇 [UPDATE_AFTER_PHOTO] Message has media, attempting edit_message_caption")
            
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
