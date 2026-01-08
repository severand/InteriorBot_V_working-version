"""Безопасная отправка Telegram сообщений с логированием и таймаутом.

Дата создания: 2026-01-09
Цель: Кроссплатформная защита от зависаний на Windows (семафор aiogram)
"""

import sys
import asyncio
import logging
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def send_menu_safe(
    callback: CallbackQuery,
    text: str,
    keyboard: InlineKeyboardMarkup,
    parse_mode: str = "HTML",
    timeout: float = 10.0
) -> Optional[Message]:
    """
    Безопасно отправляет меню с кроссплатформной защитой от зависаний.
    
    На Windows добавляет asyncio.wait_for() для защиты от зависаний семафора.
    На Linux/Mac работает обычным способом (без излишних таймаутов).
    
    Args:
        callback: CallbackQuery от пользователя
        text: Текст меню
        keyboard: Инлайн-клавиатура
        parse_mode: HTML или Markdown
        timeout: Таймаут в секундах (только Windows)
    
    Returns:
        Message если успешно, None если timeout/ошибка
    
    Пример:
        menu_msg = await send_menu_safe(
            callback,
            "🎨 Меню",
            get_post_generation_keyboard()
        )
        if menu_msg:
            await state.update_data(menu_message_id=menu_msg.message_id)
    """
    try:
        menu_task = callback.message.answer(
            text=text,
            parse_mode=parse_mode,
            reply_markup=keyboard
        )
        
        # На Windows семафор aiogram может зависнуть на 30+ секунд
        # Используем asyncio.wait_for() для принудительного прерывания
        if sys.platform == 'win32':
            try:
                logger.warning(
                    f"📊 [WIN32] Sending menu with {timeout}s timeout... "
                    f"(user_id={callback.from_user.id}, chat_id={callback.message.chat.id})"
                )
                
                menu_msg = await asyncio.wait_for(menu_task, timeout=timeout)
                
                logger.warning(
                    f"✅ [WIN32] Menu sent successfully "
                    f"(msg_id={menu_msg.message_id}, user_id={callback.from_user.id})"
                )
                return menu_msg
                
            except asyncio.TimeoutError:
                logger.warning(
                    f"⚠️ [WIN32] Menu send TIMEOUT after {timeout}s "
                    f"(user_id={callback.from_user.id}) - continuing anyway, "
                    f"user will see message in a moment"
                )
                return None
                
        else:
            # На Linux/Mac обычный await без таймаута
            logger.warning(
                f"📊 [POSIX] Sending menu normally... "
                f"(platform={sys.platform}, user_id={callback.from_user.id})"
            )
            
            menu_msg = await menu_task
            
            logger.warning(
                f"✅ [POSIX] Menu sent successfully "
                f"(msg_id={menu_msg.message_id}, user_id={callback.from_user.id})"
            )
            return menu_msg
            
    except asyncio.TimeoutError:
        # Если даже таймаут сработал на других платформах
        logger.error(
            f"❌ [TIMEOUT] Menu send timeout "
            f"(platform={sys.platform}, user_id={callback.from_user.id})"
        )
        return None
        
    except Exception as e:
        # Ловим все остальные ошибки
        logger.error(
            f"❌ [ERROR] Menu send failed: {type(e).__name__}: {e} "
            f"(platform={sys.platform}, user_id={callback.from_user.id})",
            exc_info=True
        )
        return None


async def edit_menu_safe(
    callback: CallbackQuery,
    text: str,
    keyboard: InlineKeyboardMarkup,
    parse_mode: str = "Markdown"
) -> bool:
    """
    Безопасно редактирует существующее меню.
    
    Args:
        callback: CallbackQuery от пользователя
        text: Новый текст меню
        keyboard: Новая клавиатура
        parse_mode: HTML или Markdown
    
    Returns:
        True если успешно, False если ошибка
    
    Пример:
        success = await edit_menu_safe(
            callback,
            "🎨 Новое меню",
            get_choose_style_keyboard()
        )
        if not success:
            logger.error("Failed to edit menu")
    """
    try:
        logger.warning(
            f"📝 [EDIT_MENU] Editing menu "
            f"(msg_id={callback.message.message_id}, user_id={callback.from_user.id})"
        )
        
        await callback.message.edit_text(
            text=text,
            parse_mode=parse_mode,
            reply_markup=keyboard
        )
        
        logger.warning(
            f"✅ [EDIT_MENU] Menu edited successfully "
            f"(msg_id={callback.message.message_id}, user_id={callback.from_user.id})"
        )
        return True
        
    except Exception as e:
        logger.error(
            f"❌ [EDIT_MENU_ERROR] Failed to edit menu: {type(e).__name__}: {e} "
            f"(msg_id={callback.message.message_id}, user_id={callback.from_user.id})",
            exc_info=True
        )
        return False
