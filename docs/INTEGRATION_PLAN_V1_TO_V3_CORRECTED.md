# 🚀 ИСПРАВЛЕННЫЙ ИНТЕГРАЦИОННЫЙ ПЛАН: V1 → V3

**🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ОШИБОК ПЕРВОГО ПЛАНА**

**Дата создания:** 27.12.2025 21:20 +03  
**Статус:** ✅ PRODUCTION READY (ИСПРАВЛЕННЫЙ)  
**Версия:** 2.0 CORRECTED  

---

## ⚠️ НАЙДЕННЫЕ ОШИБКИ В ПЕРВОМ ПЛАНЕ

### ОШИБКА #1: ЭКРАН ГЕНЕРАЦИИ НЕ УЧТЁН ❌

**ЧТО БЫЛО в первом плане:**
- POST_GENERATION напрямую после выбора стиля

**ЧТО ДОЛЖНО БЫТЬ по SCREENS_MAP_V3.md:**
- Между CHOOSE_STYLE и POST_GENERATION должны быть **ЭКРАНЫ ГЕНЕРАЦИИ**!
- Каждый режим имеет свой экран генерации с текстом "Примерьте / Расставьте / Генерирую..."

**НОВЫЕ ЭКРАНЫ ГЕНЕРАЦИИ (которые я пропустил):**
1. 🔄 **GENERATION OF DESIGN TRY-ON** (для SAMPLE_DESIGN) - ЭКРАН 11
2. 🔄 **Generating a room design with furniture** (для ARRANGE_FURNITURE) - ЭКРАН 14
3. 🔄 **Generating FACADE DESIGN** (для FACADE_DESIGN) - ЭКРАН 17

**Эти экраны показывают:**
- Текст "Примерьте дизайн..."
- Кнопку ДЕЙСТВИЯ ("Примерить дизайн", "Расставить мебель", "Примерить фасад")
- Кнопку "Назад" и "Главное меню"

---

### ОШИБКА #2: РЕЖИМ ДОЛЖЕН ОТОБРАЖАТЬСЯ В КАЖДОМ СООБЩЕНИИ ❌

**ЧТО БЫЛО в первом плане:**
- Просто записывали режим в state.data

**ЧТО ДОЛЖНО БЫТЬ по SCREENS_MAP_V3.md:**
```
Текстовое поле КАЖДОГО сообщения должно содержать:

✨ РЕЖИМ РАБОТЫ (BOLD + ЁМОДЗИ)
├─ Баланс пользователя
└─ Описание текущего действия
```

**ПРИМЕР:**
```
🎨 **РЕЖИМ: НОВЫЙ ДИЗАЙН**
💳 Баланс: 5 генераций

Выберите стиль дизайна...
```

```
📏 **РЕЖИМ: РЕДАКТИРОВАНИЕ**
💳 Баланс: 5 генераций

Выберите задачу для редактирования фото.
```

---

### ОШИБКА #3: FSM СОСТОЯНИЯ НЕ СООТВЕТСТВУЮТ ЭКРАНАМ ❌

**ЧТО БЫЛО в первом плане:**
- `mode_new_design`, `mode_edit_design` и т.д.

**ЧТО ДОЛЖНО БЫТЬ по SCREENS_MAP_V3.md:**

Вариант А: **Режим хранится в `state.data['current_mode']`, но FSM следует экранам:**

```python
class CreationStates(StatesGroup):
    # ВСЕ РЕЖИМЫ начинаются с этой же структуры:
    waiting_for_photo = State()              # ЭКРАН 2 (для всех режимов)
    
    # Потом РАСХОДЯТСЯ по режимам:
    
    # NEW DESIGN режим:
    choose_room = State()                    # ЭКРАН 3
    choose_style = State()                   # ЭКРАН 4-5
    # (POST_GENERATION в state=None)
    
    # EDIT DESIGN режим:
    edit_design = State()                    # ЭКРАН 8
    clear_confirm = State()                  # ЭКРАН 9
    # (POST_GENERATION в state=None)
    
    # SAMPLE DESIGN режим:
    download_sample = State()                # ЭКРАН 10
    generation_of_design_try_on = State()   # ЭКРАН 11 (НОВОЕ!)
    # (POST_GENERATION_SAMPLE в state=None)
    
    # ARRANGE_FURNITURE режим:
    uploading_photos_of_furniture = State() # ЭКРАН 13
    generating_furniture = State()           # ЭКРАН 14 (НОВОЕ!)
    # (POST_GENERATION_FURNITURE в state=None)
    
    # FACADE_DESIGN режим:
    loading_house_facade_sample = State()   # ЭКРАН 16
    generating_facade = State()              # ЭКРАН 17 (НОВОЕ!)
    # (POST_GENERATION_FACADE_DESIGN в state=None)
    
    # ДЛЯ ВСЕХ РЕЖИМОВ:
    text_input = State()                     # ЭКРАН 7 (TEXT_INPUT)
```

