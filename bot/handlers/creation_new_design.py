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
    get_uploading_photo_keyboard,
)

from services.api_fallback import smart_generate_interior

from states.fsm import CreationStates, WorkMode

from utils.texts import (
    ROOM_CHOICE_TEXT,
    CHOOSE_STYLE_TEXT,
    ERROR_INSUFFICIENT_BALANCE,
    ROOM_TYPES,
    STYLE_TYPES,
    UPLOADING_PHOTO_TEMPLATES,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()

PHOTO_SEND_LOG = {}

def log_photo_send(user_id: int, method: str, message_id: int, request_id: str = None, operation: str = ""):
    """Логирует отправку фото для диагностики"""
    if user_id not in PHOTO_SEND_LOG:
        PHOTO_SEND_LOG[user_id] = []
    
    timestamp = datetime.now().isoformat()
    rid = request_id or str(uuid.uuid4())[:8]
    
    entry = {
        'timestamp': timestamp,
        'method': method,
        'message_id': message_id,
        'request_id': rid,
        'operation': operation
    }
    
    PHOTO_SEND_LOG[user_id].append(entry)
    
    logger.warning(
        f"📊 [PHOTO_LOG] user_id={user_id}, method={method}, msg_id={message_id}, "
        f"request_id={rid}, operation={operation}, timestamp={timestamp}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 3] ВЫБОР ТИПА ПОМЕЩЕНИЯ
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """
    🏠 [SCREEN 3] Меню выбора типа помещения
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.set_state(CreationStates.room_choice)
        
        text = ROOM_CHOICE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        current_msg = callback.message
        
        if current_msg.photo:
            logger.warning(
                f"⚠️ [SCREEN 3] Current msg has PHOTO, creating NEW text menu"
            )
            
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=get_room_choice_keyboard(),
                parse_mode="Markdown"
            )
            
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'room_choice')
            
            logger.info(f"✅ [SCREEN 3] New text menu created, msg_id={new_msg.message_id}")
        else:
            await edit_menu(
                callback=callback,
                state=state,
                text=text,
                keyboard=get_room_choice_keyboard(),
                show_balance=False,
                screen_code='room_choice'
            )
            
            logger.info(f"✅ [SCREEN 3] Text menu edited")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 3 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 3→4] ОБРАБОТЧИК ВЫБОРА КОМНАТЫ
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.room_choice),
    F.data.startswith("room_")
)
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    🏠 [SCREEN 3→4] Обработчик выбора комнаты
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        room = callback.data.replace("room_", "")
        
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.update_data(selected_room=room)
        await state.set_state(CreationStates.choose_style_1)
        
        text = CHOOSE_STYLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        current_msg = callback.message
        
        if current_msg.photo:
            logger.warning(f"⚠️ [SCREEN 4] Current msg has PHOTO, creating NEW text menu")
            
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=get_choose_style_1_keyboard(),
                parse_mode="Markdown"
            )
            
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'choose_style_1')
            
            logger.info(f"✅ [SCREEN 4] New text menu created")
        else:
            await edit_menu(
                callback=callback,
                state=state,
                text=text,
                keyboard=get_choose_style_1_keyboard(),
                show_balance=False,
                screen_code='choose_style_1'
            )
            
            logger.info(f"✅ [SCREEN 4] Text menu edited")
        
        logger.info(f"[SCREEN 3→4] Selected room: {room}, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 3→4 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе комнаты", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════
# 🎨 [SCREEN 4] ВЫБОР СТИЛЯ (страница 1)
# ═════════════════════════════════════════════════════════════════════════════

# КНОПКА: Показать вторую страницу стилей
@router.callback_query(
    StateFilter(CreationStates.choose_style_1),
    F.data == "choose_style_2"
)
async def choose_style_2_menu(callback: CallbackQuery, state: FSMContext):
    """
    🎨 [SCREEN 4→5] Показать вторую страницу стилей
    """
    user_id = callback.from_user.id
    
    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.set_state(CreationStates.choose_style_2)
        
        text = CHOOSE_STYLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        current_msg = callback.message
        
        if current_msg.photo:
            logger.warning(f"⚠️ [SCREEN 5] Current msg has PHOTO, creating NEW text menu")
            
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=get_choose_style_2_keyboard(),
                parse_mode="Markdown"
            )
            
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(callback.message.chat.id, user_id, new_msg.message_id, 'choose_style_2')
        else:
            await edit_menu(
                callback=callback,
                state=state,
                text=text,
                keyboard=get_choose_style_2_keyboard(),
                show_balance=False,
                screen_code='choose_style_2'
            )
        
        logger.info(f"[SCREEN 4→5] Page 2 shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 4→5 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════
# 🎨 [SCREEN 5] ВЫБОР СТИЛЯ (страница 2)
# ═════════════════════════════════════════════════════════════════════════════

# КНОПКА: Вернуться на первую страницу
@router.callback_query(
    StateFilter(CreationStates.choose_style_2),
    F.data == "styles_page_1"
)
async def choose_style_1_menu(callback: CallbackQuery, state: FSMContext):
    """
    🎨 [SCREEN 5→4] Вернуться на первую страницу стилей
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        await state.set_state(CreationStates.choose_style_1)
        
        text = CHOOSE_STYLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        current_msg = callback.message
        
        if current_msg.photo:
            logger.warning(f"⚠️ [SCREEN 4] Current msg has PHOTO, creating NEW text menu")
            
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=get_choose_style_1_keyboard(),
                parse_mode="Markdown"
            )
            
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'choose_style_1')
        else:
            await edit_menu(
                callback=callback,
                state=state,
                text=text,
                keyboard=get_choose_style_1_keyboard(),
                show_balance=False,
                screen_code='choose_style_1'
            )
        
        logger.info(f"[SCREEN 5→4] Back to page 1, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 5→4 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════
# 🔥 [SCREEN 4-5→6] ГЕНЕРАЦИЯ ДИЗАЙНА - ГЛАВНАЯ ФУНКЦИЯ
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    🔥 [SCREEN 4-5→6] ГЕНЕРИРУЕТ ДИЗАЙН
    """
    style = callback.data.replace("style_", "", 1)
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id
    request_id = str(uuid.uuid4())[:8]

    logger.warning(f"🔍 [SCREEN 6] START: request_id={request_id}, user_id={user_id}, style={style}")

    await db.log_activity(user_id, f'style_{style}')

    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')
    work_mode = data.get('work_mode')

    if not photo_id or not room:
        await callback.answer(
            "⚠️ Сессия устарела. Загрузите фото заново.",
            show_alert=True
        )
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
                show_balance=False,
                screen_code='no_balance'
            )
            return

    if not is_admin:
        await db.decrease_balance(user_id)

    progress_msg = None
    current_msg = callback.message
    balance_text = await add_balance_and_mode_to_text(
        f"⚡ Генерирую {style} дизайн для {room}. Это может занять до 3 минут...",
        user_id,
        work_mode
    )
    
    try:
        if current_msg.photo:
            await callback.message.delete()
            logger.warning(f"📊 [SCREEN 6] Deleted media msg")
            
            progress_msg = await callback.message.answer(
                text=balance_text,
                parse_mode="HTML"
            )
            logger.warning(f"📊 [SCREEN 6] Progress msg sent")
            
        else:
            progress_msg = await callback.message.edit_text(
                text=balance_text,
                parse_mode="HTML"
            )
            logger.warning(f"📊 [SCREEN 6] Edited text menu to progress")
        
    except Exception as e:
        logger.warning(f"⚠️ [SCREEN 6] Failed to show progress: {e}")
        progress_msg = None
    
    await callback.answer()

    pro_settings = await db.get_user_pro_settings(user_id)
    use_pro = pro_settings.get('pro_mode', False)
    logger.info(f"🔧 PRO MODE для user_id={user_id}: {use_pro}")

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
        
        design_caption = f"""✨ <b>Идея для дизайна {room_display} в стиле {style_display} готова!</b>
        """
        
        menu_caption = f"""🎨 <b>Что дальше?
Есть 20 готовых стилей!</b>

Выберите действие:
🔄 Создать другой стиль.
🏠 Выбрать режим работы.

📊 Баланс: <b>{balance}</b> генераций | 🔧 Режим: <b>{work_mode}</b>"""
        
        photo_sent = False

        # ПОПЫТКА 1: Прямая отправка
        try:
            logger.warning(f"📊 [SCREEN 6] ATTEMPT 1: answer_photo")
            
            photo_msg = await callback.message.answer_photo(
                photo=result_image_url,
                caption=design_caption,
                parse_mode="HTML",
            )
            
            photo_sent = True
            logger.warning(f"📊 [SCREEN 6] SUCCESS: answer_photo")
            log_photo_send(user_id, "answer_photo", photo_msg.message_id, request_id, "style_choice")
            
            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
            
            # Отправляем меню
            try:
                menu_msg = await callback.message.answer(
                    text=menu_caption,
                    parse_mode="HTML",
                    reply_markup=get_post_generation_keyboard()
                )
                logger.warning(f"📊 [SCREEN 6] MENU SENT")
                
                await state.update_data(photo_message_id=photo_msg.message_id, menu_message_id=menu_msg.message_id)
                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                
            except Exception as menu_error:
                logger.warning(f"⚠️ [SCREEN 6] Failed to send menu: {menu_error}")
            
            # Удаляем прогресс
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception:
                    pass

        except Exception as url_error:
            logger.warning(f"📊 [SCREEN 6] FAILED ATTEMPT 1: {url_error}")

            # ПОПЫТКА 2: Загружка локально
            try:
                logger.warning(f"📊 [SCREEN 6] ATTEMPT 2: BufferedInputFile")

                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()

                            photo_msg = await callback.message.answer_photo(
                                photo=BufferedInputFile(photo_data, filename="design.jpg"),
                                caption=design_caption,
                                parse_mode="HTML",
                            )
                            
                            photo_sent = True
                            logger.warning(f"📊 [SCREEN 6] SUCCESS: BufferedInputFile")
                            log_photo_send(user_id, "answer_photo_buffered", photo_msg.message_id, request_id, "style_choice")
                            
                            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
                            
                            # Отправляем меню
                            try:
                                menu_msg = await callback.message.answer(
                                    text=menu_caption,
                                    parse_mode="HTML",
                                    reply_markup=get_post_generation_keyboard()
                                )
                                await state.update_data(photo_message_id=photo_msg.message_id, menu_message_id=menu_msg.message_id)
                                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                                
                            except Exception as menu_error:
                                logger.warning(f"⚠️ [SCREEN 6] Failed to send menu: {menu_error}")
                            
                            # Удаляем прогресс
                            if progress_msg:
                                try:
                                    await progress_msg.delete()
                                except Exception:
                                    pass

            except Exception as buffer_error:
                logger.error(f"📊 [SCREEN 6] FAILED ATTEMPT 2: {buffer_error}")

        # FALLBACK: Все попытки не сработали
        if not photo_sent:
            if not is_admin:
                await db.increase_balance(user_id, 1)
            
            logger.error(f"📊 [SCREEN 6] ALL ATTEMPTS FAILED")
            
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception:
                    pass
            
            await callback.message.answer(
                text="❌ Ошибка при отправке изображения. Баланс возвращен. Попробуйте ещё раз.",
                parse_mode="Markdown"
            )
            return

        # Переход на SCREEN 6
        await state.set_state(CreationStates.post_generation)

        logger.warning(f"📊 [SCREEN 6] GENERATION SUCCESS")
        logger.info(f"[SCREEN 6] Generated for {room}/{style}, user_id={user_id}")

    else:
        # ОШИБКА ГЕНЕРАЦИИ
        if not is_admin:
            await db.increase_balance(user_id, 1)
        
        logger.error(f"📊 [SCREEN 6] GENERATION_FAILED")
        
        if progress_msg:
            try:
                await progress_msg.delete()
            except Exception:
                pass
        
        await callback.message.answer(
            text="❌ Ошибка генерации. Баланс возвращен. Попробуйте ещё раз.",
            parse_mode="Markdown"
        )


# ═════════════════════════════════════════════════════════════════════════════
# 🔄 [SCREEN 6→4] СМЕНА СТИЛЯ ПОСЛЕ ГЕНЕРАЦИИ
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    """
    🔄 [SCREEN 6→4] Смена стиля после генерации
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id

    logger.warning(f"🔍 [SCREEN 6→4] START: user_id={user_id}")

    data = await state.get_data()
    work_mode = data.get('work_mode')

    try:
        await state.set_state(CreationStates.choose_style_1)
        
        text = CHOOSE_STYLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        await callback.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=get_choose_style_1_keyboard(),
            parse_mode="Markdown"
        )
        
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'choose_style_1')
        
        logger.info(f"✅ [SCREEN 6→4] Menu edited")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 6→4 failed: {e}", exc_info=True)
        await callback.answer(
            "❌ Ошибка при смене стиля. Попробуйте ещё раз.",
            show_alert=True
        )


