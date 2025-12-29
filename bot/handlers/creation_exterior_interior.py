# bot/handlers/creation_exterior_interior.py
# ===== PHASE 3: EXTERIOR/INTERIOR + OLD SYSTEM =====
# [2025-12-29] НОВЫЙ ФАЙЛ: Часть 3 рефакторинга creation.py
# Содержит: Старая система (what_is_in_photo -> room_choice -> style_choice -> generation)
# + Clear Space, room_chosen, style_chosen

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StateFilter
from aiogram.types import CallbackQuery, Message

from database.db import db

from keyboards.inline import (
    get_what_is_in_photo_keyboard,
    get_upload_photo_keyboard,
    get_room_keyboard,
    get_style_keyboard,
    get_payment_keyboard,
    get_post_generation_keyboard,
    get_clear_space_confirm_keyboard,
    get_main_menu_keyboard,
)

from services.api_fallback import smart_generate_with_text, smart_clear_space, smart_generate_interior

from states.fsm import CreationStates

from utils.texts import (
    WHAT_IS_IN_PHOTO_TEXT,
    EXTERIOR_HOUSE_PROMPT_TEXT,
    EXTERIOR_PLOT_PROMPT_TEXT,
    ROOM_DESCRIPTION_PROMPT_TEXT,
    CHOOSE_STYLE_TEXT,
    PHOTO_SAVED_TEXT,
    NO_BALANCE_TEXT,
    TOO_MANY_PHOTOS_TEXT,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()


# ===== OLD SYSTEM: WHAT_IS_IN_PHOTO (SCREEN 2ș23) =====
@router.callback_query(F.data.startswith("what_is_in_photo_"))
async def exterior_scene_chosen(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 2ș23: Обработка выбора "Что на фото"
    
    Опции:
    - what_is_in_photo_exterior_house → Промпт для дома
    - what_is_in_photo_exterior_plot → Промпт для участка
    - what_is_in_photo_interior → ROOM_CHOICE (одна опция)
    """
    user_id = callback.from_user.id
    scene_type = callback.data.replace("what_is_in_photo_", "")

    data = await state.get_data()
    photo_id = data.get('photo_id')

    if not photo_id:
        await show_main_menu(callback, state, [])
        return

    try:
        # Настройка состояния и текста в зависимости от типа
        if scene_type == "exterior_house":
            await state.set_state(CreationStates.exterior_prompt)
            text = EXTERIOR_HOUSE_PROMPT_TEXT
        elif scene_type == "exterior_plot":
            await state.set_state(CreationStates.exterior_prompt)
            text = EXTERIOR_PLOT_PROMPT_TEXT
        elif scene_type == "interior":
            # Определить комнату
            await state.set_state(CreationStates.room_choice)
            text = f"🏠 **Выберите комнату**"
            balance = await db.get_balance(user_id)
            text = await add_balance_and_mode_to_text(text, user_id)
        else:
            logger.error(f"[ERROR] Unknown scene_type: {scene_type}")
            await callback.answer("❌ Неизвестный тип сцены", show_alert=True)
            return

        # Сохраняем тип сцены
        await state.update_data(scene_type=scene_type)

        # Выбираем клавиатуру
        if scene_type == "interior":
            keyboard = get_room_keyboard()
        else:
            keyboard = None  # Промпт запросит текст

        # Отредактивание меню
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=keyboard,
            screen_code=f'what_is_in_photo_{scene_type}'
        )

        logger.info(f"what_is_in_photo_{scene_type} - user_id={user_id}")
        await callback.answer()

    except Exception as e:
        logger.error(f"[ERROR] EXTERIOR_SCENE_CHOSEN failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


# ===== OLD SYSTEM: ROOM CHOICE (SCREEN 3) =====
@router.callback_query(StateFilter(CreationStates.room_choice), F.data.startswith("room_"))
async def interior_room_chosen(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3ș24: Обработка выбора комнаты
    Переход к выбору стиля
    """
    user_id = callback.from_user.id
    room = callback.data.replace("room_", "")

    try:
        await state.update_data(room=room)
        await state.set_state(CreationStates.choose_style)

        text = CHOOSE_STYLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id)

        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_style_keyboard(),
            screen_code='choose_style'
        )

        await callback.answer()
        logger.info(f"interior_room_chosen - room={room}, user_id={user_id}")

    except Exception as e:
        logger.error(f"[ERROR] INTERIOR_ROOM_CHOSEN failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


# ===== OLD SYSTEM: EXTERIOR PROMPT (SCREEN 3 -> 4) =====
@router.message(StateFilter(CreationStates.exterior_prompt))
async def exterior_prompt_received(message: Message, state: FSMContext):
    """
    SCREEN 3ș24: Получение текстового описания экстерьера
    Перес к выбору стиля
    """
    user_id = message.from_user.id

    try:
        text_input = message.text or ""
        await state.update_data(exterior_prompt=text_input)
        await state.set_state(CreationStates.choose_style)

        text = CHOOSE_STYLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id)

        # Удаляем старое меню
        data = await state.get_data()
        menu_id = data.get('menu_message_id')

        if menu_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=menu_id
                )
            except Exception:
                pass

        # Отсылаем новое меню
        sent_msg = await message.answer(
            text=text,
            reply_markup=get_style_keyboard(),
            parse_mode="Markdown"
        )

        await state.update_data(menu_message_id=sent_msg.message_id)
        await db.save_chat_menu(message.chat.id, user_id, sent_msg.message_id, 'choose_style')

        logger.info(f"exterior_prompt_received - user_id={user_id}")

    except Exception as e:
        logger.error(f"[ERROR] EXTERIOR_PROMPT_RECEIVED failed: {e}", exc_info=True)


