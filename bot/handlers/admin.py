# bot/handlers/admin.py
# --- ОБНОВЛЕН: 2025-12-09 18:45 - Исправлен блок управления балансом по единому меню ---
# [2025-12-09 18:45] Удалены дублирующиеся функции управления балансом
# [2025-12-09 18:45] Добавлено удаление текстовых сообщений админа (await message.delete())
# [2025-12-09 18:45] Все операции редактируют единое меню через menu_message_id
# [2025-12-09 18:45] Добавлена функция balance_more_management для возврата к карточке пользователя
# [2025-12-09 18:45] Кнопка "Ещё одно управление" теперь ведёт к карточке с обновлённым балансом
# [2025-12-07 11:02] Заменён state.clear() на state.set_state(None) в show_admin_panel() и show_admin_settings()
# [2025-12-07 11:02] Добавлено сохранение screen_code в БД после каждого редактирования меню
# [2025-12-07 11:02] Сохраняется menu_message_id при всех переходах
# [2025-12-04 12:25] Добавлен счетчик неудачных генераций


import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.navigation import edit_menu  # ← ДОБАВИТЬ ЭНУЮ СТРОКУ
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.db import db
from states.fsm import AdminStates

from keyboards.admin_kb import (
    get_admin_main_menu,
    get_back_to_admin_menu,
    get_users_list_keyboard,
    get_balance_main_keyboard,
    get_balance_confirm_keyboard,
    get_balance_cancel_keyboard
)

logger = logging.getLogger(__name__)
router = Router()


# ===== ПРОВЕРКА АДМИНА =====
def is_admin(user_id: int, admins: list[int]) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id in admins


# ===== ГЛАВНОЕ МЕНЮ АДМИН-ПАНЕЛИ (КНОПКА) =====
@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Показывает главное меню админ-панели.
    КРИТИЧНО: ИСПОЛЬЗУЕТ state.set_state(None) вместо state.clear()!
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # ✅ КРИТИЧНО: Сохраняем menu_message_id ПЕРЕД любыми действиями
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    logger.debug(f"🔧 [ADMIN PANEL] user={user_id}, menu_id={menu_message_id}")

    # ✅ ИСПОЛЬЗУЕМ state.set_state(None) вместо state.clear()!
    await state.set_state(None)

    # ✅ ВОССТАНАВЛИВАЕМ menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    # Получаем статистику
    total_users = await db.get_total_users_count()
    total_revenue = await db.get_total_revenue()
    new_today = await db.get_new_users_count(days=1)
    successful_payments = await db.get_successful_payments_count()
    failed_today = await db.get_failed_generations_count(days=1)

    admin_text = (
        "👑 **АДМИН-ПАНЕЛЬ**\n\n"
        f"📊 **Общая статистика:**\n"
        f"• Всего пользователей: **{total_users}**\n"
        f"• Новых за сегодня: **{new_today}**\n"
        f"• Общая выручка: **{total_revenue} руб.**\n"
        f"• Успешных платежей: **{successful_payments}**\n"
        f"• ⚠️ **Неудачных генераций сегодня: {failed_today}**\n\n"
        "Выберите действие:"
    )

    try:
        await callback.message.edit_text(
            text=admin_text,
            reply_markup=get_admin_main_menu(),
            parse_mode="Markdown"
        )
        # Сохраняем screen_code в БД
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'admin_panel')

    except Exception as e:
        logger.error(f"❌ [ADMIN PANEL] Error: {e}")

    await callback.answer()


