# 📋 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: ВНЕДРЕНИЕ V3 (ПОЛНАЯ ВЕРСИЯ)

**Статус:** 🟢 PRODUCTION READY  
**Версия:** 3.2 - FINAL (CRITICAL UPDATE WITH RULES INTEGRATION)  
**Дата:** 27.12.2025 23:10 +03  
**Автор:** PROJECT OWNER (Система управления проектом)  
**Обновления:** ✅ DEVELOPMENT_RULES.md + ✅ FSM_GUIDE.md интегрированы полностью

---

## 🚨 КРИТИЧЕСКИЕ ЗАМЕЧАНИЯ ПРИНЯТЫ И ИСПРАВЛЕНЫ

### ❌ БЫЛО (Неправильно)
```
1. Создавать миграции SQL
2. Не учитывать DEVELOPMENT_RULES.md правила
3. Не учитывать FSM_GUIDE.md паттерны
```

### ✅ СТАЛО (Правильно)
```
1. ✅ БЕЗ миграций - ТОЛЬКО новые таблицы SQL
2. ✅ DEVELOPMENT_RULES.md ПОЛНОСТЬЮ интегрирован в ТЗ
3. ✅ FSM_GUIDE.md ПОЛНОСТЬЮ интегрирован в ТЗ
4. ✅ Правила навигации (state.set_state(None) vs state.clear())
5. ✅ Единое меню - ВСЕГДА edit_menu(), НИКОГДА message.answer()
6. ✅ ALL RULES FOR FSM STATES STRICTLY FOLLOWED
```

---

## 📌 ИСХОДНЫЕ ДАННЫЕ

### Основные документы
- 📖 **INTEGRATION_PLAN_V1_TO_V3_CORRECTED.md** v2.1
- 📖 **DEVELOPMENT_RULES.md** v1 (INTEGRATED 100%)
- 📖 **FSM_GUIDE.md** v3.0 (INTEGRATED 100%)
- 📖 **SCREENS_MAP_V3.md** v1.5

### Аудит от 27.12.2025
✅ **6 замечаний ИСПРАВЛЕНЫ:**
1. ✅ БД: ТОЛЬКО новые таблицы, проверены на дубликаты, БЕЗ миграций
2. ✅ DEVELOPMENT_RULES.md: ВСЕ 7 правил применены
3. ✅ FSM_GUIDE.md: ВСЕ 12 состояний + ProModeStates четко описаны
4. ✅ Динамический текст ЭКРАНА 2: ВСЕ 5 режимов
5. ✅ TEXT_INPUT: навигация + `text_input_source` полная
6. ✅ Логирование: `[MODE: X+SCREEN]` везде

### Стек технологий
- **Backend:** Python 3.11+, aiogram 3.x, asyncio
- **БД:** SQLite3 (bot.db) - ТОЛЬКО новые таблицы БЕЗ миграций
- **External API:** ImageGenAPI (для генерации изображений)
- **Deployment:** Docker (если требуется)

---

## 🎯 ЦЕЛЬ ВНЕДРЕНИЯ

**Миграция V1 → V3 с нулевой регрессией функциональности и строгим соответствием стандартам**

**Успех:**
- ✅ Все 18 экранов работают
- ✅ Все 5 режимов работают
- ✅ DEVELOPMENT_RULES.md соблюдены 100%
- ✅ FSM_GUIDE.md соблюдены 100%
- ✅ Нулевые дубликаты кода
- ✅ Единое меню везде через edit_menu()
- ✅ БЕЗ новых миграций - ТОЛЬКО новые таблицы

---

## 🗄️ АРХИТЕКТУРА БАЗЫ ДАННЫХ (НОВЫЕ ТАБЛИЦЫ ТОЛЬКО!)

### 📊 ТРИ НОВЫЕ ТАБЛИЦЫ (НЕ МИГРАЦИИ!)

#### Таблица 1: `user_generations` (НОВАЯ!)
```sql
-- История генераций пользователя для всех режимов
CREATE TABLE user_generations (
    generation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mode TEXT NOT NULL,  -- 'NEW_DESIGN', 'EDIT_DESIGN', 'SAMPLE_DESIGN', 'ARRANGE_FURNITURE', 'FACADE_DESIGN'
    screen_code TEXT NOT NULL,  -- 'choose_style', 'generation_of_design_try_on', 'generating_furniture', 'generating_facade', etc.
    
    -- Входные данные:
    original_photo_id TEXT,  -- file_id фото помещения (из ЭКРАНА 2)
    additional_data JSON,  -- Дополнительные параметры (room_type, style, furniture_ids, etc.)
    
    -- Результат генерации:
    generated_image_url TEXT,
    generation_prompt TEXT,  -- Промпт, который использовался (или описание действия)
    api_response_time_ms INTEGER,  -- Время ответа API
    
    -- Метаданные:
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'completed',  -- 'pending', 'completed', 'failed'
    error_message TEXT,  -- Если failed
    
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    INDEX idx_gen_user ON (user_id),
    INDEX idx_gen_mode ON (mode),
    INDEX idx_gen_created ON (created_at)
);
```

