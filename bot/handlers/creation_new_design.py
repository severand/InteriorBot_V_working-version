# ===== PHASE 2: NEW_DESIGN MODE (SCREEN 3-6) =====
# 📋 ОПИСАНИЕ:
# Этот файл содержит ВСЕ обработчики для режима "Создать новый дизайн"
# Управляет переходом между 4 экранами: SCREEN 3 → SCREEN 4 → SCREEN 5 → SCREEN 6
#
# АРХИТЕКТУРА:
# SCREEN 3: room_choice_menu() - Выбор комнаты (10 типов)
# SCREEN 4: choose_style_1_menu() - Выбор стиля (страница 1, 12 стилей)
# SCREEN 5: choose_style_2_menu() - Выбор стиля (страница 2, 12 стилей)
# SCREEN 6: style_choice_handler() - ГЕНЕРАЦИЯ дизайна 🔥
# SCREEN 6: post_generation_menu() - Меню после генерации
# SCREEN 6: change_style_after_gen() - Смена стиля после генерации

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


# ===== SCREEN 3: ROOM_CHOICE =====
# 📍 ЭКРАН: Выбор типа помещения
# 📊 FSM STATE: CreationStates.room_choice
# 🎯 НАЗНАЧЕНИЕ: Показать меню с 10 типами комнат (кухня, спальня, ванная, etc.)
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 2 (загрузка фото)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 4 (выбор стиля, страница 1)
#
# [2025-12-30 17:00] 🔥 FIX: НЕ редактируем медиа-сообщение, создаем новое текстовое меню
@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """
    [SCREEN 3] Меню выбора комнаты (ROOM_CHOICE)
    
    📍 ПУТЬ: user_id → [SCREEN 2: загрузка фото] → [SCREEN 3: выбор комнаты] → [SCREEN 4: стили]
    
    🔌 ТРИГГЕР: callback_data == "room_choice"
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.room_choice
    
    [2025-12-30 17:00] 🔥 FIX:
    - Если текущее сообщение содержит ФОТО (media) → НЕ редактируем его
    - Создаем НОВОЕ текстовое меню вместо попытки edit_message_text на медиа
    - Старое медиа-сообщение остаётся в истории (не удаляем автоматически)
    
    📤 ОТПРАВЛЯЕТ:
    - Текстовое сообщение: "🏠 Выберите тип помещения"
    - Inline keyboard: 10 кнопок с типами комнат (2 в ряд)
    - Показывает баланс и режим
    
    💾 СОХРАНЯЕТ В БД:
    - menu_message_id (для отслеживания)
    - screen_code = 'room_choice'
    
    📝 LOG: "[V3] NEW_DESIGN+ROOM_CHOICE - menu shown, user_id={user_id}"
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
# 📍 ЭКРАН: Обработчик выбора комнаты
# 📊 FSM STATE: CreationStates.room_choice → CreationStates.choose_style_1
# 🎯 НАЗНАЧЕНИЕ: Обработать клик на кнопку комнаты, сохранить выбор, перейти к стилям
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 3 (выбор комнаты)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 4 (выбор стиля, страница 1)
#
# [2025-12-30 17:00] 🔥 FIX: Аналогичная логика - проверяем медиа перед edit_menu
@router.callback_query(
    StateFilter(CreationStates.room_choice),
    F.data.startswith("room_")
)
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    [SCREEN 3→4] Обработчик выбора комнаты
    
    📍 ПУТЬ: [SCREEN 3] → выбор комнаты (room_*) → [SCREEN 4]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.room_choice (в этом состоянии)
    - F.data.startswith("room_") (кнопка с комнатой: room_kitchen, room_bedroom, etc.)
    
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.choose_style_1
    
    [2025-12-30 17:00] 🔥 FIX:
    - Проверяем медиа перед вызовом edit_menu
    - Если медиа - создаем новое меню вместо редактирования
    
    💾 СОХРАНЯЕТ:
    - selected_room (в FSM) → используется при генерации
    - menu_message_id (обновляется)
    - screen_code = 'choose_style_1'
    
    📤 ОТПРАВЛЯЕТ:
    - Новое меню: "🎨 Выберите стиль дизайна"
    - 12 стилей на странице 1
    
    📝 LOG: "[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}"
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
# 📍 ЭКРАН: Выбор стиля (страница 1)
# 📊 FSM STATE: CreationStates.choose_style_1
# 🎯 НАЗНАЧЕНИЕ: Показать 12 стилей (страница 1), возможность перейти на страницу 2
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 3 (выбор комнаты) или SCREEN 5 (вернуться со стр. 2)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 5 (страница 2) или SCREEN 6 (генерация, при выборе стиля)
#
# [2025-12-30 17:00] 🔥 FIX: Проверка медиа перед edit_menu
@router.callback_query(
    StateFilter(CreationStates.choose_style_2),
    F.data == "styles_page_1"
)
async def choose_style_1_menu(callback: CallbackQuery, state: FSMContext):
    """
    [SCREEN 5→4] Вернуться на первую страницу стилей
    
    📍 ПУТЬ: [SCREEN 5: стили стр. 2] → нажать "⬅️ Назад" → [SCREEN 4: стили стр. 1]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.choose_style_2 (находимся на стр. 2)
    - F.data == "styles_page_1" (кнопка "назад на стр. 1")
    
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.choose_style_1
    
    📤 ОТПРАВЛЯЕТ:
    - Меню: "🎨 Выберите стиль дизайна (страница 1)"
    - 12 стилей
    - Кнопки: "🔄 Другой стиль", "🏠 Главное меню", "▶️ Ещё"
    
    📝 LOG: "[V3] NEW_DESIGN+CHOOSE_STYLE - back to page 1, user_id={user_id}"
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
# 📍 ЭКРАН: Выбор стиля (страница 2)
# 📊 FSM STATE: CreationStates.choose_style_2
# 🎯 НАЗНАЧЕНИЕ: Показать еще 12 стилей (страница 2)
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 4 (стили стр. 1, нажал "▶️ Ещё")
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 4 (назад) или SCREEN 6 (генерация, при выборе стиля)
#
# [2025-12-30 17:00] 🔥 FIX: Проверка медиа перед edit_menu
@router.callback_query(
    StateFilter(CreationStates.choose_style_1),
    F.data == "styles_page_2"
)
async def choose_style_2_menu(callback: CallbackQuery, state: FSMContext):
    """
    [SCREEN 4→5] Показать вторую страницу стилей
    
    📍 ПУТЬ: [SCREEN 4: стили стр. 1] → нажать "▶️ Ещё" → [SCREEN 5: стили стр. 2]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.choose_style_1 (находимся на стр. 1)
    - F.data == "styles_page_2" (кнопка "далее на стр. 2")
    
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.choose_style_2
    
    📤 ОТПРАВЛЯЕТ:
    - Меню: "🎨 Выберите стиль дизайна (страница 2)"
    - 12 стилей (дополнительные)
    - Кнопки: "⬅️ Назад", "🏠 Главное меню"
    
    📝 LOG: "[V3] NEW_DESIGN+CHOOSE_STYLE - page 2 shown, user_id={user_id}"
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


# ===== SCREEN 4-5→6: STYLE_CHOICE_HANDLER (Выбор стиля + ГЕНЕРАЦИЯ) 🔥 =====
# 📍 ЭКРАН: Генерация дизайна
# 📊 FSM STATE: CreationStates.choose_style_1 или choose_style_2 → CreationStates.post_generation
# 🎯 НАЗНАЧЕНИЕ: ⭐️ ГЛАВНАЯ ФУНКЦИЯ ⭐️ Генерирует дизайн AI и отправляет результат
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 4 или SCREEN 5 (выбор стиля)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 6 (меню после генерации)
#
# 🔥 ГЕНЕРАЦИЯ ПРОИСХОДИТ ЗДЕСЬ! Используется smart_generate_interior() из services/api_fallback.py
#
# [2026-01-01 17:02] 🔥 CRITICAL FIX: Динамическое сообщение с названиями стиля и комнаты
# [2026-01-01 16:47] 🔥 CRITICAL FIX: Используется HTML вместо Markdown для caption
# [2026-01-01 17:17] 🔥 MAJOR REWRITE: Сохраняются photo_message_id и menu_message_id ОТДЕЛЬНО
@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    🔥 [SCREEN 4-5→6] ГЛАВНЫЙ ОБРАБОТЧИК: Генерация дизайна
    
    📍 ПУТЬ: [SCREEN 4 или 5] → выбор стиля (style_*) → 🔥 ГЕНЕРАЦИЯ → [SCREEN 6]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.choose_style_1 или choose_style_2 (в меню стилей)
    - F.data.startswith("style_") (кнопка со стилем: style_modern, style_minimalist, etc.)
    
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.post_generation
    
    🔥 ПРОЦЕСС ГЕНЕРАЦИИ:
    1️⃣ Проверка баланса юзера (минус 1 генерация)
    2️⃣ УДАЛЯЕМ текстовое меню со стилями (чистим интерфейс)
    3️⃣ Отправляем прогресс: "⚡ Генерирую modern дизайн..."
    4️⃣ 🤖 ГЕНЕРИРУЕМ ДИЗАЙН: smart_generate_interior(photo_id, room, style, ...)
    5️⃣ Отправляем ФОТО дизайна (сообщение 1) с динамическим caption
       Caption: "✨ Ваш новый дизайн в стиле LOFT готов! 🎨 Кухня преобразилась!"
    6️⃣ Отправляем МЕНЮ с кнопками (сообщение 2) 
       Кнопки: "🔄 Другой стиль", "📸 Новое фото", "🏠 Главное меню"
    7️⃣ Удаляем прогресс-сообщение
    
    💾 СОХРАНЯЕТ В БД:
    - photo_message_id (ID фото с дизайном) ← для редактирования
    - menu_message_id (ID меню с кнопками) ← для редактирования
    - Логирует в таблицу generations (для аналитики)
    
    ⚠️ FALLBACK МЕХАНИЗМ:
    - Если прямая отправка по URL не работает → использует BufferedInputFile
    - При ошибке возвращает баланс и показывает сообщение об ошибке
    
    🔥 ДИНАМИЧЕСКОЕ СООБЩЕНИЕ:
    room_display = ROOM_TYPES.get(room) → "Кухня"
    style_display = STYLE_TYPES.get(style) → "Современный"
    caption = f"✨ Ваш новый дизайн в стиле {style_display} готов!\\n🎨 {room_display} преобразилась!"
    
    📝 LOG: "[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}"
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

    # 🤖 ГЕНЕРИРУЕМ ДИЗАЙН
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
        # 🔥 [2026-01-01 17:02] ДИНАМИЧЕСКОЕ СООБЩЕНИЕ!
        # Получаем баланс и режим для вывода
        balance = await db.get_balance(user_id)
        
        # Получаем красивые названия из словарей
        room_display = ROOM_TYPES.get(room, room.replace('_', ' ').title())
        style_display = STYLE_TYPES.get(style, style.replace('_', ' ').title())
        
        # 🔥 [2026-01-01 17:02] ДИНАМИЧЕСКОЕ СООБЩЕНИЕ:
        # Вместо: "Ваш новый дизайн готов!"
        # Пишем:  "Ваш новый дизайн в стиле LOFT готов!"
        design_caption = f"""✨ <b>Ваш новый дизайн в стиле {style_display} готов!</b>