# ===== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ АДМИНКИ =====
@router.callback_query(F.data == "admin_main")
async def back_to_admin_main(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат в главное меню админ-панели"""
    await show_admin_panel(callback, state, admins)


# ===== ДЕТАЛЬНАЯ СТАТИСТИКА =====
@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Показать детальную статистику системы"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # ПОЛЬЗОВАТЕЛИ
    total_users = await db.get_total_users_count()
    new_today = await db.get_new_users_count(days=1)
    new_week = await db.get_new_users_count(days=7)
    active_today = await db.get_active_users_count(days=1)
    active_week = await db.get_active_users_count(days=7)

    # ГЕНЕРАЦИИ
    total_generations = await db.get_total_generations()
    generations_today = await db.get_generations_count(days=1)
    generations_week = await db.get_generations_count(days=7)
    failed_today = await db.get_failed_generations_count(days=1)
    failed_week = await db.get_failed_generations_count(days=7)
    conversion_rate = await db.get_conversion_rate()

    # ФИНАНСЫ
    total_revenue = await db.get_total_revenue()
    revenue_today = await db.get_revenue_by_period(days=1)
    revenue_week = await db.get_revenue_by_period(days=7)
    successful_payments = await db.get_successful_payments_count()
    average_payment = await db.get_average_payment()

    # ПОПУЛЯРНЫЕ КОМНАТЫ И СТИЛИ
    popular_rooms = await db.get_popular_rooms(limit=5)
    popular_styles = await db.get_popular_styles(limit=5)

    if popular_rooms:
        rooms_list = []
        for room in popular_rooms:
            room_type_clean = room['room_type'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']',
                                                                                                                    '\\]').replace(
                '`', '\\`')
            rooms_list.append(f"  • {room_type_clean}: **{room['count']}**")
        rooms_text = "\n".join(rooms_list)
    else:
        rooms_text = "  • Данных пока нет"

    if popular_styles:
        styles_list = []
        for style in popular_styles:
            style_type_clean = style['style_type'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(
                ']', '\\]').replace('`', '\\`')
            styles_list.append(f"  • {style_type_clean}: **{style['count']}**")
        styles_text = "\n".join(styles_list)
    else:
        styles_text = "  • Данных пока нет"

    stats_text = (
        "📊 **ДЕТАЛЬНАЯ СТАТИСТИКА СИСТЕМЫ**\n\n"
        "👥 **Пользователи:**\n"
        f"• Всего: **{total_users}**\n"
        f"• Новых за сегодня: **{new_today}**\n"
        f"• Новых за неделю: **{new_week}**\n"
        f"• Активных за сегодня: **{active_today}**\n"
        f"• Активных за неделю: **{active_week}**\n\n"
        "🎨 **Генерации:**\n"
        f"• Всего сгенерировано: **{total_generations}**\n"
        f"• За сегодня: **{generations_today}**\n"
        f"• За неделю: **{generations_week}**\n"
        f"• Средняя конверсия: **{conversion_rate}**\n\n"
        f"• ⚠️ **Неудачных сегодня: {failed_today}**\n"
        f"• ⚠️ **Неудачных за неделю: {failed_week}**\n\n"
        "💰 **Финансы:**\n"
        f"• Общая выручка: **{total_revenue} руб.**\n"
        f"• Выручка за сегодня: **{revenue_today} руб.**\n"
        f"• Выручка за неделю: **{revenue_week} руб.**\n"
        f"• Успешных платежей: **{successful_payments}**\n"
        f"• Средний чек: **{average_payment} руб.**\n\n"
        "🏠 **Популярные комнаты:**\n"
        f"{rooms_text}\n\n"
        "🎨 **Популярные стили:**\n"
        f"{styles_text}"
    )

    try:
        await callback.message.edit_text(
            text=stats_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
        # Сохраняем screen_code
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'admin_stats')

    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")

    await callback.answer()


# ===== СПИСОК ВСЕХ ПОЛЬЗОВАТЕЛЕЙ =====
@router.callback_query(F.data == "admin_users")
async def show_all_users(callback: CallbackQuery, admins: list[int]):
    """Показать список всех пользователей (первая страница)"""
    await show_users_page(callback, page=1, admins=admins)


@router.callback_query(F.data.startswith("admin_users_page_"))
async def show_users_page_handler(callback: CallbackQuery, admins: list[int]):
    """Обработчик пагинации пользователей"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    page = int(callback.data.split("_")[-1])
    await show_users_page(callback, page=page, admins=admins)


async def show_users_page(callback: CallbackQuery, page: int, admins: list[int]):
    """Показать конкретную страницу пользователей"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    all_users = await db.get_recent_users(limit=1000)

    if not all_users:
        await callback.answer("📭 Пользователей нет.", show_alert=True)
        return

    per_page = 10
    total_pages = (len(all_users) + per_page - 1) // per_page

    if page < 1 or page > total_pages:
        page = 1

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    users = all_users[start_idx:end_idx]

    users_text = f"👥 **СПИСОК ПОЛЬЗОВАТЕЛЕЙ** (стр. {page}/{total_pages})\n\n"
    for idx, user in enumerate(users, start=start_idx + 1):
        user_id_str = user.get('user_id', 'N/A')
        username = user.get('username', '')
        balance = user.get('balance', 0)

        username_clean = (username or "Без username").replace('@', '').replace('_', '\\\\_').replace('*', '\\\\*')

        users_text += f"{idx}. ID: `{user_id_str}` | {username_clean} | 💰 {balance}\n"

    try:
        await callback.message.edit_text(
            text=users_text,
            reply_markup=get_users_list_keyboard(page, total_pages),
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, f'admin_users_page_{page}')
    except Exception as e:
        logger.error(f"Ошибка показа пользователей: {e}")

    await callback.answer()


# ===== ПОИСК ПОЛЬЗОВАТЕЛЯ =====
@router.callback_query(F.data == "admin_find_user")
async def start_find_user(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Начало поиска пользователя"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_search)

    search_text = (
        "🔍 **ПОИСК ПОЛЬЗОВАТЕЛЯ**\n\n"
        "Отправьте мне один из следующих данных:\n\n"
        "• `ID пользователя` (например: `123456789`)\n"
        "• `@username` (например: `@ivan_petrov`)\n"
        "• `Реферальный код` (например: `abc123xyz`)\n\n"
        "⚠️ Для отмены нажмите кнопку ниже."
    )

    try:
        await callback.message.edit_text(
            text=search_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
        # Сохраняем screen_code
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'admin_find_user')

    except Exception as e:
        logger.error(f"Ошибка показа поиска: {e}")

    await callback.answer()


@router.message(AdminStates.waiting_for_search)
async def process_search_query(message: Message, state: FSMContext, admins: list[int]):
    """Обработка поискового запроса (поддерживает обычный поиск и управление балансом)"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    query = message.text.strip()

    # ✅ КРИТИЧНО: УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ СРАЗУ!
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"Не удалось удалить сообщение: {e}")

    user_data = await db.search_user(query)

    # Получаем контекст и menu_message_id
    state_data = await state.get_data()
    balance_context = state_data.get('balance_context')
    menu_message_id = state_data.get('menu_message_id')

    if not user_data:
        # ✅ ИСПОЛЬЗУЕМ edit_message_text ВМЕСТО answer
        if menu_message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    text="❌ **Пользователь не найден!**\n\nПопробуйте другой запрос.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_settings")]
                    ]),
                    parse_mode="Markdown"
                )
                await db.save_chat_menu(chat_id, user_id, menu_message_id, 'balance_not_found')
            except Exception as e:
                logger.error(f"Ошибка редактирования меню: {e}")
        return

    # ЕСЛИ ЭТО ПОИСК ДЛЯ УПРАВЛЕНИЯ БАЛАНСОМ:
    if balance_context == 'main':
        await state.set_state(None)

        found_user_id = user_data['user_id']
        username = user_data['username'] or "Не указан"
        balance = user_data['balance']
        total_generations = user_data['total_generations']
        successful_payments = user_data['successful_payments']

        # Сохраняем target_user_id для операций с балансом
        await state.update_data(target_user_id=found_user_id, balance_context='found', menu_message_id=menu_message_id)

        username_clean = username.replace('_', '\\_').replace('*', '\\*')
        tg_link = f"[{username_clean}](tg://user?id={found_user_id})"

        result_text = (
            "✅ **ПОЛЬЗОВАТЕЛЬ НАЙДЕН!**\n\n"
            f"🆔 **ID:** `{found_user_id}`\n"
            f"👤 **Username:** {tg_link}\n"
            f"💎 **Текущий баланс:** **{balance}** генераций\n"
            f"📊 **Всего генераций:** {total_generations}\n"
            f"💳 **Успешных платежей:** {successful_payments}\n\n"
            "**Выберите действие:**"
        )

        # ✅ ИСПОЛЬЗУЕМ edit_message_text ВМЕСТО answer!
        if menu_message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    text=result_text,
                    reply_markup=get_balance_main_keyboard(found_user_id),
                    parse_mode="Markdown"
                )
                await db.save_chat_menu(chat_id, user_id, menu_message_id, 'balance_user_found')
                logger.info(f"✅ Found user {found_user_id} for balance management")
            except Exception as e:
                logger.error(f"❌ Ошибка при редактировании меню: {e}")

        await db.log_activity(user_id, 'balance_search')
        return

    # ИНАЧЕ - ЭТО ОБЫЧНЫЙ ПОИСК (существующий код остается без изменений)
    await state.set_state(None)

    found_user_id = user_data['user_id']
    username = user_data['username'] or "Не указан"
    total_generations = user_data.get('total_generations', 0)
    balance = user_data['balance']
    referral_balance = user_data['referral_balance']
    referral_code = user_data['referral_code']
    referrals_count = user_data['referrals_count']
    reg_date = user_data['reg_date']

    payments_stats = await db.get_user_payments_stats(found_user_id)
    payments_count = payments_stats['count']
    total_paid = payments_stats['total_amount']

    recent_payments = await db.get_user_recent_payments(found_user_id, limit=5)
    referrer_info = await db.get_referrer_info(found_user_id)

    tg_link = f"[{username}](tg://user?id={found_user_id})"

    if referrer_info:
        referrer_id = referrer_info['referrer_id']
        referrer_username = referrer_info['referrer_username'] or "Не указан"
        referrer_text = f"[{referrer_username}](tg://user?id={referrer_id}) (ID: `{referrer_id}`)"
    else:
        referrer_text = "Нет"

    if recent_payments:
        payments_text = ""
        for payment in recent_payments:
            try:
                payment_date = datetime.fromisoformat(payment['payment_date'])
                date_str = payment_date.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = payment['payment_date']

            payments_text += f"  • {payment['amount']} руб. ({payment['tokens']} ток.) - {date_str}\n"
    else:
        payments_text = "  • Платежей нет\n"

    result_text = (
        "✅ **ПОЛЬЗОВАТЕЛЬ НАЙДЕН!**\n\n"
        f"🆔 **ID:** `{found_user_id}`\n"
        f"👤 **Username:** {tg_link}\n"
        f"💰 **Баланс генераций:** {balance}\n"
        f"💸 **Реферальный баланс:** {referral_balance} руб.\n"
        f"🔗 **Реферальный код:** `{referral_code}`\n"
        f"👥 **Привлечено рефералов:** {referrals_count}\n"
        f"🔽 **Пригласил:** {referrer_text}\n"
        f"📅 **Дата регистрации:** {reg_date}\n\n"
        "📊 **Статистика:**\n"
        f"• Количество оплат: **{payments_count}**\n"
        f"• Всего оплачено: **{total_paid} руб.**\n"
        f"• Выполнено генераций: **{total_generations}**\n\n"
        "💳 **Последние платежи:**\n"
        f"{payments_text}\n"
        "⚙️ **Доступные действия:**\n"
        f"• `/add_tokens {found_user_id} <кол-во>` - добавить токены\n"
        f"• `/balance {found_user_id}` - проверить баланс"
    )

    # ✅ КРИТИЧНО: Удаляем сообщение пользователя ПЕРЕД редактированием меню
    try:
        await message.delete()
        logger.debug(f"✅ Deleted user search message")
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить сообщение: {e}")

    # ✅ Получаем menu_message_id из БД (НЕ из FSM!)
    menu_info = await db.get_chat_menu(chat_id)

    if menu_info and menu_info.get('menu_message_id'):
        try:
            # ✅ Редактируем СУЩЕСТВУЮЩЕЕ меню согласно DEVELOPMENT_RULES.md
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_info['menu_message_id'],
                text=result_text,
                reply_markup=get_back_to_admin_menu(),
                parse_mode="Markdown"
            )
            # Сохраняем новый screen_code
            await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'admin_find_user_result')
            logger.info(
                f"✅ Regular search: edited menu for user {found_user_id}, menu_id={menu_info['menu_message_id']}")
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования меню обычного поиска: {e}")
            # Fallback: создаём новое сообщение только если редактирование не удалось
            await message.answer(
                text=result_text,
                reply_markup=get_back_to_admin_menu(),
                parse_mode="Markdown"
            )
    else:
        # Если menu_message_id потерян в БД, создаём новое (не должно происходить)
        logger.warning(f"⚠️ menu_message_id not found in DB for chat {chat_id}, creating new message")
        await message.answer(
            text=result_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )

    await db.log_activity(user_id, 'user_search')

