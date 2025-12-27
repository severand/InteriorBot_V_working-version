# 📋 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: ВНЕДРЕНИЕ V3 (ПОЛНАЯ ВЕРСИЯ)

**Статус:** 🟢 READY FOR DEVELOPMENT  
**Версия:** 3.0 - FINAL  
**Дата:** 27.12.2025 21:50 +03  
**Автор:** PROJECT OWNER (Система управления проектом)  
**Периодичность обновлений:** Еженедельно (по пятницам)

---

## 📌 ИСХОДНЫЕ ДАННЫЕ

### Основной документ
- 📖 **INTEGRATION_PLAN_V1_TO_V3_CORRECTED.md** v2.1
- Найдено и исправлено: **6 критических ошибок** первого плана
- Ключевое исправление: **3 экрана генерации** (ЭКРАН 11, 14, 17)

### Стек технологий
- **Backend:** Python 3.11+, aiogram 3.x, asyncio
- **BD:** SQLite3 (bot.db)
- **External API:** ImageGenAPI (для генерации изображений)
- **Deployment:** Docker (если требуется)

---

## 🎯 ЦЕЛЬ ВНЕДРЕНИЯ

**Миграция V1 → V3 с нулевой регрессией функциональности**

**Успех:** Все 18 экранов работают, все 5 режимов работают, логирование информативно

**Метрики:**
- ✅ 100% функциональности V1
- ✅ +3 новых экрана генерации
- ✅ Режим видно везде (в каждом сообщении)
- ✅ Нулевые дубликаты кода
- ✅ Простое логирование с режимом + экран

---

## 🏗️ АРХИТЕКТУРНЫЕ РЕШЕНИЯ

### 1️⃣ FSM ИЕРАРХИЯ (7 состояний + главное)

```
FSM ROOT: CreationStates
├─ State 1: waiting_for_photo (ЭКРАН 2 - все режимы)
├─ State 2: text_input (ЭКРАН 7 - все режимы)
│
├─ NEW_DESIGN режим:
│  ├─ choose_room (ЭКРАН 3)
│  └─ choose_style (ЭКРАН 4-5)
│
├─ EDIT_DESIGN режим:
│  ├─ edit_design (ЭКРАН 8)
│  └─ clear_confirm (ЭКРАН 9)
│
├─ SAMPLE_DESIGN режим:
│  ├─ download_sample (ЭКРАН 10)
│  └─ generation_of_design_try_on (ЭКРАН 11) ← НОВОЕ!
│
├─ ARRANGE_FURNITURE режим:
│  ├─ uploading_photos_of_furniture (ЭКРАН 13)
│  └─ generating_furniture (ЭКРАН 14) ← НОВОЕ!
│
└─ FACADE_DESIGN режим:
   ├─ loading_house_facade_sample (ЭКРАН 16)
   └─ generating_facade (ЭКРАН 17) ← НОВОЕ!

state.data ключи:
- menu_message_id (из БД)
- current_mode: 'NEW_DESIGN' | 'EDIT_DESIGN' | 'SAMPLE_DESIGN' | 'ARRANGE_FURNITURE' | 'FACADE_DESIGN'
- photo_id (для каждого режима)
```

### 2️⃣ ФУНКЦИЯ edit_menu() - БЕЗ ДУБЛИКАТОВ

```python
# ИСПОЛЬЗОВАНИЕ:
await edit_menu(
    callback=callback,
    state=state,
    text="Выберите стиль...",  # Просто текст
    keyboard=get_style_keyboard(),
    screen_code='choose_style',  # Логирование автоматически
    current_mode_in_header=True  # По умолчанию включено
)

# РЕЗУЛЬТАТ В ЧАТЕ:
# 🎨 **РЕЖИМ РАБОТЫ: НОВЫЙ ДИЗАЙН**  ← Автоматически добавляется!
# 💳 Баланс: 5 | 📋 СТАНДАРТ  ← Из add_balance_to_text()
#
# Выберите стиль...
#
# LOG: [MODE: NEW_DESIGN+choose_style]
```

### 3️⃣ ТАБЛИЦА СООТВЕТСТВИЯ: РЕЖИМ → ЭКРАН → FSM STATE