# ═════════════════════════════════════════════════════════════════════════════
# 📈 [SCREEN 6→2] ЗАГРУЗКА НОВОГО ФОТО ПОСЛЕ ГЕНЕРАЦИИ
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "uploading_photo"
)
async def new_photo_after_gen(callback: CallbackQuery, state: FSMContext):
    """
    📈 [SCREEN 6→2] Загружка нового фото после генерации
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id

    logger.warning(f"🔍 [SCREEN 6→2] START: user_id={user_id}")

    data = await state.get_data()
    work_mode = data.get('work_mode', 'new_design')

    try:
        await state.set_state(CreationStates.uploading_photo)
        
        text = UPLOADING_PHOTO_TEMPLATES.get(work_mode, "📄 Загрузите фото помещения")
        
        await callback.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=get_uploading_photo_keyboard(has_previous_photo=True),
            parse_mode="Markdown"
        )
        
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'uploading_photo')
        
        await state.update_data(
            menu_message_id=menu_message_id,
            photo_uploaded=False,
            new_photo=True
        )
        
        logger.info(f"✅ [SCREEN 6→2] Menu edited")
        logger.info(f"[SCREEN 6→2] Back to photo upload, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 6→2 failed: {e}", exc_info=True)
        await callback.answer(
            "❌ Ошибка при переходе на загружку фото. Попробуйте ещё раз.",
            show_alert=True
        )
