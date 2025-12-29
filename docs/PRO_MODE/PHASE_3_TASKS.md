# 🔧 PHASE 3 - ИНТЕГРАЦИЯ PRO MODE

**Цель:** Завершить внедрение PRO MODE и подключить к генерации  
**Последняя остановка:** PHASE 2 (коммит: `5021b162d5248e93b29f206ed6572379fdcbfc99`)  
**Фаза:** 3/3  
**Порядок:** ВБОШТ тоби указанные (1→2)

---

## ✅ TASK 1: Добавить FSM-состояния

**Где:** `bot/states/fsm.py`  
**Тим:** 5 мин  
**Цель:** Определить состояния PRO MODE

### Код:

```python
from aiogram.fsm.state import StatesGroup, State

# Добавить в конец файла:

class ProModeStates(StatesGroup):
    """
    Машина состояний для PRO MODE
    
    Описание:
    - choosing_mode: Выбор между СТАНДАРТ и PRO
    - choosing_pro_params: Выбор параметров PRO (соотношение, разрешение)
    
    Вход:
    - callback: profile_settings нажать "НАСТРОЙКИ РЕЖИМА"
    
    Выход:
    - state.set_state(None) и возврат в профиль
    """
    
    # State 1: Выбор режима (СТАНДАРТ vs PRO)
    choosing_mode = State()
    
    # State 2: Выбор параметров PRO (соотношение + разрешение)
    choosing_pro_params = State()
```

### Контроль:

- [ ] Класс `ProModeStates` добавлен
- [ ] 2 состояния дефинированы
- [ ] Описание и комментарии добавлены
- [ ] Коммит: `[FSM] Add ProModeStates to fsm.py`

---

## ✅ TASK 2: Зарегистрировать router

**Где:** `bot/handlers/__init__.py`  
**Тим:** 3 мин  
**Цель:** Подключить обработчики PRO MODE

### Код:

```python
# В топе файла - добавить импорт:
from bot.handlers.pro_mode import router as pro_mode_router

# В функции setup_routers() - добавить регистрацию:
async def setup_routers(dp: Dispatcher):
    # исторические роутеры...
    
    # ПРО MODE
    dp.include_router(pro_mode_router)
    
    logger.info("✅ [SETUP] Pro Mode router registered")
```

### Контроль:

- [ ] Импорт `pro_mode_router` добавлен
- [ ] Регистрация `dp.include_router()` в `setup_routers()`
- [ ] Логирование добавлено
- [ ] Коммит: `[SETUP] Register pro_mode router`

---

## ✅ TASK 3: Обновить FSM_GUIDE.md

**Где:** `FSM_GUIDE.md`  
**Тим:** 10 мин  
**Цель:** Додать документацию ProModeStates

### Найти раздел:

```markdown
## 📁 СПОНОЛНЮ: PRO MODE STATES

### 1. ProModeStates.choosing_mode

**Где объявлено:** `bot/states/fsm.py`  
**Где используется:** `bot/handlers/pro_mode.py`

**Смысл:**
Пользователь выбирает режим генерации: СТАНДАРТ или PRO.

**Вход в состояние:**
```python
await state.set_state(ProModeStates.choosing_mode)
```

**Кем устанавливается:**
- `show_mode_selection()` (каллбек `profile_settings`)

**Обработчики в этом состоянии:**
```python
@router.callback_query(F.data == "mode_std", state=ProModeStates.choosing_mode)
async def select_standard_mode(...)

@router.callback_query(F.data == "mode_pro", state=ProModeStates.choosing_mode)
async def select_pro_mode(...)
```

**Допустимые callback_data:**
- `mode_std` → стандартный режим
- `mode_pro` → PRO режим
- `profile_settings` → вернуться в профиль

**Выход из состояния:**
- `mode_std` → `state.set_state(None)` + подтверждение
- `mode_pro` → `ProModeStates.choosing_pro_params`
- `profile_settings` → `state.set_state(None)`

---

### 2. ProModeStates.choosing_pro_params

**Где объявлено:** `bot/states/fsm.py`  
**Где используется:** `bot/handlers/pro_mode.py`

**Смысл:**
Пользователь выбирает параметры PRO режима: соотношение и разрешение.

**Вход в состояние:**
```python
await state.set_state(ProModeStates.choosing_pro_params)
```

**Кем устанавливается:**
- `select_pro_mode()` (каллбек `mode_pro`)

**Обработчики в этом состоянии:**
```python
@router.callback_query(F.data.startswith("aspect_"), state=ProModeStates.choosing_pro_params)
async def select_aspect_ratio(...)

@router.callback_query(F.data.startswith("res_"), state=ProModeStates.choosing_pro_params)
async def select_resolution(...)

