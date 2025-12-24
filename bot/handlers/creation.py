# bot/handlers/creation.py
# --- ОБНОВЛЕН: 2025-12-07 11:09 - Внедрена система единого меню с использованием edit_menu из navigation.py ---
# [2025-12-07 11:09] КРИТИЧНО: Удалена дублирующая функция show_single_menu() - используется edit_menu() из utils/navigation.py
# [2025-12-07 11:09] Добавлены screen_code во все вызовы edit_menu()
# [2025-12-07 11:09] Заменён go_to_main_menu на использование show_main_menu() из navigation.py
# [2025-12-07 11:09] Все переходы используют единую систему навигации
# [2025-12-06] Фиксы разметки Markdown/HTML, безопасные подписи
# --- ОБНОВЛЕНО: 2025-12-23 - Интегрирована Smart Fallback система (KIE.AI + Replicate) ---
# [2025-12-23 11:33] Заменены вызовы генерации на smart_* функции из api_fallback.py
# [2025-12-23 11:33] Сохранена 100% совместимость с именами обработчиков кнопок
# [2025-12-23 11:33] Добавлена логика fallback: KIE.AI -> Replicate

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.exceptions import TelegramBadRequest

from database.db import db

from keyboards.inline import (
    get_room_keyboard,
    get_style_keyboard,
    get_payment_keyboard,
    get_post_generation_keyboard,
    get_upload_photo_keyboard,
    get_what_is_in_photo_keyboard  # ДОБАВИТЬ ЭТУ СТРОКУ
)

# ОБНОВЛЕНО: 2025-12-23 - Использование Smart Fallback системы
from services.api_fallback import (
    smart_generate_interior,
    smart_generate_with_text,
    smart_clear_space,
)

from states.fsm import CreationStates

from utils.texts import (
    CHOOSE_STYLE_TEXT,
    PHOTO_SAVED_TEXT,
    NO_BALANCE_TEXT,
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    WHAT_IS_IN_PHOTO_TEXT,  # ДОБАВИТЬ
    EXTERIOR_HOUSE_PROMPT_TEXT,  # ДОБАВИТЬ
    EXTERIOR_PLOT_PROMPT_TEXT,  # ДОБАВИТЬ
    ROOM_DESCRIPTION_PROMPT_TEXT  # ДОБАВИТЬ
)

from utils.navigation import edit_menu, show_main_menu

logger = logging.getLogger(__name__)
router = Router()


# ===== ГЛАВНЫЙ МЕНЮ И СТАРТ =====
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат в главное меню - используем show_main_menu из navigation.py"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'main_menu')

    await show_main_menu(callback, state, admins)
    await callback.answer()


@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    """Начало создания дизайна"""
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'create_design')

    # Сохраняем menu_message_id перед очисткой
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()

    # Восстанавливаем menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    await state.set_state(CreationStates.waiting_for_photo)

    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=get_upload_photo_keyboard(),
        screen_code='upload_photo'
    )
    await callback.answer()


# ===== ХЭНДЛЕР ОБРАБОТКИ ФОТО =====
@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    """Обработка загруженного фото"""
    user_id = message.from_user.id
    await db.log_activity(user_id, 'photo_upload')

    # Блок альбомов
    if message.media_group_id:
        data = await state.get_data()
        cached_group_id = data.get('media_group_id')
        try:
            await message.delete()
        except Exception:
            pass
        if cached_group_id != message.media_group_id:
            await state.update_data(media_group_id=message.media_group_id)
            msg = await message.answer(TOO_MANY_PHOTOS_TEXT)
            await asyncio.sleep(3)
            try:
                await msg.delete()
            except Exception:
                pass
        return

    await state.update_data(media_group_id=None)
    photo_file_id = message.photo[-1].file_id

    # === ИЗМЕНЕНО 2025-12-08: Переход на экран "Что на фото" ===


    # Проверка баланса
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()

            # Отправляем новое сообщение вместо редактирования
            menu_msg = await message.answer(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard(),
                parse_mode="Markdown"
            )
            await state.update_data(menu_message_id=menu_msg.message_id)

            # Сохраняем в БД
            chat_id = message.chat.id
            await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'no_balance')
            return

    # Сохраняем фото и переходим к выбору комнаты
    # ИЗМЕНЕНО: Сохраняем фото и переходим к экрану "Что на фото"
    await state.update_data(photo_id=photo_file_id)

    # ОЧИЩАЕМ старые данные сцены (важно для повторного использования)
    await state.update_data(scene_type=None, room=None, style=None, exterior_prompt=None, room_description=None)

    await state.set_state(CreationStates.what_is_in_photo)  # НОВОЕ СОСТОЯНИЕ


    # Удаляем старое меню "Отправь фото"
    data = await state.get_data()
    old_menu_id = data.get('menu_message_id')
    if old_menu_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=old_menu_id
            )
        except Exception as e:
            logger.debug(f"Не удалось удалить старое меню: {e}")

    # Добавляем баланс к тексту
    from utils.helpers import add_balance_to_text
    text_with_balance = await add_balance_to_text(WHAT_IS_IN_PHOTO_TEXT, user_id)  # ИЗМЕНЕНО

    # Отправляем НОВОЕ сообщение с экраном "Что на фото"
    sent_msg = await message.answer(
        text=text_with_balance,
        reply_markup=get_what_is_in_photo_keyboard(),  # ИЗМЕНЕНО
        parse_mode="Markdown"
    )

    # Сохраняем ID нового меню в FSM + БД
    await state.update_data(menu_message_id=sent_msg.message_id)
    await db.save_chat_menu(message.chat.id, user_id, sent_msg.message_id, 'what_is_in_photo')  # ИЗМЕНЕНО


