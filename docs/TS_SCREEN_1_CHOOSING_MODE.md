# 📋 ТЗ РЕАЛИЗАЦИИ ЭКРАНА 1 - CHOOSING_MODE

**Дата создания:** 2025-12-28  
**Версия:** 1.0  
**Статус:** 🎯 ДЕТАЛЬНОЕ ТЗ  
**Приоритет:** 🔴 КРИТИЧЕСКИЙ (первый экран - точка входа)

---

## 📌 ТЕКУЩЕЕ СОСТОЯНИЕ (V1)

### Существующий экран MAIN_MENU:
```
Адрес: bot/handlers/user_start.py::cmd_start()
ВЫЗЫВАЕТ: show_main_menu() из bot/utils/navigation.py
Текст: START_TEXT из bot/utils/texts.py
Клавиатура: get_main_menu_keyboard() из bot/keyboards/inline.py

Клавиши:
├─ 🎨 Создать дизайн → callback: create_design
├─ 👤 Личный кабинет → callback: show_profile
└─ ⚙️ Админ-панель → callback: admin_panel (только для админов)

Функция show_main_menu():
├─ Получает callback: CallbackQuery
├─ Сохраняет menu_message_id в FSM
├─ Редактирует существующее меню (Single Menu Pattern)
└─ Вызывает edit_menu() для обновления
```

### Существующий обработчик cmd_start():
```python
@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username)
    
    # Устанавливает menu_message_id
    callback = message  # Преобразование Message в CallbackQuery-like
    await show_main_menu(callback, state, admins=[...])
```

---

## 🎯 ТРЕБУЕМЫЕ ИЗМЕНЕНИЯ (V3)

### НОВЫЙ экран CHOOSING_MODE (ЭКРАН 1):
```
Текст: MAIN_MENU_CHOOSE_MODE из texts.py
       "Выберите режим работы"

Клавиши (7 кнопок в 1 колонку):
├─ Ряд 1: 🎨 Создать новый дизайн → callback: mode_new_design
├─ Ряд 2: ✏️ Редактировать дизайн → callback: mode_edit_design
├─ Ряд 3: 👁️ Примерить дизайн → callback: mode_sample_design
├─ Ряд 4: 🛋️ Расставить мебель → callback: mode_arrange_furniture
├─ Ряд 5: 🏠 Создать дизайн фасада → callback: mode_facade_design
├─ Ряд 6: 👤 Личный кабинет → callback: show_profile
└─ Ряд 7: ⚙️ Админ-панель → callback: admin_panel (только для админов)

ФSM State: CreationStates.choosing_mode
Динамический текст:
  MODE: Выбор режима работы
  BALANCE: {user.balance}

Результат выбора:
  mode_new_design → CreationStates.new_design_upload_photo
  mode_edit_design → CreationStates.edit_design_upload_photo
  mode_sample_design → CreationStates.sample_design_upload_photo
  mode_arrange_furniture → CreationStates.furniture_upload_photo
  mode_facade_design → CreationStates.facade_upload_photo
```

---

## 🔧 ПЛАН РЕАЛИЗАЦИИ БЕЗ ДУБЛИРОВАНИЯ

### ШАГИ:

#### ШАГ 1: Обновить FSM (БЕЗ ИЗМЕНЕНИЙ К СУЩЕСТВУЮЩЕМУ)

**Файл:** `bot/states/fsm.py`

**ДЕЙСТВИЕ:** Добавить НОВОЕ состояние в начало CreationStates

```python
class CreationStates(StatesGroup):
    # === НОВОЕ: РЕЖИМНЫЙ ВЫБОР ===
    choosing_mode = State()  # НОВОЕ ДЛЯ ЭКРАНА 1
    
    # === СУЩЕСТВУЮЩИЕ (СОХРАНИТЬ КАК ЕСТЬ) ===
    waiting_for_photo = State()
    what_is_in_photo = State()
    choose_room = State()
    choose_style = State()
    waiting_for_room_description = State()
    waiting_for_exterior_prompt = State()
    # ... остальные существующие
```

**✅ Совместимость:** Полная - старые состояния не трогаем

---

#### ШАГ 2: Обновить текстовые константы (МИНИМАЛЬНОЕ ДОПОЛНЕНИЕ)

**Файл:** `bot/utils/texts.py`

**ДОБАВИТЬ** (в конец файла, перед функциями):

