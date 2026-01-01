# ===== PHASE 2: NEW_DESIGN MODE (SCREEN 3-6) =====


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
    POST_GENERATION_MENU_TEXT,  # ✅ [2025-12-31 16:50] ДОБАВЛЕН ИМПОРТ
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()

# ===== ДИАГНОСТИКА: Глобальный трекер отправок фото =====
# [2025-12-30 01:47] 🔍 DIAGNOSTICS
PHOTO_SEND_LOG = {}  # Глобальный трекер: user_id -> [(timestamp, method, message_id, request_id)]

def log_photo_send(user_id: int, method: str, message_id: int, request_id: str = None, operation: str = ""):
    """
    🔍 ДИАГНОСТИКА: Логируем каждые отправки фото
    
    Методы: answer_photo, send_photo, edit_message_media, edit_message_caption
    """
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
    
    # Детальное логирование
    logger.warning(
        f"📊 [PHOTO_LOG] user_id={user_id}, method={method}, msg_id={message_id}, "
        f"request_id={rid}, operation={operation}, timestamp={timestamp}"
    )
    
    # Оверфлоу диагностики
    if len(PHOTO_SEND_LOG[user_id]) > 1:
        logger.error(
            f"🔥 [PHOTO_DOUBLE_SEND] user_id={user_id}, "
            f"count={len(PHOTO_SEND_LOG[user_id])}, "
            f"all={PHOTO_SEND_LOG[user_id]}"
        )


# ===== SCREEN 3: ROOM_CHOICE (NEW_DESIGN только) =====
# [2025-12-29] НОВОЕ (V3)
# [2025-12-30 17:00] 🔥 FIX: НЕ редактируем медиа-сообщение, создаем новое текстовое меню
@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3: Меню выбора комнаты (ROOM_CHOICE)
    Только для режима NEW_DESIGN
    
    [2025-12-30 17:00] 🔥 FIX:
    - Если menu_message_id содержит медиа (фото) - НЕ редактируем его
    - Создаем новое текстовое меню вместо попытки edit_message_text на медиа
    - Старое медиа-сообщение остаётся в истории (не удаляем автоматически)
    
    Log: "[V3] NEW_DESIGN+ROOM_CHOICE - menu shown, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        await state.set_state(CreationStates.room_choice)
        
        text = f"🏠 **Выберите тип помещения**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        # ✅ [2025-12-30 17:00] ПРАВИЛЬНАЯ ЛОГИКА:
        # Если текущее сообщение имеет фото (media) - создаем новое текстовое меню
        # Не пытаемся редактировать медиа с помощью edit_message_text!
        
        current_msg = callback.message
        
        # Проверяем, есть ли в сообщении фото
        if current_msg.photo:
            logger.warning(
                f"⚠️ [ROOM_CHOICE] Current msg has PHOTO (id={current_msg.message_id}), "
                f"creating NEW text menu instead of edit_message_text"
            )
            
            # Создаем НОВОЕ текстовое меню
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=get_room_choice_keyboard(),
                parse_mode="Markdown"
            )
            
            # Сохраняем НОВЫЙ message_id
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'room_choice')
            
            logger.info(f"✅ [ROOM_CHOICE] New text menu created, msg_id={new_msg.message_id}")
        else:
            # Текстовое сообщение - редактируем обычно
            await edit_menu(
                callback=callback,
                state=state,
                text=text,
                keyboard=get_room_choice_keyboard(),
                screen_code='room_choice'
            )
            
            logger.info(f"✅ [ROOM_CHOICE] Text menu edited, msg_id={current_msg.message_id}")
        
        logger.info(f"[V3] NEW_DESIGN+ROOM_CHOICE - menu shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] ROOM_CHOICE_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== SCREEN 3→4: ROOM_CHOICE_HANDLER =====
# [2025-12-29] НОВОЕ (V3)
# [2025-12-30 01:29] ✅ FIX: Возвращен work_mode
# [2025-12-30 17:00] 🔥 FIX: Аналогичная логика - проверяем медиа перед edit_menu
@router.callback_query(
    StateFilter(CreationStates.room_choice),
    F.data.startswith("room_")
)
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3→4: Обработчик выбора комнаты
    Сохраняет выбор и переходит на экран выбора стиля (SCREEN 4)
    
    [2025-12-30 17:00] 🔥 FIX:
    - Проверяем медиа перед вызовом edit_menu
    - Если медиа - создаем новое меню вместо редактирования
    
    Log: "[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        room = callback.data.replace("room_", "")
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        # Сохраняем выбор комнаты в FSM
        await state.update_data(selected_room=room)
        await state.set_state(CreationStates.choose_style_1)
        
        text = f"🎨 **Выберите стиль дизайна**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        # ✅ [2025-12-30 17:00] Проверяем медиа
        current_msg = callback.message
        
        if current_msg.photo:
            logger.warning(
                f"⚠️ [ROOM_CHOICE_HANDLER] Current msg has PHOTO (id={current_msg.message_id}), "
                f"creating NEW text menu"
            )
            
            # Создаем НОВОЕ текстовое меню
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=get_choose_style_1_keyboard(),
                parse_mode="Markdown"
            )
            
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'choose_style_1')
            
            logger.info(f"✅ [ROOM_CHOICE_HANDLER] New text menu created, msg_id={new_msg.message_id}")
        else:
            # Текстовое сообщение - редактируем обычно
            await edit_menu(
                callback=callback,
                state=state,
                text=text,
                keyboard=get_choose_style_1_keyboard(),
                screen_code='choose_style_1'
            )
            
            logger.info(f"✅ [ROOM_CHOICE_HANDLER] Text menu edited, msg_id={current_msg.message_id}")
        
        logger.info(f"[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] ROOM_CHOICE_HANDLER failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе комнаты", show_alert=True)


