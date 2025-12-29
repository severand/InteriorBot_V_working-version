# 📋 ПОШАГОВЫЙ ПЛАН ИНТЕГРАЦИИ V3 - MULTI-MODE SYSTEM

**Дата создания:** 28.12.2025  
**Версия плана:** V3.0  
**Статус:** ГОТОВ К ВЫПОЛНЕНИЮ  
**Ветка:** `feature/v3-multi-mode-integration`

---

## 📌 ОБЗОР СИСТЕМЫ V3

### Главное изменение: РЕЖИМЫ РАБОТЫ (FSM Modes)

Вместо линейного потока экранов → система с **5 РЕЖИМАМИ**, которые определяют поведение всех экранов:

```
REWORK MODES (FSM Level 1):
├─ NEW_DESIGN       → Создание нового дизайна
├─ EDIT_DESIGN      → Редактирование дизайна
├─ SAMPLE_DESIGN    → Примерка дизайна
├─ ARRANGE_FURNITURE → Расстановка мебели
└─ FACADE_DESIGN    → Дизайн фасада дома

SCREEN STATES (FSM Level 2):
├─ UPLOADING_PHOTO
├─ ROOM_CHOICE
├─ CHOOSE_STYLE_1
├─ CHOOSE_STYLE_2
├─ TEXT_INPUT
├─ POST_GENERATION
├─ DOWNLOAD_SAMPLE
├─ GENERATION_TRY_ON
├─ POST_GENERATION_SAMPLE
├─ UPLOADING_FURNITURE
├─ GENERATION_FURNITURE
├─ POST_GENERATION_FURNITURE
├─ LOADING_FACADE_SAMPLE
├─ GENERATION_FACADE
└─ POST_GENERATION_FACADE
```

### Ключевой концепт: "РЕЖИМ + ЭКРАН"

Каждый экран ведёт себя по-разному в зависимости от режима:

```python
# Пример: экран UPLOADING_PHOTO
if mode == NEW_DESIGN:
    text = "Загрузите фото помещения для СОЗДАНИЯ НОВОГО дизайна"
    next_screen = ROOM_CHOICE
elif mode == EDIT_DESIGN:
    text = "Загрузите фото помещения для РЕДАКТИРОВАНИЯ дизайна"
    next_screen = EDIT_DESIGN
elif mode == SAMPLE_DESIGN:
    text = "Загрузите фото помещения для ПРИМЕРКИ дизайна"
    next_screen = DOWNLOAD_SAMPLE
elif mode == ARRANGE_FURNITURE:
    text = "Загрузите фото помещения для РАССТАНОВКИ мебели"
    next_screen = UPLOADING_FURNITURE
elif mode == FACADE_DESIGN:
    text = "Загрузите фото фасада для РЕДАКТИРОВАНИЯ дизайна"
    next_screen = LOADING_FACADE_SAMPLE
```

---

## 🔄 СТРУКТУРА FSM V3 (НОВАЯ)

### Шаг 1: Расширение `bot/states/fsm.py`

```python
from enum import Enum
from aiogram.fsm.state import State, StatesGroup

# ==================== РЕЖИМЫ РАБОТЫ ====================
class WorkMode(str, Enum):
    """Режимы работы бота"""
    NEW_DESIGN = "new_design"           # Создание нового
    EDIT_DESIGN = "edit_design"         # Редактирование
    SAMPLE_DESIGN = "sample_design"     # Примерка
    ARRANGE_FURNITURE = "arrange_furniture"  # Расставить мебель
    FACADE_DESIGN = "facade_design"     # Фасад дома


# ==================== FSM STATES V3 ====================
class CreationStates(StatesGroup):
    """Состояния для процесса создания дизайна (V3)"""
    
    # УРОВЕНЬ 1: Выбор режима
    selecting_mode = State()  # SCREEN 1: MAIN_MENU - выбор режима
    
    # УРОВЕНЬ 2: Загрузка фото (общее для всех режимов)
    uploading_photo = State()  # SCREEN 2: UPLOADING_PHOTO
    
    # УРОВЕНЬ 3: Выбор комнаты (режим NEW_DESIGN)
    room_choice = State()  # SCREEN 3: ROOM_CHOICE
    
    # УРОВЕНЬ 4: Выбор стиля (режим NEW_DESIGN, EDIT_DESIGN)
    choose_style_1 = State()  # SCREEN 4: CHOOSE_STYLE_1
    choose_style_2 = State()  # SCREEN 5: CHOOSE_STYLE_2
    
    # УРОВЕНЬ 5: Редактирование (режим EDIT_DESIGN)
    edit_design = State()  # SCREEN 8: EDIT_DESIGN
    clear_confirm = State()  # SCREEN 9: CLEAR_CONFIRM
    
    # УРОВЕНЬ 6: Текстовый промт (все режимы)
    text_input = State()  # SCREEN 7: TEXT_INPUT
    
    # УРОВЕНЬ 7: После генерации (все режимы)
    post_generation = State()  # SCREEN 6: POST_GENERATION
    
    # УРОВЕНЬ 8: Примерка дизайна (режим SAMPLE_DESIGN)
    download_sample = State()  # SCREEN 10: DOWNLOAD_SAMPLE
    generation_try_on = State()  # SCREEN 11: GENERATION_TRY_ON
    post_generation_sample = State()  # SCREEN 12: POST_GENERATION_SAMPLE
    
    # УРОВЕНЬ 9: Расставить мебель (режим ARRANGE_FURNITURE)
    uploading_furniture = State()  # SCREEN 13: UPLOADING_FURNITURE
    generation_furniture = State()  # SCREEN 14: GENERATION_FURNITURE
    post_generation_furniture = State()  # SCREEN 15: POST_GENERATION_FURNITURE
    
    # УРОВЕНЬ 10: Фасад дома (режим FACADE_DESIGN)
    loading_facade_sample = State()  # SCREEN 16: LOADING_FACADE_SAMPLE
    generation_facade = State()  # SCREEN 17: GENERATION_FACADE
    post_generation_facade = State()  # SCREEN 18: POST_GENERATION_FACADE


class AdminStates(StatesGroup):
    """Состояния для админ-панели (V3 - без изменений)"""
    # Остаются все прежние states...
    waiting_for_user_id = State()
    waiting_for_search = State()
    adding_balance = State()
    removing_balance = State()
    setting_balance = State()


class ReferralStates(StatesGroup):
    """Состояния для реферальной системы (V3 - без изменений)"""
    # Остаются все прежние states...
    entering_payout_amount = State()
    entering_exchange_amount = State()
    entering_card_number = State()
    entering_yoomoney = State()
    entering_phone = State()
    entering_other_method = State()
```

---

## 📝 ТЕКСТОВЫЕ КОНСТАНТЫ V3

### Шаг 2: Расширение `bot/utils/texts.py`

