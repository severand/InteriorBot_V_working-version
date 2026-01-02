# ========================================
# bot/handlers/edit_design.py
# EDIT_DESIGN MODE HANDLERS
# Дата создания: 2026-01-02
# ========================================
"""
Обработчики для режима EDIT_DESIGN (экраны 7, 8, 9):

SCREEN 8: EDIT_DESIGN - Меню редактирования
    ├─ Кнопка: "Очистить фото" → SCREEN 9
    ├─ Кнопка: "Текстовый редактор" → SCREEN 7
    ├─ Кнопка: "⬅️ Новое фото" → SCREEN 2
    └─ Кнопка: "🏠 Режим работы" → SCREEN 1

SCREEN 7: TEXT_INPUT - Текстовый ввод описания
    ├─ Пользователь вводит текст
    ├─ СРАЗУ отправляется в API (smart_generate_with_text)
    ├─ Новое фото отправляется пользователю
    └─ Возврат на SCREEN 8

SCREEN 9: CLEAR_CONFIRM - Подтверждение очистки
    ├─ "✅ Очистить" → API (smart_clear_space) → SCREEN 8
    └─ "❌ Отмена" → SCREEN 8
"""

import logging
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states.creation import CreationStates
from keyboards.inline import (
    get_edit_design_keyboard,
    get_text_input_keyboard,
    get_clear_space_confirm_keyboard,
)
from utils.texts import (
    POST_GENERATION_MENU_TEXT,
)
from services.api_fallback import (
    smart_generate_with_text,
    smart_clear_space,
)
from services.prompts import build_design_prompt

logger = logging.getLogger(__name__)
router = Router()

# ========================================
# КОНСТАНТЫ ТЕКСТОВ
# ========================================

# SCREEN 8: EDIT_DESIGN - Меню редактирования
EDIT_DESIGN_MENU_TEXT = """✏️ **Редактируем дизайн**

Выберите действие:

🗑️ **Очистить фото** - удалить всю мебель и предметы

📝 **Текстовый редактор** - добавить описание для уточнения дизайна

Примеры описаний:
• "Добавить светлую мебель из дуба"
• "Теплые тона, минимализм"
• "Больше растений и освещения"
"""

# SCREEN 7: TEXT_INPUT - Ввод текста
TEXT_INPUT_SCREEN_TEXT = """📝 **Текстовый редактор**

Введите описание для уточнения дизайна.

Ваше описание будет **сразу отправлено в модель**, и дизайн обновится с учетом пожеланий.

**Примеры:**
• "Добавить светлую мебель"
• "Теплые тона, минимализм"
• "Больше растений"
• "Современный стиль"

Нажмите **"⬅️ Назад"** чтобы вернуться на меню редактирования.
"""

# SCREEN 9: CLEAR_CONFIRM - Подтверждение очистки
CLEAR_SPACE_CONFIRM_TEXT = """⚠️ **ПОДТВЕРЖДЕНИЕ ОЧИСТКИ**

Вы уверены, что хотите очистить помещение?

✓ Будут удалены **все предметы** из комнаты
✓ Останется только **стены, пол и потолок**

⚠️ **Это действие невозможно отменить!**

Нажмите **"✅ Очистить"** чтобы продолжить или **"❌ Отмена"** чтобы вернуться.
"""

# ========================================
# SCREEN 8: EDIT_DESIGN - Меню редактирования
# ========================================