| Режим | Экран | FSM State | Действие |
|-------|-------|-----------|----------|
| - | 1 | None | MAIN_MENU: выбор режима |
| Все | 2 | waiting_for_photo | Загрузка фото |
| NEW_DESIGN | 3 | choose_room | Выбор комнаты |
| NEW_DESIGN | 4-5 | choose_style | Выбор стиля + ГЕНЕРАЦИЯ |
| Все | 6/12/15/18 | None | POST_GENERATION |
| Все | 7 | text_input | TEXT_INPUT редактирование |
| EDIT_DESIGN | 8 | edit_design | Выбор задачи |
| EDIT_DESIGN | 9 | clear_confirm | Очистка подтверждение |
| SAMPLE_DESIGN | 10 | download_sample | Загрузка образца |
| SAMPLE_DESIGN | 11 | generation_of_design_try_on | **ГЕНЕРАЦИЯ ПРИМЕРКИ** |
| ARRANGE_FURNITURE | 13 | uploading_photos_of_furniture | Загрузка мебели |
| ARRANGE_FURNITURE | 14 | generating_furniture | **ГЕНЕРАЦИЯ РАССТАНОВКИ** |
| FACADE_DESIGN | 16 | loading_house_facade_sample | Загрузка фасада |
| FACADE_DESIGN | 17 | generating_facade | **ГЕНЕРАЦИЯ ФАСАДА** |

---

## 📊 СПРИНТЫ: 7 СПРИНТОВ = 20-24 дня разработки

### 🔴 СПРИНТ 1: ИНФРАСТРУКТУРА + ГЛАВНОЕ МЕНЮ (3-4 дня)
**Назначение:** Подготовка базы кода, FSM, главное меню с режимами

**Входящие:**
- ✅ Код V1 полностью работает
- ✅ SCREENS_MAP_V3.md есть
- ✅ INTEGRATION_PLAN_V1_TO_V3_CORRECTED.md исправлен

**Задачи:**

#### 1.1 Обновить CreationStates FSM (4 часа)
```python
# bot/states/creation_states.py
class CreationStates(StatesGroup):
    # Общие для всех режимов
    waiting_for_photo = State()  # ЭКРАН 2
    text_input = State()         # ЭКРАН 7
    
    # NEW_DESIGN
    choose_room = State()        # ЭКРАН 3
    choose_style = State()       # ЭКРАН 4-5
    
    # EDIT_DESIGN
    edit_design = State()        # ЭКРАН 8
    clear_confirm = State()      # ЭКРАН 9
    
    # SAMPLE_DESIGN ← НОВОЕ!
    download_sample = State()    # ЭКРАН 10
    generation_of_design_try_on = State()  # ЭКРАН 11
    
    # ARRANGE_FURNITURE ← НОВОЕ!
    uploading_photos_of_furniture = State()  # ЭКРАН 13
    generating_furniture = State()           # ЭКРАН 14
    
    # FACADE_DESIGN ← НОВОЕ!
    loading_house_facade_sample = State()    # ЭКРАН 16
    generating_facade = State()              # ЭКРАН 17
```

**Проверка:** `pytest test_fsm_states.py` - все состояния определены

#### 1.2 Обновить edit_menu() (6 часов)
```python
# bot/utils/navigation.py
async def edit_menu(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard=None,
    show_balance: bool = True,
    screen_code: str = None,
    current_mode_in_header: bool = True  # ← НОВОЕ!
):
    """
    ГЛАВНЫЕ ИЗМЕНЕНИЯ:
    1. Получаем current_mode из state.data
    2. Добавляем режим в header сообщения
    3. Логируем [MODE: <MODE>+<SCREEN>]
    4. Используем СУЩЕСТВУЮЩУЮ add_balance_to_text() для баланса
    
    [2025-12-27] ИСПРАВЛЕНО: Нулевые дубликаты! БЕЗ новых функций!
    """
    # ... implementation
```

**Проверка:** `pytest test_edit_menu.py` - режим добавляется правильно

#### 1.3 Удалить дубликат функции (1 час)
```python
# bot/utils/helpers.py

# ❌ УДАЛИТЬ:
# async def add_balance_and_mode_to_text(...)  ← ДУБЛИРУЕТ add_balance_to_text()

# ✅ ОСТАВИТЬ:
# async def add_balance_to_text(...)  ← Базовая функция, используется везде
```

**Проверка:** `grep -r "add_balance_and_mode_to_text" .` - результат пуст

#### 1.4 Обновить MAIN_MENU (ЭКРАН 1) (4 часа)
```python
# bot/handlers/menu_handlers.py

@router.callback_query(lambda c: c.data == 'open_main_menu')
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    ГЛАВНОЕ МЕНЮ с выбором режима
    
    ФУНКЦИОНАЛЬНОСТЬ:
    1. Кнопка: 🎨 Создать новый дизайн
       - Action: await state.update_data(current_mode='NEW_DESIGN')
       - Переход: ЭКРАН 2 (UPLOADING_PHOTO)
    
    2. Кнопка: 📏 Редактировать дизайн
       - Action: await state.update_data(current_mode='EDIT_DESIGN')
       - Переход: ЭКРАН 2 (UPLOADING_PHOTO)
    
    3. Кнопка: 🎨 Примерить дизайн
       - Action: await state.update_data(current_mode='SAMPLE_DESIGN')
       - Переход: ЭКРАН 2 (UPLOADING_PHOTO)
    
    4. Кнопка: 🛋️ Расставить мебель
       - Action: await state.update_data(current_mode='ARRANGE_FURNITURE')
       - Переход: ЭКРАН 2 (UPLOADING_PHOTO)
    
    5. Кнопка: 🏠 Дизайн фасада
       - Action: await state.update_data(current_mode='FACADE_DESIGN')
       - Переход: ЭКРАН 2 (UPLOADING_PHOTO)
    
    6. Кнопка: 👤 Профиль
    7. Кнопка: ⚙️ Админ-панель (если admin)
    """
    # ... implementation
```

