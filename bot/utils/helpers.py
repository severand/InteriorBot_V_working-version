# --- Обновлен: bot/utils/helpers.py ---
# [2025-12-03 19:32] Добавлена функция add_balance_to_text для автоматического отображения баланса
# [2025-12-24 12:44] Добавлена функция add_balance_and_mode_to_text для header с режимом

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


# ===== ФУНКЦИЯ ДЛЯ ОТОБРАЖЕНИЯ БАЛАНСА =====

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


# ===== НОВАЯ ФУНКЦИЯ ДЛЯ HEADER С РЕЖИМОМ =====

async def add_balance_and_mode_to_text(text: str, user_id: int) -> str:
    """
    Добавляет header с информацией о балансе и текущем режиме в начало текста.
    
    Header формат:
    ⚡ Баланс: 15 | Режим: 📋 СТАНДАРТ
    ────────────────────────────────────

    Args:
        text: Исходный текст сообщения
        user_id: ID пользователя

    Returns:
        Текст с добавленным header'ом
        
    Raises:
        Exception: Логируется и возвращается исходный текст
        
    Example:
        >>> result = await add_balance_and_mode_to_text(
        ...     "Выбери стиль дизайна:",
        ...     user_id=123
        ... )
        >>> print(result)
        ⚡ Баланс: 15 | Режим: 🔧 PRO
        ────────────────────────────────────
        
        Выбери стиль дизайна:
    """
    try:
        # Получаем баланс и настройки режима
        balance = await db.get_balance(user_id)
        pro_settings = await db.get_user_pro_settings(user_id)
        
        # Определяем иконку и название режима
        is_pro = pro_settings.get('pro_mode', False)
        mode_icon = "🔧" if is_pro else "📋"
        mode_name = "PRO" if is_pro else "СТАНДАРТ"
        
        # Формируем header
        separator = "─" * 36
        header = f"⚡ Баланс: {balance} | Режим: {mode_icon} {mode_name}\n{separator}\n\n"
        
        logger.debug(f"Header сформирован для user {user_id}: {mode_name} mode, balance {balance}")
        
        return header + text
        
    except Exception as e:
        logger.error(f"Ошибка формирования header для user {user_id}: {e}")
        # Возвращаем исходный текст без header'а если ошибка
        return text