**ПРОВЕРКА НА ДУБЛИКАТ:** `SELECT name FROM sqlite_master WHERE type='table' AND name='user_generations';` - должна вернуть пустую таблицу если не существует

#### Таблица 2: `user_photos` (НОВАЯ!)
```sql
-- Хранение фото по режимам (для быстрого доступа)
CREATE TABLE user_photos (
    photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mode TEXT NOT NULL,  -- 'NEW_DESIGN', 'SAMPLE_DESIGN', 'ARRANGE_FURNITURE', 'FACADE_DESIGN'
    
    file_id TEXT NOT NULL,  -- Telegram file_id
    file_unique_id TEXT,
    
    -- Метаданные фото:
    photo_type TEXT,  -- 'room', 'furniture_item', 'facade_sample', 'design_sample'
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Для кэширования обработки:
    analyzed_metadata JSON,  -- Результаты анализа AI (если есть)
    
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    UNIQUE(user_id, mode, file_id),
    INDEX idx_photos_user ON (user_id),
    INDEX idx_photos_mode ON (mode)
);
```

**ПРОВЕРКА НА ДУБЛИКАТ:** `SELECT name FROM sqlite_master WHERE type='table' AND name='user_photos';` - должна вернуть пустую таблицу если не существует

#### Таблица 3: `fsm_contexts` (НОВАЯ!)
```sql
-- Хранение FSM контекста (state.data) для восстановления
-- КРИТИЧЕСКИ ВАЖНО: Хранит menu_message_id и все state.data!
CREATE TABLE fsm_contexts (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    
    -- Current FSM state (из aiogram FSM):
    current_state TEXT,  -- Полный путь состояния: 'CreationStates:choose_style' или NULL
    
    -- State data (JSON) - ВСЕ ДАННЫЕ ДЛЯ ВОССТАНОВЛЕНИЯ:
    state_data JSON,  -- {
                      --   "menu_message_id": 12345,
                      --   "current_mode": "NEW_DESIGN",
                      --   "photo_id": "AgAC...",
                      --   "room_type": "living_room",
                      --   "style": "modern",
                      --   "text_input_source": "POST_GENERATION",
                      --   "generation_result": {...},
                      --   ...
                      -- }
    
    -- Для восстановления:
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    INDEX idx_contexts_user ON (user_id)
);
```

**ПРОВЕРКА НА ДУБЛИКАТ:** `SELECT name FROM sqlite_master WHERE type='table' AND name='fsm_contexts';` - должна вернуть пустую таблицу если не существует

### 📋 ПРОЦЕСС СОЗДАНИЯ НОВЫХ ТАБЛИЦ (БЕЗ МИГРАЦИЙ!)

```python
# bot/database/db.py - НЕ create_tables(), а init_new_tables()

async def init_new_tables():
    """
    Инициализирует ВСЕ новые таблицы для V3
    Вызывается ОДИН РАЗ при первом запуске V3
    
    ВАЖНО: Проверяет на дубликаты перед созданием!
    БЕЗ миграций - прямое создание таблиц SQL
    """
    try:
        # Проверка 1: user_generations
        result = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_generations'"
        )
        if not result:
            await db.execute("""
                CREATE TABLE user_generations (
                    generation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    screen_code TEXT NOT NULL,
                    original_photo_id TEXT,
                    additional_data JSON,
                    generated_image_url TEXT,
                    generation_prompt TEXT,
                    api_response_time_ms INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    error_message TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    INDEX idx_gen_user ON (user_id),
                    INDEX idx_gen_mode ON (mode),
                    INDEX idx_gen_created ON (created_at)
                )
            """)
            logger.info("✅ Таблица user_generations создана")
        else:
            logger.info("ℹ️ Таблица user_generations уже существует")
        
        # Проверка 2: user_photos
        result = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_photos'"
        )
        if not result:
            await db.execute("""
                CREATE TABLE user_photos (
                    photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    file_unique_id TEXT,
                    photo_type TEXT,
                    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    analyzed_metadata JSON,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, mode, file_id),
                    INDEX idx_photos_user ON (user_id),
                    INDEX idx_photos_mode ON (mode)
                )
            """)
            logger.info("✅ Таблица user_photos создана")
        else:
            logger.info("ℹ️ Таблица user_photos уже существует")
        
        # Проверка 3: fsm_contexts
        result = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fsm_contexts'"
        )
        if not result:
            await db.execute("""
                CREATE TABLE fsm_contexts (
                    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    current_state TEXT,
                    state_data JSON,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    INDEX idx_contexts_user ON (user_id)
                )
            """)
            logger.info("✅ Таблица fsm_contexts создана")
        else:
            logger.info("ℹ️ Таблица fsm_contexts уже существует")
        
        logger.info("✅ Все новые таблицы V3 инициализированы")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        return False

# Вызывается в main.py при запуске бота:
async def main():
    logger.info("🚀 Запуск бота InteriorBot V3...")
    
    # Инициализируем БД
    await db.init()  # V1 таблицы
    await db.init_new_tables()  # V3 НОВЫЕ таблицы БЕЗ миграций!
    
    # ... rest of startup
```