# ===== ИСТОРИЯ ПЛАТЕЖЕЙ =====
@router.callback_query(F.data == "admin_payments")
async def show_payments_history(callback: CallbackQuery, admins: list[int]):
    """Показать историю платежей"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    recent_payments = await db.get_user_recent_payments(None, limit=20)

    if not recent_payments:
        await callback.answer("📭 Платежей пока нет.", show_alert=True)
        return

    payments_text = "💰 **ИСТОРИЯ ПЛАТЕЖЕЙ** (последние 20)\n\n"
    for idx, payment in enumerate(recent_payments, start=1):
        status_emoji = "✅" if payment.get('status') == 'succeeded' else "⏳"
        username_clean = (payment.get('username', '') or "Без username").replace('_', '\\\\_').replace('*', '\\\\*')

        payments_text += (
            f"{idx}. {status_emoji} `{payment.get('user_id', 'N/A')}` | "
            f"{username_clean} | "
            f"**{payment.get('amount', 0)} руб.** | "
            f"{payment.get('tokens', 0)} токенов\n"
        )

    try:
        await callback.message.edit_text(
            text=payments_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'admin_payments')
    except Exception as e:
        logger.error(f"Ошибка показа платежей: {e}")

    await callback.answer()

# ===== КОМАНДЫ =====

@router.message(Command("add_tokens"))
async def cmd_add_tokens(message: Message, admins: list[int]):
    """Добавить токены пользователю"""
    user_id = message.from_user.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer(
                "❌ Неверный формат команды!\n\n"
                "Использование: `/add_tokens <user_id> <количество>`\n"
                "Пример: `/add_tokens 123456789 10`",
                parse_mode="Markdown"
            )
            return

        target_user_id = int(args[1])
        tokens_to_add = int(args[2])

        if tokens_to_add <= 0:
            await message.answer("❌ Количество токенов должно быть больше 0!")
            return

        await db.add_tokens(target_user_id, tokens_to_add)
        new_balance = await db.get_balance(target_user_id)

        await message.answer(
            f"✅ **Успешно!**\n\n"
            f"👤 Пользователь: `{target_user_id}`\n"
            f"➕ Добавлено токенов: **{tokens_to_add}**\n"
            f"💰 Новый баланс: **{new_balance}**",
            parse_mode="Markdown"
        )

        logger.info(f"Admin {user_id} added {tokens_to_add} tokens to user {target_user_id}")

    except ValueError:
        await message.answer(
            "❌ Ошибка! ID пользователя и количество токенов должны быть числами.\n\n"
            "Пример: `/add_tokens 123456789 10`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in add_tokens: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


@router.message(Command("balance"))
async def cmd_check_balance(message: Message, admins: list[int]):
    """Проверить баланс пользователя"""
    user_id = message.from_user.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer(
                "❌ Неверный формат команды!\n\n"
                "Использование: `/balance <user_id>`\n"
                "Пример: `/balance 123456789`",
                parse_mode="Markdown"
            )
            return

        target_user_id = int(args[1])
        balance = await db.get_balance(target_user_id)

        await message.answer(
            f"💰 **Баланс пользователя**\n\n"
            f"👤 ID: `{target_user_id}`\n"
            f"✨ Токенов: **{balance}**",
            parse_mode="Markdown"
        )

    except ValueError:
        await message.answer(
            "❌ Ошибка! ID пользователя должен быть числом.\n\n"
            "Пример: `/balance 123456789`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in check_balance: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


@router.message(Command("users"))
async def cmd_list_users(message: Message, admins: list[int]):
    """Показать список последних 10 пользователей"""
    user_id = message.from_user.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        users = await db.get_recent_users(limit=10)

        if not users:
            await message.answer("📭 Пользователей пока нет.")
            return

        text = "👥 **Последние пользователи:**\n\n"
        for idx, user in enumerate(users, 1):
            user_id_str = user.get('user_id', 'Unknown')
            username = user.get('username', 'Не указано')
            balance = user.get('balance', 0)

            username_clean = username.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']',
                                                                                                          '\\]').replace(
                '`', '\\`')

            text += f"{idx}. ID: `{user_id_str}` | {username_clean} | 💰 {balance}\n"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in list_users: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


# ===== УВЕДОМЛЕНИЯ АДМИНОВ =====

@router.callback_query(F.data == "admin_notifications")
async def show_admin_notifications(callback: CallbackQuery, admins: list[int]):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    settings = await db.get_admin_notifications(user_id)

    text = (
        "🔔 **НАСТРОЙКИ УВЕДОМЛЕНИЙ**\n\n"
        f"• Новый пользователь: {'✅' if settings['notify_new_users'] else '❌'}\n"
        f"• Новая оплата: {'✅' if settings['notify_new_payments'] else '❌'}\n"
        f"• Критические ошибки: {'✅' if settings['notify_critical_errors'] else '❌'}\n\n"
        "Нажмите на кнопку, чтобы переключить."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"👤 Новый пользователь {'✅' if settings['notify_new_users'] else '❌'}",
            callback_data="notify_toggle_new_users"
        )],
        [InlineKeyboardButton(
            text=f"💳 Новая оплата {'✅' if settings['notify_new_payments'] else '❌'}",
            callback_data="notify_toggle_new_payments"
        )],
        [InlineKeyboardButton(
            text=f"⚠️ Критические ошибки {'✅' if settings['notify_critical_errors'] else '❌'}",
            callback_data="notify_toggle_critical"
        )],
        [InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_main")]
    ])

    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="Markdown")
    # Сохраняем screen_code
    await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'admin_notifications')

    await callback.answer()


async def _toggle_notify_field(callback: CallbackQuery, admins: list[int], field: str):
    user_id = callback.from_user.id
    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    settings = await db.get_admin_notifications(user_id)
    settings[field] = 0 if settings[field] else 1
    await db.set_admin_notifications(
        admin_id=user_id,
        notify_new_users=settings["notify_new_users"],
        notify_new_payments=settings["notify_new_payments"],
        notify_critical_errors=settings["notify_critical_errors"],
    )
    await show_admin_notifications(callback, admins)


@router.callback_query(F.data == "notify_toggle_new_users")
async def notify_toggle_new_users(callback: CallbackQuery, admins: list[int]):
    await _toggle_notify_field(callback, admins, "notify_new_users")


@router.callback_query(F.data == "notify_toggle_new_payments")
async def notify_toggle_new_payments(callback: CallbackQuery, admins: list[int]):
    await _toggle_notify_field(callback, admins, "notify_new_payments")


@router.callback_query(F.data == "notify_toggle_critical")
async def notify_toggle_critical(callback: CallbackQuery, admins: list[int]):
    await _toggle_notify_field(callback, admins, "notify_critical_errors")


# ===== ИСТОЧНИКИ ТРАФИКА =====

@router.callback_query(F.data == "admin_sources")
async def show_sources_stats(callback: CallbackQuery, admins: list[int]):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    sources = await db.get_sources_stats()
    if not sources:
        text = "🌐 **Источники трафика**\n\nДанных пока нет."
    else:
        text = "🌐 **Источники трафика**\n\n"
        for item in sources:
            text += f"• `{item['source']}` — **{item['count']}** пользователей\n"

    await callback.message.edit_text(
        text=text,
        reply_markup=get_back_to_admin_menu(),
        parse_mode="Markdown"
    )
    # Сохраняем screen_code
    await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'admin_sources')

    await callback.answer()


# ===== НАСТРОЙКИ: ГЛАВНОЕ МЕНЮ =====
@router.callback_query(F.data == "admin_settings")
async def show_admin_settings(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Показывает главное меню настроек системы"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # ✅ ИСПРАВЛЕНО: НЕ state.clear(), А state.set_state(None)!
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.set_state(None)

    # Восстанавливаем menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    from keyboards.admin_kb import get_admin_settings_menu

    settings_text = (
        "⚙️ **Настройки**\n\n"
        "Выберите раздел для настройки:\n\n"
        "💰 **Управление балансом** — добавить/снять генерации\n"
        "📦 **Настройка пакетов** — изменить цены и количество\n"
        "🎁 **Скидки и акции** — промокоды\n"
        "🎯 **Бонусные настройки** — бонусы\n"
        "👥 **Реферальная система** — комиссии\n"
        "🔧 **Системные настройки** — лимиты"
    )

    try:
        await callback.message.edit_text(
            text=settings_text,
            reply_markup=get_admin_settings_menu(),
            parse_mode="Markdown"
        )
        # Сохраняем screen_code
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'admin_settings')

    except Exception as e:
        logger.error(f"Ошибка показа настроек: {e}")

    await callback.answer()


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: ГЛАВНОЕ МЕНЮ =====
# --- НАЧАЛО ИСПРАВЛЕННОГО БЛОКА (2025-12-09 18:45) ---

@router.callback_query(F.data == "settings_balance")
async def settings_balance(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Главное меню управления балансом"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # ✅ Сохраняем menu_message_id ПЕРЕД очисткой
    menu_message_id = callback.message.message_id

    # Используем set_state(None) вместо clear()
    await state.set_state(None)
    await state.update_data(menu_message_id=menu_message_id, balance_context='main')

    text = (
        "💰 **УПРАВЛЕНИЕ БАЛАНСОМ**\n\n"
        "Отправьте один из следующих данных для поиска пользователя:\n\n"
        "• **🆔 ID пользователя** (например: `123456789`)\n"
        "• **👤 @username** (например: `@ivan_petrov`)\n"
        "• **🔗 Реферальный код** (например: `abc123xyz`)\n\n"
        "⚠️ Для отмены нажмите кнопку ниже."
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад в настройки", callback_data="admin_settings")]
            ]),
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'settings_balance')
        logger.info(f"🔄 Admin {user_id} opened balance management menu")
    except Exception as e:
        logger.error(f"❌ Ошибка при показе меню управления балансом: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)
        return

    # ✅ Ждем текстовый ввод (ID, username или реф. код)
    await state.set_state(AdminStates.waiting_for_search)
    await callback.answer()


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: ПОИСК ПОЛЬЗОВАТЕЛЯ =====
# Функция process_search_query уже реализована выше и работает корректно


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: ДОБАВЛЕНИЕ =====

@router.callback_query(F.data.startswith("balance_add_"))
async def balance_add_start(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Начало процесса добавления генераций"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[2])

    # ✅ Сохраняем menu_message_id из текущего сообщения
    menu_message_id = callback.message.message_id

    await state.update_data(
        balance_operation='add',
        target_user_id=target_user_id,
        menu_message_id=menu_message_id
    )
    await state.set_state(AdminStates.adding_balance)

    current_balance = await db.get_balance(target_user_id)

    text = (
        f"➕ **ДОБАВИТЬ ГЕНЕРАЦИИ**\n\n"
        f"👤 Пользователь: `{target_user_id}`\n"
        f"💎 Текущий баланс: **{current_balance}**\n\n"
        "Сколько генераций добавить? Отправьте число (1-99999):"
    )

    try:
        # ✅ РЕДАКТИРУЕМ существующее сообщение, НЕ создаём новое
        await callback.message.edit_text(
            text=text,
            reply_markup=get_balance_cancel_keyboard(),
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'balance_add')
        logger.info(f"🔄 Admin {user_id} started adding balance for user {target_user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при показе экрана добавления: {e}")

    await callback.answer()


@router.message(AdminStates.adding_balance)
async def balance_add_amount(message: Message, state: FSMContext, admins: list[int]):
    """Обработка количества для добавления"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    # ✅ КРИТИЧНО: УДАЛЯЕМ сообщение админа СРАЗУ
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")

    # Валидация ввода
    try:
        amount = int(message.text.strip())
        if amount <= 0 or amount > 99999:
            raise ValueError("Out of range")
    except ValueError:
        # ✅ Получаем menu_message_id из БД
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info and menu_info['menu_message_id']:
            error_text = (
                "❌ **ОШИБКА: НЕВЕРНОЕ ЗНАЧЕНИЕ**\n\n"
                "Пожалуйста, отправьте корректное число:\n"
                "• Минимум: **1**\n"
                "• Максимум: **99999**"
            )
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_info['menu_message_id'],
                    text=error_text,
                    reply_markup=get_balance_cancel_keyboard(),
                    parse_mode="Markdown"
                )
                await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_add_error')
            except Exception as e:
                logger.error(f"❌ Ошибка при показе ошибки валидации: {e}")
        return

    # Сохраняем amount в state
    await state.update_data(amount=amount)

    # Получаем данные
    data = await state.get_data()
    target_user_id = data['target_user_id']
    current_balance = await db.get_balance(target_user_id)
    new_balance = current_balance + amount

    # Текст подтверждения
    text = (
        "✅ **ПОДТВЕРЖДЕНИЕ: ДОБАВИТЬ ГЕНЕРАЦИИ**\n\n"
        f"👤 Пользователь: `{target_user_id}`\n"
        f"💎 Текущий баланс: **{current_balance}**\n"
        f"➕ Добавить: **{amount}**\n"
        f"📊 Новый баланс: **{new_balance}**\n\n"
        "Подтвердите операцию:"
    )

    # ✅ Редактируем ЕДИНОЕ меню
    menu_info = await db.get_chat_menu(chat_id)
    if menu_info and menu_info['menu_message_id']:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_info['menu_message_id'],
                text=text,
                reply_markup=get_balance_confirm_keyboard(),
                parse_mode="Markdown"
            )
            await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_confirm_add')
            logger.info(f"✅ Admin {user_id} entered amount {amount} for adding")
        except Exception as e:
            logger.error(f"❌ Ошибка при показе подтверждения: {e}")

    await db.log_activity(user_id, 'balance_add_amount_input')


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: СПИСАНИЕ =====

