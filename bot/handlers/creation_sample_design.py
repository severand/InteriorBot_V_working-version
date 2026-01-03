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

    🔧 [2026-01-03] НОВОЕ:
    - Удаляет СТАРОЕ текстовое сообщение из БД перед переходом
    - Отправляет НОВОЕ меню на экран 11
    - Сохраняет menu_message_id в FSM для дальнейших переходов

    📋 АЛГОРИТМ:
    1️⃣ Получаем данные из FSM (work_mode, photo_id)
    2️⃣ Получаем старый menu_message_id из БД
    3️⃣ УДАЛЯЕМ старое текстовое сообщение
    4️⃣ Переходим в состояние generation_try_on
    5️⃣ Отправляем НОВОЕ меню с клавиатурой экрана 11
    6️⃣ Сохраняем new menu_message_id в БД и FSM
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    try:
        logger.info(f"🎁 [SCREEN 10→11] START: user_id={user_id}")

        data = await state.get_data()
        work_mode = data.get('work_mode')

        # 🔧 КЛЮЧЕВОЕ: Получаем СТАРЫЙ menu_message_id ИЗ БД
        old_menu_data = await db.get_chat_menu(chat_id)
        old_menu_message_id = old_menu_data.get('menu_message_id') if old_menu_data else None

        logger.info(f"🎁 [SCREEN 10→11] old_menu_message_id={old_menu_message_id}")

        # 🗑️ УДАЛЯЕМ старое сообщение
        if old_menu_message_id:
            try:
                await callback.bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_menu_message_id
                )
                logger.info(f"🗑️ [SCREEN 10→11] Удалено старое текстовое сообщение #{old_menu_message_id}")
            except TelegramBadRequest as e:
                logger.warning(f"⚠️ [SCREEN 10→11] Не удалось удалить: {e}")
            except Exception as e:
                logger.error(f"❌ [SCREEN 10→11] Ошибка удаления: {e}")

        # ✅ Переходим на SCREEN 11
        await state.set_state(CreationStates.generation_try_on)

        # 📝 Текст экрана 11
        balance_text = await add_balance_and_mode_to_text(
            "🎨 **Примерить дизайн**\n\nКликните кнопку ниже для генерации примерки:",
            user_id,
            work_mode='sample_design'
        )

        # 📨 Отправляем НОВОЕ меню
        menu_msg = await callback.message.answer(
            text=balance_text,
            reply_markup=get_generation_try_on_keyboard(),
            parse_mode="Markdown"
        )

        # 📋 Сохраняем в БД и FSM
        await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'generation_try_on')
        await state.update_data(menu_message_id=menu_msg.message_id)

        logger.info(f"✅ [SCREEN 10→11] Menu sent: msg_id={menu_msg.message_id}")
        logger.info(f"🎁 [SCREEN 10→11] COMPLETED: user_id={user_id}")

        await callback.answer()

    except Exception as e:
        logger.error(f"[ERROR] SCREEN 10→11 failed: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при переходе на примерку. Попробуйте ещё раз.", show_alert=True)