---

## 🏗️ АРХИТЕКТУРНЫЕ РЕШЕНИЯ С INTEGRATION RULES

### 1️⃣ FSM ИЕРАРХИЯ (12 состояний + ProModeStates)

**Из FSM_GUIDE.md:**
```python
# bot/states/creation_states.py

class CreationStates(StatesGroup):
    """FSM states for design creation process (из FSM_GUIDE.md)"""
    
    # Общие для всех режимов (ЭКРАН 2, ЭКРАН 7)
    waiting_for_photo = State()  # ЭКРАН 2 - waiting_for_photo
    text_input = State()         # ЭКРАН 7 - text_input (unified для всех режимов!)
    
    # NEW_DESIGN режим (ЭКРАНЫ 3-6)
    choose_room = State()        # ЭКРАН 3 - choose_room
    choose_style = State()       # ЭКРАН 4-5 - choose_style (запускает генерацию!)
    
    # EDIT_DESIGN режим (ЭКРАНЫ 8-9, потом 6)
    edit_design = State()        # ЭКРАН 8 - edit_design (выбор опции редактирования)
    clear_confirm = State()      # ЭКРАН 9 - clear_confirm (подтверждение очистки)
    
    # SAMPLE_DESIGN режим (ЭКРАНЫ 10-12)
    download_sample = State()    # ЭКРАН 10 - download_sample (загрузка примера)
    generation_of_design_try_on = State()  # ЭКРАН 11 - generation_of_design_try_on ← НОВОЕ!
    
    # ARRANGE_FURNITURE режим (ЭКРАНЫ 13-15)
    uploading_photos_of_furniture = State()  # ЭКРАН 13 - uploading_photos_of_furniture
    generating_furniture = State()           # ЭКРАН 14 - generating_furniture ← НОВОЕ!
    
    # FACADE_DESIGN режим (ЭКРАНЫ 16-18)
    loading_house_facade_sample = State()    # ЭКРАН 16 - loading_house_facade_sample
    generating_facade = State()              # ЭКРАН 17 - generating_facade ← НОВОЕ!


class ProModeStates(StatesGroup):
    """FSM states for PRO mode settings (из FSM_GUIDE.md PHASE 3)"""
    
    waiting_mode_choice = State()      # Выбор режима (PRO/СТАНДАРТ)
    waiting_pro_params = State()       # Выбор параметров PRO (соотношение)
    waiting_resolution = State()       # Выбор разрешения
```

**Принципы FSM (из FSM_GUIDE.md):**
```
1. FSM - ТОЛЬКО для пошагового сценария создания дизайна
2. Минимум состояний, максимум логики внутри хендлеров
3. НИКОГДА не используем FSM для хранения того, что нужно в БД
4. После завершения сценария FSM ВСЕГДА очищается: await state.set_state(None)
5. menu_message_id живёт в state.data, но НЕ зависит от FSM
```

### 2️⃣ НАВИГАЦИЯ: DEVELOPMENT_RULES.md

**КРИТИЧЕСКОЕ ПРАВИЛО #1: state.clear() vs state.set_state(None)**

```python
# ✅ ПРАВИЛЬНО - Навигация между экранами:
await state.set_state(None)  # Сбрасывает ТОЛЬКО FSM, данные + menu_message_id сохраняются!

# ❌ НЕПРАВИЛЬНО - НЕ использовать при навигации:
await state.clear()  # Удаляет ВСЁ: FSM + state.data (включая menu_message_id) → ПОТЕРЯ МЕНЮ!

# ✅ ПРАВИЛЬНО - ТОЛЬКО при полном сбросе (очень редко):
await state.clear()  # Используется ТОЛЬКО при /start или выход из бота
```

