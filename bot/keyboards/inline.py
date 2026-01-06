# keyboards/inline.py

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup



# --- Настройки пакетов для покупки ---
PACKAGES = {
    10: 190,
    25: 450,
    50: 850
}

# --- Настройки комнат ---
ROOM_TYPES = {
    "living_room": "Гостиная",
    "bedroom": "Спальня",
    "kitchen": "Кухня",
    "dining_room": "Столовая",
    "home_office": "Кабинет",
    "Entryway": "Прихожая",
    "bathroom_full": "Ванная",
    "toilet": "Санузел",
    "wardrobe": "Гардеробная",
    "nursery": "Детская (малыш)",
}



# ========================================
# НОВЫЕ СТРАНИЦЫ СТИЛЕЙ ДЛЯ PHASE 1.3.2
# ========================================
STYLE_PAGE_1 = [
    ("modern", "Современный"),
    ("minimalist", "Минимализм"),
    ("scandinavian", "Скандинавский"),
    ("industrial", "Индустриальный"),
    ("rustic", "Рустик"),
    ("japandi", "Джапанди"),
    ("boho", "Бохо"),
    ("midcentury", "Midcentury"),
    ("artdeco", "Артдеко"),
    ("coastal", "Прибрежный"),
    ("organic_modern", "Органический Модерн"),
    ("loft", "Лофт"),
]

STYLE_PAGE_2 = [
    ("warm_luxury", "Теплая роскошь"),
    ("neo_art_deco", "Нео Арт Деко"),
    ("conscious_eclectics", "Осознанная электика"),
    ("tactile_maximalism", "Тактильный Максимализм"),
    ("country", "Кантри"),
    ("grunge", "Гранж"),
    ("cyberpunk", "Киберпанк"),
    ("eclectic", "Екклектика"),
    ("gothic", "Готика"),
    ("futurism", "Футуризм"),
    ("baroque", "Барокко"),
    ("classicism", "Классицизм"),
]

# Структура для комнат с emoji
ROOMS_WITH_EMOJI = [
    ("💪 Гостиная", "room_living_room"),
    ("🍽 Кухня", "room_kitchen"),
    ("🛏 Спальня", "room_bedroom"),
    ("👶 Детская", "room_nursery"),
    ("🏠 Студия", "room_studio"),
    ("💼 Кабинет", "room_home_office"),
    ("🚿 Ванная", "room_bathroom_full"),
    ("🚿 Санузел", "room_toilet"),
    ("🚪 Прихожая", "room_entryway"),
    ("👗 Гардеробная", "room_wardrobe"),
]


# РЕЖИМ ПРО _ НАСТПРОЙКИ
# --- Параметры PRO MODE ---
ASPECT_RATIOS = ["16:9", "4:3", "1:1", "9:16"]
RESOLUTIONS = ["1K", "2K", "4K"]




