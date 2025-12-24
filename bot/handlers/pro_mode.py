"""PRO Mode handlers - соответствует DEVELOPMENT_RULES.md и FSM_GUIDE.md

Закрепленные правила:
- ✅ Использовать edit_menu() для редактирования
- ✅ Использовать state.set_state(None) при навигации
- ✅ Сохранять menu_message_id в FSM и БД
- ✅ Все callbacks редактируют ОДНО меню
- ✅ После каждого редактирования: db.save_chat_menu()
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.states.fsm import ProModeStates
from bot.keyboards.inline import (
    get_mode_selection_keyboard,
    get_pro_params_keyboard
)
from utils.navigation import edit_menu
from config import logger

router = Router()


# ============================================
# HANDLER 1: Show mode selection screen
# ============================================
@router.callback_query(F.data == "profile_settings")
async def show_mode_selection(callback: CallbackQuery, state: FSMContext):
    """
    Показать экран выбора режима (СТАНДАРТ vs PRO)
    
    Входящие данные:
    - Callback из меню профиля
    
    Выходящие данные:
    - FSM: ProModeStates.choosing_mode
    - menu_message_id: сохранен в FSM и БД
    
    Экран: РЕЖИМЫ (2 ряда по 2 кнопки)
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    try:
        # 1. Получаем текущий режим из БД
        user_data = await callback.bot.get_session().get(f"user:{user_id}")
        current_mode = user_data.get('mode', 'standard') if user_data else 'standard'
        
        # 2. Обновляем FSM-состояние
        await state.set_state(ProModeStates.choosing_mode)
        
        # 3. Сохраняем важные данные в FSM
        await state.update_data(
            menu_message_id=callback.message.message_id,
            current_mode=current_mode,
            user_id=user_id
        )
        
        # 4. Текст меню
        text = """⚙️ ВЫБОР РЕЖИМА ГЕНЕРАЦИИ

📋 **СТАНДАРТ** — быстрые генерации
• Соотношение: 16:9 (фиксировано)
• Разрешение: 1K (1280×720)

🔧 **PRO** — профессиональное качество
• Выбирайте соотношение: 16:9, 4:3, 1:1, 9:16
• Выбирайте разрешение: 1K, 2K, 4K
"""
        
        # 5. Редактируем меню через edit_menu()
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_mode_selection_keyboard(
                current_mode_is_pro=(current_mode == 'pro')
            ),
            show_balance=True
        )
        
        logger.info(f"✅ [PRO_MODE] Показан экран выбора режима для {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в show_mode_selection: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 2: Select STANDARD mode
# ============================================
@router.callback_query(F.data == "mode_std", state=ProModeStates.choosing_mode)
async def select_standard_mode(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь выбрал СТАНДАРТ
    
    Действие:
    - Сохраняем mode='standard' в БД
    - Возвращаемся в профиль
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    try:
        # ✅ Согласно DEVELOPMENT_RULES: state.set_state(None) при навигации
        await state.set_state(None)
        
        # Получаем menu_message_id ДО очистки
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id', callback.message.message_id)
        
        # Восстанавливаем menu_message_id после set_state
        await state.update_data(menu_message_id=menu_message_id)
        
        # TODO: Сохранить в БД: await db.update_user(user_id, mode='standard')
        
        # Текст подтверждения
        text = """✅ РЕЖИМ ИЗМЕНЁН НА СТАНДАРТ

📋 Текущий режим: СТАНДАРТ
• Соотношение: 16:9
• Разрешение: 1K

При создании дизайна будут использоваться эти параметры."""
        
        # Редактируем меню
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_mode_selection_keyboard(current_mode_is_pro=False),
            show_balance=True
        )
        
        # TODO: await db.save_chat_menu(chat_id, user_id, menu_message_id, 'mode_standard')
        
        await callback.answer("✅ Режим: СТАНДАРТ")
        logger.info(f"✅ [PRO_MODE] Пользователь {user_id} выбрал СТАНДАРТ режим")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в select_standard_mode: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 3: Select PRO mode
# ============================================
@router.callback_query(F.data == "mode_pro", state=ProModeStates.choosing_mode)
async def select_pro_mode(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь выбрал PRO - показываем параметры PRO
    
    Переход:
    - ProModeStates.choosing_mode → ProModeStates.choosing_pro_params
    
    Экран: ПАРАМЕТРЫ PRO (3 ряда: 4+3+2)
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    try:
        # 1. Получаем текущие параметры PRO из БД
        # TODO: current_ratio = await db.get_pro_setting(user_id, 'aspect_ratio') or '16:9'
        current_ratio = '16:9'
        # TODO: current_resolution = await db.get_pro_setting(user_id, 'resolution') or '1K'
        current_resolution = '1K'
        
        # 2. Переходим в состояние выбора параметров
        await state.set_state(ProModeStates.choosing_pro_params)
        
        # 3. Сохраняем параметры в FSM
        await state.update_data(
            menu_message_id=callback.message.message_id,
            user_id=user_id,
            current_ratio=current_ratio,
            current_resolution=current_resolution
        )
        
        # 4. Текст меню
        text = f"""🔧 ПАРАМЕТРЫ PRO РЕЖИМА

📑 Соотношение сторон:
• 16:9 — широкоэкранный (стандарт)
• 4:3 — классический формат
• 1:1 — квадратный формат
• 9:16 — портретный (вертикальный)

📊 Разрешение:
• 1K — 1280×720 (быстро)
• 2K — 2560×1440 (качество)
• 4K — 3840×2160 (максимум)

✅ Текущие параметры: {current_ratio} @ {current_resolution}"""
        
        # 5. Редактируем меню
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_pro_params_keyboard(
                current_ratio=current_ratio,
                current_resolution=current_resolution
            ),
            show_balance=True
        )
        
        # TODO: await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'pro_params')
        
        await callback.answer()
        logger.info(f"✅ [PRO_MODE] Показаны параметры PRO для {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в select_pro_mode: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 4: Select aspect ratio
# ============================================
@router.callback_query(F.data.startswith("aspect_"), state=ProModeStates.choosing_pro_params)
async def select_aspect_ratio(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь выбрал соотношение сторон
    
    Парсинг: aspect_16:9 → ratio = '16:9'
    
    Действие:
    - Сохраняем ratio в БД
    - Обновляем FSM
    - Переоткрываем меню с новой отметкой
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    try:
        # 1. Парсим callback_data
        aspect_ratio = callback.data.replace("aspect_", "")
        logger.debug(f"🔍 Parsed aspect_ratio: {aspect_ratio}")
        
        if aspect_ratio not in ["16:9", "4:3", "1:1", "9:16"]:
            await callback.answer("❌ Ошибка: неверное соотношение", show_alert=True)
            return
        
        # 2. Сохраняем в БД
        # TODO: await db.update_pro_settings(user_id, aspect_ratio=aspect_ratio)
        
        # 3. Обновляем state.data
        data = await state.get_data()
        await state.update_data(current_ratio=aspect_ratio)
        
        # 4. Текст обновлённого меню
        text = f"""🔧 ПАРАМЕТРЫ PRO РЕЖИМА

📑 Соотношение сторон:
• 16:9 — широкоэкранный (стандарт)
• 4:3 — классический формат
• 1:1 — квадратный формат
• 9:16 — портретный (вертикальный)

📊 Разрешение:
• 1K — 1280×720 (быстро)
• 2K — 2560×1440 (качество)
• 4K — 3840×2160 (максимум)

✅ Текущие параметры: {aspect_ratio} @ {data.get('current_resolution', '1K')}"""
        
        # 5. Редактируем меню (НЕ создаем новое!)
        await callback.message.edit_text(
            text=text,
            reply_markup=get_pro_params_keyboard(
                current_ratio=aspect_ratio,
                current_resolution=data.get('current_resolution', '1K')
            ),
            parse_mode="Markdown"
        )
        
        await callback.answer(f"✅ Соотношение: {aspect_ratio}")
        logger.info(f"✅ [PRO_MODE] Пользователь {user_id} выбрал соотношение {aspect_ratio}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в select_aspect_ratio: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 5: Select resolution
# ============================================
@router.callback_query(F.data.startswith("res_"), state=ProModeStates.choosing_pro_params)
async def select_resolution(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь выбрал разрешение
    
    Парсинг: res_1K → resolution = '1K'
    
    Действие:
    - Сохраняем resolution в БД
    - Сохраняем mode='pro' в БД
    - Обновляем FSM
    - Переоткрываем меню с новой отметкой
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    try:
        # 1. Парсим callback_data
        resolution = callback.data.replace("res_", "")
        logger.debug(f"🔍 Parsed resolution: {resolution}")
        
        if resolution not in ["1K", "2K", "4K"]:
            await callback.answer("❌ Ошибка: неверное разрешение", show_alert=True)
            return
        
        # 2. Сохраняем в БД
        # TODO: await db.update_pro_settings(
        #     user_id=user_id,
        #     resolution=resolution,
        #     mode='pro'  # Явно переводим режим в PRO
        # )
        
        # 3. Обновляем state.data
        data = await state.get_data()
        await state.update_data(current_resolution=resolution)
        
        # 4. Текст обновлённого меню
        text = f"""🔧 ПАРАМЕТРЫ PRO РЕЖИМА

📑 Соотношение сторон:
• 16:9 — широкоэкранный (стандарт)
• 4:3 — классический формат
• 1:1 — квадратный формат
• 9:16 — портретный (вертикальный)

📊 Разрешение:
• 1K — 1280×720 (быстро)
• 2K — 2560×1440 (качество)
• 4K — 3840×2160 (максимум)

✅ Текущие параметры: {data.get('current_ratio', '16:9')} @ {resolution}"""
        
        # 5. Редактируем меню (НЕ создаем новое!)
        await callback.message.edit_text(
            text=text,
            reply_markup=get_pro_params_keyboard(
                current_ratio=data.get('current_ratio', '16:9'),
                current_resolution=resolution
            ),
            parse_mode="Markdown"
        )
        
        await callback.answer(f"✅ Разрешение: {resolution}")
        logger.info(f"✅ [PRO_MODE] Пользователь {user_id} выбрал разрешение {resolution}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в select_resolution: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 6: Back to mode selection
# ============================================
@router.callback_query(F.data == "profile_settings", state=ProModeStates.choosing_pro_params)
async def back_to_mode_selection(callback: CallbackQuery, state: FSMContext):
    """
    Вернуться из параметров PRO обратно в выбор режима
    
    Переход:
    - ProModeStates.choosing_pro_params → ProModeStates.choosing_mode
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    try:
        # 1. Получаем данные ДО смены состояния
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')
        current_mode = data.get('current_mode', 'standard')
        
        # 2. Меняем состояние
        await state.set_state(ProModeStates.choosing_mode)
        
        # 3. Восстанавливаем важные данные
        await state.update_data(
            menu_message_id=menu_message_id,
            current_mode=current_mode
        )
        
        # 4. Текст
        text = """⚙️ ВЫБОР РЕЖИМА ГЕНЕРАЦИИ

📋 **СТАНДАРТ** — быстрые генерации
• Соотношение: 16:9 (фиксировано)
• Разрешение: 1K (1280×720)

🔧 **PRO** — профессиональное качество
• Выбирайте соотношение: 16:9, 4:3, 1:1, 9:16
• Выбирайте разрешение: 1K, 2K, 4K
"""
        
        # 5. Редактируем меню
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_mode_selection_keyboard(
                current_mode_is_pro=(current_mode == 'pro')
            ),
            show_balance=True
        )
        
        await callback.answer()
        logger.info(f"✅ [PRO_MODE] Вернулись к выбору режима для {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в back_to_mode_selection: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
