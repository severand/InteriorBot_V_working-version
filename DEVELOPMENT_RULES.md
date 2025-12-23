# ПРАВИЛА РАЗРАБОТКИ InteriorBot

**Дата создания:** 2025-12-06  
**Последнее обновление:** 2025-12-06

---

## 🚨 КРИТИЧЕСКИЕ ПРАВИЛА НАВИГАЦИИ

### ⚠️ ПРАВИЛО #1: state.clear() vs state.set_state(None)

**ПРОБЛЕМА:**  
Использование `state.clear()` при навигации между меню приводит к потере `menu_message_id`, что вызывает создание новых сообщений внизу чата вместо редактирования существующего.

**РЕШЕНИЕ:**

#### ✅ ПРАВИЛЬНО - Навигация между меню:
```python
# При переходах между экранами (админка, настройки, профиль и т.д.)
await state.set_state(None)  # Сбрасывает ТОЛЬКО состояние FSM, данные остаются
```

#### ❌ НЕПРАВИЛЬНО - НЕ использовать при навигации:
```python
# НЕ ДЕЛАТЬ ТАК при навигации!
await state.clear()  # Удаляет ВСЁ: состояние + данные (включая menu_message_id)
```

#### ✅ ПРАВИЛЬНО - Полный сброс:
```python
# ТОЛЬКО при полном сбросе (команда /start, выход из бота)
await state.clear()  # Очищает всё
```

---

### 📋 КОГДА ЧТО ИСПОЛЬЗОВАТЬ

| Ситуация | Метод | Причина |
|----------|-------|---------||
| Переход между меню (главное → профиль) | `state.set_state(None)` | Сохраняет `menu_message_id` |
| Переход в админ-панель | `state.set_state(None)` | Сохраняет `menu_message_id` |
| Переход в настройки | `state.set_state(None)` | Сохраняет `menu_message_id` |
| Возврат в главное меню | `state.set_state(None)` | Сохраняет `menu_message_id` |
| Команда `/start` | `state.clear()` | Полный сброс сессии |
| Отмена операции FSM | `state.clear()` | Полный сброс состояния |

---

### 🎯 ОБЯЗАТЕЛЬНОЕ СОХРАНЕНИЕ menu_message_id

**Критическая переменная:** `menu_message_id`

Эта переменная хранит ID главного сообщения меню. **Она НЕ должна теряться** при навигации!

#### ✅ ПРАВИЛЬНЫЙ ПАТТЕРН:

```python
@router.callback_query(F.data == "some_menu")
async def show_some_menu(callback: CallbackQuery, state: FSMContext):
    # 1. Сбрасываем ТОЛЬКО состояние FSM
    await state.set_state(None)
    
    # 2. menu_message_id автоматически сохраняется!
    # НЕ нужно его явно восстанавливать
    
    # 3. Используем edit_menu() для редактирования
    await edit_menu(
        callback=callback,
        state=state,
        text="Текст меню",
        keyboard=get_keyboard()
    )
```

#### ❌ НЕПРАВИЛЬНЫЙ ПАТТЕРН:

```python
@router.callback_query(F.data == "some_menu")
async def show_some_menu(callback: CallbackQuery, state: FSMContext):
    # ❌ ОШИБКА: state.clear() удалит menu_message_id!
    await state.clear()
    
    # Результат: menu_message_id потерян → создастся новое сообщение внизу
```

---

## 🛠️ ФУНКЦИЯ edit_menu()

**Всегда используйте** функцию `edit_menu()` из `utils.navigation` для редактирования меню!

```python
from utils.navigation import edit_menu

await edit_menu(
    callback=callback,
    state=state,
    text="Текст меню",
    keyboard=get_keyboard(),
    show_balance=True  # Автоматически добавит баланс
)
```

**НЕ используйте** прямое редактирование через `callback.message.edit_text()` - это может привести к потере menu_message_id!

---

## 🔍 ОТЛАДКА ПРОБЛЕМ С НАВИГАЦИЕЙ

Если появляются новые сообщения внизу вместо редактирования:

### Шаг 1: Добавьте логи
```python
data = await state.get_data()
logger.warning(f"🔍 [DEBUG] menu_message_id={data.get('menu_message_id')}")
```

### Шаг 2: Найдите место потери ID
Ищите в коде:
- `await state.clear()` - потенциальная причина
- Прямые вызовы `callback.message.edit_text()` вместо `edit_menu()`

### Шаг 3: Исправьте
Замените `state.clear()` на `state.set_state(None)` в местах навигации.

---

