# 🚀 ИНТЕГРАЦИОННЫЙ ПЛАН: V1 → V3 (SCREENS_MAP ОБНОВЛЕНИЕ)

**Дата создания:** 27.12.2025 20:59 +03  
**Автор:** PROJECT OWNER (AI Assistant)  
**Версия:** 1.0 PRODUCTION READY  
**Статус:** ✅ ГОТОВ К ВНЕДРЕНИЮ

---

## 📌 ЦЕЛЬ И ЗАДАЧА

**Цель:** Безболезненная интеграция новой архитектуры экранов (V3) в существующий проект (V1) с максимальным переиспользованием текущего кода и без потери функциональности.

**Основная новая фишка V3:** 5 независимых режимов работы (NEW_DESIGN, EDIT_DESIGN, SAMPLE_DESIGN, ARRANGE_FURNITURE, FACADE_DESIGN), каждый со своим flow-ом, но с переиспользованием базовых компонентов.

---

## 🔍 АНАЛИЗ ДУБЛИРОВАНИЙ И ПЕРЕИСПОЛЬЗОВАНИЯ

### ✅ КОМПОНЕНТЫ, КОТОРЫЕ ПЕРЕИСПОЛЬЗУЕМ (без дублирования)

| Компонент | V1 | V3 | Переиспользование | Комментарий |
|-----------|----|----|-------------------|-------------|
| `edit_menu()` | navigation.py | navigation.py | ✅ 100% | Никаких изменений |
| `show_main_menu()` | user_start.py | user_start.py | ✅ 100% | Логика остаётся |
| `CHOOSE_STYLE` экран | Есть | Есть | ✅ 100% | Используется везде |
| `POST_GENERATION` логика | Есть | Есть | ✅ 90% | Создаём 4 варианта на основе одной |
| `photo_handler()` логика | creation.py | creation.py | ✅ 80% | Добавляем проверку режима |
| `get_style_keyboard()` | inline.py | inline.py | ✅ 100% | Без изменений |
| Все админ-функции | admin.py | admin.py | ✅ 100% | Без изменений |
| Все профиль-функции | user_start.py | user_start.py | ✅ 100% | Без изменений |
| Все платежи | payment.py | payment.py | ✅ 100% | Без изменений |

### ❌ ДУБЛИРОВАНИЯ ДЛЯ УДАЛЕНИЯ

#### Проблема 1: ROOM_CHOICE vs WHAT_IS_IN_PHOTO

```python
# V1: Две идентичные функции
def get_room_keyboard():
    # 10 кнопок комнат

def get_what_is_in_photo_keyboard():
    # Те же 10 кнопок комнат!
```

**Решение:** Создать единую функцию `get_room_choice_keyboard(include_exterior=False)`

#### Проблема 2: Обработчики photo в разных состояниях

```python
# V1: Множество хендлеров для фото в разных состояниях
@router.message(state=CreationStates.waiting_for_photo)
@router.message(state=CreationStates.waiting_for_exterior_prompt)  # Нет! Это текст
@router.message(state=CreationStates.waiting_for_room_description)  # Нет! Это текст

# V3 добавляет ещё 3:
@router.message(state=CreationStates.waiting_for_furniture_photos)  # Новое
@router.message(state=CreationStates.loading_facade_sample)  # Новое
```

**Решение:** Единый unified `photo_upload_handler()` с логикой выбора на основе `mode` из state.data

#### Проблема 3: Динамические тексты

```python
# V1: Один текст
UPLOAD_PHOTO_TEXT = "Загрузите фото..."

# V3: Один текст должен меняться в зависимости от режима
UPLOAD_PHOTO_TEXT(mode) = {
    'NEW_DESIGN': "Загрузите фото помещения для создания нового дизайна",
    'EDIT_DESIGN': "Загрузите фото помещения для редактирования",
    'SAMPLE_DESIGN': "Загрузите фото помещения для примерки",
    'ARRANGE_FURNITURE': "Загрузите фото помещения для расстановки мебели",
    'FACADE_DESIGN': "Загрузите фото фасада дома"
}
```

**Решение:** Функция-помощник `get_upload_photo_text(mode)` вместо константы

---

## 📊 ПОЛНЫЙ СПЕКТР ИЗМЕНЕНИЙ ПО ФАЙЛАМ

### 1️⃣ **bot/states/fsm.py** — РАСШИРЕНИЕ FSM

**ДЕЙСТВИЕ:** Добавить 11 новых состояний, сохранить все старые