---

### ОШИБКА #4: TEXT_INPUT ЭКРАН ЗАБЫТ ❌

**ЧТО БЫЛО в первом плане:**
- Один unified `waiting_for_text_input`

**ЧТО ДОЛЖНО БЫТЬ:**
- **ЭКРАН 7: TEXT_INPUT** - вводим текстовый промпт
- Используется из разных мест:
  - Post-generation (кнопка "Текстовое редактирование")
  - Кнопка ← Назад зависит от откуда пришли!

**ВАЖНО:** На редактирование поступает **только последние картинки в режиме**!

---

### ОШИБКА #5: ЛОГИРОВАНИЕ НЕ СПЕЦИФИЦИРОВАНО ❌

**ЧТО БЫЛО в первом плане:**
- Просто `[MODE: X]`

**ЧТО ДОЛЖНО БЫТЬ по SCREENS_MAP_V3.md:**
```
ЛОГИРОВАНИЕ ФОРМАТ:
[MODE: <MODE_NAME>+<CURRENT_SCREEN>]

Примеры:
[MODE: NEW_DESIGN+UPLOADING_PHOTO]
[MODE: NEW_DESIGN+CHOOSE_STYLE_1]
[MODE: EDIT_DESIGN+EDIT_DESIGN]
[MODE: SAMPLE_DESIGN+GENERATION_OF_DESIGN_TRY_ON]
[MODE: ARRANGE_FURNITURE+GENERATING_FURNITURE]
[MODE: FACADE_DESIGN+GENERATING_FACADE]
```

Это нужно для **простого тестирования и поиска багов**!

---

## 📊 ИСПРАВЛЕННАЯ КАРТА ЭКРАНОВ (18 ЭКРАНОВ)

