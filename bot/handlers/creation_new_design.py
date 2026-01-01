# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                   📋 СКАЛЬПЕЛЬ BOT V3 - NEW_DESIGN HANDLERS                ║
# ║                     Управление экранами SCREEN 3-6                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# 📍 ОПИСАНИЕ ФАЙЛА:
#    Этот файл содержит ВСЕ обработчики (handlers) для режима "Создать новый дизайн"
#    Управляет переходом между 4 ЭКРАНАМИ согласно документу STRUCTURE.md:
#
#    SCREEN 3 → SCREEN 4 → SCREEN 5 → SCREEN 6
#
# 📚 ЭКРАНЫ:
#    • SCREEN 3: room_choice_menu() - Выбор типа помещения (10 типов)
#    • SCREEN 3→4: room_choice_handler() - Обработка выбора комнаты
#    • SCREEN 4: choose_style_1_menu() - Выбор стиля СТРАНИЦА 1 (12 стилей)
#    • SCREEN 5: choose_style_2_menu() - Выбор стиля СТРАНИЦА 2 (12 стилей)
#    • SCREEN 4-5→6: style_choice_handler() - 🔥 ГЕНЕРАЦИЯ ДИЗАЙНА [MAIN]
#    • SCREEN 6: post_generation_menu() - Меню после генерации
#    • SCREEN 6→4: change_style_after_gen() - Смена стиля (без генерации)
#
# 🔧 АРХИТЕКТУРА FSM (Finite State Machine):
#    CreationStates.room_choice → choose_style_1 → choose_style_2 → post_generation
#
# 🔥 ГЛАВНЫЙ ОБРАБОТЧИК:
#    style_choice_handler() - Генерирует дизайн через smart_generate_interior()
#
# 📊 ВЕРСИЯ: 3.0
# 📅 ДАТА: 2026-01-01
# ============================================================================

import asyncio
import logging
import html
import uuid
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

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
    ROOM_TYPES,
    STYLE_TYPES,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 3] ВЫБОР ТИПА ПОМЕЩЕНИЯ (ROOM CHOICE)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """🏠 [SCREEN 3] room_choice_menu() - Меню выбора типа помещения"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.set_state(CreationStates.room_choice)
        
        text = f"🏠 **Выберите тип помещения**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_room_choice_keyboard(),
            screen_code='room_choice'
        )
        
        logger.info(f"[V3] NEW_DESIGN+ROOM_CHOICE - menu shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] ROOM_CHOICE_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 3→4] ОБРАБОТЧИК ВЫБОРА КОМНАТЫ (ROOM CHOICE HANDLER)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.room_choice),
    F.data.startswith("room_")
)
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """🏠 [SCREEN 3→4] room_choice_handler() - Обработчик выбора комнаты"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        room = callback.data.replace("room_", "")
        
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.update_data(selected_room=room)
        await state.set_state(CreationStates.choose_style_1)
        
        text = f"🎨 **Выберите стиль дизайна**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_choose_style_1_keyboard(),
            screen_code='choose_style_1'
        )
        
        logger.info(f"[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] ROOM_CHOICE_HANDLER failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе комнаты", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🎨 [SCREEN 4] ВЫБОР СТИЛЯ СТРАНИЦА 1 (CHOOSE STYLE PAGE 1)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.choose_style_2),
    F.data == "styles_page_1"
)
async def choose_style_1_menu(callback: CallbackQuery, state: FSMContext):
    """🎨 [SCREEN 5→4] choose_style_1_menu() - Вернуться на первую страницу стилей"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.set_state(CreationStates.choose_style_1)
        
        text = f"🎨 **Выберите стиль дизайна (страница 1)**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_choose_style_1_keyboard(),
            screen_code='choose_style_1'
        )
        
        logger.info(f"[V3] NEW_DESIGN+CHOOSE_STYLE - back to page 1, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] CHOOSE_STYLE_1_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🎨 [SCREEN 5] ВЫБОР СТИЛЯ СТРАНИЦА 2 (CHOOSE STYLE PAGE 2)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.choose_style_1),
    F.data == "styles_page_2"
)
async def choose_style_2_menu(callback: CallbackQuery, state: FSMContext):
    """🎨 [SCREEN 4→5] choose_style_2_menu() - Показать вторую страницу стилей"""
    user_id = callback.from_user.id
    
    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.set_state(CreationStates.choose_style_2)
        
        text = f"🎨 **Выберите стиль дизайна (страница 2)**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
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


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🔥 [SCREEN 4-5→6] ГЛАВНЫЙ ОБРАБОТЧИК: ГЕНЕРАЦИЯ ДИЗАЙНА (STYLE CHOICE + GENERATION)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """🔥 [SCREEN 4-5→6] style_choice_handler() - ГЛАВНЫЙ ГЕНЕРАТОР ДИЗАЙНА"""
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    logger.warning(f"🔍 [DIAG_START] user_id={user_id}, style={style}")

    await db.log_activity(user_id, f'style_{style}')

    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')
    work_mode = data.get('work_mode')

    if not photo_id or not room:
        await callback.answer("⚠️ Сессия устарела. Загрузите фото заново.", show_alert=True)
        await state.clear()
        await show_main_menu(callback, state, admins)
        return

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

    if not is_admin:
        await db.decrease_balance(user_id)

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Failed to delete style menu: {e}")
    
    progress_msg = None
    try:
        balance_text = await add_balance_and_mode_to_text(
            f"⚡ Генерирую {style} дизайн...",
            user_id,
            work_mode
        )
        
        progress_msg = await callback.message.answer(
            text=balance_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to send progress msg: {e}")
    
    await callback.answer()

    pro_settings = await db.get_user_pro_settings(user_id)
    use_pro = pro_settings.get('pro_mode', False)

    try:
        result_image_url = await smart_generate_interior(
            photo_id, room, style, bot_token, use_pro=use_pro
        )
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"[ERROR] Критическая ошибка генерации: {e}")
        result_image_url = None
        success = False

    await db.log_generation(
        user_id=user_id,
        room_type=room,
        style_type=style,
        operation_type='design',
        success=success
    )

    if result_image_url:
        balance = await db.get_balance(user_id)
        
        room_display = ROOM_TYPES.get(room, room.replace('_', ' ').title())
        style_display = STYLE_TYPES.get(style, style.replace('_', ' ').title())
        
        design_caption = f"""✨ <b>Ваш новый дизайн в стиле {style_display} готов!</b>

