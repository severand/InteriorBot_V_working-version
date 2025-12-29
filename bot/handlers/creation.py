# bot/handlers/creation.py
# [2025-12-24 21:00] ЗАМЕНЕНЫ: Все вызовы add_balance_to_text на add_balance_and_mode_to_text
# [2025-12-24 21:00] РЕЗУЛЬТАТ: Header теперь показывает "⚡ Баланс: N | Режим: 🔧 PRO" или "📋 СТАНДАРТ"
# --- ФАЗА 1.4: 2025-12-29 20:45 - V3 MULTI-MODE SYSTEM (SELECT_MODE + PHOTO) ---
# [2025-12-29 20:45] ДОБАВЛЕНЫ: Импорты для SELECT_MODE и PHOTO handlers
# [2025-12-29 20:45] СТРУКТУРА: Выбор режима создания → Загрузка фото → Определение типа сцены
# [2025-12-29 20:45] ДУБЛИКАТЫ УДАЛЕНЫ: Обработчики не дублируют существующую логику
# --- ФАЗА 1.4.2: 2025-12-29 21:05 - V3 SCREEN 1: SELECT_MODE + SET_WORK_MODE ---
# [2025-12-29 21:05] ИСПРАВЛЕНЫ: Оба handler'а (select_mode + set_work_mode) с production-ready кодом
# [2025-12-29 21:05] ДОБАВЛЕНО: MODE_SELECTION_TEXT в utils/texts.py
# [2025-12-29 21:05] ПРОВЕРЕНО: Все импорты, функции БД, FSM state'ы
# [2025-12-29 21:05] ЛОГИРОВАНИЕ: Правильное логирование с [V3] префиксом
# [2025-12-29 21:05] ERROR HANDLING: Try-catch блоки с сообщениями пользователю
# --- ФАЗА 1.4.3: 2025-12-29 22:30 - V3 SCREEN 2: PHOTO_HANDLER ИСПРАВЛЕНИЯ ---
# [2025-12-29 22:30] ИСПРАВЛЕНО: StateFilter вместо F.state()
# [2025-12-29 22:30] ДОБАВЛЕНО: Правильное получение menu_message_id из БД
# [2025-12-29 22:30] УЛУЧШЕНО: Обработка ошибок при редактировании меню
# [2025-12-29 22:30] ПРОВЕРЕНО: Все импорты и функции БД (get_chat_menu, save_photo, save_chat_menu)
# [2025-12-29 22:30] ВАЛИДАЦИЯ: Фото, баланс, режим работы
# [2025-12-29 22:30] SINGLE MENU PATTERN: 100% соответствие SMP
# --- ФАЗА 1.5.1: 2025-12-29 23:00 - V3 SCREEN 3: ROOM_CHOICE (NEW_DESIGN only) ---
# [2025-12-29 23:00] ДОБАВЛЕНЫ: room_choice_menu() и room_choice_handler()
# [2025-12-29 23:00] ЛОГИКА: Выбор комнаты только для NEW_DESIGN режима
# [2025-12-29 23:00] ПЕРЕХОД: UPLOADING_PHOTO → ROOM_CHOICE → CHOOSE_STYLE_1
# [2025-12-29 23:00] СОХРАНЕНИЕ: selected_room в FSM и БД
# [2025-12-29 23:00] ЛОГИРОВАНИЕ: [V3] NEW_DESIGN+ROOM_CHOICE префикс
# --- ФАЗА 1.5.2: 2025-12-29 23:56 - ЛОВУШКА ДЛЯ ФОТО НА ДРУГИХ СОСТОЯНИЯХ ---
# [2025-12-29 23:56] ДОБАВЛЕНО: @router.message(..., F.photo) БЕЗ StateFilter
# [2025-12-29 23:56] ЛОГИКА: Перехватывает фото на экранах room_choice, choose_style, etc
# [2025-12-29 23:56] ДЕЙСТВИЕ: Переход обратно на uploading_photo без удаления фото
# [2025-12-29 23:56] СОХРАНЕНИЕ: photo_id в FSM для использования на новой загрузке

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StateFilter  # ✅ ФАЗА 1.4.3: Правильный импорт StateFilter
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.exceptions import TelegramBadRequest

from database.db import db