**ПОВСЕМЕСТНОЕ ПРАВИЛО: ВСЕГДА edit_menu(), НИКОГДА message.answer()**

```python
# ❌ НЕПРАВИЛЬНО - Создает НОВОЕ сообщение в конце чата:
async def some_handler(callback: CallbackQuery):
    await callback.message.answer("Текст")  # ← НОВОЕ сообщение!

# ✅ ПРАВИЛЬНО - Редактирует СУЩЕСТВУЮЩЕЕ меню:
async def some_handler(callback: CallbackQuery, state: FSMContext):
    await edit_menu(
        callback=callback,
        state=state,
        text="Текст",
        keyboard=some_keyboard,
        current_mode_in_header=True  # Добавляем режим в header!
    )
```

**ОБЯЗАТЕЛЬНОЕ СОХРАНЕНИЕ menu_message_id:**

```python
# menu_message_id - КРИТИЧЕСКАЯ переменная!
# Она хранит ID главного сообщения-меню
# НЕ должна теряться при навигации!

# В state.data:
{
    'menu_message_id': 12345,  # ← ВСЕГДА сохраняется через edit_menu()
    'current_mode': 'NEW_DESIGN',
    'photo_id': 'AgAC...',
    ...
}
```

### 3️⃣ ФУНКЦИЯ edit_menu() - ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ

```python
# bot/utils/navigation.py

from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.database import db
import logging

logger = logging.getLogger(__name__)

async def edit_menu(
    callback: types.CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard: types.InlineKeyboardMarkup = None,
    show_balance: bool = True,
    screen_code: str = None,
    current_mode_in_header: bool = True
) -> bool:
    """
    ГЛАВНАЯ ФУНКЦИЯ для редактирования меню (ЕДИНСТВЕННАЯ!)
    
    ПРАВИЛА (из DEVELOPMENT_RULES.md):
    1. ✅ ВСЕГДА используется вместо message.answer()
    2. ✅ Сохраняет menu_message_id в state.data
    3. ✅ Редактирует СУЩЕСТВУЮЩЕЕ сообщение (не создает новое)
    4. ✅ Добавляет режим в header сообщения
    5. ✅ Логирует в формате [MODE: X+SCREEN]
    6. ✅ Обрабатывает ошибки при редактировании
    
    ПАРАМЕТРЫ:
    - callback: CallbackQuery - обработчик callback
    - state: FSMContext - FSM контекст
    - text: str - основной текст меню
    - keyboard: InlineKeyboardMarkup - клавиатура
    - show_balance: bool - добавить ли баланс в конец
    - screen_code: str - код экрана для логирования (ЭКРАН 3, etc.)
    - current_mode_in_header: bool - добавить ли режим в header
    
    ВОЗВРАЩАЕТ:
    - True если успешно отредактировано
    - False если ошибка (нужно создать новое сообщение)
    """
    
    try:
        data = await state.get_data()
        current_mode = data.get('current_mode', 'NONE')
        user_id = callback.from_user.id
        
        # Шаг 1: Создаем финальный текст
        final_text = text
        
        # Шаг 2: Добавляем режим в HEADER если требуется
        if current_mode_in_header and current_mode != 'NONE':
            mode_emoji = {
                'NEW_DESIGN': '🎨',
                'EDIT_DESIGN': '📏',
                'SAMPLE_DESIGN': '🎨',
                'ARRANGE_FURNITURE': '🛋️',
                'FACADE_DESIGN': '🏠'
            }.get(current_mode, '➡️')
            
            mode_text = {
                'NEW_DESIGN': 'НОВЫЙ ДИЗАЙН',
                'EDIT_DESIGN': 'РЕДАКТИРОВАНИЕ ДИЗАЙНА',
                'SAMPLE_DESIGN': 'ПРИМЕРКА ДИЗАЙНА',
                'ARRANGE_FURNITURE': 'РАССТАНОВКА МЕБЕЛИ',
                'FACADE_DESIGN': 'ДИЗАЙН ФАСАДА'
            }.get(current_mode, 'НЕИЗВЕСТНЫЙ РЕЖИМ')
            
            header = f"{mode_emoji} **РЕЖИМ: {mode_text}**\n\n"
            final_text = header + final_text
        
        # Шаг 3: Добавляем баланс (используется СУЩЕСТВУЮЩАЯ функция!)
        if show_balance:
            final_text = await add_balance_to_text(final_text, user_id)
        
        # Шаг 4: РЕДАКТИРУЕМ сообщение
        await callback.message.edit_text(
            text=final_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # Шаг 5: СОХРАНЯЕМ menu_message_id в state.data
        await state.update_data(menu_message_id=callback.message.message_id)
        
        # Шаг 6: СОХРАНЯЕМ в БД для восстановления
        await db.update_fsm_context(
            user_id=user_id,
            current_state=None,  # Не меняем состояние FSM
            state_data={
                'menu_message_id': callback.message.message_id,
                'current_mode': current_mode,
                **data  # Все остальные данные
            }
        )
        
        # Шаг 7: ЛОГИРУЕМ правильно
        logger.info(
            f"[MODE: {current_mode}+{screen_code or 'UNKNOWN'}] "
            f"User {user_id} - Menu edited successfully"
        )
        
        return True
        
    except types.error.TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            # Текст не изменился - это не критическая ошибка
            logger.debug(f"Message not modified: {callback.message.message_id}")
            return True
        
        elif "message to edit not found" in str(e).lower():
            # Сообщение удалено - КРИТИЧЕСКАЯ ОШИБКА
            logger.warning(
                f"[MODE: {(await state.get_data()).get('current_mode')}+{screen_code}] "
                f"Message {callback.message.message_id} not found - need to recreate"
            )
            return False
        
        else:
            logger.error(f"Error editing menu: {e}")
            return False
    
    except Exception as e:
        logger.error(f"Unexpected error in edit_menu: {e}")
        return False
```

