import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from database.db import db

from keyboards.inline import (
    get_work_mode_selection_keyboard,
    get_uploading_photo_keyboard,
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
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    WHAT_IS_IN_PHOTO_TEXT,
    ERROR_INSUFFICIENT_BALANCE,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

logger = logging.getLogger(__name__)
router = Router()

# 📀 Отслеживание альбомов для удаления
media_group_cache = {}


async def collect_all_media_group_photos(user_id: int, media_group_id: str, message_id: int):
    """
    📀 Отслеживание всех фото альбома и удаление всех сразу
    
    Процесс:
    1. Первое фото → регистрируем
    2. Ждём 1сек - приходят остальные
    3. Отмечаем как собранные
    4. Возвращаем все message_ids для удаления
    """
    if user_id not in media_group_cache:
        media_group_cache[user_id] = {}
    
    if media_group_id not in media_group_cache[user_id]:
        media_group_cache[user_id][media_group_id] = {
            'message_ids': [message_id],
            'collected': False
        }
        logger.info(f"📀 [COLLECT] user={user_id}, group={media_group_id}, photo #1")
        
        await asyncio.sleep(1.0)
        
        media_group_cache[user_id][media_group_id]['collected'] = True
        
        final_ids = media_group_cache[user_id][media_group_id]['message_ids'].copy()
        logger.info(f"📀 [COLLECT] DONE: {len(final_ids)} photos")
        return final_ids
    else:
        if not media_group_cache[user_id][media_group_id]['collected']:
            media_group_cache[user_id][media_group_id]['message_ids'].append(message_id)
            count = len(media_group_cache[user_id][media_group_id]['message_ids'])
            logger.info(f"📀 [COLLECT] photo #{count} added")
        
        return None


# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
# 🎪 [SCREEN 0] ГЛАВНОЕ МЕНЮ
# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    🎪 [SCREEN 0] Вернуться в главное меню
    """
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'main_menu')
    await show_main_menu(callback, state, admins)
    await callback.answer()


# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
# 📋 [SCREEN 1] ВЫБОР МОДИ РАБОТЫ
# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

@router.callback_query(F.data == "select_mode")
async def select_mode(callback: CallbackQuery, state: FSMContext):
    """
    📋 [SCREEN 1] Выбор режима работы
    
    🔍 ПУТЬ: [SCREEN 0] → "🎫 Создать дизайн" → [SCREEN 1]
    
    🔍 5 МОДОВ:
    - 📋 Новый дизайн (NEW_DESIGN)
    - ✍️ Редактирование (EDIT_DESIGN)
    - 🎁 Примерка (SAMPLE_DESIGN)
    - 📋 Мебель (ARRANGE_FURNITURE)
    - 🏠 Фасад (FACADE_DESIGN)
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        await state.set_state(CreationStates.selecting_mode)
        text = MODE_SELECTION_TEXT
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_work_mode_selection_keyboard(),
            show_balance=False,
            screen_code='select_mode'
        )
        
        logger.info(f"[SCREEN 1] Showing 5 modes, user_id={user_id}")
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 1 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ёщё раз.", show_alert=True)


# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
# 📋 [SCREEN 1→2] ОБРАБОТКА ВЫБОРА МОДОВ
# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