## 📊 ИСТОРИЯ ИСПРАВЛЕНИЙ

### 2025-12-06: Исправлена потеря menu_message_id
**Проблема:** При переходе Админ-панель → Настройки → Назад → Главное меню создавалось новое сообщение.

**Файлы:**
- `bot/handlers/admin.py` - функция `show_admin_settings()`
- `bot/handlers/admin.py` - функция `show_admin_panel()`

**Исправление:**
```python
# Было
await state.clear()

# Стало
await state.set_state(None)
```

**Метод обнаружения:** Детальное логирование на каждом этапе навигации выявило, что `state.clear()` в функции `show_admin_settings()` удаляла `menu_message_id`.

---

## 🚀 ЧЕКЛИСТ ДЛЯ ПРОВЕРКИ ПЕРЕД КОММИТОМ

- [ ] Все переходы между меню используют `state.set_state(None)`
- [ ] `state.clear()` используется ТОЛЬКО при полном сбросе
- [ ] Все редактирования меню через `edit_menu()`
- [ ] Добавлены логи для отладки (если нужно)
- [ ] Проверено вручную: нет новых сообщений при навигации

---

## 📞 КОНТАКТЫ

При возникновении вопросов или обнаружении нарушений этих правил - немедленно исправляйте и обновляйте документацию!

**Эти правила обязательны для всех разработчиков и ИИ-ассистентов!**

---

## 🤖 ДЛЯ ИИ-АССИСТЕНТОВ

При работе с этим проектом:

1. **ВСЕГДА** читайте этот файл перед внесением изменений в навигацию
2. **НИКОГДА** не используйте `state.clear()` при переходах между меню
3. **ВСЕГДА** проверяйте, что `menu_message_id` сохраняется
4. **ВСЕГДА** используйте функцию `edit_menu()` для редактирования
5. При сомнениях - добавьте логи и проверьте поведение

**Запомните:** Один неправильный `state.clear()` может испортить всю навигацию!


### ✅ Паттерн: Поиск пользователя с редактированием единого меню

Получаем menu_message_id из БД (НЕ из FSM!)

menu_info = await db.get_chat_menu(chat_id)

if menu_info and menu_info.get('menu_message_id'):
# Редактируем существующее меню
await message.bot.edit_message_text(
chat_id=chat_id,
message_id=menu_info['menu_message_id'],
text=result_text,
reply_markup=keyboard,
parse_mode="Markdown"
)
# Сохраняем screen_code
await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'screen_code')

text
undefined
****************************************************************

Отлично! 🎯 Вот **критически важные паттерны**, которые нужно добавить в `DEVELOPMENT_RULES.md`:

***

## 📚 **ПАТТЕРНЫ ДЛЯ DEVELOPMENT_RULES.md**

```markdown
## 🎯 ПАТТЕРНЫ РАБОТЫ С ЕДИНЫМ МЕНЮ

---

### ✅ Паттерн 1: Обработка текстового ввода с FSM

**Проблема:** При ожидании текстового ввода (сумма, количество, ID) нужно удалить сообщение пользователя и обновить единое меню.

**Решение:**

```
@router.message(SomeState.waiting_for_input)
async def process_input(message: Message, state: FSMContext, admins: list[int]):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 1. Валидация
    try:
        value = int(message.text.strip())
        if value <= 0:
            raise ValueError("Invalid")
    except ValueError:
        # ❌ НЕ ИСПОЛЬЗУЕМ message.answer() для ошибок!
        # ✅ Получаем menu_message_id из БД и редактируем
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info and menu_info.get('menu_message_id'):
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_info['menu_message_id'],
                text="❌ **ОШИБКА**\n\nВведите корректное число:",
                reply_markup=cancel_keyboard,
                parse_mode="Markdown"
            )
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass
        return
    
    # 2. Удаляем сообщение пользователя ПОСЛЕ валидации
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить сообщение: {e}")
    
    # 3. Получаем menu_message_id из БД
    menu_info = await db.get_chat_menu(chat_id)
    
    # 4. Обновляем данные в FSM
    await state.update_data(value=value)
    
    # 5. Редактируем единое меню
    if menu_info and menu_info.get('menu_message_id'):
        await message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_info['menu_message_id'],
            text=f"✅ Получено: {value}\n\nПодтвердите:",
            reply_markup=confirm_keyboard,
            parse_mode="Markdown"
        )
        await db.save_chat_menu(chat_id, user_id, menu_info['menu_message_id'], 'confirm_screen')
