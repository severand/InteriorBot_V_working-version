# 🔴 КРИТИЧЕСКОЕ ТЗ - ЭКРАН 1 С 3 ЭЛЕМЕНТАМИ В ФУТЕРЕ

**Версия:** 3.0 - ИСПРАВЛЕННАЯ  
**Дата:** 2025-12-28 01:13  
**Статус:** 🔴 КРИТИЧЕСКАЯ ОШИБКА ИСПРАВЛЕНА  

---

## 🎯 ТРИ ЭЛЕМЕНТА В ФУТЕРЕ (ОБЯЗАТЕЛЬНО!)

**СТРУКТУРА ФУТЕРА (в КАЖДОМ сообщении):**
```
💰 Баланс: {balance} | 🎨 Режим генерации: {generation_mode} | 🔧 Режим работы: {work_mode}
```

**ПРИМЕР 1:**
```
💰 Баланс: 3 | 🎨 Режим генерации: СТАНДАРТ | 🔧 Режим работы: Выбор режима
```

**ПРИМЕР 2 (после выбора режима):**
```
💰 Баланс: 3 | 🎨 Режим генерации: СТАНДАРТ | 🔧 Режим работы: Создание
```

**ПРИМЕР 3 (другой режим генерации):**
```
💰 Баланс: 10 | 🎨 Режим генерации: ПРО | 🔧 Режим работы: Редактирование
```

---

## 🗂️ ДАННЫЕ В ФУТЕРЕ

### 1️⃣ БАЛАНС (Balance) - СТОИМОСТЬ ГЕНЕРАЦИЙ

**Источник:** `users.balance` из БД  
**Тип:** INTEGER  
**Описание:** Количество оставшихся генераций в текущем режиме генерации  
**Обновление:** При успешной генерации вычитается стоимость  
**Диапазон:** 0-бесконечность  

```python
# Текущая логика (сохранить как есть)
balance = user.balance  # из users.balance
```

---

### 2️⃣ РЕЖИМ ГЕНЕРАЦИИ (Generation Mode) - ТИП СЕРВИСА

**Источник:** `users.generation_mode` из БД  
**Тип:** TEXT (ENUM-like)  
**Возможные значения:**
```python
GENERATION_MODES = {
    "STANDARD": "СТАНДАРТ",    # базовые генерации
    "PRO": "ПРО",              # улучшенные генерации  
    "PREMIUM": "ПРЕМИУМ",      # максимум возможностей
}
```

**Описание:**
- Выбирается пользователем в отдельной части приложения (профиль/платежи)
- **НЕ выбирается на ЭКРАНЕ 1**
- Влияет на стоимость генерации и качество
- Сохраняется В БД в таблице `users`

**Обновление:**
- При смене пакета подписки в профиле
- При покупке через платежи
- Сохраняется в `users.generation_mode`

```python
# Получить из БД
generation_mode = user.generation_mode  # из users.generation_mode
generation_mode_display = GENERATION_MODES.get(generation_mode, "СТАНДАРТ")
```

---

### 3️⃣ РЕЖИМ РАБОТЫ (Work Mode) - ВЫБОР НА ЭКРАНЕ 1

**Источник:** `users.current_work_mode` из БД + FSM state  
**Тип:** TEXT (ENUM)  
**Возможные значения:**
```python
WORK_MODES = {
    "CHOOSING_MODE": "Выбор режима",          # ЭКрАН 1
    "NEW_DESIGN": "Создание",                 # новый дизайн
    "EDIT_DESIGN": "Редактирование",         # редактирование
    "SAMPLE_DESIGN": "Примерка",              # примерка
    "ARRANGE_FURNITURE": "Мебель",            # расстановка мебели
    "FACADE_DESIGN": "Фасад",                 # дизайн фасада
}
```

**Описание:**
- **ВЫБИРАЕТСЯ на ЭКРАНЕ 1** (режимный выбор)
- Определяет поток работы пользователя
- Сохраняется при выборе кнопки на ЭКРАНЕ 1
- **СОХРАНЯЕТСЯ в БД** (`users.current_work_mode`)
- **ВОССТАНАВЛИВАЕТСЯ при рестарте бота** из БД