```python
class CreationStates(StatesGroup):
    # СТАРЫЕ (ОСТАВЛЯЕМ):
    waiting_for_photo = State()                    # ✅ Переиспользуется
    choose_room = State()                          # ✅ Переиспользуется
    choose_style = State()                         # ✅ Переиспользуется
    what_is_in_photo = State()                     # ⚠️ Может быть удалено
    waiting_for_room_description = State()         # ✅ Переиспользуется
    waiting_for_exterior_prompt = State()          # ⚠️ Переименовать
    
    # НОВЫЕ (ДОБАВЛЯЕМ):
    choosing_mode = State()                        # 🆕 Выбор режима
    mode_new_design = State()                      # 🆕 Режим: новый дизайн
    mode_edit_design = State()                     # 🆕 Режим: редактирование
    mode_sample_design = State()                   # 🆕 Режим: примерка
    mode_arrange_furniture = State()               # 🆕 Режим: мебель
    mode_facade_design = State()                   # 🆕 Режим: фасад
    edit_design = State()                          # 🆕 Экран редактирования
    clear_confirm = State()                        # 🆕 Подтверждение очистки
    loading_facade_sample = State()                # 🆕 Загрузка образца фасада
    waiting_for_furniture_photos = State()         # 🆕 Загрузка мебели
    waiting_for_text_input = State()               # 🆕 Текстовый ввод (все режимы)
```

**Комментарии в коде:**

```python
# 📌 РЕЖИМНЫЕ СОСТОЯНИЯ (хранят текущий режим, влияют на поведение):
# - choosing_mode: пользователь выбирает режим в главном меню
# - mode_new_design: режим создания нового дизайна (как V1)
# - mode_edit_design: режим редактирования (новое)
# - mode_sample_design: режим примерки дизайна (новое)
# - mode_arrange_furniture: режим расстановки мебели (новое)
# - mode_facade_design: режим фасада дома (расширение V1)

# 📌 РЕЖИМ СОХРАНЯЕТСЯ В state.data:
# await state.update_data(current_mode='NEW_DESIGN')
# Это позволяет обработчикам знать, в каком режиме находится пользователь
```

---

### 2️⃣ **bot/handlers/user_start.py** — ГЛАВНОЕ МЕНЮ С РЕЖИМАМИ

**ДЕЙСТВИЕ:** Переделать главное меню на выбор режимов

```python
# НОВАЯ ФУНКЦИЯ: Главное меню с выбором режимов
@router.callback_query(F.data == "show_main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Главное меню с выбором режимов (НОВОЕ в V3)"""
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    # Показываем текущий режим (если он был выбран ранее)
    current_mode = (await state.get_data()).get('current_mode', 'не выбран')
    
    text = f"""
    🎨 **ГЛАВНОЕ МЕНЮ**
    Выберите режим работы:
    
    **Текущий режим:** {current_mode}
    **Баланс:** {user.balance} генераций
    """
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(is_admin=user_id in admins),
        screen_code='main_menu'
    )

# НОВЫЕ ФУНКЦИИ: Обработчики выбора режимов
@router.callback_query(F.data == "mode_new_design")
async def start_new_design(callback: CallbackQuery, state: FSMContext):
    """Режим: Создать новый дизайн (как V1)"""
    await state.update_data(current_mode='NEW_DESIGN')
    await state.set_state(CreationStates.waiting_for_photo)
    await edit_menu(
        callback=callback,
        state=state,
        text=get_upload_photo_text('NEW_DESIGN'),
        keyboard=get_upload_photo_keyboard(),
        screen_code='upload_photo_new_design'
    )

@router.callback_query(F.data == "mode_edit_design")
async def start_edit_design(callback: CallbackQuery, state: FSMContext):
    """Режим: Редактировать дизайн (НОВОЕ)"""
    await state.update_data(current_mode='EDIT_DESIGN')
    await state.set_state(CreationStates.waiting_for_photo)
    await edit_menu(
        callback=callback,
        state=state,
        text=get_upload_photo_text('EDIT_DESIGN'),
        keyboard=get_upload_photo_keyboard(),
        screen_code='upload_photo_edit_design'
    )

# ... аналогично для остальных 4 режимов ...
```

---

### 3️⃣ **bot/handlers/creation.py** — РАСШИРЕНИЕ ЛОГИКИ ГЕНЕРАЦИИ

**ДЕЙСТВИЕ:** Добавить обработчики для новых режимов, переделать существующие