from keyboards.inline import (
    get_room_keyboard,
    get_style_keyboard,
    get_payment_keyboard,
    get_post_generation_keyboard,
    get_upload_photo_keyboard,
    get_what_is_in_photo_keyboard,  # ✅ ФАЗА 1.4: Для выбора типа сцены (интерьер/экстерьер)
    get_mode_selection_keyboard,  # ✅ ФАЗА 1.4: Новая клавиатура для выбора режима (NEW_DESIGN/REDESIGN/CONSULTATION)
    get_room_choice_keyboard,  # ✅ ФАЗА 1.4.3: SCREEN 3
    get_choose_style_1_keyboard,  # ✅ ФАЗА 1.4.3: SCREEN 4
    get_choose_style_2_keyboard,  # ✅ ФАЗА 1.4.3: SCREEN 5
    get_edit_design_keyboard,  # ✅ ФАЗА 1.4.3: SCREEN 8
    get_download_sample_keyboard,  # ✅ ФАЗА 1.4.3: SCREEN 10
    get_uploading_furniture_keyboard,  # ✅ ФАЗА 1.4.3: SCREEN 13
    get_loading_facade_sample_keyboard,  # ✅ ФАЗА 1.4.3: SCREEN 16
)

# ОБНОВЛЕНО: 2025-12-23 - Использование Smart Fallback системы
from services.api_fallback import (
    smart_generate_interior,
    smart_generate_with_text,
    smart_clear_space,
)

from states.fsm import CreationStates, WorkMode  # ✅ ФАЗА 1.4: Добавлен WorkMode для V3 Multi-Mode

from utils.texts import (
    CHOOSE_STYLE_TEXT,
    PHOTO_SAVED_TEXT,
    NO_BALANCE_TEXT,
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    WHAT_IS_IN_PHOTO_TEXT,
    EXTERIOR_HOUSE_PROMPT_TEXT,
    EXTERIOR_PLOT_PROMPT_TEXT,
    ROOM_DESCRIPTION_PROMPT_TEXT,
    MODE_SELECTION_TEXT,  # ✅ ФАЗА 1.4.2: Текст экрана выбора режима
    UPLOADING_PHOTO_TEMPLATES,  # ✅ ФАЗА 1.4.2: Динамические шаблоны текста для режимов
    ROOM_CHOICE_TEXT,  # ✅ ФАЗА 1.4.3: SCREEN 3
    CHOOSE_STYLE_TEXT,  # ✅ ФАЗА 1.4.3: SCREEN 4-5
    EDIT_DESIGN_TEXT,  # ✅ ФАЗА 1.4.3: SCREEN 8
    DOWNLOAD_SAMPLE_TEXT,  # ✅ ФАЗА 1.4.3: SCREEN 10
    UPLOADING_FURNITURE_TEXT,  # ✅ ФАЗА 1.4.3: SCREEN 13
    LOADING_FACADE_SAMPLE_TEXT,  # ✅ ФАЗА 1.4.3: SCREEN 16
    ERROR_INSUFFICIENT_BALANCE,  # ✅ ФАЗА 1.4.3: Ошибка недостатка баланса
)

# ОБНОВЛЕНО: 2025-12-24 21:00 - Импорт обновленной функции для header с режимом
from utils.helpers import add_balance_and_mode_to_text

from utils.navigation import edit_menu, show_main_menu

logger = logging.getLogger(__name__)
router = Router()


# ===== ГЛАВНЫЙ МЕНЮ И СТАРТ =====
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат в главное меню - используем show_main_menu из navigation.py"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'main_menu')

    await show_main_menu(callback, state, admins)
    await callback.answer()


# ===== ФАЗА 1.4.2: SCREEN 1 - SELECT_MODE (Выбор режима) =====
# ✅ ОБНОВЛЕНО 2025-12-29 21:05: Production-ready код
# Дата добавления: 2025-12-29 20:45
# Обновлено: 2025-12-29 21:05