🎨 {room_display} преобразилась!"""
        
        # Отдельное сообщение с кнопками
        menu_caption = f"""🎨 <b>Что дальше?</b>

Выберите действие:
🔄 Другой стиль - примеря другой стиль на эту комнату
🏠 Главное меню - вернуться в главное меню

📊 Баланс: <b>{balance}</b> генераций | 🔧 Режим: <b>{work_mode}</b>"""
        
        photo_sent = False

        # 🔥 [2025-12-31 16:00] ПОПЫТКА 1: Отправляем фото с результатом
        try:
            logger.warning(f"📊 [DIAG] request_id={request_id} ATTEMPT_1: answer_photo (new design)")
            
            # 1️⃣ ОТПРАВЛЯЕМ ДИЗАЙН
            photo_msg = await callback.message.answer_photo(
                photo=result_image_url,
                caption=design_caption,
                parse_mode="HTML",  # 🔥 HTML вместо Markdown!
            )
            
            photo_sent = True
            logger.warning(f"📊 [DIAG] request_id={request_id} SUCCESS_ATTEMPT_1: answer_photo, msg_id={photo_msg.message_id}")
            log_photo_send(user_id, "answer_photo", photo_msg.message_id, request_id, "style_choice")
            
            # 🔥 [2025-12-31 10:19] CRITICAL: Сохраняем в БД СРАЗУ после успешной отправки
            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
            logger.warning(f"📊 [DIAG] request_id={request_id} SAVED_TO_DB after ATTEMPT_1")
            
            # 2️⃣ ОТПРАВЛЯЕМ ОТДЕЛЬНОЕ МЕНЮ С КНОПКАМИ
            try:
                menu_msg = await callback.message.answer(
                    text=menu_caption,
                    parse_mode="HTML",
                    reply_markup=get_post_generation_keyboard()
                )
                logger.warning(f"📊 [DIAG] request_id={request_id} MENU_SENT: msg_id={menu_msg.message_id}")
                
                # Сохраняем menu message_id (используется при change_style)
                await state.update_data(photo_message_id=photo_msg.message_id, menu_message_id=menu_msg.message_id)
                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                
            except Exception as menu_error:
                logger.warning(f"⚠️ [DIAG] Failed to send menu: {menu_error}")
                # Даже если меню не отправилось, дизайн уже есть
            
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
                                caption=design_caption,
                                parse_mode="HTML",  # 🔥 HTML вместо Markdown!
                            )
                            
                            logger.warning(f"📊 [DIAG] request_id={request_id} ATTEMPT_2_PHOTO_SENT: msg_id={photo_msg.message_id}")
                            log_photo_send(user_id, "answer_photo_buffered", photo_msg.message_id, request_id, "style_choice")
                            
                            photo_sent = True
                            logger.warning(f"📊 [DIAG] request_id={request_id} SUCCESS_ATTEMPT_2: answer_photo_buffered")
                            
                            # 🔥 [2025-12-31 10:19] CRITICAL: Сохраняем в БД СРАЗУ после успешной отправки
                            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
                            logger.warning(f"📊 [DIAG] request_id={request_id} SAVED_TO_DB after ATTEMPT_2")
                            
                            # 2️⃣ ОТПРАВЛЯЕМ ОТДЕЛЬНОЕ МЕНЮ С КНОПКАМИ
                            try:
                                menu_msg = await callback.message.answer(
                                    text=menu_caption,
                                    parse_mode="HTML",
                                    reply_markup=get_post_generation_keyboard()
                                )
                                logger.warning(f"📊 [DIAG] request_id={request_id} MENU_SENT: msg_id={menu_msg.message_id}")
                                
                                await state.update_data(photo_message_id=photo_msg.message_id, menu_message_id=menu_msg.message_id)
                                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                                
                            except Exception as menu_error:
                                logger.warning(f"⚠️ [DIAG] Failed to send menu: {menu_error}")
                            
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


# ===== SCREEN 6: POST_GENERATION_MENU =====
# 📍 ЭКРАН: Меню после генерации дизайна
# 📊 FSM STATE: CreationStates.post_generation
# 🎯 НАЗНАЧЕНИЕ: Показать меню с вариантами дальнейших действий
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 6 (генерация дизайна)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 4 (смена стиля) или SCREEN 0 (главное меню)
#
# [2025-12-30 17:00] 🔥 FIX: Проверка медиа перед edit_menu
# [2025-12-31 10:19] 🔥 CRITICAL HOTFIX: Добавить save_chat_menu() сразу после edit_message_caption
@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "post_generation"
)
async def post_generation_menu(callback: CallbackQuery, state: FSMContext):
    """
    [SCREEN 6] Меню после генерации (POST_GENERATION)
    
    📍 ПУТЬ: [SCREEN 6: дизайн готов] → пользователь видит меню с выборами
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.post_generation (после генерации)
    - F.data == "post_generation" (внутреннее событие обновления меню)
    
    📊 СОСТОЯНИЕ: Остаемся в CreationStates.post_generation
    
    📤 ОТПРАВЛЯЕТ:
    - Меню над фото: "🎨 Что дальше?"
    - Кнопки: "🔄 Другой стиль", "📸 Новое фото", "🏠 Главное меню"
    
    💾 СОХРАНЯЕТ В БД:
    - menu_message_id (для отслеживания)
    - screen_code = 'post_generation'
    
    [2025-12-31 10:19] 🔥 CRITICAL HOTFIX:
    - Добавить save_chat_menu() СРАЗУ после edit_message_caption()
    - Без этого при краше бота menu_message_id не обновится
    
    📝 LOG: "[V3] NEW_DESIGN+POST_GENERATION - menu shown, user_id={user_id}"
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
        text = f"""🎨 <b>Что дальше?</b>

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


# ===== SCREEN 6: CHANGE_STYLE (Смена стиля после генерации) =====
# 📍 ЭКРАН: Смена стиля (редактирование меню)
# 📊 FSM STATE: CreationStates.post_generation → CreationStates.choose_style_1
# 🎯 НАЗНАЧЕНИЕ: Вернуться на экран выбора стилей (без повторной генерации)
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 6 (меню после генерации)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 4 (стили, страница 1)
#
# [2026-01-01 17:35] 🔥 MAJOR REWRITE: РЕДАКТИРУЕМ ТОЛЬКО МЕНЮ, БЕЗ ГЕНЕРАЦИИ!
# [2025-12-31 16:00] 🔥 CRITICAL REWRITE: НЕ редактируем фото, создаем НОВОЕ меню!
@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    """
    [SCREEN 6→4] Смена стиля после генерации
    
    📍 ПУТЬ: [SCREEN 6: меню] → нажать "🔄 Другой стиль" → [SCREEN 4: стили]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.post_generation (находимся после генерации)
    - F.data == "change_style" (кнопка "смена стиля")
    
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.choose_style_1
    
    [2026-01-01 17:35] 🔥 MAJOR REWRITE:
    РЕДАКТИРУЕМ ТОЛЬКО МЕНЮ, БЕЗ ГЕНЕРАЦИИ!
    
    Логика:
    1️⃣ Юзер видит фото + меню с кнопками
    2️⃣ Нажимает "🔄 Другой стиль"
    3️⃣ РЕДАКТИРУЕМ МЕНЮ (меняем содержимое на стили)
    4️⃣ Больше НИЧЕГО не генерируем!
    5️⃣ Фото остается БЕЗ ИЗМЕНЕНИЙ
    
    Затем при выборе стиля из этого меню - вызовется style_choice_handler
    и там произойдет генерация нового дизайна
    
    📤 ОТПРАВЛЯЕТ:
    - Меню: "🎨 Выберите стиль дизайна"
    - 12 стилей (первая страница)
    - Кнопки: "⬅️ К комнате", "🏠 Главное меню", "▶️ Ещё"
    
    💾 СОХРАНЯЕТ В БД:
    - screen_code = 'choose_style_1'
    
    ❌ НЕ ГЕНЕРИРУЕТ ДИЗАЙН! Генерация произойдет при выборе стиля.
    
    📝 LOG: "[V3] NEW_DESIGN+CHANGE_STYLE - back to style selection, user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id  # 🔥 ID МЕНЮ с кнопками!

    logger.warning(f"🔍 [CHANGE_STYLE] START: user_id={user_id}, menu_msg_id={menu_message_id}")

    data = await state.get_data()
    work_mode = data.get('work_mode')
    balance = await db.get_balance(user_id)

    try:
        # ✅ РЕДАКТИРУЕМ ТЕКУЩЕЕ МЕНЮ НА ВЫБОР СТИЛЕЙ
        await state.set_state(CreationStates.choose_style_1)
        
        text = f"🎨 **Выберите стиль дизайна**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        # 🔥 [2026-01-01 17:35] РЕДАКТИРУЕМ МЕНЮ
        await callback.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=get_choose_style_1_keyboard(),
            parse_mode="Markdown"
        )
        
        # ✅ Сохраняем в БД
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'choose_style_1')
        
        logger.info(f"✅ [CHANGE_STYLE] Menu edited: msg_id={menu_message_id}, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] CHANGE_STYLE failed: {e}", exc_info=True)
        await callback.answer(
            "❌ Ошибка при смене стиля. Попробуйте еще раз.",
            show_alert=True
        )