@router.callback_query(F.data.startswith("balance_remove_"))
async def balance_remove_start(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Начало процесса списания генераций"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[2])

    # ✅ Сохраняем menu_message_id
    menu_message_id = callback.message.message_id

    await state.update_data(
        balance_operation='remove',
        target_user_id=target_user_id,
        menu_message_id=menu_message_id
    )
    await state.set_state(AdminStates.removing_balance)

    current_balance = await db.get_balance(target_user_id)

    text = (
        f"➖ **СПИСАТЬ ГЕНЕРАЦИИ**\n\n"
        f"👤 Пользователь: `{target_user_id}`\n"
        f"💎 Текущий баланс: **{current_balance}**\n\n"
        f"Сколько генераций списать? (максимум {current_balance}):\n"
        "Отправьте число:"
    )

    try:
        # ✅ РЕДАКТИРУЕМ существующее сообщение
        await callback.message.edit_text(
            text=text,
            reply_markup=get_balance_cancel_keyboard(),
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'balance_remove')
        logger.info(f"🔄 Admin {user_id} started removing balance for user {target_user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при показе экрана списания: {e}")

    await callback.answer()


@router.message(AdminStates.removing_balance)
async def balance_remove_amount(message: Message, state: FSMContext, admins: list[int]):
    """Обработка количества для списания"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    # ✅ КРИТИЧНО: УДАЛЯЕМ сообщение админа СРАЗУ
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")

    # Валидация
    try:
        amount = int(message.text.strip())
        if amount <= 0 or amount > 99999:
            raise ValueError("Out of range")
    except ValueError:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info and menu_info['menu_message_id']:
            error_text = (
                "❌ **ОШИБКА: НЕВЕРНОЕ ЗНАЧЕНИЕ**\n\n"
                "Пожалуйста, отправьте корректное число:\n"
                "• Минимум: **1**\n"
                "• Максимум: **99999**"
            )
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_info['menu_message_id'],
                    text=error_text,
                    reply_markup=get_balance_cancel_keyboard(),
                    parse_mode="Markdown"
                )
                await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_remove_error')
            except Exception as e:
                logger.error(f"❌ Ошибка при показе ошибки: {e}")
        return

    # Проверка достаточности средств
    data = await state.get_data()
    target_user_id = data['target_user_id']
    current_balance = await db.get_balance(target_user_id)

    if amount > current_balance:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info and menu_info['menu_message_id']:
            error_text = (
                f"❌ **ОШИБКА: НЕДОСТАТОЧНО СРЕДСТВ**\n\n"
                f"👤 Пользователь: `{target_user_id}`\n"
                f"💎 Текущий баланс: **{current_balance}**\n"
                f"❌ Невозможно списать **{amount}** генераций\n\n"
                f"Максимум доступно: **{current_balance}**"
            )
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_info['menu_message_id'],
                    text=error_text,
                    reply_markup=get_balance_cancel_keyboard(),
                    parse_mode="Markdown"
                )
                await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_insufficient')
            except Exception as e:
                logger.error(f"❌ Ошибка при показе ошибки недостатка средств: {e}")
        return

    await state.update_data(amount=amount)

    new_balance = current_balance - amount

    text = (
        "✅ **ПОДТВЕРЖДЕНИЕ: СПИСАТЬ ГЕНЕРАЦИИ**\n\n"
        f"👤 Пользователь: `{target_user_id}`\n"
        f"💎 Текущий баланс: **{current_balance}**\n"
        f"➖ Списать: **{amount}**\n"
        f"📊 Новый баланс: **{new_balance}**\n\n"
        "Подтвердите операцию:"
    )

    # ✅ Редактируем ЕДИНОЕ меню
    menu_info = await db.get_chat_menu(chat_id)
    if menu_info and menu_info['menu_message_id']:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_info['menu_message_id'],
                text=text,
                reply_markup=get_balance_confirm_keyboard(),
                parse_mode="Markdown"
            )
            await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_confirm_remove')
            logger.info(f"✅ Admin {user_id} entered amount {amount} for removing")
        except Exception as e:
            logger.error(f"❌ Ошибка при показе подтверждения: {e}")

    await db.log_activity(user_id, 'balance_remove_amount_input')


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: УСТАНОВКА =====

@router.callback_query(F.data.startswith("balance_set_"))
async def balance_set_start(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Начало процесса установки баланса"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[2])

    # ✅ Сохраняем menu_message_id
    menu_message_id = callback.message.message_id

    await state.update_data(
        balance_operation='set',
        target_user_id=target_user_id,
        menu_message_id=menu_message_id
    )
    await state.set_state(AdminStates.setting_balance)

    current_balance = await db.get_balance(target_user_id)

    text = (
        f"🔄 **УСТАНОВИТЬ БАЛАНС**\n\n"
        f"👤 Пользователь: `{target_user_id}`\n"
        f"💎 Текущий баланс: **{current_balance}**\n\n"
        "На какое значение установить баланс?\n"
        "Отправьте число (0-999999):"
    )

    try:
        # ✅ РЕДАКТИРУЕМ существующее сообщение
        await callback.message.edit_text(
            text=text,
            reply_markup=get_balance_cancel_keyboard(),
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'balance_set')
        logger.info(f"🔄 Admin {user_id} started setting balance for user {target_user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при показе экрана установки: {e}")

    await callback.answer()


@router.message(AdminStates.setting_balance)
async def balance_set_amount(message: Message, state: FSMContext, admins: list[int]):
    """Обработка нового значения баланса"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    # ✅ КРИТИЧНО: УДАЛЯЕМ сообщение админа СРАЗУ
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")

    # Валидация
    try:
        new_balance = int(message.text.strip())
        if new_balance < 0 or new_balance > 999999:
            raise ValueError("Out of range")
    except ValueError:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info and menu_info['menu_message_id']:
            error_text = (
                "❌ **ОШИБКА: НЕВЕРНОЕ ЗНАЧЕНИЕ**\n\n"
                "Пожалуйста, отправьте корректное число:\n"
                "• Минимум: **0**\n"
                "• Максимум: **999999**"
            )
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_info['menu_message_id'],
                    text=error_text,
                    reply_markup=get_balance_cancel_keyboard(),
                    parse_mode="Markdown"
                )
                await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_set_error')
            except Exception as e:
                logger.error(f"❌ Ошибка при показе ошибки: {e}")
        return

    await state.update_data(new_balance_value=new_balance)

    data = await state.get_data()
    target_user_id = data['target_user_id']
    current_balance = await db.get_balance(target_user_id)

    text = (
        "✅ **ПОДТВЕРЖДЕНИЕ: УСТАНОВИТЬ БАЛАНС**\n\n"
        f"👤 Пользователь: `{target_user_id}`\n"
        f"💎 Текущий баланс: **{current_balance}**\n"
        f"🔄 Установить: **{new_balance}**\n\n"
        "Подтвердите операцию:"
    )

    # ✅ Редактируем ЕДИНОЕ меню
    menu_info = await db.get_chat_menu(chat_id)
    if menu_info and menu_info['menu_message_id']:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_info['menu_message_id'],
                text=text,
                reply_markup=get_balance_confirm_keyboard(),
                parse_mode="Markdown"
            )
            await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_confirm_set')
            logger.info(f"✅ Admin {user_id} entered new balance {new_balance} for setting")
        except Exception as e:
            logger.error(f"❌ Ошибка при показе подтверждения: {e}")

    await db.log_activity(user_id, 'balance_set_amount_input')


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: ПОДТВЕРЖДЕНИЕ И ВЫПОЛНЕНИЕ =====

