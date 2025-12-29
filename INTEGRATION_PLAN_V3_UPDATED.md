# 📋 ПОНУПЛЕННОЕ ТЗ: НОВЫЕ ТРЕБОВАНИЯ К FOOTER

**Дата обновления:** 28.12.2025 10:06  
**Фокус:** КОНТРОЛЬ НА FOOTER
**Статус:** ОТКОРРЕКТИРОВАНО

---

## 📄 КОНТРОЛЬНОЕ ТРЕБОВАНИЕ

### НА КАЖДОМ ЭКРАНЕ В ФУТЕРЕ ДОЛЖНЫ БЫТЬ 3 ПАРАМЕТРА:

```
────────────────────────────────────────────
💰 Баланс: 15 | 🔧 PRO | 📝 NEW DESIGN
```

### Расшифровка 3 параметров:

| # | Параметр | Значение | Где хранится | Пример |
|---|----------|----------|--------------|--------|
| 1️⃣ | **БАЛАНС** ✅ (существует) | Количество генераций | БД + FSM | `Баланс: 15` |
| 2️⃣ | **РЕЖИМ ГЕНЕРАЦИИ** ✅ (существует) | PRO / СТАНДАРТ | БД (pro_settings) | `🔧 PRO` или `📋 СТАНДАРТ` |
| 3️⃣ | **ВЫБОР РЕЖИМА РАБОТЫ** 🔥 (НОВОЕ!) | new_design, edit_design, sample_design, arrange_furniture, facade_design | FSM `state.data['work_mode']` | `📝 NEW DESIGN` или `✏️ EDIT` |

---

## 🔧 НАЙДЕННАЯ ФУНКЦИЯ ДЛЯ FOOTER

**Файл:** `bot/utils/helpers.py`

**Функция:** `async def add_balance_and_mode_to_text(text: str, user_id: int, work_mode: str = None) -> str`

### ДО изменений (V2):
```python
# Было: 2 параметра
footer = f"\n\n{separator}\nБаланс: {balance} | Режим: {mode_icon} {mode_name}"
```

### ПОСЛЕ изменений (V3) 🔥:
```python
# Стало: 3 параметра!
footer = f"\n\n{separator}\n💰 Баланс: {balance} | {mode_icon} {mode_name} | {work_mode_display}"
```

### Что было добавлено:

```python
# ===== СЛОВАРЬ ДЛЯ ОТОБРАЖЕНИЯ РЕЖИМОВ РАБОТЫ =====
WORK_MODE_DISPLAY = {
    "new_design": "📝 NEW DESIGN",
    "edit_design": "✏️ EDIT",
    "sample_design": "🎨 SAMPLE",
    "arrange_furniture": "🛋️ FURNITURE",
    "facade_design": "🏠 FACADE",
    None: "❓ UNKNOWN",
}

# ===== НОВЫЙ ПАРАМЕТР В ФУНКЦИИ =====
async def add_balance_and_mode_to_text(
    text: str,
    user_id: int,
    work_mode: str = None  # 🔥 НОВЫЙ ПАРАМЕТР!
) -> str:
    # ...
    work_mode_display = WORK_MODE_DISPLAY.get(work_mode, WORK_MODE_DISPLAY[None])
    footer = f"\n\n{separator}\n💰 Баланс: {balance} | {mode_icon} {mode_name} | {work_mode_display}"
```

---

## 📋 ПРАВИЛА ИСПОЛЬЗОВАНИЯ ФУНКЦИИ В ОБРАБОТЧИКАХ

### ❌ НЕПРАВИЛЬНО (V2 - старый способ):
```python
text = CHOOSE_STYLE_TEXT.format(balance=balance)
# footer вычисляется автоматически, но БЕЗ режима работы
```

### ✅ ПРАВИЛЬНО (V3 - новый способ):
```python
# 1. Получаем режим из FSM
data = await state.get_data()
work_mode = data.get('work_mode')  # 'new_design', 'edit_design', и т.д.

# 2. Создаем текст БЕЗ footer'а
text = CHOOSE_STYLE_TEXT.format(
    balance=balance,
    current_mode=work_mode,
    selected_room=room
)

# 3. КРИТИЧНО: Добавляем footer через функцию с 3 параметрами!
text = await add_balance_and_mode_to_text(
    text=text,
    user_id=user_id,
    work_mode=work_mode  # 🔥 ОБЯЗАТЕЛЬНО ПЕРЕДАВАТЬ!
)

# 4. Отправляем текст с footer'ом
await edit_menu(
    callback=callback,
    state=state,
    text=text,  # Уже содержит footer!
    keyboard=keyboard,
    screen_code='choose_style_1'
)
```

---

## 🔥 КРИТИЧНЫЕ ИЗМЕНЕНИЯ В `creation_v3.py`

### ВСЕ обработчики должны следовать этому паттерну:

```python
@router.callback_query(F.data == "some_handler")
async def some_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    work_mode = data.get('work_mode')  # 🔥 ПОЛУЧИТЬ РЕЖИМ!
    
    # ... основная логика ...
    
    text = SOME_TEXT.format(
        balance=balance,
        current_mode=work_mode  # Если нужен в самом тексте
    )
    
    # 🔥 КРИТИЧНО: Добавляем footer с 3 параметрами!
    text = await add_balance_and_mode_to_text(
        text=text,
        user_id=user_id,
        work_mode=work_mode  # ОБЯЗАТЕЛЬНО!
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=text,  # Уже с footer'ом!
        keyboard=keyboard,
        screen_code='some_screen'
    )
```

---

## 📊 ТАБЛИЦА ОБРАБОТЧИКОВ И FOOTER

| Обработчик | Экран | Получает work_mode | Добавляет footer | Вызывает функцию |
|---|---|---|---|---|
| `select_mode()` | SCREEN 1 (MAIN_MENU) | ❌ Нет (это выбор режима) | ❌ Нет | ❌ Нет |
| `set_work_mode()` | -> UPLOADING_PHOTO | ✅ Да | ✅ Да | ✅ Да |
| `photo_handler()` | SCREEN 2 | ✅ Да | ✅ Да | ✅ Да |
| `room_choice_menu()` | SCREEN 3 | ✅ Да | ✅ Да | ✅ Да |
| `room_choice_handler()` | -> CHOOSE_STYLE | ✅ Да | ✅ Да | ✅ Да |
| `choose_style_1_menu()` | SCREEN 4 | ✅ Да | ✅ Да | ✅ Да |
| `choose_style_2_menu()` | SCREEN 5 | ✅ Да | ✅ Да | ✅ Да |
| `style_choice_handler()` | -> POST_GENERATION | ✅ Да | ✅ Да | ✅ Да |
| `post_generation_menu()` | SCREEN 6 | ✅ Да | ✅ Да | ✅ Да |
| `text_input_menu()` | SCREEN 7 | ✅ Да | ✅ Да | ✅ Да |
| `text_input_handler()` | -> POST_GENERATION | ✅ Да | ✅ Да | ✅ Да |
| `edit_design_menu()` | SCREEN 8 | ✅ Да | ✅ Да | ✅ Да |
| `clear_confirm_menu()` | SCREEN 9 | ✅ Да | ✅ Да | ✅ Да |
| ... | ... | ... | ... | ... |

---

## 📝 ПРИМЕР ЭКРАНА С FOOTER'ОМ

### Экран 4: CHOOSE_STYLE_1 (режим NEW_DESIGN)

```
🎨 Выберите стиль дизайна

Современный | Минимализм
Скандинавский | Индустриальный
...
⬅️ К комнате | 🏠 Главное меню | ▶️ Ещё

────────────────────────────────────────────
💰 Баланс: 15 | 🔧 PRO | 📝 NEW DESIGN
```

### Экран 8: EDIT_DESIGN (режим EDIT_DESIGN)

```
✏️ Выберите действие для редактирования

🗹️ Очистить фото | 📏 Ввести текст
⬅️ Новое фото | 🏠 Главное меню

────────────────────────────────────────────
💰 Баланс: 14 | 📋 СТАНДАРТ | ✏️ EDIT
```

---

## 🔄 ИМПОРТЫ В `creation_v3.py`

**ДОБАВИТЬ в начало файла:**

```python
from bot.utils.helpers import add_balance_and_mode_to_text  # 🔥 НОВОЕ!
```

---

## ✅ ЧЕКЛИСТ ДЛЯ РАЗРАБОТЧИКОВ

При реализации V3 проверить:

- [ ] `bot/utils/helpers.py` обновлена с новым параметром `work_mode` ✅ (СДЕЛАНО)
- [ ] В `creation_v3.py` импортирована функция `add_balance_and_mode_to_text`
- [ ] Все обработчики получают `work_mode` из `state.data`
- [ ] Все обработчики вызывают `add_balance_and_mode_to_text()` перед `edit_menu()`
- [ ] Footer показывает ВСЕ 3 параметра на каждом экране
- [ ] Emoji выглядят правильно (без квадратиков)
- [ ] Экран 1 (MAIN_MENU) выбора режима - НЕ имеет footer'а (это логично)
- [ ] Все остальные 17 экранов - ИМЕЮТ footer с 3 параметрами
- [ ] Логирование отражает режим работы

---

## 🎯 ИТОГ

**Что изменилось:**
- ✅ Функция `add_balance_and_mode_to_text()` теперь принимает 3-й параметр `work_mode`
- ✅ Footer теперь выглядит: `💰 Баланс: X | 🔧 MODE | 📝 WORK_MODE`
- ✅ Все 3 параметра отображаются в футере КАЖДОГО ЭКРАНА (кроме SCREEN 1)
- ✅ Работает для всех 5 режимов: NEW_DESIGN, EDIT_DESIGN, SAMPLE_DESIGN, ARRANGE_FURNITURE, FACADE_DESIGN

**Файл уже исправлен:** `bot/utils/helpers.py` ✅

**Осталось в `creation_v3.py`:**
- Добавить импорт
- Обновить ВСЕ обработчики чтобы вызывали эту функцию с `work_mode`

---

**ГОТОВО К РЕАЛИЗАЦИИ!** 🚀
