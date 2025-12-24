"""PRO Mode handlers - соответствует DEVELOPMENT_RULES.md и FSM_GUIDE.md

Закрепленные правила:
- ✅ Использовать edit_menu() для редактирования
- ✅ Использовать state.set_state(None) при навигации
- ✅ Сохранять menu_message_id в FSM и БД
- ✅ Все callbacks редактируют ОДНО меню
- ✅ После каждого редактирования: db.save_chat_menu()

PHASE 3 TASK 4: УБРАЛИ ВСЕ TODO, ПОДКЛЮЧИЛИ БД
Дата: 2025-12-24 13:35

PHASE 3 TASK 5: ИСПРАВЛЕНЫ ИМПОРТЫ (2025-12-24 19:52)
- Изменены абсолютные импорты на относительные
- Исправлено ModuleNotFoundError: No module named 'bot'

PHASE 3 TASK 6: ОБНОВЛЕН СИНТАКСИС AIOGRAM 3.X (2025-12-24 20:05)
- Добавлен StateFilter для корректной работы с состояниями
- Исправлены все декораторы @router.callback_query()

PHASE 3 TASK 7: ОКОНЧАТЕЛЬНО ОБНОВЛЕН StateFilter (2025-12-24 20:08)
- Перенесен импорт: from aiogram.filters import StateFilter

PHASE 3 TASK 8: ПЕРЕНАМЕНОВАН router → pro_mode_router (2025-12-24 20:11)
- router → pro_mode_router (для корректного импорта в main.py)
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states.fsm import ProModeStates
from keyboards.inline import (
    get_mode_selection_keyboard,
    get_pro_params_keyboard
)
from utils.navigation import edit_menu
from database.db import db
from config import logger

pro_mode_router = Router()


# ============================================
# HANDLER 1: Show mode selection screen
# ============================================
@pro_mode_router.callback_query(F.data == "profile_settings")
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
        # 1. Получаем текущие параметры из БД
        pro_settings = await db.get_user_pro_settings(user_id)
        current_mode_is_pro = pro_settings.get('pro_mode', False)
        
        # 2. Обновляем FSM-состояние
        await state.set_state(ProModeStates.choosing_mode)
        
        # 3. Сохраняем важные данные в FSM
        await state.update_data(
            menu_message_id=callback.message.message_id,
            current_mode_is_pro=current_mode_is_pro,
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
                current_mode_is_pro=current_mode_is_pro
            ),
            show_balance=True,
            screen_code='profile_settings'
        )
        
        logger.info(f"✅ [PRO_MODE] Показан экран выбора режима для {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в show_mode_selection: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 2: Select STANDARD mode
# ============================================
@pro_mode_router.callback_query(F.data == "mode_std", StateFilter(ProModeStates.choosing_mode))
async def select_standard_mode(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь выбрал СТАНДАРТ
    
    Действие:
    - Сохраняем mode=False в БД
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
        
        # ✅ СОХРАНИТЬ В БД
        await db.set_user_pro_mode(user_id, mode=False)
        
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
            show_balance=True,
            screen_code='profile_settings'
        )
        
        # ✅ СОХРАНИТЬ В БД
        await db.save_chat_menu(chat_id, user_id, menu_message_id, 'profile_settings')
        
        await callback.answer("✅ Режим: СТАНДАРТ")
        logger.info(f"✅ [PRO_MODE] Пользователь {user_id} выбрал СТАНДАРТ режим")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в select_standard_mode: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 3: Select PRO mode
# ============================================
@pro_mode_router.callback_query(F.data == "mode_pro", StateFilter(ProModeStates.choosing_mode))
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
        pro_settings = await db.get_user_pro_settings(user_id)
        current_ratio = pro_settings.get('pro_aspect_ratio', '16:9')
        current_resolution = pro_settings.get('pro_resolution', '1K')
        
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
            show_balance=True,
            screen_code='pro_params'
        )
        
        # ✅ СОХРАНИТЬ В БД
        await db.save_chat_menu(chat_id, user_id, callback.message.message_id, 'pro_params')
        
        await callback.answer()
        logger.info(f"✅ [PRO_MODE] Показаны параметры PRO для {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в select_pro_mode: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 4: Select aspect ratio
# ============================================
@pro_mode_router.callback_query(F.data.startswith("aspect_"), StateFilter(ProModeStates.choosing_pro_params))
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
        
        # 2. ✅ СОХРАНЯЕМ В БД
        await db.set_pro_aspect_ratio(user_id, aspect_ratio)
        
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
@pro_mode_router.callback_query(F.data.startswith("res_"), StateFilter(ProModeStates.choosing_pro_params))
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
        
        # 2. ✅ СОХРАНЯЕМ В БД
        # Сначала устанавливаем разрешение
        await db.set_pro_resolution(user_id, resolution)
        # Затем устанавливаем режим на PRO
        await db.set_user_pro_mode(user_id, mode=True)
        
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
        
        await callback.answer(f"✅ Разрешение: {resolution} | Режим: PRO 🔧")
        logger.info(f"✅ [PRO_MODE] Пользователь {user_id} выбрал разрешение {resolution} и PRO режим")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в select_resolution: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ============================================
# HANDLER 6: Back to mode selection
# ============================================
@pro_mode_router.callback_query(F.data == "profile_settings", StateFilter(ProModeStates.choosing_pro_params))
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
        
        # Получаем актуальный режим из БД
        pro_settings = await db.get_user_pro_settings(user_id)
        current_mode_is_pro = pro_settings.get('pro_mode', False)
        
        # 2. Меняем состояние
        await state.set_state(ProModeStates.choosing_mode)
        
        # 3. Восстанавливаем важные данные
        await state.update_data(
            menu_message_id=menu_message_id,
            current_mode_is_pro=current_mode_is_pro
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
                current_mode_is_pro=current_mode_is_pro
            ),
            show_balance=True,
            screen_code='profile_settings'
        )
        
        await callback.answer()
        logger.info(f"✅ [PRO_MODE] Вернулись к выбору режима для {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [PRO_MODE] Ошибка в back_to_mode_selection: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
