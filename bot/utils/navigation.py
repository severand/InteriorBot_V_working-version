# bot/utils/navigation.py
"""
Утилиты для навигации с единым меню.
Все переходы между экранами происходят через редактирование одного сообщения.
"""

import logging
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from utils.texts import START_TEXT  # ← ДОБАВЬ ИМПОРТ
from keyboards.inline import get_main_menu_keyboard


logger = logging.getLogger(__name__)

async def edit_menu(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown"
) -> bool:
    """
    Универсальная функция редактирования единого меню.
    Всегда редактирует ОДНО сообщение - никаких новых сообщений.
    
    Args:
        callback: CallbackQuery объект
        state: FSMContext для получения menu_message_id
        text: Новый текст сообщения
        keyboard: Новая клавиатура (может быть None)
        parse_mode: Режим парсинга (по умолчанию Markdown)
    
    Returns:
        bool: True если успешно отредактировано, False если создано новое
    """
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    if not menu_message_id:
        # Fallback: если ID потерян, создаем новое и сохраняем
        logger.warning(f"Menu message ID lost for user {callback.from_user.id}, creating new message")
        new_msg = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        await state.update_data(menu_message_id=new_msg.message_id)
        return False
    
    try:
        # Основной путь: редактируем существующее сообщение
        await callback.message.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        logger.debug(f"✅ Menu edited successfully (msg_id={menu_message_id})")
        return True
        
    except TelegramBadRequest as e:
        # Если текст не изменился или другая ошибка
        if "message is not modified" in str(e).lower():
            logger.debug(f"Menu text unchanged (msg_id={menu_message_id})")
            return True
        
        logger.error(f"Failed to edit menu message: {e}")
        # Создаем новое сообщение как fallback
        new_msg = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        await state.update_data(menu_message_id=new_msg.message_id)
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error editing menu: {e}")
        return False


async def show_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Показать главное меню.
    Очищает все состояния FSM и возвращает в начальный экран.
    """
    user_id = callback.from_user.id

    # Очищаем все данные, КРОМЕ menu_message_id
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()

    # Восстанавливаем menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    logger.debug(f"🏠 Returning to main menu for user {user_id}")

    await edit_menu(
        callback=callback,
        state=state,
        text=START_TEXT,
        keyboard=get_main_menu_keyboard(is_admin=user_id in admins)
    )


async def update_menu_after_photo(
    message,
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup,
    parse_mode: str = "Markdown"
) -> bool:
    """
    Обновление меню после загрузки фото пользователем.
    Используется в message handlers, а не callback handlers.
    
    Args:
        message: Message объект (сообщение с фото)
        state: FSMContext
        text: Новый текст меню
        keyboard: Новая клавиатура
        parse_mode: Режим парсинга
    
    Returns:
        bool: True если успешно
    """
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    if not menu_message_id:
        logger.warning(f"Menu message ID not found for user {message.from_user.id}")
        return False
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        logger.debug(f"✅ Menu updated after photo upload (msg_id={menu_message_id})")
        return True
        
    except TelegramBadRequest as e:
        logger.error(f"Failed to update menu after photo: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error updating menu: {e}")
        return False




