# bot/handlers/creation_new_design.py
# ===== PHASE 2: NEW_DESIGN MODE (SCREEN 3-6) =====
# [2025-12-29] НОВЫЙ ФАЙЛ: Часть 2 рефакторинга creation.py
# Содержит: room_choice (SCREEN 3), choose_style_1/2 (SCREEN 4-5), style_choice_handler (SCREEN 6 + генерация)
# + post_generation, change_style_after_gen

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StateFilter
from aiogram.types import CallbackQuery, Message

from database.db import db

from keyboards.inline import (
    get_room_choice_keyboard,
    get_choose_style_1_keyboard,
    get_choose_style_2_keyboard,
    get_post_generation_keyboard,
    get_payment_keyboard,
    get_main_menu_keyboard,
)

from services.api_fallback import smart_generate_interior

from states.fsm import CreationStates, WorkMode

from utils.texts import (
    ROOM_CHOICE_TEXT,
    CHOOSE_STYLE_TEXT,
    ERROR_INSUFFICIENT_BALANCE,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()


# ===== SCREEN 3: ROOM_CHOICE (NEW_DESIGN только) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3: Меню выбора комнаты (ROOM_CHOICE)
    Только для режима NEW_DESIGN
    
    Log: "[V3] NEW_DESIGN+ROOM_CHOICE - menu shown, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        balance = await db.get_balance(user_id)
        
        await state.set_state(CreationStates.room_choice)
        
        text = ROOM_CHOICE_TEXT.format(balance=balance)
        text = await add_balance_and_mode_to_text(text, user_id, data.get('work_mode'))
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_room_choice_keyboard(),
            screen_code='room_choice'
        )
        
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'room_choice')
        
        logger.info(f"[V3] NEW_DESIGN+ROOM_CHOICE - menu shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] ROOM_CHOICE_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== SCREEN 3→4: ROOM_CHOICE_HANDLER =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(
    StateFilter(CreationStates.room_choice),
    F.data.startswith("room_")
)
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3→4: Обработчик выбора комнаты
    Сохраняет выбор и переходит на экран выбора стиля (SCREEN 4)
    
    Поддерживаемые комнаты:
    - room_living_room, room_kitchen, room_bedroom, room_nursery, 
      room_studio, room_home_office, room_bathroom_full, room_toilet,
      room_entryway, room_wardrobe
    
    Log: "[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        room = callback.data.replace("room_", "")
        balance = await db.get_balance(user_id)
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        # Сохраняем выбор комнаты в FSM
        await state.update_data(selected_room=room)
        await state.set_state(CreationStates.choose_style_1)
        
        text = CHOOSE_STYLE_TEXT.format(
            balance=balance,
            current_mode=work_mode,
            selected_room=room
        )
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_choose_style_1_keyboard(),
            screen_code='choose_style_1'
        )
        
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'choose_style_1')
        
        logger.info(f"[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] ROOM_CHOICE_HANDLER failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе комнаты", show_alert=True)