# ===== SCREEN 4: CHOOSE_STYLE_1 (Первая страница стилей) =====
# [2025-12-29] НОВОЕ (V3)
# [2025-12-30 17:00] 🔥 FIX: Проверка медиа перед edit_menu
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
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        await state.set_state(CreationStates.choose_style_1)
        
        text = f"🎨 **Выберите стиль дизайна (страница 1)**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        current_msg = callback.message
        
        if current_msg.photo:
            logger.warning(f"⚠️ [CHOOSE_STYLE_1] Current msg has PHOTO, creating NEW text menu")
            
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
                screen_code='choose_style_1'
            )
        
        logger.info(f"[V3] NEW_DESIGN+CHOOSE_STYLE - back to page 1, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] CHOOSE_STYLE_1_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== SCREEN 5: CHOOSE_STYLE_2 (Вторая страница стилей) =====
# [2025-12-29] НОВОЕ (V3)
# [2025-12-30 17:00] 🔥 FIX: Проверка медиа перед edit_menu
@router.callback_query(
    StateFilter(CreationStates.choose_style_1),
    F.data == "styles_page_2"
)
async def choose_style_2_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 5: Показать вторую страницу стилей
    
    Log: "[V3] NEW_DESIGN+CHOOSE_STYLE - page 2 shown, user_id={user_id}"
    """
    user_id = callback.from_user.id
    
    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        await state.set_state(CreationStates.choose_style_2)
        
        text = f"🎨 **Выберите стиль дизайна (страница 2)**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        current_msg = callback.message
        
        if current_msg.photo:
            logger.warning(f"⚠️ [CHOOSE_STYLE_2] Current msg has PHOTO, creating NEW text menu")
            
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
                screen_code='choose_style_2'
            )
        
        logger.info(f"[V3] NEW_DESIGN+CHOOSE_STYLE - page 2 shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] CHOOSE_STYLE_2_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== SCREEN 4-5 to 6: STYLE_CHOICE_HANDLER (Выбор стиля + генерация) =====
# [2025-12-29] ОБНОВЛЕНО (V3) - Добавлена установка состояния.post_generation
# [2025-12-30 01:20] 🔥 BUGFIX #2: Убрать answer_photo() в fallback - редактировать меню, не отправлять новое
# [2025-12-30 01:47] 🔍 CRITICAL DIAGNOSTICS: Добавить логирование для трекинга двойной отправки
# [2025-12-30 17:00] 🔥 MAJOR FIX: Правильная обработка медиа, удаление старых при fallback
# [2025-12-31 10:19] 🔥 CRITICAL HOTFIX: Добавить save_chat_menu() после КАЖДОЙ успешной отправки фото
# [2025-12-31 16:00] 🔥 CRITICAL REWRITE: НИКОГДА НЕ удаляем старый дизайн! СОЗДАЕМ новое сообщение!
# [2025-12-31 16:30] 🔥 CRITICAL FIX: УДАЛЯЕМ старое меню со стилями ПЕРЕД созданием нового!
# [2025-12-31 16:40] 🔥 HOTFIX: ИСПРАВИТЬ callback.message.bot → callback.bot для get_message!
# [2025-12-31 16:50] 🔥 HOTFIX: ИСПОЛЬЗОВАТЬ POST_GENERATION_MENU_TEXT для caption дизайна!
# [2026-01-01 16:47] 🔥 CRITICAL FIX: ИСПОЛЬЗОВАТЬ HTML вместо Markdown в caption для избежания ошибок парсинга!
@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    SCREEN 4-5→6: Обработчик выбора стиля и генерация дизайна
    
    🔥 CRITICAL REWRITE [2025-12-31 16:30]:
    АРХИТЕКТУРА ПРАВИЛЬНАЯ:
    1️⃣ Юзер в меню стилей (текстовое сообщение с кнопками) - msg_id=7487
    2️⃣ Нажимает "выбрать стиль modern"
    3️⃣ СРАЗУ УДАЛЯЕМ ТЕКСТОВОЕ МЕНЮ СО СТИЛЯМИ (msg_id=7487)
    4️⃣ Отправляем НОВОЕ сообщение "⏳ Генерируем modern..."
    5️⃣ Генерируем изображение
    6️⃣ Отправляем НОВОЕ сообщение с дизайном + кнопки
    
    ✅ РЕЗУЛЬТАТ: 
       - СТАРЫЕ дизайны остаются в истории
       - НОВЫЙ дизайн создается отдельно
       - Меню со стилями удаляется (чистый интерфейс)
    
    [2026-01-01 16:47] 🔥 CRITICAL FIX:
    - Использовать HTML вместо Markdown для caption
    - Это избегает ошибок парсинга markdown
    
    ❌ НИКОГДА НЕ удаляем сгенерированные дизайны!
    
    Log: "[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}"
    """
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id
    request_id = str(uuid.uuid4())[:8]  # ✅ DIAGNOSTICS: request_id для трекинга

    logger.warning(f"🔍 [DIAG_START] request_id={request_id}, user_id={user_id}, style={style}")

    await db.log_activity(user_id, f'style_{style}')

    # Проверка наличия данных
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')
    work_mode = data.get('work_mode')  # ✅ Получаем work_mode

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

    # 🔥 [2025-12-31 16:30] ПРАВИЛЬНАЯ ЛОГИКА:
    # 1️⃣ УДАЛЯЕМ текстовое меню со стилями (чистим интерфейс)
    try:
        await callback.message.delete()
        logger.warning(f"📊 [DIAG] request_id={request_id} STEP_1: Deleted style menu msg_id={menu_message_id}")
    except Exception as e:
        logger.warning(f"⚠️ [DIAG] request_id={request_id} Failed to delete style menu: {e}")
    
    # 2️⃣ Отправляем прогресс-сообщение
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
        logger.warning(f"📊 [DIAG] request_id={request_id} STEP_2: Progress msg sent, msg_id={progress_msg.message_id}")
    except Exception as e:
        logger.warning(f"⚠️ [DIAG] request_id={request_id} Failed to send progress msg: {e}")
    
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
        # 🔥 [2026-01-01 16:47] ИСПОЛЬЗОВАТЬ HTML ВМЕСТО MARKDOWN!
        # Получаем баланс и режим для вывода
        balance = await db.get_balance(user_id)
        
        # Формируем caption в HTML формате (безопасно парсится Telegram)
        post_gen_caption = f"""✨ <b>Ваш новый дизайн готов!</b>

🎨 Что дальше?

Выберите действие:
🔄 Другой стиль - примеря другой стиль на эту комнату
🏠 Главное меню - вернуться в главное меню

📊 Баланс: <b>{balance}</b> генераций | 🔧 Режим: <b>{work_mode}</b>"""
        
        photo_sent = False

        # 🔥 [2025-12-31 16:00] ПОПЫТКА 1: Отправляем фото с результатом
        try:
            logger.warning(f"📊 [DIAG] request_id={request_id} ATTEMPT_1: answer_photo (new design)")
            
            # ОТПРАВЛЯЕМ НОВОЕ ФОТО (не редактируем старое!)
            photo_msg = await callback.message.answer_photo(
                photo=result_image_url,
                caption=post_gen_caption,
                parse_mode="HTML",  # 🔥 HTML вместо Markdown!
                reply_markup=get_post_generation_keyboard()
            )
            
            photo_sent = True
            logger.warning(f"📊 [DIAG] request_id={request_id} SUCCESS_ATTEMPT_1: answer_photo, msg_id={photo_msg.message_id}")
            log_photo_send(user_id, "answer_photo", photo_msg.message_id, request_id, "style_choice")
            
            # 🔥 [2025-12-31 10:19] CRITICAL: Сохраняем в БД СРАЗУ после успешной отправки
            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
            logger.warning(f"📊 [DIAG] request_id={request_id} SAVED_TO_DB after ATTEMPT_1")
            
            # Удаляем прогресс-сообщение
            if progress_msg:
                try:
                    await progress_msg.delete()
                    logger.warning(f"📊 [DIAG] request_id={request_id} Deleted progress msg")
                except Exception:
                    pass

        except Exception as url_error:
            logger.warning(f"📊 [DIAG] request_id={request_id} FAILED_ATTEMPT_1: {url_error}")

            # ===== ПОПЫТКА 2: FALLBACK через BufferedInputFile =====
            try:
                logger.warning(f"📊 [DIAG] request_id={request_id} ATTEMPT_2: BufferedInputFile")

                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()

                            photo_msg = await callback.message.answer_photo(
                                photo=BufferedInputFile(photo_data, filename="design.jpg"),
                                caption=post_gen_caption,
                                parse_mode="HTML",  # 🔥 HTML вместо Markdown!
                                reply_markup=get_post_generation_keyboard()
                            )
                            
                            logger.warning(f"📊 [DIAG] request_id={request_id} ATTEMPT_2_PHOTO_SENT: msg_id={photo_msg.message_id}")
                            log_photo_send(user_id, "answer_photo_buffered", photo_msg.message_id, request_id, "style_choice")
                            
                            photo_sent = True
                            logger.warning(f"📊 [DIAG] request_id={request_id} SUCCESS_ATTEMPT_2: answer_photo_buffered")
                            
                            # 🔥 [2025-12-31 10:19] CRITICAL: Сохраняем в БД СРАЗУ после успешной отправки
                            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
                            logger.warning(f"📊 [DIAG] request_id={request_id} SAVED_TO_DB after ATTEMPT_2")
                            
                            # Удаляем прогресс-сообщение
                            if progress_msg:
                                try:
                                    await progress_msg.delete()
                                except Exception:
                                    pass
                        else:
                            logger.error(f"📊 [DIAG] request_id={request_id} ATTEMPT_2 HTTP {resp.status}")

            except Exception as buffer_error:
                logger.error(f"📊 [DIAG] request_id={request_id} FAILED_ATTEMPT_2: {buffer_error}")

        # Если все попытки не сработали
        if not photo_sent:
            # Возвращаем баланс
            if not is_admin:
                await db.increase_balance(user_id, 1)
            
            logger.error(f"📊 [DIAG] request_id={request_id} ALL_ATTEMPTS_FAILED for user_id={user_id}")
            
            # Удаляем прогресс-сообщение
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception:
                    pass
            
            await callback.message.answer(
                text="❌ Ошибка при отправке изображения. Баланс возвращен. Попробуйте еще раз.",
                parse_mode="Markdown"
            )
            return

        # УСПЕХ - Устанавливаем состояние POST_GENERATION
        await state.set_state(CreationStates.post_generation)
        await state.update_data(menu_message_id=photo_msg.message_id)

        logger.warning(f"📊 [DIAG] request_id={request_id} SUCCESS_END for user_id={user_id}")
        logger.info(f"[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}")
        logger.info(f"[V3] NEW_DESIGN+POST_GENERATION - ready, user_id={user_id}")

    else:
        # Ошибка генерации - возвращаем баланс
        if not is_admin:
            await db.increase_balance(user_id, 1)
        
        logger.error(f"📊 [DIAG] request_id={request_id} GENERATION_FAILED for user_id={user_id}")
        
        # Удаляем прогресс-сообщение
        if progress_msg:
            try:
                await progress_msg.delete()
            except Exception:
                pass
        
        await callback.message.answer(
            text="❌ Ошибка генерации. Баланс возвращен. Попробуйте еще раз.",
            parse_mode="Markdown"
        )


# ===== SCREEN 6: POST_GENERATION_MENU (Меню после генерации) =====
# [2025-12-29] НОВОЕ (V3)
# [2025-12-30 17:00] 🔥 FIX: Проверка медиа перед edit_menu
# [2025-12-31 10:19] 🔥 CRITICAL HOTFIX: Добавить save_chat_menu() сразу после edit_message_caption
@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "post_generation"
)
async def post_generation_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 6: Меню после генерации (POST_GENERATION)
    
    [2025-12-31 10:19] 🔥 CRITICAL HOTFIX:
    - Добавить save_chat_menu() СРАЗУ после edit_message_caption()
    - Без этого при краше бота menu_message_id не обновится
    
    Log: "[V3] NEW_DESIGN+POST_GENERATION - menu shown, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        # Будем на этом экране
        await state.set_state(CreationStates.post_generation)
        
        # 🔥 [2026-01-01 16:47] Используем HTML для caption
        text = f"""✨ <b>Ваш новый дизайн готов!</b>

🎨 Что дальше?

Выберите действие:
🔄 Другой стиль - примеря другой стиль на эту комнату
🏠 Главное меню - вернуться в главное меню

📊 Баланс: <b>{balance}</b> генераций | 🔧 Режим: <b>{work_mode}</b>"""
        
        # ✅ Проверяем медиа перед edit_menu
        current_msg = callback.message
        
        if current_msg.photo:
            # Это медиа-сообщение с фото - редактируем подпись
            try:
                await callback.message.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=current_msg.message_id,
                    caption=text,
                    reply_markup=get_post_generation_keyboard(),
                    parse_mode="HTML"  # 🔥 HTML вместо Markdown!
                )
                logger.info(f"✅ [POST_GENERATION] Caption edited for media msg_id={current_msg.message_id}")
                
                # 🔥 [2025-12-31 10:19] CRITICAL: Сохраняем СРАЗУ после edit_message_caption!
                await db.save_chat_menu(chat_id, user_id, current_msg.message_id, 'post_generation')
                logger.warning(f"📊 [POST_GENERATION] SAVED_TO_DB after edit_message_caption")
                
            except Exception as e:
                logger.warning(f"⚠️ [POST_GENERATION] Failed to edit caption: {e}, trying edit_menu")
                # Fallback на текстовое меню
                await edit_menu(
                    callback=callback,
                    state=state,
                    text="✅ Выбери что дальше",
                    keyboard=get_post_generation_keyboard(),
                    screen_code='post_generation'
                )
        else:
            # Текстовое сообщение - редактируем обычно
            await edit_menu(
                callback=callback,
                state=state,
                text="✅ Выбери что дальше",
                keyboard=get_post_generation_keyboard(),
                screen_code='post_generation'
            )
        
        logger.info(f"[V3] NEW_DESIGN+POST_GENERATION - menu shown, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] POST_GENERATION_MENU failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== POST-GENERATION: CHANGE_STYLE (Смена стиля после генерации) =====
# [2025-12-29] НОВОЕ (V3)
# [2025-12-30 17:00] 🔥 FIX: Проверка медиа перед edit_menu
# [2025-12-31 16:00] 🔥 CRITICAL REWRITE: НЕ редактируем фото, создаем НОВОЕ меню!
# [2025-12-31 16:30] 🔥 CRITICAL FIX: УДАЛЯЕМ старое меню со стилями ДО создания нового!
# [2025-12-31 16:40] 🔥 HOTFIX: ИСПРАВИТЬ callback.message.bot.get_message → callback.bot.get_message!
@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    ПОСЛЕ генерации: смена стиля
    
    [2025-12-31 16:40] 🔥 HOTFIX:
    - Правильное использование callback.bot.get_message() вместо callback.message.bot.get_message()
    - Проверяем старое меню перед удалением
    - Создаем новое меню выбора стилей
    
    Логика: восстановление в состояние choose_style для новой генерации
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')
    work_mode = data.get('work_mode')
    old_menu_id = data.get('menu_message_id')

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

    # 🔥 [2025-12-31 16:40] ШАГ 1: УДАЛЯЕМ СТАРОЕ МЕНЮ СО СТИЛЯМИ (если оно есть)
    # ПРАВИЛЬНЫЙ СИНТАКСИС: callback.bot.get_message (не callback.message.bot)
    if old_menu_id:
        try:
            msg_info = await callback.bot.get_message(chat_id, old_menu_id)
            # Если это текстовое меню (не фото) - удаляем
            if msg_info and not msg_info.photo:
                await callback.bot.delete_message(chat_id, old_menu_id)
                logger.warning(f"🗑️ [CHANGE_STYLE] Deleted old style menu: msg_id={old_menu_id}")
        except Exception as delete_error:
            logger.warning(f"⚠️ [CHANGE_STYLE] Could not delete old menu: {delete_error}")
    
    # 🔥 [2025-12-31 16:30] ШАГ 2: СОЗДАЕМ НОВОЕ МЕНЮ
    # Выбор стиля снова
    await state.set_state(CreationStates.choose_style_1)

    balance = await db.get_balance(user_id)
    text = f"🎨 **Выберите стиль дизайна**"
    text = await add_balance_and_mode_to_text(text, user_id, work_mode)

    # ✅ СОЗДАЕМ НОВОЕ ТЕКСТОВОЕ МЕНЮ ДЛЯ ВЫБОРА СТИЛЯ
    try:
        new_msg = await callback.message.answer(
            text=text,
            reply_markup=get_choose_style_1_keyboard(),
            parse_mode="Markdown"
        )
        
        # ✅ Сохраняем НОВЫЙ message_id
        await state.update_data(menu_message_id=new_msg.message_id)
        await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'choose_style_1')
        
        logger.info(f"✅ [CHANGE_STYLE] New style menu created, msg_id={new_msg.message_id}, user_id={user_id}")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to create new style menu: {e}")
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)
        return

    try:
        await callback.answer()
    except Exception:
        pass

    logger.info(f"[V3] NEW_DESIGN+CHANGE_STYLE - new menu sent, user_id={user_id}")
