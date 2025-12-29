# keyboards/inline.py
# Дата объединения: 05.12.2025
# --- ОБНОВЛЕН: 2025-12-24 13:12 ---
# [2025-12-08 13:50] Добавлена новая клавиатура get_what_is_in_photo_keyboard() - 10 кнопок (интерьер+экстерьер)
# [2025-12-08 13:50] УДАЛЕНА кнопка "Очистить пространство" из get_room_keyboard() согласно ТЗ
# [2025-12-24 13:12] ОКОНЧАТЕЛЬНАЕ РЕАЛИЗАЦИЕ: 4 кнопки СООТНОШЕНИЯ В ОДНОМ РЯДУ (по 25% каждая)
# [2025-12-29 15:20] PHASE 1.3.1: Добавлена новая функция get_work_mode_selection_keyboard() для SCREEN 1
# [2025-12-29 16:21] PHASE 1.3.2: Добавлены клавиатуры для SCREEN 2-5
# [2025-12-29 16:31] ФИКС: Оставлена старая get_clear_space_confirm_keyboard(), обновлены все связи
# [2025-12-29 16:35] ФИКС: Удалена get_post_generation_keyboard_new(), оставлена только старая версия

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

#  Экран главный
def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню с кнопкой админ-панели для админов"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="                   🎨 Создать дизайн       "
                                          "                  ", callback_data="create_design"))
    builder.row(InlineKeyboardButton(text="                   👤 Личный кабинет          "
                                          "                    ", callback_data="show_profile"))
    if is_admin:
        builder.row(InlineKeyboardButton(text="         ⚙️ Админ-панель        ", callback_data="admin_panel"))
    builder.adjust(1)
    return builder.as_markup()

# Экран загружения фото
def get_upload_photo_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для экрана загружения фото с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


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
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))

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
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
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
    builder.row(InlineKeyboardButton(text="🏠 Главное меню    ", callback_data="main_menu"))

    return builder.as_markup()


# Экран подтверждения очистки пространства
def get_clear_space_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения очистки пространства (SCREEN 9)
    ОСНОВНАЯ ФУНКЦИя для SCREEN 9!
    
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
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))

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
# PHASE 1.3.1: SCREEN 1 - MODE SELECTION KEYBOARD
# ОБНОВЛЕНО: 2025-12-29 15:20
# ========================================

def get_work_mode_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора режима работы (ЭКРАН 1: MAIN_MENU)
    Все 5 режимов + разделитель
    """
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="📋 Создать новый дизайн",
        callback_data="select_mode_new_design"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Редактировать дизайн",
        callback_data="select_mode_edit_design"
    ))
    builder.row(InlineKeyboardButton(
        text="🎁 Примерить дизайн",
        callback_data="select_mode_sample_design"
    ))
    builder.row(InlineKeyboardButton(
        text="🛋️ Расставить мебель",
        callback_data="select_mode_arrange_furniture"
    ))
    builder.row(InlineKeyboardButton(
        text="🏠 Дизайн фасада дома",
        callback_data="select_mode_facade_design"
    ))

    # Разделитель
    builder.row(InlineKeyboardButton(
        text="─────────",
        callback_data="dummy_separator"
    ))

    builder.adjust(1)
    return builder.as_markup()


# ========================================
# PHASE 1.3.2: SCREEN 2-5 - НОВЫЕ КЛАВИАТУРЫ
# ОБНОВЛЕНО: 2025-12-29 16:21
# ========================================

def get_uploading_photo_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура загрузки фото (ЭКРАН 2: UPLOADING_PHOTO)
    Динамический текст зависит от режима работы
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🏠 Вернуться к режимам",
        callback_data="select_mode"
    ))
    builder.adjust(1)
    return builder.as_markup()


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
# PHASE 1.3.3: SCREEN 7-8 - ТЕКСТОВЫЙ ВВОД И РЕДАКТИРОВАНИЕ
# ОБНОВЛЕНО: 2025-12-29 16:35
# ФИКС: Удалена get_post_generation_keyboard_new()
# СОХРАНЕНЫ: get_post_generation_keyboard() и get_clear_space_confirm_keyboard()
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
# PRO MODE - ФИНАЛЬНЫЕ КЛАВИАТУРЫ
# ОБНОВЛЕНО: 2025-12-24 13:12
# ========================================

def get_mode_selection_keyboard(current_mode_is_pro: bool) -> InlineKeyboardMarkup:
    """
    Клавиатура экрана выбора режима СТАНДАРТ vs PRO
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