# ===== SCREEN 4: CHOOSE_STYLE_1 (Первая страница стилей) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(
    StateFilter(CreationStates.choose_style_2),
    F.data == "styles_page_1"
)
async def choose_style_1_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 5→4: Вернуться на первую страницу стилей
    
    Log: "[V3] NEW_DESIGN+CHOOSE_STYLE - back to page 1, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        balance = await db.get_balance(user_id)
        
        await state.set_state(CreationStates.choose_style_1)
        
        text = CHOOSE_STYLE_TEXT.format(
            balance=balance,
            current_mode=data.get('work_mode'),
            selected_room=data.get('selected_room')
        )
        text = await add_balance_and_mode_to_text(text, user_id, data.get('work_mode'))
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_choose_style_1_keyboard(),
            screen_code='choose_style_1'
        )
        
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'choose_style_1')
        
        logger.info(f"[V3] NEW_DESIGN+CHOOSE_STYLE - back to page 1, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] CHOOSE_STYLE_1_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== SCREEN 5: CHOOSE_STYLE_2 (Вторая страница стилей) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(
    StateFilter(CreationStates.choose_style_1),
    F.data == "styles_page_2"
)
async def choose_style_2_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 4→5: Показать вторую страницу стилей
    
    Log: "[V3] NEW_DESIGN+CHOOSE_STYLE - page 2 shown, user_id={user_id}"
    """
    user_id = callback.from_user.id
    
    try:
        data = await state.get_data()
        balance = await db.get_balance(user_id)
        
        await state.set_state(CreationStates.choose_style_2)
        
        text = CHOOSE_STYLE_TEXT.format(
            balance=balance,
            current_mode=data.get('work_mode'),
            selected_room=data.get('selected_room')
        )
        text = await add_balance_and_mode_to_text(text, user_id, data.get('work_mode'))
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_choose_style_2_keyboard(),
            screen_code='choose_style_2'
        )
        
        logger.info(f"[V3] NEW_DESIGN+CHOOSE_STYLE - page 2 shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] CHOOSE_STYLE_2_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== SCREEN 4-5 to 6: STYLE_CHOICE_HANDLER (Выбор стиля + генерация) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    SCREEN 4-5→6: Обработчик выбора стиля и генерация дизайна
    
    Операции:
    1. Извлечение стиля из callback_data
    2. Проверка наличия комнаты и фото
    3. Проверка баланса
    4. Минусование баланса
    5. Вывод прогресса ("Генерирую...")
    6. Вызов smart_generate_interior() с PRO параметром
    7. Отправка фото с fallback (URL → BufferedInputFile)
    8. Удаление старого меню, создание НОВОГО (под фото)
    9. Меню POST_GENERATION
    
    Styles: style_modern, style_minimalist, style_classic, ...
    
    Log: "[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}"
    """
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await db.log_activity(user_id, f'style_{style}')

    # Проверка наличия данных
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')

    if not photo_id or not room:
        await callback.answer(
            "⚠️ Сессия устарела. Загрузите фото заново.",
            show_alert=True
        )
        await state.clear()
        await show_main_menu(callback, state, admins)
        return

    # Проверка баланса
    is_admin = user_id in admins
    if not is_admin:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await edit_menu(
                callback=callback,
                state=state,
                text=ERROR_INSUFFICIENT_BALANCE,
                keyboard=get_payment_keyboard(),
                screen_code='no_balance'
            )
            return

    # Минусование баланса
    if not is_admin:
        await db.decrease_balance(user_id)

    # Показываем прогресс
    await edit_menu(
        callback=callback,
        state=state,
        text="⚡ Генерирую новый дизайн...",
        keyboard=None,
        show_balance=False,
        screen_code='generating_design'
    )
    await callback.answer()

    # Получаем PRO mode
    pro_settings = await db.get_user_pro_settings(user_id)
    use_pro = pro_settings.get('pro_mode', False)
    logger.info(f"🔧 PRO MODE для user_id={user_id}: {use_pro}")

    # ГЕНЕРАЦИЯ
    try:
        result_image_url = await smart_generate_interior(
            photo_id, room, style, bot_token, use_pro=use_pro
        )
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"[ERROR] Критическая ошибка генерации: {e}")
        result_image_url = None
        success = False

    # Логирование
    await db.log_generation(
        user_id=user_id,
        room_type=room,
        style_type=style,
        operation_type='design',
        success=success
    )

    if result_image_url:
        # Подготовка подписи
        room_name = html.escape(room.replace('_', ' ').title(), quote=True)
        style_name = html.escape(style.replace('_', ' ').title(), quote=True)
        caption = f"✨ Ваш новый дизайн {room_name} в стиле <b>{style_name}</b>!"

        photo_sent = False

        # ПОПЫТКА 1: Отправка по URL
        try:
            await callback.message.answer_photo(
                photo=result_image_url,
                caption=caption,
                parse_mode="HTML"
            )
            photo_sent = True
            logger.info(f"✅ Фото отправлено по URL: user_id={user_id}")

        except Exception as url_error:
            logger.warning(f"⚠️ Не удалось отправить по URL: {url_error}")

            # ПОПЫТКА 2: FALLBACK через BufferedInputFile
            try:
                logger.info(f"🔄 Переключаемся на BufferedInputFile для user_id={user_id}")

                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()

                            await callback.message.answer_photo(
                                photo=BufferedInputFile(photo_data, filename="design.jpg"),
                                caption=caption,
                                parse_mode="HTML"
                            )
                            photo_sent = True
                            logger.info(f"✅ Фото отправлено через BufferedInputFile: user_id={user_id}")
                        else:
                            logger.error(f"❌ HTTP {resp.status} при скачивании")

            except Exception as buffer_error:
                logger.error(f"❌ Fallback тоже не сработал: {buffer_error}")

        # Если обе попытки не сработали
        if not photo_sent:
            # Возвращаем баланс
            if not is_admin:
                await db.increase_balance(user_id, 1)
            
            await edit_menu(
                callback=callback,
                state=state,
                text="❌ Ошибка при отправке изображения. Баланс возвращен. Попробуйте еще раз.",
                keyboard=get_main_menu_keyboard(is_admin=is_admin),
                screen_code='generation_error'
            )
            return

        # УСПЕХ - Удаляем старое меню, создаем НОВОЕ (под фото)
        old_menu_id = data.get('menu_message_id')
        if old_menu_id:
            try:
                await callback.message.bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_menu_id
                )
                await db.delete_chat_menu(chat_id)
            except Exception as e:
                logger.debug(f"Не удалось удалить старое меню: {e}")

        # Отправляем НОВОЕ меню
        text_with_balance = await add_balance_and_mode_to_text(
            "✅ Выбери что дальше 👇",
            user_id
        )

        new_menu = await callback.message.answer(
            text=text_with_balance,
            reply_markup=get_post_generation_keyboard(),
            parse_mode="Markdown"
        )

        # Сохраняем в FSM + БД
        await state.update_data(menu_message_id=new_menu.message_id)
        await db.save_chat_menu(chat_id, user_id, new_menu.message_id, 'post_generation')

        logger.info(f"[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}")

    else:
        # Ошибка генерации - возвращаем баланс
        if not is_admin:
            await db.increase_balance(user_id, 1)
        
        await edit_menu(
            callback=callback,
            state=state,
            text="❌ Ошибка генерации. Баланс возвращен. Попробуйте еще раз.",
            keyboard=get_main_menu_keyboard(is_admin=user_id in admins),
            screen_code='generation_error'
        )


# ===== POST-GENERATION: CHANGE_STYLE (Смена стиля после генерации) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    ПОСЛЕ генерации: смена стиля
    
    Логика: восстановление в состояние choose_style для новой генерации
    """
    user_id = callback.from_user.id

    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')

    if not photo_id or not room:
        try:
            await callback.answer(
                "⚠️ Сессия устарела. Начните сначала.",
                show_alert=True
            )
        except Exception:
            pass

        await show_main_menu(callback, state, admins)
        return

    # Выбор стиля снова
    await state.set_state(CreationStates.choose_style_1)

    balance = await db.get_balance(user_id)
    text = CHOOSE_STYLE_TEXT.format(
        balance=balance,
        current_mode=data.get('work_mode'),
        selected_room=room
    )
    text = await add_balance_and_mode_to_text(text, user_id, data.get('work_mode'))

    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_choose_style_1_keyboard(),
        screen_code='choose_style_1'
    )

    try:
        await callback.answer()
    except Exception:
        pass

    logger.info(f"[V3] NEW_DESIGN+CHANGE_STYLE - user_id={user_id}")