**Проверка:** Нажатие на кнопку режима → current_mode сохраняется

#### 1.5 Логирование (3 часа)
```python
# bot/config/logger.py

logger.info(f"[MODE: {current_mode or 'NONE'}+{screen_code}] User {user_id}")

# Примеры логирования:
# [MODE: NEW_DESIGN+UPLOADING_PHOTO] User 123456
# [MODE: NEW_DESIGN+CHOOSE_ROOM] User 123456
# [MODE: NEW_DESIGN+CHOOSE_STYLE_1] User 123456
# [MODE: EDIT_DESIGN+UPLOADING_PHOTO] User 123456
```

**Проверка:** Логи содержат `[MODE: ...]` в начале каждой записи

**Выходящие:**
- ✅ FSM с 12 состояниями
- ✅ edit_menu() работает с режимом в header
- ✅ Нулевые дубликаты кода
- ✅ MAIN_MENU с 5 режимами
- ✅ Логирование информативно

**Проверка качества:**
```bash
pytest test_sprint1_fsm.py -v
pytest test_sprint1_menu.py -v
pytest test_sprint1_logging.py -v
```

---

### 🟢 СПРИНТ 2: NEW_DESIGN + ВЫБОР КОМНАТЫ (3-4 дня)
**Назначение:** Первый полный режим с выбором комнаты и стиля

**Входящие:**
- ✅ Спринт 1 завершен
- ✅ FSM готов
- ✅ edit_menu() работает

**Задачи:**

#### 2.1 ЭКРАН 2: UPLOADING_PHOTO (dynamic текст) (4 часа)
```python
# bot/handlers/creation.py

@router.message(CreationStates.waiting_for_photo, F.photo)
async def handle_photo_upload(message: Message, state: FSMContext):
    """
    ДИНАМИЧЕСКИЙ ТЕКСТ В ЗАВИСИМОСТИ ОТ РЕЖИМА:
    
    NEW_DESIGN:
    "Загрузите фото помещения для создания нового дизайна"
    
    EDIT_DESIGN:
    "Загрузите фото дизайна для редактирования"
    
    SAMPLE_DESIGN:
    "Загрузите фото помещения для примерки дизайна"
    
    ARRANGE_FURNITURE:
    "Загрузите фото помещения для расстановки мебели"
    
    FACADE_DESIGN:
    "Загрузите фото фасада дома для примерки"
    """
    data = await state.get_data()
    current_mode = data.get('current_mode')
    
    # Логика выбора текста по режиму
    text_by_mode = {
        'NEW_DESIGN': 'Загрузите фото помещения...',
        'EDIT_DESIGN': 'Загрузите фото дизайна...',
        # ...
    }
    
    text = text_by_mode.get(current_mode, 'Загрузите фото')
    
    # Сохраняем photo_id
    await state.update_data(photo_id=message.photo[-1].file_id)
    
    # Переход на следующий экран (зависит от режима)
    await next_screen_by_mode(message, state, current_mode)
```

**Проверка:** Каждый режим показывает правильный текст

#### 2.2 ЭКРАН 3: ROOM_CHOICE (NEW_DESIGN только) (4 часа)
```python
# bot/handlers/new_design_handlers.py

@router.callback_query(lambda c: c.data.startswith('room_'))
async def handle_room_choice(callback: CallbackQuery, state: FSMContext):
    """
    Выбор типа комнаты:
    - Гостиная
    - Кухня
    - Спальня
    - Детская
    - Ванная
    - Балкон
    """
    room_type = callback.data.split('_')[1]
    await state.update_data(room_type=room_type)
    
    # Переход на ЭКРАН 4-5: CHOOSE_STYLE
    await show_style_selection(callback, state)
```

**Проверка:** Выбор комнаты → сохраняется в state → показ стилей