```python
# === V3 НОВЫЕ ТЕКСТЫ ===

# ЭКРАН 1: CHOOSING_MODE
MAIN_MENU_CHOOSE_MODE = """
🎨 Выберите режим работы
"""

# Словарь для get_mode_header()
MODE_TITLES = {
    "NEW_DESIGN": "Создание нового дизайна",
    "EDIT_DESIGN": "Редактирование дизайна",
    "SAMPLE_DESIGN": "Примерка дизайна",
    "ARRANGE_FURNITURE": "Расстановка мебели",
    "FACADE_DESIGN": "Дизайн фасада дома"
}

# Функция для динамического заголовка (ПЕРЕИСПОЛЬЗУЕТСЯ ВО ВСЕХ ЭКРАНАХ)
def get_mode_header(current_mode: str, balance: int) -> str:
    """
    Генерирует заголовок с режимом и балансом.
    ИСПОЛЬЗУЕТСЯ во всех экранах V3.
    
    Args:
        current_mode: Текущий режим (из FSM state data)
        balance: Баланс пользователя
    
    Returns:
        Форматированный заголовок
    
    Пример:
        >>> get_mode_header("NEW_DESIGN", 10)
        "Режим: Создание нового дизайна\n💰 Баланс: 10\n"
    """
    mode_text = MODE_TITLES.get(current_mode, "Неизвестный режим")
    return f"Режим: {mode_text}\n💰 Баланс: {balance}\n"
```

**✅ Совместимость:** 
- Только ДОБАВЛЕНИЯ
- Существующие тексты не изменяются
- Функция может использоваться везде

---

#### ШАГ 3: Создать НОВУЮ клавиатуру (ОТДЕЛЬНАЯ ФУНКЦИЯ)

**Файл:** `bot/keyboards/inline.py`

**ДОБАВИТЬ** в конец файла (новая функция):

```python
# === V3 НОВЫЕ КЛАВИАТУРЫ ===

def get_mode_selection_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для ЭКРАНА 1 - выбор режима работы.
    
    НОВОЕ ДЛЯ V3
    
    Кнопки:
    ├─ Создать новый дизайн (1 в ряд)
    ├─ Редактировать дизайн (1 в ряд)
    ├─ Примерить дизайн (1 в ряд)
    ├─ Расставить мебель (1 в ряд)
    ├─ Создать дизайн фасада (1 в ряд)
    ├─ Личный кабинет (1 в ряд)
    └─ Админ-панель (1 в ряд) - только для админов
    
    Args:
        is_admin: Админ ли пользователь
    
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    # 5 основных режимов (для всех пользователей)
    builder.row(InlineKeyboardButton(
        text="🎨 Создать новый дизайн",
        callback_data="mode_new_design"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Редактировать дизайн",
        callback_data="mode_edit_design"
    ))
    builder.row(InlineKeyboardButton(
        text="👁️ Примерить дизайн",
        callback_data="mode_sample_design"
    ))
    builder.row(InlineKeyboardButton(
        text="🛋️ Расставить мебель",
        callback_data="mode_arrange_furniture"
    ))
    builder.row(InlineKeyboardButton(
        text="🏠 Создать дизайн фасада",
        callback_data="mode_facade_design"
    ))
    
    # Кабинет и админ (как в V1, но отдельно)
    builder.row(InlineKeyboardButton(
        text="👤 Личный кабинет",
        callback_data="show_profile"
    ))
    
    if is_admin:
        builder.row(InlineKeyboardButton(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        ))
    
    # Adjust: 1 кнопка в ряд (вертикально)
    builder.adjust(1)
    
    return builder.as_markup()
```

**✅ Совместимость:** 
- Новая функция, существующие функции не изменяются
- Может использоваться независимо

---

#### ШАГ 4: МОДИФИЦИРОВАТЬ обработчик cmd_start() (МИНИМАЛЬНЫЕ ИЗМЕНЕНИЯ)

**Файл:** `bot/handlers/user_start.py`

**ТЕКУЩИЙ КОД:**
```python
@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username)
    
    await show_main_menu(callback, state, admins=[...])
```