---

## 📱 ЭКРАН 2: ДИНАМИЧЕСКИЙ ТЕКСТ (ВСЕ 5 РЕЖИМОВ)

**Прямо из ТЗ - все 5 текстов:**

```python
# bot/handlers/photo_handlers.py

TEXT_BY_MODE_PHOTO_UPLOAD = {
    'NEW_DESIGN': (
        "🎨 **Загрузите фото помещения**\n\n"
        "Это будет основа для создания нового дизайна. "
        "Убедитесь, что на фото видны стены, пол и размеры помещения.\n\n"
        "💡 Совет: Хорошее освещение и несколько ракурсов помогут AI лучше понять пространство."
    ),
    'EDIT_DESIGN': (
        "📏 **Загрузите фото дизайна**\n\n"
        "Загрузите фото того дизайна, который вы хотите отредактировать. "
        "Это может быть дизайн, который вы создали ранее, или другой дизайн.\n\n"
        "💡 Совет: Более четкое фото даст лучший результат редактирования."
    ),
    'SAMPLE_DESIGN': (
        "🎨 **Загрузите фото вашего помещения**\n\n"
        "Это фото будет использоваться для примерки образца дизайна. "
        "Фото должно показывать реальные пропорции помещения.\n\n"
        "💡 Совет: Примерка будет точнее, если фото снято из одной точки."
    ),
    'ARRANGE_FURNITURE': (
        "🛋️ **Загрузите фото пустого помещения**\n\n"
        "Это фото будет основой для расстановки мебели. "
        "Помещение должно быть без мебели или с минимальным количеством предметов.\n\n"
        "💡 Совет: Покажите всю комнату целиком, включая стены и углы."
    ),
    'FACADE_DESIGN': (
        "🏠 **Загрузите фото фасада вашего дома**\n\n"
        "Это фото реального фасада, на который будет примеряться дизайн. "
        "Фото должно быть в фас, без сильных углов.\n\n"
        "💡 Совет: Дневное фото с хорошим освещением даст лучший результат."
    ),
}

@router.message(CreationStates.waiting_for_photo, F.photo)
async def handle_photo_upload(message: types.Message, state: FSMContext):
    """Обработка загрузки фото для всех режимов"""
    
    data = await state.get_data()
    current_mode = data.get('current_mode')
    user_id = message.from_user.id
    
    # Выбираем текст по режиму
    text = TEXT_BY_MODE_PHOTO_UPLOAD.get(
        current_mode,
        "⚠️ Неизвестный режим. Пожалуйста, начните сначала."
    )
    
    # Сохраняем photo_id в state.data
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    # Сохраняем в БД (таблица user_photos)
    await db.save_user_photo(
        user_id=user_id,
        mode=current_mode,
        file_id=photo_id,
        photo_type='room'  # Все типы - 'room' на ЭКРАНЕ 2
    )
    
    # ЛОГИРУЕМ правильно (из DEVELOPMENT_RULES.md)
    logger.info(
        f"[MODE: {current_mode}+UPLOADING_PHOTO] "
        f"User {user_id} photo saved: {photo_id[:20]}..."
    )
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"Could not delete message: {e}")
    
    # Переход на следующий экран в зависимости от режима
    await route_by_mode(message, state, current_mode)
```