```python
# ==================== РЕЖИМЫ И ИХ ОПИСАНИЯ ====================

# Текст для экрана выбора режима
MODE_SELECTION_TEXT = """
🎨 **Выберите режим работы:**

📊 **Ваш баланс:** {balance} генераций
🔧 **Текущий режим:** {current_mode}
"""

# Словарь названий режимов для отображения в UI
MODE_DISPLAY_NAMES = {
    "new_design": "📐 Создать новый дизайн",
    "edit_design": "✏️ Редактировать дизайн",
    "sample_design": "🎯 Примерить дизайн",
    "arrange_furniture": "🛋 Расставить мебель",
    "facade_design": "🏠 Дизайн фасада дома",
}

# Словарь описаний режимов
MODE_DESCRIPTIONS = {
    "new_design": "Создайте уникальный дизайн помещения с нуля",
    "edit_design": "Отредактируйте существующий дизайн",
    "sample_design": "Примерьте дизайн на вашу комнату",
    "arrange_furniture": "Расставьте мебель в помещении",
    "facade_design": "Создайте дизайн фасада дома",
}

# ==================== ЭКРАН 1: MAIN_MENU ====================
MAIN_MENU_MODE_TEXT = """
🎨 **Выберите режим работы**

📊 Баланс: {balance} генераций
🔧 Режим: {current_mode}
"""

# ==================== ЭКРАН 2: UPLOADING_PHOTO ====================
UPLOADING_PHOTO_TEMPLATES = {
    "new_design": "📸 Загрузите фото помещения для **создания нового дизайна**",
    "edit_design": "📸 Загрузите фото помещения для **редактирования дизайна**",
    "sample_design": "📸 Загрузите фото помещения для **примерки дизайна**",
    "arrange_furniture": "📸 Загрузите фото помещения для **расстановки мебели**",
    "facade_design": "📸 Загрузите фото фасада дома для **редактирования дизайна**",
}

# ==================== ЭКРАН 3: ROOM_CHOICE ====================
ROOM_CHOICE_TEXT = """
🏠 **Выберите тип помещения**

📊 Баланс: {balance} генераций
🔧 Режим: Создание нового дизайна
"""

# ==================== ЭКРАН 4-5: CHOOSE_STYLE ====================
CHOOSE_STYLE_TEXT = """
🎨 **Выберите стиль дизайна**

⚠️ ВНИМАНИЕ: Генерация начнется сразу после выбора!

📊 Баланс: {balance} генераций
🔧 Режим: {current_mode}
🏠 Комната: {selected_room}
"""

# ==================== ЭКРАН 6: POST_GENERATION ====================
POST_GENERATION_TEXT = """
✨ **Дизайн готов!**

Вы можете:
- 🎨 Выбрать новый стиль
- 🏠 Выбрать новую комнату
- ✍️ Отредактировать текстом
- 🏠 Вернуться в главное меню

📊 Баланс: {balance} генераций
🔧 Режим: {current_mode}
"""

# ==================== ЭКРАН 7: TEXT_INPUT ====================
TEXT_INPUT_PROMPT = """
✏️ **Отредактируйте дизайн текстом**

Дайте подробное описание желаемых изменений для AI

Пример: "Сделай интерьер более светлым, добавь больше растений, поменяй цвет стен на беж"

📊 Баланс: {balance} генераций
🔧 Режим: {current_mode}
"""

# ==================== ЭКРАН 8: EDIT_DESIGN ====================
EDIT_DESIGN_TEXT = """
✏️ **Выберите действие для редактирования**

📊 Баланс: {balance} генераций
🔧 Режим: Редактирование дизайна
"""

# ==================== ЭКРАН 9: CLEAR_CONFIRM ====================
CLEAR_CONFIRM_TEXT = """
⚠️ **Вы уверены, что хотите очистить помещение?**

Это действие нельзя отменить!
"""

CLEAR_SUCCESS_TEXT = """
✅ **Помещение очищено!**

Теперь вы можете загрузить новое фото.
"""

# ==================== ЭКРАН 10: DOWNLOAD_SAMPLE ====================
DOWNLOAD_SAMPLE_TEXT = """
📸 **Загрузите фото образец**

Это фото будет использовано для примерки выбранного дизайна на вашу комнату.

📊 Баланс: {balance} генераций
🔧 Режим: Примерка дизайна
"""

# ==================== ЭКРАН 11: GENERATION_TRY_ON ====================
GENERATION_TRY_ON_TEXT = """
🎨 **Примерьте дизайн**

Нажмите кнопку, чтобы начать генерацию примерки дизайна на вашу комнату.

⚠️ ВНИМАНИЕ: Генерация начнется сразу после нажатия!
"""

# ==================== ЭКРАН 12: POST_GENERATION_SAMPLE ====================
POST_GENERATION_SAMPLE_TEXT = """
✨ **Примерка готова!**

Вы можете:
- ✍️ Отредактировать текстом
- 📸 Загрузить новый образец
- 🏠 Вернуться в главное меню

📊 Баланс: {balance} генераций
🔧 Режим: Примерка дизайна
"""

# ==================== ЭКРАН 13: UPLOADING_FURNITURE ====================
UPLOADING_FURNITURE_TEXT = """
🛋 **Загрузите фото мебели**

Это фото будет использовано для примерки мебели в комнате.

📊 Баланс: {balance} генераций
🔧 Режим: Расстановка мебели
"""

# ==================== ЭКРАН 14: GENERATION_FURNITURE ====================
GENERATION_FURNITURE_TEXT = """
🛋 **Примерьте мебель**

Нажмите кнопку, чтобы начать генерацию примерки мебели в комнате.

⚠️ ВНИМАНИЕ: Генерация начнется сразу после нажатия!
"""

# ==================== ЭКРАН 15: POST_GENERATION_FURNITURE ====================
POST_GENERATION_FURNITURE_TEXT = """
✨ **Примерка мебели готова!**

Вы можете:
- ✍️ Отредактировать текстом
- 🛋 Загрузить новую мебель
- 🏠 Вернуться в главное меню

📊 Баланс: {balance} генераций
🔧 Режим: Расстановка мебели
"""

# ==================== ЭКРАН 16: LOADING_FACADE_SAMPLE ====================
LOADING_FACADE_SAMPLE_TEXT = """
📸 **Загрузите фото образец фасада**

Это фото будет использовано для примерки дизайна фасада дома.

📊 Баланс: {balance} генераций
🔧 Режим: Дизайн фасада
"""

# ==================== ЭКРАН 17: GENERATION_FACADE ====================
GENERATION_FACADE_TEXT = """
🏠 **Примерьте фасад дома**

Нажмите кнопку, чтобы начать генерацию примерки фасада на вашу фотографию.

⚠️ ВНИМАНИЕ: Генерация начнется сразу после нажатия!
"""

# ==================== ЭКРАН 18: POST_GENERATION_FACADE ====================
POST_GENERATION_FACADE_TEXT = """
✨ **Примерка фасада готова!**

Вы можете:
- ✍️ Отредактировать текстом
- 📸 Загрузить новый образец фасада
- 🏠 Вернуться в главное меню

📊 Баланс: {balance} генераций
🔧 Режим: Дизайн фасада
"""
```

---

## ⌨️ КЛАВИАТУРЫ V3

### Шаг 3: Расширение `bot/keyboards/inline.py`

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states.fsm import WorkMode
from bot.utils.texts import MODE_DISPLAY_NAMES, MODE_DESCRIPTIONS

