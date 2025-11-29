# creation

import asyncio
import logging

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

# Импортируем свои модули
from database.db import db
from keyboards.inline import (
    get_room_keyboard,
    get_style_keyboard,
    get_payment_keyboard,
    get_post_generation_keyboard,
    get_profile_keyboard,
    get_main_menu_keyboard
)
from services.replicate_api import generate_image
from states.fsm import CreationStates
from utils.texts import (
    CHOOSE_STYLE_TEXT,
    PHOTO_SAVED_TEXT,
    NO_BALANCE_TEXT,
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    PROFILE_TEXT,
    MAIN_MENU_TEXT
)

logger = logging.getLogger(__name__)
router = Router()

async def show_single_menu(sender, state: FSMContext, text: str, keyboard, parse_mode: str = "Markdown"):
    data = await state.get_data()
    old_menu_id = data.get('menu_message_id')
    if old_menu_id:
        try:
            await sender.bot.edit_message_text(
                chat_id=sender.chat.id,
                message_id=old_menu_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            await state.update_data(menu_message_id=old_menu_id)
            return old_menu_id
        except Exception:
            pass
    menu = await sender.answer(text, reply_markup=keyboard, parse_mode=parse_mode)
    await state.update_data(menu_message_id=menu.message_id)
    if old_menu_id and old_menu_id != menu.message_id:
        try:
            await sender.bot.delete_message(chat_id=sender.chat.id, message_id=old_menu_id)
        except Exception:
            pass
    return menu.message_id

# ===== ГЛАВНЫЙ МЕНЮ И СТАРТ =====
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_single_menu(callback.message, state, MAIN_MENU_TEXT, get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(CreationStates.waiting_for_photo)
    await show_single_menu(callback.message, state, UPLOAD_PHOTO_TEXT, None)
    await callback.answer()

# ===== ХЭНДЛЕР ОБРАБОТКИ ФОТО =====
@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    user_id = message.from_user.id
    if message.media_group_id:
        data = await state.get_data()
        cached_group_id = data.get('media_group_id')
        try: await message.delete()
        except: pass
        if cached_group_id != message.media_group_id:
            await state.update_data(media_group_id=message.media_group_id)
            msg = await message.answer(TOO_MANY_PHOTOS_TEXT)
            await asyncio.sleep(3)
            try: await msg.delete()
            except: pass
        return
    await state.update_data(media_group_id=None)
    photo_file_id = message.photo[-1].file_id
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await show_single_menu(message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return
    await state.update_data(photo_id=photo_file_id)
    await state.set_state(CreationStates.choose_room)
    menu_msg = await message.answer(
        PHOTO_SAVED_TEXT,
        reply_markup=get_room_keyboard()
    )
    await state.update_data(menu_message_id=menu_msg.message_id)

# ===== ВЫБОР КОМНАТЫ =====
@router.callback_query(CreationStates.choose_room, F.data.startswith("room_"))
async def room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    room = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await show_single_menu(callback.message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return
    await state.update_data(room=room)
    await state.set_state(CreationStates.choose_style)
    await show_single_menu(callback.message, state, CHOOSE_STYLE_TEXT, get_style_keyboard())
    await callback.answer()

# ===== ВЫБОР СТИЛЯ/ВАРИАНТА И ГЕНЕРАЦИЯ =====
@router.callback_query(CreationStates.choose_style, F.data == "back_to_room")
async def back_to_room_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.choose_room)
    await show_single_menu(callback.message, state, PHOTO_SAVED_TEXT, get_room_keyboard())
    await callback.answer()


@router.callback_query(CreationStates.choose_style, F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await show_single_menu(callback.message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')
    if user_id not in admins:
        await db.decrease_balance(user_id)
    # Сохраняем ID сообщения о прогрессе
    progress_msg_id = await show_single_menu(callback.message, state, "⏳ Генерирую новый дизайн...", None)
    await callback.answer()
    result_image_url = await generate_image(photo_id, room, style, bot_token)
    # Удаляем сообщение о прогрессе после генерации
    if progress_msg_id:
        try:
            await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=progress_msg_id)
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение о прогрессе: {e}")

    if result_image_url:
        await callback.message.answer_photo(
            photo=result_image_url,
            caption=f"✨ Ваш новый дизайн в стиле *{style.replace('_', ' ').title()}*!",
            parse_mode="Markdown"
        )
        menu = await callback.message.answer(
            "Что дальше? "
            "1. Вы можете сделать повторный дизайн этого же стиля. "
            "Каждый раз создается новый дизайн помещения!  "
            "2. Вы можете другой стиль дизайна этого помещения.",
            reply_markup=get_post_generation_keyboard()
        )
        await state.update_data(menu_message_id=menu.message_id)
    else:
        await show_single_menu(callback.message, state, "Ошибка генерации. Попробуйте еще раз.",
                               get_main_menu_keyboard())


@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.choose_style)
    await show_single_menu(callback.message, state, CHOOSE_STYLE_TEXT, get_style_keyboard())
    await callback.answer()

# ===== ДУБЛИКАТ УДАЛЁН =====
# Хэндлер show_profile теперь только в handlers/user_start.py

@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    try:
        await message.delete()
    except:
        pass

@router.message(CreationStates.choose_room)
async def block_messages_in_choose_room(message: Message, state: FSMContext):
    try:
        await message.delete()
    except:
        pass
    await state.clear()
    await state.set_state(CreationStates.waiting_for_photo)
    msg = await message.answer("🚫 Используйте кнопки! Начните заново, отправив фото.", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except:
        pass

@router.message(F.video | F.video_note | F.document | F.sticker | F.audio | F.voice | F.animation)
async def block_media_types(message: Message):
    try:
        await message.delete()
    except:
        pass

@router.message(F.photo)
async def block_unexpected_photos(message: Message, state: FSMContext):
    try:
        await message.delete()
    except:
        pass
    msg = await message.answer("🚫 Используйте кнопки меню!")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except:
        pass

@router.message(F.text)
async def block_all_text_messages(message: Message):
    try:
        await message.delete()
    except:
        pass
