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
from utils.texts import GENERATION_TRY_ON_TEXT

logger = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 10] ЗАГРУЗКА ОБРАЗЦА
# 🔧 [2026-01-03] ОБРАБОТЧИК ГОГОУПЛОАДКИ ОБРАЗЦА
# ⚠️ [В creation_main.py] НО ЕДИНОЕ МЕСТО!
# ══════════════════════════════════════════════════════════════════════════════

# 🔧 [2026-01-03] ОБРАБОТЧИК ОТПРАВКИ ФОТО УДАЛЕН!
# 
# ПОЧЕМУ:
# - Обоработчик уже есть в creation_main.py
# - При двух обоработчиках возникает конфликт:
# - Оба ловят цём цел на SCREEN 10 (@router.message(..., F.photo))
# - Может цел обработана дважды или ни разу
#
# ПОПРАВКА:
# - Принимать фото в creation_main.py
# - Переводить на SCREEN 11 в creation_main.py
# - РТИ файле (creation_sample_design.py) - нужны только картинки


# ══════════════════════════════════════════════════════════════════════════════
# 🎁 [SCREEN 11] КНОПКА: "🎨 Примерить дизайн"
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
    - ТЕКСТ из texts.py: GENERATION_TRY_ON_TEXT
    - КЛАВИАТУРА из inline.py: get_generation_try_on_keyboard()
    - TODO: Ореализовать генерацию примерки
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        logger.info(f"🎁 [SCREEN 11] КНОПКА НАЖАТА: user_id={user_id}")
        logger.warning(f"TODO: Ореализовать генерацию примерки дизайна (дальнейшая работа)")
        
        await callback.answer("⏳ Подождите... генерируем примерку", show_alert=False)

    except Exception as e:
        logger.error(f"[ERROR] SCREEN 11 кнопка failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте ещё раз.", show_alert=True)