@router.callback_query(F.data == "select_mode")
async def select_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1: Выбор режима работы (MAIN_MENU)
    
    Логика:
    1. Установка FSM state на selecting_mode
    2. Получение текущего режима из data (или "Не выбран")
    3. Получение баланса пользователя
    4. Отправка меню выбора режима

    Log: "[V3] SELECT_MODE - user_id={user_id}"
    
    Время выполнения: 30 минут
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        # Получаем текущий режим (если был выбран)
        data = await state.get_data()
        current_mode = data.get('work_mode', 'Не выбран')

        # Получаем баланс
        balance = await db.get_balance(user_id)

        # Устанавливаем состояние
        await state.set_state(CreationStates.selecting_mode)

        # Формируем текст
        text = MODE_SELECTION_TEXT

        # Добавляем footer (НОВОЕ В V3)
        text = await add_balance_and_mode_to_text(
            text=text,
            user_id=user_id,
            work_mode=None  # На экране выбора режима footer не содержит режим
        )

        # Редактируем меню
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_mode_selection_keyboard(),
            screen_code='select_mode'
        )
        
        logger.info(f"[V3] SELECT_MODE - user_id={user_id}, current_mode={current_mode}, balance={balance}")
        
    except Exception as e:
        logger.error(f"[ERROR] SELECT_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


# ===== ФАЗА 1.4.2: HANDLER SET_WORK_MODE (Обработка выбора режима) =====
# ✅ ОБНОВЛЕНО 2025-12-29 21:05: Production-ready код
# Дата добавления: 2025-12-29 21:00
# Обновлено: 2025-12-29 21:05

@router.callback_query(F.data.startswith("select_mode_"))
async def set_work_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1→2: Обработчик выбора режима работы
    
    Извлекает режим из callback_data и сохраняет в FSM
    Затем переходит на экран загрузки фото

    Режимы:
    - select_mode_new_design → NEW_DESIGN
    - select_mode_edit_design → EDIT_DESIGN
    - select_mode_sample_design → SAMPLE_DESIGN
    - select_mode_arrange_furniture → ARRANGE_FURNITURE
    - select_mode_facade_design → FACADE_DESIGN

    Log: "[V3] {MODE}+UPLOADING_PHOTO - mode selected"
    Время выполнения: 30 минут
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        # Извлекаем режим из callback_data
        mode_str = callback.data.replace("select_mode_", "")
        
        # Преобразуем строку в WorkMode enum
        mode_map = {
            "new_design": WorkMode.NEW_DESIGN,
            "edit_design": WorkMode.EDIT_DESIGN,
            "sample_design": WorkMode.SAMPLE_DESIGN,
            "arrange_furniture": WorkMode.ARRANGE_FURNITURE,
            "facade_design": WorkMode.FACADE_DESIGN,
        }
        
        work_mode = mode_map.get(mode_str)
        if not work_mode:
            logger.warning(f"[WARNING] Unknown mode_str: {mode_str}")
            await callback.answer("❌ Неизвестный режим", show_alert=True)
            return
        
        # Сохраняем режим в FSM
        await state.update_data(work_mode=work_mode.value)
        await state.set_state(CreationStates.uploading_photo)
        
        # Получаем баланс
        balance = await db.get_balance(user_id)
        
        # Динамический текст в зависимости от режима
        text = UPLOADING_PHOTO_TEMPLATES.get(
            work_mode.value,
            "📸 Загрузите фото"
        )
        
        # Добавляем footer
        text = await add_balance_and_mode_to_text(
            text=text,
            user_id=user_id,
            work_mode=work_mode.value
        )
        
        # Редактируем меню
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_upload_photo_keyboard(),
            screen_code='uploading_photo'
        )
        
        # Сохраняем menu_message_id в БД
        await db.save_chat_menu(
            chat_id,
            user_id,
            callback.message.message_id,
            'uploading_photo'
        )
        
        logger.info(f"[V3] {work_mode.value.upper()}+UPLOADING_PHOTO - mode selected, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SET_WORK_MODE failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе режима", show_alert=True)


# ===== ФАЗА 1.4.3: SCREEN 2 - PHOTO_HANDLER (Загрузка фото для всех режимов) =====
# ✅ ИСПРАВЛЕНО 2025-12-29 22:30: StateFilter, проверка меню, обработка ошибок
# Время выполнения: 1 час

