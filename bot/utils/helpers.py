# --- Обновлен: bot/utils/helpers.py ---
# [2025-12-03 19:32] Добавлена функция add_balance_to_text для автоматического отображения баланса
# [2025-12-24 12:44] Добавлена функция add_balance_and_mode_to_text для footer с режимом
# [2025-12-24 21:38] ИСПРАВЛЕНА: header должен быть ВНИЗУ, emoji без квадратиков
# [2025-12-24 21:56] ИСПРАВЛЕНА: убрана проблема с квадратиками - используются Unicode escape для emoji
# [2025-12-24 22:01] ОПТИМИЗИРОВАНА: линия сокращена с 36 на 18 символов для мобильной версии

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
        Текст с добавленным балансом в конце
    """
    try:
        balance = await db.get_balance(user_id)
        balance_footer = f"\n\n{'─' * 36}\nБаланс генераций: {balance}"
        return text + balance_footer
    except Exception as e:
        logger.error(f"Ошибка получения баланса для {user_id}: {e}")
        return text


# ===== НОВАЯ ИСПРАВЛЕННАЯ ФУНКЦИЯ ДЛЯ FOOTER С РЕЖИМОМ И БАЛАНСОМ =====

async def add_balance_and_mode_to_text(text: str, user_id: int) -> str:
    """
    Добавляет footer с информацией о балансе и текущем режиме В КОНЕЦ текста.
    
    Footer формат (в конце текста):
    ──────────────────
    Баланс: 15 | Режим: PRO
    
    [2025-12-24 22:01] ОПТИМИЗИРОВАНО:
    - Линия сокращена с 36 на 18 символов (в два раза короче)
    - Теперь всегда вмещается в одну строку на мобильном
    - Работает корректно как для "PRO" так и для "СТАНДАРТ"

    Args:
        text: Исходный текст сообщения
        user_id: ID пользователя

    Returns:
        Текст с добавленным footer'ом в конце
        
    Raises:
        Exception: Логируется и возвращается исходный текст
        
    Example:
        >>> result = await add_balance_and_mode_to_text(
        ...     "Выбери стиль дизайна:",
        ...     user_id=123
        ... )
        >>> print(result)
        Выбери стиль дизайна:
        
        ──────────────────
        Баланс: 15 | Режим: PRO
    """
    try:
        # Получаем баланс и настройки режима
        balance = await db.get_balance(user_id)
        pro_settings = await db.get_user_pro_settings(user_id)
        
        # [2025-12-24 21:56] ИСПРАВЛЕНО: Используем Unicode escape-sequences вместо строковых emoji
        # Это предотвращает проблемы с квадратиками в Telegram
        is_pro = pro_settings.get('pro_mode', False)
        mode_icon = "\ud83d\udd27" if is_pro else "\ud83d\udccb"  # ✅ Unicode escapes!
        # \ud83d\udd27 = 🔧 (wrench для PRO)
        # \ud83d\udccb = 📋 (clipboard для СТАНДАРТ)
        mode_name = "PRO" if is_pro else "СТАНДАРТ"
        
        # [2025-12-24 22:01] ОПТИМИЗИРОВАНО: линия в два раза короче для мобильной версии!
        # Была: separator = "─" * 36 (занимала 2+ строки на мобильном)
        # Теперь: separator = "─" * 18 (всегда в одну строку)
        separator = "─" * 18  # ✅ В ДВА РАЗА КОРОЧЕ!
        footer = f"\n\n{separator}\nБаланс: {balance} | Режим: {mode_icon} {mode_name}"
        
        logger.debug(f"Footer сформирован для user {user_id}: {mode_name} mode, balance {balance}, separator={len(separator)}chars")
        
        return text + footer
        
    except Exception as e:
        logger.error(f"Ошибка формирования footer для user {user_id}: {e}")
        # Возвращаем исходный текст без footer'а если ошибка
        return text
