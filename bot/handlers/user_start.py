# bot/handlers/user_start.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from tenacity import retry, stop_after_attempt, wait_exponential

from database.db import db
from config import config
from states.fsm import CreationStates
from keyboards.inline import get_main_menu_keyboard, get_mode_selection_keyboard, get_profile_keyboard
from utils.texts import START_TEXT, MODE_SELECTION_TEXT, PROFILE_TEXT
from utils.navigation import edit_menu, show_main_menu
from utils.helpers import add_balance_and_mode_to_text

logger = logging.getLogger(__name__)
router = Router()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
async def send_message_with_retry(message: Message, text: str, **kwargs):
    """Отправить сообщение с retry"""
    return await message.answer(text, **kwargs)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
async def delete_message_safe(message: Message):
    """Безопасное удаление с retry"""
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"Could not delete message: {e}")


@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, admins: list[int]):
    """SCREEN 0: ГЛАВНОЕ МЕНИ с 3 кнопками"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username

    start_param = message.text.split()[1] if len(message.text.split()) > 1 else None

    if start_param == "payment_success":
        await db.delete_old_menu_if_exists(chat_id, message.bot)

        user_data = await db.get_user_data(user_id)

        if user_data:
            balance = user_data.get('balance', 0)
            text = f"✅ **Платёж успешен!**\n\n💎 Ваш баланс: **{balance}** генераций"

            try:
                menu_msg = await send_message_with_retry(
                    message,
                    text,
                    reply_markup=get_profile_keyboard(),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to send payment_success message: {e}")
                return

            await delete_message_safe(message)
            await state.update_data(menu_message_id=menu_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'profile')
            logger.info(f"✅ [PAYMENT_SUCCESS] User {user_id}, msg_id={menu_msg.message_id}")
            return

    await db.delete_old_menu_if_exists(chat_id, message.bot)
    await state.clear()
    await state.update_data(session_started=True)
    logger.info(f"🔴 [/START] session_started=True для user_id={user_id}")

    user_data = await db.get_user_data(user_id)
    is_new_user = user_data is None

    if is_new_user:
        referrer_code = None
        if start_param and start_param.startswith('ref_'):
            referrer_code = start_param.replace('ref_', '')

        await db.create_user(user_id, username, referrer_code)

        if start_param and start_param.startswith("src_"):
            source = start_param[4:]
            await db.set_user_source(user_id, source)

        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_new_users")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        f"👤 Новый пользователь: ID `{user_id}`, username: @{username or 'не указан'}",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Error notifying admins: {e}")

    await delete_message_safe(message)

    try:
        text = await add_balance_and_mode_to_text(START_TEXT, user_id)
        menu_msg = await send_message_with_retry(
            message,
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send main menu message: {e}")
        return

    await state.update_data(menu_message_id=menu_msg.message_id)
    await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'main_menu')
    logger.info(f"✅ [START] User {user_id}: SCREEN 0, msg_id={menu_msg.message_id}, new={is_new_user}")


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат в SCREEN 0"""
    await show_main_menu(callback, state, admins)
    await callback.answer()


@router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    """Показывает профиль пользователя"""
    user_id = callback.from_user.id

    try:
        user_data = await db.get_user_data(user_id)

        if not user_data:
            username = callback.from_user.username
            await db.create_user(user_id, username)
            user_data = await db.get_user_data(user_id)

        if user_data:
            balance = user_data.get('balance', 0)
            reg_date = user_data.get('reg_date', 'неизвестно')
            username = user_data.get('username') or callback.from_user.username or 'не указан'

            profile_text = PROFILE_TEXT.format(
                user_id=user_id,
                username=username,
                balance=balance,
                reg_date=reg_date
            )

            await edit_menu(
                callback=callback,
                state=state,
                text=profile_text,
                keyboard=get_profile_keyboard(),
                show_balance=False,
                screen_code='profile'
            )
        else:
            await callback.answer("❌ Ошибка создания профиля", show_alert=True)

    except Exception as e:
        logger.error(f"Error in show_profile: {e}")
        await callback.answer("❌ Ошибка загрузки профиля", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "buy_generations")
