import logging
import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from keyboards.inline import get_generation_try_on_keyboard
from states.fsm import CreationStates, WorkMode
from utils.helpers import add_balance_and_mode_to_text
from utils.texts import GENERATION_TRY_ON_TEXT

logger = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 10] ЗАГРУЗКА ОБРАЗЦА ФОТО (SAMPLE_DESIGN)
# 🔧 [2026-01-03] ДОБАВЛЕН ОБРАБОТЧИК ДЛЯ ЗАГРУЗКИ ВТОРОГО ФОТО!
# ══════════════════════════════════════════════════════════════════════════════

@router.message(StateFilter(CreationStates.download_sample), F.photo)
async def download_sample_photo_handler(message: Message, state: FSMContext):
    """
    🎁 [SCREEN 10] Обработка загрузки образца фото (второе фото)
    
    📍 ПУТЬ: [SCREEN 10: download_sample] → загружка фото образца → [SCREEN 11: generation_try_on]
    
    🔧 [2026-01-03] ИСПРАВЛЕНИЕ:
    - Добавлен обработчик для загрузки образца в состояние download_sample
    - После загрузки → переход на SCREEN 11 с кнопкой "🎨 Примерить дизайн"
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    try:
        logger.info(f"🎁 [SCREEN 10] Загруженный образец фото")
        
        data = await state.get_data()
        work_mode = data.get('work_mode')
        photo_id = message.photo[-1].file_id
        
        # 🎯 Сохраняем photo_id образца в FSM (второе фото для примерки)
        await state.update_data(
            sample_photo_id=photo_id,  # ОБРАЗЕЦ фото
            session_started=False
        )
        
        logger.info(f"🎁 [SCREEN 10] Образец фото сохранено в FSM: {photo_id[:30]}...")
        
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


# ═════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 11] КНОПКА: "🎨 Примерить дизайн"
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.generation_try_on),
    F.data == "generate_try_on"
)
async def generate_try_on_handler(callback: CallbackQuery, state: FSMContext):
    """
    🎁 [SCREEN 11] КНОПКА: "🎨 Примерить дизайн"

    📍 ПУТЬ: [SCREEN 11: generation_try_on] → Кнопка → [Запуск генерации]

    🔧 [2026-01-03] ОСНОВНОЕ:
    - ТЕКСТ из texts.py: GENERATION_TRY_ON_TEXT
    - КЛАВИАТУРА из inline.py: get_generation_try_on_keyboard()
    - TODO: Реализовать генерацию примерки
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        logger.info(f"🎁 [SCREEN 11] КНОПКА НАЖАТА: user_id={user_id}")
        logger.warning(f"TODO: Реализовать генерацию примерки дизайна (дальнейшая работа)")
        
        await callback.answer("⏳ Подождите... генерируем примерку", show_alert=False)

    except Exception as e:
        logger.error(f"[ERROR] SCREEN 11 кнопка failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)


async def _delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int):
    """Удалить сообщение через N секунд"""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"✅ Удалено сообщение {message_id}")
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить: {e}")