# ========================================
# SCREEN 0: ГЛАВНОЕ МЕНЮ - 3 КНОПКИ
# РЕАЛИЗАЦИЯ: 2025-12-30 23:45
# ========================================

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    SCREEN 0: Главное меню с 3 кнопками
    Используется при /start команде
    
    Структура:
    - Ряд 1: 🎨 Создать дизайн
    - Ряд 2: 👤 Личный кабинет
    - Ряд 3: ⚙️ Админ
    
    Каждая кнопка в отдельном ряду (по одной)
    По документации QUICK-REFERENCE.md (2025-12-30)
    """
    builder = InlineKeyboardBuilder()

    # Ряд 1: Создать дизайн
    builder.row(InlineKeyboardButton(
        text="🎨 Создать дизайн помещения или фасада дома",
        callback_data="create_design"
    ))
    
    # Ряд 2: Личный кабинет
    builder.row(InlineKeyboardButton(
        text="👤 Личный кабинет",
        callback_data="show_profile"
    ))
    
    # Ряд 3: Админ панель (только для админов)
    builder.row(InlineKeyboardButton(
        text="⚙️ Админ",
        callback_data="admin_panel"
    ))

    builder.adjust(1)
    return builder.as_markup()


# ========================================
# SCREEN 1: SELECTING_MODE - 5 РЕЖИМОВ + РАЗДЕЛИТЕЛЬ
# РЕАЛИЗАЦИЯ: 2025-12-30 23:45
# ПЕРЕИМЕНОВАНА ИЗ: get_work_mode_selection_keyboard()
# ========================================

def get_mode_selection_keyboard() -> InlineKeyboardMarkup:
    """
    SCREEN 1: Режимы работы с 5 кнопками + разделитель
    Используется после нажатия "Создать дизайн" на SCREEN 0
    
    Структура:
    - Ряд 1: 📋 Создать новый дизайн → select_mode_new_design
    - Ряд 2: ✏️ Редактировать дизайн → select_mode_edit_design
    - Ряд 3: 🎁 Примерить дизайн → select_mode_sample_design
    - Ряд 4: 🛋️ Расставить мебель → select_mode_arrange_furniture
    - Ряд 5: 🏠 Дизайн фасада → select_mode_facade_design
    - Ряд 6: 👤 Личный кабинет (разделитель) → show_profile
    
    По документации QUICK-REFERENCE.md (2025-12-30)
    FSM State: CreationStates.selecting_mode
    """
    builder = InlineKeyboardBuilder()

    # Ряд 1: Создать новый дизайн
    builder.row(InlineKeyboardButton(
        text="📋 Создать новый дизайн помещения   ",
        callback_data="select_mode_new_design"
    ))
    
    # Ряд 2: Редактировать дизайн
    builder.row(InlineKeyboardButton(
        text="✏️ Редактировать дизайн текстом    ",
        callback_data="select_mode_edit_design"
    ))
    
    # Ряд 3: Примерить дизайн
    builder.row(InlineKeyboardButton(
        text="🎁 Примерить дизайн на помещение    ",
        callback_data="select_mode_sample_design"
    ))
    
    # Ряд 4: Расставить мебель
    builder.row(InlineKeyboardButton(
        text="🛋️ Расставить мебель в помещении   ",
        callback_data="select_mode_arrange_furniture"
    ))
    
    # Ряд 5: Дизайн фасада
    builder.row(InlineKeyboardButton(
        text="🏠 Дизайн фасада дома",
        callback_data="select_mode_facade_design"
    ))

    # Ряд 6: Личный кабинет (разделитель)
    #builder.row(InlineKeyboardButton(
        #text="          👤 Личный кабинет           ",
        #callback_data="show_profile"
    #))

    builder.adjust(1)
    return builder.as_markup()


# Используется для обратной совместимости (старое имя)
def get_work_mode_selection_keyboard() -> InlineKeyboardMarkup:
    """
    ✅ ИСПРАВЛЕНО (2025-12-30 15:20)
    Сохранена для обратной совместимости
    Вызывает get_mode_selection_keyboard() БЕЗ параметров
    """
    return get_mode_selection_keyboard()


# ========================================
# SCREEN 2: UPLOADING_PHOTO - КЛАВИАТУРА
# 🆕 [2026-01-02 22:00] ОБНОВЛЕНА С ДВУМЯ КНОПКАМИ
# 🔧 [2026-01-02 22:47] ИСПРАВЛЕНА - скрываем при первом старте
# ========================================

def get_uploading_photo_keyboard(has_previous_photo: bool = False) -> InlineKeyboardMarkup:
    """
    🔧 [2026-01-02 22:47] SCREEN 2: ОБНОВЛЕНА ЛОГИКА КНОПОК
    
    НОВОЕ:
    - Кнопка "📸 Использовать текущую фото" - ТОЛЬКО если has_previous_photo=True
    - Кнопка "🏠 Главное меню" - ВСЕГДА
    
    Параметры:
    - has_previous_photo: bool - есть ли сохраненная фото в БД?
    
    ВАЖНО:
    При первом старте бота (свежая сессия):
    - has_previous_photo = False
    - Показываем ТОЛЬКО "🏠 Главное меню"
    
    После загрузки первой фото или повторного использования:
    - has_previous_photo = True
    - Показываем ОБРАЯЕ кнопки:
      * 📸 Использовать текущую фото
      * 🏠 Главное меню
    
    Вызов:
    1. [SCREEN 1→2] set_work_mode() → db.get_last_user_photo(user_id)
    2. Передает has_previous_photo в get_uploading_photo_keyboard(has_previous_photo=...)
    3. Клавиатура выстраивается динамически
    
    Обработчики callback:
    - "use_current_photo" → use_current_photo() в creation_main.py
    - "select_mode" → вернуться на SCREEN 1 выбора режимов
    """
    builder = InlineKeyboardBuilder()
    
    # 🔧 ТОЛЬКО если есть сохраненная фото в БД!
    if has_previous_photo:
        builder.row(InlineKeyboardButton(
            text="📸 Использовать текущее фото",
            callback_data="use_current_photo"
        ))
    
    # Кнопка "Главное меню" - ВСЕГДА показываем
    builder.row(InlineKeyboardButton(
        text="🏠 Выбрать режим работы",
        callback_data="select_mode"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


# ========================================
# [LEGACY] get_room_keyboard() - ДЛЯ СОВМЕСТИМОСТИ
# Используется в creation_exterior_interior.py
# ========================================

def get_room_keyboard() -> InlineKeyboardMarkup:
    """
    🔧 [2026-01-02 17:30] ВОССТАНОВЛЕНА ДЛЯ СОВМЕСТИМОСТИ
    
    Старая функция выбора комнаты после генерации или очистки
    Используется в legacy обработчике creation_exterior_interior.py
    
    ВНИМАНИЕ: Это устаревшая функция!
    В новой архитектуре используйте get_room_choice_keyboard()
    """
    builder = InlineKeyboardBuilder()

    # ЗАКОММЕНТИРОВАНО 2025-12-08 согласно ТЗ:
    #builder.row(InlineKeyboardButton(text="🧭 Очистить пространство", callback_data="clear_space_confirm"))

    # Комнаты
    for key, text in ROOM_TYPES.items():
        builder.row(InlineKeyboardButton(text=text, callback_data=f"room_{key}"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode"))
    builder.adjust(2)
    return builder.as_markup()


# ========================================
# SCREEN 3: ROOM_CHOICE - ВЫБОР ТИПА КОМНАТЫ
# ========================================

def get_room_choice_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора комнаты (SCREEN 3: ROOM_CHOICE)
    10 комнат, по 2 в ряд
    """
    builder = InlineKeyboardBuilder()
    for i in range(0, len(ROOMS_WITH_EMOJI), 2):
        buttons = [InlineKeyboardButton(
            text=ROOMS_WITH_EMOJI[i][0],
            callback_data=ROOMS_WITH_EMOJI[i][1]
        )]
        if i + 1 < len(ROOMS_WITH_EMOJI):
            buttons.append(InlineKeyboardButton(
                text=ROOMS_WITH_EMOJI[i+1][0],
                callback_data=ROOMS_WITH_EMOJI[i+1][1]
            ))
        builder.row(*buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Новое фото              ", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Режим работы            ", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ========================================
# SCREEN 4: CHOOSE_STYLE_1 - ВЫБОР СТИЛЯ (СТРАНИЦА 1)
# ========================================

def get_choose_style_1_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора стиля 1 (SCREEN 4: CHOOSE_STYLE_1)
    12 стилей, по 2 в ряд
    """
    builder = InlineKeyboardBuilder()
    for i in range(0, len(STYLE_PAGE_1), 2):
        buttons = [InlineKeyboardButton(
            text=STYLE_PAGE_1[i][1],
            callback_data=f"style_{STYLE_PAGE_1[i][0]}"
        )]
        if i + 1 < len(STYLE_PAGE_1):
            buttons.append(InlineKeyboardButton(
                text=STYLE_PAGE_1[i+1][1],
                callback_data=f"style_{STYLE_PAGE_1[i+1][0]}"
            ))
        builder.row(*buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ К комнате", callback_data="room_choice"),
        InlineKeyboardButton(text="▶️ Ещё", callback_data="choose_style_2"),
        #InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    
    )
        # ✅ ПРАВИЛЬНЫЙ ADJUST: 2 для стилей, 1 для последнего ряда
    builder.adjust(2, 2, 2, 2, 2, 2, 2, 1)  # 6 рядов со стилями (по 2) + 1 ряд с 3 кнопками
    return builder.as_markup()


# ========================================
# SCREEN 5: CHOOSE_STYLE_2 - ВЫБОР СТИЛЯ (СТРАНИЦА 2)
# ========================================

def get_choose_style_2_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора стиля 2 (SCREEN 5: CHOOSE_STYLE_2)
    12 эндовых стилей, по 2 в ряд
    """
    builder = InlineKeyboardBuilder()
    for i in range(0, len(STYLE_PAGE_2), 2):
        buttons = [InlineKeyboardButton(
            text=STYLE_PAGE_2[i][1],
            callback_data=f"style_{STYLE_PAGE_2[i][0]}"
        )]
        if i + 1 < len(STYLE_PAGE_2):
            buttons.append(InlineKeyboardButton(
                text=STYLE_PAGE_2[i+1][1],
                callback_data=f"style_{STYLE_PAGE_2[i+1][0]}"
            ))
        builder.row(*buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="styles_page_1"),
        #InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    # ✅ ПРАВИЛЬНЫЙ ADJUST: 2 для каждого ряда стилей + 2 для навигации
    builder.adjust(2, 2, 2, 2, 2, 2, 1)  # 6 рядов стилей (по 2) + 1 ряд навигации (по 2)
    return builder.as_markup()


# ========================================
# SCREEN 6: POST_GENERATION - ПОСЛЕ ГЕНЕРАЦИИ
# ========================================

def get_post_generation_keyboard(show_continue_editing: bool = False) -> InlineKeyboardMarkup:
    """
    ОСНОВНАЯ версия клавиатуры после генерации (SCREEN 6).
    Используется для всех сценариев генерации.

    Логика:
    - Если show_continue_editing = True → РУЧНОЙ ПРОМПТ (дом, участок, другое помещение)
      Ряд 1: [✏️ Продолжить редактирование] [📸 Новое фото]
    - Если show_continue_editing = False → ГЕНЕРАЦИЯ ПО СТИЛЮ
      Ряд 1: [🔄 Другой стиль] [📸 Новое фото]
    - Ряд 2: [🏠 Главное меню]
    
    ОБНОВЛЕНО: 2025-12-29 16:35 (PHASE 1.3.3 cleanup)
    """
    builder = InlineKeyboardBuilder()

    # Ряд 1: две кнопки в ряд
    if show_continue_editing:
        # Ручной промпт
        builder.row(
            InlineKeyboardButton(text="✏️ Продолжить редактирование", callback_data="continue_editing"),
            InlineKeyboardButton(text="📸 Новое фото", callback_data="uploading_photo"),
        )
    else:
        # Генерация по стилю
        builder.row(
            InlineKeyboardButton(text="🔄 Другой стиль      ", callback_data="change_style"),
            InlineKeyboardButton(text="📸 Новое фото         ", callback_data="uploading_photo"),
        )

    # Ряд 2: Главное меню (широкая)
    builder.row(InlineKeyboardButton(text="🏠 Выбрать новый режим    ", callback_data="select_mode"))

    return builder.as_markup()


# ========================================
# SCREEN 7: TEXT_INPUT - ТЕКСТОВЫЙ ВВОД
# ========================================

def get_text_input_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура текстового редактирования (SCREEN 7: TEXT_INPUT)
    После ввода текста пользователь может вернуться назад
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_from_text_input"
    ))
    builder.adjust(1)
    return builder.as_markup()


