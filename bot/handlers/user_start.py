# bot/handlers/user_start.py
# --- ИСПРАВЛЕНИЯ ВЕРСИИ ----
# [2025-11-23 19:00 MSK] Реализована система единого меню:
# - Сохранение menu_message_id при старте
# - Использование edit_menu для всех переходов
# - Добавлен хэндлер main_menu для возврата
# [2025-11-29 21:35 MSK] ИСПРАВЛЕНИЕ: Автоматическое создание пользователя в show_profile
# ---

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Импорты наших модулей
from database.db import db
from states.fsm import CreationStates
from keyboards.inline import get_main_menu_keyboard, get_profile_keyboard, get_payment_keyboard
from utils.texts import START_TEXT, PROFILE_TEXT, UPLOAD_PHOTO_TEXT
from utils.navigation import edit_menu, show_main_menu

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, admins: list[int]):
    """
    Обрабатывает команду /start.
    Создает пользователя в базе и показывает главное меню.
    ВАЖНО: Сохраняет menu_message_id для дальнейшей навигации.
    """
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username

    # Создаем пользователя в базе (если его нет)
    await db.create_user(user_id, username)

    # Отправляем главное меню и СОХРАНЯЕМ его ID
    menu_msg = await message.answer(
        START_TEXT,
        reply_markup=get_main_menu_keyboard(is_admin=user_id in admins),
        parse_mode="Markdown"
    )

    # КРИТИЧЕСКОЕ: сохраняем ID главного меню
    await state.update_data(menu_message_id=menu_msg.message_id)


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Return to main menu from any screen"""
    await show_main_menu(callback, state, admins)
    await callback.answer()


@router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    """
    Показывает профиль пользователя (баланс, дата регистрации).
    РЕДАКТИРУЕТ существующее меню.
    ИСПРАВЛЕНИЕ: Автоматически создаёт пользователя, если его нет в БД.
    """
    user_id = callback.from_user.id

    # Получаем данные пользователя из БД
    user_data = await db.get_user_data(user_id)

    # ===== ИСПРАВЛЕНИЕ: Автоматическое создание пользователя =====
    if not user_data:
        # Пользователя нет в БД - создаём автоматически
        username = callback.from_user.username
        await db.create_user(user_id, username)
        # Получаем данные заново
        user_data = await db.get_user_data(user_id)
    # ==============================================================

    if user_data:
        balance = user_data.get('balance', 0)
        created_at = user_data.get('created_at', 'неизвестно')

        # Используем edit_menu вместо edit_text
        await edit_menu(
            callback=callback,
            state=state,
            text=PROFILE_TEXT.format(
                user_id=user_id,
                username=user_data.get('username', 'Не указан'),
                balance=balance,
                reg_date=created_at
            ),
            keyboard=get_profile_keyboard()
        )
    else:
        # Это не должно произойти после автоматического создания
        await callback.answer("❌ Ошибка создания профиля. Попробуйте /start", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "buy_generations")
async def buy_generations_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки 'Купить генерации' в профиле.
    Переводит в меню выбора пакета.
    """
    await edit_menu(
        callback=callback,
        state=state,
        text="💰 **Выберите пакет генераций:**\n\nПосле оплаты баланс автоматически пополнится.",
        keyboard=get_payment_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс создания дизайна.
    Переводит в состояние ожидания фото и РЕДАКТИРУЕТ меню.
    """
    # Очищаем данные о предыдущем фото (если было)
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    # Очищаем все данные, кроме menu_message_id
    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    await state.set_state(CreationStates.waiting_for_photo)

    # Редактируем меню на инструкцию загрузки
    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=None  # Убираем кнопки во время ожидания фото
    )
    await callback.answer()
