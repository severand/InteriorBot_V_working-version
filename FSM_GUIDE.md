# 🔄 FSM_GUIDE - Машина состояний InteriorBot

**Назначение:** Подробное описание FSM (Finite State Machine) для всех сценариев бота.  
**Уровень:** Technical / Flow Design  
**Последнее обновление:** December 24, 2025  

---

## 📋 Содержание

1. [Общее устройство FSM](#общее-устройство-fsm)
2. [Список состояний](#список-состояний)
3. [Диаграммы переходов](#диаграммы-переходов)
4. [Данные FSM (state.data)](#данные-fsm-statedata)
5. [Паттерны использования](#паттерны-использования)
6. [Антипаттерны и ошибки](#антипаттерны-и-ошибки)
7. [Как добавлять новые состояния](#как-добавлять-новые-состояния)
8. [ProModeStates (PHASE 3)](#promodesstates-phase-3)

---

## 🧠 Общее устройство FSM

### Технология

FSM реализована через `aiogram 3.x` и модуль `bot/states/fsm.py`.

```python
from aiogram.fsm.state import StatesGroup, State

class CreationStates(StatesGroup):
    """FSM states for design creation process"""

    # State 1: ожидание фото
    waiting_for_photo = State()

    # State 2: выбор комнаты
    choose_room = State()

    # State 3: выбор стиля (запуск генерации)
    choose_style = State()
```

FSM используется **ТОЛЬКО** для пользовательского flow создания дизайна. Все остальные части бота (профиль, платежи, навигация) работают без FSM-состояний (state=None), опираясь на callback_data и `state.data`.

### Принципы

1. **FSM - только для бизнес-пошагового сценария.**
2. **Минимум состояний, максимум логики внутри хендлеров.**
3. **Никогда не используем FSM для хранения того, что нужно в БД.**
4. **После завершения сценария FSM всегда очищается.**
5. **menu_message_id живёт в `state.data`, но не зависит от FSM.**

---

## 📌 Список состояний

### 1. `CreationStates.waiting_for_photo`

**Где объявлено:** `bot/states/fsm.py`  
**Где используется:** `bot/handlers/creation.py`

**Смысл:**
Пользователь должен отправить фото комнаты.

**Вход в состояние:**
```python
await state.set_state(CreationStates.waiting_for_photo)
```

**Кем устанавливается:**
- `start_creation()` (callback `create_design`)

**Обработчики в этом состоянии:**
```python
@router.message(
    content_types=["photo"],
    state=CreationStates.waiting_for_photo
)
async def photo_uploaded(message: Message, state: FSMContext):
    ...
```

**Что разрешено:**
- `message.photo` — загрузка одного фото.

**Что запрещено / блокируется:**
- Альбомы (media_group)
- Видео, документы, стикеры
- Текстовые сообщения

**Выход из состояния:**
- При успешном фото → `CreationStates.choose_room`
- При нехватке баланса → `state.set_state(None)` + редирект в оплату
- При /start или main_menu → `state.set_state(None)`

---

### 2. `CreationStates.choose_room`

**Смысл:**
Пользователь выбрал фото, теперь выбирает тип комнаты.

**Вход в состояние:**
```python
await state.set_state(CreationStates.choose_room)
```

**Кем устанавливается:**
- `photo_uploaded()` после успешной валидации фото.

**Обработчики:**
```python
@router.callback_query(
    F.data.startswith("room_"),
    state=CreationStates.choose_room
)
async def room_chosen(callback: CallbackQuery, state: FSMContext):
    ...
```

**Допустимые `callback_data`:**
- `room_living_room`
- `room_bedroom`
- `room_kitchen`
- `room_office`

**Выход из состояния:**
- Всегда → `CreationStates.choose_style` после выбора комнаты.
- При main_menu → `state.set_state(None)`.

---

### 3. `CreationStates.choose_style`

**Смысл:**
Пользователь выбрал комнату, теперь выбирает стиль. Выбор стиля **запускает генерацию**.

**Вход в состояние:**
```python
await state.set_state(CreationStates.choose_style)
```

**Кем устанавливается:**
- `room_chosen()` после записи `room` в `state.data`.
- `change_style_after_gen()` когда пользователь хочет новый стиль для того же фото.

**Обработчики:**
```python
@router.callback_query(
    F.data.startswith("style_"),
    state=CreationStates.choose_style
)
async def style_chosen(callback: CallbackQuery, state: FSMContext):
    ...

@router.callback_query(
    F.data == "back_to_room",
    state=CreationStates.choose_style
)
async def back_to_room_selection(callback: CallbackQuery, state: FSMContext):
    ...
```

**Допустимые `callback_data`:**
- `style_modern`
- `style_minimalist`
- `style_scandinavian`
- `style_industrial`
- `style_rustic`
- `style_japandi`
- `style_boho`
- `style_mediterranean`
- `style_midcentury`
- `style_artdeco`
- `back_to_room`

**Выход из состояния:**
- При выборе `style_*` → `state.set_state(None)` после генерации.
- При `back_to_room` → `CreationStates.choose_room`.
- При main_menu → `state.set_state(None)`.

---

## 🔄 Диаграммы переходов

### High-Level State Machine

```text
┌───────────────┐
│  NO STATE     │
│  (idle)       │
└──────┬────────┘
       │ callback: create_design
       ▼
┌─────────────────────────┐
│ waiting_for_photo       │
│ (ожидаем одно фото)    │
└──────┬──────────────────┘
       │ message: photo
       ▼
┌─────────────────────────┐
│ choose_room             │
│ (выбор типа комнаты)   │
└──────┬──────────────────┘
       │ callback: room_*
       ▼
┌─────────────────────────┐
│ choose_style            │
│ (выбор стиля)          │
└──────┬──────────────────┘
       │ callback: style_*
       ▼
┌───────────────┐
│  NO STATE     │
│  (результат)  │
└───────────────┘

Дополнительный переход:

choose_style --callback: back_to_room--> choose_room
NO STATE     --callback: change_style--> choose_style (если photo_id есть в state.data)
```

### Детализированная диаграмма с условиями

```text
STATE: NO STATE
  EVENT: callback("create_design")
    ACTIONS:
      - state.set_state(waiting_for_photo)
      - показать текст "Пришлите фото комнаты"
    NEXT: waiting_for_photo

STATE: waiting_for_photo
  EVENT: message(photo)
    CONDITIONS:
      - НЕ альбом (media_group_id == None или новый)
      - balance > 0 ИЛИ user ∈ ADMIN_IDS
    ACTIONS:
      - сохранить photo_id в state.data
      - state.set_state(choose_room)
      - показать клавиатуру комнат
    NEXT: choose_room

  EVENT: message(photo_album)
    ACTIONS:
      - удалить сообщение
      - показать предупреждение (один раз на media_group_id)
    NEXT: waiting_for_photo

  EVENT: callback("main_menu")
    ACTIONS:
      - state.set_state(None)
      - показать главное меню
    NEXT: NO STATE

STATE: choose_room
  EVENT: callback("room_*")
    CONDITIONS:
      - balance > 0 ИЛИ user ∈ ADMIN_IDS
    ACTIONS:
      - room = callback.data.replace("room_", "")
      - сохранить room в state.data
      - state.set_state(choose_style)
      - показать клавиатуру стилей
    NEXT: choose_style

  EVENT: callback("main_menu")
    ACTIONS:
      - state.set_state(None)
      - главное меню
    NEXT: NO STATE

STATE: choose_style
  EVENT: callback("style_*")
    CONDITIONS:
      - balance > 0 ИЛИ user ∈ ADMIN_IDS
    ACTIONS:
      - style = callback.data.replace("style_", "")
      - достать photo_id, room из state.data
      - при необходимости списать баланс (не для админа)
      - вызвать generate_image()
      - отправить результат
      - показать post-generation меню
      - state.set_state(None)
      - очистить photo_id/room из state.data
    NEXT: NO STATE

  EVENT: callback("back_to_room")
    ACTIONS:
      - state.set_state(choose_room)
      - показать клавиатуру комнат
    NEXT: choose_room

  EVENT: callback("main_menu")
    ACTIONS:
      - state.set_state(None)
      - главное меню
    NEXT: NO STATE

STATE: NO STATE (после генерации)
  EVENT: callback("change_style")
    CONDITIONS:
      - в state.data ещё есть photo_id и room (если не очищены полностью)
    ACTIONS:
      - state.set_state(choose_style)
      - показать клавиатуру стилей
    NEXT: choose_style
```

---

## 🧱 Данные FSM (state.data)

### Ключевые поля

```python
# Всегда должны жить в state.data:
'menu_message_id': int   # ID главного сообщения-меню, редактируем его

# В процессе генерации добавляются:
'photo_id': str          # file_id фото из Telegram
'room': str              # 'living_room', 'bedroom', 'kitchen', 'office'
'media_group_id': str    # защита от альбомов (временное)
```

### Жизненный цикл state.data

```python
# После /start
{
  'menu_message_id': 12345
}

# После загрузки фото (waiting_for_photo → choose_room)
{
  'menu_message_id': 12345,
  'photo_id': 'AgAC...',
  'media_group_id': 'g123'  # если был альбом
}

# После выбора комнаты (choose_room → choose_style)
{
  'menu_message_id': 12345,
  'photo_id': 'AgAC...',
  'room': 'living_room',
  'media_group_id': 'g123'
}

# После генерации (choose_style → None)
{
  'menu_message_id': 12345
}
```

### Правило по очистке

- `await state.set_state(None)` — сбрасывает **только FSM**, но **НЕ очищает** `state.data`.
- `await state.clear()` — очищает **и FSM, и state.data** (опасно для `menu_message_id`).

В проекте **по умолчанию** при навигации между экранами используем `set_state(None)`, а `clear()` — только при полном ресете сессии, если это действительно нужно.

---

## 📐 Паттерны использования

### Паттерн 1: Вход в FSM через кнопки

```python
@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext):
    """Начало FSM сценария"""
    await state.set_state(CreationStates.waiting_for_photo)
    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=...
    )
```

### Паттерн 2: Узконаправленные хендлеры по состояниям

```python
@router.message(F.photo, state=CreationStates.waiting_for_photo)
async def photo_uploaded(...):
    ...

@router.callback_query(F.data.startswith("room_"), state=CreationStates.choose_room)
async def room_chosen(...):
    ...

@router.callback_query(F.data.startswith("style_"), state=CreationStates.choose_style)
async def style_chosen(...):
    ...
```

Такой подход гарантирует, что **код не смешивается** между разными шагами сценария.

### Паттерн 3: Возвраты назад без потери данных

```python
@router.callback_query(F.data == "back_to_room", state=CreationStates.choose_style)
async def back_to_room_selection(callback: CallbackQuery, state: FSMContext):
    """Назад к выбору комнаты, фото остаётся тем же"""
    await state.set_state(CreationStates.choose_room)
    await edit_menu(
        callback=callback,
        state=state,
        text=CHOOSE_ROOM_TEXT,
        keyboard=get_room_keyboard()
    )
```

### Паттерн 4: Использование admin-режима в FSM

```python
user_id = callback.from_user.id

if user_id not in config.ADMIN_IDS:
    balance = await db.get_balance(user_id)
    if balance <= 0:
        # редирект в оплату
        await state.set_state(None)
        ...
    else:
        await db.decrease_balance(user_id)
# админов не трогаем
```

---

## ❌ Антипаттерны и ошибки

### Ошибка 1: Использование `state.clear()` при навигации

```python
# ❌ ПЛОХО
await state.clear()  # Удалит menu_message_id и всё остальное

# ✅ ПРАВИЛЬНО
await state.set_state(None)  # FSM → None, но данные (в т.ч. menu_message_id) живут
```

**Последствия:**
- Потеря `menu_message_id` → бот не может редактировать старое меню и начинает слать новые сообщения в конец чата.

### Ошибка 2: Обработка не того состояния

```python
# ❌ ПЛОХО
@router.message(F.photo)
async def process_photo_anytime(message: Message, state: FSMContext):
    ...

# ✅ ПРАВИЛЬНО
@router.message(F.photo, state=CreationStates.waiting_for_photo)
async def photo_uploaded(message: Message, state: FSMContext):
    ...
```

**Почему плохо:**
- FSM теряет смысл, фото может быть обработано в неподходящий момент.

### Ошибка 3: Забыть очистить FSM после завершения сценария

```python
# ❌ ПЛОХО: FSM останется в состоянии choose_style
async def style_chosen(...):
    ...
    # нет state.set_state(None)

# ✅ ПРАВИЛЬНО
async def style_chosen(...):
    ...
    await state.set_state(None)
```

**Последствия:**
- Следующие callback'и будут пытаться матчиться к хендлерам `state=CreationStates.choose_style`.

### Ошибка 4: Хранить в state.data то, что должно быть в БД

```python
# ❌ ПЛОХО: долгоживущие данные в state.data
await state.update_data(total_payments_count=123)

# ✅ ПРАВИЛЬНО: хранить агрегаты в БД или считать на лету
count = await db.get_payments_count(user_id)
```

---

## ➕ Как добавлять новые состояния

### Шаг 1: Добавить состояние в `fsm.py`

```python
class CreationStates(StatesGroup):
    waiting_for_photo = State()
    choose_room = State()
    choose_style = State()
    confirm_result = State()  # NEW: подтверждение результата
```

### Шаг 2: Добавить переход в нужном месте

```python
# Например, после генерации вместо полного выхода в None
await state.set_state(CreationStates.confirm_result)
await callback.message.answer(
    "Нравится дизайн?", reply_markup=get_confirm_keyboard()
)
```

### Шаг 3: Добавить хендлер для нового состояния

```python
@router.callback_query(F.data.in_({"confirm_ok", "confirm_retry"}), state=CreationStates.confirm_result)
async def confirm_result(callback: CallbackQuery, state: FSMContext):
    if callback.data == "confirm_ok":
        # зафиксировать результат, например, в БД
        await state.set_state(None)
        await edit_menu(...)
    else:
        # вернуть на выбор стиля
        await state.set_state(CreationStates.choose_style)
        await edit_menu(...)
```

### Шаг 4: Обновить документацию

- `FSM_GUIDE.md` — добавить новое состояние и переходы
- `API_REFERENCE.md` — описать новые callback_data и хендлеры

---

## 🎯 ProModeStates (PHASE 3)

**Статус:** ✅ PRODUCTION READY  
**Добавлено:** December 24, 2025  
**Где используется:** `bot/handlers/pro_mode.py`  

### Описание

ProModeStates управляет FSM для системы выбора режима работы (PRO/СТАНДАРТ) и его параметров (соотношение сторон, разрешение). Эта система позволяет пользователю выбрать режим генерации дизайна через меню профиля.

### Состояния

```python
class ProModeStates(StatesGroup):
    """FSM states for PRO mode settings"""
    
    waiting_mode_choice = State()      # Выбор режима (PRO/СТАНДАРТ)
    waiting_pro_params = State()       # Выбор параметров PRO (соотношение)
    waiting_resolution = State()       # Выбор разрешения
```

### Диаграмма переходов

```text
┌──────────────────────────────────────────────────────────────┐
│                   PROFILE (Existing State)                    │
│              User views profile information                   │
│         Button "⚙️ SETTINGS" visible in menu                  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ User clicks "⚙️ SETTINGS"
                        ↓
         ┌──────────────────────────────────┐
         │   waiting_mode_choice            │
         │  Show mode selection keyboard:   │
         │  - PRO 🔧                        │
         │  - СТАНДАРТ 📋                   │
         │  - ❌ Cancel                     │
         └───────────┬─────────────┬────────┘
                     │             │
         ┌───────────┘             └──────────────┐
         │                                        │
         │ User selects              User cancels
         │ "PRO 🔧"                  or "СТАНДАРТ"
         ↓                                        ↓
    ┌────────────────────┐           ┌──────────────────┐
    │ waiting_pro_params │           │ PROFILE (Back)   │
    │ Show keyboard:     │           │                  │
    │ - 16:9             │           │ Mode saved in DB │
    │ - 4:3              │           │ (pro_mode=False) │
    │ - 1:1              │           └──────────────────┘
    │ - 9:16             │
    │ - ❌ Cancel        │
    └────────┬───────────┘
             │
    ┌────────┴────────────┐
    │                     │
    │ User selects    User cancels
    │ aspect ratio    or "❌ Cancel"
    │                     │
    ↓                     ↓
┌──────────────────┐  ┌──────────────┐
│ waiting_resolution│  │ PROFILE      │
│                  │  │ (Back)       │
│ Show keyboard:   │  │              │
│ - 1K             │  │ Mode saved   │
│ - 2K             │  │ in DB        │
│ - 4K             │  │              │
│ - ❌ Cancel      │  └──────────────┘
└────────┬─────────┘
         │
    ┌────┴────────┐
    │             │
    │ User     User
    │ selects  cancels
    │ resolution
    │             │
    ↓             ↓
┌─────────────┐  ┌──────────┐
│ PROFILE     │  │ PROFILE  │
│ (Back)      │  │ (Back)   │
│             │  │          │
│ PRO Mode    │  │ Previous │
│ settings    │  │ settings │
│ saved to DB │  │ restored │
└─────────────┘  └──────────┘
```

### State Transitions

| From State | Trigger | To State | Action |
|-----------|---------|----------|--------|
| profile | ⚙️ SETTINGS button | waiting_mode_choice | Show mode selection keyboard |
| waiting_mode_choice | "PRO 🔧" | waiting_pro_params | Save pro_mode=True, show aspect ratios |
| waiting_mode_choice | "СТАНДАРТ 📋" | profile | Save pro_mode=False, back to profile |
| waiting_mode_choice | ❌ Cancel | profile | Discard changes, back to profile |
| waiting_pro_params | Select ratio (16:9/4:3/1:1/9:16) | waiting_resolution | Save ratio, show resolutions |
| waiting_pro_params | ❌ Cancel | profile | Discard changes, back to profile |
| waiting_resolution | Select resolution (1K/2K/4K) | profile | Save resolution, back to profile |
| waiting_resolution | ❌ Cancel | profile | Discard changes, back to profile |

### Handler Mapping

```python
# В bot/handlers/pro_mode.py

pro_mode_router = Router()

# ENTRY POINT: settings_button (profile.py calls this)
@profile_router.callback_query(F.data == "settings")
async def settings_button(callback: CallbackQuery, state: FSMContext):
    """Show mode selection keyboard"""
    await state.set_state(ProModeStates.waiting_mode_choice)
    await edit_menu(
        callback=callback,
        state=state,
        text="Выберите режим:",
        keyboard=kb_pro_modes()
    )

# MODE SELECTION
@pro_mode_router.callback_query(
    ProModeStates.waiting_mode_choice,
    F.data == "mode_pro"
)
async def select_pro_mode(callback: CallbackQuery, state: FSMContext):
    """User selected PRO mode"""
    await state.set_state(ProModeStates.waiting_pro_params)
    await edit_menu(
        callback=callback,
        state=state,
        text="Выберите соотношение сторон:",
        keyboard=kb_aspect_ratios()
    )

@pro_mode_router.callback_query(
    ProModeStates.waiting_mode_choice,
    F.data == "mode_standard"
)
async def select_standard_mode(callback: CallbackQuery, state: FSMContext):
    """User selected STANDARD mode"""
    user_id = callback.from_user.id
    await db.set_user_pro_mode(user_id, False)
    await state.set_state(None)
    # Back to profile
    await show_profile(callback, state)

# ASPECT RATIO SELECTION
@pro_mode_router.callback_query(
    ProModeStates.waiting_pro_params,
    F.data.in_(["ratio_16_9", "ratio_4_3", "ratio_1_1", "ratio_9_16"])
)
async def select_aspect_ratio(callback: CallbackQuery, state: FSMContext):
    """User selected aspect ratio"""
    user_id = callback.from_user.id
    ratio = callback.data.replace("ratio_", "").replace("_", ":")
    
    await db.set_pro_aspect_ratio(user_id, ratio)
    await state.set_state(ProModeStates.waiting_resolution)
    await edit_menu(
        callback=callback,
        state=state,
        text="Выберите разрешение:",
        keyboard=kb_resolutions()
    )

# RESOLUTION SELECTION
@pro_mode_router.callback_query(
    ProModeStates.waiting_resolution,
    F.data.in_(["res_1k", "res_2k", "res_4k"])
)
async def select_resolution(callback: CallbackQuery, state: FSMContext):
    """User selected resolution"""
    user_id = callback.from_user.id
    resolution = callback.data.replace("res_", "").upper()
    
    await db.set_pro_resolution(user_id, resolution)
    await db.set_user_pro_mode(user_id, True)
    await state.set_state(None)
    
    await edit_menu(
        callback=callback,
        state=state,
        text="✅ PRO режим активирован!",
        keyboard=kb_main_menu()
    )

# CANCEL BUTTONS
@pro_mode_router.callback_query(
    F.data == "cancel",
    (ProModeStates.waiting_pro_params | ProModeStates.waiting_resolution)
)
async def cancel_pro_params(callback: CallbackQuery, state: FSMContext):
    """Cancel PRO params selection"""
    await state.set_state(None)
    await show_profile(callback, state)
```

### Database Interaction

```python
# Functions used from bot/database/db.py:

await db.get_user_pro_settings(user_id)
    # Returns: {'pro_mode': bool, 'pro_aspect_ratio': str, 
    #           'pro_resolution': str, 'pro_mode_changed_at': str}

await db.set_user_pro_mode(user_id, True/False)
    # Sets pro_mode and updates pro_mode_changed_at timestamp

await db.set_pro_aspect_ratio(user_id, '16:9')
    # Sets pro_aspect_ratio field

await db.set_pro_resolution(user_id, '2K')
    # Sets pro_resolution field
```

### Data Flow

```
User Input (callback)
    ↓
Keyboard Callback (F.data)
    ↓
State Handler (ProModeStates.*)
    ↓
DB Function (db.set_*)
    ↓
Database Update (users table)
    ↓
State Transition (→ next State or None)
    ↓
Show next Keyboard or Back to Profile
```

### Validation

```python
# Valid aspect ratios:
VALID_RATIOS = ['16:9', '4:3', '1:1', '9:16']

# Valid resolutions:
VALID_RESOLUTIONS = ['1K', '2K', '4K']

# All values come from keyboard buttons, so validation is safe
# But DB functions include validation checks as defensive measure
```

### Error Handling

```python
# DB functions return bool:
# True = success, False = error

# If DB function fails:
if not await db.set_pro_mode(user_id, True):
    # Log error
    logger.error(f"Failed to set pro_mode for {user_id}")
    # Show error to user
    await callback.answer(
        "❌ Ошибка при сохранении. Попробуйте позже.",
        show_alert=True
    )
    # Don't change FSM state
```

---

## 📚 Связанные документы

- [ARCHITECTURE.md](ARCHITECTURE.md) — общая архитектура и потоки данных
- [API_REFERENCE.md](API_REFERENCE.md) — список всех хендлеров и callback_data
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) — как локально поднимать и дебажить FSM
- [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) — правила использования `state.set_state()` и `state.clear()`
- [PHASE_3_TASKS.md](docs/PRO_MODE/PHASE_3_TASKS.md) — требования PHASE 3

---

**Document Status:** ✅ Complete  
**Last Updated:** December 24, 2025  
**Version:** 3.0 Professional (with ProModeStates)
