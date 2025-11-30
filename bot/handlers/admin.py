# handlers/admin.py

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import db
from keyboards.admin_kb import (
    get_admin_main_menu,
    get_back_to_admin_menu,
    get_users_list_keyboard
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
    Срабатывает при нажатии кнопки "⚙️ Админ-панель".
    """
    user_id = callback.from_user.id

    # Проверка прав админа
    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Получаем статистику
    total_users = await db.get_total_users_count()
    total_revenue = await db.get_total_revenue()

    # Генерации и активность - заглушки (таблицы нет)
    total_generations = "В разработке"
    active_today = "В разработке"

    # Формируем текст
    admin_text = (
        "👑 **АДМИН-ПАНЕЛЬ**\n\n"
        f"📊 **Общая статистика:**\n"
        f"• Всего пользователей: **{total_users}**\n"
        f"• Всего генераций: **{total_generations}**\n"
        f"• Общая выручка: **{total_revenue} руб.**\n"
        f"• Активных сегодня: **{active_today}**\n\n"
        "Выберите действие:"
    )

    # Редактируем сообщение
    try:
        await callback.message.edit_text(
            text=admin_text,
            reply_markup=get_admin_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения админ-панели: {e}")
        await callback.message.answer(
            text=admin_text,
            reply_markup=get_admin_main_menu(),
            parse_mode="Markdown"
        )

    await callback.answer()


# ===== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ АДМИНКИ =====
@router.callback_query(F.data == "admin_main")
async def back_to_admin_main(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат в главное меню админ-панели"""
    await show_admin_panel(callback, state, admins)


# ===== ДЕТАЛЬНАЯ СТАТИСТИКА =====
@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery, admins: list[int]):
    """Показать детальную статистику системы"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Получаем статистику
    total_users = await db.get_total_users_count()
    new_today = await db.get_new_users_count(days=1)
    new_week = await db.get_new_users_count(days=7)

    total_revenue = await db.get_total_revenue()
    revenue_today = await db.get_revenue_by_period(days=1)
    revenue_week = await db.get_revenue_by_period(days=7)
    successful_payments = await db.get_successful_payments_count()
    average_payment = await db.get_average_payment()

    # Заглушки для недоступных данных
    total_generations = "Скоро"
    generations_today = "Скоро"
    generations_week = "Скоро"
    conversion_rate = "Скоро"
    active_today = "Скоро"
    active_week = "Скоро"
    popular_rooms = "Отслеживание в разработке"
    popular_styles = "Отслеживание в разработке"

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
        "💰 **Финансы:**\n"
        f"• Общая выручка: **{total_revenue} руб.**\n"
        f"• Выручка за сегодня: **{revenue_today} руб.**\n"
        f"• Выручка за неделю: **{revenue_week} руб.**\n"
        f"• Успешных платежей: **{successful_payments}**\n"
        f"• Средний чек: **{average_payment} руб.**\n\n"
        "🏠 **Популярные комнаты:**\n"
        f"{popular_rooms}\n\n"
        "🎨 **Популярные стили:**\n"
        f"{popular_styles}"
    )

    try:
        await callback.message.edit_text(
            text=stats_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
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

    # Извлекаем номер страницы
    page = int(callback.data.split("_")[-1])
    await show_users_page(callback, page=page, admins=admins)


async def show_users_page(callback: CallbackQuery, page: int, admins: list[int]):
    """Показать конкретную страницу пользователей"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Получаем пользователей для страницы
    users, total_pages = await db.get_all_users_paginated(page=page, per_page=10)

    if not users:
        await callback.answer("📭 Пользователей нет.", show_alert=True)
        return

    # Формируем текст
    users_text = f"👥 **СПИСОК ПОЛЬЗОВАТЕЛЕЙ** (стр. {page}/{total_pages})\n\n"
    for idx, user in enumerate(users, start=1):
        user_id_str = user['user_id']
        username = user['username']
        balance = user['balance']

        # ===== ИСПРАВЛЕНИЕ: Экранируем username =====
        # Убираем @ и экранируем спецсимволы Markdown
        username_clean = username.replace('@', '').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(
            ']', '\\]').replace('`', '\\`')

        users_text += f"{idx}. ID: `{user_id_str}` | {username_clean} | 💰 {balance}\n"

    try:
        await callback.message.edit_text(
            text=users_text,
            reply_markup=get_users_list_keyboard(page, total_pages),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка показа пользователей: {e}")

    await callback.answer()


# ===== ПОИСК ПОЛЬЗОВАТЕЛЯ (ЗАГЛУШКА) =====
@router.callback_query(F.data == "admin_find_user")
async def find_user_stub(callback: CallbackQuery, admins: list[int]):
    """Заглушка для поиска пользователя"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    await callback.answer("🔍 Функция поиска в разработке. Используйте /balance <user_id>", show_alert=True)


# ===== ИСТОРИЯ ПЛАТЕЖЕЙ =====
@router.callback_query(F.data == "admin_payments")
async def show_payments_history(callback: CallbackQuery, admins: list[int]):
    """Показать историю платежей"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Получаем последние 20 платежей
    payments = await db.get_all_payments(limit=20)

    if not payments:
        await callback.answer("📭 Платежей пока нет.", show_alert=True)
        return

    # Формируем текст
    payments_text = "💰 **ИСТОРИЯ ПЛАТЕЖЕЙ** (последние 20)\n\n"
    for idx, payment in enumerate(payments, start=1):
        status_emoji = "✅" if payment['status'] == 'succeeded' else "⏳"
        # Экранируем username
        username_clean = payment['username'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']',
                                                                                                                 '\\]').replace(
            '`', '\\`')

        payments_text += (
            f"{idx}. {status_emoji} `{payment['user_id']}` | "
            f"{username_clean} | "
            f"**{payment['amount']} руб.** | "
            f"{payment['tokens']} токенов\n"
        )

    try:
        await callback.message.edit_text(
            text=payments_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка показа платежей: {e}")

    await callback.answer()


# ===== КОМАНДЫ (ОСТАВЛЯЕМ КАК БЫЛИ) =====

@router.message(Command("add_tokens"))
async def cmd_add_tokens(message: Message, admins: list[int]):
    """
    Добавить токены пользователю
    Использование: /add_tokens <user_id> <количество>
    Пример: /add_tokens 123456789 10
    """
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
    """
    Проверить баланс пользователя
    Использование: /balance <user_id>
    Пример: /balance 123456789
    """
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
    """
    Показать список последних 10 пользователей
    Использование: /users
    """
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

            # Экранируем username
            username_clean = username.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']',
                                                                                                          '\\]').replace(
                '`', '\\`')

            text += f"{idx}. ID: `{user_id_str}` | {username_clean} | 💰 {balance}\n"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in list_users: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")