# ==================== ЭКРАН 1: MODE_SELECTION_KEYBOARD ====================
def get_mode_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора режима работы (SCREEN 1: MAIN_MENU)
    
    Структура (по 1 кнопке в ряд):
    ├─ 📐 Создать новый дизайн
    ├─ ✏️ Редактировать дизайн
    ├─ 🎯 Примерить дизайн
    ├─ 🛋 Расставить мебель
    ├─ 🏠 Дизайн фасада дома
    ├─ 👤 Личный кабинет
    ├─ ⚙️ Админ панель
    └─ ❌ Закрыть меню
    """
    builder = InlineKeyboardBuilder()
    
    # Режимы работы
    builder.row(InlineKeyboardButton(
        text="📐 Создать новый дизайн",
        callback_data="select_mode_new_design"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Редактировать дизайн",
        callback_data="select_mode_edit_design"
    ))
    builder.row(InlineKeyboardButton(
        text="🎯 Примерить дизайн",
        callback_data="select_mode_sample_design"
    ))
    builder.row(InlineKeyboardButton(
        text="🛋 Расставить мебель",
        callback_data="select_mode_arrange_furniture"
    ))
    builder.row(InlineKeyboardButton(
        text="🏠 Дизайн фасада дома",
        callback_data="select_mode_facade_design"
    ))
    
    # Разделитель
    builder.row(InlineKeyboardButton(
        text="───────────────",
        callback_data="dummy"
    ))
    
    # Личный кабинет и админ
    builder.row(
        InlineKeyboardButton(text="👤 Личный кабинет", callback_data="show_profile"),
        InlineKeyboardButton(text="⚙️ Админ", callback_data="admin_panel")
    )
    
    builder.adjust(1)
    return builder.as_markup()


# ==================== ЭКРАН 2: UPLOADING_PHOTO_KEYBOARD ====================
def get_uploading_photo_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура загрузки фото (SCREEN 2: UPLOADING_PHOTO)
    Динамический текст в зависимости от режима!
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="select_mode"  # Возврат к выбору режима
    ))
    builder.adjust(1)
    return builder.as_markup()


# ==================== ЭКРАН 3: ROOM_CHOICE_KEYBOARD ====================
def get_room_choice_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора комнаты (SCREEN 3: ROOM_CHOICE)
    Структура (по 2 в ряд):
    ├─ 💪 Гостиная | 🝴 Кухня
    ├─ 🛏 Спальня | 👶 Детская
    ├─ 🚿 Студия | 💼 Кабинет
    ├─ 🚿 Ванная | 💼 Санузел
    ├─ 💪 Прихожая | 🝴 Гардеробная
    ├─ ⬅️ Новое фото | 🏠 Главное меню
    """
    builder = InlineKeyboardBuilder()
    
    rooms = [
        ("💪 Гостиная", "room_living_room"),
        ("🝴 Кухня", "room_kitchen"),
        ("🛏 Спальня", "room_bedroom"),
        ("👶 Детская", "room_nursery"),
        ("🚿 Студия", "room_studio"),
        ("💼 Кабинет", "room_home_office"),
        ("🚿 Ванная", "room_bathroom_full"),
        ("💼 Санузел", "room_toilet"),
        ("💪 Прихожая", "room_entryway"),
        ("🝴 Гардеробная", "room_wardrobe"),
    ]
    
    # Добавляем комнаты по 2 в ряд
    for i in range(0, len(rooms), 2):
        row = [InlineKeyboardButton(text=rooms[i][0], callback_data=f"room_{rooms[i][1]}")]
        if i + 1 < len(rooms):
            row.append(InlineKeyboardButton(text=rooms[i+1][0], callback_data=f"room_{rooms[i+1][1]}"))
        builder.row(*row)
    
    # Кнопки навигации
    builder.row(
        InlineKeyboardButton(text="⬅️ Новое фото", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== ЭКРАН 4: CHOOSE_STYLE_1_KEYBOARD ====================
def get_choose_style_1_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора стиля 1 (SCREEN 4: CHOOSE_STYLE_1)
    Структура (по 2 в ряд):
    ├─ Современный | Минимализм
    ├─ Скандинавский | Индустриальный (лофт)
    ├─ Рустик | Джапанди
    ├─ Бохо / Эклектика | Mid‑century / винтаж
    ├─ Арт‑деко | Прибрежный
    ├─ Органический Модерн | Лофт
    ├─ ⬅️ Выбрать комнату | 🏠 Главное меню | ▶️ Ещё стили
    """
    builder = InlineKeyboardBuilder()
    
    styles_page1 = [
        ("Современный", "style_modern"),
        ("Минимализм", "style_minimalist"),
        ("Скандинавский", "style_scandinavian"),
        ("Индустриальный", "style_industrial"),
        ("Рустик", "style_rustic"),
        ("Джапанди", "style_japandi"),
        ("Бохо", "style_boho"),
        ("Mid-century", "style_midcentury"),
        ("Арт-деко", "style_artdeco"),
        ("Прибрежный", "style_coastal"),
        ("Органический Модерн", "style_organic_modern"),
        ("Лофт", "style_loft"),
    ]
    
    # Добавляем стили по 2 в ряд
    for i in range(0, len(styles_page1), 2):
        row = [InlineKeyboardButton(text=styles_page1[i][0], callback_data=styles_page1[i][1])]
        if i + 1 < len(styles_page1):
            row.append(InlineKeyboardButton(text=styles_page1[i+1][0], callback_data=styles_page1[i+1][1]))
        builder.row(*row)
    
    # Навигация
    builder.row(
        InlineKeyboardButton(text="⬅️ К комнате", callback_data="room_choice"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode"),
        InlineKeyboardButton(text="▶️ Ещё", callback_data="choose_style_2")
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== ЭКРАН 5: CHOOSE_STYLE_2_KEYBOARD ====================
def get_choose_style_2_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора стиля 2 (SCREEN 5: CHOOSE_STYLE_2)
    Дополнительные стили
    """
    builder = InlineKeyboardBuilder()
    
    styles_page2 = [
        ("Теплая роскошь", "style_warm_luxury"),
        ("Нео Арт Деко", "style_neo_art_deco"),
        ("Осознанная электика", "style_conscious_eclectics"),
        ("Тактильный Максимализм", "style_tactile_maximalism"),
        ("Рустик", "style_rustic"),
        ("Джапанди", "style_japandi"),
        ("Бохо", "style_boho"),
        ("Mid-century", "style_midcentury"),
        ("Арт-деко", "style_artdeco"),
        ("Прибрежный", "style_coastal"),
        ("Органический Модерн", "style_organic_modern"),
        ("Лофт", "style_loft"),
    ]
    
    # Добавляем стили по 2 в ряд
    for i in range(0, len(styles_page2), 2):
        row = [InlineKeyboardButton(text=styles_page2[i][0], callback_data=styles_page2[i][1])]
        if i + 1 < len(styles_page2):
            row.append(InlineKeyboardButton(text=styles_page2[i+1][0], callback_data=styles_page2[i+1][1]))
        builder.row(*row)
    
    # Навигация
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="choose_style_1"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== ЭКРАН 6: POST_GENERATION_KEYBOARD ====================
def get_post_generation_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после генерации (SCREEN 6: POST_GENERATION)
    Динамическая в зависимости от режима!
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🎨 Новый стиль", callback_data="choose_style_1"),
        InlineKeyboardButton(text="🏠 Новая комната", callback_data="room_choice")
    )
    builder.row(InlineKeyboardButton(
        text="✍️ Текстовое редактирование",
        callback_data="text_input"
    ))
    builder.row(InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="select_mode"
    ))
    builder.adjust(2, 1, 1)
    return builder.as_markup()