```
МОДА РАБОТЫ: current_mode ∈ {'NEW_DESIGN', 'EDIT_DESIGN', 'SAMPLE_DESIGN', 
                              'ARRANGE_FURNITURE', 'FACADE_DESIGN'}

┌─────────────────────────────────────────────────────────────┐
│ ЭКРАН 1: MAIN MENU (выбор режима)                          │
│ FSM: None                                                   │
│ Кнопки: 5 режимов + профиль + админ                       │
│ Действие: Выбор режима сохраняется в state.data            │
└─────────────────────────────────────────────────────────────┘

         ↓ Выбор режима (5 параллельных потоков)

┌─────────────────────────────────────────────────────────────┐
│ ЭКРАН 2: UPLOADING PHOTO (для всех режимов)               │
│ FSM: waiting_for_photo                                      │
│ Логирование: [MODE: <MODE>+UPLOADING_PHOTO]               │
│ Текст: Динамически в зависимости от режима                │
│ Действие: Загрузка фото → next_screen_by_mode             │
└─────────────────────────────────────────────────────────────┘

         ↓ Фото загружено → state.data['photo_id'] = ...

    ┌────────────────────────────────────────────────────────┐
    │           РЕЖИМ ВЫБОР ПО ТИПУ                         │
    └────────────────────────────────────────────────────────┘

    ↓ NEW_DESIGN              ↓ EDIT_DESIGN              ↓ SAMPLE_DESIGN
    │                         │                         │
    │                         │                         │
┌───────────────┐        ┌──────────────┐         ┌──────────────────┐
│ЭКРАН 3:       │        │ЭКРАН 8:      │         │ЭКРАН 10:         │
│ROOM_CHOICE    │        │EDIT_DESIGN   │         │DOWNLOAD_SAMPLE   │
│FSM:choose_room│        │FSM:edit_design│        │FSM:download_sample│
│→выбор комнаты │        │→задача       │         │→загрузка образца  │
└───────┬───────┘        └────────┬─────┘         └────────┬──────────┘
        │                        │                        │
        ↓                        ↓                        ↓
┌───────────────┐        ┌──────────────┐         ┌──────────────────┐
│ЭКРАН 4-5:     │        │ЭКРАН 9:      │         │ЭКРАН 11:         │
│CHOOSE_STYLE   │        │CLEAR_CONFIRM │         │GENERATION OF ... │
│FSM:choose_style│       │FSM:clear_conf│         │FSM:generation..  │
│→выбор стиля   │        │→подтверждение│        │→примеря дизайна   │
│(запуск генер.)│        │              │         │                  │
└───────┬───────┘        └───────┬──────┘         └────────┬──────────┘
        │                        │                        │
        ↓                        ↓                        ↓
    ГЕНЕРАЦИЯ                ГЕНЕРАЦИЯ              ГЕНЕРАЦИЯ ПРИМЕРКИ
        │                        │                        │
        ↓                        ↓                        ↓
┌───────────────┐        ┌──────────────┐         ┌──────────────────┐
│ЭКРАН 6:       │        │После очистки: │         │ЭКРАН 12:         │
│POST_GENERATION│        │→EDIT_DESIGN   │         │POST_GENERATION_S │
│FSM: None      │        │(итеративно)   │         │FSM: None         │
│→результат     │        │              │         │→результат примерки│
└───────┬───────┘        │ ИЛИ           │         └────────┬──────────┘
        │                │→POST_GENERATION│                │
        ↓                │  (экран 6)    │                ↓
                         └──────────────┘         ТЕКСТ РЕДАКТИРОВАНИЕ
    ТЕКСТ                                          (ЭКРАН 7)
    РЕДАКТИРОВАНИЕ
    (ЭКРАН 7)


    ↓ ARRANGE_FURNITURE       ↓ FACADE_DESIGN
    │                         │
    │                         │
┌──────────────────┐     ┌──────────────────┐
│ЭКРАН 13:         │     │ЭКРАН 16:         │
│UPLOADING_PHOTOS  │     │LOADING_FACADE_S  │
│FSM:uploading_furn│     │FSM:loading_facade│
│→загрузка мебели  │     │→загрузка образца │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ↓                        ↓
┌──────────────────┐     ┌──────────────────┐
│ЭКРАН 14:         │     │ЭКРАН 17:         │
│GENERATING_FURNIT │     │GENERATING_FACADE │
│FSM:generating_fur│     │FSM:generating_fac│
│→расставляем     │      │→примеря фасад   │
│мебель           │      │                  │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ↓                        ↓
    ГЕНЕРАЦИЯ               ГЕНЕРАЦИЯ ФАСАДА
         │                        │
         ↓                        ↓
┌──────────────────┐     ┌──────────────────┐
│ЭКРАН 15:         │     │ЭКРАН 18:         │
│POST_GENERATION_F │     │POST_GENERATION_F │
│FSM: None        │     │FSM: None         │
│→результат       │     │→результат фасада│
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         └────────┬───────────────┘
                  │
                  ↓
            ТЕКСТ РЕДАКТИРОВАНИЕ
            (ЭКРАН 7)


┌──────────────────────────────────────────────────────────┐
│ ЭКРАН 7: TEXT_INPUT (для всех режимов)                 │
│ FSM: text_input                                         │
│ Кнопки: Назад (зависит от откуда), Главное меню       │
│ Действие: Редактирование последней картинки             │
└──────────────────────────────────────────────────────────┘
```

---

## 📋 ИСПРАВЛЕННАЯ FSM АРХИТЕКТУРА

### CreationStates (ИСПРАВЛЕННЫЙ ВАРИАНТ)