**Логика:**
1. Пользователь нажимает кнопку на ЭКРАНЕ 1
2. `current_work_mode` обновляется в БД
3. `current_work_mode` обновляется в FSM state
4. Футер показывает актуальный режим
5. При рестарте - режим восстанавливается из БД

```python
# Получить из БД + FSM
data = await state.get_data()
current_work_mode = data.get('current_work_mode') or (await db.get_user_work_mode(user_id))
work_mode_display = WORK_MODES.get(current_work_mode, "Выбор режима")
```

---

## 📊 РАЗЛИЧИЕ МЕЖДУ РЕЖИМОМ ГЕНЕРАЦИИ И РЕЖИМОМ РАБОТЫ

| Параметр | Режим генерации | Режим работы |
|----------|------------------|---------------|
| **Что это** | Тип сервиса (тариф) | Тип задачи |
| **Где выбирается** | Профиль/Платежи | ЭКРАН 1 |
| **Кто выбирает** | Пользователь (редко) | Пользователь (всегда) |
| **Влияет на** | Стоимость, качество | Поток работы, функции |
| **Тип данных** | STANDARD/PRO/PREMIUM | NEW_DESIGN/EDIT_DESIGN/etc |
| **Сохраняется в** | users.generation_mode | users.current_work_mode |
| **Период сохранения** | На сессию пользователя | На сессию |
| **Обновляется** | При смене пакета | При выборе на ЭКРАНЕ 1 |
| **Восстанавливается** | Автоматически из БД | Из БД при старте |

---

## 🗄️ ТРЕБУЕМЫЕ ИЗМЕНЕНИЯ БД

### ТАБЛИЦА: users

**Добавить поля:**
```sql
ALTER TABLE users ADD COLUMN generation_mode TEXT DEFAULT 'STANDARD';
ALTER TABLE users ADD COLUMN current_work_mode TEXT DEFAULT 'CHOOSING_MODE';
```

**Структура:**
```sql
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    reg_date TIMESTAMP,
    generation_mode TEXT DEFAULT 'STANDARD',        -- 🔵 НОВОЕ (режим генерации)
    current_work_mode TEXT DEFAULT 'CHOOSING_MODE'  -- 🔴 НОВОЕ (режим работы)
);
```

### ТАБЛИЦА: chat_menus

**Добавить поля для восстановления:**
```sql
ALTER TABLE chat_menus ADD COLUMN current_work_mode TEXT DEFAULT 'CHOOSING_MODE';
```

**Описание:** Дублируем `current_work_mode` для восстановления UI при рестарте бота

---

## 🔧 КОД БД (db.py)

```python
class Database:
    # ... существующие методы ...
    
    # === V3 НОВЫЕ МЕТОДЫ ===
    
    async def set_user_work_mode(self, user_id: int, work_mode: str) -> bool:
        """
        Установить режим работы пользователя.
        Вызывается при выборе режима на ЭКРАНЕ 1.
        """
        try:
            await self.execute(
                "UPDATE users SET current_work_mode = ? WHERE user_id = ?",
                (work_mode, user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting work mode: {e}")
            return False
    
    async def get_user_work_mode(self, user_id: int) -> str:
        """
        Получить текущий режим работы пользователя.
        Используется при рестарте бота для восстановления режима.
        """
        try:
            result = await self.fetch_one(
                "SELECT current_work_mode FROM users WHERE user_id = ?",
                (user_id,)
            )
            return result['current_work_mode'] if result else 'CHOOSING_MODE'
        except:
            return 'CHOOSING_MODE'
    
    async def get_user_generation_mode(self, user_id: int) -> str:
        """
        Получить режим генерации пользователя (тариф).
        Используется при формировании футера.
        """
        try:
            result = await self.fetch_one(
                "SELECT generation_mode FROM users WHERE user_id = ?",
                (user_id,)
            )
            return result['generation_mode'] if result else 'STANDARD'
        except:
            return 'STANDARD'
    
    async def set_user_generation_mode(self, user_id: int, mode: str) -> bool:
        """
        Установить режим генерации при смене тарифа.
        """
        try:
            await self.execute(
                "UPDATE users SET generation_mode = ? WHERE user_id = ?",
                (mode, user_id)
            )
            return True
        except:
            return False

    async def init_db_v3():
        """
        Инициализация БД для V3 (добавление новых колонок).
        Вызывается один раз при старте бота.
        """
        try:
            await self.execute(
                "ALTER TABLE users ADD COLUMN generation_mode TEXT DEFAULT 'STANDARD'"
            )
        except:
            pass  # Колонка уже есть
        
        try:
            await self.execute(
                "ALTER TABLE users ADD COLUMN current_work_mode TEXT DEFAULT 'CHOOSING_MODE'"
            )
        except:
            pass  # Колонка уже есть
        
        try:
            await self.execute(
                "ALTER TABLE chat_menus ADD COLUMN current_work_mode TEXT DEFAULT 'CHOOSING_MODE'"
            )
        except:
            pass  # Колонка уже есть
```