#### 2.3 ЭКРАН 4-5: CHOOSE_STYLE (4 часа)
```python
# bot/handlers/new_design_handlers.py

@router.callback_query(lambda c: c.data.startswith('style_'))
async def handle_style_choice(callback: CallbackQuery, state: FSMContext):
    """
    Выбор стиля → ЗАПУСК ГЕНЕРАЦИИ
    
    Стили:
    - Современный
    - Минимализм
    - Скандинавский
    - Индустриальный
    - Классический
    - Bohemian
    - и т.д.
    
    ПРОЦЕСС:
    1. Пользователь выбирает стиль
    2. Вызывается API: generate_design(photo_id, room_type, style)
    3. Результат сохраняется
    4. Показывается POST_GENERATION (ЭКРАН 6)
    """
    style = callback.data.split('_')[1]
    data = await state.get_data()
    
    # Запуск генерации
    result = await api.generate_design(
        photo_id=data['photo_id'],
        room_type=data['room_type'],
        style=style
    )
    
    # Сохранение результата
    await state.update_data(generation_result=result)
    
    # Переход на POST_GENERATION
    await show_post_generation(callback, state, result)
```

**Проверка:** Выбор стиля → API вызов → результат

#### 2.4 ЭКРАН 6: POST_GENERATION (3 часа)
```python
# bot/handlers/creation.py

# Показывает результат генерации с кнопками:
# [🎨 Промпт] - TEXT_INPUT
# [↺ Переделать] - repeat generation
# [💾 Сохранить] - save to gallery
# [← Назад] - back to style
# [🏠 Главное меню] - main menu
```

**Проверка:** Все кнопки работают правильно

**Выходящие:**
- ✅ NEW_DESIGN режим полностью функционален
- ✅ ЭКРАНЫ 2, 3, 4-5, 6 работают
- ✅ Логирование с режимом + экран
- ✅ Динамический текст по режиму

**Проверка качества:**
```bash
pytest test_sprint2_new_design.py -v
pytest test_sprint2_generation.py -v
```

---

### 🟠 СПРИНТ 3: EDIT_DESIGN (3-4 дня)
**Назначение:** Режим редактирования с очисткой и текстовым редактированием

#### 3.1-3.4 EDIT_DESIGN (ЭКРАНЫ 8-9 + POST_GENERATION) (18 часов)
```
ЭКРАН 2: Загрузка фото
↓
ЭКРАН 8: EDIT_DESIGN - выбор задачи
├─ Кнопка: "🗹️ Очистить" → ЭКРАН 9
└─ Кнопка: "📏 Текстовое редактирование" → ЭКРАН 7
↓
ЭКРАН 9: CLEAR_CONFIRM - подтверждение
├─ Кнопка: "✅ Очистить" → ГЕНЕРАЦИЯ → ЭКРАН 6
└─ Кнопка: "❌ Отмена" → ЭКРАН 8
↓
ЭКРАН 6: POST_GENERATION
↓
ЭКРАН 7: TEXT_INPUT (если нужно редактировать)
```

**Логирование:**
```
[MODE: EDIT_DESIGN+UPLOADING_PHOTO]
[MODE: EDIT_DESIGN+EDIT_DESIGN]
[MODE: EDIT_DESIGN+CLEAR_CONFIRM]
[MODE: EDIT_DESIGN+TEXT_INPUT]
```

**Выходящие:**
- ✅ EDIT_DESIGN режим готов
- ✅ 2 режима (NEW_DESIGN, EDIT_DESIGN) работают полностью

**Проверка качества:**
```bash
pytest test_sprint3_edit_design.py -v
```

---

### 🟡 СПРИНТ 4: SAMPLE_DESIGN + ЭКРАН ГЕНЕРАЦИИ (2-3 дня)
**Назначение:** Третий режим с НОВЫМ экраном генерации примерки

#### 4.1-4.3 SAMPLE_DESIGN (ЭКРАНЫ 10-12) (14 часов)
```
ЭКРАН 2: Загрузка фото
↓
ЭКРАН 10: DOWNLOAD_SAMPLE - загрузка образца дизайна
├─ Ввод: URL образца или загрузка файла
└─ Кнопка: "✅ Загружено"
↓
ЭКРАН 11: GENERATION_OF_DESIGN_TRY_ON ← НОВОЕ СОСТОЯНИЕ!
├─ Текст: "Примерьте дизайн на ваше помещение"
├─ Кнопка: "🎨 Примерить дизайн" ← ГЛАВНАЯ КНОПКА
├─ Процесс: API вызов try_on_design()
└─ Результат: Показать примерку
↓
ЭКРАН 12: POST_GENERATION_SAMPLE
├─ [🎨 Промпт]
├─ [↺ Переделать]
├─ [💾 Сохранить]
├─ [← Назад]
└─ [🏠 Главное меню]
↓
ЭКРАН 7: TEXT_INPUT (если нужно)
```

**КЛЮЧЕВОЕ ОТЛИЧИЕ:** ЭКРАН 11 это отдельное состояние FSM!