# ========================================
# SCREEN 8: EDIT_DESIGN - МЕНЮ РЕДАКТИРОВАНИЯ
# ========================================

def get_edit_design_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура редактирования дизайна (SCREEN 8: EDIT_DESIGN)
    Опции: очистить фото, ввести текст, новое фото, главное меню
    
    NSI: callback_data должны быть clear_space_confirm, не clear_confirm!
    """
    builder = InlineKeyboardBuilder()
    
    # Первый ряд
    builder.row(
        InlineKeyboardButton(text="Очистить фото", callback_data="clear_space_confirm_keyboard"),
        InlineKeyboardButton(text="Текстовый редактор", callback_data="text_input")
    )
    
    # Второй ряд
    builder.row(
        InlineKeyboardButton(text="⬅️ Новое фото", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Режим работы", callback_data="select_mode")
    )
    
    builder.adjust(2, 2)
    return builder.as_markup()


# ========================================
# SCREEN 9: CLEAR_CONFIRM - ПОДТВЕРЖДЕНИЕ ОЧИСТКИ
# ========================================

def get_clear_space_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения очистки пространства (SCREEN 9)
    ОСНОВНАЯ ФУНКЦИЯ для SCREEN 9!
    
    Дата: 2025-12-08
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Очистить", callback_data="clear_space_execute"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="clear_space_cancel"))
    builder.adjust(1)
    return builder.as_markup()


# ========================================
# SCREEN 10: DOWNLOAD_SAMPLE - ЗАГРУЗКА ОБРАЗЦА
# ========================================

def get_download_sample_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура лоадинга образца (SCREEN 10: DOWNLOAD_SAMPLE)
    Навигация на главное меню и назад к загружению
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ========================================
# SCREEN 11: GENERATION_TRY_ON - ГЕНЕРАЦИЯ ПРИМЕРКИ
# ========================================

def get_generation_try_on_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура генерации примерки (SCREEN 11: GENERATION_TRY_ON)
    Кнопка генерации + навигация
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎨 Примерить дизайн",
        callback_data="generate_try_on"
    ))
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="download_sample"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ========================================
# SCREEN 12: POST_GENERATION_SAMPLE - РЕЗУЛЬТАТ ПРИМЕРКИ
# ========================================

def get_post_generation_sample_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после примерки (SCREEN 12: POST_GENERATION_SAMPLE)
    Основные действия: текст, новый образец
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✏️ Текстовое редактирование",
        callback_data="text_input"
    ))
    builder.row(
        InlineKeyboardButton(text="📸 Новый образец", callback_data="download_sample"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ========================================
# SCREEN 13: UPLOADING_FURNITURE - ЗАГРУЗКА МЕБЕЛИ
# ========================================

def get_uploading_furniture_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура загружения фото мебели (SCREEN 13: UPLOADING_FURNITURE)
    Навигация: назад, меню
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ========================================
# SCREEN 14: GENERATION_FURNITURE - ГЕНЕРАЦИЯ МЕБЕЛИ
# ========================================

def get_generation_furniture_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура генерации мебели (SCREEN 14: GENERATION_FURNITURE)
    Кнопка генерации + навигация
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎨 Расставить мебель",
        callback_data="generate_furniture"
    ))
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="uploading_furniture"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ========================================
# SCREEN 15: POST_GENERATION_FURNITURE - РЕЗУЛЬТАТ МЕБЕЛИ
# ========================================

def get_post_generation_furniture_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после остановки мебели (SCREEN 15: POST_GENERATION_FURNITURE)
    Основные действия: текст, новая мебель
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✏️ Текстовое редактирование",
        callback_data="text_input"
    ))
    builder.row(
        InlineKeyboardButton(text="🛋 Новая мебель", callback_data="uploading_furniture"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ========================================
# SCREEN 16: LOADING_FACADE_SAMPLE - ЗАГРУЗКА ОБРАЗЦА ФАСАДА
# ========================================

def get_loading_facade_sample_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура лоадинга образца фасада (SCREEN 16: LOADING_FACADE_SAMPLE)
    Навигация по фасадам
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ========================================
# SCREEN 17: GENERATION_FACADE - ГЕНЕРАЦИЯ ФАСАДА
# ========================================

def get_generation_facade_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура генерации дизайна фасада (SCREEN 17: GENERATION_FACADE)
    Кнопка генерации + навигация
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎨 Оформить фасад",
        callback_data="generate_facade"
    ))
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="loading_facade_sample"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ========================================
# SCREEN 18: POST_GENERATION_FACADE - РЕЗУЛЬТАТ ФАСАДА
# ========================================

def get_post_generation_facade_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после оформления фасада (SCREEN 18: POST_GENERATION_FACADE)
    Основные действия: текст, новый образец
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✏️ Текстовое редактирование",
        callback_data="text_input"
    ))
    builder.row(
        InlineKeyboardButton(text="📸 Новый образец", callback_data="loading_facade_sample"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ========================================
# ПРОФИЛЬ И ФИНАНСЫ
# ========================================

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    ФИНАЛЬНО ОБНОВЛЕНА: 2025-12-24 13:05
    """
    builder = InlineKeyboardBuilder()

    # Ряд 1: Купить генерации
    builder.row(
        InlineKeyboardButton(text="💳 Стоимость генераций", callback_data="buy_generations")
    )

    # Ряд 2: Настройки режима | Поддержка
    builder.row(
        InlineKeyboardButton(text="⚙️ НАСТРОЙКИ РЕЖИМА", callback_data="profile_settings"),
        InlineKeyboardButton(text="💬 Поддержка", callback_data="show_support")
    )

    # Ряд 3: Главное меню
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode"))

    builder.adjust(1, 2, 1)
    return builder.as_markup()