**НОВЫЙ КОД:**
```python
@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot, admins: list = [123456]):
    """Команда /start - показать экран выбора режима (V3)"""
    user = await db.get_user(message.from_user.id)
    
    # 1. Если новый пользователь - добавить в БД
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username)
        user = await db.get_user(message.from_user.id)
    
    # 2. Инициализировать режим (сбросить, чтобы был чистый старт)
    await state.update_data(
        menu_message_id=None,
        current_mode=None,
        photos={},
        latest_generation_id=None
    )
    
    # 3. Установить режимный выбор
    await state.set_state(CreationStates.choosing_mode)
    
    # 4. Логирование
    logger.info(f"USER {message.from_user.id} | /start | Экран выбора режима")
    
    # 5. Показать экран выбора режима
    is_admin = message.from_user.id in admins
    
    # Текст с балансом
    text = f"💰 Баланс: {user.balance}\n\n{MAIN_MENU_CHOOSE_MODE}"
    
    # Вызвать edit_menu (который уже существует и работает!)
    await edit_menu(
        callback=message,  # edit_menu должна поддерживать Message
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(is_admin=is_admin),
        screen_code='choosing_mode'
    )
```

**ИЗМЕНЕНИЯ:**
- ✅ Добавлены инициализация режима и photos
- ✅ Устанавливается state = choosing_mode
- ✅ Добавлено логирование
- ✅ Переиспользуется edit_menu() из navigation.py (СУЩЕСТВУЮЩАЯ!)
- ✅ Переиспользуется get_mode_selection_keyboard() (НОВАЯ, но компактная)

**❌ НЕ изменяются:**
- db.get_user(), db.add_user() - используются как есть
- show_main_menu() - может остаться для других вызовов
- Single Menu Pattern - сохраняется

---

#### ШАГ 5: Добавить импорты в user_start.py

**ТЕКУЩИЕ импорты:**
```python
from aiogram import F, Router, types, Bot
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_profile_keyboard,
    get_payment_keyboard,
    get_upload_photo_keyboard
)
from bot.utils.texts import START_TEXT, MAIN_MENU_TEXT, ...
from bot.utils.navigation import edit_menu, show_main_menu, update_menu_after_photo
from bot.database import db
```

**ДОБАВИТЬ:**
```python
# Из inline.py (новая функция V3)
from bot.keyboards.inline import (
    get_mode_selection_keyboard,  # ← НОВОЕ
    # ... существующие
)

# Из texts.py (новые константы V3)
from bot.utils.texts import (
    MAIN_MENU_CHOOSE_MODE,  # ← НОВОЕ
    MODE_TITLES,            # ← НОВОЕ (словарь)
    get_mode_header,        # ← НОВОЕ (функция)
    # ... существующие
)

# FSM
from bot.states.fsm import CreationStates  # ← добавить choosing_mode

# Логирование
import logging
logger = logging.getLogger(__name__)
```

**✅ Только ДОБАВЛЕНИЯ, никаких удалений**

---

#### ШАГ 6: Обработчик back_to_main_menu() (МИНИМАЛЬНОЕ ИЗМЕНЕНИЕ)

**ТЕКУЩИЙ КОД:**
```python
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list):
    await show_main_menu(callback, state, admins=admins)
```

**НОВЫЙ КОД:**
```python
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list = [123456]):
    """Возврат в главное меню (режимный выбор)"""
    user = await db.get_user(callback.from_user.id)
    
    # Сохранить menu_message_id
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    # Полный сброс режима и данных
    await state.clear()
    
    # Восстановить menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
    
    # Установить режимный выбор
    await state.set_state(CreationStates.choosing_mode)
    
    logger.info(f"USER {callback.from_user.id} | BACK_TO_MAIN_MENU | choosing_mode")
    
    # Показать экран
    is_admin = callback.from_user.id in admins
    text = f"💰 Баланс: {user.balance}\n\n{MAIN_MENU_CHOOSE_MODE}"
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(is_admin=is_admin),
        screen_code='choosing_mode'
    )
```

**ИЗМЕНЕНИЯ:**
- ✅ Полный сброс режима (state.clear())
- ✅ Восстановление menu_message_id
- ✅ Логирование

---

#### ШАГ 7: Обновить navigation.py - адаптировать edit_menu() для Message

**Файл:** `bot/utils/navigation.py`

**ТЕКУЩАЯ СИГНАТУРА:**
```python
async def edit_menu(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown",
    show_balance: bool = True,
    screen_code: str = 'main_menu'
) -> bool:
```

