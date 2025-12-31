# keyboards/inline.py
# Дата объединения: 05.12.2025
# --- ОБНОВЛЕН: 2025-12-30 23:45 ---
# [2025-12-30 23:45] ИСПРАВЛЕНИЕ: РАЗДЕЛЕНЫ SCREEN 0 и SCREEN 1 согласно QUICK-REFERENCE.md
# [2025-12-30 23:45] НОВАЯ: get_main_menu_keyboard() для SCREEN 0 (3 кнопки)
# [2025-12-30 23:45] ПЕРЕИМЕНОВАНА: get_work_mode_selection_keyboard() → get_mode_selection_keyboard()
# [2025-12-30 15:20] 🔧 CRITICAL FIX: get_mode_selection_keyboard(current_mode_is_pro) → get_pro_mode_selection_keyboard()
#                    - Удален конфликт имён
#                    - Теперь get_work_mode_selection_keyboard() вызывает правильную функцию
# [2025-12-31 12:36] 🔥 CRITICAL: Remove back button from SCREEN 2
#                    - get_uploading_photo_keyboard() now has NO buttons
#                    - User must upload photo to proceed

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

# --- 16 стилей, 2 кнопки в ряд ---
STYLE_TYPES = [
    ("modern", "Современный"),
    ("minimalist", "Минимализм"),
    ("scandinavian", "Скандинавский"),
    ("industrial", "Индустриальный (лофт)"),
    ("rustic", "Рустик"),
    ("japandi", "Джапанди"),
    ("boho", "Бохо / Эклектика"),
    ("midcentury", "Mid‭‑century / винтаж"),
    ("artdeco", "Арт‭деко"),
    ("coastal", "Прибрежный"),
    ("Organic Modern", "Органический Модерн"),
    ("Loft", "Лофт"),
]

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
    ("midcentury", "Mid-century"),
    ("artdeco", "Арт-деко"),
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
        text="🎨 Создать дизайн",
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
# SCREEN 1: РЕЖИМЫ РАБОТЫ - 5 РЕЖИМОВ + РАЗДЕЛИТЕЛЬ
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
        text="📋 Создать новый дизайн",
        callback_data="select_mode_new_design"
    ))
    
    # Ряд 2: Редактировать дизайн
    builder.row(InlineKeyboardButton(
        text="✏️ Редактировать дизайн",
        callback_data="select_mode_edit_design"
    ))
    
    # Ряд 3: Примерить дизайн
    builder.row(InlineKeyboardButton(
        text="🎁 Примерить дизайн",
        callback_data="select_mode_sample_design"
    ))
    
    # Ряд 4: Расставить мебель
    builder.row(InlineKeyboardButton(
        text="🛋️ Расставить мебель",
        callback_data="select_mode_arrange_furniture"
    ))
    
    # Ряд 5: Дизайн фасада
    builder.row(InlineKeyboardButton(
        text="🏠 Дизайн фасада дома",
        callback_data="select_mode_facade_design"
    ))

    # Ряд 6: Личный кабинет (разделитель)
    builder.row(InlineKeyboardButton(
        text="👤 Личный кабинет",
        callback_data="show_profile"
    ))

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


# Экран загружения фото
def get_uploading_photo_keyboard() -> InlineKeyboardMarkup:
    """
    🔥 [2025-12-31 12:36] SCREEN 2: NO BUTTONS!
    
    SCREEN 2 (uploading_photo) должен быть чистым:
    - Только текст с инструкциями
    - БЕЗ кнопок
    - Юзер должен загрузить фото или закрыть Telegram
    - Нет способа вернуться назад
    
    Это сфокусирует юзера на загрузке фото.
    """
    # ✅ ИСПРАВЛЕНО: Вернуть пустую клавиатуру
    return InlineKeyboardMarkup(inline_keyboard=[])


# Экран выбора что на фото - дом или комнаты
def get_what_is_in_photo_keyboard() -> InlineKeyboardMarkup:
    """
    НОВАЯ КЛАВИАТУРА: Экран "Что на фото" - 10 кнопок + Главное меню

    Структура (по 2 в ряд):
    - Ряд 1: Дом (фасад) | Участок / двор [ЭКСТЕРЬЕР]
    - Ряд 2-5: 8 комнат интерьера [ИНТЕРЬЕР]
    - Ряд 6: Главное меню

    Дата создания: 2025-12-08
    """
    builder = InlineKeyboardBuilder()

    # Ряд 1: ЭКСТЕРЬЕР (2 кнопки)
    builder.row(
       # InlineKeyboardButton(text="🏠 Дом (фасад)", callback_data="scene_house_exterior"),
       # InlineKeyboardButton(text="🌳 Участок / двор", callback_data="scene_plot_exterior")
    )

    # Ряд 2: ИНТЕРЬЕР - Гостиная и Кухня
    builder.row(
        InlineKeyboardButton(text="🛋 Гостиная", callback_data="room_living_room"),
        InlineKeyboardButton(text="🍽 Кухня", callback_data="room_kitchen")
    )

    # Ряд 3: ИНТЕРЬЕР - Спальня и Детская
    builder.row(
        InlineKeyboardButton(text="🛏 Спальня", callback_data="room_bedroom"),
        InlineKeyboardButton(text="👶 Детская", callback_data="room_nursery")
    )

    # Ряд 4: ИНТЕРЬЕР - Ванная и Кабинет
    builder.row(
        InlineKeyboardButton(text="🚿 Ванная / санузел", callback_data="room_bathroom_full"),
        InlineKeyboardButton(text="💼 Кабинет", callback_data="room_home_office")
    )

    builder.row(
        InlineKeyboardButton(text="🛋 Прихожая", callback_data="Entryway"),
        InlineKeyboardButton(text="🍽 Гардеробная", callback_data="wardrobe")
    )

    # Ряд 5: ИНТЕРЬЕР - Другое помещение и Комната целиком
    builder.row(
        InlineKeyboardButton(text="🔍 Другое помещение", callback_data="room_other"),
        InlineKeyboardButton(text="🏡 Комната целиком", callback_data="room_studio")
    )

    # Ряд 6: Главное меню
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode"))

    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup()


