# bot/handlers/user_start.py
# --- ОБНОВЛЕН: 2025-12-30 23:50 - ИСПРАВЛЕНИЕ SCREEN 0 и SCREEN 1 ---
# [2025-12-30 23:50] ИСПРАВЛЕНИЕ: cmd_start теперь показывает SCREEN 0 (главное меню, 3 кнопки)
# [2025-12-30 23:50] ИСПРАВЛЕНИЕ: create_design показывает SCREEN 1 (режимы, 5 кнопок)
# [2025-12-30 23:50] Обновлены импорты: get_main_menu_keyboard + get_mode_selection_keyboard

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.db import db
from config import config
from states.fsm import CreationStates
from keyboards.inline import get_main_menu_keyboard, get_mode_selection_keyboard, get_profile_keyboard
from utils.texts import START_TEXT, MODE_SELECTION_TEXT, PROFILE_TEXT
from utils.navigation import edit_menu, show_main_menu
from utils.helpers import add_balance_to_text
from utils.helpers import add_balance_and_mode_to_text
logger = logging.getLogger(__name__)
router = Router()

#  https://t.me/Interior_Bot1_bot?start=payment_success


# Обрабатывает команду /start.
@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, admins: list[int]):
    """
    SCREEN 0: ГЛАВНОЕ МЕНИ с 3 кнопками
    Безопасно удаляет старое меню, создает новое и сохраняет в БД.
    
    🔴 КРИТИЧЕСКОЕ: Устанавливаем session_started=True
    Это обеспечивает правильную логику видимости кнопки загружения фото
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username

    # ===== 1️⃣ ПАРЗИМ АРГУМЕНТЫ =====
    start_param = message.text.split()[1] if len(message.text.split()) > 1 else None

    # ===== 2️⃣ ПРОВЕРЯЕМ - УСПЕШНЫЙ ПЛАТЕЖ? =====
    if start_param == "payment_success":
        # Удаляем старое меню
        await db.delete_old_menu_if_exists(chat_id, message.bot)

        # Показываем личный кабинет
        user_data = await db.get_user_data(user_id)
        if user_data:
            balance = user_data.get('balance', 0)
            text = f"✅ **Платёж успешен!**\n\n💎 Ваш баланс: **{balance}** генераций"

            from keyboards.inline import get_profile_keyboard

            # Сохраняем в FSM + БД
            menu_msg = await message.answer(
                text,
                reply_markup=get_profile_keyboard(),
                parse_mode="Markdown"
            )

            # Удаляем команду
            try:
                await message.delete()
            except:
                pass

            # Сохраняем в FSM + БД
            await state.update_data(menu_message_id=menu_msg.message_id)
            await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'profile')

            logger.info(f"✅ [PAYMENT_SUCCESS] User {user_id} redirected to profile, msg_id={menu_msg.message_id}")
            return

    # ===== 3️⃣ БЕЗОПАСНО УДАЛЯЕМ СТАРОЕ МЕНУ =====
    await db.delete_old_menu_if_exists(chat_id, message.bot)

    # ===== 4️⃣ ОЧИЩАЕМ FSM STATE =====
    await state.clear()

    # ===== 🔴 КРИТИЧЕСКОЕ: УСТАНАВЛИВАЕМ session_started=True =====
    # Это указывает на то, что пользователь только что нажал /start
    # Флаг будет отключен после загружки первого фото в этой сессии
    await state.update_data(session_started=True)
    logger.info(f"🔴 [/START] Установлен флаг session_started=True для user_id={user_id}")

    # ===== 5️⃣ ПРОВЕРЯЕМ - НОВЫЙ ПОЛЬЗОВАТЕЛЬ? =====
    user_data = await db.get_user_data(user_id)
    is_new_user = user_data is None

    if is_new_user:
        # Парсим реферальный код
        referrer_code = None
        if start_param and start_param.startswith('ref_'):
            referrer_code = start_param.replace('ref_', '')

        # Создаём пользователя
        await db.create_user(user_id, username, referrer_code)

        # Разбор источника
        if start_param and start_param.startswith("src_"):
            source = start_param[4:]
            await db.set_user_source(user_id, source)

        # Уведомление админов о НОВОМ пользователе
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
                    logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")

    # ===== 6️⃣ УДАЛЯЕМ КОМАНДУ /start ИЗ ЧАТА =====
    try:
        await message.delete()
    except:
        pass

    # ===== 7️⃣ ОТПРАВЛЯЕМ SCREEN 0: ГЛАВНОЕ МЕНИ С БАЛАНСОМ =====
    text = await add_balance_and_mode_to_text(START_TEXT, user_id)
    menu_msg = await message.answer(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

    # ===== 8️⃣ 📔 СОХРАНЯЕМ В FSM + БД =====
    await state.update_data(menu_message_id=menu_msg.message_id)
    await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'main_menu')

    logger.info(f"✅ [START] User {user_id}: SCREEN 0 created, msg_id={menu_msg.message_id}, new={is_new_user}")


# Возврат в главное меню из любого места.
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Возврат в SCREEN 0 (главное меню) из любого места.
    МОНОПОЛЬзУЕТ state.set_state(None) вместо state.clear()!
    """
    await show_main_menu(callback, state, admins)
    await callback.answer()


