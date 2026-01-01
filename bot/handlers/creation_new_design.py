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
#    • SCREEN 6→2: uploading_photo_from_generation() - 🆕 Новое фото [NEW]
#
# 🔧 АРХИТЕКТУРА FSM (Finite State Machine):
#    CreationStates.room_choice → choose_style_1 → choose_style_2 → post_generation
#
# 🔥 ГЛАВНЫЙ ОБРАБОТЧИК:
#    style_choice_handler() - Генерирует дизайн через smart_generate_interior()
#
# 📊 ВЕРСИЯ: 3.1
# 📅 ДАТА: 2026-01-02
# 🔧 HOTFIX: [2026-01-02 12:00] Добавлены обработчики для change_style и to_main_menu из post_generation
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
    UPLOAD_PHOTO_TEXT,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()

# ═══════════════════════════════════════════════════════════════════════════════
# 🔍 ДИАГНОСТИКА: Глобальный трекер отправок фото (для дебага)
# ═══════════════════════════════════════════════════════════════════════════════
# [2025-12-30 01:47] 📊 DIAGNOSTICS
# Логирует каждую попытку отправки фото (answer_photo, send_photo, edit_message_media)
# Помогает диагностировать проблемы с двойными отправками фото

PHOTO_SEND_LOG = {}  # Глобальный трекер: user_id -> [(timestamp, method, message_id, request_id)]

