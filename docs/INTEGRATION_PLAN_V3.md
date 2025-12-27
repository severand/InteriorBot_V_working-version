# 🔧 ПЛАН ИНТЕГРАЦИИ V3 - ДЕТАЛЬНЫЙ ГАЙД

**Дата создания:** 2025-12-28  
**Версия:** V3.0 - ПОЛНАЯ ИНТЕГРАЦИЯ С РЕЖИМАМИ РАБОТЫ  
**Статус:** ✅ ГОТОВ К ИСПОЛНЕНИЮ  

---

## 📋 СОДЕРЖАНИЕ
1. [Архитектурные изменения](#архитектурные-изменения)
2. [Добавление новых FSM состояний](#добавление-новых-fsm-состояний)
3. [Таблица маппинга V1 → V3](#таблица-маппинга-v1--v3)
4. [Разработка новых компонентов](#разработка-новых-компонентов)
5. [Модификация существующих компонентов](#модификация-существующих-компонентов)
6. [Порядок разработки (выполнения)](#порядок-разработки-выполнения)
7. [Тестирование и валидация](#тестирование-и-валидация)

---

## 🏗 АРХИТЕКТУРНЫЕ ИЗМЕНЕНИЯ

### ШАГ 1: СИСТЕМА РЕЖИМОВ РАБОТЫ (РЕЖИМНЫЙ ДВИЖОК)

**ПРОБЛЕМА:** V1 имел один поток - создание дизайна. V3 требует 5 НЕЗАВИСИМЫХ РЕЖИМОВ с собственными потоками.

**РЕШЕНИЕ:** Добавить систему режимов в FSM State контекст.

```
FSM State Context (в памяти):
├── user_id
├── chat_id
├── menu_message_id         (Single Menu Pattern - существует)
├── current_mode: str       ← НОВОЕ (NEW_DESIGN / EDIT_DESIGN / SAMPLE_DESIGN / etc)
├── photos: dict            ← НОВОЕ (по режимам)
│   ├── new_photo_id
│   ├── sample_photo_id
│   ├── furniture_photo_id
│   ├── facade_sample_id
│   └── facade_original_id
├── room_type: str          (существует)
├── style_type: str         (существует)
├── latest_generation_id    ← НОВОЕ (отслеживание последней генерации)
└── mode_history: list      ← НОВОЕ (для логирования FSM: MODE+SCREEN)
```

### ШАГ 2: СИСТЕМА ЛОГИРОВАНИЯ РЕЖИМОВ

**ТРЕБОВАНИЕ:** В каждом логе показывать "Режим + Экран"

**Реализация:**
```python
# Везде в обработчиках добавить логирование:
logger.info(f"USER {user_id} | {current_mode}+{screen_code} | Action: {action}")

# Примеры:
# USER 123456 | NEW_DESIGN+UPLOADING_PHOTO | Action: photo_received
# USER 123456 | NEW_DESIGN+CHOOSE_STYLE | Action: style_selected
# USER 123456 | EDIT_DESIGN+CLEAR_CONFIRM | Action: confirm_clear
```

### ШАГ 3: СИСТЕМА ТЕКСТОВЫХ ПОЛЕЙ С ДИНАМИЧЕСКОЙ ИНФОРМАЦИЕЙ

**ТРЕБОВАНИЕ:** Каждое текстовое поле должно показывать:
- Текущий режим
- Текущий баланс
- Инструкция для режима

**Реализация:**
```python
# В texts.py добавить:
def get_mode_header(current_mode: str, balance: int) -> str:
    mode_text = MODES_TITLES[current_mode]  # "Создание нового дизайна", etc
    return f"Режим: {mode_text}\n💰 Баланс: {balance}\n"

# Использование:
header = get_mode_header(current_mode, user.balance)
full_text = header + UPLOADING_PHOTO_TEXT
```

---

## 📍 ДОБАВЛЕНИЕ НОВЫХ FSM СОСТОЯНИЙ

### ТЕКУЩИЕ СОСТОЯНИЯ (из fsm.py)

```python
# bot/states/fsm.py - ДО
class CreationStates(StatesGroup):
    waiting_for_photo = State()
    what_is_in_photo = State()
    choose_room = State()
    choose_style = State()
    waiting_for_room_description = State()
    waiting_for_exterior_prompt = State()
```

### НОВЫЕ СОСТОЯНИЯ (ПОЛНЫЙ СПИСОК)

```python
# bot/states/fsm.py - ПОСЛЕ

class CreationStates(StatesGroup):
    # РЕЖИМНЫЙ ВЫБОР
    choosing_mode = State()               # НОВОЕ: Экран выбора режима
    
    # NEW DESIGN поток (обновлено)
    new_design_upload_photo = State()     # ПЕРЕИМЕНОВАНО из waiting_for_photo
    new_design_choose_room = State()      # ПЕРЕИМЕНОВАНО из choose_room
    new_design_choose_style_1 = State()   # ПЕРЕИМЕНОВАНО + новый choose_style_1
    new_design_choose_style_2 = State()   # НОВОЕ: Ещё стили
    new_design_text_input = State()       # НОВОЕ: Текстовое редактирование
    
    # EDIT DESIGN поток (НОВОЕ)
    edit_design_upload_photo = State()
    edit_design_menu = State()
    edit_design_clear_confirm = State()
    edit_design_text_input = State()
    
    # SAMPLE DESIGN поток (НОВОЕ)
    sample_design_upload_photo = State()
    sample_design_upload_sample = State()
    sample_design_generate = State()
    sample_design_text_input = State()
    
    # ARRANGE FURNITURE поток (НОВОЕ)
    furniture_upload_photo = State()
    furniture_upload_furniture_photos = State()
    furniture_generate = State()
    furniture_text_input = State()
    
    # FACADE DESIGN поток (НОВОЕ)
    facade_upload_photo = State()
    facade_upload_sample = State()
    facade_generate = State()
    facade_text_input = State()
    
    # POST-GENERATION состояния
    post_generation_new_design = State()     # НОВОЕ
    post_generation_sample = State()         # НОВОЕ
    post_generation_furniture = State()      # НОВОЕ
    post_generation_facade = State()         # НОВОЕ
```

**ИТОГО:**
- Было: 6 состояний
- Стало: 28 состояний
- Добавлено: 22 новых

---

## 📊 ТАБЛИЦА МАППИНГА V1 → V3

### ЭКРАНЫ V1 (13 пользовательских)

| V1 Экран | V1 FSM State | СТАТУС |
|---|---|---|
| MAIN_MENU | None | РЕДАКТИРУЕТСЯ |
| UPLOAD_PHOTO | waiting_for_photo | ДУБЛИРУЕТСЯ НА 5 РЕЖИМОВ |
| WHAT_IS_IN_PHOTO | what_is_in_photo | ПЕРЕИМЕНОВЫВАЕТСЯ → ROOM_CHOICE |
| CHOOSE_ROOM | choose_room | ПОЛНОСТЬЮ УДАЛЯЕТСЯ (→ ROOM_CHOICE) |
| CHOOSE_STYLE | choose_style | РАСКРЫВАЕТСЯ НА 2 (STYLE_1, STYLE_2) |
| POST_GENERATION | None | РАСКРЫВАЕТСЯ НА 4 (для каждого режима) |
| PROFILE | None | СОХРАНЯЕТСЯ |
| PAYMENT | None | СОХРАНЯЕТСЯ |
| PAYMENT_LINK | None | СОХРАНЯЕТСЯ |
| SUPPORT | None | СОХРАНЯЕТСЯ |
| ADMIN_MAIN | None | СОХРАНЯЕТСЯ |
| ... другие админ | ... | СОХРАНЯЮТСЯ |

### НОВЫЕ ЭКРАНЫ V3

| V3 Экран | V3 FSM State | ОПИСАНИЕ |
|---|---|---|
| CHOOSING_MODE | choosing_mode | Выбор 5 режимов |
| ROOM_CHOICE | (дин) | Выбор комнаты для NEW_DESIGN |
| CHOOSE_STYLE_1 | new_design_choose_style_1 | 1-я часть стилей |
| CHOOSE_STYLE_2 | new_design_choose_style_2 | 2-я часть стилей |
| TEXT_INPUT | (дин) | Текстовое редактирование (все режимы) |
| EDIT_DESIGN | edit_design_menu | Меню редактирования |
| CLEAR_CONFIRM | edit_design_clear_confirm | Подтверждение очистки |
| DOWNLOAD_SAMPLE | sample_design_upload_sample | Загрузка образца |
| GENERATION_SAMPLE | sample_design_generate | Экран генерации примерки |
| UPLOADING_FURNITURE | furniture_upload_furniture_photos | Загрузка мебели |
| GENERATION_FURNITURE | furniture_generate | Экран генерации мебели |
| LOADING_FACADE_SAMPLE | facade_upload_sample | Загрузка образца фасада |
| GENERATION_FACADE | facade_generate | Экран генерации фасада |
| POST_GEN_SAMPLE | post_generation_sample | После генерации примерки |
| POST_GEN_FURNITURE | post_generation_furniture | После генерации мебели |
| POST_GEN_FACADE | post_generation_facade | После генерации фасада |

---

## 🔨 РАЗРАБОТКА НОВЫХ КОМПОНЕНТОВ

### 1️⃣ НОВЫЕ FSM СОСТОЯНИЯ

**Файл:** `bot/states/fsm.py`

**ДЕЙСТВИЕ:** Полностью переписать CreationStates согласно таблице выше

```python
class CreationStates(StatesGroup):
    # Режимный выбор
    choosing_mode = State()
    
    # NEW DESIGN
    new_design_upload_photo = State()
    new_design_choose_room = State()
    new_design_choose_style_1 = State()
    new_design_choose_style_2 = State()
    new_design_text_input = State()
    new_design_post_generation = State()
    
    # EDIT DESIGN
    edit_design_upload_photo = State()
    edit_design_menu = State()
    edit_design_clear_confirm = State()
    edit_design_text_input = State()
    
    # SAMPLE DESIGN
    sample_design_upload_photo = State()
    sample_design_upload_sample = State()
    sample_design_generate = State()
    sample_design_text_input = State()
    sample_design_post_generation = State()
    
    # ARRANGE FURNITURE
    furniture_upload_photo = State()
    furniture_upload_furniture_photos = State()
    furniture_generate = State()
    furniture_text_input = State()
    furniture_post_generation = State()
    
    # FACADE DESIGN
    facade_upload_photo = State()
    facade_upload_sample = State()
    facade_generate = State()
    facade_text_input = State()
    facade_post_generation = State()
```

### 2️⃣ НОВЫЕ ТЕКСТОВЫЕ КОНСТАНТЫ

**Файл:** `bot/utils/texts.py`

**ДОБАВИТЬ:**

```python
# РЕЖИМЫ (для заголовков)
MODE_TITLES = {
    "NEW_DESIGN": "Создание нового дизайна",
    "EDIT_DESIGN": "Редактирование дизайна",
    "SAMPLE_DESIGN": "Примерка дизайна",
    "ARRANGE_FURNITURE": "Расстановка мебели",
    "FACADE_DESIGN": "Дизайн фасада дома"
}

# ЭКРАН 1: MAIN MENU (НОВОЕ)
MAIN_MENU_CHOOSE_MODE = """
Выберите режим работы
"""

# ЭКРАН 2: UPLOADING_PHOTO (ВАРИАТИВНЫЙ ТЕКСТ)
UPLOADING_PHOTO_NEW_DESIGN = "Загрузите фото помещения для создания нового дизайна"
UPLOADING_PHOTO_EDIT_DESIGN = "Загрузите фото помещения для редактирования дизайна"
UPLOADING_PHOTO_SAMPLE_DESIGN = "Загрузите фото помещения для примерки дизайна"
UPLOADING_PHOTO_ARRANGE_FURNITURE = "Загрузите фото помещения для расстановки мебели"
UPLOADING_PHOTO_FACADE = "Загрузите фото дома для создания дизайна фасада"

# ЭКРАН 3: ROOM_CHOICE (БЕЗ ИЗМЕНЕНИЙ)
ROOM_CHOICE_TEXT = """
Выберите тип помещения
"""

# ЭКРАН 4-5: CHOOSE_STYLE (РАЗДЕЛЕНА НА 2)
CHOOSE_STYLE_1_TEXT = "Выберите стиль дизайна. ВНИМАНИЕ: генерация начнется сразу после нажатия кнопки."
CHOOSE_STYLE_2_TEXT = "Выберите стиль дизайна. ВНИМАНИЕ: генерация начнется сразу после нажатия кнопки."

# ЭКРАН 6: POST_GENERATION (НОВОЕ)
POST_GENERATION_TEXT = "Вы можете выбрать новый стиль, новую комнату или редактировать текстом."

# ЭКРАН 7: TEXT_INPUT (НОВОЕ)
TEXT_INPUT_PROMPT = "Дайте задание AI"

# ЭКРАН 8: EDIT_DESIGN (НОВОЕ)
EDIT_DESIGN_MENU_TEXT = "Выберите задачу для редактирования фото."

# ЭКРАН 9: CLEAR_CONFIRM (НОВОЕ)
CLEAR_CONFIRM_TEXT = "Вы уверены, что хотите очистить помещение?"

# ЭКРАН 10: DOWNLOAD_SAMPLE (НОВОЕ)
DOWNLOAD_SAMPLE_TEXT = "Загрузите фото образец для примерки"

# ЭКРАН 11: GENERATION_SAMPLE (НОВОЕ)
GENERATION_SAMPLE_TEXT = "Примерьте дизайн на ваше помещение"

# ЭКРАН 12: POST_GENERATION_SAMPLE (НОВОЕ)
POST_GENERATION_SAMPLE_TEXT = "Результат примерки дизайна"

# ЭКРАН 13: UPLOADING_FURNITURE (НОВОЕ)
UPLOADING_FURNITURE_TEXT = "Загрузите фото мебели"

# ЭКРАН 14: GENERATION_FURNITURE (НОВОЕ)
GENERATION_FURNITURE_TEXT = "Примерьте мебель на ваше помещение"

# ЭКРАН 15: POST_GENERATION_FURNITURE (НОВОЕ)
POST_GENERATION_FURNITURE_TEXT = "Результат расстановки мебели"

# ЭКРАН 16: LOADING_FACADE_SAMPLE (НОВОЕ)
LOADING_FACADE_SAMPLE_TEXT = "Загрузите фото образец фасада дома"

# ЭКРАН 17: GENERATION_FACADE (НОВОЕ)
GENERATION_FACADE_TEXT = "Примерьте фасад на ваш дом"

# ЭКРАН 18: POST_GENERATION_FACADE (НОВОЕ)
POST_GENERATION_FACADE_TEXT = "Результат дизайна фасада"

# ФУНКЦИЯ ДЛЯ ДИНАМИЧЕСКОГО ЗАГОЛОВКА
def get_mode_header(current_mode: str, balance: int) -> str:
    """Генерирует заголовок с режимом и балансом"""
    mode_text = MODE_TITLES.get(current_mode, "Неизвестный режим")
    return f"Режим: {mode_text}\n💰 Баланс: {balance}\n"
```

### 3️⃣ НОВЫЕ ФУНКЦИИ КЛАВИАТУР

**Файл:** `bot/keyboards/inline.py`

**ДОБАВИТЬ:**

```python
# КЛАВИАТУРА 1: ВЫБОР РЕЖИМА (НОВОЕ)
def get_mode_selection_keyboard() -> InlineKeyboardMarkup:
    """Экран выбора режима работы"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎨 Создать новый дизайн", 
                                    callback_data="mode_new_design"))
    builder.row(InlineKeyboardButton(text="✏️ Редактировать дизайн", 
                                    callback_data="mode_edit_design"))
    builder.row(InlineKeyboardButton(text="👔 Примерить дизайн", 
                                    callback_data="mode_sample_design"))
    builder.row(InlineKeyboardButton(text="🪑 Расставить мебель", 
                                    callback_data="mode_arrange_furniture"))
    builder.row(InlineKeyboardButton(text="🏠 Создать дизайн фасада", 
                                    callback_data="mode_facade_design"))
    builder.row(InlineKeyboardButton(text="👤 Личный кабинет", 
                                    callback_data="show_profile"))
    builder.row(InlineKeyboardButton(text="⚙️ Админ-панель", 
                                    callback_data="admin_panel"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 3: ВЫБОР КОМНАТЫ (НОВОЕ - раскрыто на 2 в ряд)
def get_room_choice_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа помещения"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💪 Гостиная", callback_data="room_living_room"),
        InlineKeyboardButton(text="🍽 Кухня", callback_data="room_kitchen")
    )
    builder.row(
        InlineKeyboardButton(text="🛏 Спальня", callback_data="room_bedroom"),
        InlineKeyboardButton(text="👶 Детская", callback_data="room_nursery")
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Студия", callback_data="room_studio"),
        InlineKeyboardButton(text="💼 Кабинет", callback_data="room_home_office")
    )
    builder.row(
        InlineKeyboardButton(text="🚿 Ванная", callback_data="room_bathroom_full"),
        InlineKeyboardButton(text="🚽 Санузел", callback_data="room_toilet")
    )
    builder.row(
        InlineKeyboardButton(text="🏃 Прихожая", callback_data="room_entryway"),
        InlineKeyboardButton(text="👗 Гардеробная", callback_data="room_wardrobe")
    )
    builder.row(InlineKeyboardButton(text="📸 Новое фото", callback_data="mode_new_design"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

# КЛАВИАТУРА 4-5: ВЫБОР СТИЛЯ (РАСКРЫТО НА 2 ЧАСТИ)
def get_style_1_keyboard() -> InlineKeyboardMarkup:
    """1-я часть стилей дизайна"""
    builder = InlineKeyboardBuilder()
    styles = [
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
    for i in range(0, len(styles), 2):
        builder.row(
            InlineKeyboardButton(text=styles[i][0], callback_data=styles[i][1]),
            InlineKeyboardButton(text=styles[i+1][0], callback_data=styles[i+1][1])
        )
    builder.row(InlineKeyboardButton(text="▶️ Ещё стили", callback_data="style_next_page"))
    builder.row(InlineKeyboardButton(text="⬅️ Выбрать комнату", callback_data="back_to_room_choice"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

def get_style_2_keyboard() -> InlineKeyboardMarkup:
    """2-я часть стилей дизайна (дополнительные)"""
    builder = InlineKeyboardBuilder()
    styles = [
        ("Теплая роскошь", "style_warm_luxury"),
        ("Нео Арт Деко", "style_neo_artdeco"),
        ("Осознанная электика", "style_conscious_eclectic"),
        ("Тактильный Максимализм", "style_tactile_maximalism"),
        ("Монолит", "style_monolith"),
        ("Эко-минимализм", "style_eco_minimal"),
    ]
    for i in range(0, len(styles), 2):
        if i + 1 < len(styles):
            builder.row(
                InlineKeyboardButton(text=styles[i][0], callback_data=styles[i][1]),
                InlineKeyboardButton(text=styles[i+1][0], callback_data=styles[i+1][1])
            )
        else:
            builder.row(InlineKeyboardButton(text=styles[i][0], callback_data=styles[i][1]))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="style_prev_page"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

# КЛАВИАТУРА 6: POST_GENERATION (ПЕРЕРАБОТАНО)
def get_post_generation_keyboard(show_room_option: bool = True) -> InlineKeyboardMarkup:
    """После генерации - выбор действий"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎨 Новый стиль", callback_data="back_to_style"),
        InlineKeyboardButton(text="🏛 Новая комната", callback_data="back_to_room_choice")
    )
    builder.row(InlineKeyboardButton(text="✍️ Текстовое редактирование", 
                                    callback_data="text_edit_mode"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

# КЛАВИАТУРА 7: TEXT_INPUT (НОВОЕ)
def get_text_input_keyboard(back_screen: str = "post_generation") -> InlineKeyboardMarkup:
    """Ввод текстового промпта"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_{back_screen}"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 8: EDIT_DESIGN (НОВОЕ)
def get_edit_design_keyboard() -> InlineKeyboardMarkup:
    """Меню редактирования дизайна"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗹️ Очистить фото", callback_data="clear_design"),
        InlineKeyboardButton(text="📝 Ввести текст", callback_data="text_edit_design")
    )
    builder.row(InlineKeyboardButton(text="📸 Новое фото", callback_data="mode_edit_design"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

# КЛАВИАТУРА 9: CLEAR_CONFIRM (НОВОЕ)
def get_clear_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение очистки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="confirm_clear"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_clear")
    )
    builder.adjust(2)
    return builder.as_markup()

# КЛАВИАТУРА 10: DOWNLOAD_SAMPLE (НОВОЕ)
def get_download_sample_keyboard() -> InlineKeyboardMarkup:
    """Загрузка образца для примерки"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_upload_photo"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 11: GENERATION_SAMPLE (НОВОЕ)
def get_generation_sample_keyboard() -> InlineKeyboardMarkup:
    """Экран генерации примерки"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎨 Примерить дизайн", 
                                    callback_data="generate_sample"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_sample_upload"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 12: POST_GENERATION_SAMPLE (НОВОЕ)
def get_post_generation_sample_keyboard() -> InlineKeyboardMarkup:
    """После генерации примерки"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✍️ Текстовое редактирование", 
                                    callback_data="text_edit_sample"))
    builder.row(InlineKeyboardButton(text="📸 Новый образец", 
                                    callback_data="back_sample_upload"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 13: UPLOADING_FURNITURE (НОВОЕ)
def get_uploading_furniture_keyboard() -> InlineKeyboardMarkup:
    """Загрузка мебели"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_upload_photo"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 14: GENERATION_FURNITURE (НОВОЕ)
def get_generation_furniture_keyboard() -> InlineKeyboardMarkup:
    """Экран генерации расстановки мебели"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎨 Расставить мебель", 
                                    callback_data="generate_furniture"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", 
                                    callback_data="back_furniture_upload"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 15: POST_GENERATION_FURNITURE (НОВОЕ)
def get_post_generation_furniture_keyboard() -> InlineKeyboardMarkup:
    """После генерации расстановки мебели"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✍️ Текстовое редактирование", 
                                    callback_data="text_edit_furniture"))
    builder.row(InlineKeyboardButton(text="📸 Новая мебель", 
                                    callback_data="back_furniture_upload"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 16: LOADING_FACADE_SAMPLE (НОВОЕ)
def get_loading_facade_sample_keyboard() -> InlineKeyboardMarkup:
    """Загрузка образца фасада"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_upload_photo"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 17: GENERATION_FACADE (НОВОЕ)
def get_generation_facade_keyboard() -> InlineKeyboardMarkup:
    """Экран генерации дизайна фасада"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Примерить фасад", 
                                    callback_data="generate_facade"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", 
                                    callback_data="back_facade_sample"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# КЛАВИАТУРА 18: POST_GENERATION_FACADE (НОВОЕ)
def get_post_generation_facade_keyboard() -> InlineKeyboardMarkup:
    """После генерации дизайна фасада"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✍️ Текстовое редактирование", 
                                    callback_data="text_edit_facade"))
    builder.row(InlineKeyboardButton(text="📸 Новый образец фасада", 
                                    callback_data="back_facade_sample"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()
```

---

## 🔄 МОДИФИКАЦИЯ СУЩЕСТВУЮЩИХ КОМПОНЕНТОВ

### 1️⃣ user_start.py

**ИЗМЕНЕНИЯ:**

#### А) `cmd_start()` - без изменений, но добавить режим

```python
@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    user = await db.get_user(message.from_user.id)
    
    # Если пользователь новый
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username)
    
    # Инициализировать режим
    await state.update_data(
        menu_message_id=None,
        current_mode=None,
        photos={},
        latest_generation_id=None
    )
    
    await show_main_menu(message, state, admins=[...])
```

#### Б) `show_main_menu()` (ПЕРЕРАБОТКА) - изменить на выбор режимов

```python
async def show_main_menu(message: Message, state: FSMContext, admins: list):
    """Главное меню - выбор режима (V3)"""
    user = await db.get_user(message.from_user.id)
    is_admin = message.from_user.id in admins
    
    # Сбросить состояние FSM (но сохранить menu_message_id!)
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    await state.set_state(None)
    
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
    
    # Подготовить текст с заголовком
    text = f"💰 Баланс: {user.balance}\n\n{MAIN_MENU_CHOOSE_MODE}"
    
    # Редактировать меню
    await edit_menu(
        callback=message,  # Адаптировать edit_menu для Message
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(is_admin),
        screen_code='main_menu'
    )
```

#### В) `back_to_main_menu()` - переиспользовать

```python
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list):
    """Возврат в главное меню из любой точки"""
    user = await db.get_user(callback.from_user.id)
    is_admin = callback.from_user.id in admins
    
    # Сохранить menu_message_id
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    # Полный сброс режима
    await state.clear()
    
    # Восстановить menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
    
    text = f"💰 Баланс: {user.balance}\n\n{MAIN_MENU_CHOOSE_MODE}"
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(is_admin),
        screen_code='main_menu'
    )
```

---

### 2️⃣ creation.py

**ПОЛНАЯ ПЕРЕРАБОТКА** - создать обработчики для всех 5 режимов

#### А) Обработчик выбора режима (НОВОЕ)

```python
@router.callback_query(F.data == "mode_new_design")
async def mode_new_design(callback: CallbackQuery, state: FSMContext):
    """Выбор режима: Создание нового дизайна"""
    user = await db.get_user(callback.from_user.id)
    
    if user.balance <= 0:
        await callback.answer("⚠️ Недостаточно баланса!", show_alert=True)
        return
    
    # Установить режим
    await state.update_data(current_mode="NEW_DESIGN")
    await state.set_state(CreationStates.new_design_upload_photo)
    
    # Логирование
    logger.info(f"USER {callback.from_user.id} | NEW_DESIGN | Режим выбран")
    
    # Показать экран загрузки
    text = f"{get_mode_header('NEW_DESIGN', user.balance)}{UPLOADING_PHOTO_NEW_DESIGN}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(),  # Измененная клавиатура
        screen_code='uploading_photo_new_design'
    )

@router.callback_query(F.data == "mode_edit_design")
async def mode_edit_design(callback: CallbackQuery, state: FSMContext):
    """Режим: Редактирование дизайна"""
    user = await db.get_user(callback.from_user.id)
    
    await state.update_data(current_mode="EDIT_DESIGN")
    await state.set_state(CreationStates.edit_design_upload_photo)
    
    logger.info(f"USER {callback.from_user.id} | EDIT_DESIGN | Режим выбран")
    
    text = f"{get_mode_header('EDIT_DESIGN', user.balance)}{UPLOADING_PHOTO_EDIT_DESIGN}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_upload_photo_keyboard(),
        screen_code='uploading_photo_edit_design'
    )

# Аналогично для SAMPLE_DESIGN, ARRANGE_FURNITURE, FACADE_DESIGN...
```

#### Б) Обработчик загрузки фото (ПЕРЕРАБОТКА - работает со всеми режимами)

```python
@router.message(
    StateFilter(
        CreationStates.new_design_upload_photo,
        CreationStates.edit_design_upload_photo,
        CreationStates.sample_design_upload_photo,
        CreationStates.furniture_upload_photo,
        CreationStates.facade_upload_photo
    )
)
async def photo_handler_multi_mode(message: Message, state: FSMContext):
    """Обработчик загрузки фото для всех режимов"""
    user = await db.get_user(message.from_user.id)
    data = await state.get_data()
    current_mode = data.get('current_mode')
    
    # Валидация
    if not message.photo:
        return
    
    if user.balance <= 0:
        await message.answer(NO_BALANCE_TEXT)
        return
    
    # Сохранить фото
    photo_id = message.photo[-1].file_id
    
    # В зависимости от режима - переход на следующий экран
    if current_mode == "NEW_DESIGN":
        await state.update_data(photos={'new_photo_id': photo_id})
        await state.set_state(CreationStates.new_design_choose_room)
        logger.info(f"USER {message.from_user.id} | NEW_DESIGN+UPLOADING_PHOTO | photo_received")
        
        text = f"{get_mode_header('NEW_DESIGN', user.balance)}{ROOM_CHOICE_TEXT}"
        await update_menu_after_photo(
            message=message,
            state=state,
            text=text,
            keyboard=get_room_choice_keyboard(),
            screen_code='room_choice'
        )
    
    elif current_mode == "EDIT_DESIGN":
        await state.update_data(photos={'edit_photo_id': photo_id})
        await state.set_state(CreationStates.edit_design_menu)
        logger.info(f"USER {message.from_user.id} | EDIT_DESIGN+UPLOADING_PHOTO | photo_received")
        
        text = f"{get_mode_header('EDIT_DESIGN', user.balance)}{EDIT_DESIGN_MENU_TEXT}"
        await update_menu_after_photo(
            message=message,
            state=state,
            text=text,
            keyboard=get_edit_design_keyboard(),
            screen_code='edit_design_menu'
        )
    
    # ... аналогично для других режимов
```

#### В) Обработчик выбора комнаты (NEW_DESIGN)

```python
@router.callback_query(F.data.startswith("room_"), StateFilter(CreationStates.new_design_choose_room))
async def new_design_room_choice(callback: CallbackQuery, state: FSMContext):
    """Выбор комнаты в режиме NEW_DESIGN"""
    user = await db.get_user(callback.from_user.id)
    
    room_type = callback.data.replace("room_", "")
    await state.update_data(room_type=room_type)
    await state.set_state(CreationStates.new_design_choose_style_1)
    
    logger.info(f"USER {callback.from_user.id} | NEW_DESIGN+ROOM_CHOICE | room={room_type}")
    
    text = f"{get_mode_header('NEW_DESIGN', user.balance)}{CHOOSE_STYLE_1_TEXT}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_style_1_keyboard(),
        screen_code='choose_style_1'
    )
```

#### Г) Обработчик выбора стиля (NEW_DESIGN)

```python
@router.callback_query(F.data.startswith("style_"), StateFilter(CreationStates.new_design_choose_style_1))
async def new_design_style_choice_1(callback: CallbackQuery, state: FSMContext):
    """Выбор стиля в режиме NEW_DESIGN"""
    user = await db.get_user(callback.from_user.id)
    
    if user.balance <= 0:
        await callback.answer("⚠️ Недостаточно баланса!", show_alert=True)
        return
    
    style_type = callback.data.replace("style_", "")
    await state.update_data(style_type=style_type)
    
    # Уменьшить баланс
    await db.update_balance(callback.from_user.id, -1)
    
    logger.info(f"USER {callback.from_user.id} | NEW_DESIGN+CHOOSE_STYLE | style={style_type}")
    
    # Генерация
    data = await state.get_data()
    photo_id = data['photos']['new_photo_id']
    room = data.get('room_type')
    
    # Вызвать API генерации
    generation_result = await services.kie_api.generate_design(
        photo_id=photo_id,
        room_type=room,
        style_type=style_type
    )
    
    # Сохранить результат
    await state.update_data(latest_generation_id=generation_result['id'])
    
    # Показать результат
    await edit_menu(
        callback=callback,
        state=state,
        text=POST_GENERATION_TEXT,
        keyboard=get_post_generation_keyboard(),
        screen_code='post_generation_new_design'
    )
    
    # Отправить сгенерированное изображение
    await callback.message.answer_photo(
        photo=generation_result['image_url'],
        caption="Вот ваш результат! 🎨"
    )
```

#### Д) Обработчик для других режимов

```python
# EDIT_DESIGN обработчики
@router.callback_query(F.data == "clear_design", StateFilter(CreationStates.edit_design_menu))
async def edit_design_clear(callback: CallbackQuery, state: FSMContext):
    """Подтверждение очистки в режиме EDIT_DESIGN"""
    user = await db.get_user(callback.from_user.id)
    
    await state.set_state(CreationStates.edit_design_clear_confirm)
    
    text = f"{get_mode_header('EDIT_DESIGN', user.balance)}{CLEAR_CONFIRM_TEXT}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_clear_confirm_keyboard(),
        screen_code='clear_confirm'
    )

@router.callback_query(F.data == "confirm_clear", StateFilter(CreationStates.edit_design_clear_confirm))
async def confirm_clear_space(callback: CallbackQuery, state: FSMContext):
    """Выполнить очистку помещения"""
    user = await db.get_user(callback.from_user.id)
    
    if user.balance <= 0:
        await callback.answer("⚠️ Недостаточно баланса!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, -1)
    
    data = await state.get_data()
    photo_id = data['photos']['edit_photo_id']
    
    # Вызвать API для очистки
    generation_result = await services.kie_api.clear_space(photo_id=photo_id)
    
    # Обновить последнюю генерацию
    await state.update_data(latest_generation_id=generation_result['id'])
    
    logger.info(f"USER {callback.from_user.id} | EDIT_DESIGN+CLEAR_CONFIRM | space_cleared")
    
    # Показать результат
    await callback.message.answer_photo(
        photo=generation_result['image_url'],
        caption="Помещение очищено! 🧹"
    )
    
    # Вернуться в меню редактирования
    await state.set_state(CreationStates.edit_design_menu)
    text = f"{get_mode_header('EDIT_DESIGN', user.balance)}{EDIT_DESIGN_MENU_TEXT}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_edit_design_keyboard(),
        screen_code='edit_design_menu'
    )

# SAMPLE_DESIGN обработчики
@router.message(StateFilter(CreationStates.sample_design_upload_sample))
async def sample_design_upload(message: Message, state: FSMContext):
    """Загрузка образца в режиме SAMPLE_DESIGN"""
    user = await db.get_user(message.from_user.id)
    
    if not message.photo:
        return
    
    sample_photo_id = message.photo[-1].file_id
    await state.update_data(photos={'sample_photo_id': sample_photo_id})
    await state.set_state(CreationStates.sample_design_generate)
    
    logger.info(f"USER {message.from_user.id} | SAMPLE_DESIGN+DOWNLOAD_SAMPLE | sample_uploaded")
    
    text = f"{get_mode_header('SAMPLE_DESIGN', user.balance)}{GENERATION_SAMPLE_TEXT}"
    await update_menu_after_photo(
        message=message,
        state=state,
        text=text,
        keyboard=get_generation_sample_keyboard(),
        screen_code='generation_sample'
    )

@router.callback_query(F.data == "generate_sample", StateFilter(CreationStates.sample_design_generate))
async def generate_sample_design(callback: CallbackQuery, state: FSMContext):
    """Генерация примерки в режиме SAMPLE_DESIGN"""
    user = await db.get_user(callback.from_user.id)
    
    if user.balance <= 0:
        await callback.answer("⚠️ Недостаточно баланса!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, -1)
    
    data = await state.get_data()
    original_photo = data['photos']['new_photo_id']
    sample_photo = data['photos']['sample_photo_id']
    
    # Вызвать API для примерки
    generation_result = await services.kie_api.try_on_design(
        original_photo_id=original_photo,
        sample_photo_id=sample_photo
    )
    
    await state.update_data(latest_generation_id=generation_result['id'])
    await state.set_state(CreationStates.sample_design_post_generation)
    
    logger.info(f"USER {callback.from_user.id} | SAMPLE_DESIGN+GENERATION | design_generated")
    
    # Показать результат
    await callback.message.answer_photo(
        photo=generation_result['image_url'],
        caption="Примерка готова! 👀"
    )
    
    text = f"{get_mode_header('SAMPLE_DESIGN', user.balance)}{POST_GENERATION_SAMPLE_TEXT}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_post_generation_sample_keyboard(),
        screen_code='post_generation_sample'
    )

# ARRANGE_FURNITURE обработчики
@router.message(StateFilter(CreationStates.furniture_upload_furniture_photos))
async def furniture_photos_upload(message: Message, state: FSMContext):
    """Загрузка фото мебели"""
    user = await db.get_user(message.from_user.id)
    
    if not message.photo:
        return
    
    furniture_photo_id = message.photo[-1].file_id
    await state.update_data(photos={'furniture_photo_id': furniture_photo_id})
    await state.set_state(CreationStates.furniture_generate)
    
    logger.info(f"USER {message.from_user.id} | ARRANGE_FURNITURE+UPLOADING_FURNITURE | furniture_uploaded")
    
    text = f"{get_mode_header('ARRANGE_FURNITURE', user.balance)}{GENERATION_FURNITURE_TEXT}"
    await update_menu_after_photo(
        message=message,
        state=state,
        text=text,
        keyboard=get_generation_furniture_keyboard(),
        screen_code='generation_furniture'
    )

@router.callback_query(F.data == "generate_furniture", StateFilter(CreationStates.furniture_generate))
async def generate_furniture_arrangement(callback: CallbackQuery, state: FSMContext):
    """Генерация расстановки мебели"""
    user = await db.get_user(callback.from_user.id)
    
    if user.balance <= 0:
        await callback.answer("⚠️ Недостаточно баланса!", show_alert=True)
        return
    
    await db.update_balance(callback.from_user.id, -1)
    
    data = await state.get_data()
    room_photo = data['photos']['new_photo_id']
    furniture_photo = data['photos']['furniture_photo_id']
    
    # Вызвать API
    generation_result = await services.kie_api.arrange_furniture(
        room_photo_id=room_photo,
        furniture_photo_id=furniture_photo
    )
    
    await state.update_data(latest_generation_id=generation_result['id'])
    await state.set_state(CreationStates.furniture_post_generation)
    
    logger.info(f"USER {callback.from_user.id} | ARRANGE_FURNITURE+GENERATION | furniture_arranged")
    
    # Показать результат
    await callback.message.answer_photo(
        photo=generation_result['image_url'],
        caption="Мебель расставлена! 🪑"
    )
    
    text = f"{get_mode_header('ARRANGE_FURNITURE', user.balance)}{POST_GENERATION_FURNITURE_TEXT}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_post_generation_furniture_keyboard(),
        screen_code='post_generation_furniture'
    )

# FACADE_DESIGN обработчики (аналогично SAMPLE_DESIGN)
@router.message(StateFilter(CreationStates.facade_upload_sample))
async def facade_sample_upload(message: Message, state: FSMContext):
    """Загрузка образца фасада"""
    user = await db.get_user(message.from_user.id)
    
    if not message.photo:
        return
    
    facade_sample_id = message.photo[-1].file_id
    await state.update_data(photos={'facade_sample_id': facade_sample_id})
    await state.set_state(CreationStates.facade_generate)
    
    logger.info(f"USER {message.from_user.id} | FACADE_DESIGN+LOADING_FACADE | sample_uploaded")
    
    text = f"{get_mode_header('FACADE_DESIGN', user.balance)}{GENERATION_FACADE_TEXT}"
    await update_menu_after_photo(
        message=message,
        state=state,
        text=text,
        keyboard=get_generation_facade_keyboard(),
        screen_code='generation_facade'
    )
```

---

### 3️⃣ Обработчик текстового редактирования (НОВОЕ - для всех режимов)

**ВАЖНО:** Текстовое редактирование работает с ПОСЛЕДНЕЙ генерацией в режиме!

```python
@router.callback_query(F.data.startswith("text_edit"))
async def text_edit_mode(callback: CallbackQuery, state: FSMContext):
    """Переход в режим текстового редактирования"""
    user = await db.get_user(callback.from_user.id)
    data = await state.get_data()
    current_mode = data.get('current_mode')
    
    # Проверка: есть ли генерация для редактирования
    if not data.get('latest_generation_id'):
        await callback.answer("⚠️ Нечего редактировать!", show_alert=True)
        return
    
    # Установить состояние в зависимости от режима
    if current_mode == "NEW_DESIGN":
        await state.set_state(CreationStates.new_design_text_input)
    elif current_mode == "EDIT_DESIGN":
        await state.set_state(CreationStates.edit_design_text_input)
    elif current_mode == "SAMPLE_DESIGN":
        await state.set_state(CreationStates.sample_design_text_input)
    elif current_mode == "ARRANGE_FURNITURE":
        await state.set_state(CreationStates.furniture_text_input)
    elif current_mode == "FACADE_DESIGN":
        await state.set_state(CreationStates.facade_text_input)
    
    logger.info(f"USER {callback.from_user.id} | {current_mode}+TEXT_INPUT | mode_entered")
    
    text = f"{get_mode_header(current_mode, user.balance)}{TEXT_INPUT_PROMPT}"
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_text_input_keyboard(),
        screen_code='text_input'
    )

@router.message(
    StateFilter(
        CreationStates.new_design_text_input,
        CreationStates.edit_design_text_input,
        CreationStates.sample_design_text_input,
        CreationStates.furniture_text_input,
        CreationStates.facade_text_input
    )
)
async def text_input_handler(message: Message, state: FSMContext):
    """Обработчик текстового промпта для редактирования"""
    user = await db.get_user(message.from_user.id)
    data = await state.get_data()
    current_mode = data.get('current_mode')
    
    if user.balance <= 0:
        await message.answer(NO_BALANCE_TEXT)
        return
    
    # Получить текстовый промпт
    text_prompt = message.text
    
    # Уменьшить баланс
    await db.update_balance(message.from_user.id, -1)
    
    # Получить последнюю генерацию
    last_generation_id = data.get('latest_generation_id')
    
    # Вызвать API редактирования
    generation_result = await services.kie_api.edit_by_text(
        generation_id=last_generation_id,
        text_prompt=text_prompt
    )
    
    # Обновить последнюю генерацию
    await state.update_data(latest_generation_id=generation_result['id'])
    
    logger.info(f"USER {message.from_user.id} | {current_mode}+TEXT_INPUT | text_applied={text_prompt[:30]}")
    
    # Показать результат
    await message.answer_photo(
        photo=generation_result['image_url'],
        caption="Редактирование применено! ✨"
    )
    
    # Вернуться на POST_GENERATION
    if current_mode == "NEW_DESIGN":
        await state.set_state(CreationStates.new_design_post_generation)
        text = f"{get_mode_header(current_mode, user.balance)}{POST_GENERATION_TEXT}"
        keyboard = get_post_generation_keyboard()
    elif current_mode == "SAMPLE_DESIGN":
        await state.set_state(CreationStates.sample_design_post_generation)
        text = f"{get_mode_header(current_mode, user.balance)}{POST_GENERATION_SAMPLE_TEXT}"
        keyboard = get_post_generation_sample_keyboard()
    elif current_mode == "ARRANGE_FURNITURE":
        await state.set_state(CreationStates.furniture_post_generation)
        text = f"{get_mode_header(current_mode, user.balance)}{POST_GENERATION_FURNITURE_TEXT}"
        keyboard = get_post_generation_furniture_keyboard()
    elif current_mode == "FACADE_DESIGN":
        await state.set_state(CreationStates.facade_post_generation)
        text = f"{get_mode_header(current_mode, user.balance)}{POST_GENERATION_FACADE_TEXT}"
        keyboard = get_post_generation_facade_keyboard()
    else:
        # EDIT_DESIGN - вернуться в меню
        await state.set_state(CreationStates.edit_design_menu)
        text = f"{get_mode_header(current_mode, user.balance)}{EDIT_DESIGN_MENU_TEXT}"
        keyboard = get_edit_design_keyboard()
    
    await edit_menu(
        callback=message,
        state=state,
        text=text,
        keyboard=keyboard,
        screen_code='post_generation'
    )
```

---

## 📋 ПОРЯДОК РАЗРАБОТКИ (ВЫПОЛНЕНИЯ)

### ФАЗА 1: Подготовка (День 1-2)

- [ ] **ШАГИ:**
  1. Обновить `bot/states/fsm.py` - добавить все 28 новых состояний
  2. Обновить `bot/utils/texts.py` - добавить все новые текстовые константы и функцию `get_mode_header()`
  3. Обновить `bot/keyboards/inline.py` - добавить все 18 новых функций клавиатур

- [ ] **ПРОВЕРКА:** 
  - Убедиться, что нет импорт-ошибок
  - Боту должно быть достаточно памяти для всех состояний
  - Все callback_data должны быть уникальны

### ФАЗА 2: Модификация обработчиков (День 3-5)

- [ ] **ШАГИ:**
  1. Обновить `user_start.py`:
     - `cmd_start()` - инициализировать режим
     - `show_main_menu()` - переделать на выбор режимов
     - `back_to_main_menu()` - полный сброс режима
  2. Переписать `creation.py`:
     - Добавить обработчик `mode_new_design()`, `mode_edit_design()`, и т.д.
     - Переписать `photo_handler()` для всех режимов
     - Добавить обработчики комнаты, стилей, редактирования
     - Добавить обработчик текстового редактирования

- [ ] **ПРОВЕРКА:**
  - Тестировать каждый режим отдельно
  - Проверить логирование (должны видны "MODE+SCREEN")
  - Убедиться, что баланс уменьшается при каждой генерации

### ФАЗА 3: Интеграция и тестирование (День 6-7)

- [ ] **ШАГИ:**
  1. Подключить все новые обработчики в `bot/loader.py`
  2. Полное тестирование всех потоков
  3. Проверка работы Single Menu Pattern со всеми режимами
  4. Проверка работы БД (сохранение меню, баланса, генераций)

- [ ] **ПРОВЕРКА:**
  - Каждый режим работает независимо
  - Можно переключаться между режимами без потери данных
  - Текстовое редактирование работает со всеми режимами
  - Логирование показывает все переходы

---

## 🧪 ТЕСТИРОВАНИЕ И ВАЛИДАЦИЯ

### ЧЕКЛИСТ ТЕСТИРОВАНИЯ

#### NEW_DESIGN режим
- [ ] /start → выбор режима
- [ ] Выбрать "Создать новый дизайн"
- [ ] Загрузить фото
- [ ] Выбрать комнату
- [ ] Выбрать стиль (1-я часть)
- [ ] Генерация прошла ✓
- [ ] Баланс уменьшился на 1 ✓
- [ ] Текстовое редактирование работает ✓
- [ ] Можно выбрать новый стиль / комнату / вернуться в меню ✓

#### EDIT_DESIGN режим
- [ ] Выбрать "Редактировать дизайн"
- [ ] Загрузить фото
- [ ] Выбрать "Очистить фото"
- [ ] Подтвердить очистку ✓
- [ ] Генерация прошла ✓
- [ ] Текстовое редактирование работает ✓

#### SAMPLE_DESIGN режим
- [ ] Выбрать "Примерить дизайн"
- [ ] Загрузить фото помещения
- [ ] Загрузить образец дизайна
- [ ] Нажать "Примерить дизайн"
- [ ] Генерация прошла ✓
- [ ] Текстовое редактирование работает ✓

#### ARRANGE_FURNITURE режим
- [ ] Выбрать "Расставить мебель"
- [ ] Загрузить фото помещения
- [ ] Загрузить фото мебели
- [ ] Нажать "Расставить мебель"
- [ ] Генерация прошла ✓
- [ ] Текстовое редактирование работает ✓

#### FACADE_DESIGN режим
- [ ] Выбрать "Создать дизайн фасада"
- [ ] Загрузить фото фасада дома
- [ ] Загрузить образец фасада
- [ ] Нажать "Примерить фасад"
- [ ] Генерация прошла ✓
- [ ] Текстовое редактирование работает ✓

#### Общие проверки
- [ ] Single Menu Pattern работает (нет спама сообщений)
- [ ] Логирование показывает "MODE+SCREEN" ✓
- [ ] Переключение между режимами без потери данных ✓
- [ ] /start не сбрасывает текущий режим (если не выбран новый)
- [ ] Админ-панель работает по-прежнему ✓
- [ ] Профиль и оплата работают по-прежнему ✓

---

## 📌 КРИТИЧЕСКИЕ ЗАМЕЧАНИЯ

### ⚠️ ОЧЕНЬ ВАЖНО!

1. **ТЕКСТОВОЕ РЕДАКТИРОВАНИЕ:**
   - Работает ТОЛЬКО с последней генерацией в текущем режиме!
   - Если пользователь переключился в новый режим - старые генерации недоступны!
   - Это правильно по архитектуре V3!

2. **ЗАГРУЗКА ФОТО:**
   - Разрешена ТОЛЬКО в состояниях `*_upload_photo`
   - Во всех остальных состояниях загрузка фото должна быть проигнорирована или обработана fallback'ом

3. **БАЛАНС:**
   - Проверять ДО, а не ПОСЛЕ генерации
   - Уменьшать сразу при нажатии на стиль / генерацию (не после результата!)

4. **РЕЖИМЫ:**
   - Хранить в FSM `current_mode` - это ОБЯЗАТЕЛЬНО!
   - Логировать `"MODE+SCREEN"` - это ОБЯЗАТЕЛЬНО для отладки!

5. **SINGLE MENU PATTERN:**
   - `menu_message_id` должен сохраняться при переключении режимов!
   - Сброс режима = `.clear()`, но с восстановлением `menu_message_id` потом!

---

## 🎯 РЕЗУЛЬТАТ ИНТЕГРАЦИИ

**После полной реализации плана:**

✅ 5 независимых режимов работы  
✅ 18 новых экранов  
✅ 28 новых FSM состояний  
✅ 18 новых функций клавиатур  
✅ Системы логирования (MODE+SCREEN)  
✅ Текстовое редактирование для всех режимов  
✅ Сохранение Single Menu Pattern  
✅ Полная обратная совместимость с V1 компонентами (профиль, оплата, админ-панель)  

---

**Документ подготовлен:** 2025-12-28  
**Версия:** V3.0 INTEGRATION PLAN  
**Статус:** ✅ ГОТОВ К ИСПОЛНЕНИЮ  
**Контакт для уточнений:** Документация в `/docs`