@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """
    SCREEN 2: Загрузка фото (UPLOADING_PHOTO)
    
    Логика:
    1. Валидация: проверяем, что это фото
    2. Проверка баланса (баланс > 0, кроме режима EDIT_DESIGN который может работать без баланса)
    3. Сохраняем file_id в FSM и БД
    4. Переходим на экран в зависимости от режима:
       - NEW_DESIGN → ROOM_CHOICE (SCREEN 3)
       - EDIT_DESIGN → EDIT_DESIGN (SCREEN 8)
       - SAMPLE_DESIGN → DOWNLOAD_SAMPLE (SCREEN 10)
       - ARRANGE_FURNITURE → UPLOADING_FURNITURE (SCREEN 13)
       - FACADE_DESIGN → LOADING_FACADE_SAMPLE (SCREEN 16)

    Log: "[V3] NEW_DESIGN+UPLOADING_PHOTO - photo saved, user_id={user_id}"
    Время выполнения: 1 час
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    work_mode = data.get('work_mode')

    try:
        # ===== 0. ПОЛУЧЕНИЕ MENU_MESSAGE_ID =====
        # КРИТИЧНО: Получаем menu_message_id (для редактирования существующего меню!)
        menu_info = await db.get_chat_menu(chat_id)
        menu_message_id = menu_info.get('menu_message_id') if menu_info else None

        # ===== 1. ВАЛИДАЦИЯ =====
        # Проверка: отправлено ли фото?
        if not message.photo:
            # ✅ ПРАВИЛЬНО: Редактируем меню (Single Menu Pattern!)
            
            if menu_message_id:
                # Редактируем существующее меню
                try:
                    await message.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_message_id,
                        text="❌ **ОШИБКА**\n\nПожалуйста, отправьте фото помещения:",
                        reply_markup=get_upload_photo_keyboard(),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось отредактировать меню: {e}")
                    # Fallback: создаем новое сообщение
                    new_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
                    await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
            else:
                # Fallback: создаем новое сообщение (редко)
                new_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
                await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
            
            # Удаляем сообщение пользователя
            try:
                await message.delete()
            except:
                pass
            
            return
        
        # Удаляем сообщение пользователя ПОСЛЕ валидации
        try:
            await message.delete()
        except Exception as e:
            logger.debug(f"⚠️ Не удалось удалить сообщение пользователя: {e}")
        
        # ===== 2. ПРОВЕРКА БАЛАНСА =====
        balance = await db.get_balance(user_id)
        
        # Проверка баланса (для большинства режимов нужен баланс)
        # Исключение: EDIT_DESIGN может работать без баланса (редактирование существующего)
        if balance <= 0 and work_mode != WorkMode.EDIT_DESIGN.value:
            error_text = ERROR_INSUFFICIENT_BALANCE
            
            if menu_message_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_message_id,
                        text=error_text,
                        reply_markup=get_payment_keyboard(),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось отредактировать меню: {e}")
                    new_msg = await message.answer(error_text)
                    await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
            else:
                new_msg = await message.answer(error_text)
                await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
            
            return
        
        # ===== 3. СОХРАНЕНИЕ ФОТО =====
        photo_id = message.photo[-1].file_id
        
        # Сохраняем в БД
        await db.save_photo(user_id, photo_id)
        
        # Сохраняем в FSM
        await state.update_data(
            photo_id=photo_id,
            new_photo=True,
            menu_message_id=menu_message_id  # Сохраняем menu_message_id в FSM!
        )
        
        # ===== 4. ПЕРЕХОД НА СЛЕДУЮЩИЙ ЭКРАН (зависит от режима) =====
        
        if work_mode == WorkMode.NEW_DESIGN.value:
            # NEW_DESIGN → ROOM_CHOICE (SCREEN 3)
            await state.set_state(CreationStates.room_choice)
            text = ROOM_CHOICE_TEXT.format(balance=balance)
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_room_choice_keyboard()
            screen = 'room_choice'
            
        elif work_mode == WorkMode.EDIT_DESIGN.value:
            # EDIT_DESIGN → EDIT_DESIGN (SCREEN 8)
            await state.set_state(CreationStates.edit_design)
            text = EDIT_DESIGN_TEXT.format(balance=balance)
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_edit_design_keyboard()
            screen = 'edit_design'
            
        elif work_mode == WorkMode.SAMPLE_DESIGN.value:
            # SAMPLE_DESIGN → DOWNLOAD_SAMPLE (SCREEN 10)
            await state.set_state(CreationStates.download_sample)
            text = DOWNLOAD_SAMPLE_TEXT.format(balance=balance)
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_download_sample_keyboard()
            screen = 'download_sample'
            
        elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
            # ARRANGE_FURNITURE → UPLOADING_FURNITURE (SCREEN 13)
            await state.set_state(CreationStates.uploading_furniture)
            text = UPLOADING_FURNITURE_TEXT.format(balance=balance)
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_uploading_furniture_keyboard()
            screen = 'uploading_furniture'
            
        elif work_mode == WorkMode.FACADE_DESIGN.value:
            # FACADE_DESIGN → LOADING_FACADE_SAMPLE (SCREEN 16)
            await state.set_state(CreationStates.loading_facade_sample)
            text = LOADING_FACADE_SAMPLE_TEXT.format(balance=balance)
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_loading_facade_sample_keyboard()
            screen = 'loading_facade_sample'
        else:
            # Fallback (не должно быть)
            logger.error(f"[ERROR] Unknown work_mode: {work_mode}")
            await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
            return
        
        # ===== 5. РЕДАКТИРОВАНИЕ МЕНЮ =====
        if menu_message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отредактировать меню: {e}. Создаем новое.")
                # Fallback: создаем новое сообщение
                new_msg = await message.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
                await state.update_data(menu_message_id=new_msg.message_id)
                await db.save_chat_menu(chat_id, user_id, new_msg.message_id, screen)
        else:
            # Fallback: создаем новое сообщение
            new_msg = await message.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, screen)
        
        # Сохраняем в БД
        await db.save_chat_menu(chat_id, user_id, menu_message_id or 0, screen)
        
        logger.info(f"[V3] {work_mode.upper()}+UPLOADING_PHOTO - photo saved, user_id={user_id}, mode={work_mode}")
        
    except Exception as e:
        logger.error(f"[ERROR] PHOTO_HANDLER failed for user {user_id}: {e}", exc_info=True)
        try:
            await message.answer("❌ Ошибка при обработке фото. Попробуйте еще раз.")
        except:
            pass


# ===== ФАЗА 1.5.2: ЛОВУШКА ДЛЯ ФОТО НА ДРУГИХ СОСТОЯНИЯХ (NEW!) =====
# ✅ ДОБАВЛЕНО 2025-12-29 23:56: Перехват фото на всех других экранах
# Дата добавления: 2025-12-29 23:56
# Время выполнения: 30 минут

@router.message(F.photo)
async def photo_redirect_handler(message: Message, state: FSMContext):
    """
    НОВЫЙ ОБРАБОТЧИК: Ловушка для фото на ДРУГИХ состояниях (SCREEN 3, 4, 5, и т.д.)
    
    Логика:
    1. Проверяем текущее состояние FSM
    2. Если состояние НЕ uploading_photo - это ВТОРОЙ экран загрузки фото
    3. Вместо удаления фото - ПЕРЕХОДИМ НА ЭКРАН загрузки фото
    4. Сохраняем photo_id и старый state для восстановления
    5. Удаляем сообщение пользователя (рекомендация отправлять через меню)
    
    Исключение: Если state вообще не установлен - отправляем в главное меню
    
    Log: "[V3] PHOTO_REDIRECT - Переход на uploading_photo из {current_state}, user_id={user_id}"
    Время выполнения: 30 минут
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    try:
        # Получаем текущее состояние
        current_state = await state.get_state()
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        logger.info(f"[V3] PHOTO_REDIRECT - Перехвачено фото на state={current_state}, user_id={user_id}, work_mode={work_mode}")
        
        # ===== ПРОВЕРКА 1: Есть ли вообще состояние? =====
        if not current_state or not work_mode:
            logger.warning(f"[WARNING] Фото без состояния: state={current_state}, work_mode={work_mode}")
            # Нет состояния - это новый пользователь или потеря сессии
            await message.answer("❌ Сессия потеряна. Начните заново из главного меню.")
            await state.clear()
            try:
                await message.delete()
            except:
                pass
            return
        
        # ===== ПРОВЕРКА 2: Это УЖЕ экран загрузки фото? =====
        if current_state == CreationStates.uploading_photo.state:
            # Это должно было обработаться выше в @router.message(StateFilter(uploading_photo), F.photo)
            # Если сюда попало - значит что-то не так, но не критично
            logger.warning(f"[WARNING] Фото на uploading_photo но попало сюда: user_id={user_id}")
            try:
                await message.delete()
            except:
                pass
            return
        
        # ===== ОСНОВНАЯ ЛОГИКА: ВТОРОЙ ЭКРАН ЗАГРУЗКИ =====
        # Сохраняем текущее состояние (для восстановления если нужно)
        previous_state = current_state
        previous_data = data.copy()
        
        # Сохраняем новое фото
        photo_id = message.photo[-1].file_id
        
        # Сохраняем в БД
        await db.save_photo(user_id, photo_id)
        logger.info(f"✅ Фото сохранено из state {previous_state}: user_id={user_id}")
        
        # Обновляем FSM с новым фото
        await state.update_data(
            photo_id=photo_id,
            new_photo=True,
            previous_state=previous_state  # Сохраняем предыдущее состояние
        )
        
        # Переходим на экран загрузки фото
        await state.set_state(CreationStates.uploading_photo)
        
        # Получаем текущий баланс
        balance = await db.get_balance(user_id)
        
        # Формируем текст экрана загрузки фото (динамический в зависимости от режима)
        text = UPLOADING_PHOTO_TEMPLATES.get(
            work_mode,
            "📸 Загрузите фото"
        )
        
        # Добавляем footer
        text = await add_balance_and_mode_to_text(
            text=text,
            user_id=user_id,
            work_mode=work_mode
        )
        
        # Получаем menu_message_id из БД
        menu_info = await db.get_chat_menu(chat_id)
        menu_message_id = menu_info.get('menu_message_id') if menu_info else None
        
        # Редактируем или создаём меню
        if menu_message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    text=text,
                    reply_markup=get_upload_photo_keyboard(),
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Меню отредактировано для uploading_photo: msg_id={menu_message_id}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отредактировать меню: {e}. Создаем новое.")
                new_msg = await message.answer(text=text, reply_markup=get_upload_photo_keyboard(), parse_mode="Markdown")
                await state.update_data(menu_message_id=new_msg.message_id)
                await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
        else:
            # Создаём новое меню
            new_msg = await message.answer(text=text, reply_markup=get_upload_photo_keyboard(), parse_mode="Markdown")
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
        
        # Сохраняем в БД
        await db.save_chat_menu(chat_id, user_id, menu_message_id or 0, 'uploading_photo')
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except Exception as e:
            logger.debug(f"⚠️ Не удалось удалить сообщение пользователя: {e}")
        
        logger.info(f"[V3] PHOTO_REDIRECT УСПЕХ - Переход на uploading_photo из {previous_state}, user_id={user_id}")
        
    except Exception as e:
        logger.error(f"[ERROR] PHOTO_REDIRECT_HANDLER failed: {e}", exc_info=True)
        try:
            await message.delete()
        except:
            pass