@router.callback_query(F.data == "balance_confirm_operation")
async def balance_confirm(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Подтверждение и выполнение операции с балансом"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    data = await state.get_data()
    operation = data.get('balance_operation')
    target_user_id = data.get('target_user_id')
    amount = data.get('amount')
    new_balance_value = data.get('new_balance_value')

    if not operation or not target_user_id:
        await callback.answer("❌ Ошибка: контекст операции потерян.", show_alert=True)
        return

    current_balance = await db.get_balance(target_user_id)

    # ===== ДОБАВЛЕНИЕ =====
    if operation == 'add':
        new_balance = current_balance + amount
        success = await db.add_tokens(target_user_id, amount)

        if success:
            text = (
                "✅ **УСПЕШНО ДОБАВЛЕНО!**\n\n"
                f"👤 Пользователь: `{target_user_id}`\n"
                f"➕ Добавлено: **{amount}** генераций\n"
                f"📊 Новый баланс: **{new_balance}**\n\n"
                "Операция выполнена ✓"
            )
            logger.info(f"✅ Admin {user_id} added {amount} tokens to user {target_user_id}")
        else:
            text = "❌ **ОШИБКА** при добавлении генераций. Попробуйте позже."

    # ===== СПИСАНИЕ =====
    elif operation == 'remove':
        if amount > current_balance:
            text = (
                f"❌ **ОШИБКА: НЕДОСТАТОЧНО СРЕДСТВ**\n\n"
                f"Баланс изменился. Текущий баланс: **{current_balance}**"
            )
        else:
            success = await db.add_tokens(target_user_id, -amount)

            if success:
                new_balance = current_balance - amount
                text = (
                    "✅ **УСПЕШНО СПИСАНО!**\n\n"
                    f"👤 Пользователь: `{target_user_id}`\n"
                    f"➖ Списано: **{amount}** генераций\n"
                    f"📊 Новый баланс: **{new_balance}**\n\n"
                    "Операция выполнена ✓"
                )
                logger.info(f"✅ Admin {user_id} removed {amount} tokens from user {target_user_id}")
            else:
                text = "❌ **ОШИБКА** при списании генераций. Попробуйте позже."

    # ===== УСТАНОВКА =====
    elif operation == 'set':
        diff = new_balance_value - current_balance
        success = await db.add_tokens(target_user_id, diff)

        if success:
            text = (
                "✅ **УСПЕШНО УСТАНОВЛЕНО!**\n\n"
                f"👤 Пользователь: `{target_user_id}`\n"
                f"🔄 Баланс установлен: **{new_balance_value}** генераций\n\n"
                "Операция выполнена ✓"
            )
            logger.info(f"✅ Admin {user_id} set balance for user {target_user_id} to {new_balance_value}")
        else:
            text = "❌ **ОШИБКА** при установке баланса. Попробуйте позже."

    else:
        text = "❌ **ОШИБКА**: неизвестная операция."

    # ✅ КРИТИЧНО: Сохраняем last_target_user_id для кнопки "Ещё одно управление"
    await state.update_data(last_target_user_id=target_user_id)

    # ✅ Показываем результат в ЕДИНОМ меню
    menu_info = await db.get_chat_menu(chat_id)
    if menu_info and menu_info['menu_message_id']:
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Ещё одно управление", callback_data="balance_more_management")],
                    [InlineKeyboardButton(text="⬅️ Назад в настройки", callback_data="admin_settings")]
                ]),
                parse_mode="Markdown"
            )
            await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'balance_result')
        except Exception as e:
            logger.error(f"❌ Ошибка при показе результата: {e}")

    # ✅ Очищаем состояние, но сохраняем menu_message_id и last_target_user_id
    await state.set_state(None)
    await state.update_data(
        menu_message_id=menu_info['menu_message_id'] if menu_info else None,
        last_target_user_id=target_user_id
    )

    await db.log_activity(user_id, f'balance_{operation}_confirmed')
    await callback.answer("✅ Операция выполнена!", show_alert=False)


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: ЕЩЁ ОДНО УПРАВЛЕНИЕ =====

