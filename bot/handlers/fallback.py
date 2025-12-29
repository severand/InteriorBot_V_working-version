# bot/handlers/fallback.py
"""
Глобальный обработчик устаревших callback после перезапуска бота.
КРИТИЧНО: Регистрируется ПОСЛЕДНИМ в main.py!

Дата создания: 2025-12-10
Обновлён: 2025-12-10 - Соответствие DEVELOPMENT_RULES.md
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from database.db import db

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data != "")
async def handle_all_stale_callbacks(callback: CallbackQuery, state: FSMContext):
    """
    ЛОВИТ ВСЕ необработанные callback_query.

    Срабатывает только если callback НЕ был обработан другими хендлерами.

    ПРИЧИНЫ:
    - Бот был перезапущен
    - FSM сброшен (данные потеряны)
    - Старое меню осталось в чате

    СООТВЕТСТВИЕ: DEVELOPMENT_RULES.md
    - Использует db.get_chat_menu() для получения menu_message_id
    - Использует state.set_state(None) вместо state.clear()
    - Сохраняет screen_code после редактирования
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    logger.warning(
        f"⚠️ STALE CALLBACK DETECTED:\n"
        f"   user={user_id}\n"
        f"   data='{callback.data}'\n"
        f"   msg_id={callback.message.message_id}\n"
        f"   text='{callback.message.text[:50]}...'"
    )

    # ✅ ПРАВИЛЬНО: Получаем menu_message_id из БД (НЕ из FSM!)
    menu_info = await db.get_chat_menu(chat_id)

    # ПРОВЕРКА: Это текущее меню из БД?
    if menu_info and menu_info['menu_message_id'] == callback.message.message_id:
        logger.info(f"🔄 Refreshing stale menu for user {user_id}")

        try:
            # ✅ ПРАВИЛЬНО: state.set_state(None) вместо state.clear()
            await state.set_state(None)

            # ✅ Получаем СВЕЖИЙ баланс из БД (не из кэша)
            balance = await db.get_balance(user_id)

            # Импортируем клавиатуру
            from keyboards.inline import get_main_menu_keyboard

            # ✅ Безопасное редактирование меню
            try:
                await callback.message.edit_text(
                    text=(
                        f"🎨 **ГЛАВНОЕ МЕНЮ**\n\n"
                        f"💎 Ваш баланс: **{balance}** генераций\n\n"
                        f"_Меню обновлено после перезапуска бота._\n\n"
                        "Выберите действие:"
                    ),
                    reply_markup=get_main_menu_keyboard(is_admin=False),
                    parse_mode="Markdown"
                )

                # ✅ КРИТИЧНО: Сохраняем screen_code в БД
                await db.save_chat_menu(
                    chat_id,
                    user_id,
                    callback.message.message_id,
                    'main_menu_refreshed'
                )

                # ✅ Сохраняем menu_message_id в FSM
                await state.update_data(menu_message_id=callback.message.message_id)

                await callback.answer(
                    "✅ Меню обновлено! Попробуйте снова.",
                    show_alert=False
                )

                await db.log_activity(user_id, 'stale_menu_auto_refreshed')

            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    # Текст не изменился - не ошибка
                    await callback.answer("Меню уже актуально")
                else:
                    logger.error(f"❌ Error editing stale menu: {e}")
                    await callback.answer(
                        "⚠️ Ошибка обновления.\nОтправьте /start",
                        show_alert=True
                    )

        except Exception as e:
            logger.error(f"❌ Critical error refreshing stale menu: {e}")
            await callback.answer(
                "⚠️ Меню устарело.\nОтправьте /start для обновления.",
                show_alert=True
            )
    else:
        # Это ОЧЕНЬ старое меню (не в БД или другое сообщение)
        logger.warning(
            f"⚠️ Very old menu detected: "
            f"msg_id={callback.message.message_id}, "
            f"db_msg_id={menu_info.get('menu_message_id') if menu_info else 'None'}"
        )

        await callback.answer(
            "⚠️ Это меню устарело.\n\n"
            "Отправьте команду /start для обновления.",
            show_alert=True
        )

        await db.log_activity(user_id, 'very_old_menu_detected')