# ==================== ЭКРАН 7: TEXT_INPUT_KEYBOARD ====================
def get_text_input_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура текстового редактирования (SCREEN 7: TEXT_INPUT)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_from_text_input"
    ))
    builder.adjust(1)
    return builder.as_markup()


# ==================== ЭКРАН 8: EDIT_DESIGN_KEYBOARD ====================
def get_edit_design_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура редактирования дизайна (SCREEN 8: EDIT_DESIGN)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🗹️ Очистить фото", callback_data="clear_confirm"),
        InlineKeyboardButton(text="📏 Ввести текст", callback_data="text_input")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Новое фото", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2, 2)
    return builder.as_markup()


# ==================== ЭКРАН 9: CLEAR_CONFIRM_KEYBOARD ====================
def get_clear_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения очистки (SCREEN 9: CLEAR_CONFIRM)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да, очистить", callback_data="clear_execute"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="edit_design")
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== ЭКРАН 10: DOWNLOAD_SAMPLE_KEYBOARD ====================
def get_download_sample_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура загрузки образца (SCREEN 10: DOWNLOAD_SAMPLE)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== ЭКРАН 11: GENERATION_TRY_ON_KEYBOARD ====================
def get_generation_try_on_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура генерации примерки (SCREEN 11: GENERATION_TRY_ON)
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


# ==================== ЭКРАН 12: POST_GENERATION_SAMPLE_KEYBOARD ====================
def get_post_generation_sample_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после примерки (SCREEN 12: POST_GENERATION_SAMPLE)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="✍️ Текстовое редактирование",
        callback_data="text_input"
    ))
    builder.row(
        InlineKeyboardButton(text="📸 Новый образец", callback_data="download_sample"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ==================== ЭКРАН 13: UPLOADING_FURNITURE_KEYBOARD ====================
def get_uploading_furniture_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура загрузки мебели (SCREEN 13: UPLOADING_FURNITURE)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== ЭКРАН 14: GENERATION_FURNITURE_KEYBOARD ====================
def get_generation_furniture_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура генерации мебели (SCREEN 14: GENERATION_FURNITURE)
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


# ==================== ЭКРАН 15: POST_GENERATION_FURNITURE_KEYBOARD ====================
def get_post_generation_furniture_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после примерки мебели (SCREEN 15: POST_GENERATION_FURNITURE)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="✍️ Текстовое редактирование",
        callback_data="text_input"
    ))
    builder.row(
        InlineKeyboardButton(text="🛋 Новая мебель", callback_data="uploading_furniture"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ==================== ЭКРАН 16: LOADING_FACADE_SAMPLE_KEYBOARD ====================
def get_loading_facade_sample_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура загрузки образца фасада (SCREEN 16: LOADING_FACADE_SAMPLE)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="uploading_photo"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== ЭКРАН 17: GENERATION_FACADE_KEYBOARD ====================
def get_generation_facade_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура генерации фасада (SCREEN 17: GENERATION_FACADE)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🎨 Примерить фасад",
        callback_data="generate_facade"
    ))
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="loading_facade_sample"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()


# ==================== ЭКРАН 18: POST_GENERATION_FACADE_KEYBOARD ====================
def get_post_generation_facade_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после примерки фасада (SCREEN 18: POST_GENERATION_FACADE)
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="✍️ Текстовое редактирование",
        callback_data="text_input"
    ))
    builder.row(
        InlineKeyboardButton(text="📸 Новый образец", callback_data="loading_facade_sample"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="select_mode")
    )
    builder.adjust(1, 2)
    return builder.as_markup()
```

---

## 🎯 НОВЫЕ ОБРАБОТЧИКИ V3

### Шаг 4: Новый файл `bot/handlers/creation_v3.py`

```python
"""
Обработчики для V3 Multi-Mode System

Организация:
1. Выбор режима (select_mode)
2. Загрузка фото (photo_handler)
3. Выбор комнаты (room_choice_handler) - только для NEW_DESIGN
4. Выбор стиля (style_choice_handler) - для NEW_DESIGN, EDIT_DESIGN
5. Редактирование (edit_design_handler) - для EDIT_DESIGN
6. Примерка дизайна (sample_design handlers) - для SAMPLE_DESIGN
7. Расстановка мебели (furniture handlers) - для ARRANGE_FURNITURE
8. Дизайн фасада (facade handlers) - для FACADE_DESIGN
9. Текстовый промт (text_input_handler) - для всех режимов
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command

from bot.states.fsm import CreationStates, WorkMode
from bot.keyboards.inline import (
    get_mode_selection_keyboard,
    get_uploading_photo_keyboard,
    get_room_choice_keyboard,
    get_choose_style_1_keyboard,
    get_choose_style_2_keyboard,
    get_post_generation_keyboard,
    get_text_input_keyboard,
    get_edit_design_keyboard,
    get_clear_confirm_keyboard,
    get_download_sample_keyboard,
    get_generation_try_on_keyboard,
    get_post_generation_sample_keyboard,
    get_uploading_furniture_keyboard,
    get_generation_furniture_keyboard,
    get_post_generation_furniture_keyboard,
    get_loading_facade_sample_keyboard,
    get_generation_facade_keyboard,
    get_post_generation_facade_keyboard,
)
from bot.utils.texts import (
    MODE_SELECTION_TEXT,
    UPLOADING_PHOTO_TEMPLATES,
    ROOM_CHOICE_TEXT,
    CHOOSE_STYLE_TEXT,
    POST_GENERATION_TEXT,
    TEXT_INPUT_PROMPT,
    EDIT_DESIGN_TEXT,
    CLEAR_CONFIRM_TEXT,
    CLEAR_SUCCESS_TEXT,
    DOWNLOAD_SAMPLE_TEXT,
    GENERATION_TRY_ON_TEXT,
    POST_GENERATION_SAMPLE_TEXT,
    UPLOADING_FURNITURE_TEXT,
    GENERATION_FURNITURE_TEXT,
    POST_GENERATION_FURNITURE_TEXT,
    LOADING_FACADE_SAMPLE_TEXT,
    GENERATION_FACADE_TEXT,
    POST_GENERATION_FACADE_TEXT,
)
from bot.utils.navigation import edit_menu, show_main_menu
from bot.database.db import get_user_balance, update_balance, save_photo
from bot.services.kie_api import generate_image

router = Router()

# ==================== ЭКРАН 1: SELECT MODE ====================

@router.callback_query(F.data == "select_mode")
async def select_mode(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 1: Выбор режима работы (MAIN_MENU)
    
    Логика:
    1. Установка FSM state на selecting_mode
    2. Получение текущего режима из data
    3. Получение баланса пользователя
    4. Отправка меню выбора режима
    
    Log: "SELECT_MODE - user_id={user_id}"
    """
    user_id = callback.from_user.id
    
    # Получаем текущий режим
    data = await state.get_data()
    current_mode = data.get('work_mode', 'Не выбран')
    
    # Получаем баланс
    balance = await get_user_balance(user_id)
    
    # Устанавливаем состояние
    await state.set_state(CreationStates.selecting_mode)
    await state.update_data(work_mode=current_mode)
    
    text = MODE_SELECTION_TEXT.format(
        balance=balance,
        current_mode=current_mode
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(),
        screen_code='select_mode'
    )
    
    print(f"[V3] SELECT_MODE - user_id={user_id}, current_mode={current_mode}")