```python
# bot/states/creation_states.py
class CreationStates(StatesGroup):
    # ...
    # SAMPLE_DESIGN
    download_sample = State()  # ЭКРАН 10
    generation_of_design_try_on = State()  # ЭКРАН 11 ← НОВОЕ!
```

**Логирование:**
```
[MODE: SAMPLE_DESIGN+UPLOADING_PHOTO]
[MODE: SAMPLE_DESIGN+DOWNLOAD_SAMPLE]
[MODE: SAMPLE_DESIGN+GENERATION_OF_DESIGN_TRY_ON] ← НОВОЕ!
[MODE: SAMPLE_DESIGN+TEXT_INPUT]
```

**Выходящие:**
- ✅ SAMPLE_DESIGN режим готов
- ✅ 3 режима работают
- ✅ ЭКРАН 11 (НОВЫЙ!) работает

**Проверка качества:**
```bash
pytest test_sprint4_sample_design.py -v
pytest test_sprint4_generation_screen_11.py -v
```

---

### 🟣 СПРИНТ 5: ARRANGE_FURNITURE + ЭКРАН ГЕНЕРАЦИИ (2-3 дня)
**Назначение:** Четвертый режим с НОВЫМ экраном расстановки мебели

#### 5.1-5.3 ARRANGE_FURNITURE (ЭКРАНЫ 13-15) (14 часов)
```
ЭКРАН 2: Загрузка фото помещения
↓
ЭКРАН 13: UPLOADING_PHOTOS_OF_FURNITURE - загрузка фото мебели
├─ Ввод: Несколько фото мебели (или с URL)
└─ Кнопка: "✅ Загруженно"
↓
ЭКРАН 14: GENERATING_FURNITURE ← НОВОЕ СОСТОЯНИЕ!
├─ Текст: "Расставьте мебель в комнате"
├─ Кнопка: "🎨 Расставить мебель" ← ГЛАВНАЯ КНОПКА
├─ Процесс: API вызов arrange_furniture()
└─ Результат: Показать расстановку
↓
ЭКРАН 15: POST_GENERATION_FURNITURE
├─ [🎨 Промпт]
├─ [↺ Переделать]
├─ [💾 Сохранить]
├─ [← Назад]
└─ [🏠 Главное меню]
↓
ЭКРАН 7: TEXT_INPUT (если нужно)
```

**КЛЮЧЕВОЕ ОТЛИЧИЕ:** ЭКРАН 14 это отдельное состояние FSM!

```python
# bot/states/creation_states.py
class CreationStates(StatesGroup):
    # ...
    # ARRANGE_FURNITURE
    uploading_photos_of_furniture = State()  # ЭКРАН 13
    generating_furniture = State()  # ЭКРАН 14 ← НОВОЕ!
```

**Логирование:**
```
[MODE: ARRANGE_FURNITURE+UPLOADING_PHOTO]
[MODE: ARRANGE_FURNITURE+UPLOADING_PHOTOS_OF_FURNITURE]
[MODE: ARRANGE_FURNITURE+GENERATING_FURNITURE] ← НОВОЕ!
[MODE: ARRANGE_FURNITURE+TEXT_INPUT]
```

**Выходящие:**
- ✅ ARRANGE_FURNITURE режим готов
- ✅ 4 режима работают
- ✅ ЭКРАН 14 (НОВЫЙ!) работает

**Проверка качества:**
```bash
pytest test_sprint5_arrange_furniture.py -v
pytest test_sprint5_generation_screen_14.py -v
```

---

### 🔵 СПРИНТ 6: FACADE_DESIGN + ЭКРАН ГЕНЕРАЦИИ (2-3 дня)
**Назначение:** Пятый режим с НОВЫМ экраном дизайна фасада

#### 6.1-6.3 FACADE_DESIGN (ЭКРАНЫ 16-18) (14 часов)
```
ЭКРАН 2: Загрузка фото фасада дома
↓
ЭКРАН 16: LOADING_HOUSE_FACADE_SAMPLE - загрузка образца фасада
├─ Ввод: URL образца или загрузка файла
└─ Кнопка: "✅ Загружено"
↓
ЭКРАН 17: GENERATING_FACADE ← НОВОЕ СОСТОЯНИЕ!
├─ Текст: "Примерьте фасад дома"
├─ Кнопка: "🎨 Примерить фасад" ← ГЛАВНАЯ КНОПКА
├─ Процесс: API вызов generate_facade()
└─ Результат: Показать фасад
↓
ЭКРАН 18: POST_GENERATION_FACADE_DESIGN
├─ [🎨 Промпт]
├─ [↺ Переделать]
├─ [💾 Сохранить]
├─ [← Назад]
└─ [🏠 Главное меню]
↓
ЭКРАН 7: TEXT_INPUT (если нужно)
```