```python
# МОДИФИЦИРОВАННЫЙ ОБРАБОТЧИК: photo_handler с логикой режимов
@router.message(F.photo, StateFilter(CreationStates.waiting_for_photo))
async def photo_handler(message: Message, state: FSMContext):
    """Обработка загруженного фото (работает для всех 5 режимов)"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    current_mode = data.get('current_mode')
    
    # Проверка баланса
    user = await db.get_user(user_id)
    if user.balance <= 0 and user_id not in admins:
        await message.delete()
        await edit_menu(..., text=NO_BALANCE_TEXT, screen_code='no_balance')
        return
    
    # Сохраняем фото
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    # Логирование с режимом
    logger.info(f"📸 [MODE: {current_mode}] User {user_id} uploaded photo")
    
    # Переход на следующий экран в зависимости от режима
    if current_mode == 'NEW_DESIGN':
        await state.set_state(CreationStates.choose_room)
        next_text = "Выберите тип комнаты"
        next_keyboard = get_room_choice_keyboard()
    
    elif current_mode == 'EDIT_DESIGN':
        await state.set_state(CreationStates.edit_design)
        next_text = "Что вы хотите сделать?"
        next_keyboard = get_edit_design_keyboard()
    
    elif current_mode == 'SAMPLE_DESIGN':
        await state.set_state(CreationStates.loading_facade_sample)  # Переиспользуем
        next_text = "Загрузите фото образца дизайна"
        next_keyboard = get_upload_sample_keyboard()
    
    elif current_mode == 'ARRANGE_FURNITURE':
        await state.set_state(CreationStates.waiting_for_furniture_photos)
        next_text = "Загрузите фото мебели"
        next_keyboard = get_upload_furniture_keyboard()
    
    elif current_mode == 'FACADE_DESIGN':
        await state.set_state(CreationStates.loading_facade_sample)
        next_text = "Загрузите фото образца фасада"
        next_keyboard = get_upload_facade_sample_keyboard()
    
    # Редактируем меню
    await message.delete()
    menu_info = await db.get_chat_menu(chat_id)
    if menu_info and menu_info.get('menu_message_id'):
        await message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_info['menu_message_id'],
            text=next_text,
            reply_markup=next_keyboard,
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], f'{current_mode}_next_step')

# НОВАЯ ФУНКЦИЯ: Обработка режима EDIT_DESIGN
@router.callback_query(F.data == "clear_space", state=CreationStates.edit_design)
async def clear_space(callback: CallbackQuery, state: FSMContext):
    """Очистить пространство в режиме EDIT_DESIGN"""
    await state.set_state(CreationStates.clear_confirm)
    await edit_menu(
        callback=callback,
        state=state,
        text="Вы уверены, что хотите очистить пространство?",
        keyboard=get_clear_confirm_keyboard(),
        screen_code='clear_confirm'
    )

@router.callback_query(F.data == "confirm_clear", state=CreationStates.clear_confirm)
async def confirm_clear(callback: CallbackQuery, state: FSMContext):
    """Выполнить очистку"""
    user_id = callback.from_user.id
    data = await state.get_data()
    photo_id = data.get('photo_id')
    
    # API вызов для очистки
    result_image_url = await kie_api.clear_space_in_photo(photo_id)
    
    # Показать результат
    await callback.message.edit_caption(
        caption="✅ Пространство очищено!",
        reply_markup=get_post_generation_keyboard(show_continue_editing=True)
    )
    
    await state.set_state(None)
    logger.info(f"🧹 [EDIT_DESIGN] Cleared space for {user_id}")

# НОВАЯ ФУНКЦИЯ: Текстовое редактирование (для EDIT_DESIGN и других режимов)
@router.message(StateFilter(CreationStates.waiting_for_text_input))
async def text_input_handler(message: Message, state: FSMContext):
    """Обработка текстового промпта для редактирования"""
    user_id = message.from_user.id
    data = await state.get_data()
    current_mode = data.get('current_mode')
    photo_id = data.get('photo_id')
    text_prompt = message.text
    
    # Проверка баланса
    user = await db.get_user(user_id)
    if user.balance <= 0:
        await message.delete()
        await edit_menu(..., text=NO_BALANCE_TEXT)
        return
    
    # Удаляем сообщение пользователя
    await message.delete()
    
    # API вызов
    if current_mode == 'EDIT_DESIGN':
        result_url = await kie_api.edit_design_with_text(photo_id, text_prompt)
    elif current_mode == 'SAMPLE_DESIGN':
        result_url = await kie_api.try_on_design_with_text(photo_id, text_prompt)
    # ... и так далее для других режимов ...
    
    # Показать результат
    await state.set_state(None)
    await edit_menu(
        callback=...,  # Нужна CallbackQuery для edit_menu, или используем другой подход
        text="✅ Результат готов!",
        keyboard=...,
        screen_code='post_generation'
    )
    
    logger.info(f"✍️ [{current_mode}] Applied text prompt for {user_id}")

# ... аналогично для остальных режимов ...
```

---