**НОВАЯ СИГНАТУРА:**
```python
from typing import Union
from aiogram.types import CallbackQuery, Message

async def edit_menu(
    callback: Union[CallbackQuery, Message],  # ← ИЗМЕНЕНО: поддерживает оба типа
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown",
    show_balance: bool = True,
    screen_code: str = 'main_menu'
) -> bool:
    """
    Редактирует или создает меню (Single Menu Pattern).
    
    ВЫ МОГУ ВЫЗОВ ИЗ:
    - CallbackQuery (нажата кнопка)
    - Message (команда /start или загрузка фото)
    
    Args:
        callback: CallbackQuery или Message
        state: FSM контекст
        text: Текст сообщения
        keyboard: Inline клавиатура
        parse_mode: Режим парсинга
        show_balance: (ИСТОРИЧЕСКИЙ параметр, можно не использовать)
        screen_code: Код экрана для логирования
    
    Returns:
        True если редактировано существующее, False если создано новое
    """
    
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id if isinstance(callback, CallbackQuery) else callback.chat.id
    
    # Получить menu_message_id из FSM
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    # Если нет в FSM - восстановить из БД
    if not menu_message_id:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info:
            menu_message_id = menu_info['menu_message_id']
            await state.update_data(menu_message_id=menu_message_id)
    
    # Если есть menu_message_id - попробовать отредактировать
    if menu_message_id:
        try:
            if isinstance(callback, CallbackQuery):
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode
                )
                await callback.answer()  # Скрыть "loading"
                return True
            else:  # Message
                # Для Message нельзя редактировать через бота
                # Создаем новое сообщение
                raise Exception("Cannot edit message for Message type")
        
        except Exception as e:
            # Если не смогли отредактировать - создать новое
            pass
    
    # FALLBACK: Создать новое сообщение
    if isinstance(callback, CallbackQuery):
        new_message = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
    else:  # Message
        new_message = await callback.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
    
    # Сохранить новый menu_message_id
    new_menu_message_id = new_message.message_id
    await state.update_data(menu_message_id=new_menu_message_id)
    await db.save_chat_menu(
        chat_id=chat_id,
        user_id=user_id,
        menu_message_id=new_menu_message_id,
        screen_code=screen_code
    )
    
    return False
```

**✅ ПРЕИМУЩЕСТВА:**
- Поддерживает оба типа callback (CallbackQuery и Message)
- Использует существующую логику SMP
- Минимальные изменения существующего кода
- Обратная совместимость (старые вызовы работают как раньше)

---

## 📊 МАТРИЦА ПЕРЕИСПОЛЬЗОВАНИЯ

| Компонент | Статус | Действие |
|-----------|--------|----------|
| **FSM** | ДОБАВЛЕНИЕ | Добавить `choosing_mode` State |
| **texts.py** | ДОПОЛНЕНИЕ | Добавить MAIN_MENU_CHOOSE_MODE, MODE_TITLES, get_mode_header() |
| **inline.py** | НОВОЕ | Добавить get_mode_selection_keyboard() |
| **user_start.py** | МОДИФИКАЦИЯ | Изменить cmd_start(), back_to_main_menu() |
| **navigation.py** | АДАПТАЦИЯ | Обновить edit_menu() для поддержки Message |
| **db.py** | БЕЗ ИЗМЕНЕНИЙ | Переиспользуется как есть |
| **admin.py** | БЕЗ ИЗМЕНЕНИЙ | Переиспользуется как есть |
| **payment.py** | БЕЗ ИЗМЕНЕНИЙ | Переиспользуется как есть |
| **Single Menu Pattern** | СОХРАНЯЕТСЯ | Работает так же |

---

## 🔍 ПРОВЕРКА БЕЗ ДУБЛИРОВАНИЯ

### ПОВТОРНОЕ ИСПОЛЬЗОВАНИЕ:
- ✅ `db.get_user()` - ИСХОДНЫЙ КОД
- ✅ `db.add_user()` - ИСХОДНЫЙ КОД
- ✅ `db.save_chat_menu()` - ИСХОДНЫЙ КОД
- ✅ `db.get_chat_menu()` - ИСХОДНЫЙ КОД
- ✅ `edit_menu()` - АДАПТИРОВАННЫЙ (но логика та же)
- ✅ `Single Menu Pattern` - ПЕРЕИСПОЛЬЗУЕТСЯ
- ✅ `show_main_menu()` - СОХРАНЯЕТСЯ для других вызовов
- ✅ `CreationStates` - РАСШИРЯЕТСЯ (не изменяется)

### НОВОЕ КОД:
- Функция `get_mode_selection_keyboard()` - 50 строк
- Функция `get_mode_header()` - 15 строк
- Константы `MAIN_MENU_CHOOSE_MODE`, `MODE_TITLES` - 10 строк
- Модификация `cmd_start()` - +15 строк
- Модификация `back_to_main_menu()` - +20 строк
- Адаптация `edit_menu()` - +30 строк