def log_photo_send(user_id: int, method: str, message_id: int, request_id: str = None, operation: str = ""):
    """
    🔍 ДИАГНОСТИКА: Логирует каждую отправку фото
    
    📝 ПАРАМЕТРЫ:
    - user_id: ID пользователя
    - method: Метод отправки (answer_photo, send_photo, edit_message_media, edit_message_caption)
    - message_id: ID сообщения с фото
    - request_id: ID запроса для трекинга (auto-generated если не указан)
    - operation: Наименование операции (style_choice, post_generation, etc)
    
    📊 НАЗНАЧЕНИЕ:
    Помогает отследить и диагностировать проблемы с:
    - Двойными отправками фото
    - Потерей message_id при отправке
    - Ошибками при редактировании медиа
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
    
    # Оверфлоу диагностики (если более 1 отправки подряд)
    if len(PHOTO_SEND_LOG[user_id]) > 1:
        logger.error(
            f"🔥 [PHOTO_DOUBLE_SEND] user_id={user_id}, "
            f"count={len(PHOTO_SEND_LOG[user_id])}, "
            f"all={PHOTO_SEND_LOG[user_id]}"
        )


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🆕 [2026-01-01 20:30] HANDLER: UPLOADING_PHOTO FROM POST-GENERATION
# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 📍 ЭКРАН: 6→2 (навигация для нового фото)
# 📊 FSM STATE: CreationStates.post_generation → CreationStates.uploading_photo
# 🎯 НАЗНАЧЕНИЕ: При клике на кнопку "📸 Новое фото" - вернуться к загрузке фото
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 6 (меню после генерации)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 2 (загрузка нового фото)
# 🔌 ТРИГГЕР: F.data == "uploading_photo"
#
# 📋 ЛОГИКА:
# 1️⃣ Пользователь видит готовый дизайн + меню
# 2️⃣ Нажимает кнопку "📸 Новое фото"
# 3️⃣ ОЧИЩАЕМ ВСЕ ДАННЫЕ О ТЕКУЩЕМ ДИЗАЙНЕ
# 4️⃣ Переходим в состояние uploading_photo
# 5️⃣ Показываем текст "Загрузите новое фото"
# 6️⃣ Пользователь загружает НОВОЕ фото
# 7️⃣ Начинается НОВЫЙ ЦИКЛ (выбор комнаты, стиля, генерация)
#
# 📝 ЛОГИРОВАНИЕ:
# - "[V3] NEW_DESIGN+UPLOAD_NEW_PHOTO - reset to uploading_photo, user_id={user_id}"

@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "uploading_photo"
)
async def uploading_photo_from_generation(callback: CallbackQuery, state: FSMContext):
    """
    🆕 [2026-01-01 20:30] uploading_photo_from_generation() - Новое фото после дизайна
    
    📍 ПУТЬ: [SCREEN 6: дизайн готов] → нажать "📸 Новое фото" → [SCREEN 2: загрузка]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.post_generation (находимся после генерации)
    - F.data == "uploading_photo" (кнопка "новое фото")
    
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.uploading_photo
    
    📋 АЛГОРИТМ:
    1️⃣ ОЧИЩАЕМ ВСЕ данные о ТЕКУЩЕМ дизайне (photo_id, selected_room, etc.)
    2️⃣ Переходим в состояние uploading_photo
    3️⃣ Отправляем текст: "Загрузите новое фото"
    4️⃣ Показываем ПУСТУЮ клавиатуру (БЕЗ кнопок)
    5️⃣ Пользователь загружает НОВОЕ фото
    6️⃣ Триггер photo_handler из creation_main.py обрабатывает его
    
    💾 ОЧИЩАЕТ ИЗ FSM:
    - photo_id (текущее фото)
    - selected_room (выбранная комната)
    - menu_message_id (ID старого меню)
    - photo_message_id (ID старого дизайна)
    - Остальные данные FSM тоже очищаются
    
    ⚠️ ОТЛИЧИЕ ОТ ПЕРВОНАЧАЛЬНОЙ ЗАГРУЗКИ:
    - При запуске бота (SCREEN 0→1→2) - пользователь попадает на uploading_photo из select_mode
    - Здесь (SCREEN 6→2) - пользователь попадает на uploading_photo из post_generation
    - Технически - один и тот же экран, но разный путь туда
    
    📤 ОТПРАВЛЯЕТ:
    - Текст: "📷 Загрузите новое фото помещения"
    - Клавиатура: get_uploading_photo_keyboard() → ПУСТАЯ (без кнопок)
    - Без баланса и режима работы
    
    📝 ЛОГИРОВАНИЕ:
    - "[V3] NEW_DESIGN+UPLOAD_NEW_PHOTO - reset to uploading_photo, user_id={user_id}"
    - "🆕 [UPLOADING_PHOTO] New photo for user={user_id}, cleared FSM state"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id

    try:
        logger.warning(f"🆕 [UPLOADING_PHOTO] START: user_id={user_id}, from post_generation")
        
        # ✅ ОЧИЩАЕМ ВСЕ ДАННЫЕ О ТЕКУЩЕМ ДИЗАЙНЕ (но сохраняем work_mode)
        data = await state.get_data()
        work_mode = data.get('work_mode')  # ← СОХРАНЯЕМ режим работы
        
        # Очищаем FSM
        await state.clear()
        
        # Восстанавливаем только work_mode (если был сохранён)
        if work_mode:
            await state.update_data(work_mode=work_mode)
        
        # Переходим в состояние загрузки фото
        await state.set_state(CreationStates.uploading_photo)
        
        # Формируем текст меню для загрузки
        text = UPLOAD_PHOTO_TEXT or "📷 Загрузите новое фото помещения"
        
        # ✅ Редактируем текущее меню или создаем новое
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_uploading_photo_keyboard(),
            show_balance=False,
            screen_code='uploading_photo'
        )
        
        logger.warning(f"🆕 [UPLOADING_PHOTO] READY: user_id={user_id}, waiting for new photo")
        logger.info(f"[V3] NEW_DESIGN+UPLOAD_NEW_PHOTO - reset to uploading_photo, user_id={user_id}")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] UPLOADING_PHOTO_FROM_GENERATION failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🆕 [2026-01-02 12:00] HANDLER: TO_MAIN_MENU FROM POST-GENERATION
# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 📍 ЭКРАН: 6→0 (вернуться в главное меню из экрана дизайна)
# 📊 FSM STATE: CreationStates.post_generation → clear/WorkMode.select_mode
# 🎯 НАЗНАЧЕНИЕ: При клике на кнопку "🏠 Главное меню" - вернуться в главное меню
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 6 (меню после генерации)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 0 (главное меню)
# 🔌 ТРИГГЕР: StateFilter(CreationStates.post_generation) + F.data == "to_main_menu"
#
# 📋 ЛОГИКА:
# 1️⃣ Пользователь видит готовый дизайн + меню
# 2️⃣ Нажимает кнопку "🏠 Главное меню"
# 3️⃣ Очищаем FSM (завершаем режим new_design)
# 4️⃣ Показываем главное меню с 3 кнопками (Новый дизайн, Галерея, Настройки)
#
# 📝 ЛОГИРОВАНИЕ:
# - "[V3] NEW_DESIGN+TO_MAIN_MENU - reset, user_id={user_id}"