### 4️⃣ **bot/keyboards/inline.py** — РАСШИРЕНИЕ КЛАВИАТУР

**ДЕЙСТВИЕ:** Добавить новые клавиатуры, удалить дублирования

```python
# НОВАЯ ФУНКЦИЯ: Выбор режима (главное меню V3)
def get_mode_selection_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Выбор режима работы (ГЛАВНОЕ МЕНЮ V3)"""
    builder = InlineKeyboardBuilder()
    
    # Ряд 1: NEW DESIGN
    builder.row(InlineKeyboardButton(text="🎨 Создать новый дизайн", callback_data="mode_new_design"))
    
    # Ряд 2: EDIT DESIGN
    builder.row(InlineKeyboardButton(text="✏️ Редактировать дизайн", callback_data="mode_edit_design"))
    
    # Ряд 3: SAMPLE DESIGN
    builder.row(InlineKeyboardButton(text="📸 Примерить дизайн", callback_data="mode_sample_design"))
    
    # Ряд 4: ARRANGE FURNITURE
    builder.row(InlineKeyboardButton(text="🪑 Расставить мебель", callback_data="mode_arrange_furniture"))
    
    # Ряд 5: FACADE DESIGN
    builder.row(InlineKeyboardButton(text="🏠 Дизайн фасада", callback_data="mode_facade_design"))
    
    # Ряд 6: Profile & Admin
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"),
        InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel") if is_admin else None
    )
    
    builder.adjust(1)
    return builder.as_markup()

# УДАЛИТЬ ДУБЛИРОВАНИЕ: Объединить get_room_keyboard и get_what_is_in_photo_keyboard
def get_room_choice_keyboard(include_exterior: bool = False) -> InlineKeyboardMarkup:
    """Выбор типа комнаты (UNIFIED функция)
    
    include_exterior=False: только комнаты (для NEW_DESIGN)
    include_exterior=True: комнаты + экстерьер (для FACADE_DESIGN)
    """
    builder = InlineKeyboardBuilder()
    
    # Комнаты (всегда показываются)
    builder.row(
        InlineKeyboardButton(text="🛋 Гостиная", callback_data="room_living_room"),
        InlineKeyboardButton(text="🍽 Кухня", callback_data="room_kitchen")
    )
    # ... остальные комнаты ...
    
    # Экстерьер (опционально, для FACADE_DESIGN)
    if include_exterior:
        builder.row(
            InlineKeyboardButton(text="🏠 Дом (фасад)", callback_data="scene_house_exterior"),
            InlineKeyboardButton(text="🌳 Участок", callback_data="scene_plot_exterior")
        )
    
    builder.adjust(2)
    return builder.as_markup()

# НОВАЯ ФУНКЦИЯ: Редактирование дизайна
def get_edit_design_keyboard() -> InlineKeyboardMarkup:
    """Меню редактирования дизайна (EDIT_DESIGN)"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🧹 Очистить пространство", callback_data="clear_space"),
        InlineKeyboardButton(text="✍️ Текстовое редактирование", callback_data="text_edit")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Новое фото", callback_data="mode_edit_design"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="show_main_menu")
    )
    
    builder.adjust(2, 2)
    return builder.as_markup()

# НОВАЯ ФУНКЦИЯ: Подтверждение очистки
def get_clear_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение очистки пространства"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да, очистить", callback_data="confirm_clear"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_clear")
    )
    
    builder.adjust(2)
    return builder.as_markup()

# ... аналогично для SAMPLE_DESIGN, ARRANGE_FURNITURE, FACADE_DESIGN ...

# МОДИФИЦИРОВАТЬ: get_post_generation_keyboard
def get_post_generation_keyboard(show_continue_editing: bool = False, mode: str = None) -> InlineKeyboardMarkup:
    """Post-generation меню (параметризованное для разных режимов)
    
    mode='NEW_DESIGN': Новый стиль, Новая комната, Главное меню
    mode='EDIT_DESIGN': Новое редактирование, Главное меню
    mode='SAMPLE_DESIGN': Новый образец, Текстовое редактирование, Главное меню
    """
    builder = InlineKeyboardBuilder()
    
    if mode == 'NEW_DESIGN':
        builder.row(
            InlineKeyboardButton(text="🎨 Новый стиль", callback_data="change_style"),
            InlineKeyboardButton(text="🛋 Новая комната", callback_data="back_to_room")
        )
        builder.row(InlineKeyboardButton(text="📸 Новое фото", callback_data="mode_new_design"))
    
    elif mode == 'EDIT_DESIGN':
        builder.row(
            InlineKeyboardButton(text="✍️ Ещё редактировать", callback_data="text_edit"),
            InlineKeyboardButton(text="🧹 Очистить заново", callback_data="clear_space")
        )
        builder.row(InlineKeyboardButton(text="📸 Новое фото", callback_data="mode_edit_design"))
    
    # ... и так далее для остальных режимов ...
    
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="show_main_menu"))
    builder.adjust(2, 1, 1)
    return builder.as_markup()
```