```python
class CreationStates(StatesGroup):
    """V3 FSM с 7 экранами генерации"""
    
    # ОБЩЕЕ для всех режимов:
    waiting_for_photo = State()              # ЭКРАН 2
    text_input = State()                     # ЭКРАН 7
    
    # NEW_DESIGN режим (ЭКРАНЫ 3-6):
    choose_room = State()                    # ЭКРАН 3
    choose_style = State()                   # ЭКРАН 4-5
    
    # EDIT_DESIGN режим (ЭКРАНЫ 8-9):
    edit_design = State()                    # ЭКРАН 8
    clear_confirm = State()                  # ЭКРАН 9
    
    # SAMPLE_DESIGN режим (ЭКРАНЫ 10-12):
    download_sample = State()                # ЭКРАН 10
    generation_of_design_try_on = State()   # ЭКРАН 11 ✨ НОВОЕ!
    
    # ARRANGE_FURNITURE режим (ЭКРАНЫ 13-15):
    uploading_photos_of_furniture = State() # ЭКРАН 13
    generating_furniture = State()           # ЭКРАН 14 ✨ НОВОЕ!
    
    # FACADE_DESIGN режим (ЭКРАНЫ 16-18):
    loading_house_facade_sample = State()   # ЭКРАН 16
    generating_facade = State()              # ЭКРАН 17 ✨ НОВОЕ!

# ЛОГИРОВАНИЕ ФОРМАТ:
# [MODE: NEW_DESIGN+UPLOADING_PHOTO]
# [MODE: NEW_DESIGN+CHOOSE_STYLE_1]
# [MODE: SAMPLE_DESIGN+GENERATION_OF_DESIGN_TRY_ON]
# [MODE: ARRANGE_FURNITURE+GENERATING_FURNITURE]
# [MODE: FACADE_DESIGN+GENERATING_FACADE]
```

### state.data СТРУКТУРА

```python
# После /start
state.data = {
    'menu_message_id': 12345,
    'user_id': user_id
}

# После выбора режима (ЭКРАН 1)
state.data = {
    'menu_message_id': 12345,
    'current_mode': 'NEW_DESIGN'  # ✨ ВАЖНО!
}

# После загрузки фото (ЭКРАН 2)
state.data = {
    'menu_message_id': 12345,
    'current_mode': 'NEW_DESIGN',
    'photo_id': 'AgAC...'
}

# Остальные режимно-специфичные поля добавляются по необходимости
```

---

## 🎨 ИСПРАВЛЕННЫЕ ЭКРАНЫ С РЕЖИМОМ

### ЭКРАН 1: MAIN MENU

```
┌──────────────────────────────────────┐
│ 🎨 ГЛАВНОЕ МЕНЮ                      │
│                                      │
│ Выберите режим работы:               │
│ [Создать новый дизайн]               │
│ [Редактировать дизайн]               │
│ [Примерить дизайн]                   │
│ [Расставить мебель]                  │
│ [Дизайн фасада дома]                 │
│ [👤 Профиль] [⚙️ Админ-панель]       │
└──────────────────────────────────────┘
```

### ЭКРАН 2: UPLOADING PHOTO (NEW_DESIGN)

```
┌────────────────────────────────────────────────┐
│ 🎨 **РЕЖИМ: НОВЫЙ ДИЗАЙН**                     │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Загрузите фото помещения для создания          │
│ нового дизайна                                 │
│                                                │
│ [🏠 Главное меню]                              │
│                                                │
│ LOG: [MODE: NEW_DESIGN+UPLOADING_PHOTO]        │
└────────────────────────────────────────────────┘
```

### ЭКРАН 3: ROOM_CHOICE

```
┌────────────────────────────────────────────────┐
│ 🎨 **РЕЖИМ: НОВЫЙ ДИЗАЙН** → Выбор комнаты    │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Выберите тип комнаты:                          │
│ [💪 Гостиная] [🝴 Кухня]                        │
│ [🛏 Спальня] [👶 Детская]                       │
│ ...                                            │
│ [Новое фото] [🏠 Главное меню]                 │
│                                                │
│ LOG: [MODE: NEW_DESIGN+CHOOSE_ROOM]            │
└────────────────────────────────────────────────┘
```

### ЭКРАН 4-5: CHOOSE_STYLE

```
┌────────────────────────────────────────────────┐
│ 🎨 **РЕЖИМ: НОВЫЙ ДИЗАЙН** → Выбор стиля      │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Выберите стиль. Генерация начнется сразу!     │
│ [Современный] [Минимализм]                     │
│ [Скандинавский] [Индустриальный]               │
│ ...                                            │
│ [⬅️ Комната] [🏠 Главное меню] [▶️ Ещё]         │
│                                                │
│ LOG: [MODE: NEW_DESIGN+CHOOSE_STYLE_1]         │
└────────────────────────────────────────────────┘
```

### ЭКРАН 8: EDIT_DESIGN

