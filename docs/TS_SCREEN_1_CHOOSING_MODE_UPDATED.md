# 🔴 КРИТИЧЕСКОЕ ОБНОВЛЕНИЕ ТЗ ЭКРАНА 1 - FOOTER + БД АНАЛИЗ

**Версия:** 2.0 - ИСПРАВЛЕННАЯ  
**Дата:** 2025-12-28 01:09  
**Статус:** 🔴 КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ  

---

## ⚠️ КРИТИЧЕСКИЕ УПУЩЕНИЯ В ТЗ 1.0

### ОШИБКА 1: РЕЖИМ НЕ В ФУТЕРЕ (КРИТИЧНАЯ!)

**Что НЕ учтено в ТЗ 1.0:**
```
❌ ЭКРАН 1.0 ТЗ:
- Режим НЕ показывается в футере
- Баланс есть в начале текста, но НЕ в каждом сообщении
- Нет системы обновления текста с режимом во ВСЕХ экранах

✅ ТЕКУЩАЯ РЕАЛЬНОСТЬ (на скриншоте):
- ФУТЕР имеет ДВА значения:
  ┌─────────────────────────────┐
  │ Баланс: 3 | Режим: СТАНДАРТ │
  └─────────────────────────────┘
- Это ЕДИНОЕ поле в футере каждого сообщения
- РЕЖИМ отображается ВСЕГДА рядом с баланс
- РЕЖИМ ОБНОВЛЯЕТСЯ динамически
```

### ОШИБКА 2: БД АНАЛИЗ ОТСУТСТВУЕТ

**В ТЗ 1.0 НЕ ОПИСАНО:**
- Где хранится текущий режим пользователя
- Нужны ли новые таблицы БД
- Как обновляется режим при переключении

---

## 📊 АНАЛИЗ БАЗЫ ДАННЫХ

### ТЕКУЩАЯ СТРУКТУРА (V1)

```sql
-- Таблица пользователей
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    reg_date TIMESTAMP,
    -- ОТСУТСТВУЕТ: current_mode field! ⚠️
);

-- Таблица сохранённого меню (SMP)
CREATE TABLE chat_menus (
    chat_id INTEGER,
    user_id INTEGER,
    menu_message_id INTEGER,
    screen_code TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
    -- ОТСУТСТВУЕТ: current_mode field! ⚠️
);

-- Таблица генераций (если есть)
CREATE TABLE generations (
    generation_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    photo_id TEXT,
    room_type TEXT,
    style_type TEXT,
    result_photo TEXT,
    created_at TIMESTAMP,
    -- ОТСУТСТВУЕТ: generation_mode field! ⚠️
);
```

### ТРЕБУЕМЫЕ ИЗМЕНЕНИЯ БД (БЕЗ МИГРАЦИЙ)

#### ОПЦИЯ 1: ДОБАВИТЬ КОЛОННЫ К СУЩЕСТВУЮЩИМ ТАБЛИЦАМ (РЕКОМЕНДУЕТСЯ)

**А) Таблица users**
```sql
-- ДОБАВИТЬ КОЛОННУ (если её нет):
ALTER TABLE users ADD COLUMN current_mode TEXT DEFAULT 'NEW_DESIGN';

-- Или создать таблицу заново (если её нет):
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    reg_date TIMESTAMP,
    current_mode TEXT DEFAULT 'NEW_DESIGN'  -- ✅ НОВОЕ
);
```

**Назначение:**
- Хранит ТЕКУЩИЙ режим пользователя
- Сохраняется при выборе режима на ЭКРАНЕ 1
- Используется для формирования ФУТЕРА
- Используется в логировании

**Пример:**
```
user_id=123456
username="test_user"
balance=10
current_mode="SAMPLE_DESIGN"  -- ✅ НОВОЕ
reg_date="2025-12-28 00:00:00"
```