**ВСЕГО НОВЫХ СТРОК: ~150 строк (МИНИМАЛЬНО!)**

---

## 🧪 ЧЕК-ЛИСТ РЕАЛИЗАЦИИ

### ФАЗА 1: Подготовка (30 мин)
- [ ] Обновить `bot/states/fsm.py` - добавить `choosing_mode`
- [ ] Обновить `bot/utils/texts.py` - добавить 3 константы и 1 функцию
- [ ] Добавить `get_mode_selection_keyboard()` в `bot/keyboards/inline.py`

### ФАЗА 2: Модификация обработчиков (30 мин)
- [ ] Обновить импорты в `bot/handlers/user_start.py`
- [ ] Изменить `cmd_start()` - добавить инициализацию режима
- [ ] Изменить `back_to_main_menu()` - добавить логику режима
- [ ] Добавить логирование (logger.info)

### ФАЗА 3: Адаптация навигации (30 мин)
- [ ] Обновить сигнатуру `edit_menu()` в `navigation.py`
- [ ] Добавить поддержку Message типа
- [ ] Протестировать fallback логику

### ФАЗА 4: Тестирование (1 час)
- [ ] `/start` показывает экран выбора режима ✓
- [ ] Баланс отображается верно ✓
- [ ] Кнопки режимов активны ✓
- [ ] Админ видит админ-панель ✓
- [ ] Обычный пользователь НЕ видит админ-панель ✓
- [ ] Single Menu Pattern работает ✓
- [ ] Логирование показывает правильные режимы ✓
- [ ] Можно вернуться в режимный выбор командой /start ✓

---

## 💾 ПОРЯДОК КОММИТОВ

### Коммит 1: FSM и тексты
```bash
git add bot/states/fsm.py bot/utils/texts.py
git commit -m "feat(v3): Add choosing_mode state and mode texts"
```

### Коммит 2: Клавиатуры
```bash
git add bot/keyboards/inline.py
git commit -m "feat(v3): Add mode selection keyboard"
```

### Коммит 3: Обработчики
```bash
git add bot/handlers/user_start.py
git commit -m "feat(v3): Update cmd_start and back_to_main_menu for mode selection"
```

### Коммит 4: Навигация
```bash
git add bot/utils/navigation.py
git commit -m "feat(v3): Adapt edit_menu to support Message type"
```

---

## 📝 КОММЕНТАРИЙ К КОДУ

```python
# Пример комментирования в коде

@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot, admins: list = [123456]):
    """Команда /start - показать экран выбора режима (ЭКРАН 1, V3)"""
    # === V1 ЛОГИКА ===
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username)
        user = await db.get_user(message.from_user.id)
    
    # === V3 НОВОЕ: Инициализация режима ===
    # Сбросить старый режим, если был
    await state.update_data(
        menu_message_id=None,
        current_mode=None,  # ← НОВОЕ V3
        photos={},          # ← НОВОЕ V3
        latest_generation_id=None  # ← НОВОЕ V3
    )
    
    # === V3 НОВОЕ: Установить режимный выбор ===
    await state.set_state(CreationStates.choosing_mode)
    
    # === V3 НОВОЕ: Логирование ===
    logger.info(f"USER {message.from_user.id} | /start | CHOOSING_MODE")
    
    # === V3 + V1: Показать экран ===
    is_admin = message.from_user.id in admins
    text = f"💰 Баланс: {user.balance}\n\n{MAIN_MENU_CHOOSE_MODE}"
    
    await edit_menu(
        callback=message,  # ← НОВОЕ: edit_menu теперь поддерживает Message
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(is_admin=is_admin),  # ← НОВОЕ
        screen_code='choosing_mode'  # ← НОВОЕ
    )
```

---

## 🎯 РЕЗУЛЬТАТ РЕАЛИЗАЦИИ

**ПОСЛЕ ВЫПОЛНЕНИЯ ТЗ:**

✅ Пользователь видит экран выбора режима при /start  
✅ 5 режимов выбора + профиль + админ-панель  
✅ Баланс отображается в заголовке  
✅ Логирование показывает режимы  
✅ Single Menu Pattern сохранен  
✅ Нет дублирования кода  
✅ 100% переиспользование существующих компонентов  
✅ Обратная совместимость с V1 (профиль, оплата, админ работают как прежде)  

---

**ТЗ подготовлено:** 2025-12-28  
**Статус:** 🎯 ГОТОВО К РЕАЛИЗАЦИИ  
**Примерное время выполнения:** 2-3 часа  
