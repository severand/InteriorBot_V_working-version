# ===== PHASE 2: NEW_DESIGN MODE (SCREEN 3-6) =====
# [2025-12-29] ОБНОВЛЕНО: Добавлены post_generation_menu() и явная установка состояния
# [2025-12-29] НОВЫЙ ФАЙЛ: Часть 2 рефакторинга creation.py
# Содержит: room_choice (SCREEN 3), choose_style_1/2 (SCREEN 4-5), style_choice_handler (SCREEN 6 + генерация)
# + post_generation_menu (SCREEN 6), change_style_after_gen
# [2025-12-30 01:20] 🔥 BUGFIX #1: Убрать work_mode из add_balance_and_mode_to_text() - функция принимает 2 аргумента!
# [2025-12-30 01:20] 🔥 BUGFIX #2: Убрать answer_photo() в fallback - редактировать текст, а не отправлять новое фото

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

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
        
        text = f"🏠 **Выберите тип помещения**"
        text = await add_balance_and_mode_to_text(text, user_id)  # ✅ 2 аргумента!
        
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
# [2025-12-30 01:20] 🔥 BUGFIX #1: Убрать work_mode argument
@router.callback_query(
    StateFilter(CreationStates.room_choice),
    F.data.startswith("room_")
)
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3→4: Обработчик выбора комнаты
    Сохраняет выбор и переходит на экран выбора стиля (SCREEN 4)
    
    Log: "[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        room = callback.data.replace("room_", "")
        balance = await db.get_balance(user_id)
        data = await state.get_data()
        
        # Сохраняем выбор комнаты в FSM
        await state.update_data(selected_room=room)
        await state.set_state(CreationStates.choose_style_1)
        
        text = f"🎨 **Выберите стиль дизайна**"
        text = await add_balance_and_mode_to_text(text, user_id)  # ✅ 2 аргумента!
        
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
        
        text = f"🎨 **Выберите стиль дизайна (страница 1)**"
        text = await add_balance_and_mode_to_text(text, user_id)  # ✅ 2 аргумента!
        
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
        
        text = f"🎨 **Выберите стиль дизайна (страница 2)**"
        text = await add_balance_and_mode_to_text(text, user_id)  # ✅ 2 аргумента!
        
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
# [2025-12-29] ОБНОВЛЕНО (V3) - Добавлена установка state.post_generation
# [2025-12-30 01:20] 🔥 BUGFIX #2: Убрать answer_photo() в fallback - редактировать меню, не отправлять новое
@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    SCREEN 4-5→6: Обработчик выбора стиля и генерация дизайна
    
    🔥 BUGFIX #2 [2025-12-30 01:20]:
    - БЫЛО: answer_photo() → ВТОРОЕ ФОТО
    - ТЕПЕРЬ: edit_message_media() → ОДНО ФОТО в ОДНОМ сообщении
    - Fallback: edit_message_text() вместо answer()
    
    Log: "[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}"
    """
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id

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
        
        # Подготовка текста для post_generation меню
        post_gen_text = await add_balance_and_mode_to_text(
            "✅ **Выбери что дальше**",
            user_id
        )

        photo_sent = False

        # ===== ПОПЫТКА 1: edit_message_media для ОДНОГО сообщения =====
        try:
            logger.info(f"📸 [STYLE_CHOICE] CALLING edit_message_media - menu_id={menu_message_id}, style={style}")
            
            await callback.message.bot.edit_message_media(
                chat_id=chat_id,
                message_id=menu_message_id,
                media=InputMediaPhoto(
                    media=result_image_url,
                    caption=caption,
                    parse_mode="HTML"
                ),
                reply_markup=get_post_generation_keyboard()
            )
            
            photo_sent = True
            logger.info(f"✅ [STYLE_CHOICE] SUCCESS edit_message_media - Photo + menu in ONE message, menu_id={menu_message_id}")

        except Exception as media_error:
            logger.warning(f"⚠️ [STYLE_CHOICE] FAILED edit_message_media: {media_error}")

            # ===== ПОПЫТКА 2: Отправка фото + редактирование текста (БЕЗ дублирования!) =====
            try:
                logger.info(f"🔄 [STYLE_CHOICE] FALLBACK - Sending photo separately")
                
                # Отправляем фото
                photo_msg = await callback.message.answer_photo(
                    photo=result_image_url,
                    caption=caption,
                    parse_mode="HTML"
                )
                
                # ✅ БЕЗ дублирования! Редактируем СТАРОЕ меню (не создаем новое)
                try:
                    await callback.message.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_message_id,
                        text=post_gen_text,
                        reply_markup=get_post_generation_keyboard(),
                        parse_mode="Markdown"
                    )
                    logger.info(f"✅ [STYLE_CHOICE] FALLBACK: Old menu edited with post_generation text")
                except Exception as e:
                    logger.debug(f"⚠️ Не удалось отредактировать старое меню: {e}")
                
                photo_sent = True
                logger.info(f"✅ [STYLE_CHOICE] FALLBACK SUCCESS - Photo sent via URL")

            except Exception as url_error:
                logger.warning(f"⚠️ [STYLE_CHOICE] FALLBACK 1 FAILED: {url_error}")

                # ===== ПОПЫТКА 3: FALLBACK через BufferedInputFile (БЕЗ дублирования!) =====
                try:
                    logger.info(f"🔄 [STYLE_CHOICE] FALLBACK 2 - BufferedInputFile")

                    async with aiohttp.ClientSession() as session:
                        async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                            if resp.status == 200:
                                photo_data = await resp.read()

                                photo_msg = await callback.message.answer_photo(
                                    photo=BufferedInputFile(photo_data, filename="design.jpg"),
                                    caption=caption,
                                    parse_mode="HTML"
                                )
                                
                                # ✅ Редактируем СТАРОЕ меню
                                try:
                                    await callback.message.bot.edit_message_text(
                                        chat_id=chat_id,
                                        message_id=menu_message_id,
                                        text=post_gen_text,
                                        reply_markup=get_post_generation_keyboard(),
                                        parse_mode="Markdown"
                                    )
                                    logger.info(f"✅ [STYLE_CHOICE] FALLBACK 2: Old menu edited")
                                except Exception as e:
                                    logger.debug(f"⚠️ Не удалось отредактировать меню: {e}")
                                
                                photo_sent = True
                                logger.info(f"✅ [STYLE_CHOICE] FALLBACK 2 SUCCESS - Photo via BufferedInputFile")
                            else:
                                logger.error(f"❌ [STYLE_CHOICE] HTTP {resp.status}")

                except Exception as buffer_error:
                    logger.error(f"❌ [STYLE_CHOICE] FALLBACK 2 FAILED: {buffer_error}")

        # Если все три попытки не сработали
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

        # УСПЕХ - Устанавливаем состояние POST_GENERATION
        await state.set_state(CreationStates.post_generation)
        await state.update_data(menu_message_id=menu_message_id)
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'post_generation')

        logger.info(f"[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}")
        logger.info(f"[V3] NEW_DESIGN+POST_GENERATION - ready, user_id={user_id}")

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


# ===== SCREEN 6: POST_GENERATION_MENU (Меню после генерации) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "post_generation"
)
async def post_generation_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 6: Меню после генерации (POST_GENERATION)
    
    Log: "[V3] NEW_DESIGN+POST_GENERATION - menu shown, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        balance = await db.get_balance(user_id)
        
        # Будем на этом экране
        await state.set_state(CreationStates.post_generation)
        
        text = f"✅ **Выбери что дальше**"
        text = await add_balance_and_mode_to_text(text, user_id)  # ✅ 2 аргумента!
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_post_generation_keyboard(),
            screen_code='post_generation'
        )
        
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'post_generation')
        
        logger.info(f"[V3] NEW_DESIGN+POST_GENERATION - menu shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] POST_GENERATION_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


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
    text = f"🎨 **Выберите стиль дизайна**"
    text = await add_balance_and_mode_to_text(text, user_id)  # ✅ 2 аргумента!

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