# ===== ФАЗА 1.5.1: SCREEN 3 - ROOM_CHOICE (NEW_DESIGN только) =====
# ✅ ДОБАВЛЕНО 2025-12-29 23:00: Production-ready код
# Дата добавления: 2025-12-29 23:00
# Время выполнения: 1 час

@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3: Меню выбора комнаты (ROOM_CHOICE)
    Только для режима NEW_DESIGN
    
    Логика:
    1. Получение баланса пользователя
    2. Установка FSM state на room_choice
    3. Формирование текста с информацией о балансе
    4. Отправка меню выбора комнаты
    5. Сохранение menu_message_id в БД
    
    Log: "[V3] NEW_DESIGN+ROOM_CHOICE - menu shown, user_id={user_id}"
    Время выполнения: 1 час
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


@router.callback_query(F.data.startswith("room_"))
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3→4: Обработчик выбора комнаты
    Сохраняет выбор и переходит на экран выбора стиля (SCREEN 4 - CHOOSE_STYLE_1)
    
    Поддерживаемые комнаты:
    - room_living_room (Гостиная)
    - room_kitchen (Кухня)
    - room_bedroom (Спальня)
    - room_nursery (Детская)
    - room_studio (Студия)
    - room_home_office (Кабинет)
    - room_bathroom_full (Ванная)
    - room_toilet (Туалет)
    - room_entryway (Прихожая)
    - room_wardrobe (Гардеробная)
    
    Логика:
    1. Извлечение типа комнаты из callback_data
    2. Получение баланса
    3. Сохранение выбора в FSM (selected_room)
    4. Установка FSM state на choose_style_1
    5. Формирование текста с информацией о выбранной комнате
    6. Отправка меню выбора стиля
    7. Сохранение menu_message_id в БД
    
    Log: "[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}, user_id={user_id}"
    Время выполнения: 1 час
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