---

### 5️⃣ **bot/utils/texts.py** — ДИНАМИЧЕСКИЕ ТЕКСТЫ

**ДЕЙСТВИЕ:** Добавить функции для динамических текстов вместо констант

```python
# НОВАЯ ФУНКЦИЯ: Динамический текст загрузки фото
def get_upload_photo_text(mode: str) -> str:
    """Текст экрана загрузки фото в зависимости от режима"""
    texts = {
        'NEW_DESIGN': "Загрузите фото помещения для создания нового дизайна 🎨",
        'EDIT_DESIGN': "Загрузите фото помещения для редактирования ✏️",
        'SAMPLE_DESIGN': "Загрузите фото помещения для примерки дизайна 📸",
        'ARRANGE_FURNITURE': "Загрузите фото помещения для расстановки мебели 🪑",
        'FACADE_DESIGN': "Загрузите фото фасада дома 🏠"
    }
    return texts.get(mode, "Загрузите фото")

# НОВЫЕ КОНСТАНТЫ
MODE_SELECTION_TEXT = """
🎨 **ВЫБЕРИТЕ РЕЖИМ РАБОТЫ**

Каждый режим позволяет создавать разные типы дизайнов:

🎨 **Создать новый дизайн** - генерация дизайна по стилю
✏️ **Редактировать дизайн** - изменение существующего дизайна текстом
📸 **Примерить дизайн** - примерка дизайна на фото образец
🪑 **Расставить мебель** - визуализация мебели в интерьере
🏠 **Дизайн фасада** - генерация фасада дома с образцом
"""

EDIT_DESIGN_TEXT = """
✏️ **РЕЖИМ РЕДАКТИРОВАНИЯ**

Выберите, что вы хотите сделать:

🧹 **Очистить пространство** - удалить мебель и элементы
✍️ **Текстовое редактирование** - описать изменения текстом
"""

CLEAR_CONFIRM_TEXT = """
⚠️ **ПОДТВЕРЖДЕНИЕ**

Вы уверены, что хотите очистить пространство от мебели и элементов дизайна?
"""

# ... и так далее ...
```

---

### 6️⃣ **bot/services/kie_api.py** — НОВЫЕ API ФУНКЦИИ

**ДЕЙСТВИЕ:** Добавить методы для новых режимов

```python
class KIEApi:
    """KIE AI Integration - все методы для генерации"""
    
    # СУЩЕСТВУЮЩИЕ (оставляем):
    async def generate_design(self, photo_id: str, style: str, room: str) -> str:
        """Генерация дизайна по стилю (V1)"""
        ...
    
    # НОВЫЕ (добавляем):
    async def clear_space_in_photo(self, photo_id: str) -> str:
        """Очистить пространство в фото (EDIT_DESIGN)"""
        # API вызов к KIE
        # Возвращает URL результата
    
    async def edit_design_with_text(self, photo_id: str, prompt: str) -> str:
        """Отредактировать дизайн текстовым промптом (EDIT_DESIGN)"""
        # API вызов
    
    async def try_on_design(self, original_photo: str, sample_photo: str) -> str:
        """Примерить дизайн на фото образец (SAMPLE_DESIGN)"""
        # API вызов
    
    async def arrange_furniture(self, room_photo: str, furniture_photos: list) -> str:
        """Расставить мебель в интерьере (ARRANGE_FURNITURE)"""
        # API вызов
    
    async def generate_facade(self, facade_photo: str, sample_photo: str, style: str = None) -> str:
        """Генерировать фасад дома (FACADE_DESIGN)"""
        # API вызов
```

---

## 📅 СПРИНТЫ РЕАЛИЗАЦИИ

### 🔴 СПРИНТ 1: FSM и главное меню (3-4 дня)

**Цель:** Готова инфраструктура для 5 режимов

**Tasks:**
1. ✅ Добавить 11 новых состояний в `fsm.py`
2. ✅ Создать функцию `show_main_menu()` с 5 кнопками режимов
3. ✅ Создать функцию `get_mode_selection_keyboard()`
4. ✅ Добавить текстовые константы для режимов
5. ✅ Протестировать переходы между режимами

**Вывод:**
- Пользователь видит 5 кнопок режимов в главном меню
- Выбранный режим сохраняется в `state.data['current_mode']`
- Логирование: `[MODE: <name>] User entered mode`