# ===== НОВЫЙ БЛОК: ОБРАБОТКА ЭКРАНА "ЧТО НА ФОТО" =====
# Дата добавления: 2025-12-08

@router.callback_query(CreationStates.what_is_in_photo, F.data.startswith("scene_"))
async def exterior_scene_chosen(callback: CallbackQuery, state: FSMContext):
    """
    НОВЫЙ ОБРАБОТЧИК: Выбран ЭКСТЕРЬЕР (дом или участок)

    Дата создания: 2025-12-08
    Переход к текстовому вводу пожеланий для экстерьера
    """
    scene_type = callback.data.replace("scene_", "")
    user_id = callback.from_user.id

    await db.log_activity(user_id, f'scene_{scene_type}')

    # Сохраняем тип сцены, очищаем room
    await state.update_data(scene_type=scene_type, room=None)
    await state.set_state(CreationStates.waiting_for_exterior_prompt)

    # Определяем текст в зависимости от типа экстерьера
    if scene_type == "house_exterior":
        prompt_text = EXTERIOR_HOUSE_PROMPT_TEXT
    else:  # plot_exterior
        prompt_text = EXTERIOR_PLOT_PROMPT_TEXT

    await edit_menu(
        callback=callback,
        state=state,
        text=prompt_text,
        keyboard=get_upload_photo_keyboard(),  # Только "Главное меню"
        screen_code='exterior_prompt'
    )
    await callback.answer()