**КЛЮЧЕВОЕ ОТЛИЧИЕ:** ЭКРАН 17 это отдельное состояние FSM!

```python
# bot/states/creation_states.py
class CreationStates(StatesGroup):
    # ...
    # FACADE_DESIGN
    loading_house_facade_sample = State()  # ЭКРАН 16
    generating_facade = State()  # ЭКРАН 17 ← НОВОЕ!
```

**Логирование:**
```
[MODE: FACADE_DESIGN+UPLOADING_PHOTO]
[MODE: FACADE_DESIGN+LOADING_HOUSE_FACADE_SAMPLE]
[MODE: FACADE_DESIGN+GENERATING_FACADE] ← НОВОЕ!
[MODE: FACADE_DESIGN+TEXT_INPUT]
```

**Выходящие:**
- ✅ FACADE_DESIGN режим готов
- ✅ ВСЕ 5 режимов работают
- ✅ ЭКРАН 17 (НОВЫЙ!) работает

**Проверка качества:**
```bash
pytest test_sprint6_facade_design.py -v
pytest test_sprint6_generation_screen_17.py -v
```

---

### ✅ СПРИНТ 7: ЭКРАН TEXT_INPUT + ФИНАЛИЗАЦИЯ (3-4 дня)
**Назначение:** Unified TEXT_INPUT для всех режимов, финальное тестирование

#### 7.1 ЭКРАН 7: TEXT_INPUT (Unified) (6 часов)
```
Текущий режим может запросить TEXT_INPUT из разных мест:
- POST_GENERATION (всех режимов): кнопка "🎨 Промпт"
- EDIT_DESIGN: выбор "📏 Текстовое редактирование"

ЭКРАН 7 (Unified):
├─ Текст: "Дайте задание AI:"
├─ Ввод: Текстовый промпт пользователя
├─ Кнопка: "🎨 Применить" → ГЕНЕРАЦИЯ
├─ Кнопка: "← Назад" → Вернуться в зависимости от режима
└─ Кнопка: "🏠 Главное меню" → MAIN_MENU

ВУЗ: Кнопка "Назад" должна вернуть в ПРАВИЛЬНЫЙ экран!
```

```python
# bot/handlers/text_input_handler.py

@router.message(CreationStates.text_input)
async def handle_text_input(message: Message, state: FSMContext):
    """
    Unified TEXT_INPUT для всех режимов
    
    ЛОГИКА НАВИГАЦИИ (ОЧЕНЬ ВАЖНО!):
    1. Получаем текущий режим
    2. Применяем текстовое редактирование
    3. Вернулись на ЭКРАН 6/12/15/18 (POST_GENERATION варианта)
    
    Кнопка "Назад" должна ЗНАТЬ откуда мы пришли!
    Например, если из EDIT_DESIGN → назад в ЭКРАН 8
            если из NEW_DESIGN → назад в ЭКРАН 6
    """
```

**Логирование:**
```
[MODE: NEW_DESIGN+TEXT_INPUT]
[MODE: EDIT_DESIGN+TEXT_INPUT]
[MODE: SAMPLE_DESIGN+TEXT_INPUT]
[MODE: ARRANGE_FURNITURE+TEXT_INPUT]
[MODE: FACADE_DESIGN+TEXT_INPUT]
```

#### 7.2 E2E Тестирование (8 часов)
```bash
# ТЕСТОВЫЙ ПЛАН:

# 1. NEW_DESIGN MODE
pytest test_e2e_new_design_full_flow.py -v
# Логирование: [MODE: NEW_DESIGN+UPLOADING_PHOTO] → 
#              [MODE: NEW_DESIGN+CHOOSE_ROOM] → 
#              [MODE: NEW_DESIGN+CHOOSE_STYLE_1] → 
#              [GENERATION] →
#              [MODE: NEW_DESIGN+TEXT_INPUT] (опционально)

# 2. EDIT_DESIGN MODE
pytest test_e2e_edit_design_full_flow.py -v

# 3. SAMPLE_DESIGN MODE (с новым ЭКРАНОМ 11)
pytest test_e2e_sample_design_full_flow.py -v
# Логирование: [MODE: SAMPLE_DESIGN+UPLOADING_PHOTO] → 
#              [MODE: SAMPLE_DESIGN+DOWNLOAD_SAMPLE] → 
#              [MODE: SAMPLE_DESIGN+GENERATION_OF_DESIGN_TRY_ON] ← НОВОЕ!

# 4. ARRANGE_FURNITURE MODE (с новым ЭКРАНОМ 14)
pytest test_e2e_arrange_furniture_full_flow.py -v
# Логирование: [MODE: ARRANGE_FURNITURE+UPLOADING_PHOTO] → 
#              [MODE: ARRANGE_FURNITURE+UPLOADING_PHOTOS_OF_FURNITURE] → 
#              [MODE: ARRANGE_FURNITURE+GENERATING_FURNITURE] ← НОВОЕ!

# 5. FACADE_DESIGN MODE (с новым ЭКРАНОМ 17)
pytest test_e2e_facade_design_full_flow.py -v
# Логирование: [MODE: FACADE_DESIGN+UPLOADING_PHOTO] → 
#              [MODE: FACADE_DESIGN+LOADING_HOUSE_FACADE_SAMPLE] → 
#              [MODE: FACADE_DESIGN+GENERATING_FACADE] ← НОВОЕ!

# 6. РЕГРЕССИОННОЕ ТЕСТИРОВАНИЕ (V1 функциональность)
pytest test_regression_v1_features.py -v
```