---

## 📝 КОД ТЕКСТОВ (texts.py)

```python
# === РЕЖИМЫ ГЕНЕРАЦИИ ===
GENERATION_MODES = {
    "STANDARD": "СТАНДАРТ",
    "PRO": "ПРО",
    "PREMIUM": "ПРЕМИУМ",
}

# === РЕЖИМЫ РАБОТЫ ===
WORK_MODES = {
    "CHOOSING_MODE": "Выбор режима",
    "NEW_DESIGN": "Создание",
    "EDIT_DESIGN": "Редактирование",
    "SAMPLE_DESIGN": "Примерка",
    "ARRANGE_FURNITURE": "Мебель",
    "FACADE_DESIGN": "Фасад",
}

def get_footer_text(user_balance: int, generation_mode: str, work_mode: str) -> str:
    """
    Формирует футер с ТРИ элементами для КАЖДОГО сообщения.
    
    Args:
        user_balance: Баланс пользователя (количество генераций)
        generation_mode: Режим генерации (STANDARD/PRO/PREMIUM)
        work_mode: Режим работы (NEW_DESIGN/EDIT_DESIGN/etc)
    
    Returns:
        Форматированная строка футера
    
    Пример:
        >>> get_footer_text(3, "STANDARD", "CHOOSING_MODE")
        "💰 Баланс: 3 | 🎨 Режим генерации: СТАНДАРТ | 🔧 Режим работы: Выбор режима"
    """
    gen_mode_display = GENERATION_MODES.get(generation_mode, "СТАНДАРТ")
    work_mode_display = WORK_MODES.get(work_mode, "Выбор режима")
    
    return f"💰 Баланс: {user_balance} | 🎨 Режим генерации: {gen_mode_display} | 🔧 Режим работы: {work_mode_display}"

def format_message_with_footer(header: str, content: str, footer: str) -> str:
    """
    Форматирует полное сообщение с заголовком, контентом и футером.
    
    Args:
        header: Заголовок сообщения
        content: Основное содержимое
        footer: Футер (из get_footer_text)
    
    Returns:
        Полное сообщение
    """
    return f"{header}\n\n{content}\n\n{'─' * 50}\n{footer}"
```

---

## 🎯 ПРИМЕНЕНИЕ ФУТЕРА В ОБРАБОТЧИКАХ

**ОБЩАЯ СХЕМА (применяется ко ВСЕМ экранам):**

```python
@router.callback_query(F.data == "mode_new_design")
async def mode_new_design(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    
    # 1. Обновить режим работы
    new_work_mode = "NEW_DESIGN"
    await db.set_user_work_mode(callback.from_user.id, new_work_mode)
    await state.update_data(current_work_mode=new_work_mode)
    
    # 2. Получить все данные для футера
    generation_mode = await db.get_user_generation_mode(callback.from_user.id)
    
    # 3. Сформировать футер
    footer = get_footer_text(
        user_balance=user.balance,
        generation_mode=generation_mode,
        work_mode=new_work_mode
    )
    
    # 4. Сформировать полный текст
    content = "🎨 Загрузите фото помещения для создания нового дизайна"
    text = f"{content}\n\n{'─' * 50}\n{footer}"
    
    # 5. Показать сообщение
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_upload_photo_keyboard(),
        screen_code='uploading_photo'
    )
    
    logger.info(f"USER {callback.from_user.id} | WORK_MODE: NEW_DESIGN | GENERATION_MODE: {generation_mode}")
```