**PR Description:**
```
FEAT: Introduce FSM infrastructure for 5 design modes

- Add 11 new CreationStates for mode selection
- Redesign main menu with 5 mode buttons
- Implement mode selection keyboard
- Add comprehensive logging with mode tracking
- SCREENS_MAP V3: Screen 1 (MAIN MENU) implemented
```

---

### 🟡 СПРИНТ 2: Режим NEW_DESIGN (полная совместимость с V1) (3-4 дня)

**Цель:** V1 функциональность работает как V3 NEW_DESIGN режим

**Tasks:**
1. ✅ Модифицировать `photo_handler()` для режима NEW_DESIGN
2. ✅ Объединить `get_room_keyboard()` и `get_what_is_in_photo_keyboard()`
3. ✅ Убедиться, что CHOOSE_STYLE работает (без изменений)
4. ✅ Убедиться, что POST_GENERATION работает
5. ✅ Полное тестирование: photo → room → style → result

**Чеклист переиспользования:**
- ✅ `photo_handler()` переиспользуется (добавлена логика режима)
- ✅ `choose_room()` переиспользуется
- ✅ `choose_style()` переиспользуется без изменений
- ✅ `style_chosen()` переиспользуется без изменений

**Вывод:**
- NEW_DESIGN режим полностью работает
- Все V1 функциональность сохранена
- Нет дублирующего кода

**PR Description:**
```
FEAT: Implement NEW_DESIGN mode (V1 compatibility layer)

- Refactor photo_handler to support NEW_DESIGN mode
- Unify room selection keyboards (remove duplication)
- Ensure CHOOSE_STYLE works for all modes
- Add mode-specific logging
- SCREENS_MAP V3: Screens 2-6 (upload → style → result) working
```

---

### 🟠 СПРИНТ 3: Режим EDIT_DESIGN (3-4 дня)

**Цель:** Редактирование существующего дизайна

**Tasks:**
1. ✅ Создать экран EDIT_DESIGN с клавиатурой
2. ✅ Создать экран CLEAR_CONFIRM
3. ✅ Реализовать `clear_space_in_photo()` в KIEApi
4. ✅ Реализовать `edit_design_with_text()` в KIEApi
5. ✅ Тестирование: photo → edit screen → action → result

**Новые функции:**
- `process_edit_design()` в creation.py
- `clear_space()` обработчик
- `text_input_handler()` для редактирования
- `get_edit_design_keyboard()`
- `get_clear_confirm_keyboard()`

**Вывод:**
- EDIT_DESIGN режим полностью функционален
- Очистка пространства работает
- Текстовое редактирование работает

**PR Description:**
```
FEAT: Add EDIT_DESIGN mode with space clearing and text editing

- Create EDIT_DESIGN screen and handlers
- Implement clear_space_in_photo API method
- Implement edit_design_with_text API method
- Add text input unified handler
- SCREENS_MAP V3: Screens 8-9 (edit design workflow) implemented
```

---

### 🟡 СПРИНТ 4: Режим SAMPLE_DESIGN (2-3 дня)

**Цель:** Примерка дизайна на образец

**Tasks:**
1. ✅ Создать экран DOWNLOAD_SAMPLE
2. ✅ Создать экран GENERATION_OF_DESIGN_TRY_ON
3. ✅ Создать экран POST_GENERATION_SAMPLE
4. ✅ Реализовать `try_on_design()` в KIEApi
5. ✅ Тестирование: photo → sample photo → try-on → result

**Новые функции:**
- `waiting_for_sample_handler()` для загрузки образца
- `process_sample_generation()` для примерки
- `get_download_sample_keyboard()`
- `get_try_on_generation_keyboard()`

**Вывод:**
- SAMPLE_DESIGN режим работает
- Примерка дизайна на образец возможна

**PR Description:**
```
FEAT: Add SAMPLE_DESIGN mode for design try-on feature

- Create DOWNLOAD_SAMPLE and try-on generation screens
- Implement try_on_design API method
- Add sample photo handlers
- SCREENS_MAP V3: Screens 10-12 (sample design workflow) implemented
```

---

### 🟠 СПРИНТ 5: Режим ARRANGE_FURNITURE (2-3 дня)

**Цель:** Расстановка мебели в интерьере

**Tasks:**
1. ✅ Создать экран UPLOADING_PHOTOS_OF_FURNITURE
2. ✅ Создать экран GENERATING_A_ROOM_DESIGN_WITH_FURNITURE
3. ✅ Создать экран POST_GENERATION_FURNITURE
4. ✅ Реализовать `arrange_furniture()` в KIEApi
5. ✅ Тестирование: room photo → furniture photos → arrangement → result