**Б) Таблица chat_menus**
```sql
-- ОБНОВИТЬ (добавить колонну):
ALTER TABLE chat_menus ADD COLUMN current_mode TEXT DEFAULT 'NEW_DESIGN';

-- Или переоздать с новой структурой:
CREATE TABLE IF NOT EXISTS chat_menus (
    chat_id INTEGER,
    user_id INTEGER,
    menu_message_id INTEGER,
    screen_code TEXT,
    current_mode TEXT DEFAULT 'NEW_DESIGN'  -- ✅ НОВОЕ (дублируем из users)
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Назначение:**
- Резервное хранилище режима (восстановление после перезапуска)
- Помогает воссоздать ФУТЕР после перезапуска бота
- Используется в логировании

**В) Таблица generations (если есть, или создать)**
```sql
CREATE TABLE IF NOT EXISTS generations (
    generation_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    mode TEXT DEFAULT 'NEW_DESIGN',  -- ✅ НОВОЕ
    photo_id TEXT,
    room_type TEXT,
    style_type TEXT,
    result_photo TEXT,
    created_at TIMESTAMP
);
```

**Назначение:**
- Аудит: в каком режиме была сделана генерация
- Статистика: какие режимы используются чаще
- Восстановление: какие режимы были активны для пользователя

#### ОПЦИЯ 2: ИСПОЛЬЗОВАТЬ JSON В СУЩЕСТВУЮЩЕЙ ТАБЛИЦЕ (АЛЬТЕРНАТИВА)

```sql
-- Если БД не поддерживает ALTER, сохранять режим в JSON в meta field:
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    reg_date TIMESTAMP,
    meta TEXT  -- JSON: {"current_mode": "NEW_DESIGN", "last_mode_change": "2025-12-28 01:09"}
);

-- В Python коде:
import json
meta = json.loads(user.meta or '{}')
current_mode = meta.get('current_mode', 'NEW_DESIGN')
```

### ИТОГОВАЯ РЕКОМЕНДАЦИЯ

**✅ ИСПОЛЬЗУЙ ОПЦИЮ 1 (ДОБАВИТЬ КОЛОННЫ)** 
- ВСЕ таблицы БД поддерживают ALTER TABLE
- БЕЗ МИГРАЦИЙ (просто добавляем колонны)
- В Python коде используем с DEFAULT значениями
- Если колонна уже есть - скрипт просто её пропустит

**Скрипт инициализации БД (в db.py):**
```python
async def init_db():
    """Инициализировать БД с колонками для V3"""
    try:
        # Попытка добавить колонну (если её нет, будет ошибка, которую пропустим)
        await db.execute(
            "ALTER TABLE users ADD COLUMN current_mode TEXT DEFAULT 'NEW_DESIGN'"
        )
    except Exception as e:
        # Колонна уже есть - игнорируем ошибку
        pass
    
    try:
        await db.execute(
            "ALTER TABLE chat_menus ADD COLUMN current_mode TEXT DEFAULT 'NEW_DESIGN'"
        )
    except:
        pass

# Вызывать при запуске бота:
async def main():
    await init_db()
    # ... запуск бота
```

---

## 🎨 ДИНАМИЧЕСКИЙ ТЕКСТ ФУТЕРА

### СТРУКТУРА ФУТЕРА (ВСЕ ЭКРАНЫ V3)

**На скриншоте видно:**
```
┌──────────────────────────────────┐
│ Баланс: 3 | Режим: СТАНДАРТ       │  ← ФУТЕР
└──────────────────────────────────┘
```

**СТРУКТУРА в коде:**
```python
# ФОРМУЛА ДЛЯ ВСЕХ ЭКРАНОВ:
footer_text = f"💰 Баланс: {user.balance} | 🔧 Режим: {MODE_TITLES[current_mode]}"