@router.callback_query(F.data == "profile_settings", state=ProModeStates.choosing_pro_params)
async def back_to_mode_selection(...)
```

**Допустимые callback_data:**
- `aspect_16:9`, `aspect_4:3`, `aspect_1:1`, `aspect_9:16` → выбор соотношения
- `res_1K`, `res_2K`, `res_4K` → выбор разрешения
- `profile_settings` → вернуться к выбору режима

**Выход из состояния:**
- `aspect_*` → Обновить menu (state не исменяется)
- `res_*` → Обновить menu (state не исменяется)
- `profile_settings` → `ProModeStates.choosing_mode`
```

### Контроль:

- [ ] Добавлен раздел "ПРО MODE STATES"
- [ ] Описаны оба состояния
- [ ] Указаны обработчики для каждого состояния
- [ ] Коммит: `[DOC] Update FSM_GUIDE.md with ProModeStates`

---

## ✅ TASK 4: Подключить к БД (Placeholder)

**Где:** `bot/handlers/pro_mode.py`  
**Тим:** 20 мин  
**Цель:** Удалить TODO и споси трю БД

### TODO для замены:

```python
# TODO 1: Определить актуальные db функции:
await db.get_user(user_id)
await db.get_pro_settings(user_id)
await db.update_pro_settings(user_id, **params)
await db.save_chat_menu(chat_id, user_id, message_id, screen_code)
```

### Контроль:

- [ ] Все TODO удалены
- [ ] Подключены функции БД
- [ ] Коммит: `[DB] Connect pro_mode handlers to database`

---

## ✅ TASK 5: Обновить генерацию десина

**Где:** `bot/handlers/creation.py`  
**Тим:** 15 мин  
**Цель:** Передать параметры PRO в генератор

### Логика:

```python
# Перед запросом в апи генерации:
user_settings = await db.get_pro_settings(user_id)

if user_settings['mode'] == 'pro':
    aspect_ratio = user_settings.get('aspect_ratio', '16:9')
    resolution = user_settings.get('resolution', '1K')
else:
    aspect_ratio = '16:9'  # по умолчанию
    resolution = '1K'

# Передать в API
result = await generate_design(
    photo=photo,
    room=room,
    style=style,
    aspect_ratio=aspect_ratio,
    resolution=resolution
)
```

### Контроль:

- [ ] Получаем настройки из БД
- [ ] Получаем дефолты для стандартного режима
- [ ] Передаем в генератор
- [ ] Коммит: `[GENERATION] Pass PRO params to API`

---

## ✅ TASK 6: Тестирование

**Где:** `tests/test_pro_mode.py` (НОВЫЙ ФАЙЛ)  
**Тим:** 30 мин  
**Цель:** Покрыть unit-тестами

### Контроль:

- [ ] Тест для `show_mode_selection()`
- [ ] Тест для `select_standard_mode()`
- [ ] Тест для `select_pro_mode()`
- [ ] Тест для `select_aspect_ratio()`
- [ ] Тест для `select_resolution()`
- [ ] Проверка `menu_message_id` сохраняется
- [ ] Коммит: `[TEST] Add unit tests for pro_mode handlers`

---

## 📁 ПОРЯДОК ВЫПОЛНЕНИЯ

```
1. TASK 1: FSM состояния  ✅ (5 мин)
↓
2. TASK 2: Обработчики регистрации ✅ (3 мин)
↓
3. TASK 3: Обновить FSM_GUIDE.md ✅ (10 мин)
↓
4. TASK 4: Подключение к БД ✅ (20 мин)
↓
5. TASK 5: Обновить генерацию ✅ (15 мин)
↓
6. TASK 6: Тестирование ✅ (30 мин)
↓
ЭКОНОМЫ → PHASE 3 COMPLETE!
```

**Общее время:** ~80 мин = **1.5 часа**

---

## ⚠️ НОРМАЛИЗАЦИЯ COMMITS

Каждый коммит должен иметь тег:

```
[FSM]       - добавление состояний
[SETUP]     - регистрация роутеров
[DOC]       - обновление документации
[DB]        - связь с базой
[GENERATION] - интеграция с генерацией
[TEST]      - тесты
```

---

## ✅ ЭКОНОМы ПОСЛЕ PHASE 3

```
ПОЛНОСТЬЮ READY TO:
- Показывать экран выбора режима ✅
- Выбирать ПЕРОІМ, аспект, разрешение ✅
- Сохранять в БД ✅
- Передавать в генерацию ✅
- Полное тестирование ✅
```

---

*Новые задачи актуальны на 24.12.2025, 13:19 UTC+3*