# Выбрано другое помещение и текстовый ввод
@router.callback_query(CreationStates.what_is_in_photo, F.data.startswith("room_"))
async def interior_room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    НОВЫЙ ОБРАБОТЧИК: Выбран ИНТЕРЬЕР (комната)

    Дата создания: 2025-12-08
    Логика разветвления:
    - "Другое помещение" → текстовый ввод
    - Стандартные комнаты → выбор стиля
    """
    room = callback.data.replace("room_", "")
    user_id = callback.from_user.id

    await db.log_activity(user_id, f'room_{room}')

    # Проверка баланса
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await edit_menu(
                callback=callback,
                state=state,
                text=NO_BALANCE_TEXT,
                keyboard=get_payment_keyboard(),
                screen_code='no_balance'
            )
            return

    # ОСОБЫЙ СЛУЧАЙ: "Другое помещение"
    if room == "other":
        await state.update_data(scene_type="interior", room="other_room")
        await state.set_state(CreationStates.waiting_for_room_description)

        await edit_menu(
            callback=callback,
            state=state,
            text=ROOM_DESCRIPTION_PROMPT_TEXT,
            keyboard=get_upload_photo_keyboard(),
            screen_code='room_description'
        )
        await callback.answer()
        return

    # СТАНДАРТНЫЕ КОМНАТЫ → выбор стиля
    await state.update_data(scene_type="interior", room=room)
    await state.set_state(CreationStates.choose_style)

    await edit_menu(
        callback=callback,
        state=state,
        text=CHOOSE_STYLE_TEXT,
        keyboard=get_style_keyboard(),
        screen_code='choose_style'
    )
    await callback.answer()



# ===== НОВЫЙ БЛОК: ТЕКСТОВЫЙ ВВОД ДЛЯ ЭКСТЕРЬЕРА =====
# Дата добавления: 2025-12-08
@router.message(CreationStates.waiting_for_exterior_prompt, F.text)
async def exterior_prompt_received(message: Message, state: FSMContext, admins: list[int], bot_token: str):
    """
    НОВЫЙ ОБРАБОТЧИК: Получен текстовый промпт для экстерьера → запуск генерации

    Дата создания: 2025-12-08
    Использует новую функцию smart_generate_with_text() из api_fallback.py
    """
    user_prompt = message.text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Валидация
    if len(user_prompt) < 5:
        msg = await message.answer("⚠️ Опишите подробнее (минимум 5 символов)")
        await asyncio.sleep(3)
        try:
            await msg.delete()
            await message.delete()
        except:
            pass
        return

    # Получаем данные
    data = await state.get_data()
    photo_id = data.get('photo_id')
    scene_type = data.get('scene_type', 'custom')

    if not photo_id:
        await message.answer("⚠️ Сессия устарела. Загрузите фото заново.")
        await state.clear()
        return

    # Сохраняем промпт
    await state.update_data(exterior_prompt=user_prompt)

    # Удаляем текст пользователя
    try:
        await message.delete()
    except:
        pass

    # Проверка баланса
    is_admin = user_id in admins
    if not is_admin:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()

            data = await state.get_data()
            menu_id = data.get('menu_message_id')
            if menu_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_id,
                        text=NO_BALANCE_TEXT,
                        reply_markup=get_payment_keyboard(),
                        parse_mode="Markdown"
                    )
                except:
                    pass
            return

    if not is_admin:
        await db.decrease_balance(user_id)

    # Показываем прогресс
    data = await state.get_data()
    menu_id = data.get('menu_message_id')
    if menu_id:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_id,
                text=" ⏳ Создаю дизайн экстерьера...",
                #parse_mode="Markdown"
            )
        except:
            pass

    # ЗАПУСК ГЕНЕРАЦИИ С ТЕКСТОВЫМ ПРОМПТОМ (с использованием Smart Fallback)
    try:
        result_image_url = await smart_generate_with_text(
            photo_file_id=photo_id,
            user_prompt=user_prompt,
            bot_token=bot_token,
            scene_type=scene_type
        )
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"Критическая ошибка генерации экстерьера: {e}")
        result_image_url = None
        success = False

        # Уведомление админов
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_critical_errors")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Критическая ошибка генерации экстерьера:\nПользователь: `{user_id}`\n\n{str(e)[:500]}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    # Логирование
    await db.log_generation(
        user_id=user_id,
        room_type=scene_type,
        style_type='text_prompt',
        operation_type='exterior',
        success=success
    )

    if result_image_url:
        # Подготовка подписи
        scene_name = "дома" if scene_type == "house_exterior" else "участка"
        caption = (
            f"✨ Ваш новый дизайн {scene_name}!\n\n"
            f"Ваше задание: {user_prompt}"
        )


        # Отправка фото
        sent_photo_message = None  # ДОБАВЛЕНО 2025-12-08 15:47: для сохранения file_id
        try:
            sent_photo_message = await message.answer_photo(
                photo=result_image_url,
                caption=caption,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки фото помещения: {e}")

            # Fallback
            import aiohttp
            from aiogram.types import BufferedInputFile

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()
                            sent_photo_message = await message.answer_photo(  # ИЗМЕНЕНО: сохраняем результат
                                photo=BufferedInputFile(photo_data, filename="room.jpg"),
                                caption=caption,
                                parse_mode="HTML"
                            )
            except Exception as fallback_error:
                logger.error(f"❌ Fallback тоже не сработал: {fallback_error}")

                if menu_id:
                    try:
                        await message.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=menu_id,
                            text="❌ Ошибка при отправке изображения. Попробуйте еще раз.",
                            reply_markup=get_payment_keyboard(),
                            parse_mode="Markdown"
                        )
                    except:
                        pass
                return

        # ДОБАВЛЕНО 2025-12-08 15:47: Сохранение file_id сгенерированной картинки
        if sent_photo_message and sent_photo_message.photo:
            new_photo_id = sent_photo_message.photo[-1].file_id
            await state.update_data(photo_id=new_photo_id)
            logger.info(
                f"✅ Сохранён file_id отредактированного помещения: user_id={user_id}, file_id={new_photo_id[:30]}...")

        # Успех - создаём меню под картинкой



        if menu_id:
            try:
                await message.bot.delete_message(chat_id=chat_id, message_id=menu_id)
                await db.delete_chat_menu(chat_id)
            except:
                pass

        from utils.helpers import add_balance_to_text
        text_with_balance = await add_balance_to_text("✅ Выбери что дальше 👇", user_id)

        new_menu = await message.answer(
            text=text_with_balance,
            reply_markup=get_post_generation_keyboard(show_continue_editing=True),
            parse_mode="Markdown"
        )

        await state.update_data(menu_message_id=new_menu.message_id)
        await db.save_chat_menu(chat_id, user_id, new_menu.message_id, 'post_generation')

    else:
        # Ошибка генерации
        from keyboards.inline import get_main_menu_keyboard
        if menu_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_id,
                    text="❌ Ошибка генерации. Попробуйте еще раз.",
                    reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                    parse_mode="Markdown"
                )
            except:
                pass


# ===== НОВЫЙ БЛОК: ТЕКСТОВЫЙ ВВОД ДЛЯ "ДРУГОГО ПОМЕЩЕНИЯ" =====

@router.message(CreationStates.waiting_for_room_description, F.text)
async def room_description_received(message: Message, state: FSMContext, admins: list[int], bot_token: str):
    """
    ОБНОВЛЕНО: 2025-12-08 16:01
    [2025-12-08 16:01] Добавлено сохранение file_id после отправки фото
    [2025-12-23 11:33] Обновлено для использования smart_generate_with_text из api_fallback.py

    НОВЫЙ ОБРАБОТЧИК: Получено описание "Другого помещения"

    Дата создания: 2025-12-08
    Вариант реализации: Сразу генерация (без выбора стиля, стиль указан в описании)
    """
    room_description = message.text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Валидация
    if len(room_description) < 5:
        msg = await message.answer("⚠️ Опишите подробнее (минимум 5 символов)")
        await asyncio.sleep(3)
        try:
            await msg.delete()
            await message.delete()
        except:
            pass
        return

    # Получаем данные
    data = await state.get_data()
    photo_id = data.get('photo_id')

    if not photo_id:
        await message.answer("⚠️ Сессия устарела. Загрузите фото заново.")
        await state.clear()
        return

    # Сохраняем описание
    await state.update_data(room_description=room_description)

    # Удаляем текст пользователя
    try:
        await message.delete()
    except:
        pass

    # Проверка баланса
    is_admin = user_id in admins
    if not is_admin:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()

            data = await state.get_data()
            menu_id = data.get('menu_message_id')
            if menu_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_id,
                        text=NO_BALANCE_TEXT,
                        reply_markup=get_payment_keyboard(),
                        parse_mode="Markdown"
                    )
                except:
                    pass
            return

    if not is_admin:
        await db.decrease_balance(user_id)

    # Показываем прогресс
    data = await state.get_data()
    menu_id = data.get('menu_message_id')
    if menu_id:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_id,
                text="⏳ Создаю дизайн помещения...",
                parse_mode="Markdown"
            )
        except:
            pass

    # ЗАПУСК ГЕНЕРАЦИИ С ТЕКСТОВЫМ ПРОМПТОМ (с использованием Smart Fallback)
    try:
        result_image_url = await smart_generate_with_text(
            photo_file_id=photo_id,
            user_prompt=room_description,
            bot_token=bot_token,
            scene_type="other_room"
        )
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"Критическая ошибка генерации другого помещения: {e}")
        result_image_url = None
        success = False

        # Уведомление админов
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_critical_errors")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Критическая ошибка генерации 'Другого помещения':\nПользователь: `{user_id}`\n\n{str(e)[:500]}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    # Логирование
    await db.log_generation(
        user_id=user_id,
        room_type='other_room',
        style_type='text_prompt',
        operation_type='design',
        success=success
    )

    if result_image_url:
        # Подготовка подписи
        caption = (
            f"✨ Ваш новый дизайн помещения!\n\n"
            f"Ваше задание: {room_description}"
        )

        # Отправка фото
        sent_photo_message = None  # ДОБАВЛЕНО 2025-12-08 16:01
        try:
            sent_photo_message = await message.answer_photo(  # ИЗМЕНЕНО: сохраняем результат
                photo=result_image_url,
                caption=caption,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки фото помещения: {e}")

            # Fallback
            import aiohttp
            from aiogram.types import BufferedInputFile

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()
                            sent_photo_message = await message.answer_photo(  # ИЗМЕНЕНО: сохраняем результат
                                photo=BufferedInputFile(photo_data, filename="room.jpg"),
                                caption=caption,
                                parse_mode="HTML"
                            )
            except Exception as fallback_error:
                logger.error(f"❌ Fallback тоже не сработал: {fallback_error}")

                if menu_id:
                    try:
                        await message.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=menu_id,
                            text="❌ Ошибка при отправке изображения. Попробуйте еще раз.",
                            reply_markup=get_payment_keyboard(),
                            parse_mode="Markdown"
                        )
                    except:
                        pass
                return

        # ДОБАВЛЕНО 2025-12-08 16:01: Сохранение file_id сгенерированной картинки
        if sent_photo_message and sent_photo_message.photo:
            new_photo_id = sent_photo_message.photo[-1].file_id
            await state.update_data(photo_id=new_photo_id)
            logger.info(
                f"✅ Сохранён file_id отредактированного помещения: user_id={user_id}, file_id={new_photo_id[:30]}...")

        # Успех - создаём меню под картинкой
        if menu_id:
            try:
                await message.bot.delete_message(chat_id=chat_id, message_id=menu_id)
                await db.delete_chat_menu(chat_id)
            except:
                pass

        from utils.helpers import add_balance_to_text
        text_with_balance = await add_balance_to_text("✅ Выбери что дальше 👇", user_id)

        new_menu = await message.answer(
            text=text_with_balance,
            reply_markup=get_post_generation_keyboard(show_continue_editing=True),
            parse_mode="Markdown"
        )

        await state.update_data(menu_message_id=new_menu.message_id)
        await db.save_chat_menu(chat_id, user_id, new_menu.message_id, 'post_generation')

    else:
        # Ошибка генерации
        from keyboards.inline import get_main_menu_keyboard
        if menu_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_id,
                    text="❌ Ошибка генерации. Попробуйте еще раз.",
                    reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                    parse_mode="Markdown"
                )
            except:
                pass



# ===== ОБРАБОТЧИК КНОПКИ "ПРОДОЛЖИТЬ РЕДАКТИРОВАНИЕ" =====
# ДОБАВЛЕНО: 2025-12-08 16:00
@router.callback_query(F.data == "continue_editing")
async def continue_editing_handler(callback: CallbackQuery, state: FSMContext):
    """
    НОВЫЙ ОБРАБОТЧИК: Кнопка "Продолжить редактирование"

    Дата создания: 2025-12-08 16:00
    Возвращает к экрану ввода текстового промпта с текущей (отредактированной) картинкой
    """
    user_id = callback.from_user.id

    # Получаем данные из FSM
    data = await state.get_data()
    scene_type = data.get('scene_type')
    room = data.get('room')
    photo_id = data.get('photo_id')

    logger.info(
        f"🔄 Продолжить редактирование: user_id={user_id}, scene_type={scene_type}, room={room}, photo_id={'ДА' if photo_id else 'НЕТ'}")

    # Проверка наличия данных
    if not photo_id:
        await callback.answer("⚠️ Сессия устарела. Загрузите фото заново.", show_alert=True)
        await state.clear()
        from utils.navigation import show_main_menu
        from loader import bot
        admins = []  # Заглушка, т.к. admins нужны для show_main_menu
        await show_main_menu(callback, state, admins)
        return

    await db.log_activity(user_id, 'continue_editing')

    # Определяем к какому экрану возвращаться
    if scene_type in ["house_exterior", "plot_exterior"]:
        # ЭКСТЕРЬЕР → ввод промпта для экстерьера
        await state.set_state(CreationStates.waiting_for_exterior_prompt)

        if scene_type == "house_exterior":
            prompt_text = EXTERIOR_HOUSE_PROMPT_TEXT
        else:
            prompt_text = EXTERIOR_PLOT_PROMPT_TEXT

        logger.info(f"✅ Возврат к exterior_prompt для {scene_type}")

        await edit_menu(
            callback=callback,
            state=state,
            text=prompt_text,
            keyboard=get_upload_photo_keyboard(),
            screen_code='exterior_prompt'
        )

    elif room == "other_room":
        # "ДРУГОЕ ПОМЕЩЕНИЕ" → ввод описания помещения
        await state.set_state(CreationStates.waiting_for_room_description)

        logger.info(f"✅ Возврат к room_description для other_room")

        await edit_menu(
            callback=callback,
            state=state,
            text=ROOM_DESCRIPTION_PROMPT_TEXT,
            keyboard=get_upload_photo_keyboard(),
            screen_code='room_description'
        )

    else:
        # Некорректное состояние - возврат в главное меню
        logger.warning(f"⚠️ Некорректные данные для continue_editing: scene_type={scene_type}, room={room}")
        await callback.answer("⚠️ Ошибка. Возврат в главное меню.", show_alert=True)
        await state.clear()
        from utils.navigation import show_main_menu
        from loader import bot
        admins = []
        await show_main_menu(callback, state, admins)
        return

    await callback.answer()


# ===== ВЫБОР КОМНАТЫ =====
@router.callback_query(CreationStates.choose_room, F.data.startswith("room_"))
async def room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Обработка выбора комнаты"""
    room = callback.data.replace("room_", "", 1)
    user_id = callback.from_user.id

    await db.log_activity(user_id, f'room_{room}')

    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await edit_menu(
                callback=callback,
                state=state,
                text=NO_BALANCE_TEXT,
                keyboard=get_payment_keyboard(),
                screen_code='no_balance'
            )
            return

    await state.update_data(room=room)
    await state.set_state(CreationStates.choose_style)

    await edit_menu(
        callback=callback,
        state=state,
        text=CHOOSE_STYLE_TEXT,
        keyboard=get_style_keyboard(),
        screen_code='choose_style'
    )
    await callback.answer()