**Новые функции:**
- `waiting_for_furniture_handler()` для загрузки мебели
- `process_furniture_generation()` для расстановки
- `get_upload_furniture_keyboard()`
- `get_furniture_generation_keyboard()`

**Вывод:**
- ARRANGE_FURNITURE режим работает
- Расстановка мебели возможна

**PR Description:**
```
FEAT: Add ARRANGE_FURNITURE mode for furniture visualization

- Create furniture upload and generation screens
- Implement arrange_furniture API method
- Add furniture photo handlers
- SCREENS_MAP V3: Screens 13-15 (furniture arrangement workflow) implemented
```

---

### 🔴 СПРИНТ 6: Режим FACADE_DESIGN (2-3 дня)

**Цель:** Расширенный режим фасада дома

**Tasks:**
1. ✅ Переделать EXTERIOR_PROMPT в FACADE_DESIGN
2. ✅ Создать экран LOADING_A_HOUSE_FACADE_SAMPLE
3. ✅ Создать экран GENERATING_FACADE_DESIGN
4. ✅ Создать экран POST_GENERATION_FACADE_DESIGN
5. ✅ Реализовать `generate_facade()` в KIEApi
6. ✅ Тестирование: facade photo → sample facade → generation → result

**Migration:**
- Переименовать `waiting_for_exterior_prompt` в `loading_facade_sample`
- Переместить логику из `waiting_for_exterior_prompt_handler()`
- Добавить экран загрузки образца

**Вывод:**
- FACADE_DESIGN режим полностью функционален
- V1 фасад функциональность мигрирована
- Новый экран образца добавлен

**PR Description:**
```
FEAT: Add FACADE_DESIGN mode for house facade generation

- Migrate EXTERIOR_PROMPT to FACADE_DESIGN mode
- Create facade sample upload screen
- Implement generate_facade API method
- Add facade generation handlers
- SCREENS_MAP V3: Screens 16-18 (facade design workflow) implemented
```

---

### ✅ СПРИНТ 7: Интеграция и финализация (2-3 дня)

**Цель:** Полная интеграция, удаление дублирований, документация

**Tasks:**
1. ✅ Убедиться, что нет дублирующего кода
2. ✅ Все переходы используют `edit_menu()`
3. ✅ Полное логирование с режимами на каждом экране
4. ✅ Обновить SCREENS_MAP документацию
5. ✅ Обновить API_REFERENCE документацию
6. ✅ Обновить DEVELOPMENT_RULES
7. ✅ E2E тестирование всех 5 режимов

**Чеклист:**
- [ ] Все 5 режимов работают независимо
- [ ] Нет дублирующих функций (room_keyboard, photo_handler, и т.д.)
- [ ] Логирование полное: `[MODE: X] step=Y`
- [ ] Все экраны V3 отражены в коде
- [ ] Админ-панель работает как раньше
- [ ] Платежи работают как раньше
- [ ] Профиль работает как раньше
- [ ] Реферальная система работает как раньше
- [ ] Тесты проходят
- [ ] Документация актуальна

**Вывод:**
- V1 → V3 интеграция завершена
- Нулевая функциональная регрессия
- Все новые режимы работают идеально
- Код чистый и готов к прodu

**PR Description:**
```
FEAT/REFACTOR: Complete V1→V3 integration and cleanup

- Remove all code duplication (room keyboards, photo handlers)
- Implement comprehensive mode-based logging throughout
- Update all documentation (SCREENS_MAP, API_REFERENCE)
- Complete E2E testing of all 5 design modes
- Verify zero regression in existing features
- SCREENS_MAP V3: All 18 screens fully implemented and tested

BREAKING CHANGES: None (full backward compatibility)
DEPRECATED: None
NEW FEATURES: 5 design modes, text editing, furniture arrangement, sample-based design, facade design
```

---

## 📌 КРИТИЧЕСКИЕ МОМЕНТЫ ПРИ РЕАЛИЗАЦИИ

### 1. Логирование с режимом на КАЖДОМ этапе

```python
# ✅ ПРАВИЛЬНО
logger.info(f"🎨 [MODE: NEW_DESIGN] User {user_id} entered UPLOADING_PHOTO")
logger.info(f"📋 [MODE: NEW_DESIGN] User {user_id} selected room: {room}")
logger.info(f"🎨 [MODE: NEW_DESIGN] User {user_id} selected style: {style}")
logger.info(f"✅ [MODE: NEW_DESIGN] Generated result for {user_id}")

# ❌ НЕПРАВИЛЬНО
logger.info(f"User {user_id} uploaded photo")  # Нет режима!
```

### 2. Сохранение режима в state.data ПЕРЕД входом в waiting_for_photo