#### 7.3 Документирование (4 часа)
```
Обновить:
1. README.md - описание всех 18 экранов
2. SCREENS_MAP_V3.md - уже правильна (исправлена в плане)
3. FSM_GUIDE.md - добавить 3 новых состояния
4. DEVELOPMENT_RULES.md - логирование с режимом
5. API_REFERENCE.md - новые ЭКРАН 11, 14, 17
```

**Выходящие:**
- ✅ Все 18 экранов работают
- ✅ Все 5 режимов полностью функциональны
- ✅ Логирование информативно: `[MODE: X+SCREEN]`
- ✅ TEXT_INPUT unified для всех режимов
- ✅ Нулевая регрессия V1 функциональности
- ✅ Документация обновлена

**Проверка качества:**
```bash
pytest test_sprint7_text_input.py -v
pytest test_e2e_all_modes.py -v
pytest test_regression_full.py -v
```

---

## 🎯 МЕТРИКИ УСПЕХА

### Функциональность
- ✅ 18 экранов реализовано и работает
- ✅ 5 режимов полностью функциональны
- ✅ 3 новых экрана генерации (11, 14, 17)
- ✅ TEXT_INPUT unified для всех режимов
- ✅ Логирование: `[MODE: X+SCREEN]` везде

### Качество кода
- ✅ Нулевые дубликаты функций
- ✅ Используется ТОЛЬКО базовая `add_balance_to_text()`
- ✅ `edit_menu()` дополнена (не переписана)
- ✅ Все FSM состояния определены (12 состояний)
- ✅ Нулевая регрессия V1 функциональности

### Тестирование
- ✅ Unit тесты: 50+ тестов (каждый спринт)
- ✅ E2E тесты: 5 полных потоков (все режимы)
- ✅ Регрессионные тесты: V1 функциональность
- ✅ Coverage: >85%

### Документация
- ✅ SCREENS_MAP_V3.md обновлена
- ✅ FSM_GUIDE.md обновлен
- ✅ API_REFERENCE.md обновлен
- ✅ Логирование документировано
- ✅ README.md обновлен

---

## 📅 ВРЕМЕННОЙ ГРАФИК

| Спринт | Название | Дни | Даты (примерно) | Статус |
|--------|----------|-----|-----------------|--------|
| 1 | FSM + MAIN_MENU | 3-4 | дн. 1-4 | 🔴 TODO |
| 2 | NEW_DESIGN | 3-4 | дн. 5-8 | 🔴 TODO |
| 3 | EDIT_DESIGN | 3-4 | дн. 9-12 | 🔴 TODO |
| 4 | SAMPLE_DESIGN + ЭКРАН 11 | 2-3 | дн. 13-15 | 🔴 TODO |
| 5 | ARRANGE_FURNITURE + ЭКРАН 14 | 2-3 | дн. 16-18 | 🔴 TODO |
| 6 | FACADE_DESIGN + ЭКРАН 17 | 2-3 | дн. 19-21 | 🔴 TODO |
| 7 | TEXT_INPUT + ФИНАЛИЗАЦИЯ | 3-4 | дн. 22-24 | 🔴 TODO |
| **ИТОГО** | **V3 ГОТОВ** | **20-24** | **~24-30 дней** | 🟢 PLAN |

---

## 🔧 ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Структура файлов (NO CHANGES)
```
bot/
├─ handlers/
│  ├─ creation.py (обновить edit_menu usage)
│  ├─ new_design_handlers.py (НОВЫЕ - для режима)
│  ├─ edit_design_handlers.py (НОВЫЕ - для режима)
│  ├─ sample_design_handlers.py (НОВЫЕ - для режима)
│  ├─ arrange_furniture_handlers.py (НОВЫЕ - для режима)
│  ├─ facade_design_handlers.py (НОВЫЕ - для режима)
│  └─ text_input_handler.py (обновить)
│
├─ states/
│  └─ creation_states.py (обновить - добавить 3 состояния)
│
├─ utils/
│  ├─ navigation.py (обновить edit_menu())
│  └─ helpers.py (УДАЛИТЬ add_balance_and_mode_to_text)
│
└─ config/
   └─ logger.py (логирование с режимом)
```