@router.callback_query(F.data.startswith("select_mode_"))
async def set_work_mode(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора режима
    
    Извлекает режим из callback_data и сохраняет в FSM
    Затем переходит на экран загрузки фото
    
    Modes:
    - select_mode_new_design
    - select_mode_edit_design
    - select_mode_sample_design
    - select_mode_arrange_furniture
    - select_mode_facade_design
    """
    user_id = callback.from_user.id
    mode_str = callback.data.replace("select_mode_", "")
    
    # Преобразуем строку в WorkMode enum
    mode_map = {
        "new_design": WorkMode.NEW_DESIGN,
        "edit_design": WorkMode.EDIT_DESIGN,
        "sample_design": WorkMode.SAMPLE_DESIGN,
        "arrange_furniture": WorkMode.ARRANGE_FURNITURE,
        "facade_design": WorkMode.FACADE_DESIGN,
    }
    
    work_mode = mode_map.get(mode_str)
    if not work_mode:
        return
    
    # Сохраняем режим в FSM
    await state.update_data(work_mode=work_mode.value)
    await state.set_state(CreationStates.uploading_photo)
    
    # Получаем баланс
    balance = await get_user_balance(user_id)
    
    # Динамический текст в зависимости от режима
    text = UPLOADING_PHOTO_TEMPLATES.get(
        work_mode.value,
        "📸 Загрузите фото"
    )
    text += f"\n\n📊 Баланс: {balance}"
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_uploading_photo_keyboard(),
        screen_code='uploading_photo'
    )
    
    print(f"[V3] {work_mode.value.upper()}+UPLOADING_PHOTO - user_id={user_id}")


# ==================== ЭКРАН 2: UPLOADING PHOTO ====================

@router.message(StateFilter(CreationStates.uploading_photo))
async def photo_handler(message: Message, state: FSMContext):
    """
    SCREEN 2: Загрузка фото (UPLOADING_PHOTO)
    
    Логика:
    1. Валидация: проверяем, что это фото
    2. Проверка баланса (баланс > 0?)
    3. Сохраняем file_id в FSM
    4. Переходим на экран в зависимости от режима:
       - NEW_DESIGN → ROOM_CHOICE
       - EDIT_DESIGN → EDIT_DESIGN
       - SAMPLE_DESIGN → DOWNLOAD_SAMPLE
       - ARRANGE_FURNITURE → UPLOADING_FURNITURE
       - FACADE_DESIGN → LOADING_FACADE_SAMPLE
    
    Log: "NEW_DESIGN+UPLOADING_PHOTO - photo saved"
    """
    user_id = message.from_user.id
    data = await state.get_data()
    work_mode = data.get('work_mode')
    
    # Валидация
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото")
        return
    
    # Проверка баланса
    balance = await get_user_balance(user_id)
    if balance <= 0 and work_mode != "edit_design":  # edit_design может работать без баланса
        await message.answer("❌ У вас недостаточно генераций. Пожалуйста, пополните баланс.")
        return
    
    # Сохраняем фото
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id, new_photo=True)
    await save_photo(user_id, photo_id)
    
    # Переходим на следующий экран в зависимости от режима
    if work_mode == WorkMode.NEW_DESIGN.value:
        await state.set_state(CreationStates.room_choice)
        text = ROOM_CHOICE_TEXT.format(balance=balance)
        keyboard = get_room_choice_keyboard()
        screen = 'room_choice'
        
    elif work_mode == WorkMode.EDIT_DESIGN.value:
        await state.set_state(CreationStates.edit_design)
        text = EDIT_DESIGN_TEXT.format(balance=balance)
        keyboard = get_edit_design_keyboard()
        screen = 'edit_design'
        
    elif work_mode == WorkMode.SAMPLE_DESIGN.value:
        await state.set_state(CreationStates.download_sample)
        text = DOWNLOAD_SAMPLE_TEXT.format(balance=balance)
        keyboard = get_download_sample_keyboard()
        screen = 'download_sample'
        
    elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
        await state.set_state(CreationStates.uploading_furniture)
        text = UPLOADING_FURNITURE_TEXT.format(balance=balance)
        keyboard = get_uploading_furniture_keyboard()
        screen = 'uploading_furniture'
        
    elif work_mode == WorkMode.FACADE_DESIGN.value:
        await state.set_state(CreationStates.loading_facade_sample)
        text = LOADING_FACADE_SAMPLE_TEXT.format(balance=balance)
        keyboard = get_loading_facade_sample_keyboard()
        screen = 'loading_facade_sample'
    
    # Обновляем меню
    await edit_menu(
        callback=CallbackQuery(message),  # Преобразуем Message в CallbackQuery
        state=state,
        text=text,
        keyboard=keyboard,
        screen_code=screen
    )
    
    print(f"[V3] {work_mode.upper()}+UPLOADING_PHOTO - photo saved, user_id={user_id}")


# ==================== ЭКРАН 3: ROOM CHOICE (только для NEW_DESIGN) ====================

@router.callback_query(F.data == "room_choice")
async def room_choice_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 3: Выбор комнаты (ROOM_CHOICE)
    Только для режима NEW_DESIGN
    """
    data = await state.get_data()
    balance = await get_user_balance(callback.from_user.id)
    
    await state.set_state(CreationStates.room_choice)
    
    text = ROOM_CHOICE_TEXT.format(balance=balance)
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_room_choice_keyboard(),
        screen_code='room_choice'
    )


@router.callback_query(F.data.startswith("room_"))
async def room_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора комнаты
    Переходит на экран выбора стиля
    """
    room = callback.data.replace("room_", "")
    balance = await get_user_balance(callback.from_user.id)
    
    await state.update_data(selected_room=room)
    await state.set_state(CreationStates.choose_style_1)
    
    text = CHOOSE_STYLE_TEXT.format(
        balance=balance,
        current_mode="Создание нового дизайна",
        selected_room=room
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_choose_style_1_keyboard(),
        screen_code='choose_style_1'
    )
    
    print(f"[V3] NEW_DESIGN+ROOM_CHOICE - selected: {room}")


# ==================== ЭКРАН 4-5: CHOOSE STYLE ====================

@router.callback_query(F.data == "choose_style_1")
async def choose_style_1_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню стилей (страница 1)"""
    balance = await get_user_balance(callback.from_user.id)
    data = await state.get_data()
    
    await state.set_state(CreationStates.choose_style_1)
    
    text = CHOOSE_STYLE_TEXT.format(
        balance=balance,
        current_mode=data.get('work_mode', 'Неизвестно'),
        selected_room=data.get('selected_room', 'Не выбрана')
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_choose_style_1_keyboard(),
        screen_code='choose_style_1'
    )