```python
# ✅ ПРАВИЛЬНО
@router.callback_query(F.data == "mode_new_design")
async def start_new_design(...):
    await state.update_data(current_mode='NEW_DESIGN')  # ← СНАЧАЛА
    await state.set_state(CreationStates.waiting_for_photo)  # ← ПОТОМ

# ❌ НЕПРАВИЛЬНО
@router.callback_query(F.data == "mode_new_design")
async def start_new_design(...):
    await state.set_state(CreationStates.waiting_for_photo)
    await state.update_data(current_mode='NEW_DESIGN')  # ← СЛИШКОМ ПОЗДНО
```

### 3. Использование `edit_menu()` ВЕЗДЕ, не прямые `callback.message.edit_text()`

```python
# ✅ ПРАВИЛЬНО
await edit_menu(
    callback=callback,
    state=state,
    text="...",
    keyboard=...,
    screen_code=f'{current_mode}_next_step'
)

# ❌ НЕПРАВИЛЬНО
await callback.message.edit_text(text="...", reply_markup=keyboard)
```

### 4. Удаление сообщений пользователя ПЕРЕД редактированием меню

```python
# ✅ ПРАВИЛЬНО (для message handlers)
await message.delete()  # ← СНАЧАЛА
await edit_menu(...)     # ← ПОТОМ

# ❌ НЕПРАВИЛЬНО
await edit_menu(...)
await message.delete()  # ← СЛИШКОМ ПОЗДНО
```

### 5. Проверка баланса ПЕРЕД любой генерацией

```python
# ✅ ПРАВИЛЬНО
user = await db.get_user(user_id)
if user.balance <= 0 and user_id not in ADMINS:
    # Редирект на оплату
    return
# Генерируем

# ❌ НЕПРАВИЛЬНО
# Генерируем без проверки баланса
```

---

## 🧪 ТАБЛИЦА ТЕСТИРОВАНИЯ (ДЛЯ КАЖДОГО СПРИНТА)

```markdown
## Тестирование Спринта X: [РЕЖИМ]

### Сценарий 1: Основной поток (Happy Path)
- [ ] Нажать кнопку режима в главном меню
- [ ] Режим сохранён в state.data
- [ ] Загрузить фото
- [ ] Фото сохранено в state.data
- [ ] Следующий экран соответствует режиму
- [ ] Выполнить действие (выбрать стиль / очистить / и т.д.)
- [ ] API вызов произойдёт
- [ ] Результат показан
- [ ] Вернуться в главное меню
- [ ] Режим очищен (state.set_state(None))

### Сценарий 2: Ошибка баланса
- [ ] Установить balance = 0 в БД
- [ ] Нажать кнопку режима
- [ ] Загрузить фото
- [ ] Показана ошибка NO_BALANCE_TEXT
- [ ] Редирект на оплату

### Сценарий 3: Отмена на разных этапах
- [ ] Отмена на экране загрузки
- [ ] Отмена на экране выбора (комнаты, стиля, и т.д.)
- [ ] Отмена на экране подтверждения
- [ ] Каждый раз возврат в главное меню

### Сценарий 4: Логирование
- [ ] Каждый переход логируется с `[MODE: X]`
- [ ] Логи содержат user_id и текущий экран
- [ ] Логирование помогает найти баги

### Сценарий 5: Единое меню (SMP)
- [ ] Нет спама новых сообщений внизу
- [ ] Существующее меню редактируется
- [ ] Даже после перезапуска бота меню восстанавливается
```

---

## 📚 ДОКУМЕНТЫ ДЛЯ ОБНОВЛЕНИЯ

1. **SCREENS_MAP.md** → Обновить на V3 полностью
2. **FSM_GUIDE.md** → Добавить 5 новых режимов
3. **DEVELOPMENT_RULES.md** → Добавить правила работы с режимами
4. **API_REFERENCE.md** → Добавить новые обработчики и API методы
5. **ARCHITECTURE.md** → Обновить диаграмму потоков

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

- [ ] Все 11 новых FSM состояний добавлены
- [ ] Все 5 режимов реализованы
- [ ] Нет дублирующего кода (удалены дублирования)
- [ ] Логирование полное и информативное
- [ ] Все переходы используют edit_menu()
- [ ] Баланс проверяется везде
- [ ] API методы реализованы
- [ ] Документация обновлена
- [ ] E2E тесты пройдены
- [ ] Нулевая регрессия функциональности V1
- [ ] Все 18 экранов V3 работают

---

**Документ готов к использованию на GitHub**  
**Дата завершения анализа:** 27.12.2025 20:59 +03  
**Статус:** 🟢 READY FOR DEVELOPMENT