def get_payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tokens, price in PACKAGES.items():
        button_text = f"{tokens} генераций - {price} руб."
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"pay_{tokens}_{price}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))
    builder.adjust(2)
    return builder.as_markup()

def get_payment_check_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Перейти к оплате", url=url))
    builder.row(InlineKeyboardButton(text="⬅️ Назад ", callback_data="show_profile"))
    builder.adjust(1)
    return builder.as_markup()


# ========================================
# PRO MODE - ФИНАЛЬНЫЕ КЛАВИАТУРЫ
# ✅ ПЕРЕИМЕНОВАНА (2025-12-30 15:20)
# get_mode_selection_keyboard(current_mode_is_pro) → get_pro_mode_selection_keyboard()
# ========================================

def get_pro_mode_selection_keyboard(current_mode_is_pro: bool) -> InlineKeyboardMarkup:
    """
    ✅ ПЕРЕИМЕНОВАНА (2025-12-30 15:20)
    Клавиатура экрана выбора режима СТАНДАРТ vs PRO
    
    Было: get_mode_selection_keyboard(current_mode_is_pro: bool) - конфликт имён
    Теперь: get_pro_mode_selection_keyboard(current_mode_is_pro: bool) - уникальное имя
    """
    builder = InlineKeyboardBuilder()
    std_mark = "" if current_mode_is_pro else "✅"
    pro_mark = "✅" if current_mode_is_pro else ""
    builder.row(
        InlineKeyboardButton(
            text=f"{std_mark} 📋 СТАНДАРТ".strip(),
            callback_data="mode_std"
        ),
        InlineKeyboardButton(
            text=f"{pro_mark} 🔧 PRO".strip(),
            callback_data="mode_pro"
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    builder.adjust(2, 2)
    return builder.as_markup()


def get_pro_params_keyboard(
    current_ratio: str = "16:9",
    current_resolution: str = "1K"
) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора параметров PRO режима
    """
    builder = InlineKeyboardBuilder()
    aspect_buttons = []
    for ratio in ASPECT_RATIOS:
        mark = "✅" if ratio == current_ratio else ""
        button_text = f"{mark} {ratio}".strip()
        aspect_buttons.append(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"aspect_{ratio}"
            )
        )
    builder.row(*aspect_buttons)
    resolution_buttons = []
    for resolution in RESOLUTIONS:
        mark = "✅" if resolution == current_resolution else ""
        button_text = f"{mark} {resolution}".strip()
        resolution_buttons.append(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"res_{resolution}"
            )
        )
    builder.row(*resolution_buttons)
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к режимам", callback_data="profile_settings"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()
