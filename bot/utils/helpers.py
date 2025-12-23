# --- Обновлен: bot/utils/helpers.py ---
# [2025-12-03 19:32] Добавлена функция add_balance_to_text для автоматического отображения баланса

import asyncio
import logging

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ParseMode

# Импорт для работы с балансом
from database.db import db

logger = logging.getLogger(__name__)

# Ключ для хранения ID Пина
NAV_MSG_ID_KEY = "navigation_message_id"


async def delete_message_after_delay(message: Message, delay: int = 3):
    """
    Удаляет сообщение через указанное количество секунд.
    """
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить временное сообщение (ID: {message.message_id}): {e}")


async def edit_nav_message(bot, chat_id, state: FSMContext, text: str, reply_markup=None):
    """
    Универсальная функция для редактирования навигационного сообщения (Пина).
    Возвращает True, если редактирование прошло успешно.
    """
    data = await state.get_data()
    nav_msg_id = data.get(NAV_MSG_ID_KEY)

    if nav_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=nav_msg_id,
                text=text,
                reply_markup=reply_markup,  # Здесь может быть InlineKeyboardMarkup, если нужно
                parse_mode=ParseMode.MARKDOWN
            )
            return True
        except TelegramBadRequest as e:
            logger.warning(f"Ошибка редактирования Пина (ID:{nav_msg_id}): {e}")

    # Если редактирование не удалось, это должно быть исправлено в хэндлере,
    # который должен отправить новое сообщение и сохранить его ID.
    return False


# ===== НОВАЯ ФУНКЦИЯ ДЛЯ ОТОБРАЖЕНИЯ БАЛАНСА =====

async def add_balance_to_text(text: str, user_id: int) -> str:
    """
    Добавляет информацию о балансе генераций в конец текста.

    Args:
        text: Исходный текст сообщения
        user_id: ID пользователя

    Returns:
        Текст с добавленным балансом
    """
    try:
        balance = await db.get_balance(user_id)
        balance_text = f"\n\n{'─' * 20}\n💎 **Баланс генераций:** {balance}"
        return text + balance_text
    except Exception as e:
        logger.error(f"Ошибка получения баланса для {user_id}: {e}")
        return text