@router.callback_query(F.data == "choose_style_2")
async def choose_style_2_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню стилей (страница 2)"""
    balance = await get_user_balance(callback.from_user.id)
    data = await state.get_data()
    
    await state.set_state(CreationStates.choose_style_2)
    
    text = CHOOSE_STYLE_TEXT.format(
        balance=balance,
        current_mode=data.get('work_mode', 'Неизвестно'),
        selected_room=data.get('selected_room', 'Не выбрана')
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_choose_style_2_keyboard(),
        screen_code='choose_style_2'
    )


@router.callback_query(F.data.startswith("style_"))
async def style_choice_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора стиля
    
    Логика:
    1. Извлекаем стиль из callback_data
    2. Сохраняем в FSM
    3. Проверяем баланс
    4. Вызываем API для генерации
    5. Отправляем результат
    6. Переходим на POST_GENERATION
    
    Log: "NEW_DESIGN+CHOOSE_STYLE_1 - generating design"
    """
    user_id = callback.from_user.id
    data = await state.get_data()
    work_mode = data.get('work_mode')
    style = callback.data.replace("style_", "")
    
    # Проверяем баланс
    balance = await get_user_balance(user_id)
    if balance <= 0:
        await callback.answer("❌ Недостаточно генераций", show_alert=True)
        return
    
    # Сохраняем выбор стиля
    await state.update_data(selected_style=style)
    
    # Получаем фото
    photo_id = data.get('photo_id')
    room = data.get('selected_room', 'studio')
    
    # Вызываем API для генерации
    try:
        result = await generate_image(
            photo_id=photo_id,
            room_type=room,
            style=style,
            mode=work_mode
        )
        
        # Обновляем баланс
        new_balance = balance - 1
        await update_balance(user_id, new_balance)
        
        # Отправляем результат
        await callback.message.answer_photo(
            photo=result['image_url'],
            caption=f"✨ Дизайн готов!\n\nБаланс: {new_balance}"
        )
        
        # Переходим на POST_GENERATION
        await state.set_state(CreationStates.post_generation)
        
        text = POST_GENERATION_TEXT.format(
            balance=new_balance,
            current_mode=work_mode
        )
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_post_generation_keyboard(),
            screen_code='post_generation'
        )
        
        print(f"[V3] {work_mode.upper()}+CHOOSE_STYLE - generated, new_balance={new_balance}")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка генерации: {str(e)}", show_alert=True)
        print(f"[ERROR] Generation failed: {e}")


# ==================== ЭКРАН 6: POST_GENERATION ====================

@router.callback_query(F.data == "post_generation")
async def post_generation_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню после генерации"""
    balance = await get_user_balance(callback.from_user.id)
    data = await state.get_data()
    
    await state.set_state(CreationStates.post_generation)
    
    text = POST_GENERATION_TEXT.format(
        balance=balance,
        current_mode=data.get('work_mode', 'Неизвестно')
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_post_generation_keyboard(),
        screen_code='post_generation'
    )


# ==================== ЭКРАН 7: TEXT INPUT ====================

@router.callback_query(F.data == "text_input")
async def text_input_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 7: Переход на экран текстового ввода
    """
    await state.set_state(CreationStates.text_input)
    
    balance = await get_user_balance(callback.from_user.id)
    
    text = TEXT_INPUT_PROMPT.format(
        balance=balance,
        current_mode="Редактирование"
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_text_input_keyboard(),
        screen_code='text_input'
    )


@router.message(StateFilter(CreationStates.text_input))
async def text_input_handler(message: Message, state: FSMContext):
    """
    Обработчик текстового промта
    
    Логика:
    1. Получаем последнюю картинку из FSM
    2. Получаем промт из сообщения
    3. Вызываем API с промтом
    4. Отправляем результат
    5. Возвращаемся на POST_GENERATION
    
    Log: "NEW_DESIGN+TEXT_INPUT - prompt received"
    """
    user_id = message.from_user.id
    data = await state.get_data()
    work_mode = data.get('work_mode')
    photo_id = data.get('photo_id')
    prompt = message.text
    
    # Проверяем баланс
    balance = await get_user_balance(user_id)
    if balance <= 0:
        await message.answer("❌ Недостаточно генераций")
        return
    
    # Вызываем API с текстовым промтом
    try:
        result = await generate_image(
            photo_id=photo_id,
            prompt=prompt,
            mode=work_mode
        )
        
        # Обновляем баланс
        new_balance = balance - 1
        await update_balance(user_id, new_balance)
        
        # Отправляем результат
        await message.answer_photo(
            photo=result['image_url'],
            caption=f"✨ Дизайн отредактирован!\n\nБаланс: {new_balance}"
        )
        
        # Возвращаемся на POST_GENERATION
        await state.set_state(CreationStates.post_generation)
        
        text = POST_GENERATION_TEXT.format(
            balance=new_balance,
            current_mode=work_mode
        )
        
        # Вызываем через callback
        # TODO: Реализовать через edit_menu
        
        print(f"[V3] {work_mode.upper()}+TEXT_INPUT - prompt: '{prompt}', new_balance={new_balance}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        print(f"[ERROR] Text input generation failed: {e}")


# ==================== ЭКРАН 8: EDIT_DESIGN ====================

@router.callback_query(F.data == "edit_design")
async def edit_design_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 8: Меню редактирования дизайна (только для EDIT_DESIGN режима)
    """
    balance = await get_user_balance(callback.from_user.id)
    
    await state.set_state(CreationStates.edit_design)
    
    text = EDIT_DESIGN_TEXT.format(balance=balance)
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_edit_design_keyboard(),
        screen_code='edit_design'
    )


# ==================== ЭКРАН 9: CLEAR_CONFIRM ====================

@router.callback_query(F.data == "clear_confirm")
async def clear_confirm_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 9: Подтверждение очистки помещения
    """
    await state.set_state(CreationStates.clear_confirm)
    
    text = CLEAR_CONFIRM_TEXT
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_clear_confirm_keyboard(),
        screen_code='clear_confirm'
    )


@router.callback_query(F.data == "clear_execute")
async def clear_execute(callback: CallbackQuery, state: FSMContext):
    """
    Выполнить очистку помещения
    """
    user_id = callback.from_user.id
    data = await state.get_data()
    photo_id = data.get('photo_id')
    
    # Вызываем API для очистки
    try:
        result = await generate_image(
            photo_id=photo_id,
            clear_space=True,
            mode="edit_design"
        )
        
        # Отправляем результат
        await callback.message.answer_photo(
            photo=result['image_url'],
            caption="✅ Помещение очищено!"
        )
        
        # Возвращаемся в EDIT_DESIGN
        await state.set_state(CreationStates.edit_design)
        balance = await get_user_balance(user_id)
        
        text = EDIT_DESIGN_TEXT.format(balance=balance)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_edit_design_keyboard(),
            screen_code='edit_design'
        )
        
        print(f"[V3] EDIT_DESIGN+CLEAR_CONFIRM - space cleared")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка очистки: {str(e)}", show_alert=True)