# ===== ОЧИСТКА ПРОСТРАНСТВА =====
@router.callback_query(CreationStates.choose_style,
                       F.data == "clear_space_confirm")
async def clear_space_confirm_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждение очистки пространства"""
    text = (
        "⚠️ **Подтверждение очистки**\n\n"
        "Хотите очистить изображение, "
        "нажмите кнопку «Очистить».\n\n"
        "Если нет — вернитесь назад."
    )

    from keyboards.inline import get_clear_space_confirm_keyboard

    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_clear_space_confirm_keyboard(),
        screen_code='clear_space_confirm'
    )
    await callback.answer()



@router.callback_query(CreationStates.choose_style,
                       F.data == "clear_space_execute")
async def clear_space_execute_handler(callback: CallbackQuery, state: FSMContext,
                                      admins: list[int], bot_token: str):

    """   # --- ИСПРАВЛЕНО: 2025-12-07 22:35 ---
    # Добавлено: Сохранение file_id очищенного фото в FSM для генерации дизайна
    # Теперь дизайн создаётся на основе ОЧИЩЕННОГО фото, а не исходного
    # Меню появляется ПОД картинкой (единое меню)
    # --- ОБНОВЛЕНО: 2025-12-23 ---
    # Использует smart_clear_space из api_fallback.py для Smart Fallback

    Выполнение очистки пространства
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await db.log_activity(user_id, 'clear_space')

    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await edit_menu(
                callback=callback,
                state=state,
                text=NO_BALANCE_TEXT,
                keyboard=get_payment_keyboard(),
                screen_code='no_balance'
            )
            return

    data = await state.get_data()
    photo_id = data.get('photo_id')

    if not photo_id:
        await callback.answer("Ошибка: фото не найдено", show_alert=True)
        return

    if user_id not in admins:
        await db.decrease_balance(user_id)

    # Показываем прогресс
    await edit_menu(
        callback=callback,
        state=state,
        text="⏳ Очищаю пространство...",
        keyboard=None,
        show_balance=False,
        screen_code='clearing_space'
    )
    await callback.answer()

    # ЗАПУСК ГЕНЕРАЦИИ С ИСПОЛЬЗОВАНИЕМ SMART FALLBACK
    try:
        result_image_url = await smart_clear_space(photo_id, bot_token)
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"Критическая ошибка очистки пространства: {e}")
        result_image_url = None
        success = False

        # Уведомление админов о критической ошибке
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_critical_errors")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Критическая ошибка очистки:\nПользователь: `{user_id}`\n\n{str(e)[:500]}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    await db.log_generation(
        user_id=user_id,
        room_type='clear_space',
        style_type='clear_space',
        operation_type='clear_space',
        success=success
    )

    if result_image_url:
        # Отправляем очищенное фото
        sent_message = await callback.message.answer_photo(
            photo=result_image_url,
            caption="✨ Пространство очищено!",
            parse_mode="Markdown"
        )

        # ✅ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Извлекаем file_id очищенного фото и сохраняем в FSM
        cleared_file_id = sent_message.photo[-1].file_id
        await state.update_data(photo_id=cleared_file_id)
        logger.info(f"✅ Очищенное фото сохранено: user_id={user_id}, file_id={cleared_file_id}")

        await state.set_state(CreationStates.choose_room)

        # ✅ ИСПРАВЛЕНО: Удаляем старое меню и создаём НОВОЕ под картинкой
        data = await state.get_data()
        old_menu_id = data.get('menu_message_id')
        if old_menu_id:
            try:
                await callback.message.bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_menu_id
                )
                await db.delete_chat_menu(chat_id)
            except Exception as e:
                logger.debug(f"Не удалось удалить старое меню: {e}")

        # Создаём НОВОЕ меню ПОД картинкой
        from utils.helpers import add_balance_to_text
        text_with_balance = await add_balance_to_text(PHOTO_SAVED_TEXT, user_id)

        new_menu = await callback.message.answer(
            text=text_with_balance,
            reply_markup=get_room_keyboard(),
            parse_mode="Markdown"
        )

        # Сохраняем ID нового меню в FSM + БД
        await state.update_data(menu_message_id=new_menu.message_id)
        await db.save_chat_menu(chat_id, user_id, new_menu.message_id, 'choose_room')

    else:
        # При ошибке редактируем существующее меню
        await edit_menu(
            callback=callback,
            state=state,
            text="❌ Ошибка очистки. Попробуйте еще раз.",
            keyboard=get_room_keyboard(),
            screen_code='clear_space_error'
        )