@router.callback_query(F.data == "balance_more_management")
async def balance_more_management(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат к карточке выбранного пользователя для продолжения управления балансом"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # ✅ Получаем last_target_user_id из state
    data = await state.get_data()
    last_target_user_id = data.get('last_target_user_id')

    if not last_target_user_id:
        # Если потерялся контекст, возвращаем к вводу ID
        await callback.answer("⚠️ Контекст потерян. Введите ID пользователя заново.", show_alert=True)
        await settings_balance(callback, state, admins)
        return

    # ✅ Запрашиваем свежие данные пользователя из БД
    try:
        # Используем метод search_user для получения данных
        user_data = await db.search_user(str(last_target_user_id))

        if not user_data:
            await callback.answer("❌ Пользователь не найден в базе данных.", show_alert=True)
            await settings_balance(callback, state, admins)
            return

        username = user_data.get('username') or "Не указан"
        balance = user_data.get('balance', 0)
        total_generations = user_data.get('total_generations', 0)
        successful_payments = user_data.get('successful_payments', 0)

        # ✅ Обновляем state
        await state.set_state(None)
        await state.update_data(
            target_user_id=last_target_user_id,
            menu_message_id=callback.message.message_id,
            last_target_user_id=last_target_user_id
        )

        # Формируем текст карточки
        username_clean = username.replace('_', '\\_').replace('*', '\\*')
        tg_link = f"[{username_clean}](tg://user?id={last_target_user_id})"

        result_text = (
            "✅ **ПОЛЬЗОВАТЕЛЬ**\n\n"
            f"🆔 **ID:** `{last_target_user_id}`\n"
            f"👤 **Username:** {tg_link}\n"
            f"💎 **Текущий баланс:** **{balance}** генераций\n"
            f"📊 **Всего генераций:** {total_generations}\n"
            f"💳 **Успешных платежей:** {successful_payments}\n\n"
            "**Выберите действие:**"
        )

        # ✅ Редактируем ЕДИНОЕ меню
        await callback.message.edit_text(
            text=result_text,
            reply_markup=get_balance_main_keyboard(last_target_user_id),
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'balance_user_found')

        logger.info(f"✅ Admin {user_id} returned to manage user {last_target_user_id}")
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при возврате к карточке пользователя: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


# ===== УПРАВЛЕНИЕ БАЛАНСОМ: ОТМЕНА =====

@router.callback_query(F.data == "balance_cancel_operation")
async def balance_cancel(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Отмена операции с балансом"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # ✅ Возвращаемся в меню управления балансом
    await state.set_state(None)
    await settings_balance(callback, state, admins)
    await db.log_activity(user_id, 'balance_cancelled')


# --- КОНЕЦ ИСПРАВЛЕННОГО БЛОКА ---


# ===== ДРУГИЕ РАЗДЕЛЫ НАСТРОЕК (БЕЗ ИЗМЕНЕНИЙ) =====

@router.callback_query(F.data == "settings_packages")
async def settings_packages(callback: CallbackQuery, admins: list[int]):
    from keyboards.admin_kb import get_back_to_settings
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await callback.message.edit_text(
        "📦 **Настройка пакетов**\n\n_В разработке..._",
        reply_markup=get_back_to_settings(),
        parse_mode="Markdown"
    )
    await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'settings_packages')
    await callback.answer()


@router.callback_query(F.data == "settings_discounts")
async def settings_discounts(callback: CallbackQuery, admins: list[int]):
    from keyboards.admin_kb import get_back_to_settings
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await callback.message.edit_text(
        "🎁 **Скидки и акции**\n\n_В разработке..._",
        reply_markup=get_back_to_settings(),
        parse_mode="Markdown"
    )
    await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'settings_discounts')
    await callback.answer()


@router.callback_query(F.data == "settings_bonuses")
async def settings_bonuses(callback: CallbackQuery, admins: list[int]):
    from keyboards.admin_kb import get_back_to_settings
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await callback.message.edit_text(
        "🎯 **Бонусные настройки**\n\n_В разработке..._",
        reply_markup=get_back_to_settings(),
        parse_mode="Markdown"
    )
    await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'settings_bonuses')
    await callback.answer()


@router.callback_query(F.data == "settings_referral")
async def settings_referral(callback: CallbackQuery, admins: list[int]):
    from keyboards.admin_kb import get_back_to_settings
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await callback.message.edit_text(
        "👥 **Реферальная система**\n\n_В разработке..._",
        reply_markup=get_back_to_settings(),
        parse_mode="Markdown"
    )
    await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'settings_referral')
    await callback.answer()


@router.callback_query(F.data == "settings_system")
async def settings_system(callback: CallbackQuery, admins: list[int]):
    from keyboards.admin_kb import get_back_to_settings
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await callback.message.edit_text(
        "🔧 **Системные настройки**\n\n_В разработке..._",
        reply_markup=get_back_to_settings(),
        parse_mode="Markdown"
    )
    await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'settings_system')
    await callback.answer()