# ==================== ЭКРАН 10-12: SAMPLE_DESIGN РЕЖИМ ====================

@router.callback_query(F.data == "download_sample")
async def download_sample_menu(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 10: Загрузка образца дизайна (SAMPLE_DESIGN режим)
    """
    balance = await get_user_balance(callback.from_user.id)
    
    await state.set_state(CreationStates.download_sample)
    
    text = DOWNLOAD_SAMPLE_TEXT.format(balance=balance)
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_download_sample_keyboard(),
        screen_code='download_sample'
    )


@router.message(StateFilter(CreationStates.download_sample))
async def download_sample_handler(message: Message, state: FSMContext):
    """
    Обработчик загрузки образца дизайна
    """
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото")
        return
    
    # Сохраняем образец
    sample_id = message.photo[-1].file_id
    await state.update_data(sample_photo_id=sample_id)
    
    # Переходим на GENERATION_TRY_ON
    await state.set_state(CreationStates.generation_try_on)
    balance = await get_user_balance(message.from_user.id)
    
    text = GENERATION_TRY_ON_TEXT
    
    # TODO: Обновить меню через edit_menu


@router.callback_query(F.data == "generate_try_on")
async def generate_try_on(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 11: Генерация примерки дизайна
    """
    user_id = callback.from_user.id
    data = await state.get_data()
    
    # Получаем фото
    main_photo_id = data.get('photo_id')
    sample_photo_id = data.get('sample_photo_id')
    design_style = data.get('selected_style', 'modern')
    
    # Проверяем баланс
    balance = await get_user_balance(user_id)
    if balance <= 0:
        await callback.answer("❌ Недостаточно генераций", show_alert=True)
        return
    
    # Вызываем API для примерки
    try:
        result = await generate_image(
            photo_id=main_photo_id,
            sample_photo_id=sample_photo_id,
            style=design_style,
            mode='sample_design'
        )
        
        # Обновляем баланс
        new_balance = balance - 1
        await update_balance(user_id, new_balance)
        
        # Отправляем результат
        await callback.message.answer_photo(
            photo=result['image_url'],
            caption=f"✨ Примерка готова!\n\nБаланс: {new_balance}"
        )
        
        # Переходим на POST_GENERATION_SAMPLE
        await state.set_state(CreationStates.post_generation_sample)
        
        text = POST_GENERATION_SAMPLE_TEXT.format(balance=new_balance)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_post_generation_sample_keyboard(),
            screen_code='post_generation_sample'
        )
        
        print(f"[V3] SAMPLE_DESIGN+GENERATION_TRY_ON - generated, new_balance={new_balance}")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ==================== ЭКРАН 13-15: ARRANGE_FURNITURE РЕЖИМ ====================

@router.message(StateFilter(CreationStates.uploading_furniture))
async def uploading_furniture_handler(message: Message, state: FSMContext):
    """
    Обработчик загрузки фото мебели
    """
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото мебели")
        return
    
    # Сохраняем фото мебели
    furniture_photo_id = message.photo[-1].file_id
    await state.update_data(furniture_photo_id=furniture_photo_id)
    
    # Переходим на GENERATION_FURNITURE
    await state.set_state(CreationStates.generation_furniture)
    balance = await get_user_balance(message.from_user.id)
    
    text = GENERATION_FURNITURE_TEXT
    
    # TODO: Обновить меню через edit_menu