@router.callback_query(StateFilter(CreationStates.edit_design), F.data == "text_input")
async def open_text_editor(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 8 → SCREEN 7
    Открыть текстовый редактор для ввода описания
    
    Переводит пользователя в состояние text_input и показывает
    экран с инструкциями и клавиатурой для возврата.
    """
    await callback.answer()
    
    # Перейти в режим ввода текста
    await state.set_state(CreationStates.text_input)
    
    # Показать SCREEN 7 с клавиатурой
    await callback.message.edit_text(
        text=TEXT_INPUT_SCREEN_TEXT,
        reply_markup=get_text_input_keyboard()
    )


# ========================================
# SCREEN 7: TEXT_INPUT - Получить текст и отправить в API
# ========================================

@router.message(StateFilter(CreationStates.text_input), F.text)
async def receive_text_prompt(
    message: Message,
    state: FSMContext,
    bot_token: str
):
    """
    SCREEN 7: Получить текстовый промпт и СРАЗУ отправить в модель
    
    Логика:
    1. Валидация текста (минимум 3 символа)
    2. Сохраняем текст в FSM: additional_text
    3. Получаем текущие параметры дизайна (фото, room_type, style_type)
    4. Собираем полный промпт = base_prompt + additional_text
    5. Вызываем API: smart_generate_with_text()
    6. Отправляем новое фото
    7. Сохраняем новый photo_id
    8. Возвращаемся на SCREEN 8
    
    ❌ НЕ повторяем ввод
    ✅ ОДИН ввод = ОДИН API вызов
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Получить текст от пользователя
    user_text = message.text.strip()
    
    # ШАГ 1: Валидация
    if not user_text or len(user_text) < 3:
        error_msg = await message.answer("⚠️ Введите описание (минимум 3 символа)")
        await asyncio.sleep(2)
        try:
            await error_msg.delete()
        except Exception as e:
            logger.debug(f"Could not delete error message: {e}")
        return
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"Could not delete user message: {e}")
    
    # ШАГ 2: Сохраняем текст в FSM
    data = await state.get_data()
    additional_text = data.get('additional_text', '')
    
    # Если уже есть текст, добавляем к нему (это повторный ввод)
    if additional_text:
        additional_text = additional_text + ' ' + user_text
    else:
        additional_text = user_text
    
    await state.update_data(additional_text=additional_text)
    
    # ШАГ 3: Получаем текущие параметры дизайна
    photo_id = data.get('photo_id')
    room_type = data.get('room_type', 'living_room')
    style_type = data.get('style_type', 'modern')
    use_pro = data.get('use_pro', False)
    menu_message_id = data.get('menu_message_id')
    
    # ШАГ 4: Показываем прогресс
    try:
        if menu_message_id:
            progress_msg = await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_message_id,
                text="⏳ **Применяю ваше описание...**"
            )
        else:
            progress_msg = await message.answer("⏳ **Применяю ваше описание...** ")
    except Exception as e:
        logger.error(f"Error showing progress: {e}")
        progress_msg = await message.answer("⏳ **Применяю ваше описание...** ")
    
    try:
        # ШАГ 5: Собираем полный промпт
        base_prompt = await build_design_prompt(style_type, room_type, translate=True)
        full_prompt = f"{base_prompt}\n\nДополнительные пожелания клиента:\n{additional_text}"
        
        logger.info(f"🎨 [USER {user_id}] Text editing started")
        logger.info(f"   Room: {room_type} | Style: {style_type}")
        logger.info(f"   Custom text: {user_text[:50]}...")
        
        # ШАГ 6: Вызываем API
        result_image_url = await smart_generate_with_text(
            photo_file_id=photo_id,
            user_prompt=full_prompt,
            bot_token=bot_token,
            scene_type=room_type,
            use_pro=use_pro
        )
        
        # ШАГ 7: Отправляем новое фото
        if result_image_url:
            # Удаляем прогресс-сообщение
            try:
                if menu_message_id:
                    await message.bot.delete_message(
                        chat_id=chat_id,
                        message_id=menu_message_id
                    )
            except Exception as e:
                logger.debug(f"Could not delete progress message: {e}")
            
            # Отправить новое фото
            sent_photo = await message.answer_photo(
                photo=result_image_url,
                caption="✨ **Дизайн обновлен с учетом ваших пожеланий!**"
            )
            
            # ШАГ 8: Сохраняем новый photo_id
            new_file_id = sent_photo.photo[-1].file_id
            await state.update_data(photo_id=new_file_id)
            
            logger.info(f"✅ [USER {user_id}] Text design updated successfully")
            
            # Небольшая пауза для лучшего UX
            await asyncio.sleep(1)
            
            # ШАГ 9: Возвращаемся на SCREEN 8
            await state.set_state(CreationStates.edit_design)
            menu_msg = await message.answer(
                text=EDIT_DESIGN_MENU_TEXT,
                reply_markup=get_edit_design_keyboard()
            )
            await state.update_data(menu_message_id=menu_msg.message_id)
        else:
            logger.error(f"❌ [USER {user_id}] Text design generation failed")
            error_text = (
                "❌ Ошибка при генерации дизайна.\n\n"
                "Пожалуйста, попробуйте позже."
            )
            try:
                if menu_message_id:
                    await message.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_message_id,
                        text=error_text
                    )
                else:
                    await message.answer(error_text)
            except Exception as e:
                await message.answer(error_text)
    
    except Exception as e:
        logger.error(f"❌ Error processing text prompt: {e}", exc_info=True)
        error_text = (
            "❌ Техническая ошибка.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        try:
            if menu_message_id:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    text=error_text
                )
            else:
                await message.answer(error_text)
        except Exception as e2:
            await message.answer(error_text)


# ========================================
# SCREEN 7: TEXT_INPUT - Вернуться назад без отправки в API
# ========================================