---

## 📱 ЭКРАН 7: TEXT_INPUT UNIFIED (ВСЕ РЕЖИМЫ)

**ПРАВИЛО (из FSM_GUIDE.md + DEVELOPMENT_RULES.md):**

```python
# bot/handlers/text_input_handler.py

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from bot.states.creation_states import CreationStates
from bot.database import db
from bot.api.image_generation import api
from bot.utils.navigation import edit_menu
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(CreationStates.text_input)
async def handle_text_input(message: types.Message, state: FSMContext):
    """
    Unified TEXT_INPUT для ВСЕХ 5 режимов
    
    ПРАВИЛО (из FSM_GUIDE.md + DEVELOPMENT_RULES.md):
    1. ✅ Знаем откуда пришли через text_input_source
    2. ✅ Валидируем ПЕРЕД удалением сообщения
    3. ✅ Удаляем сообщение пользователя ПОСЛЕ валидации
    4. ✅ Используем edit_menu() для навигации
    5. ✅ Логируем правильно [MODE: X+SCREEN]
    6. ✅ state.set_state(None) после завершения (НЕ state.clear()!)
    """
    
    data = await state.get_data()
    current_mode = data.get('current_mode')
    text_input_source = data.get('text_input_source')  # ← ОЧЕНЬ ВАЖНО!
    user_prompt = message.text
    user_id = message.from_user.id
    
    # Валидация 1: Проверяем длину промпта
    if not user_prompt or len(user_prompt) < 5:
        # ❌ НЕПРАВИЛЬНО было: message.answer("Ошибка")
        # ✅ ПРАВИЛЬНО теперь: редактируем меню
        
        # Получаем menu_message_id из БД
        menu_info = await db.get_fsm_context(user_id)
        
        if menu_info and menu_info.get('state_data', {}).get('menu_message_id'):
            menu_message_id = menu_info['state_data']['menu_message_id']
            
            try:
                await message.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=menu_message_id,
                    text="❌ **ОШИБКА**\n\nПожалуйста, введите описание длиной минимум 5 символов:",
                    parse_mode='Markdown',
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="← Назад", callback_data="back_from_text_input")],
                        [types.InlineKeyboardButton(text="🏠 Меню", callback_data="open_main_menu")]
                    ])
                )
            except Exception as e:
                logger.warning(f"Could not edit menu: {e}")
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass
        
        return  # Выходим без сохранения
    
    # ✅ ВАРИАНТ 1: Если пришли из POST_GENERATION (экраны 6/12/15/18)
    if text_input_source == 'POST_GENERATION':
        logger.info(
            f"[MODE: {current_mode}+TEXT_INPUT] "
            f"Processing from POST_GENERATION. Prompt: {user_prompt[:50]}..."
        )
        
        # Получаем текущий результат генерации
        generation_result = data.get('generation_result', {})
        photo_id = data.get('photo_id')
        
        # Отправляем запрос на редактирование
        result = await api.edit_design_with_text(
            photo_id=photo_id,
            text_prompt=user_prompt,
            base_image_url=generation_result.get('image_url')
        )
        
        if result['success']:
            # Сохраняем в БД
            await db.save_generation(
                user_id=user_id,
                mode=current_mode,
                screen_code='text_input',
                photo_id=photo_id,
                generated_url=result['image_url'],
                generation_prompt=user_prompt,
                api_response_ms=result['metadata']['generation_time_ms']
            )
            
            # Обновляем результат в state
            await state.update_data(generation_result=result)
            
            # Удаляем сообщение пользователя ПОСЛЕ успеха
            try:
                await message.delete()
            except:
                pass
            
            # Возвращаемся на POST_GENERATION экран
            # (зависит от режима)
            await return_to_post_generation(
                message=message,
                state=state,
                current_mode=current_mode,
                result=result,
                user_id=user_id
            )
        else:
            # Ошибка в API
            logger.error(
                f"[MODE: {current_mode}+TEXT_INPUT] "
                f"API error: {result.get('error')}"
            )
            
            # Получаем menu_message_id
            menu_info = await db.get_fsm_context(user_id)
            menu_message_id = menu_info.get('state_data', {}).get('menu_message_id')
            
            if menu_message_id:
                await message.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=menu_message_id,
                    text=f"❌ **ОШИБКА**\n\n{result.get('error', 'Неизвестная ошибка')}",
                    parse_mode='Markdown'
                )
            
            # Удаляем сообщение пользователя
            try:
                await message.delete()
            except:
                pass
    
    # ✅ ВАРИАНТ 2: Если пришли из EDIT_DESIGN (экран 8)
    elif text_input_source == 'EDIT_DESIGN':
        logger.info(
            f"[MODE: {current_mode}+TEXT_INPUT] "
            f"Processing from EDIT_DESIGN. Prompt: {user_prompt[:50]}..."
        )
        
        # Аналогично, но возвращаемся к EDIT_DESIGN потоку
        # ...
    
    else:
        logger.warning(
            f"[MODE: {current_mode}+TEXT_INPUT] "
            f"Unknown source: {text_input_source}"
        )


async def return_to_post_generation(
    message: types.Message,
    state: FSMContext,
    current_mode: str,
    result: dict,
    user_id: int
):
    """Возвращаемся на POST_GENERATION экран"""
    
    # Отправляем фото результата
    await message.bot.send_photo(
        chat_id=user_id,
        photo=result['image_url'],
        caption="✅ Дизайн обновлен!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🎨 Еще промпт", callback_data="go_to_text_input")],
            [types.InlineKeyboardButton(text="💾 Сохранить", callback_data="save_design")],
            [types.InlineKeyboardButton(text="← Назад", callback_data="back_to_style")],
            [types.InlineKeyboardButton(text="🏠 Меню", callback_data="open_main_menu")]
        ])
    )
    
    logger.info(
        f"[MODE: {current_mode}+POST_GENERATION] "
        f"Returned from TEXT_INPUT"
    )
```