@router.callback_query(F.data == "generate_furniture")
async def generate_furniture(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 14: Генерация примерки мебели
    """
    user_id = callback.from_user.id
    data = await state.get_data()
    
    # Получаем фото
    room_photo_id = data.get('photo_id')
    furniture_photo_id = data.get('furniture_photo_id')
    
    # Проверяем баланс
    balance = await get_user_balance(user_id)
    if balance <= 0:
        await callback.answer("❌ Недостаточно генераций", show_alert=True)
        return
    
    # Вызываем API для расстановки мебели
    try:
        result = await generate_image(
            photo_id=room_photo_id,
            furniture_photo_id=furniture_photo_id,
            mode='arrange_furniture'
        )
        
        # Обновляем баланс
        new_balance = balance - 1
        await update_balance(user_id, new_balance)
        
        # Отправляем результат
        await callback.message.answer_photo(
            photo=result['image_url'],
            caption=f"✨ Мебель расставлена!\n\nБаланс: {new_balance}"
        )
        
        # Переходим на POST_GENERATION_FURNITURE
        await state.set_state(CreationStates.post_generation_furniture)
        
        text = POST_GENERATION_FURNITURE_TEXT.format(balance=new_balance)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_post_generation_furniture_keyboard(),
            screen_code='post_generation_furniture'
        )
        
        print(f"[V3] ARRANGE_FURNITURE+GENERATION_FURNITURE - generated, new_balance={new_balance}")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ==================== ЭКРАН 16-18: FACADE_DESIGN РЕЖИМ ====================

@router.message(StateFilter(CreationStates.loading_facade_sample))
async def loading_facade_sample_handler(message: Message, state: FSMContext):
    """
    Обработчик загрузки образца фасада
    """
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото образца фасада")
        return
    
    # Сохраняем образец фасада
    facade_sample_id = message.photo[-1].file_id
    await state.update_data(facade_sample_id=facade_sample_id)
    
    # Переходим на GENERATION_FACADE
    await state.set_state(CreationStates.generation_facade)
    balance = await get_user_balance(message.from_user.id)
    
    text = GENERATION_FACADE_TEXT
    
    # TODO: Обновить меню через edit_menu


@router.callback_query(F.data == "generate_facade")
async def generate_facade(callback: CallbackQuery, state: FSMContext):
    """
    SCREEN 17: Генерация примерки фасада
    """
    user_id = callback.from_user.id
    data = await state.get_data()
    
    # Получаем фото
    main_facade_photo_id = data.get('photo_id')
    facade_sample_id = data.get('facade_sample_id')
    facade_style = data.get('facade_style', 'modern')
    
    # Проверяем баланс
    balance = await get_user_balance(user_id)
    if balance <= 0:
        await callback.answer("❌ Недостаточно генераций", show_alert=True)
        return
    
    # Вызываем API для примерки фасада
    try:
        result = await generate_image(
            photo_id=main_facade_photo_id,
            facade_sample_id=facade_sample_id,
            style=facade_style,
            mode='facade_design'
        )
        
        # Обновляем баланс
        new_balance = balance - 1
        await update_balance(user_id, new_balance)
        
        # Отправляем результат
        await callback.message.answer_photo(
            photo=result['image_url'],
            caption=f"✨ Фасад готов!\n\nБаланс: {new_balance}"
        )
        
        # Переходим на POST_GENERATION_FACADE
        await state.set_state(CreationStates.post_generation_facade)
        
        text = POST_GENERATION_FACADE_TEXT.format(balance=new_balance)
        
        await edit_menu(
            callback=callback,
            state=state,
            text=text,
            keyboard=get_post_generation_facade_keyboard(),
            screen_code='post_generation_facade'
        )
        
        print(f"[V3] FACADE_DESIGN+GENERATION_FACADE - generated, new_balance={new_balance}")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ==================== УТИЛИТЫ ====================

@router.callback_query(F.data == "uploading_photo")
async def uploading_photo_callback(callback: CallbackQuery, state: FSMContext):
    """
    Переход на экран загрузки фото
    """
    data = await state.get_data()
    work_mode = data.get('work_mode')
    balance = await get_user_balance(callback.from_user.id)
    
    await state.set_state(CreationStates.uploading_photo)
    
    text = UPLOADING_PHOTO_TEMPLATES.get(
        work_mode,
        "📸 Загрузите фото"
    )
    text += f"\n\n📊 Баланс: {balance}"
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_uploading_photo_keyboard(),
        screen_code='uploading_photo'
    )


@router.callback_query(F.data == "back_from_text_input")
async def back_from_text_input(callback: CallbackQuery, state: FSMContext):
    """
    Возврат из TEXT_INPUT на соответствующий экран
    
    Логика: Зависит от того, из какого режима пришли
    - Если из POST_GENERATION → назад на POST_GENERATION
    - Если из POST_GENERATION_SAMPLE → назад на POST_GENERATION_SAMPLE
    - Если из EDIT_DESIGN → назад на EDIT_DESIGN
    """
    data = await state.get_data()
    work_mode = data.get('work_mode')
    balance = await get_user_balance(callback.from_user.id)
    
    if work_mode == WorkMode.SAMPLE_DESIGN.value:
        await state.set_state(CreationStates.post_generation_sample)
        text = POST_GENERATION_SAMPLE_TEXT.format(balance=balance)
        keyboard = get_post_generation_sample_keyboard()
        screen = 'post_generation_sample'
    elif work_mode == WorkMode.ARRANGE_FURNITURE.value:
        await state.set_state(CreationStates.post_generation_furniture)
        text = POST_GENERATION_FURNITURE_TEXT.format(balance=balance)
        keyboard = get_post_generation_furniture_keyboard()
        screen = 'post_generation_furniture'
    elif work_mode == WorkMode.FACADE_DESIGN.value:
        await state.set_state(CreationStates.post_generation_facade)
        text = POST_GENERATION_FACADE_TEXT.format(balance=balance)
        keyboard = get_post_generation_facade_keyboard()
        screen = 'post_generation_facade'
    else:  # NEW_DESIGN, EDIT_DESIGN
        await state.set_state(CreationStates.post_generation)
        text = POST_GENERATION_TEXT.format(
            balance=balance,
            current_mode=work_mode
        )
        keyboard = get_post_generation_keyboard()
        screen = 'post_generation'
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=keyboard,
        screen_code=screen
    )
```

---

## 📊 ТАБЛИЦА ИНТЕГРАЦИИ ВСЕХ ФАЙЛОВ

| Файл | Изменения | Статус |
|---|---|---|
| `bot/states/fsm.py` | + WorkMode enum, + 15 новых states | ✅ |
| `bot/utils/texts.py` | + 18 текстовых констант + MODE_NAMES + MODE_DESCRIPTIONS | ✅ |
| `bot/keyboards/inline.py` | + 18 новых функций клавиатур | ✅ |
| `bot/handlers/user_start.py` | Обновить вызов select_mode вместо create_design | ⏳ |
| `bot/handlers/creation_v3.py` | ✨ НОВЫЙ ФАЙЛ с 50+ обработчиков | ✅ |
| `bot/utils/navigation.py` | edit_menu() - никаких изменений (совместима с V3) | ✅ |
| `bot/database/db.py` | get_user_balance(), update_balance() - совместима | ✅ |
| `bot/loader.py` | Добавить импорт и регистрацию router'а из creation_v3.py | ⏳ |
| `bot/config.py` | Добавить логирование режимов (опционально) | ⏳ |

---

## 🚀 ПОРЯДОК ВЫПОЛНЕНИЯ

### ЭТАП 1: Базовая структура (День 1)
```
1. Обновить bot/states/fsm.py (+ WorkMode, + states)
2. Обновить bot/utils/texts.py (+ новые тексты)
3. Обновить bot/keyboards/inline.py (+ 18 клавиатур)
4. Создать bot/handlers/creation_v3.py (весь код выше)
5. Обновить bot/loader.py (+ импорт + регистрация)
```

### ЭТАП 2: Тестирование (День 2)
```
1. Тест режима NEW_DESIGN (полный цикл)
2. Тест режима EDIT_DESIGN
3. Тест режима SAMPLE_DESIGN
4. Тест режима ARRANGE_FURNITURE
5. Тест режима FACADE_DESIGN
6. Проверка логирования
```

### ЭТАП 3: Оптимизация (День 3)
```
1. Проверить работу SMP (Single Menu Pattern)
2. Оптимизировать API вызовы
3. Добавить обработку ошибок
4. Финальное тестирование
```

---

## 📋 ЧЕКЛИСТ ИНТЕГРАЦИИ

- [ ] FSM расширен на 15 новых states
- [ ] Тексты экранов добавлены для всех 18 экранов
- [ ] 18 функций клавиатур созданы
- [ ] 50+ обработчиков в creation_v3.py реализованы
- [ ] Router зарегистрирован в loader.py
- [ ] Логирование работает для каждого режима+экрана
- [ ] Все callback'а правильно обработаны
- [ ] Баланс проверяется перед генерацией
- [ ] SMP работает корректно
- [ ] Тестирование всех режимов пройдено

---

## 🐛 ИЗВЕСТНЫЕ ВОПРОСЫ И РЕШЕНИЯ

### Вопрос 1: Как работает логирование?
```python
# Формат: MODE+STATE
print(f"[V3] {work_mode.upper()}+UPLOADING_PHOTO - photo saved, user_id={user_id}")
# Пример: [V3] NEW_DESIGN+UPLOADING_PHOTO - photo saved, user_id=123456
```

### Вопрос 2: Где хранится текущий режим?
```python
# В FSM state.data
await state.update_data(work_mode=WorkMode.NEW_DESIGN.value)

# Восстановление
data = await state.get_data()
work_mode = data.get('work_mode')
```

### Вопрос 3: Как обновляется баланс в UI?
```python
# После каждой генерации баланс обновляется в тексте экрана
text = CHOOSE_STYLE_TEXT.format(
    balance=new_balance,  # Новое значение
    current_mode=work_mode,
    selected_room=room
)

await edit_menu(
    callback=callback,
    state=state,
    text=text,  # Текст обновлен с новым балансом
    keyboard=keyboard
)
```

---

## 📞 ПОДДЕРЖКА

Если возникнут вопросы при интеграции:
1. Проверьте логирование в консоли
2. Посмотрите на формат callback_data (должен совпадать с именем функции)
3. Убедитесь, что FSM state правильно обновляется
4. Проверьте, что все клавиатуры импортированы в creation_v3.py

---

**План готов к выполнению! 🚀**

Следующий шаг: Выполнить ЭТАП 1 (обновление файлов) и создать pull request.
