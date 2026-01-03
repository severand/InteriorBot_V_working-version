import logging
import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from keyboards.inline import get_generation_try_on_keyboard
from states.fsm import CreationStates
from utils.helpers import add_balance_and_mode_to_text
from utils.texts import GENERATION_TRY_ON_TEXT  # 🔧 [2026-01-03] НОВОЕ

logger = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 10→11] ГЕНЕРАЦИЯ ПРИМЕРКИ
# 🔧 [2026-01-03] ОТДЕЛЬНЫЙ ФАЙЛ ДЛЯ ОБРАБОТЧИКА generate_try_on
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(
    StateFilter(CreationStates.download_sample),
    F.data == "generate_try_on"
)
async def generate_try_on_handler(callback: CallbackQuery, state: FSMContext):
    """
    🎁 [SCREEN 10→11] Обработчик генерации примерки

    📍 ПУТЬ: [SCREEN 10: download_sample] → "🎨 Примерить дизайн" → [SCREEN 11: generation_try_on]

    🔧 [2026-01-03] ОСНОВНОЕ:
    - ТЕКСТ из texts.py: GENERATION_TRY_ON_TEXT
    - КЛАВИАТУРА из inline.py: get_generation_try_on_keyboard()
    - РЕДАКТИРУЕМ текущее сообщение

    📋 АЛГОРИТМ:
    1️⃣ Получаем данные из FSM
    2️⃣ Переходим в состояние generation_try_on
    3️⃣ Получаем текст с балансом и режимом
    4️⃣ РЕДАКТИРУЕМ текущее сообщение
    5️⃣ Сохраняем menu_message_id в БД
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        logger.info(f"🎁 [SCREEN 10→11] START: user_id={user_id}")

        data = await state.get_data()
        work_mode = data.get('work_mode')

        # ✅ Переходим на SCREEN 11
        await state.set_state(CreationStates.generation_try_on)

        # 📝 Получаем текст из texts.py и добавляем баланс/режим
        balance_text = await add_balance_and_mode_to_text(
            GENERATION_TRY_ON_TEXT,
            user_id,
            work_mode='sample_design'
        )

        # 📝 РЕДАКТИРУЕМ текущее сообщение (не создаём новое!)
        await callback.message.edit_text(
            text=balance_text,
            reply_markup=get_generation_try_on_keyboard(),
            parse_mode="Markdown"
        )

        # 📋 Сохраняем в БД (message_id остается прежним)
        await db.save_chat_menu(
            chat_id,
            user_id,
            callback.message.message_id,
            'generation_try_on'
        )
        await state.update_data(menu_message_id=callback.message.message_id)

        logger.info(f"✅ [SCREEN 10→11] Menu EDITED: msg_id={callback.message.message_id}")
        logger.info(f"🎁 [SCREEN 10→11] COMPLETED: user_id={user_id}")

        await callback.answer()

    except Exception as e:
        logger.error(f"[ERROR] SCREEN 10→11 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при переходе на примерку. Попробуйте ещё раз.", show_alert=True)
