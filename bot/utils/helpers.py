# --- Обновлен: bot/utils/helpers.py ---
# [2025-12-03 19:32] Добавлена функция add_balance_to_text для автоматического отображения баланса
# [2025-12-24 12:44] Добавлена функция add_balance_and_mode_to_text для footer с режимом
# [2025-12-24 21:38] ИСПРАВЛЕНА: header должен быть ВНИЗУ, emoji без квадратиков
# [2025-12-24 21:56] ИСПРАВЛЕНА: убрана проблема с квадратиками - используются Unicode escape для emoji
# [2025-12-24 22:01] ОПТИМИЗИРОВАНА: линия сокращена с 36 на 18 символов для мобильной версии
# [2025-12-27 09:41] КРИТИЧНО ИСПРАВЛЕНО: Surrogate characters заменены на правильные Unicode escapes (U+1F527, U+1F4CB)
# [2025-12-30 01:26] 🔥 CRITICAL FIX: Добавлен 3-й аргумент work_mode для отображения режима работы

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
# [2025-12-30 01:26] 🔥 CRITICAL FIX: Добавлен 3-й аргумент work_mode

async def add_balance_and_mode_to_text(
    text: str, 
    user_id: int, 
    work_mode: str = None
) -> str:
    """
    Добавляет footer с информацией о балансе, режиме генерации и режиме работы В КОНЕЦ текста.
    
    Footer формат (в конце текста):
    ──────────────────
    Баланс: 15 | Режим: 🔧 PRO | Работа: 📋 Новый дизайн
    
    [2025-12-30 01:26] 🔥 CRITICAL FIX:
    - Добавлен 3-й аргумент work_mode (опциональный)
    - Теперь показывает: Баланс + Режим генерации (PRO/СТАНДАРТ) + Режим работы (NEW_DESIGN/EDIT_DESIGN/...)
    - Режимы работы:
      * new_design → 📋 Новый дизайн
      * edit_design → ✏️ Редактирование
      * sample_design → 🎁 Примерить
      * arrange_furniture → 🛋️ Мебель
      * facade_design → 🏠 Фасад

    Args:
        text: Исходный текст сообщения
        user_id: ID пользователя
        work_mode: Режим работы (new_design, edit_design, и т.д.) - опционально

    Returns:
        Текст с добавленным footer'ом в конце
        
    Raises:
        Exception: Логируется и возвращается исходный текст
        
    Example:
        >>> result = await add_balance_and_mode_to_text(
        ...     "Выбери стиль дизайна:",
        ...     user_id=123,
        ...     work_mode="new_design"
        ... )
        >>> print(result)
        Выбери стиль дизайна:
        
        ──────────────────
        Баланс: 15 | Режим: 🔧 PRO | Работа: 📋 Новый дизайн
    """
    try:
        # Получаем баланс и настройки режима генерации
        balance = await db.get_balance(user_id)
        pro_settings = await db.get_user_pro_settings(user_id)
        
        # Режим генерации (PRO/СТАНДАРТ)
        is_pro = pro_settings.get('pro_mode', False)
        mode_icon = "\U0001f527" if is_pro else "\U0001f4cb"  # 🔧 PRO / 📋 СТАНДАРТ
        mode_name = "PRO" if is_pro else "СТАНДАРТ"
        
        # ✅ НОВОЕ: Режим работы (NEW_DESIGN, EDIT_DESIGN, и т.д.)
        work_mode_text = ""
        if work_mode:
            work_mode_map = {
                "new_design": "\U0001f4cb \u041d\u043e\u0432\u044b\u0439 \u0434\u0438\u0437\u0430\u0439\u043d",  # 📋
                "edit_design": "\u270f\ufe0f \u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435",  # ✏️
                "sample_design": "\U0001f381 \u041f\u0440\u0438\u043c\u0435\u0440\u0438\u0442\u044c",  # 🎁
                "arrange_furniture": "\U0001f6cb\ufe0f \u041c\u0435\u0431\u0435\u043b\u044c",  # 🛋️
                "facade_design": "\U0001f3e0 \u0424\u0430\u0441\u0430\u0434",  # 🏠
            }
            work_mode_display = work_mode_map.get(work_mode, work_mode)
            work_mode_text = f" | \u0420\u0430\u0431\u043e\u0442\u0430: {work_mode_display}"
        
        # Формируем footer
        separator = "─" * 18
        footer = f"\n\n{separator}\n\u0411\u0430\u043b\u0430\u043d\u0441: {balance} | \u0420\u0435\u0436\u0438\u043c: {mode_icon} {mode_name}{work_mode_text}"
        
        logger.debug(
            f"Footer \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d \u0434\u043b\u044f user {user_id}: "
            f"{mode_name} mode, balance {balance}, work_mode={work_mode}"
        )
        
        return text + footer
        
    except Exception as e:
        logger.error(f"Ошибка формирования footer для user {user_id}: {e}")
        # Возвращаем исходный текст без footer'а если ошибка
        return text