```
┌────────────────────────────────────────────────┐
│ 📏 **РЕЖИМ: РЕДАКТИРОВАНИЕ**                   │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Выберите задачу для редактирования:            │
│ [🗹️ Очистить] [📏 Текстовое редактирование]   │
│ [⬅️ Новое фото] [🏠 Главное меню]              │
│                                                │
│ LOG: [MODE: EDIT_DESIGN+EDIT_DESIGN]           │
└────────────────────────────────────────────────┘
```

### ЭКРАН 11: GENERATION OF DESIGN TRY-ON ✨

```
┌────────────────────────────────────────────────┐
│ 📏 **РЕЖИМ: ПРИМЕРКА ДИЗАЙНА**                │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Примерьте дизайн на ваше помещение             │
│                                                │
│ [🎨 Примерить дизайн] (ГЛАВНАЯ КНОПКА)        │
│ [⬅️ Назад] [🏠 Главное меню]                    │
│                                                │
│ LOG: [MODE: SAMPLE_DESIGN+GENERATION_OF_DE..]  │
└────────────────────────────────────────────────┘
```

### ЭКРАН 14: GENERATING FURNITURE ✨

```
┌────────────────────────────────────────────────┐
│ 🛋️ **РЕЖИМ: РАССТАНОВКА МЕБЕЛИ**              │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Расставьте мебель в комнате                    │
│                                                │
│ [🎨 Расставить мебель] (ГЛАВНАЯ КНОПКА)       │
│ [⬅️ Назад] [🏠 Главное меню]                    │
│                                                │
│ LOG: [MODE: ARRANGE_FURNITURE+GENERATING_F..]  │
└────────────────────────────────────────────────┘
```

### ЭКРАН 17: GENERATING FACADE ✨

```
┌────────────────────────────────────────────────┐
│ 🏠 **РЕЖИМ: ДИЗАЙН ФАСАДА**                    │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Примерьте фасад дома                           │
│                                                │
│ [🎨 Примерить фасад] (ГЛАВНАЯ КНОПКА)         │
│ [⬅️ Назад] [🏠 Главное меню]                    │
│                                                │
│ LOG: [MODE: FACADE_DESIGN+GENERATING_FACADE]   │
└────────────────────────────────────────────────┘
```

### ЭКРАН 7: TEXT_INPUT (для всех режимов)

```
┌────────────────────────────────────────────────┐
│ ✍️ **РЕЖИМ: <ТЕКСТОВОЕ РЕДАКТИРОВАНИЕ>**      │
│ 💳 Баланс: 5 генераций                         │
│                                                │
│ Дайте задание AI:                              │
│ [Текстовый ввод] ← пользователь пишет         │
│                                                │
│ [⬅️ Назад] [🏠 Главное меню]                    │
│                                                │
│ LOG: [MODE: NEW_DESIGN+TEXT_INPUT]             │
└────────────────────────────────────────────────┘
```

---

## 🔧 КОД: ФУНКЦИЯ ПОКАЗА ЭКРАНА С РЕЖИМОМ

```python
async def show_screen_with_mode(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard,
    screen_code: str
):
    """Показать экран с режимом в заголовке"""
    data = await state.get_data()
    current_mode = data.get('current_mode', 'НЕИЗВЕСТНЫЙ')
    user = await db.get_user(callback.from_user.id)
    
    # Формируем заголовок с режимом и балансом
    mode_emoji = {
        'NEW_DESIGN': '🎨',
        'EDIT_DESIGN': '📏',
        'SAMPLE_DESIGN': '📏',
        'ARRANGE_FURNITURE': '🛋️',
        'FACADE_DESIGN': '🏠'
    }.get(current_mode, '✨')
    
    mode_name = {
        'NEW_DESIGN': 'НОВЫЙ ДИЗАЙН',
        'EDIT_DESIGN': 'РЕДАКТИРОВАНИЕ',
        'SAMPLE_DESIGN': 'ПРИМЕРКА ДИЗАЙНА',
        'ARRANGE_FURNITURE': 'РАССТАНОВКА МЕБЕЛИ',
        'FACADE_DESIGN': 'ДИЗАЙН ФАСАДА'
    }.get(current_mode, 'РЕЖИМ')
    
    # Формируем финальный текст
    final_text = f"""{mode_emoji} **РЕЖИМ: {mode_name}**
💳 Баланс: {user.balance} генераций

{text}"""
    
    # Логирование с режимом и экраном
    logger.info(f"[MODE: {current_mode}+{screen_code}] User {callback.from_user.id}")
    
    # Используем edit_menu
    await edit_menu(
        callback=callback,
        state=state,
        text=final_text,
        keyboard=keyboard,
        screen_code=f'{current_mode}+{screen_code}'
    )
```