# ===== OLD SYSTEM: ROOM DESCRIPTION (SCREEN 4) =====
@router.message(StateFilter(CreationStates.room_description))
async def room_description_received(message: Message, state: FSMContext):
    """
    SCREEN 4ș25: Описание комнаты текстом
    Аналогично exterior_prompt_received
    """
    user_id = message.from_user.id

    try:
        text_input = message.text or ""
        await state.update_data(room_description=text_input)
        await state.set_state(CreationStates.choose_style)

        text = CHOOSE_STYLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id)

        data = await state.get_data()
        menu_id = data.get('menu_message_id')

        if menu_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=menu_id
                )
            except Exception:
                pass

        sent_msg = await message.answer(
            text=text,
            reply_markup=get_style_keyboard(),
            parse_mode="Markdown"
        )

        await state.update_data(menu_message_id=sent_msg.message_id)
        await db.save_chat_menu(message.chat.id, user_id, sent_msg.message_id, 'choose_style')

        logger.info(f"room_description_received - user_id={user_id}")

    except Exception as e:
        logger.error(f"[ERROR] ROOM_DESCRIPTION_RECEIVED failed: {e}", exc_info=True)


# ===== OLD SYSTEM: STYLE CHOICE (SCREEN 5 -> 6 генерация) =====
@router.callback_query(
    StateFilter(CreationStates.choose_style),
    F.data.startswith("style_")
)
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    SCREEN 5ș26: Обработка выбора стиля (старая система)
    
    Нарабатывает:
    - Определение типа генерации (экстерьер/интерьер)
    - Декремент баланса
    - Отправка изображения
    """
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    data = await state.get_data()
    photo_id = data.get('photo_id')
    scene_type = data.get('scene_type')
    room = data.get('room')
    exterior_prompt = data.get('exterior_prompt', '')
    room_description = data.get('room_description', '')

    if not photo_id:
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
                text=NO_BALANCE_TEXT,
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
        text="⚡ Генериру дизайн...",
        keyboard=None,
        show_balance=False,
        screen_code='generating_design'
    )
    await callback.answer()

    # Определение типа нейро для женерации
    is_exterior = scene_type and "exterior" in scene_type
    is_interior = scene_type == "interior"

    # Получаем PRO сеттингс
    pro_settings = await db.get_user_pro_settings(user_id)
    use_pro = pro_settings.get('pro_mode', False)

    # ГЕНЕРАЦИЯ
    try:
        if is_exterior:
            result_image_url = await smart_generate_with_text(
                photo_id, style, exterior_prompt, bot_token, use_pro=use_pro
            )
        elif is_interior:
            result_image_url = await smart_generate_interior(
                photo_id, room, style, bot_token, use_pro=use_pro
            )
        else:
            result_image_url = await smart_generate_with_text(
                photo_id, style, room_description, bot_token, use_pro=use_pro
            )
        
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"[ERROR] Критическая ошибка генерации: {e}")
        result_image_url = None
        success = False

    # Логирование
    op_type = 'exterior' if is_exterior else ('interior' if is_interior else 'design')
    await db.log_generation(
        user_id=user_id,
        room_type=room or 'N/A',
        style_type=style,
        operation_type=op_type,
        success=success
    )

    if result_image_url:
        caption = f"✨ Новый дизайн!"
        photo_sent = False

        # ПОПЫТКА 1: URL
        try:
            await callback.message.answer_photo(
                photo=result_image_url,
                caption=caption,
                parse_mode="HTML"
            )
            photo_sent = True

        except Exception as url_error:
            logger.warning(f"⚠️ Не удалось отправить по URL: {url_error}")

            # ПОПЫТКА 2: FALLBACK
            try:
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
            except Exception as buffer_error:
                logger.error(f"❌ Fallback не сработал: {buffer_error}")

        # Меню после генерации
        if not photo_sent:
            await edit_menu(
                callback=callback,
                state=state,
                text="❌ Ошибка при отправке",
                keyboard=get_main_menu_keyboard(is_admin=is_admin),
                screen_code='generation_error'
            )
            return

        # НОВОЕ меню ПОД ФОТО
        old_menu_id = data.get('menu_message_id')
        if old_menu_id:
            try:
                await callback.message.bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_menu_id
                )
            except Exception:
                pass

        text_with_balance = await add_balance_and_mode_to_text(
            "✅ Выбери что дальше 👇",
            user_id
        )

        new_menu = await callback.message.answer(
            text=text_with_balance,
            reply_markup=get_post_generation_keyboard(),
            parse_mode="Markdown"
        )

        await state.update_data(menu_message_id=new_menu.message_id)
        await db.save_chat_menu(chat_id, user_id, new_menu.message_id, 'post_generation')

    else:
        await edit_menu(
            callback=callback,
            state=state,
            text="❌ Ошибка генерации",
            keyboard=get_main_menu_keyboard(is_admin=is_admin),
            screen_code='generation_error'
        )

    logger.info(f"style_chosen - style={style}, user_id={user_id}")


# ===== OLD SYSTEM: CLEAR SPACE =====
@router.callback_query(F.data == "clear_space")
async def clear_space_handler(callback: CallbackQuery, state: FSMContext):
    """
    CLEAR SPACE фича: ты это чочеть убрать
    """
    user_id = callback.from_user.id
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    if not photo_id or not room:
        await show_main_menu(callback, state, [])
        return

    await edit_menu(
        callback=callback,
        state=state,
        text="🛋 Отородить мебель?",
        keyboard=get_clear_space_confirm_keyboard(),
        screen_code='clear_space_confirm'
    )

    logger.info(f"clear_space_handler - user_id={user_id}")
    await callback.answer()


@router.callback_query(F.data == "clear_space_confirm")
async def clear_space_execute(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    Оригинальное меню арены (clear_space)
    """
    user_id = callback.from_user.id
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    # Проверка баланса
    is_admin = user_id in admins
    if not is_admin:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await edit_menu(
                callback=callback,
                state=state,
                text=NO_BALANCE_TEXT,
                keyboard=get_payment_keyboard(),
                screen_code='no_balance'
            )
            return

    # Тратать баланс
    if not is_admin:
        await db.decrease_balance(user_id)

    # Показываем прогресс
    await edit_menu(
        callback=callback,
        state=state,
        text="⚡ Отороря...",
        keyboard=None,
        show_balance=False,
        screen_code='clearing_space'
    )
    await callback.answer()

    # Получаем PRO
    pro_settings = await db.get_user_pro_settings(user_id)
    use_pro = pro_settings.get('pro_mode', False)

    # ОДЕВОИИЕ
    try:
        result_image_url = await smart_clear_space(
            photo_id, room, bot_token, use_pro=use_pro
        )
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"[ERROR] clear_space generation failed: {e}")
        result_image_url = None
        success = False

    await db.log_generation(
        user_id=user_id,
        room_type=room,
        style_type='clear',
        operation_type='clear_space',
        success=success
    )

    if result_image_url:
        photo_sent = False

        try:
            await callback.message.answer_photo(
                photo=result_image_url,
                caption="👏 Комната очищена!",
                parse_mode="HTML"
            )
            photo_sent = True
        except Exception as url_error:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()
                            await callback.message.answer_photo(
                                photo=BufferedInputFile(photo_data, filename="clear.jpg"),
                                caption="👏 Комната очищена!",
                                parse_mode="HTML"
                            )
                            photo_sent = True
            except Exception:
                pass

        if photo_sent:
            old_menu_id = data.get('menu_message_id')
            if old_menu_id:
                try:
                    await callback.message.bot.delete_message(
                        chat_id=callback.message.chat.id,
                        message_id=old_menu_id
                    )
                except Exception:
                    pass

            text_with_balance = await add_balance_and_mode_to_text(
                "✅ что дальше?",
                user_id
            )

            new_menu = await callback.message.answer(
                text=text_with_balance,
                reply_markup=get_post_generation_keyboard(),
                parse_mode="Markdown"
            )

            await state.update_data(menu_message_id=new_menu.message_id)
        else:
            await edit_menu(
                callback=callback,
                state=state,
                text="❌ Ошибка при отправке",
                keyboard=get_main_menu_keyboard(is_admin=is_admin),
                screen_code='generation_error'
            )
    else:
        await edit_menu(
            callback=callback,
            state=state,
            text="❌ Ошибка генерации",
            keyboard=get_main_menu_keyboard(is_admin=is_admin),
            screen_code='generation_error'
        )

    logger.info(f"clear_space_execute - user_id={user_id}")


@router.callback_query(F.data == "clear_space_cancel")
async def clear_space_cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Откать оторора"""
    data = await state.get_data()
    balance = await db.get_balance(callback.from_user.id)

    text = f"Воцбратилось. Баланс: {balance}"
    text = await add_balance_and_mode_to_text(text, callback.from_user.id)

    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_post_generation_keyboard(),
        screen_code='post_generation'
    )
    await callback.answer()

    logger.info(f"clear_space_cancel - user_id={callback.from_user.id}")