### API Методы (НОВЫЕ ВЫЗОВЫ)
```python
# Существующие (БЕЗ ИЗМЕНЕНИЙ):
await api.generate_design(photo_id, room_type, style)
await api.clear_space_in_photo(photo_id)
await api.edit_design_with_text(photo_id, text_prompt)

# НОВЫЕ (спринты 4-6):
await api.try_on_design(sample_id, photo_id)  # ЭКРАН 11
await api.arrange_furniture(furniture_ids, photo_id)  # ЭКРАН 14
await api.generate_facade(facade_sample_id, photo_id)  # ЭКРАН 17
```

---

## 🚨 КРИТИЧЕСКИЕ ТОЧКИ

### ⚠️ ТОЧКА 1: Удаление дубликата (Спринт 1)
**Проблема:** `add_balance_and_mode_to_text()` дублирует `add_balance_to_text()`
**Решение:** Удалить полностью, использовать ТОЛЬКО базовую функцию
**Проверка:** `grep -r "add_balance_and_mode_to_text" .` должен вернуть пусто

### ⚠️ ТОЧКА 2: edit_menu() с режимом в header (Спринт 1)
**Проблема:** Нужно добавить режим в HEADER, но не создавать новые функции
**Решение:** Дополнить `edit_menu()` параметром `current_mode_in_header=True`
**Проверка:** Каждое сообщение показывает режим в первой строке

### ⚠️ ТОЧКА 3: Три новых ЭКРАНА ГЕНЕРАЦИИ (Спринты 4-6)
**Проблема:** ЭКРАНЫ 11, 14, 17 это НОВЫЕ FSM СОСТОЯНИЯ
**Решение:** Добавить в CreationStates:
- `generation_of_design_try_on` (ЭКРАН 11)
- `generating_furniture` (ЭКРАН 14)
- `generating_facade` (ЭКРАН 17)
**Проверка:** Логирование показывает эти экраны

### ⚠️ ТОЧКА 4: Динамический текст по режиму (Спринт 2)
**Проблема:** ЭКРАН 2 (UPLOADING_PHOTO) должен иметь разный текст для каждого режима
**Решение:** Dictionary с текстом по режиму
**Проверка:** Каждый режим показывает правильный текст

### ⚠️ ТОЧКА 5: Навигация в TEXT_INPUT (Спринт 7)
**Проблема:** Кнопка "Назад" должна знать откуда мы пришли
**Решение:** Хранить в state.data `text_input_source` (POST_GENERATION или EDIT_DESIGN)
**Проверка:** Кнопка "Назад" возвращает в правильный экран

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

**Перед началом разработки:**
- [ ] Все разработчики прочитали это ТЗ
- [ ] GitHub Issues созданы для каждого спринта
- [ ] Тестовые данные подготовлены
- [ ] Staging environment готов

**Спринт 1:**
- [ ] FSM с 12 состояниями создана
- [ ] edit_menu() дополнена параметром current_mode_in_header
- [ ] add_balance_and_mode_to_text() УДАЛЕНА
- [ ] MAIN_MENU с 5 кнопками работает
- [ ] Логирование: [MODE: X+SCREEN]
- [ ] Unit тесты пройдены: 10+

**Спринты 2-6:**
- [ ] Каждый режим полностью функционален
- [ ] ЭКРАНЫ 11, 14, 17 работают (новые!)
- [ ] Динамический текст по режиму
- [ ] Логирование информативно
- [ ] Unit тесты пройдены: каждый спринт 5-8 тестов
- [ ] E2E тесты пройдены: каждый режим полный поток

**Спринт 7:**
- [ ] TEXT_INPUT unified для всех режимов
- [ ] E2E тесты: ВСЕ режимы полные потоки
- [ ] Регрессионные тесты: V1 функциональность сохранена
- [ ] Coverage: >85%
- [ ] Документация обновлена
- [ ] Готово к Production

---

## 📞 КОНТАКТЫ И ПОДДЕРЖКА

**Project Owner:** [Your Name]  
**QA Lead:** [QA Name]  
**DevOps Lead:** [DevOps Name]  
**Tech Lead:** [Tech Name]

**Еженедельные синхры:** Пятницы, 15:00 UTC+3  
**Блокеры:** Сообщать сразу в Slack #interiorbot-v3  
**Документация:** GitHub Wiki

---

**Статус:** 🟢 PRODUCTION READY  
**Версия:** 3.0 - FINAL  
**Последнее обновление:** 27.12.2025 21:50 UTC+3