---

## 🎯 ИСПРАВЛЕННЫЕ СПРИНТЫ (7 спринтов, 20-24 дня)

### 🔴 СПРИНТ 1: FSM + ГЛАВНОЕ МЕНЮ (3-4 дня)

**Задачи:**
1. ✅ Добавить `current_mode` в FSM.data
2. ✅ Создать ЭКРАН 1 (MAIN_MENU) с 5 кнопками режимов
3. ✅ Реализовать функцию `show_screen_with_mode()` показа режима
4. ✅ Логирование с форматом `[MODE: <MODE>+<SCREEN>]`

**Вывод:** Главное меню с режимами и показом режима на каждом экране готово

---

### 🟢 СПРИНТ 2: NEW_DESIGN + ЭКРАН ВЫБОРА КОМНАТЫ (3-4 дня)

**Задачи:**
1. ✅ ЭКРАН 2: UPLOADING_PHOTO (динамический текст по режиму)
2. ✅ ЭКРАН 3: ROOM_CHOICE (unified функция)
3. ✅ ЭКРАН 4-5: CHOOSE_STYLE (без изменений, запускает генерацию)
4. ✅ POST_GENERATION (ЭКРАН 6): сохраняется

**Логирование:**
```
[MODE: NEW_DESIGN+UPLOADING_PHOTO]
[MODE: NEW_DESIGN+CHOOSE_ROOM]
[MODE: NEW_DESIGN+CHOOSE_STYLE_1]
[MODE: NEW_DESIGN+CHOOSE_STYLE_2]
```

**Вывод:** NEW_DESIGN режим полностью функционален

---

### 🟠 СПРИНТ 3: EDIT_DESIGN (3-4 дня)

**Задачи:**
1. ✅ ЭКРАН 8: EDIT_DESIGN (выбор задачи)
2. ✅ ЭКРАН 9: CLEAR_CONFIRM (подтверждение очистки)
3. ✅ Реализовать `clear_space_in_photo()` API метод
4. ✅ TEXT_INPUT используется из POST_GENERATION

**Логирование:**
```
[MODE: EDIT_DESIGN+UPLOADING_PHOTO]
[MODE: EDIT_DESIGN+EDIT_DESIGN]
[MODE: EDIT_DESIGN+CLEAR_CONFIRM]
[MODE: EDIT_DESIGN+TEXT_INPUT]
```

**Вывод:** EDIT_DESIGN режим готов

---

### 🟡 СПРИНТ 4: SAMPLE_DESIGN + ЭКРАН ГЕНЕРАЦИИ (2-3 дня)

**Задачи:**
1. ✅ ЭКРАН 10: DOWNLOAD_SAMPLE (загрузка образца)
2. ✅ **ЭКРАН 11: GENERATION_OF_DESIGN_TRY_ON (НОВОЕ!) - экран генерации с кнопкой**
3. ✅ Реализовать `try_on_design()` API метод
4. ✅ ЭКРАН 12: POST_GENERATION_SAMPLE

**Логирование:**
```
[MODE: SAMPLE_DESIGN+UPLOADING_PHOTO]
[MODE: SAMPLE_DESIGN+DOWNLOAD_SAMPLE]
[MODE: SAMPLE_DESIGN+GENERATION_OF_DESIGN_TRY_ON]  ← НОВОЕ!
[MODE: SAMPLE_DESIGN+TEXT_INPUT]
```

**Вывод:** SAMPLE_DESIGN с экраном генерации готов

---

### 🟣 СПРИНТ 5: ARRANGE_FURNITURE + ЭКРАН ГЕНЕРАЦИИ (2-3 дня)

**Задачи:**
1. ✅ ЭКРАН 13: UPLOADING_PHOTOS_OF_FURNITURE
2. ✅ **ЭКРАН 14: GENERATING_FURNITURE (НОВОЕ!) - экран генерации с кнопкой**
3. ✅ Реализовать `arrange_furniture()` API метод
4. ✅ ЭКРАН 15: POST_GENERATION_FURNITURE