🎨 {room_display} преобразилась!"""
        
        menu_caption = f"""🎨 <b>Что дальше?</b>

Выберите действие:
🔄 Другой стиль - примеря другой стиль на эту комнату
🏠 Главное меню - вернуться в главное меню

📊 Баланс: <b>{balance}</b> генераций | 🔧 Режим: <b>{work_mode}</b>"""
        
        photo_sent = False

        try:
            photo_msg = await callback.message.answer_photo(
                photo=result_image_url,
                caption=design_caption,
                parse_mode="HTML",
            )
            
            photo_sent = True
            logger.warning(f"📊 SUCCESS: answer_photo, msg_id={photo_msg.message_id}")
            
            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
            
            try:
                menu_msg = await callback.message.answer(
                    text=menu_caption,
                    parse_mode="HTML",
                    reply_markup=get_post_generation_keyboard()
                )
                logger.warning(f"📊 MENU_SENT: msg_id={menu_msg.message_id}")
                
                await state.update_data(photo_message_id=photo_msg.message_id, menu_message_id=menu_msg.message_id)
                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                
            except Exception as menu_error:
                logger.warning(f"⚠️ Failed to send menu: {menu_error}")
            
            if progress_msg:
                try:
                    await progress_msg.delete()
                    logger.warning(f"📊 Deleted progress msg")
                except Exception:
                    pass

        except Exception as url_error:
            logger.warning(f"📊 FAILED_ATTEMPT_1: {url_error}")

            try:
                logger.warning(f"📊 ATTEMPT_2: BufferedInputFile")

                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()

                            photo_msg = await callback.message.answer_photo(
                                photo=BufferedInputFile(photo_data, filename="design.jpg"),
                                caption=design_caption,
                                parse_mode="HTML",
                            )
                            
                            logger.warning(f"📊 ATTEMPT_2_PHOTO_SENT: msg_id={photo_msg.message_id}")
                            
                            photo_sent = True
                            logger.warning(f"📊 SUCCESS_ATTEMPT_2: answer_photo_buffered")
                            
                            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
                            logger.warning(f"📊 SAVED_TO_DB after ATTEMPT_2")
                            
                            try:
                                menu_msg = await callback.message.answer(
                                    text=menu_caption,
                                    parse_mode="HTML",
                                    reply_markup=get_post_generation_keyboard()
                                )
                                await state.update_data(photo_message_id=photo_msg.message_id, menu_message_id=menu_msg.message_id)
                                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                            except Exception as menu_error:
                                logger.warning(f"⚠️ Failed to send menu after ATTEMPT_2: {menu_error}")
                            
                            if progress_msg:
                                try:
                                    await progress_msg.delete()
                                except Exception:
                                    pass

                        else:
                            logger.error(f"[ERROR] HTTP {resp.status} when downloading image")
                            photo_sent = False

            except Exception as fallback_error:
                logger.error(f"[ERROR] FALLBACK ATTEMPT_2 failed: {fallback_error}")
                photo_sent = False

        if not photo_sent:
            if not is_admin:
                await db.increase_balance(user_id, 1)
            
            try:
                if progress_msg:
                    await progress_msg.edit_text("❌ Ошибка при отправке изображения. Баланс возвращен. Попробуйте еще раз.")
                else:
                    await callback.message.answer("❌ Ошибка при отправке изображения. Баланс возвращен. Попробуйте еще раз.")
            except Exception as e:
                logger.error(f"[ERROR] Failed to send error message: {e}")

    else:
        if not is_admin:
            await db.increase_balance(user_id, 1)
        
        try:
            if progress_msg:
                await progress_msg.edit_text(f"❌ Ошибка при генерации дизайна.\n\n🔧 Попробуйте:\n1. Загрузить другое фото\n2. Выбрать другой стиль\n3. Связаться с поддержкой")
            else:
                await callback.message.answer(f"❌ Ошибка при генерации дизайна.\n\n🔧 Попробуйте:\n1. Загрузить другое фото\n2. Выбрать другой стиль\n3. Связаться с поддержкой")
        except Exception as e:
            logger.error(f"[ERROR] Failed to send error message: {e}")

    await state.set_state(CreationStates.post_generation)
    logger.info(f"[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}")