```

**Ключевые моменты:**
- ✅ Валидация ПЕРЕД удалением сообщения
- ✅ Удаление сообщения пользователя ПОСЛЕ успешной валидации
- ✅ Получение `menu_message_id` из БД (не из FSM!)
- ✅ Редактирование существующего меню
- ✅ Сохранение screen_code после каждого изменения

---

### ✅ Паттерн 2: Переходы между состояниями FSM

**Проблема:** При переходе из одного FSM-состояния в другое нужно сохранить `menu_message_id`.

**Решение:**

```
@router.callback_query(F.data == "next_step")
async def next_step(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    # ✅ КРИТИЧНО: Сохраняем menu_message_id ПЕРЕД изменением состояния
    menu_message_id = callback.message.message_id
    
    # Получаем текущие данные
    data = await state.get_data()
    
    # Устанавливаем новое состояние
    await state.set_state(NewState.next_step)
    
    # ✅ ВОССТАНАВЛИВАЕМ menu_message_id после set_state
    await state.update_data(
        menu_message_id=menu_message_id,
        # Сохраняем другие важные данные
        target_id=data.get('target_id'),
        amount=data.get('amount')
    )
    
    # Редактируем меню
    await callback.message.edit_text(
        text="Следующий шаг...",
        reply_markup=keyboard
    )
    await db.save_chat_menu(chat_id, user_id, menu_message_id, 'next_step')
```

**Ключевые моменты:**
- ✅ Сохраняем `menu_message_id` ПЕРЕД `set_state()`
- ✅ Восстанавливаем после `set_state()`
- ✅ Переносим важные данные из старого состояния

---

### ✅ Паттерн 3: Возврат к предыдущему экрану после FSM

**Проблема:** После завершения FSM-операции нужно вернуться к предыдущему меню с обновлёнными данными.

**Решение:**

```
@router.callback_query(F.data == "operation_confirm")
async def confirm_operation(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    # Получаем данные
    data = await state.get_data()
    target_id = data['target_id']
    amount = data['amount']
    
    # Выполняем операцию
    await db.perform_operation(target_id, amount)
    
    # ✅ КРИТИЧНО: Сохраняем target_id для возврата
    await state.update_data(last_target_id=target_id)
    
    # Показываем результат
    await callback.message.edit_text(
        text="✅ Операция выполнена!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ещё одна операция", callback_data="operation_more")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
        ])
    )
    
    # ✅ Сбрасываем состояние, но СОХРАНЯЕМ важные данные
    await state.set_state(None)
    await state.update_data(
        menu_message_id=callback.message.message_id,
        last_target_id=target_id
    )

@router.callback_query(F.data == "operation_more")
async def operation_more(callback: CallbackQuery, state: FSMContext):
    """Повторная операция с тем же объектом"""
    data = await state.get_data()
    last_target_id = data.get('last_target_id')
    
    if not last_target_id:
        await callback.answer("⚠️ Контекст потерян", show_alert=True)
        return
    
    # Получаем свежие данные из БД
    target_data = await db.get_target(last_target_id)
    
    # Показываем обновлённую карточку
    await callback.message.edit_text(
        text=f"Объект: {last_target_id}\nБаланс: {target_data['balance']}",
        reply_markup=operation_keyboard(last_target_id)
    )
```

**Ключевые моменты:**
- ✅ Сохраняем `last_target_id` для повторных операций
- ✅ Получаем СВЕЖИЕ данные из БД (не из кэша)
- ✅ Кнопка "Ещё одно действие" ведёт к обновлённой карточке

---

### ✅ Паттерн 4: Обработка ошибок при редактировании меню

**Проблема:** `edit_message_text` может упасть если сообщение удалено или текст не изменился.

**Решение:**

```
async def safe_edit_menu(
    bot,
    chat_id: int,
    message_id: int,
    text: str,
    keyboard,
    parse_mode: str = "Markdown"
):
    """Безопасное редактирование меню с обработкой ошибок"""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            # Текст не изменился - это не ошибка
            logger.debug(f"Message not modified: {message_id}")
            return True
        elif "message to edit not found" in str(e).lower():
            # Сообщение удалено - нужно создать новое
            logger.warning(f"Message {message_id} not found, need to recreate")
            return False
        else:
            logger.error(f"Error editing menu: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error editing menu: {e}")
        return False

# Использование
menu_info = await db.get_chat_menu(chat_id)
if menu_info and menu_info.get('menu_message_id'):
    success = await safe_edit_menu(
        bot=message.bot,
        chat_id=chat_id,
        message_id=menu_info['menu_message_id'],
        text="Новый текст",
        keyboard=keyboard
    )
    
    if not success:
        # Fallback: создаём новое сообщение
        new_msg = await message.answer(text="Новый текст", reply_markup=keyboard)
        await db.save_chat_menu(chat_id, user_id, new_msg.message_id, 'screen_code')