@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "to_main_menu"
)
async def to_main_menu_from_post_generation(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    🆕 [2026-01-02 12:00] to_main_menu_from_post_generation() - В главное меню из дизайна
    
    📍 ПУТЬ: [SCREEN 6: дизайн готов] → нажать "🏠 Главное меню" → [SCREEN 0: меню]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.post_generation (находимся после генерации)
    - F.data == "to_main_menu" (кнопка "главное меню")
    
    📊 НОВОЕ СОСТОЯНИЕ: clear (FSM очищается)
    
    📋 АЛГОРИТМ:
    1️⃣ ОЧИЩАЕМ ВСЕ данные о текущем дизайне (photo_id, room, style, etc.)
    2️⃣ Завершаем режим new_design
    3️⃣ Показываем главное меню (show_main_menu)
    
    📤 ОТПРАВЛЯЕТ:
    - Главное меню с кнопками:
      ├─ "✨ Создать новый дизайн"
      ├─ "🖼️ Моя галерея"
      └─ "⚙️ Настройки"
    
    📝 ЛОГИРОВАНИЕ:
    - "[V3] NEW_DESIGN+TO_MAIN_MENU - reset, user_id={user_id}"
    """
    user_id = callback.from_user.id
    
    try:
        logger.warning(f"🏠 [TO_MAIN_MENU] START: user_id={user_id}, from post_generation")
        
        # ✅ Очищаем FSM (завершаем режим new_design)
        await state.clear()
        
        # Показываем главное меню
        await show_main_menu(callback, state, admins)
        
        logger.info(f"[V3] NEW_DESIGN+TO_MAIN_MENU - reset, user_id={user_id}")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] TO_MAIN_MENU_FROM_POST_GENERATION failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🔄 [SCREEN 6→4] СМЕНА СТИЛЯ ПОСЛЕ ГЕНЕРАЦИИ (CHANGE STYLE) - FIXED VERSION
# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 📍 ЭКРАН: 6→4 (навигация назад БЕЗ переколки фото)
# 📊 FSM STATE: CreationStates.post_generation → CreationStates.choose_style_1
# 🎯 НАЗНАЧЕНИЕ: Вернуться на экран выбора стилей БЕЗ повторной загрузки фото
# ⬅️ ПРЕДЫДУЩИЙ ЭКРАН: SCREEN 6 (меню после генерации)
# ➡️ СЛЕДУЮЩИЙ ЭКРАН: SCREEN 4 (стили, страница 1)
# 🔌 ТРИГГЕР: StateFilter(CreationStates.post_generation) + F.data == "change_style"
#
# 📋 ЛОГИКА:
# 1️⃣ Пользователь видит готовый дизайн + меню
# 2️⃣ Нажимает кнопку "🔄 Другой стиль"
# 3️⃣ РЕДАКТИРУЕМ ТОЛЬКО МЕНЮ (на стили)
# 4️⃣ Показываем снова меню со стилями
# 5️⃣ При выборе стиля → вызовется style_choice_handler и произойдет генерация
#
# [2026-01-02 12:00] 🔥 CRITICAL FIX: Добавлен StateFilter для post_generation!
# [2026-01-01 17:35] 🔥 MAJOR REWRITE: РЕДАКТИРУЕМ ТОЛЬКО МЕНЮ, БЕЗ ГЕНЕРАЦИИ!
#
# 📝 ЛОГИРОВАНИЕ:
# - "[V3] NEW_DESIGN+CHANGE_STYLE - back to style selection, user_id={user_id}"

@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "change_style"
)
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    """
    🔄 [SCREEN 6→4] change_style_after_gen() - Смена стиля после генерации
    
    📍 ПУТЬ: [SCREEN 6: дизайн готов] → нажать "🔄 Другой стиль" → [SCREEN 4: выбор стилей]
    
    🔌 ТРИГГЕР: 
    - StateFilter: CreationStates.post_generation (находимся после генерации)
    - F.data == "change_style" (кнопка "смена стиля")
    
    📊 НОВОЕ СОСТОЯНИЕ: CreationStates.choose_style_1
    
    [2026-01-02 12:00] 🔥 CRITICAL FIX:
    - ДОБАВЛЕН StateFilter(CreationStates.post_generation)!
    - БЕЗ этого фильтра callback мог бы поймать неправильный handler
    - Теперь обработчик срабатывает ТОЛЬКО из состояния post_generation
    
    [2026-01-01 17:35] 🔥 MAJOR REWRITE - РЕДАКТИРУЕМ ТОЛЬКО МЕНЮ!
    
    📋 ЛОГИКА (ВАЖНО!):
    1️⃣ Юзер видит ФОТО дизайна + МЕНЮ с кнопками
    2️⃣ Нажимает "🔄 Другой стиль"
    3️⃣ РЕДАКТИРУЕМ ТОЛЬКО МЕНЮ (меняем содержимое на стили)
    4️⃣ ФОТО ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ!
    5️⃣ Больше НИЧЕГО не генерируем!
    
    Затем при выборе стиля из этого меню:
    → вызовется style_choice_handler()
    → произойдет генерация НОВОГО дизайна
    → придет НОВОЕ фото с новым стилем
    
    ✨ ЭФФЕКТ ДЛЯ ЮЗЕРА:
    "Я вижу свой дизайн, нажимаю 'другой стиль', и вижу новое меню
     с выбором стилей. Без лишних движений - сразу выбираю новый стиль
     и генерируется новый дизайн."
    
    📤 ОТПРАВЛЯЕТ:
    - Редактированное МЕНЮ: "🎨 Выберите стиль дизайна"
    - 12 стилей (первая страница)
    - Кнопки: "⬅️ Вернуться на первую", "🏠 Главное меню", "▶️ Ещё"
    
    💾 СОХРАНЯЕТ В БД:
    - screen_code = 'choose_style_1'
    
    ❌ НЕ ГЕНЕРИРУЕТ ДИЗАЙН!
    ❌ НЕ УДАЛЯЕТ ФОТО!
    ✅ РЕДАКТИРУЕТ ТОЛЬКО МЕНЮ!
    
    📝 ЛОГИРОВАНИЕ:
    - "[V3] NEW_DESIGN+CHANGE_STYLE - back to style selection, user_id={user_id}"
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
        # Переходим в состояние выбора стиля
        await state.set_state(CreationStates.choose_style_1)
        
        # Формируем текст меню со стилями
        text = f"🎨 **Выберите стиль дизайна**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        # 🔥 [2026-01-01 17:35] РЕДАКТИРУЕМ ТОЛЬКО МЕНЮ - БЕЗ ФОТО!
        await callback.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=get_choose_style_1_keyboard(),
            parse_mode="Markdown"
        )
        
        # ✅ Сохраняем в БД (обновляем screen_code)
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'choose_style_1')
        
        logger.info(f"✅ [CHANGE_STYLE] Menu edited: msg_id={menu_message_id}, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] CHANGE_STYLE failed: {e}", exc_info=True)
        await callback.answer(
            "❌ Ошибка при смене стиля. Попробуйте еще раз.",
            show_alert=True
        )


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 3] ВЫБОР ТИПА ПОМЕЩЕНИЯ (ROOM CHOICE)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """
    🏠 [SCREEN 3] room_choice_menu() - Меню выбора типа помещения
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        # Устанавливаем состояние: "пользователь выбирает комнату"
        await state.set_state(CreationStates.room_choice)
        
        # Формируем текст меню
        text = f"🏠 **Выберите тип помещения**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        # ✅ [2025-12-30 17:00] ПРАВИЛЬНАЯ ЛОГИКА:
        # Проверяем, есть ли в сообщении ФОТО
        current_msg = callback.message
        
        if current_msg.photo:
            # Текущее сообщение содержит ФОТО → создаем НОВОЕ текстовое меню
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
            
            # Сохраняем НОВЫЙ message_id в FSM
            await state.update_data(menu_message_id=new_msg.message_id)
            
            # Сохраняем в БД для отслеживания
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'room_choice')
            
            logger.info(f"✅ [ROOM_CHOICE] New text menu created, msg_id={new_msg.message_id}")
        else:
            # Текущее сообщение - ТЕКСТ → редактируем обычно
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


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 3→4] ОБРАБОТЧИК ВЫБОРА КОМНАТЫ (ROOM CHOICE HANDLER)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.room_choice),
    F.data.startswith("room_")
)
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    🏠 [SCREEN 3→4] room_choice_handler() - Обработчик выбора комнаты
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        # Извлекаем выбранную комнату из callback_data
        # Пример: "room_kitchen" → room = "kitchen"
        room = callback.data.replace("room_", "")
        
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        # Сохраняем выбор комнаты в FSM (будет использован при генерации)
        await state.update_data(selected_room=room)
        
        # Переходим в состояние выбора стиля
        await state.set_state(CreationStates.choose_style_1)
        
        # Формируем текст меню со стилями
        text = f"🎨 **Выберите стиль дизайна**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode)
        
        # ✅ [2025-12-30 17:00] Проверяем медиа ДО редактирования
        current_msg = callback.message
        
        if current_msg.photo:
            # Текущее сообщение содержит ФОТО → создаем НОВОЕ текстовое меню
            logger.warning(
                f"⚠️ [ROOM_CHOICE_HANDLER] Current msg has PHOTO (id={current_msg.message_id}), "
                f"creating NEW text menu"
            )
            
            # Создаем НОВОЕ текстовое меню со СТИЛЯМИ
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=get_choose_style_1_keyboard(),
                parse_mode="Markdown"
            )
            
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'choose_style_1')
            
            logger.info(f"✅ [ROOM_CHOICE_HANDLER] New text menu created, msg_id={new_msg.message_id}")
        else:
            # Текущее сообщение - ТЕКСТ → редактируем обычно
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


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🎨 [SCREEN 4] ВЫБОР СТИЛЯ СТРАНИЦА 1 (CHOOSE STYLE PAGE 1)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.choose_style_2),
    F.data == "styles_page_1"
)
async def choose_style_1_menu(callback: CallbackQuery, state: FSMContext):
    """
    🎨 [SCREEN 5→4] choose_style_1_menu() - Вернуться на первую страницу стилей
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        # Переходим в состояние выбора стиля (страница 1)
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


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🎨 [SCREEN 5] ВЫБОР СТИЛЯ СТРАНИЦА 2 (CHOOSE STYLE PAGE 2)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.choose_style_1),
    F.data == "styles_page_2"
)
async def choose_style_2_menu(callback: CallbackQuery, state: FSMContext):
    """
    🎨 [SCREEN 4→5] choose_style_2_menu() - Показать вторую страницу стилей
    """
    user_id = callback.from_user.id
    
    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        balance = await db.get_balance(user_id)
        
        # Переходим в состояние выбора стиля (страница 2)
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


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🔥 [SCREEN 4-5→6] ГЛАВНЫЙ ОБРАБОТЧИК: ГЕНЕРАЦИЯ ДИЗАЙНА (STYLE CHOICE + GENERATION)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    🔥 [SCREEN 4-5→6] style_choice_handler() - ГЛАВНЫЙ ГЕНЕРАТОР ДИЗАЙНА
    """
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id
    request_id = str(uuid.uuid4())[:8]  # ✅ DIAGNOSTICS: для трекинга

    logger.warning(f"🔍 [DIAG_START] request_id={request_id}, user_id={user_id}, style={style}")

    await db.log_activity(user_id, f'style_{style}')

    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    # 1️⃣ ИЗВЛЕЧЕНИЕ И ПРОВЕРКА ДАННЫХ
    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')
    work_mode = data.get('work_mode')  # ✅ Получаем work_mode для отображения

    if not photo_id or not room:
        await callback.answer(
            "⚠️ Сессия устарела. Загрузите фото заново.",
            show_alert=True
        )
        await state.clear()
        await show_main_menu(callback, state, admins)
        return

    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    # 2️⃣ ПРОВЕРКА БАЛАНСА
    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    
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

    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    # 3️⃣ МИНУСОВАНИЕ БАЛАНСА
    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    
    if not is_admin:
        await db.decrease_balance(user_id)

    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    # 4️⃣ [НОВЫЙ ПОДХОД] РЕДАКТИРОВАНИЕ ИЛИ УДАЛЕНИЕ ТЕКУЩЕГО МЕНЮ
    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    # [2026-01-01 17:35] 🔥 HOTFIX: РЕДАКТИРУЕМ ТЕКСТ, УДАЛЯЕМ ФОТО
    
    progress_msg = None
    current_msg = callback.message
    balance_text = await add_balance_and_mode_to_text(
        f"⚡ Генерирую {style} дизайн...",
        user_id,
        work_mode
    )
    
    try:
        if current_msg.photo:
            # Текущее сообщение содержит ФОТО → удаляем его и создаем НОВОЕ для прогресса
            await callback.message.delete()
            logger.warning(f"📊 [DIAG] request_id={request_id} STEP_1: Deleted media msg_id={menu_message_id}")
            
            progress_msg = await callback.message.answer(
                text=balance_text,
                parse_mode="Markdown"
            )
            logger.warning(f"📊 [DIAG] request_id={request_id} STEP_2: Progress msg sent, msg_id={progress_msg.message_id}")
            
        else:
            # Текущее сообщение - ТЕКСТ → редактируем его в ПРОГРЕСС (экономим место)
            progress_msg = await callback.message.edit_text(
                text=balance_text,
                parse_mode="Markdown"
            )
            logger.warning(f"📊 [DIAG] request_id={request_id} STEP_1: Edited text menu to progress, msg_id={progress_msg.message_id}")
        
    except Exception as e:
        logger.warning(f"⚠️ [DIAG] request_id={request_id} Failed to edit/delete menu: {e}")
        # Если что-то пошло не так, продолжаем без прогресса-сообщения
        progress_msg = None
    
    await callback.answer()

    # Получаем PRO режим для улучшенной генерации
    pro_settings = await db.get_user_pro_settings(user_id)
    use_pro = pro_settings.get('pro_mode', False)
    logger.info(f"🔧 PRO MODE для user_id={user_id}: {use_pro}")

    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    # 5️⃣ 🤖 ГЕНЕРАЦИЯ ДИЗАЙНА [ГЛАВНАЯ ОПЕРАЦИЯ]
    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    
    try:
        result_image_url = await smart_generate_interior(
            photo_id, room, style, bot_token, use_pro=use_pro
        )
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"[ERROR] Критическая ошибка генерации: {e}")
        result_image_url = None
        success = False

    # Логируем результат генерации
    await db.log_generation(
        user_id=user_id,
        room_type=room,
        style_type=style,
        operation_type='design',
        success=success
    )

    # ═══════════════════════════════════════════════════════════════════════════════════════════════════
    # 6️⃣ ОБРАБОТКА УСПЕШНОЙ ГЕНЕРАЦИИ
    # ═══════════════════════════════════════════════════════════════════════════════════════════════════

    if result_image_url:
        # Получаем текущий баланс для отображения
        balance = await db.get_balance(user_id)
        
        # 🔥 [2026-01-01 17:02] ДИНАМИЧЕСКОЕ СООБЩЕНИЕ!
        # Получаем красивые названия стиля и комнаты из словарей
        room_display = ROOM_TYPES.get(room, room.replace('_', ' ').title())
        style_display = STYLE_TYPES.get(style, style.replace('_', ' ').title())
        
        # 🔥 [2026-01-01 16:47] Используем HTML вместо Markdown для caption
        design_caption = f"""✨ <b>Ваш новый дизайн {room_display} в стиле {style_display} готов!</b>
         """
        
        # Отдельное сообщение с кнопками для управления
        menu_caption = f"""🎨 <b>Что дальше?</b>

