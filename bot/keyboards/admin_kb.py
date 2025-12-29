# bot/keyboards/admin_kb.py
# --- ОБНОВЛЕН: 2025-12-09 16:24 - Удалены дублирующиеся функции клавиатур для баланса ---
# [2025-12-09 16:24] Были дублированы: get_balance_main_keyboard, get_balance_confirm_keyboard, get_balance_cancel_keyboard
# [2025-12-09 16:24] Удалена ненужная функция: get_balance_search_type_keyboard (неправильный подход)
# [2025-12-09 16:24] Оставлены только первые определения каждой функции

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_menu():
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()

    builder.button(text="📊 Статистика системы", callback_data="admin_stats")
    builder.button(text="👥 Все пользователи", callback_data="admin_users")
    builder.button(text="🔍 Найти пользователя", callback_data="admin_find_user")
    builder.button(text="💰 История платежей", callback_data="admin_payments")
    builder.button(text="🔔 Уведомления", callback_data="admin_notifications")
    builder.button(text="🌐 Источники трафика", callback_data="admin_sources")
    builder.button(text="⚙️ Настройки", callback_data="admin_settings")
    builder.button(text="🏠 Главное меню бота", callback_data="main_menu")

    builder.adjust(2)  # ПО 2 КНОПКИ В РЯД

    return builder.as_markup()


def get_admin_settings_menu():
    """Меню настроек: 6 кнопок по 2 в ряд + большая кнопка назад"""
    builder = InlineKeyboardBuilder()

    builder.button(text="💰 Управление балансом", callback_data="settings_balance")
    builder.button(text="📦 Настройка пакетов", callback_data="settings_packages")
    builder.button(text="🎁 Скидки и акции", callback_data="settings_discounts")
    builder.button(text="🎯 Бонусные настройки", callback_data="settings_bonuses")
    builder.button(text="👥 Реферальная система", callback_data="settings_referral")
    builder.button(text="🔧 Настройки", callback_data="settings_system")
    builder.button(text="⬅️ Назад", callback_data="admin_main")

    builder.adjust(2, 2, 2, 1)  # ВОТ ПРАВИЛЬНАЯ НАСТРОЙКА!

    return builder.as_markup()


def get_back_to_admin_menu() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ-меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад ", callback_data="admin_main")]
    ])
    return keyboard


def get_back_to_settings():
    """Кнопка возврата в меню настроек"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="admin_settings")
    return builder.as_markup()


def get_users_list_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавиатура списка пользователей с пагинацией"""
    buttons = []

    # Кнопки пагинации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"admin_users_page_{current_page - 1}")
        )

    nav_buttons.append(
        InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop")
    )

    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"admin_users_page_{current_page + 1}")
        )

    buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад ", callback_data="admin_main")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_balance_main_keyboard(user_id: int):
    """Клавиатура выбора действия для управления балансом"""
    builder = InlineKeyboardBuilder()

    builder.button(text="➕ Добавить генерации", callback_data=f"balance_add_{user_id}")
    builder.button(text="➖ Списать генерации", callback_data=f"balance_remove_{user_id}")
    builder.button(text="🔄 Установить баланс", callback_data=f"balance_set_{user_id}")
    builder.button(text="🔍 Найти другого", callback_data="settings_balance")
    builder.button(text="⬅️ Назад в настройки", callback_data="admin_settings")

    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_balance_confirm_keyboard():
    """Клавиатура подтверждения операции с балансом"""
    builder = InlineKeyboardBuilder()

    builder.button(text="✅ Подтвердить", callback_data="balance_confirm_operation")
    builder.button(text="❌ Отмена", callback_data="balance_cancel_operation")

    builder.adjust(2)
    return builder.as_markup()


def get_balance_cancel_keyboard():
    """Клавиатура для отмены ввода"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Отмена", callback_data="balance_more_management") # balance_more_management
    return builder.as_markup()                               # settings_balance