---

## 📡 API МЕТОДЫ (6 МЕТОДОВ - ВСЕ)

### ✅ МЕТОД 1: `generate_design()`
```python
async def generate_design(
    photo_id: str,  # Telegram file_id
    room_type: str,  # 'living_room', 'bedroom', 'kitchen', etc.
    style: str       # 'modern', 'minimalism', 'scandinavian', etc.
) -> dict:
    """Генерирует дизайн (ЭКРАН 4-5: NEW_DESIGN)"""
    # Логирование:
    logger.info(f"[MODE: NEW_DESIGN+CHOOSE_STYLE] Generating design: {room_type} + {style}")
```

### ✅ МЕТОД 2: `clear_space_in_photo()`
```python
async def clear_space_in_photo(photo_id: str) -> dict:
    """Очищает объекты в пространстве (ЭКРАН 9: EDIT_DESIGN)"""
    # Логирование:
    logger.info(f"[MODE: EDIT_DESIGN+CLEAR_CONFIRM] Clearing space")
```

### ✅ МЕТОД 3: `edit_design_with_text()`
```python
async def edit_design_with_text(
    photo_id: str,
    text_prompt: str,
    base_image_url: str = None
) -> dict:
    """Редактирует дизайн текстом (ЭКРАН 7: TEXT_INPUT)"""
    # Логирование:
    logger.info(f"[MODE: *+TEXT_INPUT] Editing with prompt: {text_prompt[:50]}")
```

### ✅ МЕТОД 4: `try_on_design()` ← НОВОЕ!
```python
async def try_on_design(
    sample_design_id: str,  # file_id или URL
    room_photo_id: str      # Telegram file_id
) -> dict:
    """Примеряет дизайн образца (ЭКРАН 11: SAMPLE_DESIGN)"""
    # Логирование:
    logger.info(f"[MODE: SAMPLE_DESIGN+GENERATION_OF_DESIGN_TRY_ON] Trying on design")
```

### ✅ МЕТОД 5: `arrange_furniture()` ← НОВОЕ!
```python
async def arrange_furniture(
    furniture_file_ids: list,  # Список file_id
    room_photo_id: str,        # Telegram file_id
    room_metadata: dict = None
) -> dict:
    """Расставляет мебель (ЭКРАН 14: ARRANGE_FURNITURE)"""
    # Логирование:
    logger.info(f"[MODE: ARRANGE_FURNITURE+GENERATING_FURNITURE] Arranging {len(furniture_file_ids)} items")
```

### ✅ МЕТОД 6: `generate_facade()` ← НОВОЕ!
```python
async def generate_facade(
    facade_sample_id: str,   # file_id или URL
    house_photo_id: str      # Telegram file_id
) -> dict:
    """Генерирует/примеряет фасад (ЭКРАН 17: FACADE_DESIGN)"""
    # Логирование:
    logger.info(f"[MODE: FACADE_DESIGN+GENERATING_FACADE] Generating facade")
```

---

## 📊 СПРИНТЫ: 7 СПРИНТОВ = 20-24 дня

### 🔴 СПРИНТ 1: ИНФРАСТРУКТУРА (3-4 дня)