# Где:
# user.balance = текущий баланс из БД
# current_mode = из FSM state или БД (NEW_DESIGN / EDIT_DESIGN / etc)
# MODE_TITLES = словарь (уже в ТЗ 1.0):
MODE_TITLES = {
    "NEW_DESIGN": "Создание",
    "EDIT_DESIGN": "Редактирование",
    "SAMPLE_DESIGN": "Примерка",
    "ARRANGE_FURNITURE": "Мебель",
    "FACADE_DESIGN": "Фасад"
}
```

### ИСПОЛЬЗОВАНИЕ ФУТЕРА ВО ВСЕХ СООБЩЕНИЯХ

**В каждом text сообщении:**
```python
# СХЕМА (применяется везде):
text = f"""
{header}  # Основной контент экрана

─────────────────────────────────
💰 Баланс: {user.balance} | 🔧 Режим: {MODE_TITLES[current_mode]}
"""

# Примеры:

# ЭКРАН 1 (CHOOSING_MODE):
text = f"""
🎨 Выберите режим работы

─────────────────────────────────
💰 Баланс: {user.balance} | 🔧 Режим: Выбор режима
"""

# ЭКРАН 2 (UPLOADING_PHOTO):
text = f"""
📸 Загрузите фото помещения

─────────────────────────────────
💰 Баланс: {user.balance} | 🔧 Режим: {MODE_TITLES[current_mode]}
"""

# ЭКРАН 3 (ROOM_CHOICE):
text = f"""
🏠 Выберите тип помещения

─────────────────────────────────
💰 Баланс: {user.balance} | 🔧 Режим: {MODE_TITLES[current_mode]}
"""
```

### ДИНАМИЧЕСКОЕ ОБНОВЛЕНИЕ

**Когда пользователь выбирает режим на ЭКРАНЕ 1:**
```python
@router.callback_query(F.data == "mode_new_design")
async def mode_new_design(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    
    # ✅ СОХРАНЯЕМ режим в 2 места:
    # 1. FSM state (на сессию)
    await state.update_data(current_mode="NEW_DESIGN")
    
    # 2. БД (на постоянно)
    await db.execute(
        "UPDATE users SET current_mode = ? WHERE user_id = ?",
        ("NEW_DESIGN", callback.from_user.id)
    )
    
    # ✅ ФОРМИРУЕМ текст с ФУТЕРОМ:
    text = f"""
🎨 Загрузите фото помещения для создания нового дизайна

─────────────────────────────────
💰 Баланс: {user.balance} | 🔧 Режим: {MODE_TITLES['NEW_DESIGN']}
"""
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,  # ✅ ТЕКСТ С ФУТЕРОМ
        keyboard=get_upload_photo_keyboard(),
        screen_code='uploading_photo'
    )