@router.callback_query(F.data.startswith("select_mode_"))
async def set_work_mode(callback: CallbackQuery, state: FSMContext):
    """
    📋 [SCREEN 1→2] Обработка выбора режима
    
    🔍 ПУТЬ: [SCREEN 1] → выбрал режим → [SCREEN 2: лоаджка фото]
    
    ✏️ НОВОЕ (2026-01-02): Проверяем в БД есть ли последняя фото
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id

    try:
        mode_str = callback.data.replace("select_mode_", "")
        
        mode_map = {
            "new_design": WorkMode.NEW_DESIGN,
            "edit_design": WorkMode.EDIT_DESIGN,
            "sample_design": WorkMode.SAMPLE_DESIGN,
            "arrange_furniture": WorkMode.ARRANGE_FURNITURE,
            "facade_design": WorkMode.FACADE_DESIGN,
        }
        
        work_mode = mode_map.get(mode_str)
        if not work_mode:
            logger.warning(f"[WARNING] Unknown mode: {mode_str}")
            await callback.answer("❌ Неизвестный режим", show_alert=True)
            return
        
        # 📄 НОВОЕ: Проверяем опытнюю фото в БД
        last_photo_id = await db.get_last_user_photo(user_id)
        has_previous_photo = last_photo_id is not None
        
        logger.info(f"[SCREEN 1→2] Модь {work_mode.value}, фото в БД: {has_previous_photo}, user_id={user_id}")
        
        await state.update_data(
            work_mode=work_mode.value,
            photo_uploaded=False,
            has_previous_photo=has_previous_photo
        )
        await state.set_state(CreationStates.uploading_photo)
        
        text = UPLOADING_PHOTO_TEMPLATES.get(work_mode.value, "📄 Лоаджка фото")
        
        # 📄 НОВОЕ: Передаем флаг в клавиатуру
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_uploading_photo_keyboard(has_previous_photo=has_previous_photo),
            show_balance=False,
            screen_code='uploading_photo'
        )
        
        logger.info(f"[SCREEN 1→2] Mode selected: {work_mode.value}, user_id={user_id}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 1→2 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при выборе режима", show_alert=True)


# 📄 НОВОЕ: ОБОРАТЧОК "ОПЫТНАЯ ФОТО" (2026-01-02)
@router.callback_query(F.data == "use_current_photo")
async def use_current_photo(callback: CallbackQuery, state: FSMContext):
    """
    📐 [SCREEN 2] Использовать сохраненную фото из БД
    
    🔍 ПУТЬ: [SCREEN 2] → кнопка использовать → [SCREEN 3+]
    
    КРИТИЧНО:
    - Получаем photo_id из БД
    - Обновляем FSM state
    - Отвратываем К ПОЗОЛОЦ выбора режима
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        data = await state.get_data()
        work_mode = data.get('work_mode')
        
        # Получаем photo_id из БД (НО НЕ из state!)
        photo_id = await db.get_last_user_photo(user_id)
        
        if not photo_id:
            logger.warning(f"⚠️ Фото не найдена в БД для user_id={user_id}")
            await callback.answer(
                "❌ Фото не найдена. Лоаджка новою.",
                show_alert=True
            )
            return
        
        # Сохраняем фото в FSM
        await state.update_data(
            photo_id=photo_id,
            photo_uploaded=True,
            new_photo=False  # НЕ новая все старая
        )
        
        logger.info(f"📐 Опытная фото выбрана: {photo_id[:20]}... (user_id={user_id})")
        
        # ОПОВЕДОМЛЯЕМ ВЫБОР ROOM НА ОНОВОЕ PHOTO
        if work_mode == WorkMode.NEW_DESIGN.value:
            await state.set_state(CreationStates.room_choice)
            text = f"🏠 **Выберите комнату**"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode='new_design')
            keyboard = get_room_choice_keyboard()
            screen = 'room_choice'
            
        elif work_mode == WorkMode.EDIT_DESIGN.value:
            await state.set_state(CreationStates.edit_design)
            text = f"✍️ **Редактируем дизайн**"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode='edit_design')
            keyboard = get_edit_design_keyboard()
            screen = 'edit_design'
            
        elif work_mode == WorkMode.SAMPLE_DESIGN.value:
            await state.set_state(CreationStates.download_sample)
            text = f"📄 **Скачать примеры**"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode='sample_design')
            keyboard = get_download_sample_keyboard()
            screen = 'download_sample'
            
        elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
            await state.set_state(CreationStates.uploading_furniture)
            text = f"📋 **Расставка мебели**"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode='arrange_furniture')
            keyboard = get_uploading_furniture_keyboard()
            screen = 'uploading_furniture'
            
        elif work_mode == WorkMode.FACADE_DESIGN.value:
            await state.set_state(CreationStates.loading_facade_sample)
            text = f"🏠 **Дизайн фасада**"
            text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
            keyboard = get_loading_facade_sample_keyboard()
            screen = 'loading_facade_sample'
        else:
            logger.error(f"[ERROR] Неизвестный work_mode: {work_mode}")
            await callback.answer("❌ Неизвестный режим")
            return
        
        # Отправляем меню
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=keyboard,
            show_balance=False,
            screen_code=screen
        )
        
        logger.info(f"📐 Опытная фото использована, переход на {screen}")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] use_current_photo failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё.", show_alert=True)


# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
# 📄 [SCREEN 2] ЛОАДЖКА ФОТО
# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """
    📄 [SCREEN 2] Обработка лоаджки фото
    
    🔍 ПУТЬ: [SCREEN 2] → лоаджка фото → [SCREEN 3+] (выбор режима)
    
    📀 ЛОГИКА:
    1. Если альбом → собрать, удалить все, выксести
    2. Одиночное фото → Обработать нормально
    
    🔏 НОВОЕ (2026-01-02): Сохраняем photo_id в БД!
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 📀 АЛЬБОМ ФОТО - Удалить все
    if message.media_group_id:
        logger.info(f"📀 [ALBUM] media_group_id={message.media_group_id}")
        
        collected_ids = await collect_all_media_group_photos(
            user_id,
            message.media_group_id,
            message.message_id
        )
        
        if collected_ids:
            logger.warning(f"❌ [ALBUM] {len(collected_ids)} фото детектировано!")
            
            delete_tasks = []
            for msg_id in collected_ids:
                delete_tasks.append(
                    message.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                )
            
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"🗑️ [ALBUM] Удалено {success_count}/{len(collected_ids)} фото")
        
        return
    
    # 📄 ОДИНОЧНОЕ ФОТО - Обработать
    logger.info(f"📄 [SINGLE] Одиночное фото")
    
    data = await state.get_data()
    work_mode = data.get('work_mode')
    
    if not message.photo:
        error_msg = await message.answer("❌ Пожалуйста, отправьте фото:")
        await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
        asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
        return
    
    balance = await db.get_balance(user_id)
    if balance <= 0 and work_mode != WorkMode.EDIT_DESIGN.value:
        error_text = ERROR_INSUFFICIENT_BALANCE
        error_msg = await message.answer(error_text)
        await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'uploading_photo')
        asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))
        return
    
    photo_id = message.photo[-1].file_id
    
    # 🔏 НОВОЕ (2026-01-02): Сохраняем в БД!
    save_success = await db.save_user_photo(user_id, photo_id)
    if save_success:
        logger.info(f"📄 Фото сохранена в БД")
    else:
        logger.error(f"❌ Ошибка сохранения photo_id в БД")
    
    logger.info(f"📐 [SCREEN 2] Фото сохранено")
    
    await state.update_data(
        photo_id=photo_id,
        new_photo=True,
        photo_uploaded=True
    )
    
    old_menu_data = await db.get_chat_menu(chat_id)
    old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None
    
    if old_menu_message_id:
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=old_menu_message_id)
            logger.info(f"🗑️ [SCREEN 2] Удалено старое меню")
        except Exception as e:
            logger.debug(f"⚠️ Не удалось удалить: {e}")
    
    # ОПОВЕДОМЛЯЕМ СЛЕДУЮЩИЙ ЭКРАН
    if work_mode == WorkMode.NEW_DESIGN.value:
        await state.set_state(CreationStates.room_choice)
        text = f"🏠 **Выберите комнату**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='new_design')
        keyboard = get_room_choice_keyboard()
        screen = 'room_choice'
        
    elif work_mode == WorkMode.EDIT_DESIGN.value:
        await state.set_state(CreationStates.edit_design)
        text = f"✍️ **Редактируем дизайн**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='edit_design')
        keyboard = get_edit_design_keyboard()
        screen = 'edit_design'
        
    elif work_mode == WorkMode.SAMPLE_DESIGN.value:
        await state.set_state(CreationStates.download_sample)
        text = f"📄 **Скачать примеры**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='sample_design')
        keyboard = get_download_sample_keyboard()
        screen = 'download_sample'
        
    elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
        await state.set_state(CreationStates.uploading_furniture)
        text = f"📋 **Расставка мебели**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='arrange_furniture')
        keyboard = get_uploading_furniture_keyboard()
        screen = 'uploading_furniture'
        
    elif work_mode == WorkMode.FACADE_DESIGN.value:
        await state.set_state(CreationStates.loading_facade_sample)
        text = f"🏠 **Дизайн фасада**"
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
        keyboard = get_loading_facade_sample_keyboard()
        screen = 'loading_facade_sample'
    else:
        logger.error(f"[ERROR] Неизвестный work_mode: {work_mode}")
        await message.answer("❌ Неизвестный режим. Вернитесь в главное меню.")
        return
    
    logger.info(f"📄 [SCREEN 2] Отправлям меню - screen={screen}")
    menu_msg = await message.answer(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"✅ [SCREEN 2] Меню отправлено")
    
    await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, screen)
    await state.update_data(menu_message_id=menu_msg.message_id)
    
    logger.info(f"📀 [SCREEN 2] COMPLETED - переход на {screen}")


async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int):
    """Удалить сообщение через N секунд"""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"✅ Удалено сообщение {message_id}")
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить: {e}")


# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
# 📋 [СТАРАЯ СИСТЕМА] что-то
# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    """Начать создание дизайна (старая система)"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'create_design')

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()

    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    await state.set_state(CreationStates.uploading_photo)

    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=get_uploading_photo_keyboard(),
        show_balance=False,
        screen_code='upload_photo'
    )
