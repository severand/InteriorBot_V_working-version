import logging
import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from keyboards.inline import get_generation_try_on_keyboard
from states.fsm import CreationStates
from utils.helpers import add_balance_and_mode_to_text
from utils.texts import GENERATION_TRY_ON_TEXT, DOWNLOAD_SAMPLE_TEXT

logger = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 10] ЗАГРУЗКА ОБРАЗЦА
# 🔧 [2026-01-03] ОБРАБОТЧИК ГОГОУПЛОАДКИ ОБРАЗЦА
# ══════════════════════════════════════════════════════════════════════════════

@router.message(
    StateFilter(CreationStates.download_sample),
    F.photo
)
async def download_sample_photo_handler(message: Message, state: FSMContext):
    """
    🎁 [SCREEN 10→11] Обработчик готового фото образца

    📍 ПУТЬ: [SCREEN 10: download_sample] → Отправляет фото → [SCREEN 11: generation_try_on]

    🔧 [2026-01-03] ОСНОВНОЕ:
    - Отнимает фото образца (текущее сообщение УДАЛЯЕТСЯ)
    - Отправляет НОВОЕ сообщение SCREEN 11
    - Фото сохраняется в FSM

    📋 АЛГОРИТМ:
    1️⃣ Получаем новое фото образца (file_id)
    2️⃣ Оставляем в FSM (photo_sample_design_id)
    3️⃣ ОТУЛЯЕМ старое сообщение SCREEN 10 (АЛЮМ тип)
    4️⃣ ОТПРАВЛЯЕМ НОВОЕ сообщение с SCREEN 11
    5️⃣ Переходим в состояние generation_try_on
    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        logger.info(f"🎁 [SCREEN 10→11] START: user_id={user_id}, photo received")

        data = await state.get_data()
        work_mode = data.get('work_mode')
        menu_message_id = data.get('menu_message_id')

        # 📷 Сохраняем file_id образца в FSM
        photo_file_id = message.photo[-1].file_id
        await state.update_data(photo_sample_design_id=photo_file_id)

        # ✅ ОтУЛЯЕМ старое сообщение SCREEN 10
        if menu_message_id:
            try:
                await message.bot.delete_message(chat_id, menu_message_id)
                logger.info(f"📡 ОтУЛЯто старое сообщение (msg_id={menu_message_id})")
            except TelegramBadRequest as e:
                logger.warning(f"⚠️ Не удалось удалить старое: {e}")

        # ✅ Переходим на SCREEN 11
        await state.set_state(CreationStates.generation_try_on)

        # 📝 Получаем текст из texts.py и добавляем баланс/режим
        balance_text = await add_balance_and_mode_to_text(
            GENERATION_TRY_ON_TEXT,
            user_id,
            work_mode='sample_design'
        )

        # 📝 ОТПРАВЛЯЕМ НОВОЕ сообщение с SCREEN 11
        new_message = await message.answer(
            text=balance_text,
            reply_markup=get_generation_try_on_keyboard(),
            parse_mode="Markdown"
        )

        # 📋 Сохраняем в БД
        await db.save_chat_menu(
            chat_id,
            user_id,
            new_message.message_id,
            'generation_try_on'
        )
        await state.update_data(menu_message_id=new_message.message_id)

        logger.info(f"✅ [SCREEN 10→11] Menu SENT: msg_id={new_message.message_id}")
        logger.info(f"🎁 [SCREEN 10→11] COMPLETED: user_id={user_id}")

    except Exception as e:
        logger.error(f"[ERROR] SCREEN 10→11 failed: {e}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке образца. Попробуйте ещё раз.")


# ══════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 11] НАЖАТО КНОПКУ "🎨 Примерить дизайн"
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.generation_try_on),
    F.data == "generate_try_on"
)
async def generate_try_on_handler(callback: CallbackQuery, state: FSMContext):
    """
    🎁 [SCREEN 11] КНОПКА: "🎨 Примерить дизайн"

    📍 ПУТЬ: [SCREEN 11: generation_try_on] → Кнопка → [Зает работать генерация]

    🔧 [2026-01-03] ОСНОВНОЕ:
    - Здесь будет логика генерации (сейчас TODO)
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        logger.info(f"🎁 [SCREEN 11] КНОПКА НАЖАТА: user_id={user_id}")
        logger.warning(f"TODO: Ореализовать генерацию примерки дизайна")
        
        await callback.answer("⏳ Подождите... генерируем примерку", show_alert=False)

    except Exception as e:
        logger.error(f"[ERROR] SCREEN 11 кнопка failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)