#  """Показывает профиль пользователя"""
@router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id

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
            screen_code='profile'  # ← ДОБАВЛЕН screen_code
        )
    else:
        await callback.answer("❌ Ошибка создания профиля. Попробуйте /start", show_alert=True)

    await callback.answer()


#  """Обработка нажатия 'Купить генерации'"""
@router.callback_query(F.data == "buy_generations")
async def buy_generations_handler(callback: CallbackQuery, state: FSMContext):

    from keyboards.inline import get_payment_keyboard

    await edit_menu(
        callback=callback,
        state=state,
        text="💰 **Выберите пакет генераций:**\n\nПосле оплаты баланс автоматически пополнится.",
        keyboard=get_payment_keyboard(),
        screen_code='balance'  # ← ДОБАВЛЕН screen_code
    )
    await callback.answer()


# """Начало создания дизайна"""
@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext):
    """
    НОВОЕ (2025-12-30): Показываем SCREEN 1 (режимы работы с 5 кнопками)
    
    Flow:
    create_design button (SCREEN 0 - главное меню)
            ↓
    show SCREEN 1 (select_mode с 5 кнопками режимов)
            ↓
    пользователь выбирает режим
            ↓
    переход на SCREEN 2 (uploading_photo)
    """

    user_id = callback.from_user.id
    await db.log_activity(user_id, 'create_design')

    # СОХРАНЯЕМ menu_message_id перед очисткой
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()

    # ВОссТАНАВЛИВАЕМ menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    # Устанавливаем состояние для выбора режима
    await state.set_state(CreationStates.selecting_mode)

    #=================================
    # Показываем SCREEN 1 с 5 режимами
    #==================================
    text = MODE_SELECTION_TEXT
    text = await add_balance_and_mode_to_text(text, user_id)
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(),
        show_balance=False,  # Баланс уже добавлен выше
        screen_code='selecting_mode'
    )
    
    logger.info(f"[CREATE_DESIGN] User {user_id}: showing SCREEN 1 (selecting_mode)")
    await callback.answer()


#"""Показывает статистику пользователя"""
@router.callback_query(F.data == "show_statistics")
async def show_statistics(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    user_data = await db.get_user_data(user_id)

    if not user_data:
        await callback.answer("❌ Ошибка получения данных", show_alert=True)
        return

    balance = user_data.get('balance', 0)
    reg_date = user_data.get('reg_date', 'неизвестно')

    stats_text = (
        f"📋 **СТАТИСТИКА**\n\n"
        f"─────────────\n"
        f"✨ Нынешний баланс: **{balance}** генераций\n"
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
        screen_code='statistics'  # ← ДОБАВЛЕН screen_code
    )

    await callback.answer()


#"""Показывает экран партнёрской программы"""
@router.callback_query(F.data == "show_referral_program")
async def show_referral_program(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
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
        screen_code='referral'  # ← ДОБАВЛЕН screen_code
    )

    await callback.answer()


# """Показывает информацию о поддержке"""
@router.callback_query(F.data == "show_support")
async def show_support(callback: CallbackQuery, state: FSMContext):

    support_text = (
        "💬 **ПОДДЕРЖКА**\n\n"
        "─────────────\n"
        "📧 Email: support@example.com\n"
        "💬 Telegram: `@support_bot`\n"
        "─────────────\n\n"
        "\u2139️ Мы ответим в течение 24 часов"
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
        screen_code='support'  # ← ДОБАВЛЕН screen_code
    )

    await callback.answer()
