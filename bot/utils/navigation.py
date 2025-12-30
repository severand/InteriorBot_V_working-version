"""
Утилиты для навигации с единым меню.
Все переходы между экранами происходят через редактирование одного сообщения.
Система работает даже после перезапуска бота благодаря сохранению в БД.
"""

import logging
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from utils.helpers import add_balance_to_text, add_balance_and_mode_to_text
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
    Универсальная функция редактирования единого меню с гибридной логикой (FSM + БД).

    ЛОГИКА РАБОТЫ:
    1. Ищем menu_message_id в FSM state (быстро)
    2. Если нет - ищем в БД (надёжно)
    3. Восстанавливаем в FSM state
    4. Пытаемся отредактировать существующее сообщение
    5. Если получилось - сохраняем в FSM + БД одновременно
    6. Если не получилось - удаляем старое, создаём новое, сохраняем

    Args:
        callback: CallbackQuery объект
        state: FSMContext для получения/сохранения menu_message_id
        text: Новый текст сообщения
        keyboard: Новая клавиатура
        parse_mode: Режим парсинга (по умолчанию Markdown)
        show_balance: Показывать ли баланс и режим (по умолчанию True)
        screen_code: Код текущего экрана для сохранения в БД

    Returns:
        bool: True если успешно отредактировано, False если создано новое
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # [2025-12-24 21:45] ОБНОВЛЕНО: Добавляем баланс И РЕЖИМ к тексту если нужно
    if show_balance:
        text = await add_balance_and_mode_to_text(text, user_id)  # ✅ НОВАЯ ФУНКЦИЯ!

    # ===== ШАГ 1: ПРИОРИТЕТ 1 - FSM (БЫСТРО) =====
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    logger.debug(f"🔍 [EDIT_MENU] Step 1: FSM lookup - menu_id={menu_message_id}")

    # ===== ШАГ 2: ПРИОРИТЕТ 2 - БД (НАДЁНАГО) =====
    if not menu_message_id:
        logger.info(f"📥 [EDIT_MENU] Step 2: FSM empty, checking DB...")
        menu_info = await db.get_chat_menu(chat_id)

        if menu_info:
            menu_message_id = menu_info['menu_message_id']
            logger.info(
                f"📥 [EDIT_MENU] Restored from DB: menu_id={menu_message_id}, screen={menu_info['screen_code']}")

            # ===== ШАГ 3: ВОССТАНАВЛИВАЕМ В FSM =====
            await state.update_data(menu_message_id=menu_message_id)
        else:
            logger.warning(f"⚠️ [EDIT_MENU] No menu found in DB for chat {chat_id}")

    # ===== ШАГ 4: ПЫТАЕМСЯ РЕДАКТИРОВАТЬ =====
    if menu_message_id:
        try:
            await callback.message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_message_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            logger.debug(f"✅ [EDIT_MENU] Step 4: Successfully edited msg_id={menu_message_id}, screen={screen_code}")

            # ===== ШАГ 5: СОХРАНЯЕМ В FSM + БД ОДНОВРЕМЕННО =====
            await state.update_data(menu_message_id=menu_message_id)
            await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)

            return True

        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug(f"ℹ️ [EDIT_MENU] Text unchanged for msg_id={menu_message_id}")
                # Обновляем screen_code даже если текст не изменился
                await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)
                return True

            logger.warning(f"⚠️ [EDIT_MENU] Failed to edit msg_id={menu_message_id}: {e}")
            # Продолжаем к созданию нового сообщения

        except Exception as e:
            logger.error(f"❌ [EDIT_MENU] Unexpected error editing msg_id={menu_message_id}: {e}")

    # ===== ШАГ 6: FALLBACK - СОЗДАЁМ НОВОЕ СООБЩЕНИЕ =====
    logger.info(f"🇦 [EDIT_MENU] Step 6: Creating new menu message...")

    # Безопасно удаляем старое меню если есть
    if menu_message_id:
        await db.delete_old_menu_if_exists(chat_id, callback.message.bot)

    # Создаём новое сообщение
    try:
        new_msg = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )

        logger.info(f"✅ [EDIT_MENU] Created new menu: msg_id={new_msg.message_id}, screen={screen_code}")

        # ===== ШАГ 7: СОХРАНЯЕМ НОВЫЙ ID В FSM + БД =====
        await state.update_data(menu_message_id=new_msg.message_id)
        await db.save_chat_menu(chat_id, user_id, new_msg.message_id, screen_code)

        return False

    except Exception as e:
        logger.error(f"❌ [EDIT_MENU] Failed to create new message: {e}")
        return False


async def show_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Показать главное меню (SCREEN 0).
    КРИТИЧНО: СОХРАНЯЕТ menu_message_id перед любыми операциями!
    
    ОБНОВЛЕНО: 2025-12-30 - Использует get_work_mode_selection_keyboard() с 6 кнопками
    """
    from keyboards.inline import get_work_mode_selection_keyboard
    from utils.texts import START_TEXT
    from states.fsm import CreationStates

    user_id = callback.from_user.id

    # ✅ КРИТИЧНОЕ: Сохраняем menu_message_id ПЕРЕД любыми действиями
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    logger.debug(f"🏠 [MAIN MENU] user={user_id}, menu_id={menu_message_id}")

    # Очищаем FSM состояние
    await state.clear()

    # Устанавливаем новое состояние: selecting_mode (SCREEN 0)
    await state.set_state(CreationStates.selecting_mode)

    # ✅ ВОССТАНАВЛИВАЕМ menu_message_id СРАЗУ ПОСЛЕ инициализации состояния
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
        logger.debug(f"✅ [MAIN MENU] Restored menu_id={menu_message_id}")

    # [2025-12-24 21:45] ОБНОВЛЕНО: edit_menu теперь автоматически добавляет режим в footer
    # Пытаемся отредактировать текущее меню
    await edit_menu(
        callback=callback,
        state=state,
        text=START_TEXT,
        keyboard=get_work_mode_selection_keyboard(),  # ✅ 6 кнопок SCREEN 0
        show_balance=True,  # [2025-12-24 21:45] ✅ НУЖНО! тогда режим покажется
        screen_code='selecting_mode'  # ✅ ОБНОВЛЕНО: screen_code = selecting_mode (SCREEN 0)
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
    Обновление меню после загружения фото пользователем.
    ОТБСОВАНЫ в message handlers, а не callback handlers.

    Args:
        message: Message объект (сообщение с фото)
        state: FSMContext
        text: Новый текст меню
        keyboard: Новая клавиатура
        parse_mode: Режим парсинга

    Returns:
        bool: True если успешно
    """
    chat_id = message.chat.id
    user_id = message.from_user.id

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    # Пробуем восстановить из БД если потеряли
    if not menu_message_id:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info:
            menu_message_id = menu_info['menu_message_id']
            await state.update_data(menu_message_id=menu_message_id)
            logger.info(f"📥 [UPDATE_AFTER_PHOTO] Restored menu_id={menu_message_id} from DB")

    if not menu_message_id:
        logger.warning(f"⚠️ [UPDATE_AFTER_PHOTO] Menu ID not found for user {user_id}")
        return False

    try:
        await message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        logger.debug(f"✅ [UPDATE_AFTER_PHOTO] Menu updated: msg_id={menu_message_id}")

        # Сохраняем в БД
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'photo_uploaded')

        return True

    except TelegramBadRequest as e:
        logger.error(f"❌ [UPDATE_AFTER_PHOTO] Failed to update menu: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ [UPDATE_AFTER_PHOTO] Unexpected error: {e}")
        return False