---

## 📋 ЭКРАН 1: ПРИМЕНЕНИЕ ФУТЕРА

```python
@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username)
        user = await db.get_user(message.from_user.id)
    
    # Инициализировать состояние
    await state.clear()
    await state.set_state(CreationStates.choosing_mode)
    
    # На ЭКРАНЕ 1 режим работы = "CHOOSING_MODE" (выбор)
    work_mode = "CHOOSING_MODE"
    
    # Получить режим генерации
    generation_mode = await db.get_user_generation_mode(message.from_user.id)
    
    # Сформировать футер
    footer = get_footer_text(
        user_balance=user.balance,
        generation_mode=generation_mode,
        work_mode=work_mode
    )
    
    # Сформировать текст с футером
    content = "🎯 Выберите режим работы"
    text = f"{content}\n\n{'─' * 50}\n{footer}"
    
    await edit_menu(
        callback=message,
        state=state,
        text=text,
        keyboard=get_mode_selection_keyboard(is_admin=message.from_user.id in admins),
        screen_code='choosing_mode'
    )
    
    logger.info(f"USER {message.from_user.id} | CHOOSING_MODE | GENERATION_MODE: {generation_mode}")
```

---

## ✅ ЧЕК-ЛИСТ РЕАЛИЗАЦИИ

### ФАЗА 1: БД
- [ ] Добавить `generation_mode` в таблицу `users`
- [ ] Добавить `current_work_mode` в таблицу `users`
- [ ] Добавить `current_work_mode` в таблицу `chat_menus`
- [ ] Создать функцию `init_db_v3()` в `db.py`
- [ ] Добавить методы `set_user_work_mode()`, `get_user_work_mode()`, `get_user_generation_mode()`, `set_user_generation_mode()`

### ФАЗА 2: ТЕКСТЫ
- [ ] Добавить `GENERATION_MODES` словарь
- [ ] Добавить `WORK_MODES` словарь
- [ ] Добавить функцию `get_footer_text()`
- [ ] Добавить функцию `format_message_with_footer()`

### ФАЗА 3: ОБРАБОТЧИКИ
- [ ] Обновить `cmd_start()` - использовать footers
- [ ] Обновить все 5 обработчиков режимов - использовать footers
- [ ] Обновить `back_to_main_menu()` - использовать footers
- [ ] Добавить логирование с 2 режимами

### ФАЗА 4: ТЕСТИРОВАНИЕ
- [ ] /start показывает все ТРИ элемента в футере
- [ ] Баланс отображается правильно
- [ ] Режим генерации отображается (по умолчанию СТАНДАРТ)
- [ ] Режим работы = "Выбор режима" на ЭКРАНЕ 1
- [ ] При выборе режима - режим работы обновляется
- [ ] Режим работы сохраняется в БД
- [ ] При рестарте - режим восстанавливается из БД
- [ ] Футер видно на ВСЕХ экранах

---

## 🎯 КРИТИЧНЫЕ ТРЕБОВАНИЯ

**🔴 ОБЯЗАТЕЛЬНО:**
1. Футер с ТРИ элементами на КАЖДОМ сообщении
2. Баланс из `users.balance`
3. Режим генерации из `users.generation_mode`
4. Режим работы из `users.current_work_mode`
5. Режим работы сохраняется в БД при выборе
6. Режим работы восстанавливается из БД при рестарте
7. БЕЗ миграций - только ALTER TABLE

---

**Обновлено:** 2025-12-28 01:13  
**Статус:** ✅ ГОТОВО К РЕАЛИЗАЦИИ (С УЧЁТОМ 3 ЭЛЕМЕНТОВ ФУТЕРА)  
**Время реализации:** 2-3 часа  
