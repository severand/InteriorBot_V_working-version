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
from keyboards.inline import (
    get_generation_facade_keyboard,
    get_post_generation_facade_keyboard,
    get_loading_facade_sample_keyboard,
)
from states.fsm import CreationStates
from utils.helpers import add_balance_and_mode_to_text
from utils.texts import (
    GENERATION_FACADE_TEXT,
    LOADING_FACADE_SAMPLE_TEXT,
    SCREEN_16_PHOTO_FACADE,
)
from services.kie_api import apply_style_to_room
from config import config

logger = logging.getLogger(__name__)
router = Router()

PHOTO_SEND_LOG = {}
media_group_cache = {}


def log_photo_send(user_id: int, method: str, message_id: int, request_id: str = None, operation: str = ""):
    if user_id not in PHOTO_SEND_LOG:
        PHOTO_SEND_LOG[user_id] = []
    timestamp = datetime.now().isoformat()
    rid = request_id or str(uuid.uuid4())[:8]
    entry = {'timestamp': timestamp, 'method': method, 'message_id': message_id, 'request_id': rid, 'operation': operation}
    PHOTO_SEND_LOG[user_id].append(entry)
    logger.warning(f"📊 [PHOTO_LOG] user_id={user_id}, method={method}, msg_id={message_id}, request_id={rid}, operation={operation}, timestamp={timestamp}")


async def collect_all_media_group_photos(user_id: int, media_group_id: str, message_id: int):
    if user_id not in media_group_cache:
        media_group_cache[user_id] = {}
    if media_group_id not in media_group_cache[user_id]:
        media_group_cache[user_id][media_group_id] = {'message_ids': [message_id], 'collected': False}
        logger.info(f"📄 [COLLECT] user={user_id}, group={media_group_id}, photo #1")
        await asyncio.sleep(1.0)
        media_group_cache[user_id][media_group_id]['collected'] = True
        final_ids = media_group_cache[user_id][media_group_id]['message_ids'].copy()
        logger.info(f"📄 [COLLECT] DONE: {len(final_ids)} photos")
        return final_ids
    else:
        if not media_group_cache[user_id][media_group_id]['collected']:
            media_group_cache[user_id][media_group_id]['message_ids'].append(message_id)
            count = len(media_group_cache[user_id][media_group_id]['message_ids'])
            logger.info(f"📄 [COLLECT] photo #{count} added")
        return None


# ════════════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 16] ЗАГРУЗКА ОБРАЗЦА ФАСАДА
# ════════════════════════════════════════════════════════════════════════════════════

@router.message(StateFilter(CreationStates.loading_facade_sample), F.photo)
async def download_facade_photo_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    try:
        if message.media_group_id:
            logger.info(f"📄 [ALBUM] [SCREEN 16] media_group_id={message.media_group_id}")
            collected_ids = await collect_all_media_group_photos(user_id, message.media_group_id, message.message_id)
            if collected_ids:
                logger.warning(f"❌ [ALBUM] [SCREEN 16] {len(collected_ids)} фото детектировано! УДАЛЯЕМ!")
                delete_tasks = [message.bot.delete_message(chat_id=chat_id, message_id=msg_id) for msg_id in collected_ids]
                results = await asyncio.gather(*delete_tasks, return_exceptions=True)
                success_count = sum(1 for r in results if not isinstance(r, Exception))
                logger.info(f"🗑️ [ALBUM] [SCREEN 16] Удалено {success_count}/{len(collected_ids)} фото")
            return
        
        logger.info(f"📄 [SINGLE] [SCREEN 16] Одиночное фото образца фасада")
        data = await state.get_data()
        work_mode = data.get('work_mode')
        photo_id = message.photo[-1].file_id
        
        await state.update_data(facade_sample_photo_id=photo_id, session_started=False)
        logger.info(f"📄 [FSM] Образец фасада фото сохранено в FSM: {photo_id[:30]}...")
        await db.save_sample_photo(user_id, photo_id)
        logger.info(f"📄 [БД] Образец фасада фото сохранено")
        
        old_menu_data = await db.get_chat_menu(chat_id)
        old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None
        if old_menu_message_id:
            try:
                await message.bot.delete_message(chat_id=chat_id, message_id=old_menu_message_id)
                logger.info(f"🗑️ [SCREEN 16] Удалено старое меню (msg_id={old_menu_message_id})")
            except Exception as e:
                logger.debug(f"⚠️ Не удалось удалить: {e}")

        logger.info(f"🏠 [SCREEN 16] Отправляю образец фасада с сообщением")
        sample_msg = await message.answer_photo(photo=photo_id, caption=SCREEN_16_PHOTO_FACADE, parse_mode="Markdown")
        logger.info(f"🏠 [SCREEN 16] Образец фасада отправлено (msg_id={sample_msg.message_id})")
        
        try:
            await message.delete()
            logger.info(f"🗑️ [SCREEN 16] Удалено оригинальное фото юзера (msg_id={message.message_id})")
        except Exception as e:
            logger.debug(f"⚠️ Не удалось удалить фото юзера: {e}")

        await state.set_state(CreationStates.generation_facade)
        text = GENERATION_FACADE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
        keyboard = get_generation_facade_keyboard()
        logger.info(f"🏠 [SCREEN 16→17] Отправляю меню SCREEN 17 с кнопкой генерации")
        menu_msg = await message.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
        logger.info(f"✅ [SCREEN 16→17] Меню SCREEN 17 отправлено (msg_id={menu_msg.message_id})")
        await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'generation_facade')
        await state.update_data(menu_message_id=menu_msg.message_id)
        logger.info(f"📄 [SCREEN 16→17] COMPLETED - переход на generation_facade")
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 16 photo handler failed: {e}", exc_info=True)
        error_msg = await message.answer(f"❌ Ошибка при загрузке образца фасада: {str(e)[:50]}")
        await db.save_chat_menu(chat_id, user_id, error_msg.message_id, 'loading_facade_sample')
        asyncio.create_task(_delete_message_after_delay(message.bot, chat_id, error_msg.message_id, 3))