```

---

### ✅ Паттерн 5: Множественные callback_data с параметрами

**Проблема:** При использовании `callback_data` с ID (например, `balance_add_123456`) нужно корректно извлечь ID.

**Решение:**

```
# ✅ ПРАВИЛЬНО: Хендлер с startswith
@router.callback_query(F.data.startswith("balance_add_"))
async def balance_add(callback: CallbackQuery, state: FSMContext):
    # Извлекаем ID из callback_data
    try:
        target_id = int(callback.data.split("_"))
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка: неверный формат", show_alert=True)
        return
    
    # Остальная логика...

# ✅ ПРАВИЛЬНО: Создание callback_data
def get_balance_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Добавить",
            callback_data=f"balance_add_{user_id}"
        )],
        [InlineKeyboardButton(
            text="➖ Списать",
            callback_data=f"balance_remove_{user_id}"
        )]
    ])
```

**Важно:**
- ✅ Используйте `F.data.startswith()` для хендлера
- ✅ Всегда обрабатывайте ошибки при парсинге ID
- ✅ Ограничение: `callback_data` максимум 64 байта

---

### ✅ Паттерн 6: Отмена FSM-операции

**Проблема:** При отмене операции нужно корректно вернуться в меню без потери контекста.

**Решение:**

```
@router.callback_query(F.data == "cancel_operation")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    # Получаем данные ДО сброса состояния
    data = await state.get_data()
    return_screen = data.get('return_screen', 'main_menu')
    menu_message_id = data.get('menu_message_id')
    
    # Сбрасываем состояние
    await state.set_state(None)
    
    # Восстанавливаем menu_message_id
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
    
    # Возвращаем в нужное меню
    if return_screen == 'settings':
        await show_settings(callback, state)
    elif return_screen == 'admin_panel':
        await show_admin_panel(callback, state, admins)
    else:
        await show_main_menu(callback, state)
    
    await callback.answer("❌ Операция отменена")

# При начале операции сохраняем откуда пришли
@router.callback_query(F.data == "start_operation")
async def start_operation(callback: CallbackQuery, state: FSMContext):
    await state.update_data(
        menu_message_id=callback.message.message_id,
        return_screen='settings'  # ✅ Запоминаем откуда пришли
    )
    await state.set_state(OperationState.waiting_input)
```

---

### ✅ Паттерн 7: Пагинация с сохранением menu_message_id

**Проблема:** При пагинации (список пользователей, платежей) нужно сохранять единое меню.

**Решение:**

```
@router.callback_query(F.data.startswith("users_page_"))
async def show_users_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_"))
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    users, total_pages = await db.get_users_paginated(page=page, per_page=10)
    
    text = f"👥 Пользователи (стр. {page}/{total_pages})\n\n"
    for user in users:
        text += f"-  {user['name']} - {user['balance']}\n"
    
    # ✅ Редактируем ТО ЖЕ сообщение
    await callback.message.edit_text(
        text=text,
        reply_markup=get_pagination_keyboard(page, total_pages)
    )
    
    # ✅ Обновляем screen_code с номером страницы
    await db.save_chat_menu(
        chat_id, 
        user_id, 
        callback.message.message_id, 
        f'users_page_{page}'
    )

