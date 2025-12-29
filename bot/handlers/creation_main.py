# bot/handlers/creation_main.py
# ===== PHASE 1: MAIN ENTRY POINT + PHOTO UPLOAD =====
# [2025-12-29] НОВЫЙ ФАЙЛ: Часть 1 рефакторинга creation.py
# Содержит: select_mode (SCREEN 1), set_work_mode, photo_handler (SCREEN 2)
# + старые handlers для обратной совместимости (what_is_in_photo)

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StateFilter
from aiogram.types import CallbackQuery, Message

from database.db import db

from keyboards.inline import (
    get_mode_selection_keyboard,
    get_upload_photo_keyboard,
    get_what_is_in_photo_keyboard,
    get_payment_keyboard,
    get_room_choice_keyboard,
    get_edit_design_keyboard,
    get_download_sample_keyboard,
    get_uploading_furniture_keyboard,
    get_loading_facade_sample_keyboard,
)

from states.fsm import CreationStates, WorkMode

from utils.texts import (
    MODE_SELECTION_TEXT,
    UPLOADING_PHOTO_TEMPLATES,
    PHOTO_SAVED_TEXT,
    NO_BALANCE_TEXT,
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    WHAT_IS_IN_PHOTO_TEXT,
    ERROR_INSUFFICIENT_BALANCE,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

logger = logging.getLogger(__name__)
router = Router()


# ===== SCREEN 0: MAIN MENU =====
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'main_menu')
    await show_main_menu(callback, state, admins)
    await callback.answer()


# ===== SCREEN 1: SELECT_MODE (Выбор режима) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(F.data == "select_mode")
async def select_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1: Выбор режима работы
    
    Логика:
    1. Получение текущего режима из FSM
    2. Получение баланса пользователя
    3. Отправка меню выбора режима
    
    Log: "[V3] SELECT_MODE - user_id={user_id}"
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        # Получаем текущий режим
        data = await state.get_data()
        current_mode = data.get('work_mode', 'Не выбран')

        # Получаем баланс
        balance = await db.get_balance(user_id)

        # Устанавливаем состояние
        await state.set_state(CreationStates.selecting_mode)

        # Формируем текст
        text = MODE_SELECTION_TEXT

        # Добавляем footer с балансом
        text = await add_balance_and_mode_to_text(text=text, user_id=user_id, work_mode=None)

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


# ===== HANDLER: SET_WORK_MODE (Обработка выбора режима) =====
# [2025-12-29] НОВОЕ (V3)
@router.callback_query(F.data.startswith("select_mode_"))
async def set_work_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1→2: Обработчик выбора режима работы
    
    Режимы:
    - select_mode_new_design → NEW_DESIGN
    - select_mode_edit_design → EDIT_DESIGN
    - select_mode_sample_design → SAMPLE_DESIGN
    - select_mode_arrange_furniture → ARRANGE_FURNITURE
    - select_mode_facade_design → FACADE_DESIGN
    
    Log: "[V3] {MODE}+UPLOADING_PHOTO - mode selected"
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
        text = UPLOADING_PHOTO_TEMPLATES.get(work_mode.value, "📸 Загрузите фото")
        
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


