# keyboards/inline.py
# Дата объединения: 05.12.2025
# --- ОБНОВЛЕН: 2025-12-24 13:05 ---
# [2025-12-08 13:50] Добавлена новая клавиатура get_what_is_in_photo_keyboard() - 10 кнопок (интерьер+экстерьер)
# [2025-12-08 13:50] УДАЛЕНА кнопка "Очистить пространство" из get_room_keyboard() согласно ТЗ
# [2025-12-08 13:50] Функция get_clear_space_confirm_keyboard() СОХРАНЕНА для будущего использования
# [2025-12-24 13:05] ФИНАЛЬНАЯ РЕАЛИЗАЦИЯ: MODE_SELECTION (2 ряда по 50%), PRO_PARAMS (3 ряда БЕЗ пустых)

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
    #("mediterranean", "Средиземноморский"),
    ("midcentury", "Mid‑century / винтаж"),
    ("artdeco", "Арт‑деко"),
    #("hitech", "Хай-тек"),
    #("classic", "Классический"),
    #("contemporary", "Контемпорари"),
    #("eclectic", "Эклектика"),
    #("transitional", "Переходный"),
    ("coastal", "Прибрежный"),
    ("Organic Modern", "Органический Модерн"),
    ("Loft", "Лофт"),
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

# Экран загрузки фото
def get_upload_photo_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для экрана загрузки фото с кнопкой назад"""
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
    #builder.row(InlineKeyboardButton(text="🧽 Очистить пространство", callback_data="clear_space_confirm"))

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
        InlineKeyboardButton(text="🧽 Очистить пространство", callback_data="clear_space_confirm"),
        InlineKeyboardButton(text="⬅️ Выбрать комнату", callback_data="back_to_room"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
    )
    return builder.as_markup()


# Экран после генерации  или очистки помещения
def get_post_generation_keyboard(show_continue_editing: bool = False) -> InlineKeyboardMarkup:
    """
    ОБНОВЛЕНО: 2025-12-08 21:18

    Универсальная клавиатура после генерации.

    Логика:
    - Если show_continue_editing = True → это сценарий РУЧНОГО ПРОМПТА (дом, участок, другое помещение)
      Ряд 1: [✏️ Продолжить редактирование] [📸 Новое фото]
    - Если show_continue_editing = False → это сценарий ПО СТИЛЮ
      Ряд 1: [🔄 Другой стиль] [📸 Новое фото]
    - Ряд 2: [🏠 Главное меню]
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
    Клавиатура подтверждения очистки пространства

    ПРИМЕЧАНИЕ: Функция СОХРАНЕНА для будущего использования.
    Кнопка будет перенесена на другой экран в следующей версии.
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
    
    Структура:
    - Ряд 1: Купить генерации | (пусто)
    - Ряд 2: Настройки режима | Поддержка  
    - Ряд 3: Главное меню
    
    Распределение: adjust(2, 2, 1)
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

    # Ряд 3: Главное меню (широкая кнопка)
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))

    builder.adjust(1, 2, 1)
    return builder.as_markup()


def get_payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tokens, price in PACKAGES.items():
        button_text = f"{tokens} генераций - {price} руб."
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"pay_{tokens}_{price}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))
    # builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

# Экран перейти к оплате
def get_payment_check_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Перейти к оплате", url=url))
    # builder.row(InlineKeyboardButton(text="🔄 Я оплатил! (Проверить)", callback_data="check_payment"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад ", callback_data="show_profile"))
    # builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


# ========================================
# PRO MODE - ФИНАЛЬНЫЕ КЛАВИАТУРЫ
# ОБНОВЛЕНО: 2025-12-24 13:05
# ========================================

def get_mode_selection_keyboard(current_mode_is_pro: bool) -> InlineKeyboardMarkup:
    """
    Клавиатура экрана выбора режима СТАНДАРТ vs PRO.
    
    ФИНАЛЬНАЯ ВЕРСИЯ: 2025-12-24 13:05
    
    Структура:
    - Ряд 1: [СТАНДАРТ 50%] [✅ PRO 50%]  (по 50% каждая в одном ряду)
    - Ряд 2: [⬅️ Назад 50%] [🏠 Главное 50%]  (по 50% каждая в одном ряду)
    
    Распределение: adjust(2, 2)
    
    Args:
        current_mode_is_pro: True если текущий режим PRO, False если СТАНДАРТ
    
    Returns:
        InlineKeyboardMarkup с 4 кнопками (2 ряда по 2)
    """
    builder = InlineKeyboardBuilder()
    
    # Определяем метки активности
    std_mark = "" if current_mode_is_pro else "✅"
    pro_mark = "✅" if current_mode_is_pro else ""
    
    # РЯД 1: РЕЖИМЫ (по 50% ширины каждая в одном ряду)
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
    
    # РЯД 2: НАВИГАЦИЯ (по 50% ширины каждая в одном ряду)
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
    Клавиатура для выбора параметров PRO режима.
    
    ФИНАЛЬНАЯ ВЕРСИЯ: 2025-12-24 13:05
    БЕЗ ПУСТЫХ РЯДОВ!
    
    Структура:
    - РЫД 1: 4 кнопки соотношения (каждая 100%, но в разных рядах)
      * 16:9 (каждая в отдельном ряду)
      * 4:3
      * 1:1
      * 9:16
    - РЫД 2: 3 кнопки разрешения (33% ширины каждая в одном ряду)
      * 1K | 2K | 4K (все в одном ряду)
    - РЫД 3: 2 кнопки навигации (по 50% ширины каждая в одном ряду)
      * ⬅️ Назад | 🏠 Главное
    
    Распределение: 4 отдельных ряда + 1 ряд из 3 + 1 ряд из 2
    
    Args:
        current_ratio: текущее соотношение (по умолчанию "16:9")
        current_resolution: текущее разрешение (по умолчанию "1K")
    
    Returns:
        InlineKeyboardMarkup с кнопками для выбора параметров
    """
    builder = InlineKeyboardBuilder()
    
    # ===== РЫД 1: СООТНОШЕНИЕ СТОРОН (4 кнопки, каждая в отдельном ряду) =====
    for ratio in ASPECT_RATIOS:
        mark = "✅" if ratio == current_ratio else ""
        button_text = f"{mark} {ratio}".strip()
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"aspect_{ratio}"
            )
        )
    
    # ===== РЫД 2: РАЗРЕШЕНИЕ (3 кнопки в одном ряду) =====
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
    builder.row(*resolution_buttons)  # 3 в одном ряду
    
    # ===== РЫД 3: НАВИГАЦИЯ (2 кнопки по 50% ширины в одном ряду) =====
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к режимам", callback_data="profile_settings"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()