**Логирование:**
```
[MODE: ARRANGE_FURNITURE+UPLOADING_PHOTO]
[MODE: ARRANGE_FURNITURE+UPLOADING_PHOTOS_OF_FURNITURE]
[MODE: ARRANGE_FURNITURE+GENERATING_FURNITURE]  ← НОВОЕ!
[MODE: ARRANGE_FURNITURE+TEXT_INPUT]
```

**Вывод:** ARRANGE_FURNITURE с экраном генерации готов

---

### 🔵 СПРИНТ 6: FACADE_DESIGN + ЭКРАН ГЕНЕРАЦИИ (2-3 дня)

**Задачи:**
1. ✅ ЭКРАН 16: LOADING_HOUSE_FACADE_SAMPLE
2. ✅ **ЭКРАН 17: GENERATING_FACADE (НОВОЕ!) - экран генерации с кнопкой**
3. ✅ Реализовать `generate_facade()` API метод
4. ✅ ЭКРАН 18: POST_GENERATION_FACADE_DESIGN

**Логирование:**
```
[MODE: FACADE_DESIGN+UPLOADING_PHOTO]
[MODE: FACADE_DESIGN+LOADING_HOUSE_FACADE_SAMPLE]
[MODE: FACADE_DESIGN+GENERATING_FACADE]  ← НОВОЕ!
[MODE: FACADE_DESIGN+TEXT_INPUT]
```

**Вывод:** FACADE_DESIGN с экраном генерации готов

---

### ✅ СПРИНТ 7: ЭКРАН TEXT_INPUT + ИНТЕГРАЦИЯ (2-3 дня)

**Задачи:**
1. ✅ ЭКРАН 7: TEXT_INPUT (unified для всех режимов)
2. ✅ Кнопка "Назад" зависит от режима и откуда пришли
3. ✅ Реализовать `edit_design_with_text()` для всех режимов
4. ✅ Финальное тестирование всех 18 экранов
5. ✅ Проверка нулевой регрессии
6. ✅ Обновление документации

**Логирование:**
```
[MODE: NEW_DESIGN+TEXT_INPUT]
[MODE: EDIT_DESIGN+TEXT_INPUT]
[MODE: SAMPLE_DESIGN+TEXT_INPUT]
[MODE: ARRANGE_FURNITURE+TEXT_INPUT]
[MODE: FACADE_DESIGN+TEXT_INPUT]
```

**Вывод:** Все 18 экранов работают, нулевая регрессия

---

## ✨ КЛЮЧЕВЫЕ ОТЛИЧИЯ ИСПРАВЛЕННОГО ПЛАНА

### ЧТО ДОБАВЛЕНО:
1. ✨ **3 экрана генерации** (ЭКРАНЫ 11, 14, 17)
2. ✨ **Показ режима в КАЖДОМ сообщении** с балансом
3. ✨ **Логирование с форматом `[MODE: <NAME>+<SCREEN>]`**
4. ✨ **Unified ЭКРАН 7 (TEXT_INPUT) для всех режимов**
5. ✨ **Четкое разделение FSM по режимам и экранам**

### ЧТО ИСПРАВЛЕНО:
1. 🔧 Первый план пропустил экраны генерации
2. 🔧 Режим теперь видно везде (не только в памяти)
3. 🔧 Логирование теперь информативно (режим + экран)
4. 🔧 FSM состояния четко соответствуют экранам
5. 🔧 TEXT_INPUT обработан правильно

---

## 📚 ДОКУМЕНТАЦИЯ ДЛЯ ОБНОВЛЕНИЯ

1. **SCREENS_MAP_V3.md** ← Уже точный (7 ошибок исправлены в плане)
2. **FSM_GUIDE.md** → Добавить 3 новых состояния
3. **DEVELOPMENT_RULES.md** → Добавить правила логирования с режимом
4. **API_REFERENCE.md** → Добавить новые экраны и хендлеры

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

- [ ] 3 экрана генерации реализованы (11, 14, 17)
- [ ] Режим показывается в КАЖДОМ сообщении
- [ ] Логирование: `[MODE: <MODE>+<SCREEN>]` везде
- [ ] Все 18 экранов работают
- [ ] TEXT_INPUT unified для всех режимов
- [ ] Нулевая регрессия функциональности V1
- [ ] Документация обновлена
- [ ] E2E тестирование всех режимов

---

**Статус:** ✅ READY FOR DEVELOPMENT (ИСПРАВЛЕННЫЙ)  
**Дата:** 27.12.2025 21:20 +03  
**Версия:** 2.0 CORRECTED