# ===== SCREEN 2: PHOTO_HANDLER (Загрузка фото для всех режимов) =====
# [2025-12-29] ОБНОВЛЕНО (V3)
@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """
    SCREEN 2: Загрузка фото (UPLOADING_PHOTO)
    
    Логика:
    1. Валидация фото
    2. Проверка баланса (кроме EDIT_DESIGN)
    3. Сохранение file_id в FSM и БД
    4. Переход на СЛЕДУЮЩИЙ экран (зависит от режима):
       - NEW_DESIGN → ROOM_CHOICE
       - EDIT_DESIGN → EDIT_DESIGN
       - SAMPLE_DESIGN → DOWNLOAD_SAMPLE
       - ARRANGE_FURNITURE → UPLOADING_FURNITURE
       - FACADE_DESIGN → LOADING_FACADE_SAMPLE
    
    Log: "[V3] {MODE}+UPLOADING_PHOTO - photo saved, user_id={user_id}"
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    work_mode = data.get('work_mode')

    try:
        # ===== 1. ПОЛУЧЕНИЕ MENU_MESSAGE_ID =====
        menu_info = await db.get_chat_menu(chat_id)
        menu_message_id = menu_info.get('menu_message_id') if menu_info else None

        # ===== 2. ВАЛИДАЦИЯ =====
        if not message.photo:
            if menu_message_id:
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
                    new_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
                    await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
            else:
                new_msg = await message.answer("❌ Пожалуйста, отправьте фото помещения:")
                await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'uploading_photo')
            
            try:
                await message.delete()
            except:
                pass
            return
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except Exception as e:
            logger.debug(f"⚠️ Не удалось удалить сообщение пользователя: {e}")
        
        # ===== 3. ПРОВЕРКА БАЛАНСА =====
        balance = await db.get_balance(user_id)
        
        # Исключение для EDIT_DESIGN: может работать БЕЗ баланса
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
        
        # ===== 4. СОХРАНЕНИЕ ФОТО =====
        photo_id = message.photo[-1].file_id
        await db.save_photo(user_id, photo_id)
        
        await state.update_data(
            photo_id=photo_id,
            new_photo=True,
            menu_message_id=menu_message_id
        )
        
        # ===== 5. ПЕРЕХОД НА СЛЕДУЮЩИЙ ЭКРАН (зависит от режима) =====
        
        if work_mode == WorkMode.NEW_DESIGN.value:
            # NEW_DESIGN → ROOM_CHOICE (SCREEN 3)
            await state.set_state(CreationStates.room_choice)
            text = f"🏠 **Выберите комнату** \n\nБаланс: {balance}"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_room_choice_keyboard()
            screen = 'room_choice'
            
        elif work_mode == WorkMode.EDIT_DESIGN.value:
            # EDIT_DESIGN → EDIT_DESIGN (SCREEN 8)
            await state.set_state(CreationStates.edit_design)
            text = f"✏️ **Редактируем дизайн** \n\nБаланс: {balance}"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_edit_design_keyboard()
            screen = 'edit_design'
            
        elif work_mode == WorkMode.SAMPLE_DESIGN.value:
            # SAMPLE_DESIGN → DOWNLOAD_SAMPLE (SCREEN 10)
            await state.set_state(CreationStates.download_sample)
            text = f"📥 **Скачать примеры** \n\nБаланс: {balance}"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_download_sample_keyboard()
            screen = 'download_sample'
            
        elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
            # ARRANGE_FURNITURE → UPLOADING_FURNITURE (SCREEN 13)
            await state.set_state(CreationStates.uploading_furniture)
            text = f"🛋️ **Расстановка мебели** \n\nБаланс: {balance}"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_uploading_furniture_keyboard()
            screen = 'uploading_furniture'
            
        elif work_mode == WorkMode.FACADE_DESIGN.value:
            # FACADE_DESIGN → LOADING_FACADE_SAMPLE (SCREEN 16)
            await state.set_state(CreationStates.loading_facade_sample)
            text = f"🏢 **Дизайн фасада** \n\nБаланс: {balance}"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode)
            keyboard = get_loading_facade_sample_keyboard()
            screen = 'loading_facade_sample'
        else:
            logger.error(f"[ERROR] Unknown work_mode: {work_mode}")
            await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
            return
        
        # ===== 6. РЕДАКТИРОВАНИЕ МЕНЮ =====
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
                new_msg = await message.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
                await state.update_data(menu_message_id=new_msg.message_id)
                await db.save_chat_menu(chat_id, user_id, new_msg.message_id, screen)
        else:
            new_msg = await message.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
            await state.update_data(menu_message_id=new_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, new_msg.message_id, screen)
        
        # Сохраняем в БД
        await db.save_chat_menu(chat_id, user_id, menu_message_id or 0, screen)
        
        logger.info(f"[V3] {work_mode.upper()}+UPLOADING_PHOTO - photo saved, user_id={user_id}")
        
    except Exception as e:
        logger.error(f"[ERROR] PHOTO_HANDLER failed for user {user_id}: {e}", exc_info=True)
        try:
            await message.answer("❌ Ошибка при обработке фото. Попробуйте еще раз.")
        except:
            pass


# ===== OLD SYSTEM: CREATE_DESIGN (для обратной совместимости) =====
@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    """Начало создания дизайна (старая система)"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'create_design')

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()

    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    await state.set_state(CreationStates.waiting_for_photo)

    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=get_upload_photo_keyboard(),
        screen_code='upload_photo'
    )
    await callback.answer()


# ===== OLD SYSTEM: PHOTO_UPLOADED (для what_is_in_photo) =====
@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    """Обработка загруженного фото (старая система -> what_is_in_photo)"""
    user_id = message.from_user.id
    await db.log_activity(user_id, 'photo_upload')

    # Блок альбомов
    if message.media_group_id:
        data = await state.get_data()
        cached_group_id = data.get('media_group_id')
        try:
            await message.delete()
        except Exception:
            pass
        if cached_group_id != message.media_group_id:
            await state.update_data(media_group_id=message.media_group_id)
            msg = await message.answer(TOO_MANY_PHOTOS_TEXT)
            await asyncio.sleep(3)
            try:
                await msg.delete()
            except Exception:
                pass
        return

    await state.update_data(media_group_id=None)
    photo_file_id = message.photo[-1].file_id

    # Проверка баланса
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            menu_msg = await message.answer(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard(),
                parse_mode="Markdown"
            )
            await state.update_data(menu_message_id=menu_msg.message_id)
            chat_id = message.chat.id
            await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'no_balance')
            return

    # Сохраняем фото и переходим к экрану "Что на фото"
    await state.update_data(photo_id=photo_file_id)
    await state.update_data(scene_type=None, room=None, style=None)
    await state.set_state(CreationStates.what_is_in_photo)

    # Удаляем старое меню
    data = await state.get_data()
    old_menu_id = data.get('menu_message_id')
    if old_menu_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=old_menu_id
            )
        except Exception as e:
            logger.debug(f"Не удалось удалить старое меню: {e}")

    # Отправляем НОВОЕ сообщение с экраном "Что на фото"
    text_with_balance = await add_balance_and_mode_to_text(WHAT_IS_IN_PHOTO_TEXT, user_id)
    sent_msg = await message.answer(
        text=text_with_balance,
        reply_markup=get_what_is_in_photo_keyboard(),
        parse_mode="Markdown"
    )

    await state.update_data(menu_message_id=sent_msg.message_id)
    await db.save_chat_menu(message.chat.id, user_id, sent_msg.message_id, 'what_is_in_photo')

    logger.info(f"[V3] PHOTO_UPLOADED - what_is_in_photo screen shown, user_id={user_id}")