Выберите действие:
🔄 Другой стиль - примерьте другой стиль!
🏠 Главное меню - выбрать другой режим!

📊 Баланс: <b>{balance}</b> генераций | 🔧 Режим: <b>{work_mode}</b>"""
        
        photo_sent = False

        # ═════════════════════════════════════════════════════════════════════════════════════════════
        # ПОПЫТКА 1: Отправить фото прямо по URL из AI API
        # ═════════════════════════════════════════════════════════════════════════════════════════════
        
        try:
            logger.warning(f"📊 [DIAG] request_id={request_id} ATTEMPT_1: answer_photo (new design)")
            
            # 6️⃣ ОТПРАВЛЯЕМ ДИЗАЙН (сообщение 1)
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
            
            # ═════════════════════════════════════════════════════════════════════════════════════════
            # 7️⃣ ОТПРАВЛЯЕМ МЕНЮ С КНОПКАМИ (сообщение 2)
            # ═════════════════════════════════════════════════════════════════════════════════════════
            
            try:
                menu_msg = await callback.message.answer(
                    text=menu_caption,
                    parse_mode="HTML",
                    reply_markup=get_post_generation_keyboard()
                )
                logger.warning(f"📊 [DIAG] request_id={request_id} MENU_SENT: msg_id={menu_msg.message_id}")
                
                # Сохраняем оба message_id (используются для редактирования)
                await state.update_data(photo_message_id=photo_msg.message_id, menu_message_id=menu_msg.message_id)
                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                
            except Exception as menu_error:
                logger.warning(f"⚠️ [DIAG] Failed to send menu: {menu_error}")
                # Даже если меню не отправилось, дизайн уже есть
            
            # ═════════════════════════════════════════════════════════════════════════════════════════
            # 8️⃣ ОЧИСТКА ИНТЕРФЕЙСА - Удаляем сообщение с прогрессом
            # ═════════════════════════════════════════════════════════════════════════════════════════
            
            if progress_msg:
                try:
                    await progress_msg.delete()
                    logger.warning(f"📊 [DIAG] request_id={request_id} Deleted progress msg")
                except Exception:
                    pass

        except Exception as url_error:
            logger.warning(f"📊 [DIAG] request_id={request_id} FAILED_ATTEMPT_1: {url_error}")

            # ═════════════════════════════════════════════════════════════════════════════════════════
            # ПОПЫТКА 2: FALLBACK - Загружаем файл локально через BufferedInputFile
            # ═════════════════════════════════════════════════════════════════════════════════════════
            
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
                            
                            # Отправляем меню
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
                            
                            # Удаляем прогресс
                            if progress_msg:
                                try:
                                    await progress_msg.delete()
                                except Exception:
                                    pass
                        else:
                            logger.error(f"📊 [DIAG] request_id={request_id} ATTEMPT_2 HTTP {resp.status}")

            except Exception as buffer_error:
                logger.error(f"📊 [DIAG] request_id={request_id} FAILED_ATTEMPT_2: {buffer_error}")

        # ═════════════════════════════════════════════════════════════════════════════════════════════
        # FALLBACK: Если все попытки не сработали - возвращаем баланс
        # ═════════════════════════════════════════════════════════════════════════════════════════════
        
        if not photo_sent:
            # Возвращаем баланс пользователю
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

        # ═════════════════════════════════════════════════════════════════════════════════════════════
        # 9️⃣ ПЕРЕХОД НА SCREEN 6 - Устанавливаем состояние POST_GENERATION
        # ═════════════════════════════════════════════════════════════════════════════════════════════
        
        await state.set_state(CreationStates.post_generation)

        logger.warning(f"📊 [DIAG] request_id={request_id} SUCCESS_END for user_id={user_id}")
        logger.info(f"[V3] NEW_DESIGN+STYLE - generated for {room}/{style}, user_id={user_id}")
        logger.info(f"[V3] NEW_DESIGN+POST_GENERATION - ready, user_id={user_id}")

    else:
        # ═════════════════════════════════════════════════════════════════════════════════════════════
        # ❌ ОШИБКА ГЕНЕРАЦИИ - Возвращаем баланс и показываем ошибку
        # ═════════════════════════════════════════════════════════════════════════════════════════════
        
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


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
# 🎨 [SCREEN 6] МЕНЮ ПОСЛЕ ГЕНЕРАЦИИ (POST-GENERATION MENU)
# ═════════════════════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.post_generation),
    F.data == "post_generation"
)
async def post_generation_menu(callback: CallbackQuery, state: FSMContext):
    """
    🎨 [SCREEN 6] post_generation_menu() - Меню после генерации дизайна
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
        
        # ✅ Проверяем, является ли текущее сообщение медиа
        current_msg = callback.message
        
        if current_msg.photo:
            # Это медиа-сообщение с фото - редактируем подпись (caption)
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
                # Fallback на текстовое меню (если редактирование caption не прошло)
                await edit_menu(
                    callback=callback,
                    state=state,
                    text="✅ Выбери что дальше",
                    keyboard=get_post_generation_keyboard(),
                    screen_code='post_generation'
                )
        else:
            # Текущее сообщение - ТЕКСТ → редактируем обычно
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
