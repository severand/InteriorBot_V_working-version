import logging
import asyncio
import uuid
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from keyboards.inline import get_generation_try_on_keyboard, get_post_generation_sample_keyboard
from states.fsm import CreationStates, WorkMode
from utils.helpers import add_balance_and_mode_to_text
from utils.texts import GENERATION_TRY_ON_TEXT
from services.kie_api import apply_style_to_room
from config import config

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


# ══════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 10] ЗАГРУЗКА ОБРАЗЦА ФОТО (SAMPLE_DESIGN)
# 🔧 [2026-01-03 17:51] КРИТИЧНО: ДОБАВЛЕНО СОХРАНЕНИЕ ОБРАЗЦА В БД!
# ══════════════════════════════════════════════════════════════════════════════

@router.message(StateFilter(CreationStates.download_sample), F.photo)
async def download_sample_photo_handler(message: Message, state: FSMContext):
    """
    🎁 [SCREEN 10] Обработка загрузки образца фото (второе фото)
    
    📍 ПУТЬ: [SCREEN 10: download_sample] → загружка фото образца → [SCREEN 11: generation_try_on]
    
    🔧 [2026-01-03 17:51] КРИТИЧНО:
    - Образец сохраняется в FSM (для текущей сессии)
    - Образец сохраняется в БД (для повторного использования)
    - Может заменяться многократно
    - Основное фото (main_photo_id) НЕ трогается
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    try:
        logger.info(f"🎁 [SCREEN 10] Загруженный образец фото")
        
        data = await state.get_data()
        work_mode = data.get('work_mode')
        photo_id = message.photo[-1].file_id
        
        # 🎯 Сохраняем photo_id образца В ДВУХ МЕСТАХ:
        # 1️⃣ В FSM (для текущей сессии)
        await state.update_data(
            sample_photo_id=photo_id,  # ОБРАЗЕЦ фото
            session_started=False
        )
        logger.info(f"📄 [FSM] Образец фото сохранено в FSM: {photo_id[:30]}...")
        
        # 2️⃣ В БД (sample_photo_id для повторного использования) - ⭐ НОВОЕ
        await db.save_sample_photo(user_id, photo_id)
        logger.info(f"📄 [БД] Образец фото сохранено в user_photos.sample_photo_id")
        
        # Удаляем старое меню (SCREEN 10)
        old_menu_data = await db.get_chat_menu(chat_id)
        old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None
        
        if old_menu_message_id:
            try:
                await message.bot.delete_message(chat_id=chat_id, message_id=old_menu_message_id)
                logger.info(f"🗑️ [SCREEN 10] Удалено старое меню (msg_id={old_menu_message_id})")
            except Exception as e:
                logger.debug(f"⚠️ Не удалось удалить: {e}")
        
        # ПЕРЕХОД НА SCREEN 11: generation_try_on
        await state.set_state(CreationStates.generation_try_on)
        
        text = GENERATION_TRY_ON_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='sample_design')
        keyboard = get_generation_try_on_keyboard()
        
        logger.info(f"🎁 [SCREEN 10→11] Отправляю меню SCREEN 11 с кнопкой примерки")
        menu_msg = await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"✅ [SCREEN 10→11] Меню SCREEN 11 отправлено (msg_id={menu_msg.message_id})")
        
        await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'generation_try_on')
        await state.update_data(menu_message_id=menu_msg.message_id)
        
        logger.info(f"📄 [SCREEN 10→11] COMPLETED - переход на generation_try_on")
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 10 photo handler failed: {e}", exc_info=True)
        error_msg = await message.answer(f"❌ Ошибка при загрузке образца: {str(e)[:50]}")
        await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'download_sample')
        asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))


# ════════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 11] КНОПКА: "🎨 Примерить дизайн"
# ════════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.generation_try_on),
    F.data == "generate_try_on"
)
async def generate_try_on_handler(callback: CallbackQuery, state: FSMContext):
    """
    🎁 [SCREEN 11] КНОПКА: "🎨 Примерить дизайн"

    📍 ПУТЬ: [SCREEN 11: generation_try_on] → Кнопка → [Запуск генерации примерки]

    🔧 [2026-01-03 21:20] РЕАЛИЗОВАНО:
    - Получаем основное фото (main_photo_id) из FSM или БД
    - Получаем образец фото (sample_photo_id) из FSM
    - Вызываем apply_style_to_room(main_photo_id, sample_photo_id)
    - Показываем "⏳ Генерируем примерку..."
    - При готовности показываем результат с клавиатурой SCREEN 12
    - На ошибку показываем сообщение об ошибке
    
    📊 [2026-01-03 19:17] ЛОГИРОВАНИЕ:
    - ДЕТАЛЬНЫЕ логи источника фото (БД vs FSM)
    - Для отладки перезагрузки при потере FSM
    
    🔧 [2026-01-03 19:40] КРИТИЧНО FIX:
    - Отправляем ОТДЕЛЬНОЕ текстовое сообщение с кнопками ПОСЛЕ фото
    - Фото отправляется БЕЗ кнопок (просто с caption)
    - Это предотвращает удаление меню при перезагрузке бота
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    request_id = str(uuid.uuid4())[:8]

    try:
        logger.info(f"🎁 [SCREEN 11] КНОПКА НАЖАТА: user_id={user_id}")
        logger.info(f"═" * 80)
        logger.info(f"📊 [SCREEN 11] ДИАГНОСТИКА ЗАГРУЗКИ ФОТО")
        logger.info(f"═" * 80)
        
        # 🔄 ЗАГРУЖЕННЫЙ ОБРАЗЕЦ
        data = await state.get_data()
        sample_photo_id = data.get('sample_photo_id')
        
        logger.info(f"\n1️⃣  ОБРАЗЕЦ ФОТО (sample_photo_id):")
        if sample_photo_id:
            logger.info(f"   ✅ НАЙДЕН в FSM: {sample_photo_id[:40]}...")
        else:
            logger.error(f"   ❌ НЕ НАЙДЕН в FSM")
        
        if not sample_photo_id:
            logger.error("❌ Образец фото не найден в FSM")
            await callback.answer(
                "❌ Ошибка: образец фото не найден. Загрузите образец еще раз.",
                show_alert=True
            )
            return
        
        # 🎯 ПОЛУЧАЕМ ОСНОВНОЕ ФОТО (С ПОДРОБНЫМ ЛОГИРОВАНИЕМ)
        logger.info(f"\n2️⃣  ОСНОВНОЕ ФОТО (main_photo_id):")
        logger.info(f"   🔍 Проверяю источники данных...")
        
        # ПОПЫТКА 1: БД
        logger.info(f"   📌 ПОПЫТКА 1: Получаю из БД...")
        user_photos = await db.get_user_photos(user_id)
        logger.info(f"   📦 Результат get_user_photos(): {user_photos}")
        
        main_photo_id = user_photos.get('photo_id') if user_photos else None
        
        if user_photos is None:
            logger.warning(f"   ⚠️  БД: Запрос вернул NULL (нет записи в таблице user_photos)")
        elif isinstance(user_photos, dict):
            if 'photo_id' in user_photos:
                photo_value = user_photos['photo_id']
                if photo_value:
                    logger.info(f"   ✅ БД: photo_id найден: {photo_value[:40]}...")
                else:
                    logger.warning(f"   ⚠️  БД: photo_id найден, но ПУСТ (NULL)")
            else:
                logger.warning(f"   ⚠️  БД: Поле photo_id отсутствует в словаре")
                logger.info(f"      Доступные ключи: {list(user_photos.keys())}")
        
        # ПОПЫТКА 2: FSM (Fallback)
        if not main_photo_id:
            logger.info(f"   📌 ПОПЫТКА 2: БД вернула пусто, беру из FSM (fallback)...")
            main_photo_id = data.get('photo_id')
            
            if main_photo_id:
                logger.info(f"   ✅ FSM: photo_id найден (FALLBACK): {main_photo_id[:40]}...")
                logger.warning(f"   ⚠️  ВНИМАНИЕ: Используется photo_id из FSM (не из БД!)")
                logger.warning(f"   ⚠️  Это может означать:")
                logger.warning(f"      - Перезагрузка бота (FSM восстановлен из памяти)")
                logger.warning(f"      - Баг в сохранении в БД")
                logger.warning(f"      - Первый раз загрузки в этой сессии")
            else:
                logger.error(f"   ❌ FSM: photo_id ОТСУТСТВУЕТ")
        else:
            logger.info(f"   ✅ ИСТОЧНИК: БД")
        
        # ИТОГОВЫЙ РЕЗУЛЬТАТ
        logger.info(f"\n3️⃣  ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        if main_photo_id:
            source = "БД" if user_photos and user_photos.get('photo_id') else "FSM (FALLBACK)"
            logger.info(f"   ✅ ОСНОВНОЕ ФОТО НАЙДЕНО (источник: {source})")
            logger.info(f"      {main_photo_id[:40]}...")
        else:
            logger.error(f"   ❌ ОСНОВНОЕ ФОТО НЕ НАЙДЕНО НИ В БД НИ В FSM")
        
        logger.info(f"\n✅ ОБРАЗЕЦ ФОТО: {sample_photo_id[:40]}...")
        logger.info(f"═" * 80)
        
        if not main_photo_id:
            logger.error("❌ Основное фото не найдено в БД")
            await callback.answer(
                "❌ Ошибка: основное фото не найдено. Загрузите фото комнаты еще раз.",
                show_alert=True
            )
            return
        
        logger.info(f"\n✅ Оба фото найдены:")
        logger.info(f"   - Основное: {main_photo_id[:30]}...")
        logger.info(f"   - Образец: {sample_photo_id[:30]}...")
        
        # ⏳ ПОКАЗЫВАЕМ СООБЩЕНИЕ О ГЕНЕРАЦИИ
        await callback.answer("⏳ Подождите... генерируем примерку", show_alert=False)
        
        # 🔄 РЕДАКТИРУЕМ МЕНЮ НА "ГЕНЕРИРУЮ"
        menu_message_id = data.get('menu_message_id')
        if menu_message_id:
            try:
                await callback.message.edit_text(
                    text="⏳ *Генерируем примерку дизайна...*\n\nЭто может занять до 2 минут.",
                    parse_mode="Markdown",
                    reply_markup=None
                )
                logger.info(f"📝 Обновлено меню на SCREEN 11 (генерация)")
            except TelegramBadRequest as e:
                logger.debug(f"⚠️ Не удалось отредактировать: {e}")
        
        # 🎨 ЗАПУСКАЕМ ГЕНЕРАЦИЮ
        logger.info(f"🚀 Запускаем apply_style_to_room()...")
        result_url = await apply_style_to_room(
            main_photo_file_id=main_photo_id,
            sample_photo_file_id=sample_photo_id,
            bot_token=config.BOT_TOKEN
        )
        
        if not result_url:
            logger.error("❌ Генерация провалилась")
            error_text = "❌ Ошибка генерации. Пожалуйста, попробуйте еще раз."
            try:
                await callback.message.edit_text(
                    text=error_text,
                    reply_markup=get_generation_try_on_keyboard()
                )
            except TelegramBadRequest:
                await callback.message.answer(text=error_text)
            return
        
        # ✅ ГЕНЕРАЦИЯ УСПЕШНА
        logger.info(f"✅ Результат примерки готов: {result_url[:50]}...")
        log_photo_send(user_id, "answer_photo", 0, request_id, "apply_style_to_room")
        
        # ПЕРЕХОД НА SCREEN 12: post_generation_sample
        await state.set_state(CreationStates.post_generation_sample)
        await state.update_data(last_generated_image_url=result_url)
        
        # 🔧 [2026-01-03 19:40] КРИТИЧНО FIX:
        # Отправляем ТОЛЬКО ФОТО (БЕЗ КНОПОК)
        photo_caption = (
            "✨ *Примерка готова!*\n\n"
            "Дизайн применен к вашей комнате с сохранением мебели и макета."
        )
        
        # Удаляем меню генерации
        if menu_message_id:
            try:
                await callback.message.delete()
                logger.info(f"🗑️ Удалено меню генерации")
            except TelegramBadRequest:
                logger.debug("⚠️ Не удалось удалить меню")
        
        # ОТПРАВЛЯЕМ ФОТО БЕЗ КНОПОК
        photo_msg = await callback.message.answer_photo(
            photo=result_url,
            caption=photo_caption,
            parse_mode="Markdown"
        )
        logger.info(f"📸 [SCREEN 12] Фото примерки отправлено (msg_id={photo_msg.message_id})")
        log_photo_send(user_id, "answer_photo", photo_msg.message_id, request_id, "apply_style_to_room_success")
        
        await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation_sample_photo')
        
        # 🔧 [2026-01-03 19:40] ОТПРАВЛЯЕМ ОТДЕЛЬНОЕ МЕНЮ СООБЩЕНИЕ С КНОПКАМИ
        # Как в creation_new_design.py - это предотвращает удаление при перезагрузке
        data = await state.get_data()
        work_mode = data.get('work_mode', 'sample_design')
        balance = await db.get_balance(user_id)
        
        menu_text = (
            f"🎨 *Примерка дизайна готова!*\n\n"
            f"Выберите действие:\n"
            f"🔄 Загрузить новый образец\n"
            f"🏠 Вернуться в меню\n\n"
            f"📊 Баланс: *{balance}* генераций | 🔧 Режим: *{work_mode}*"
        )
        
        menu_msg = await callback.message.answer(
            text=menu_text,
            reply_markup=get_post_generation_sample_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"📝 [SCREEN 12] Меню с кнопками отправлено (msg_id={menu_msg.message_id})")
        
        await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_sample_menu')
        await state.update_data(
            photo_message_id=photo_msg.message_id,
            menu_message_id=menu_msg.message_id
        )
        
        logger.info(f"✅ [SCREEN 11→12] COMPLETED - примерка готова с отдельным меню")
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 11 кнопка failed: {e}", exc_info=True)
        await callback.answer(
            f"❌ Ошибка. Попробуйте еще раз: {str(e)[:50]}",
            show_alert=True
        )


async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int):
    """Удалить сообщение через N секунд"""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"✅ Удалено сообщение {message_id}")
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить: {e}")