@router.callback_query(StateFilter(CreationStates.generation_facade), F.data == "loading_facade_sample")
async def back_to_facade_upload(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    try:
        await state.set_state(CreationStates.loading_facade_sample)
        text = LOADING_FACADE_SAMPLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
        keyboard = get_loading_facade_sample_keyboard()
        logger.info(f"⬅️ [SCREEN 17→16] НАЖАТА КНОПКА НАЗАД - возврат на SCREEN 16")
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'loading_facade_sample')
        logger.info(f"✅ [SCREEN 17→16] Меню SCREEN 16 доставлено")
        await callback.answer()
    except Exception as e:
        logger.error(f"[ERROR] back_to_facade_upload failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


@router.callback_query(StateFilter(CreationStates.post_generation_facade), F.data == "loading_facade_sample")
async def new_facade_from_screen_18(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    try:
        await state.set_state(CreationStates.loading_facade_sample)
        text = LOADING_FACADE_SAMPLE_TEXT
        text = await add_balance_and_mode_to_text(text, user_id, work_mode='facade_design')
        keyboard = get_loading_facade_sample_keyboard()
        logger.info(f"📸 [SCREEN 18→16] НАЖАТА КНОПКА 'НОВЫЙ ОБРАЗЕЦ' - возврат на SCREEN 16")
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'loading_facade_sample')
        logger.info(f"✅ [SCREEN 18→16] Меню SCREEN 16 доставлено")
        await callback.answer()
    except Exception as e:
        logger.error(f"[ERROR] new_facade_from_screen_18 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


@router.callback_query(StateFilter(CreationStates.post_generation_facade), F.data == "text_input")
async def text_input_from_screen_18(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    try:
        data = await state.get_data()
        last_generated_url = data.get('last_generated_facade_url')
        
        if not last_generated_url:
            logger.error(f"❌ [SCREEN 18] last_generated_facade_url not found in FSM")
            await callback.answer("❌ Ошибка: сгенерированное изображение не найдено.", show_alert=True)
            return
        
        logger.info(f"✏️ [SCREEN 18→7] НАЖАТА КНОПКА 'ТЕКСТОВОЕ РЕДАКТИРОВАНИЕ'")
        logger.info(f"   🔄 Загружаю фасад в Telegram, чтобы получить реальный file_id")
        
        uploaded_photo = await callback.message.answer_photo(
            photo=last_generated_url,
            caption="⏳ Подготавливаю к редактированию..."
        )
        
        real_photo_id = uploaded_photo.photo[-1].file_id
        logger.info(f"✅ [ДБ] Получен реальный file_id: {real_photo_id[:30]}...")
        
        await db.save_user_photo(user_id, real_photo_id)
        logger.info(f"✅ [ДБ] Сохранено сгенерированное фасад с реальным file_id")
        
        await state.update_data(
            photo_id=real_photo_id,
            menu_message_id=callback.message.message_id
        )
        logger.info(f"📝 [FSM] Обновлено: photo_id = {real_photo_id[:30]}...")
        
        await state.set_state(CreationStates.edit_design)
        
        from keyboards.inline import get_edit_design_keyboard
        
        edit_design_menu_text = """✏️ **Редактируем дизайн фасада**

Выберите действие:

🗑️ **Очистить фото** - удалить всю отделку

📝 **Текстовый редактор** - добавить описание для уточнения дизайна

Примеры описаний:
• "Добавить светлый сайдинг"
• "Теплые тона, классика"
• "Больше стекла и растений"
"""
        
        logger.info(f"📄 [SCREEN 18→8] Отправляю меню SCREEN 8")
        
        await uploaded_photo.delete()
        menu_msg = await callback.message.edit_text(
            text=edit_design_menu_text,
            reply_markup=get_edit_design_keyboard()
        )
        
        await state.update_data(menu_message_id=menu_msg.message_id)
        await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'edit_design')
        
        logger.info(f"✅ [SCREEN 18→8] COMPLETED - переход на SCREEN 8 выполнен")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[ERROR] text_input_from_screen_18 failed: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка: {str(e)[:50]}", show_alert=True)


# ════════════════════════════════════════════════════════════════════════════════════
# 🏠 [SCREEN 17] КНОПКА: "🎨 Оформить фасад"
# ════════════════════════════════════════════════════════════════════════════════════

@router.callback_query(StateFilter(CreationStates.generation_facade), F.data == "generate_facade")
async def generate_facade_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    request_id = str(uuid.uuid4())[:8]

    try:
        logger.info(f"🏠 [SCREEN 17] КНОПКА НАЖАТА: user_id={user_id}")
        logger.info(f"{'═' * 80}")
        logger.info(f"📊 [SCREEN 17] ДИАГНОСТИКА ЗАГРУЗКИ ФОТО")
        logger.info(f"{'═' * 80}")
        
        data = await state.get_data()
        facade_sample_photo_id = data.get('facade_sample_photo_id')
        
        logger.info(f"\n1️⃣  ОБРАЗЕЦ ФАСАДА (facade_sample_photo_id):")
        if facade_sample_photo_id:
            logger.info(f"   ✅ НАЙДЕН в FSM: {facade_sample_photo_id[:40]}...")
        else:
            logger.error(f"   ❌ НЕ НАЙДЕН в FSM")
        
        if not facade_sample_photo_id:
            logger.error("❌ Образец фасада не найден в FSM")
            await callback.answer("❌ Ошибка: образец фасада не найден. Загрузите образец еще раз.", show_alert=True)
            return
        
        logger.info(f"\n2️⃣  ОСНОВНОЕ ФОТО (main_photo_id):")
        logger.info(f"   🔍 Проверяю источники данных...")
        
        logger.info(f"   📋 ПОПЫТКА 1: Получаю из БД...")
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
        
        if not main_photo_id:
            logger.info(f"   📋 ПОПЫТКА 2: БД вернула пусто, беру из FSM (fallback)...")
            main_photo_id = data.get('photo_id')
            if main_photo_id:
                logger.info(f"   ✅ FSM: photo_id найден (FALLBACK): {main_photo_id[:40]}...")
            else:
                logger.error(f"   ❌ FSM: photo_id ОТСУТСТВУЕТ")
        else:
            logger.info(f"   ✅ ИСТОЧНИК: БД")
        
        logger.info(f"\n3️⃣  ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        if main_photo_id:
            source = "БД" if user_photos and user_photos.get('photo_id') else "FSM (FALLBACK)"
            logger.info(f"   ✅ ОСНОВНОЕ ФОТО НАЙДЕНО (источник: {source})")
            logger.info(f"      {main_photo_id[:40]}...")
        else:
            logger.error(f"   ❌ ОСНОВНОЕ ФОТО НЕ НАЙДЕНО")
        
        logger.info(f"\n✅ ОБРАЗЕЦ ФАСАДА: {facade_sample_photo_id[:40]}...")
        logger.info(f"{'═' * 80}")
        
        if not main_photo_id:
            await callback.answer("❌ Ошибка: основное фото не найдено. Загрузите фото еще раз.", show_alert=True)
            return
        
        logger.info(f"\n✅ Оба фото найдены:")
        logger.info(f"   - Основное: {main_photo_id[:30]}...")
        logger.info(f"   - Образец фасада: {facade_sample_photo_id[:30]}...")
        
        await callback.answer("⏳ Подождите... генерируем фасад", show_alert=False)
        
        progress_message_id = callback.message.message_id
        logger.info(f"🔧 [PROGRESS] Сохраняю ID прогресс-сообщения: {progress_message_id}")
        
        if progress_message_id:
            try:
                await callback.message.edit_text(
                    text="⏳ *Генерирую дизайн фасада...*\n\nЭто может занять до 2 минут.",
                    parse_mode="Markdown",
                    reply_markup=None
                )
                logger.info(f"📝 Обновлено меню на SCREEN 17 (генерация)")
            except TelegramBadRequest as e:
                logger.debug(f"⚠️ Не удалось отредактировать: {e}")
        
        logger.info(f"🚀 Запускаем apply_style_to_room()...")
        result_url = await apply_style_to_room(
            main_photo_file_id=main_photo_id,
            sample_photo_file_id=facade_sample_photo_id,
            bot_token=config.BOT_TOKEN
        )
        
        if not result_url:
            logger.error("❌ Генерация провалилась")
            error_text = "❌ Ошибка генерации. Пожалуйста, попробуйте еще раз."
            try:
                await callback.message.edit_text(
                    text=error_text,
                    reply_markup=get_generation_facade_keyboard()
                )
            except TelegramBadRequest:
                await callback.message.answer(text=error_text)
            return
        
        logger.info(f"✅ Результат генерации фасада готов: {result_url[:50]}...")
        log_photo_send(user_id, "answer_photo", 0, request_id, "apply_style_to_room")
        
        if progress_message_id:
            try:
                await callback.bot.delete_message(chat_id=chat_id, message_id=progress_message_id)
                logger.info(f"🗑️ [PROGRESS] Удалено прогресс-сообщение (msg_id={progress_message_id})")
            except TelegramBadRequest as e:
                logger.warning(f"⚠️ [PROGRESS] Не удалось удалить прогресс: {e}")
                try:
                    await callback.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_message_id,
                        text="✅ *Генерация фасада готова!*"
                    )
                    logger.info(f"📝 [PROGRESS] Отредактировано вместо удаления")
                except Exception as e2:
                    logger.debug(f"⚠️ [PROGRESS] Fallback не сработал: {e2}")
        
        photo_caption = ("✨ *Дизайн фасада готов!*\n\nФасад оформлен с учетом вашего выбора.")
        photo_msg = await callback.message.answer_photo(photo=result_url, caption=photo_caption, parse_mode="Markdown")
        logger.info(f"📸 [SCREEN 18] ФОТО фасада отправлено (msg_id={photo_msg.message_id})")
        log_photo_send(user_id, "answer_photo", photo_msg.message_id, request_id, "apply_style_to_room_success")
        
        data = await state.get_data()
        work_mode = data.get('work_mode', 'facade_design')
        balance = await db.get_balance(user_id)
        
        menu_text = (f"🏠 *Дизайн фасада готов!*\n\nВыберите действие:\n✏️ Редактировать текстом\n📸 Загрузить новый образец\n🏠 Вернуться в меню\n\n💰 Баланс: *{balance}* генераций")
        menu_msg = await callback.message.answer(text=menu_text, reply_markup=get_post_generation_facade_keyboard(), parse_mode="Markdown")
        logger.info(f"📝 [SCREEN 18] МЕНЮ отправлено (msg_id={menu_msg.message_id})")
        
        await state.update_data(
            photo_message_id=photo_msg.message_id,
            menu_message_id=menu_msg.message_id,
            last_generated_facade_url=result_url
        )
        
        await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation_facade_photo')
        logger.info(f"💾 [ДБ] Сохранено ФОТО: msg_id={photo_msg.message_id}")
        
        await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_facade')
        logger.info(f"💾 [ДБ] Сохранено МЕНЮ: msg_id={menu_msg.message_id}")
        
        await state.set_state(CreationStates.post_generation_facade)
        
        logger.info(f"✅ [SCREEN 17→18] COMPLETED!")
        logger.info(f"   ✅ ПРОГРЕСС: удалено (msg_id={progress_message_id})")
        logger.info(f"   ✅ ФОТО: msg_id={photo_msg.message_id}")
        logger.info(f"   ✅ МЕНЮ: msg_id={menu_msg.message_id}")
        logger.info(f"   ✅ ОБЕ ID сохранены в FSM & ДБ")
        
    except Exception as e:
        logger.error(f"[ERROR] SCREEN 17 кнопка failed: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка. Попробуйте еще раз: {str(e)[:50]}", show_alert=True)


async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"✅ Удалено сообщение {message_id}")
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить: {e}")