async def buy_generations_handler(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия 'Купить генерации'"""
    try:
        from keyboards.inline import get_payment_keyboard

        await edit_menu(
            callback=callback,
            state=state,
            text="💰 **Выберите пакет генераций:**\n\nПосле оплаты баланс автоматически пополнится.",
            keyboard=get_payment_keyboard(),
            screen_code='balance'
        )
    except Exception as e:
        logger.error(f"Error in buy_generations_handler: {e}")
        await callback.answer("❌ Ошибка загрузки платежей", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext):
    """SCREEN 1: Показываем режимы работы с 5 кнопками"""
    user_id = callback.from_user.id

    try:
        await db.log_activity(user_id, 'create_design')

        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')

        await state.clear()

        if menu_message_id:
            await state.update_data(menu_message_id=menu_message_id)

        await state.set_state(CreationStates.selecting_mode)

        text = MODE_SELECTION_TEXT
        text = await add_balance_and_mode_to_text(text, user_id)

        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_mode_selection_keyboard(),
            show_balance=False,
            screen_code='selecting_mode'
        )

        logger.info(f"[CREATE_DESIGN] User {user_id}: SCREEN 1 (selecting_mode)")

    except Exception as e:
        logger.error(f"Error in start_creation: {e}")
        await callback.answer("❌ Ошибка загрузки режимов", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "show_statistics")
async def show_statistics(callback: CallbackQuery, state: FSMContext):
    """Показывает статистику пользователя"""
    user_id = callback.from_user.id

    try:
        user_data = await db.get_user_data(user_id)

        if not user_data:
            await callback.answer("❌ Ошибка получения данных", show_alert=True)
            return

        balance = user_data.get('balance', 0)
        reg_date = user_data.get('reg_date', 'неизвестно')

        stats_text = (
            f"📋 **СТАТИСТИКА**\n\n"
            f"─────────────\n"
            f"✨ Текущий баланс: **{balance}** генераций\n"
            f"📅 С нами с: {reg_date}\n"
            f"─────────────\n\n"
            f"ℹ️ Детальная статистика в разработке..."
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))

        await edit_menu(
            callback=callback,
            state=state,
            text=stats_text,
            keyboard=builder.as_markup(),
            show_balance=False,
            screen_code='statistics'
        )
    except Exception as e:
        logger.error(f"Error in show_statistics: {e}")
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "show_referral_program")
async def show_referral_program(callback: CallbackQuery, state: FSMContext):
    """Показывает экран партнёрской программы"""
    user_id = callback.from_user.id

    try:
        user_data = await db.get_user_data(user_id)

        if not user_data:
            await callback.answer("❌ Ошибка получения данных", show_alert=True)
            return

        referral_code = user_data.get('referral_code', '')
        referrals_count = user_data.get('referrals_count', 0)
        referral_balance = user_data.get('referral_balance', 0)
        referral_total_earned = user_data.get('referral_total_earned', 0) or 0
        referral_total_paid = user_data.get('referral_total_paid', 0) or 0

        commission_percent = await db.get_setting('referral_commission_percent') or '10'

        bot_username = config.BOT_USERNAME.replace('@', '')
        referral_link = f"t.me/{bot_username}?start=ref_{referral_code}"

        def get_word_form(count: int) -> str:
            if count % 10 == 1 and count % 100 != 11:
                return "друг"
            elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
                return "друга"
            else:
                return "дружей"

        referrals_word = get_word_form(referrals_count)

        def format_number(num: int) -> str:
            return f"{num:,}".replace(',', ' ')

        referral_text = (
            f"🎁 **ПАРТНЕРСКАЯ ПРОГРАММА**\n\n"
            f"─────────────\n"
            f"🔗 Ваша ссылка:\n`{referral_link}`\n\n"
            f"👥 Приглашено: **{referrals_count}** {referrals_word}\n"
            f"─────────────\n\n"
            f"💰 **Реферальный баланс:**\n"
            f"• Доступно: **{format_number(referral_balance)} руб.**\n"
            f"• Всего заработано: {format_number(referral_total_earned)} руб.\n"
            f"• Выплачено: {format_number(referral_total_paid)} руб.\n\n"
            f"🎯 **Ваши условия:**\n"
            f"• За регистрацию: +2 генерации\n"
            f"• % от покупок: {commission_percent}%\n"
            f"─────────────"
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="💸 Вывести деньги", callback_data="referral_request_payout"),
            InlineKeyboardButton(text="💎 Обменять на генерации", callback_data="referral_exchange_tokens")
        )
        builder.row(InlineKeyboardButton(text="⚙️ Реквизиты для выплат", callback_data="referral_setup_payment"))
        builder.row(InlineKeyboardButton(text="📋 История операций", callback_data="referral_history"))
        builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))

        builder.adjust(2, 1, 1, 1)

        await edit_menu(
            callback=callback,
            state=state,
            text=referral_text,
            keyboard=builder.as_markup(),
            show_balance=False,
            screen_code='referral'
        )
    except Exception as e:
        logger.error(f"Error in show_referral_program: {e}")
        await callback.answer("❌ Ошибка загрузки реферальной программы", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "show_support")
async def show_support(callback: CallbackQuery, state: FSMContext):
    """Показывает информацию о поддержке"""
    try:
        support_text = (
            "💬 **ПОДДЕРЖКА**\n\n"
            "─────────────\n"
            "📧 Email: support@example.com\n"
            "💬 Telegram: `@support_bot`\n"
            "─────────────\n\n"
            "ℹ️ Мы ответим в течение 24 часов"
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))

        await edit_menu(
            callback=callback,
            state=state,
            text=support_text,
            keyboard=builder.as_markup(),
            show_balance=False,
            screen_code='support'
        )
    except Exception as e:
        logger.error(f"Error in show_support: {e}")
        await callback.answer("❌ Ошибка загрузки поддержки", show_alert=True)

    await callback.answer()