@router.callback_query(StateFilter(CreationStates.text_input), F.data == "back_from_text_input")
async def back_from_text_input(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 7 → SCREEN 8
    Вернуться на меню редактирования без отправки текста в API
    
    Пользователь может передумать и вернуться на меню редактирования,
    не отправляя описание в модель.
    """
    await callback.answer()
    
    # Перейти обратно в режим edit_design
    await state.set_state(CreationStates.edit_design)
    
    # Показать SCREEN 8 с меню редактирования
    await callback.message.edit_text(
        text=EDIT_DESIGN_MENU_TEXT,
        reply_markup=get_edit_design_keyboard()
    )


# ========================================
# SCREEN 8: EDIT_DESIGN - Показать подтверждение очистки
# ========================================

@router.callback_query(StateFilter(CreationStates.edit_design), F.data == "clear_space_confirm_keyboard")
async def show_clear_confirmation(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 8 → SCREEN 9
    Показать подтверждение перед очисткой пространства
    
    Когда пользователь нажимает "Очистить фото", показываем
    экран подтверждения с предупреждением о необратимости действия.
    """
    await callback.answer()
    
    # Показать SCREEN 9 с подтверждением
    await callback.message.edit_text(
        text=CLEAR_SPACE_CONFIRM_TEXT,
        reply_markup=get_clear_space_confirm_keyboard()
    )


# ========================================
# SCREEN 9: CLEAR_CONFIRM - Выполнить очистку
# ========================================

@router.callback_query(StateFilter(CreationStates.edit_design), F.data == "clear_space_execute")
async def execute_clear_space(
    callback: CallbackQuery,
    state: FSMContext,
    bot_token: str
):
    """
    SCREEN 9: Выполнить очистку пространства
    
    Логика:
    1. Показать прогресс: "⏳ Очищаю помещение..."
    2. Вызвать API: smart_clear_space(photo_id)
    3. Отправить очищенное фото
    4. Сохранить новый photo_id
    5. Вернуться на SCREEN 8
    
    Промпт для API:
    "Completely remove all interior details from this space."
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    # ШАГ 1: Показываем прогресс
    try:
        progress_msg = await callback.message.edit_text(
            text="⏳ **Очищаю помещение...**"
        )
    except Exception as e:
        logger.error(f"Error showing clear progress: {e}")
        progress_msg = None
    
    try:
        # ШАГ 2: Получаем текущие параметры
        data = await state.get_data()
        photo_id = data.get('photo_id')
        use_pro = data.get('use_pro', False)
        
        logger.info(f"🗑️ [USER {user_id}] Clear space started")
        
        # ШАГ 3: Вызываем API для очистки
        result_image_url = await smart_clear_space(
            photo_file_id=photo_id,
            bot_token=bot_token,
            use_pro=use_pro
        )
        
        # ШАГ 4: Отправляем очищенное фото
        if result_image_url:
            # Удаляем прогресс-сообщение
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception as e:
                    logger.debug(f"Could not delete progress message: {e}")
            
            # Отправить очищенное фото
            sent_photo = await callback.message.answer_photo(
                photo=result_image_url,
                caption="✨ **Помещение очищено!**\n\nТеперь вы можете редактировать дизайн"
            )
            
            # Сохраняем новый photo_id
            new_file_id = sent_photo.photo[-1].file_id
            await state.update_data(photo_id=new_file_id)
            
            logger.info(f"✅ [USER {user_id}] Clear space completed successfully")
            
            # Небольшая пауза
            await asyncio.sleep(1)
            
            # ШАГ 5: Возвращаемся на SCREEN 8
            await state.set_state(CreationStates.edit_design)
            menu_msg = await callback.message.answer(
                text=EDIT_DESIGN_MENU_TEXT,
                reply_markup=get_edit_design_keyboard()
            )
            await state.update_data(menu_message_id=menu_msg.message_id)
        else:
            logger.error(f"❌ [USER {user_id}] Clear space API failed")
            error_text = (
                "❌ Ошибка при очистке помещения.\n\n"
                "Пожалуйста, попробуйте позже."
            )
            try:
                if progress_msg:
                    await progress_msg.edit_text(error_text)
                else:
                    await callback.message.answer(error_text)
            except Exception as e:
                await callback.message.answer(error_text)
    
    except Exception as e:
        logger.error(f"❌ Error executing clear space: {e}", exc_info=True)
        error_text = (
            "❌ Техническая ошибка.\n\n"
            "Пожалуйста, попробуйте позже."
        )
        try:
            if progress_msg:
                await progress_msg.edit_text(error_text)
            else:
                await callback.message.answer(error_text)
        except Exception as e2:
            await callback.message.answer(error_text)


# ========================================
# SCREEN 9: CLEAR_CONFIRM - Отмена очистки
# ========================================

@router.callback_query(StateFilter(CreationStates.edit_design), F.data == "clear_space_cancel")
async def cancel_clear_space(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 9 → SCREEN 8
    Отмена очистки, возврат на меню редактирования
    
    Пользователь может отменить очистку и вернуться на SCREEN 8
    без выполнения API запроса.
    """
    await callback.answer()
    
    # Перейти обратно в режим edit_design
    await state.set_state(CreationStates.edit_design)
    
    # Показать SCREEN 8 с меню редактирования
    await callback.message.edit_text(
        text=EDIT_DESIGN_MENU_TEXT,
        reply_markup=get_edit_design_keyboard()
    )