def get_pagination_keyboard(page: int, total_pages: int):
    buttons = []
    
    # Кнопки навигации
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"users_page_{page-1}"
        ))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(
            text="Вперёд ➡️",
            callback_data=f"users_page_{page+1}"
        ))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Кнопка возврата
    buttons.append([InlineKeyboardButton(
        text="⬅️ В меню",
        callback_data="back_to_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

---

## 🚨 АНТИПАТТЕРНЫ (ЧТО НЕ ДЕЛАТЬ)

### ❌ НЕ использовать message.answer() при FSM

```
# ❌ НЕПРАВИЛЬНО
@router.message(State.waiting_input)
async def process_input(message: Message):
    await message.answer("Результат")  # Создаст НОВОЕ сообщение!
```

```
# ✅ ПРАВИЛЬНО
@router.message(State.waiting_input)
async def process_input(message: Message):
    await message.delete()
    menu_info = await db.get_chat_menu(message.chat.id)
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=menu_info['menu_message_id'],
        text="Результат"
    )
```

---

### ❌ НЕ забывать удалять сообщения пользователя

```
# ❌ НЕПРАВИЛЬНО
@router.message(State.waiting_input)
async def process_input(message: Message):
    # Сообщение пользователя останется в чате!
    value = message.text
```

```
# ✅ ПРАВИЛЬНО
@router.message(State.waiting_input)
async def process_input(message: Message):
    value = message.text
    try:
        await message.delete()  # Удаляем сразу
    except:
        pass
```

---

### ❌ НЕ использовать FSM-данные для хранения актуальной информации

```
# ❌ НЕПРАВИЛЬНО
data = await state.get_data()
balance = data['user_balance']  # Может быть устаревшим!
```

```
# ✅ ПРАВИЛЬНО
data = await state.get_data()
user_id = data['target_user_id']
balance = await db.get_balance(user_id)  # Всегда актуально
```

---

## 📋 ЧЕКЛИСТ ПЕРЕД КОММИТОМ

- [ ] Все `message.answer()` в FSM заменены на `edit_message_text()`
- [ ] Все сообщения пользователя удаляются через `message.delete()`
- [ ] `menu_message_id` сохраняется при всех переходах
- [ ] Используется `state.set_state(None)` вместо `state.clear()`
- [ ] После каждого редактирования вызывается `db.save_chat_menu()`
- [ ] Актуальные данные берутся из БД, не из FSM
- [ ] Обработаны ошибки `edit_message_text()`
- [ ] Добавлены логи для отладки
```

***

Добавь эти паттерны в `DEVELOPMENT_RULES.md` - они покроют **95% типовых ситуаций** при работе с единым меню! 🎯


Паттерн: YooKassa без вебхука

    Использовать официальный Python SDK YooKassa: конфигурация через YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env и Configuration.account_id/secret_key в payment_api.py.

​

При создании платежа обязательно указывать confirmation.confirmation_url и return_url, где return_url — deep‑link в бота вида https://t.me/<BOT_LINK>?start=payment_success (без передачи статуса платежа через return_url, т.к. YooKassa никогда не шлёт туда статусы).

    ​

    В боте использовать единое меню: все экраны должны открываться через edit_message_text (у нас это edit_menu), единственный menu_message_id хранить в FSM и в таблице chat_menus.

Типичные трудности и причины

    Ошибочный return_url по умолчанию (https://t.me/your_bot) в SDK‑обёртке: приводило к возврату в чужой/пустой бот. Причина — заглушка в коде, не привязанная к конфигу проекта.

    ​

    Несоответствие BOT_USERNAME (используется в рефералке) и фактической ссылки бота (@Interior_Bot1_bot): deep‑link вёл в правильный бот, но существующая переменная окружения описывала другое имя.

    Нарушение паттерна «единого меню»: первые правки создавали новое меню через message.answer, а не редактировали существующее, что визуально давало два меню в чате.

    Особенность Telegram: при переходе по ?start=... клиент всегда отправляет в чат команду /start, которую бот может только удалить post factum — поэтому кнопка /start кратко «мигает».

Как решали и почему так

    return_url привязан к конфигу: введён BOT_LINK в .env и используется в payment_api.py для формирования https://t.me/<BOT_LINK>?start=payment_success. Это убирает хардкод и упрощает смену имени/зеркала бота.

    Обработчик /start (cmd_start) доработан:

        различает обычный старт, реферальный старт и start=payment_success;

        при payment_success сначала удаляет старое меню через delete_old_menu_if_exists, затем создаёт одно новое сообщение «Платёж успешен» и сохраняет его menu_message_id в FSM и chat_menus;

        не создаёт пользователя повторно и не шлёт уведомление админам, если пользователь уже есть (убран эффект «новый пользователь» при возврате с оплаты).

    Стратегия единого меню сохранена: все дальнейшие экраны (главное меню, профиль, создание дизайна) работают через edit_menu, который:

        восстанавливает menu_message_id из FSM или БД;

        пытается отредактировать существующее сообщение;

        при неудаче удаляет старое меню и создаёт новое, обновляя запись в chat_menus.

Ограничения текущего решения (без вебхука)

    Статус платежа фактически не проверяется: начисление баланса и показ «Платёж успешен» завязаны на факте возврата по return_url, а не на событии payment.succeeded от YooKassa.

​

Нет автообновления при задержке платежа или последующей отмене: если банк проведёт платёж позже или произойдёт возврат, бот об этом не узнает без опроса API или вебхука.

​

Для прода обязательно планировать следующий шаг: внедрение обработчика вебхуков (payment.succeeded) с валидацией подписи, обновлением записи в payments и начислением токенов в фоне.
​