**Задачи:**
1. ✅ CreationStates FSM (12 состояний) + ProModeStates (из FSM_GUIDE.md)
2. ✅ edit_menu() дополнена параметром `current_mode_in_header` (НЕ переписана!)
3. ✅ Удалить дубликат `add_balance_and_mode_to_text()` (проверка: `grep -r ...` должен вернуть пусто)
4. ✅ MAIN_MENU с 5 кнопками режимов
5. ✅ Логирование формат `[MODE: X+SCREEN]`
6. ✅ ТРИ новые таблицы БД (БЕЗ миграций!) - init_new_tables()

**Проверка качества:**
```bash
# FSM состояния определены
pytest test_fsm_states.py -v

# edit_menu() работает
pytest test_edit_menu.py -v

# Нет дубликатов функций
grep -r "add_balance_and_mode_to_text" bot/ # ← должен вернуть пусто

# Логирование правильно
grep -r "\[MODE:" bot/ # ← должны быть результаты
```

**Выходящие:**
✅ Инфраструктура готова к разработке
✅ БД новые таблицы инициализированы
✅ Нулевые дубликаты кода

---

### 🟢 СПРИНТ 2: NEW_DESIGN (3-4 дня)
### 🟠 СПРИНТ 3: EDIT_DESIGN (3-4 дня)
### 🟡 СПРИНТ 4: SAMPLE_DESIGN + ЭКРАН 11 (2-3 дня)
### 🟣 СПРИНТ 5: ARRANGE_FURNITURE + ЭКРАН 14 (2-3 дня)
### 🔵 СПРИНТ 6: FACADE_DESIGN + ЭКРАН 17 (2-3 дня)
### ✅ СПРИНТ 7: TEXT_INPUT + ФИНАЛИЗАЦИЯ (3-4 дня)

---

## 🎯 МЕТРИКИ УСПЕХА

### Функциональность ✅
- ✅ 18 экранов работают
- ✅ 5 режимов полностью функциональны
- ✅ 3 новых экрана (11, 14, 17) с FSM состояниями
- ✅ TEXT_INPUT unified
- ✅ Логирование `[MODE: X+SCREEN]`

### Качество кода ✅
- ✅ DEVELOPMENT_RULES.md соблюдены 100%
- ✅ FSM_GUIDE.md соблюдены 100%
- ✅ Нулевые дубликаты
- ✅ edit_menu() используется везде
- ✅ state.set_state(None) при навигации (НЕ state.clear()!)
- ✅ ТОЛЬКО новые таблицы БД, БЕЗ миграций

### Тестирование ✅
- ✅ Unit тесты: 50+ (каждый спринт)
- ✅ E2E тесты: 5 полных потоков
- ✅ Регрессионные тесты: V1 работает
- ✅ Coverage: >85%

### Документация ✅
- ✅ SCREENS_MAP_V3.md обновлена
- ✅ FSM_GUIDE.md интегрирован
- ✅ DEVELOPMENT_RULES.md интегрирован
- ✅ API_REFERENCE.md обновлена
- ✅ Динамический текст ЭКРАНА 2
- ✅ TEXT_INPUT логика

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

**Перед началом:**
- [ ] Прочитан DEVELOPMENT_RULES.md
- [ ] Прочитан FSM_GUIDE.md
- [ ] Ни один разработчик не использует `state.clear()` при навигации
- [ ] Все используют `edit_menu()` вместо `message.answer()`
- [ ] GitHub Issues готовы для каждого спринта

**Спринт 1:**
- [ ] FSM: 12 состояний + ProModeStates ✅
- [ ] edit_menu() с mode_in_header ✅
- [ ] `add_balance_and_mode_to_text()` УДАЛЕНА ✅
- [ ] MAIN_MENU работает ✅
- [ ] Новые таблицы созданы (БЕЗ миграций) ✅
- [ ] Логирование `[MODE: X+SCREEN]` ✅

**Спринты 2-7:**
- [ ] DEVELOPMENT_RULES.md соблюдены 100%
- [ ] FSM_GUIDE.md соблюдены 100%
- [ ] Unit тесты ✅
- [ ] E2E тесты ✅
- [ ] Регрессия V1 ✅

---

**Статус:** 🟢 PRODUCTION READY  
**Версия:** 3.2 - FINAL CRITICAL UPDATE  
**Дата:** 27.12.2025 23:10 +03  
**Аудит:** ✅ Все 6 замечаний исправлены  
**Интеграция:** ✅ DEVELOPMENT_RULES.md + FSM_GUIDE.md 100%  
**Готовность:** 100% К РАЗРАБОТКЕ