# Экран выбора комнаты после генерации или очистки
def get_room_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    # ЗАКОММЕНТИРОВАНО 2025-12-08 согласно ТЗ:
    #builder.row(InlineKeyboardButton(text="🧭 Очистить пространство", callback_data="clear_space_confirm"))

    # Комнаты
    for key, text in ROOM_TYPES.items():
        builder.row(InlineKeyboardButton(text=text, callback_data=f"room_{key}"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode"))
    builder.adjust(2)
    return builder.as_markup()


#  Экран выбора стилей
def get_style_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # 16 стилей — 2 в ряд
    style_rows = [STYLE_TYPES[i:i + 2] for i in range(0, len(STYLE_TYPES), 2)]
    for row in style_rows:
        buttons = [
            InlineKeyboardButton(text=style_name, callback_data=f"style_{style_key}")
            for style_key, style_name in row
        ]
        builder.row(*buttons)
    # Кнопка "К выбору комнаты" и "Главное меню" — отдельно
    builder.row(
        InlineKeyboardButton(text="🧭 Очистить пространство", callback_data="clear_space_confirm"),
        InlineKeyboardButton(text="⬅️ Выбрать комнату", callback_data="back_to_room"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode"),
    )
    return builder.as_markup()


# Экран после генерации  или очистки помещения
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
            InlineKeyboardButton(text="📸 Новое фото", callback_data="create_design"),
        )
    else:
        # Генерация по стилю
        builder.row(
            InlineKeyboardButton(text="🔄 Другой стиль      ", callback_data="change_style"),
            InlineKeyboardButton(text="📸 Новое фото         ", callback_data="create_design"),
        )

    # Ряд 2: Главное меню (широкая)
    builder.row(InlineKeyboardButton(text="🏠 Главное меню    ", callback_data="select_mode"))

    return builder.as_markup()


# Экран подтверждения очистки пространства
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


# Экран Личного кабинета
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
# SCREEN 2-5 - ЗАГРУЗКА ФОТО И ВЫБОР СТИЛЕЙ
# ОБНОВЛЕНО: 2025-12-29 16:21
# ========================================

def get_room_choice_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора комнаты (ЭКРАН 3: ROOM_CHOICE)
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
        InlineKeyboardButton(text="⬅️ Новое фото", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_choose_style_1_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора стиля 1 (ЭКРАН 4: CHOOSE_STYLE_1)
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode"),
        InlineKeyboardButton(text="▶️ Ещё", callback_data="choose_style_2")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_choose_style_2_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора стиля 2 (ЭКРАН 5: CHOOSE_STYLE_2)
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
        InlineKeyboardButton(text="⬅️ Назад", callback_data="choose_style_1"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ========================================
# SCREEN 7-8 - ТЕКСТОВЫЙ ВВОД И РЕДАКТИРОВАНИЕ
# ОБНОВЛЕНО: 2025-12-29 16:35
# ========================================

def get_text_input_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура текстового редактирования (ЭКРАН 7: TEXT_INPUT)
    После ввода текста пользователь может вернуться назад
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_from_text_input"
    ))
    builder.adjust(1)
    return builder.as_markup()


def get_edit_design_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура редактирования дизайна (ЭКРАН 8: EDIT_DESIGN)
    Опции: очистить фото, ввести текст, новое фото, главное меню
    
    NSI: callback_data должны быть clear_space_confirm, не clear_confirm!
    """
    builder = InlineKeyboardBuilder()
    
    # Первый ряд
    builder.row(
        InlineKeyboardButton(text="📁 Очистить фото", callback_data="clear_space_confirm"),
        InlineKeyboardButton(text="📑 Ввести текст", callback_data="text_input")
    )
    
    # Второй ряд
    builder.row(
        InlineKeyboardButton(text="⬅️ Новое фото", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    
    builder.adjust(2, 2)
    return builder.as_markup()


# ========================================
# SCREEN 10-18 - НОВЫЕ МОДЫ (УНИВЕРСАЛЬНЫЕ)
# ОБНОВЛЕНО: 2025-12-29 16:38
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