@router.callback_query(CreationStates.choose_style,
                       F.data == "clear_space_cancel")
async def clear_space_cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена очистки пространства"""
    await state.set_state(CreationStates.choose_room)

    await edit_menu(
        callback=callback,
        state=state,
        text=PHOTO_SAVED_TEXT,
        keyboard=get_room_keyboard(),
        screen_code='choose_room'
    )
    await callback.answer()


# ===== ВЫБОР СТИЛЯ/ВАРИАНТА И ГЕНЕРАЦИЯ =====
@router.callback_query(CreationStates.choose_style, F.data == "back_to_room")
async def back_to_room_selection(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору комнаты"""
    await state.set_state(CreationStates.choose_room)

    await edit_menu(
        callback=callback,
        state=state,
        text=PHOTO_SAVED_TEXT,
        keyboard=get_room_keyboard(),
        screen_code='choose_room'
    )
    await callback.answer()


@router.callback_query(CreationStates.choose_style, F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    # --- ИСПРАВЛЕНО: 2025-12-07 21:08 ---
    # Добавлен fallback-механизм отправки фото: сначала URL, при ошибке - BufferedInputFile
    # Решена проблема ClientOSError: [Errno 22] на Windows
    # Соблюдена технология единого меню
    # --- ОБНОВЛЕНО: 2025-12-23 ---
    # Использует smart_generate_interior из api_fallback.py для Smart Fallback

    Обработка выбора стиля и генерация дизайна
    """
    import aiohttp
    from aiogram.types import BufferedInputFile

    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await db.log_activity(user_id, f'style_{style}')

    # Проверка наличия данных
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    if not photo_id or not room:
        await callback.answer(
            "⚠️ Сессия устарела. Загрузите фото заново.",
            show_alert=True
        )
        await state.clear()
        await show_main_menu(callback, state, admins)
        return

    # Проверка баланса
    is_admin = user_id in admins
    if not is_admin:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await edit_menu(
                callback=callback,
                state=state,
                text=NO_BALANCE_TEXT,
                keyboard=get_payment_keyboard(),
                screen_code='no_balance'
            )
            return

    if not is_admin:
        await db.decrease_balance(user_id)

    # Показываем прогресс
    await edit_menu(
        callback=callback,
        state=state,
        text="⏳ Создаю новый дизайн...",
        keyboard=None,
        show_balance=False,
        screen_code='generating_design'
    )
    await callback.answer()

    # ЗАПУСК ГЕНЕРАЦИИ С ИСПОЛЬЗОВАНИЕМ SMART FALLBACK
    try:
        result_image_url = await smart_generate_interior(photo_id, room, style, bot_token)
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"Критическая ошибка генерации: {e}")
        result_image_url = None
        success = False

        # Уведомление админов
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_critical_errors")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        (
                            f"⚠️ Критическая ошибка генерации:\n"
                            f"Пользователь: `{user_id}`\nКомната: {room}\nСтиль: {style}\n\n{str(e)[:500]}"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    await db.log_generation(
        user_id=user_id,
        room_type=room,
        style_type=style,
        operation_type='design',
        success=success
    )

    if result_image_url:
        # Подготовка подписи
        room_name = html.escape(room.replace('_', ' ').title(), quote=True)
        style_name = html.escape(style.replace('_', ' ').title(), quote=True)
        caption = f"✨ Ваш новый дизайн {room_name} в стиле <b>{style_name}</b>!"

        photo_sent = False

        # ===== ПОПЫТКА 1: ОТПРАВКА ПО URL (БЫСТРО) =====
        try:
            await callback.message.answer_photo(
                photo=result_image_url,
                caption=caption,
                parse_mode="HTML"
            )
            photo_sent = True
            logger.info(f"✅ Фото отправлено по URL: user_id={user_id}")

        except Exception as url_error:
            logger.warning(f"⚠️ Не удалось отправить по URL: {url_error}")

            # ===== ПОПЫТКА 2: СКАЧИВАЕМ И ОТПРАВЛЯЕМ (FALLBACK) =====
            try:
                logger.info(f"🔄 Переключаемся на BufferedInputFile для user_id={user_id}")

                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()

                            await callback.message.answer_photo(
                                photo=BufferedInputFile(photo_data, filename="design.jpg"),
                                caption=caption,
                                parse_mode="HTML"
                            )
                            photo_sent = True
                            logger.info(f"✅ Фото отправлено через BufferedInputFile: user_id={user_id}")
                        else:
                            logger.error(f"❌ HTTP {resp.status} при скачивании")

            except Exception as buffer_error:
                logger.error(f"❌ Fallback тоже не сработал: {buffer_error}")

        # Если обе попытки провалились
        if not photo_sent:
            from keyboards.inline import get_main_menu_keyboard
            await edit_menu(
                callback=callback,
                state=state,
                text="❌ Ошибка при отправке изображения. Попробуйте еще раз.",
                keyboard=get_main_menu_keyboard(is_admin=is_admin),
                screen_code='generation_error'
            )
            return

        # ✅ УСПЕХ - СОЗДАЕМ МЕНЮ ПОД КАРТИНКОЙ
        data = await state.get_data()
        old_menu_id = data.get('menu_message_id')
        if old_menu_id:
            try:
                await callback.message.bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_menu_id
                )
                await db.delete_chat_menu(chat_id)
            except Exception as e:
                logger.debug(f"Не удалось удалить старое меню: {e}")

        # Отправляем НОВОЕ меню
        from utils.helpers import add_balance_to_text
        text_with_balance = await add_balance_to_text(
            "✅ Выбери что дальше 👇",
            user_id
        )

        new_menu = await callback.message.answer(
            text=text_with_balance,
            reply_markup=get_post_generation_keyboard(),
            parse_mode="Markdown"
        )

        # Сохраняем в FSM + БД (соблюдаем технологию единого меню)
        await state.update_data(menu_message_id=new_menu.message_id)
        await db.save_chat_menu(chat_id, user_id, new_menu.message_id, 'post_generation')

    else:
        from keyboards.inline import get_main_menu_keyboard
        await edit_menu(
            callback=callback,
            state=state,
            text="❌ Ошибка генерации. Попробуйте еще раз.",
            keyboard=get_main_menu_keyboard(is_admin=user_id in admins),
            screen_code='generation_error'
        )





# --- ИСПРАВЛЕНО: 2025-12-07 13:18 - Добавлена проверка устаревших сессий с использованием существующей show_main_menu() ---
#  После генерации
@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Смена стиля после генерации"""
    user_id = callback.from_user.id

    # Проверяем наличие данных в FSM
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    # Если данных нет (после перезапуска), сбрасываем в главное меню
    if not photo_id or not room:
        # Пытаемся ответить на callback (если не устарел)
        try:
            await callback.answer(
                "⚠️ Сессия устарела. Начните сначала.",
                show_alert=True
            )
        except Exception:
            pass  # Callback устарел, игнорируем

        # ИСПОЛЬЗУЕМ СУЩЕСТВУЮЩУЮ ФУНКЦИЮ!
        await show_main_menu(callback, state, admins)
        return

    # Если данные есть, продолжаем
    await state.set_state(CreationStates.choose_style)

    await edit_menu(
        callback=callback,
        state=state,
        text=CHOOSE_STYLE_TEXT,
        keyboard=get_style_keyboard(),
        screen_code='choose_style'
    )

    try:
        await callback.answer()
    except Exception:
        pass  # Callback устарел


@router.callback_query(F.data.startswith("room_") | F.data.startswith("style_") |
                       F.data.in_(["clear_space_confirm", "clear_space_execute", "clear_space_cancel"]))
async def handle_stale_creation_buttons(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Универсальный обработчик для кнопок выбора комнаты/стиля.
    После перезапуска FSM пустой, фото недоступно → сброс в главное меню.
    """
    user_id = callback.from_user.id

    # Проверяем наличие photo_id в FSM
    data = await state.get_data()
    photo_id = data.get('photo_id')

    # Если фото нет → сессия устарела, возвращаем в главное меню
    if not photo_id:
        try:
            await callback.answer(
                "⚠️ Сессия устарела после перезапуска.\nНачните создание дизайна заново.",
                show_alert=True
            )
        except Exception:
            pass

        # Очищаем FSM
        await state.clear()

        # Возвращаем в главное меню
        await show_main_menu(callback, state, admins)
        return

    # Если photo_id есть, этот обработчик не должен был сработать
    # (значит, основной обработчик с FSM-фильтром должен был его перехватить)
    # На всякий случай просто игнорируем
    await callback.answer()



# ===== БЛОКИРОВКИ ВВОДА =====
@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    """Блокировка любых сообщений кроме фото"""
    try:
        await message.delete()
    except Exception:
        pass


@router.message(CreationStates.choose_room)
async def block_messages_in_choose_room(message: Message, state: FSMContext):
    """Блокируем любые сообщения на экране выбора помещения"""
    try:
        await message.delete()
    except Exception:
        pass

    msg = await message.answer(
        "🚫 Используйте кнопки!",
        parse_mode=ParseMode.MARKDOWN
    )
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


@router.message(F.video | F.video_note | F.document | F.sticker | F.audio | F.voice | F.animation)
async def block_media_types(message: Message):
    """Блокировка неподдерживаемых типов медиа"""
    try:
        await message.delete()
    except Exception:
        pass


@router.message(F.photo)
async def block_unexpected_photos(message: Message, state: FSMContext):
    """Блокировка фото вне состояния waiting_for_photo"""
    try:
        await message.delete()
    except Exception:
        pass
    msg = await message.answer("🚫 Используйте кнопки меню!")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


@router.message(F.text)
async def block_all_text_messages(message: Message):
    """Блокировка всех текстовых сообщений"""
    try:
        await message.delete()
    except Exception:
        pass