```

---

## 📝 ОБНОВЛЁННАЯ МАТРИЦА БД

| Таблица | Колонна | Тип | Назначение | Статус |
|---------|---------|-----|-----------|--------|
| **users** | user_id | INTEGER | PK | ✅ Существует |
| | username | TEXT | Имя | ✅ Существует |
| | balance | INTEGER | Баланс генераций | ✅ Существует |
| | reg_date | TIMESTAMP | Дата регистрации | ✅ Существует |
| | **current_mode** | TEXT | **НОВОЕ**: Текущий режим | 🔴 **ДОБАВИТЬ** |
| **chat_menus** | chat_id | INTEGER | Чат пользователя | ✅ Существует |
| | user_id | INTEGER | Пользователь | ✅ Существует |
| | menu_message_id | INTEGER | ID меню сообщения | ✅ Существует |
| | screen_code | TEXT | Код экрана | ✅ Существует |
| | **current_mode** | TEXT | **НОВОЕ**: Режим (бэкап) | 🔴 **ДОБАВИТЬ** |
| | created_at | TIMESTAMP | Время создания | ✅ Существует |
| | updated_at | TIMESTAMP | Время обновления | ✅ Существует |
| **generations** | generation_id | INTEGER | PK | ✅ Если существует |
| | user_id | INTEGER | Пользователь | ✅ Если существует |
| | **mode** | TEXT | **НОВОЕ**: Режим при генерации | 🔴 **ДОБАВИТЬ** |
| | photo_id | TEXT | Исходная фото | ✅ Если существует |
| | result_photo | TEXT | Результат | ✅ Если существует |
| | created_at | TIMESTAMP | Время | ✅ Если существует |

---

## 🔧 КОД БД.PY (НОВЫЕ МЕТОДЫ)

**ДОБАВИТЬ в bot/database/db.py:**

```python
class Database:
    # ... существующие методы ...
    
    # === V3 НОВЫЕ МЕТОДЫ ===
    
    async def set_user_mode(self, user_id: int, mode: str) -> bool:
        """
        Установить текущий режим пользователя.
        
        Args:
            user_id: ID пользователя
            mode: Режим (NEW_DESIGN, EDIT_DESIGN, etc)
        
        Returns:
            True если успешно
        """
        try:
            await self.execute(
                "UPDATE users SET current_mode = ? WHERE user_id = ?",
                (mode, user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting user mode: {e}")
            return False
    
    async def get_user_mode(self, user_id: int) -> str:
        """
        Получить текущий режим пользователя.
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Режим или 'NEW_DESIGN' по умолчанию
        """
        try:
            result = await self.fetch_one(
                "SELECT current_mode FROM users WHERE user_id = ?",
                (user_id,)
            )
            return result['current_mode'] if result else 'NEW_DESIGN'
        except:
            return 'NEW_DESIGN'
    
    async def update_chat_menu_mode(
        self,
        chat_id: int,
        menu_message_id: int,
        mode: str
    ) -> bool:
        """
        Обновить режим в таблице chat_menus.
        
        Args:
            chat_id: ID чата
            menu_message_id: ID меню сообщения
            mode: Режим
        
        Returns:
            True если успешно
        """
        try:
            await self.execute(
                "UPDATE chat_menus SET current_mode = ? WHERE chat_id = ? AND menu_message_id = ?",
                (mode, chat_id, menu_message_id)
            )
            return True
        except:
            return False
    
    async def log_generation_mode(
        self,
        user_id: int,
        mode: str,
        room_type: str = None,
        style_type: str = None
    ) -> bool:
        """
        Логировать генерацию с режимом.
        
        Args:
            user_id: ID пользователя
            mode: Режим генерации
            room_type: Тип комнаты (если есть)
            style_type: Тип стиля (если есть)
        
        Returns:
            True если успешно
        """
        try:
            await self.execute(
                """INSERT INTO generations (user_id, mode, room_type, style_type, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, mode, room_type, style_type, datetime.now())
            )
            return True
        except:
            return False
```

---

## 🔄 ОБНОВЛЁННЫЙ ПОТОК ЭКРАНА 1

**НОВАЯ ЛОГИКА с ФУТЕРОМ:**

```
1. /start
   ↓
2. cmd_start() вызывается
   ├─ Получить user из БД
   ├─ Получить текущий mode из БД (или 'NEW_DESIGN' по умолчанию)
   ├─ Инициализировать FSM:
   │  ├─ current_mode = None (пока не выбран)
   │  ├─ menu_message_id = None
   │  └─ photos = {}
   ├─ Установить state = CreationStates.choosing_mode
   └─ ОТОБРАЗИТЬ ЭКРАН 1:
      ├─ Основной текст: "Выберите режим работы"
      └─ ФУТЕР: "💰 Баланс: {balance} | 🔧 Режим: Выбор режима"
   ↓
3. Пользователь нажимает одну из 5 кнопок режима
   ├─ Например: "mode_new_design"
   ↓
4. mode_new_design() обработчик:
   ├─ Обновить FSM: current_mode = "NEW_DESIGN"
   ├─ Обновить БД: users.current_mode = "NEW_DESIGN"
   ├─ Обновить FSM: current_mode в state
   ├─ Установить state = CreationStates.new_design_upload_photo
   └─ ОТОБРАЗИТЬ ЭКРАН 2:
      ├─ Основной текст: "Загрузите фото помещения"
      └─ ФУТЕР: "💰 Баланс: {balance} | 🔧 Режим: Создание" ✅
   ↓
5. Все последующие экраны показывают АКТУАЛЬНЫЙ режим в ФУТЕРЕ
```

---

## ✅ ИТОГОВЫЙ ЧЕК-ЛИСТ ОБНОВЛЕНИЯ

### ШАГИ РЕАЛИЗАЦИИ:

- [ ] **ШАГ 1: БД ИНИЦИАЛИЗАЦИЯ** (5 мин)
  - [ ] Добавить колонну `current_mode` в таблицу `users`
  - [ ] Добавить колонну `current_mode` в таблицу `chat_menus`
  - [ ] Добавить колонну `mode` в таблицу `generations` (если существует)
  - [ ] Создать функцию `init_db()` в db.py
  - [ ] Вызвать `init_db()` при запуске бота

- [ ] **ШАГ 2: ДОБАВИТЬ МЕТОДЫ БД** (10 мин)
  - [ ] Добавить `set_user_mode()` в db.py
  - [ ] Добавить `get_user_mode()` в db.py
  - [ ] Добавить `update_chat_menu_mode()` в db.py
  - [ ] Добавить `log_generation_mode()` в db.py

- [ ] **ШАГ 3: ОБНОВИТЬ ТЕКСТЫ** (10 мин)
  - [ ] Добавить переменную для ФУТЕРА (или создать функцию)
  - [ ] Обновить ВСЕ `text = f"..."` с ФУТЕРОМ
  - [ ] Проверить, что footer используется везде

- [ ] **ШАГ 4: ОБНОВИТЬ ОБРАБОТЧИКИ** (15 мин)
  - [ ] cmd_start() - получить и показать режим
  - [ ] mode_new_design() - сохранить режим в БД и FSM
  - [ ] mode_edit_design() - сохранить режим в БД и FSM
  - [ ] mode_sample_design() - сохранить режим в БД и FSM
  - [ ] mode_arrange_furniture() - сохранить режим в БД и FSM
  - [ ] mode_facade_design() - сохранить режим в БД и FSM

- [ ] **ШАГ 5: ОБНОВИТЬ EDIT_MENU()** (5 мин)
  - [ ] Убедиться, что ФУТЕР передаётся в text параметре
  - [ ] Проверить, что режим обновляется на каждый экран

- [ ] **ШАГ 6: ЛОГИРОВАНИЕ** (5 мин)
  - [ ] Добавить logger.info с режимом
  - [ ] Формат: `"USER {id} | {MODE}+{SCREEN} | Action"`

- [ ] **ШАГ 7: ТЕСТИРОВАНИЕ** (30 мин)
  - [ ] /start показывает баланс и режим в футере
  - [ ] Выбор режима обновляет футер
  - [ ] Режим сохраняется в БД (проверить SELECT)
  - [ ] При перезапуске бота режим восстанавливается
  - [ ] Single Menu Pattern работает
  - [ ] Логирование показывает режимы

---

## 📌 КРИТИЧНЫЕ МОМЕНТЫ

**🔴 ОБЯЗАТЕЛЬНО:**
1. РЕЖИМ В ФУТЕРЕ **КАЖДОГО** СООБЩЕНИЯ (не только на ЭКРАНЕ 1!)
2. РЕЖИМ СОХРАНЯЕТСЯ В БД при выборе
3. РЕЖИМ ВОССТАНАВЛИВАЕТСЯ из БД при перезапуске бота
4. РЕЖИМ ЛОГИРУЕТСЯ (MODE+SCREEN)
5. БЕЗ МИГРАЦИЙ - только ALTER TABLE

**🟡 ВАЖНО:**
- Обновить ТЕ образцы get_mode_header() для показа режима в футере
- Убедиться, что все 5 обработчиков режимов работают одинаково
- Проверить, что режим НЕ сбрасывается при /start (сохраняется)

---

**Обновлено:** 2025-12-28 01:09  
**Статус:** ✅ ГОТОВО К РЕАЛИЗАЦИИ (С УЧЁТОМ ФУТЕРА И БД)  
**Время реализации:** 2-3 часа  
