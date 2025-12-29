# 📘 РЕФЕРАЛЬНАЯ ПРОГРАММА - ПОЛНАЯ ДОКУМЕНТАЦИЯ

**Проект:** InteriorBot-v2  
**Репозиторий:** https://github.com/severand/InteriorBot-v2  
**Дата:** 03.12.2025  
**Версия:** 1.0.0

---

## 🎯 НАЗНАЧЕНИЕ СИСТЕМЫ

Полнофункциональная реферальная программа для Telegram-бота с:

✅ **Приглашением друзей** по уникальной реферальной ссылке  
✅ **Автоматическим начислением** процента от покупок рефералов  
✅ **Выводом денег** на карты/СБП/YooMoney/другие способы  
✅ **Обменом реферального баланса** на генерации  
✅ **Полной историей операций** (заработки, обмены, выплаты)  
✅ **Админ-панелью** для управления выплатами и настройками

---

## 📊 АРХИТЕКТУРА ПРОЕКТА

### Структура файлов

```
InteriorBot-v2/
└── bot/
    ├── config.py                    # Конфигурация (BOT_USERNAME)
    ├── main.py                      # Регистрация роутеров
    ├── database/
    │   ├── models.py                # SQL-схемы и запросы
    │   └── db.py                    # Методы работы с БД
    ├── handlers/
    │   ├── user_start.py            # Профиль + реферальная инфо
    │   ├── payment.py               # Начисление % от покупок
    │   ├── referral.py              # Выплаты, обмены, реквизиты, история
    │   └── admin.py                 # Админ-панель (управление выплатами)
    ├── keyboards/
    │   └── inline.py                # Кнопки профиля с реферальными действиями
    ├── states/
    │   └── fsm.py                   # ReferralStates, AdminStates
    └── utils/
        └── texts.py                 # PROFILE_WITH_REFERRAL_TEXT
```

---

## 🗄️ БАЗА ДАННЫХ

### 1. Таблица `users` (расширенная)

#### Основные поля:
```sql
user_id INTEGER PRIMARY KEY
username TEXT
balance INTEGER DEFAULT 3                    -- баланс генераций
reg_date DATETIME DEFAULT CURRENT_TIMESTAMP
```

#### Реферальные поля:
```sql
referral_code TEXT UNIQUE                    -- уникальный код пользователя (8 символов)
referred_by INTEGER                          -- ID реферера (кто пригласил)
referrals_count INTEGER DEFAULT 0            -- количество приглашённых
```

#### Финансовые поля:
```sql
referral_balance INTEGER DEFAULT 0           -- баланс в рублях (для вывода)
referral_total_earned INTEGER DEFAULT 0      -- всего заработано (рубли)
referral_total_paid INTEGER DEFAULT 0        -- всего выплачено (рубли)
```

#### Реквизиты для выплат:
```sql
payment_method TEXT                          -- способ: card/sbp/yoomoney/other
payment_details TEXT                         -- номер карты/телефона/кошелька
sbp_bank TEXT                                -- название банка для СБП
```

#### Статистика:
```sql
total_generations INTEGER DEFAULT 0          -- всего генераций сделано
successful_payments INTEGER DEFAULT 0        -- успешных оплат
total_spent INTEGER DEFAULT 0                -- всего потрачено (рубли)
```

**⚠️ ВАЖНО:** Если база уже существует, нужно добавить новые поля через ALTER TABLE.

---

### 2. Таблица `referral_earnings` (НОВАЯ)

**Назначение:** Логирование каждого начисления комиссии рефереру

```sql
CREATE TABLE IF NOT EXISTS referral_earnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,              -- кто получил комиссию
    referred_id INTEGER NOT NULL,              -- кто совершил покупку
    payment_id TEXT NOT NULL,                  -- ID платежа в payments
    amount INTEGER NOT NULL,                   -- сумма покупки (рубли)
    commission_percent INTEGER NOT NULL,       -- процент комиссии (10%)
    earnings INTEGER NOT NULL,                 -- заработок реферера (рубли)
    tokens_given INTEGER NOT NULL,             -- бонусные генерации рефереру
    status TEXT DEFAULT 'credited',            -- статус: credited/cancelled
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
    FOREIGN KEY (referred_id) REFERENCES users (user_id)
)
```

**Пример записи:**
```
referrer_id: 123456
referred_id: 789012
payment_id: "yookassa_abc123"
amount: 990 руб (покупка реферала)
commission_percent: 10
earnings: 99 руб (10% от 990)
tokens_given: 3 генерации (99 руб / 29 руб за генерацию)
```

---

### 3. Таблица `referral_exchanges` (НОВАЯ)

**Назначение:** Логирование обменов реферального баланса на генерации

```sql
CREATE TABLE IF NOT EXISTS referral_exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,                   -- сумма обмена (рубли)
    tokens INTEGER NOT NULL,                   -- получено генераций
    exchange_rate INTEGER NOT NULL,            -- курс обмена (29 руб/генерация)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
```

**Пример записи:**
```
user_id: 123456
amount: 290 руб
tokens: 10 генераций
exchange_rate: 29 руб/генерация
```

---

### 4. Таблица `referral_payouts` (НОВАЯ)

**Назначение:** Заявки на выплату реферального баланса

```sql
CREATE TABLE IF NOT EXISTS referral_payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,                   -- сумма выплаты
    payment_method TEXT,                       -- card/sbp/yoomoney/other
    payment_details TEXT,                      -- реквизиты
    status TEXT DEFAULT 'pending',             -- pending/completed/rejected
    admin_note TEXT,                           -- примечание админа
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,                     -- когда обработано
    processed_by INTEGER,                      -- ID админа
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
```

**Статусы:**
- `pending` - ожидает обработки
- `completed` - выплачено
- `rejected` - отклонено

---

### 5. Таблица `settings` (дополнена)

**Новые настройки реферальной программы:**

| Ключ | Значение по умолчанию | Описание |
|------|----------------------|----------|
| `welcome_bonus` | `"3"` | Бонус новому пользователю (генерации) |
| `referral_bonus_inviter` | `"2"` | Бонус пригласившему при регистрации (генерации) |
| `referral_bonus_invited` | `"2"` | Бонус новому пользователю от реферера (генерации) |
| `referral_enabled` | `"1"` | Включена ли программа (1/0) |
| `referral_commission_percent` | `"10"` | Процент от покупок рефералов (%) |
| `referral_min_payout` | `"500"` | Минимальная сумма вывода (рубли) |
| `referral_exchange_rate` | `"29"` | Курс обмена рубли → генерации (руб/генерация) |

**Изменение настроек через код:**
```python
await db.set_setting("referral_commission_percent", "15")  # Поменять на 15%
await db.set_setting("referral_min_payout", "1000")        # Мин. вывод 1000 руб
```

---

## 🔄 СХЕМА РАБОТЫ СИСТЕМЫ

### 1. Регистрация по реферальной ссылке

**Пользовательский флоу:**
```
1. Реферер копирует свою ссылку: t.me/YourBot?start=ref_ABC12345
2. Друг переходит по ссылке → /start ref_ABC12345
3. Бот регистрирует нового пользователя
4. Начисляет бонусы ОБОИМ:
   - Реферер: +2 генерации (referral_bonus_inviter)
   - Новый: +2 генерации (referral_bonus_invited)
```

**Код в user_start.py:**
```python
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Парсим реферальный код
    referrer_code = None
    if len(message.text.split()) > 1:
        args = message.text.split()[1]
        if args.startswith('ref_'):
            referrer_code = args.replace('ref_', '')
    
    # Создаём пользователя с реферальным кодом
    await db.create_user(user_id, message.from_user.username, referrer_code)
```

**Код в db.py:**
```python
async def create_user(self, user_id: int, username: str, referrer_code: str):
    # Создаём пользователя с начальным балансом
    await db.execute(CREATE_USER, (user_id, username, initial_balance))
    
    # Генерируем уникальный код (8 символов)
    import secrets
    ref_code = secrets.token_urlsafe(8)
    await db.execute(UPDATE_REFERRAL_CODE, (ref_code, user_id))
    
    # Обрабатываем реферальную систему
    if referrer_code:
        await self.process_referral(user_id, referrer_code)
```

---

### 2. Начисление процента от покупок

**Пользовательский флоу:**
```
1. Реферал покупает пакет (например, 60 генераций за 990 руб)
2. После успешной оплаты:
   - Реферал получает 60 генераций
   - Рефереру начисляется:
     a) 99 руб на реферальный баланс (10% от 990)
     b) 3 генерации на основной баланс (99 / 29 = 3)
3. Операция логируется в referral_earnings
```

**Код в payment.py:**
```python
@router.callback_query(F.data == "check_payment")
async def check_payment(callback: CallbackQuery):
    # После успешной оплаты
    if is_paid:
        # 1. Начисляем токены покупателю
        await db.add_tokens(user_id, last_payment['tokens'])
        
        # 2. Начисляем комиссию рефереру
        await _process_referral_commission(
            user_id=user_id,
            payment_id=last_payment['yookassa_payment_id'],
            amount=last_payment['amount'],
            purchased_tokens=last_payment['tokens']
        )
```

**Функция начисления в payment.py:**
```python
async def _process_referral_commission(user_id, payment_id, amount, purchased_tokens):
    # 1. Проверяем включена ли программа
    enabled = await db.get_setting("referral_enabled")
    if str(enabled) != "1":
        return
    
    # 2. Находим реферера
    user = await db.get_user_data(user_id)
    referrer_id = user.get("referred_by")
    if not referrer_id:
        return
    
    # 3. Рассчитываем комиссию
    commission_percent = int(await db.get_setting("referral_commission_percent") or "10")
    earnings = int(amount * commission_percent / 100)
    
    # 4. Начисляем рубли на реферальный баланс
    await db.add_referral_balance(referrer_id, earnings)
    
    # 5. Конвертируем в генерации
    exchange_rate = int(await db.get_setting("referral_exchange_rate") or "29")
    tokens_to_give = earnings // exchange_rate
    
    if tokens_to_give > 0:
        await db.add_tokens(referrer_id, tokens_to_give)
    
    # 6. Логируем
    await db.log_referral_earning(
        referrer_id=referrer_id,
        referred_id=user_id,
        payment_id=payment_id,
        amount=amount,
        commission_percent=commission_percent,
        earnings=earnings,
        tokens=tokens_to_give
    )
```

---

### 3. Обмен реферального баланса на генерации

**Пользовательский флоу:**
```
1. Пользователь в профиле: "💎 Обменять на генерации"
2. Видит баланс и курс: 290 руб = 10 генераций
3. Вводит количество генераций или /all
4. Подтверждает обмен
5. Мгновенное начисление генераций
```

**Код в referral.py:**
```python
@router.callback_query(F.data == "referral_exchange_tokens")
async def exchange_to_tokens(callback: CallbackQuery, state: FSMContext):
    balance = await db.get_referral_balance(user_id)
    exchange_rate = int(await db.get_setting("referral_exchange_rate") or "29")
    max_tokens = balance // exchange_rate
    
    # Запрашиваем количество
    await state.set_state(ReferralStates.entering_exchange_amount)

@router.message(ReferralStates.entering_exchange_amount)
async def process_exchange_amount(message: Message, state: FSMContext):
    tokens = int(message.text)  # или /all
    cost = tokens * exchange_rate
    
    # Выполняем обмен
    await db.decrease_referral_balance(user_id, cost)
    await db.increase_balance(user_id, tokens)
    
    # Логируем
    await db.log_referral_exchange(user_id, cost, tokens, exchange_rate)
```

---

### 4. Запрос выплаты

**Пользовательский флоу:**
```
1. Пользователь: "💸 Вывести деньги"
2. Проверки:
   - Минимальная сумма ≥ 500 руб
   - Реквизиты указаны
3. Вводит сумму или /all
4. Подтверждает заявку
5. Создаётся запись в referral_payouts со статусом "pending"
6. Баланс замораживается (уменьшается сразу)
7. Админ обрабатывает заявку вручную
```

**Код в referral.py:**
```python
@router.callback_query(F.data == "referral_request_payout")
async def request_payout(callback: CallbackQuery, state: FSMContext):
    balance = await db.get_referral_balance(user_id)
    min_payout = int(await db.get_setting("referral_min_payout") or "500")
    
    # Проверки
    if balance < min_payout:
        await callback.answer("⚠️ Недостаточно средств")
        return
    
    payment_details = await db.get_payment_details(user_id)
    if not payment_details:
        await callback.answer("⚠️ Укажите реквизиты")
        return
    
    await state.set_state(ReferralStates.entering_payout_amount)

@router.callback_query(F.data.startswith("confirm_payout_"))
async def confirm_payout(callback: CallbackQuery):
    amount = int(callback.data.split("_")[-1])
    
    # Создаём заявку
    payout_id = await db.create_payout_request(user_id, amount, method, details)
    
    # Замораживаем баланс
    await db.decrease_referral_balance(user_id, amount)
```

---

### 5. Настройка реквизитов

**Поддерживаемые способы:**

| Способ | payment_method | Формат payment_details | Валидация |
|--------|---------------|----------------------|-----------|
| Банковская карта | `card` | 16-19 цифр без пробелов | 16-19 цифр |
| СБП (по телефону) | `sbp` | +7XXXXXXXXXX | 12 символов |
| YooMoney | `yoomoney` | 11-15 цифр номера кошелька | 11-15 цифр |
| Другой способ | `other` | Произвольный текст | Минимум 5 символов |

**Код в referral.py:**
```python
@router.callback_query(F.data == "referral_setup_payment")
async def setup_payment_method(callback: CallbackQuery):
    # Показываем меню выбора способа
    keyboard = [
        [Button("💳 Банковская карта", "payment_method_card")],
        [Button("📱 СБП", "payment_method_sbp")],
        [Button("💵 YooMoney", "payment_method_yoomoney")],
        [Button("💰 Другой", "payment_method_other")]
    ]

# Для каждого способа свой handler
@router.callback_query(F.data == "payment_method_card")
async def setup_card(callback, state):
    await state.set_state(ReferralStates.entering_card_number)

@router.message(ReferralStates.entering_card_number)
async def process_card_number(message, state):
    card = re.sub(r'[^\d]', '', message.text)  # Только цифры
    await db.set_payment_details(user_id, "card", card)
```

**Валидация телефона в referral.py:**
```python
def validate_phone(phone: str) -> tuple[bool, str]:
    # Убираем всё кроме цифр и +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Приводим к +7
    if phone.startswith('8'):
        phone = '+7' + phone[1:]
    elif phone.startswith('7'):
        phone = '+' + phone
    
    # Проверяем длину (должно быть +7XXXXXXXXXX = 12 символов)
    if len(phone) != 12:
        return False, ""
    
    # Форматируем: +7 (999) 123-45-67
    formatted = f"+7 ({phone[2:5]}) {phone[5:8]}-{phone[8:10]}-{phone[10:]}"
    return True, formatted
```

---

## 🎨 ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС

### Профиль с реферальной информацией

**Текст профиля (utils/texts.py):**
```python
PROFILE_WITH_REFERRAL_TEXT = (
    "👤 **ВАШ ПРОФИЛЬ**\n\n"
    "─────────────────\n"
    "🎯 **Баланс генераций:** {balance}\n"
    "─────────────────\n\n"
    "🎁 **Партнёрская программа:**\n"
    "🔗 Ваша ссылка: `{referral_link}`\n"
    "👥 Приглашено: **{referrals_count}** {referrals_word}\n\n"
    "💰 **Реферальный баланс:**\n"
    "• Доступно: **{referral_balance} руб.**\n"
    "• Всего заработано: {total_earned} руб.\n"
    "• Выплачено: {total_paid} руб.\n\n"
    "🎯 **Ваши условия:**\n"
    "• За регистрацию: +2 генерации\n"
    "• % от покупок: {commission_percent}%\n"
    "─────────────────"
)
```

**Кнопки профиля (keyboards/inline.py):**
```python
def get_profile_keyboard() -> InlineKeyboardMarkup:
    builder.row(
        InlineKeyboardButton(text="💳 Купить токены", callback_data="buy_generations")
    )
    builder.row(
        InlineKeyboardButton(text="💸 Вывести деньги", callback_data="referral_request_payout"),
        InlineKeyboardButton(text="💎 Обменять на генерации", callback_data="referral_exchange_tokens")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Реквизиты для выплат", callback_data="referral_setup_payment")
    )
    builder.row(
        InlineKeyboardButton(text="📊 История операций", callback_data="referral_history")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
    )
```

**Формирование данных в user_start.py:**
```python
@router.callback_query(F.data == "menu_profile")
async def profile_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Получаем все данные
    balance = await db.get_balance(user_id)
    user_data = await db.get_user(user_id)
    referral_code = user_data.get('referral_code', '')
    referrals_count = user_data.get('referrals_count', 0)
    referral_balance = await db.get_referral_balance(user_id)
    total_earned = user_data.get('referral_total_earned', 0) or 0
    total_paid = user_data.get('referral_total_paid', 0) or 0
    commission_percent = await db.get_setting("referral_commission_percent") or "10"
    
    # Формируем ссылку
    bot_username = config.BOT_USERNAME.replace('@', '')
    referral_link = f"t.me/{bot_username}?start=ref_{referral_code}"
    
    # Правильное склонение
    referrals_word = get_word_form(referrals_count, ("друг", "друга", "друзей"))
    
    # Форматируем текст
    profile_text = PROFILE_WITH_REFERRAL_TEXT.format(
        balance=balance,
        referral_link=referral_link,
        referrals_count=referrals_count,
        referrals_word=referrals_word,
        referral_balance=format_number(referral_balance),
        total_earned=format_number(total_earned),
        total_paid=format_number(total_paid),
        commission_percent=commission_percent
    )
```

---

## 🔌 МЕТОДЫ DATABASE API

### Основные методы работы с рефералами (db.py)

**Создание и получение пользователей:**
```python
# Создать пользователя с реферальным кодом
await db.create_user(user_id, username, referrer_code=None)

# Получить пользователя по ID
user = await db.get_user(user_id)

# Получить пользователя по реферальному коду
referrer = await db.get_user_by_referral_code("ABC12345")

# Получить полные данные пользователя
user_data = await db.get_user_data(user_id)
```

**Работа с реферальным балансом:**
```python
# Получить реферальный баланс (рубли)
balance = await db.get_referral_balance(user_id)

# Добавить к реферальному балансу
await db.add_referral_balance(user_id, amount=99)

# Уменьшить реферальный баланс
await db.decrease_referral_balance(user_id, amount=500)

# Получить общий заработок
total_earned = await db.get_user_total_earned(user_id)
```

**Работа с генерациями:**
```python
# Получить баланс генераций
balance = await db.get_balance(user_id)

# Добавить генерации
await db.add_tokens(user_id, tokens=10)
await db.increase_balance(user_id, amount=10)  # Альтернатива

# Уменьшить генерации
await db.decrease_balance(user_id)  # -1 генерация
```

**Логирование операций:**
```python
# Залогировать заработок реферера
await db.log_referral_earning(
    referrer_id=123456,
    referred_id=789012,
    payment_id="yookassa_abc",
    amount=990,
    commission_percent=10,
    earnings=99,
    tokens_given=3
)

# Залогировать обмен на генерации
await db.log_referral_exchange(
    user_id=123456,
    amount=290,
    tokens=10,
    exchange_rate=29
)

# Создать заявку на выплату
payout_id = await db.create_payout_request(
    user_id=123456,
    amount=1000,
    payment_method="sbp",
    payment_details="+79991234567"
)
```

**Получение истории:**
```python
# История заработков
earnings = await db.get_user_referral_earnings(user_id)

# История обменов
exchanges = await db.get_user_exchanges(user_id)

# История выплат
payouts = await db.get_user_payouts(user_id)
```

**Работа с реквизитами:**
```python
# Установить реквизиты
await db.set_payment_details(user_id, "sbp", "+79991234567", sbp_bank="Сбербанк")

# Получить реквизиты
details = await db.get_payment_details(user_id)
```

**Работа с настройками:**
```python
# Получить настройку
value = await db.get_setting("referral_commission_percent")

# Установить настройку
await db.set_setting("referral_commission_percent", "15")

# Получить все настройки
all_settings = await db.get_all_settings()
```

**Статистика:**
```python
# Статистика рефералов
stats = await db.get_total_referral_stats()

# Статистика обменов
exchange_stats = await db.get_total_exchanges_stats()

# Статистика выплат
payout_stats = await db.get_payout_stats()
```

---

## 🛠️ FSM STATES

### ReferralStates (states/fsm.py)

```python
class ReferralStates(StatesGroup):
    entering_payout_amount = State()      # Ввод суммы выплаты
    entering_exchange_amount = State()    # Ввод количества генераций
    entering_card_number = State()        # Ввод номера карты
    entering_yoomoney = State()           # Ввод YooMoney
    entering_phone = State()              # Ввод телефона для СБП
    entering_other_method = State()       # Ввод другого способа
```

**Использование:**
```python
# Установка состояния
await state.set_state(ReferralStates.entering_payout_amount)

# Проверка состояния
current = await state.get_state()
if current == ReferralStates.entering_phone:
    # Обработка ввода телефона
```

---

## 📋 CALLBACK DATA

### Реферальные callback_data

| Callback Data | Handler | Файл | Описание |
|--------------|---------|------|----------|
| `referral_request_payout` | `request_payout()` | referral.py | Начало запроса выплаты |
| `referral_exchange_tokens` | `exchange_to_tokens()` | referral.py | Начало обмена на генерации |
| `referral_setup_payment` | `setup_payment_method()` | referral.py | Настройка реквизитов |
| `referral_history` | `show_referral_history()` | referral.py | История операций |
| `payment_method_card` | `setup_card()` | referral.py | Привязка карты |
| `payment_method_sbp` | `setup_sbp()` | referral.py | Привязка СБП |
| `payment_method_yoomoney` | `setup_yoomoney()` | referral.py | Привязка YooMoney |
| `payment_method_other` | `setup_other()` | referral.py | Другой способ |
| `confirm_exchange_{tokens}` | `confirm_exchange()` | referral.py | Подтверждение обмена |
| `confirm_payout_{amount}` | `confirm_payout()` | referral.py | Подтверждение выплаты |
| `show_profile` | `show_profile_handler()` | user_start.py | Показать профиль |

---

## ⚙️ КОНФИГУРАЦИЯ

### config.py

**Обязательное поле для реферальной системы:**
```python
class Config:
    BOT_USERNAME = os.getenv('BOT_USERNAME', 'YourBotUsername')  # Для реферальных ссылок
```

**Добавить в .env:**
```env
BOT_USERNAME=your_bot_username  # БЕЗ @
```

**Формирование ссылки:**
```python
bot_username = config.BOT_USERNAME.replace('@', '')
referral_link = f"t.me/{bot_username}?start=ref_{referral_code}"
```

---

## 🔐 БЕЗОПАСНОСТЬ И ВАЛИДАЦИЯ

### Маскирование реквизитов

**При отображении:**
```python
# Карта: 1234 5678 9012 3456 → 1234 **** **** 3456
if method == 'card' and len(details) >= 16:
    masked = f"{details[:4]} {'*' * 4} {'*' * 4} {details[-4:]}"

# Телефон: +79991234567 → +7 (999) ***-**-67
elif method == 'sbp' and len(details) >= 10:
    masked = f"+7 ({details[2:5]}) ***-**-{details[-2:]}"

# Другое: длинный текст → первые 10 символов + ***
else:
    masked = details[:10] + '***' if len(details) > 10 else details
```

---

## 🔄 ЖИЗНЕННЫЙ ЦИКЛ ДАННЫХ

### Пример полного цикла

**1. Регистрация нового пользователя:**
```sql
-- Шаг 1: Создание пользователя
INSERT INTO users (user_id, username, balance) VALUES (789012, 'newuser', 3)

-- Шаг 2: Генерация реферального кода
UPDATE users SET referral_code = 'qwer5678' WHERE user_id = 789012

-- Шаг 3: Если есть реферер (код ref_ABC12345)
-- 3a. Находим реферера
SELECT * FROM users WHERE referral_code = 'ABC12345'  -- user_id = 123456

-- 3b. Связываем
UPDATE users SET referred_by = 123456 WHERE user_id = 789012

-- 3c. Увеличиваем счётчик
UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = 123456

-- 3d. Начисляем бонусы
UPDATE users SET balance = balance + 2 WHERE user_id = 123456  -- реферер
UPDATE users SET balance = balance + 2 WHERE user_id = 789012  -- новый
```

**2. Покупка пакета рефералом:**
```sql
-- Шаг 1: Реферал покупает 60 генераций за 990 руб
INSERT INTO payments (user_id, yookassa_payment_id, amount, tokens, status)
VALUES (789012, 'yookassa_xyz', 990, 60, 'pending')

-- Шаг 2: Оплата подтверждена
UPDATE payments SET status = 'succeeded' WHERE yookassa_payment_id = 'yookassa_xyz'

-- Шаг 3: Начисление генераций рефералу
UPDATE users SET balance = balance + 60 WHERE user_id = 789012

-- Шаг 4: Начисление комиссии рефереру (10% от 990 = 99 руб)
-- 4a. Рубли на реферальный баланс
UPDATE users SET 
    referral_balance = referral_balance + 99,
    referral_total_earned = referral_total_earned + 99
WHERE user_id = 123456

-- 4b. Генерации на основной баланс (99/29 = 3)
UPDATE users SET balance = balance + 3 WHERE user_id = 123456

-- 4c. Логирование
INSERT INTO referral_earnings 
(referrer_id, referred_id, payment_id, amount, commission_percent, earnings, tokens_given)
VALUES (123456, 789012, 'yookassa_xyz', 990, 10, 99, 3)
```

**3. Обмен реферального баланса на генерации:**
```sql
-- Реферер обменивает 290 руб на 10 генераций
-- Шаг 1: Уменьшаем реферальный баланс
UPDATE users SET referral_balance = referral_balance - 290 WHERE user_id = 123456

-- Шаг 2: Увеличиваем баланс генераций
UPDATE users SET balance = balance + 10 WHERE user_id = 123456

-- Шаг 3: Логирование
INSERT INTO referral_exchanges (user_id, amount, tokens, exchange_rate)
VALUES (123456, 290, 10, 29)
```

**4. Запрос выплаты:**
```sql
-- Шаг 1: Создание заявки
INSERT INTO referral_payouts (user_id, amount, payment_method, payment_details)
VALUES (123456, 1000, 'sbp', '+79991234567')

-- Шаг 2: Замораживание баланса
UPDATE users SET referral_balance = referral_balance - 1000 WHERE user_id = 123456

-- Шаг 3: Админ обрабатывает заявку
UPDATE referral_payouts 
SET status = 'completed', processed_at = CURRENT_TIMESTAMP, processed_by = 7884972750
WHERE id = 42

-- Шаг 4: Обновляем total_paid
UPDATE users SET referral_total_paid = referral_total_paid + 1000 WHERE user_id = 123456
```

---

## 🎮 HANDLERS FLOW

### Карта обработчиков

```
┌─────────────────────────────────────────────────────┐
│         ПРОФИЛЬ (user_start.py)                     │
│  Callback: menu_profile                             │
│  ↓                                                   │
│  Показывает реферальную информацию                  │
│  + 4 кнопки реферальных действий                    │
└─────────────────────────────────────────────────────┘
          │
          ├──→ 💸 Вывести деньги
          │    │
          │    └──→ referral.py: request_payout()
          │         ├─ Проверка минимума
          │         ├─ Проверка реквизитов
          │         └─ ReferralStates.entering_payout_amount
          │              └─ process_payout_amount()
          │                   └─ confirm_payout()
          │
          ├──→ 💎 Обменять на генерации
          │    │
          │    └──→ referral.py: exchange_to_tokens()
          │         ├─ Расчёт максимума
          │         └─ ReferralStates.entering_exchange_amount
          │              └─ process_exchange_amount()
          │                   └─ confirm_exchange()
          │
          ├──→ ⚙️ Реквизиты
          │    │
          │    └──→ referral.py: setup_payment_method()
          │         ├─ payment_method_card → setup_card()
          │         ├─ payment_method_sbp → setup_sbp()
          │         ├─ payment_method_yoomoney → setup_yoomoney()
          │         └─ payment_method_other → setup_other()
          │
          └──→ 📊 История операций
               │
               └──→ referral.py: show_referral_history()
                    ├─ Получает earnings
                    ├─ Получает exchanges
                    ├─ Получает payouts
                    └─ Форматирует вывод
```

### Начисление при покупке

```
┌─────────────────────────────────────────────────────┐
│      ПОКУПКА (payment.py)                           │
│  Callback: check_payment                            │
└─────────────────────────────────────────────────────┘
          │
          ├─ 1. Проверка статуса в YooKassa
          │
          ├─ 2. Если is_paid:
          │    ├─ add_tokens(user_id, tokens)
          │    └─ _process_referral_commission()
          │         ├─ Проверка referral_enabled
          │         ├─ Получение referred_by
          │         ├─ Расчёт earnings
          │         ├─ add_referral_balance()
          │         ├─ add_tokens() (рефереру)
          │         └─ log_referral_earning()
          │
          └─ 3. Показ успеха
```

---

## 💾 ИНТЕГРАЦИЯ В ДРУГОЙ ПРОЕКТ

### Минимальные требования

**1. Зависимости:**
```
aiogram>=3.0
aiosqlite
python-dotenv
```

**2. Обязательные файлы:**
```
database/models.py    # SQL-схемы (4 новые таблицы)
database/db.py        # Методы (~25 методов)
handlers/referral.py  # Полный handler
states/fsm.py         # ReferralStates
```

**3. Модификации существующих файлов:**
```
config.py            # Добавить BOT_USERNAME
user_start.py        # Обновить profile_callback()
payment.py           # Добавить _process_referral_commission()
keyboards/inline.py  # Добавить 4 кнопки в get_profile_keyboard()
utils/texts.py       # Добавить PROFILE_WITH_REFERRAL_TEXT
main.py              # Зарегистрировать referral.router
```

### Пошаговая интеграция

**Этап 1: База данных**
1. Скопировать из `models.py` создание 4 таблиц
2. Добавить DEFAULT_SETTINGS (7 настроек)
3. Добавить все SQL-запросы для работы с рефералами
4. Добавить методы в `db.py` (секция REFERRAL METHODS)

**Этап 2: Handlers**
1. Скопировать `handlers/referral.py` целиком
2. Обновить `user_start.py`:
   - Импортировать PROFILE_WITH_REFERRAL_TEXT
   - Обновить profile_callback()
   - Добавить обработку реферального кода в start_command()
3. Обновить `payment.py`:
   - Добавить `_convert_earnings_to_tokens()`
   - Добавить `_process_referral_commission()`
   - Вызвать в `check_payment()`

**Этап 3: UI**
1. Добавить 4 кнопки в `keyboards/inline.py`
2. Добавить ReferralStates в `states/fsm.py`
3. Добавить тексты в `utils/texts.py`

**Этап 4: Конфиг**
1. Добавить BOT_USERNAME в `config.py`
2. Добавить в .env файл
3. Зарегистрировать router в `main.py`

---

## 🧪 ТЕСТИРОВАНИЕ

### Проверочный чек-лист

**Регистрация:**
- [ ] Новый пользователь получает 3 генерации
- [ ] Генерируется уникальный referral_code
- [ ] Реферальная ссылка отображается в профиле
- [ ] Регистрация по реферальной ссылке добавляет +2 обоим
- [ ] referred_by корректно заполняется
- [ ] referrals_count увеличивается у реферера

**Начисление от покупок:**
- [ ] После успешной оплаты вызывается `_process_referral_commission()`
- [ ] Рассчитывается корректный процент (10% по умолчанию)
- [ ] Рубли начисляются на referral_balance
- [ ] Генерации начисляются на основной balance
- [ ] Запись добавляется в referral_earnings
- [ ] Если referred_by пустой — начисления не происходит

**Обмен на генерации:**
- [ ] Показывается максимум по курсу
- [ ] Нельзя обменять больше баланса
- [ ] Реферальный баланс уменьшается
- [ ] Генерации увеличиваются
- [ ] Запись добавляется в referral_exchanges
- [ ] /all обменивает всю сумму

**Вывод денег:**
- [ ] Проверка минимальной суммы (500 руб)
- [ ] Проверка наличия реквизитов
- [ ] Создаётся запись в referral_payouts
- [ ] Баланс замораживается (уменьшается сразу)
- [ ] Заявка отображается в админ-панели
- [ ] После обработки админом статус меняется

**Реквизиты:**
- [ ] Валидация номера карты (16-19 цифр)
- [ ] Валидация телефона (+7XXXXXXXXXX)
- [ ] Валидация YooMoney (11-15 цифр)
- [ ] Сохранение в payment_method + payment_details
- [ ] Маскирование при отображении

**История операций:**
- [ ] Отображаются заработки (последние 5)
- [ ] Отображаются обмены (последние 5)
- [ ] Отображаются выплаты (последние 5)
- [ ] Даты форматируются корректно
- [ ] Суммы форматируются с пробелами

---

## 🚨 ОБРАБОТКА ОШИБОК

### Типичные ошибки и решения

**1. Ошибка: "Field referral_code doesn't exist"**
```
Причина: База старая, поля не добавлены
Решение: Запустить миграцию ALTER TABLE
```

**2. Ошибка: "BOT_USERNAME not found"**
```
Причина: Не указано имя бота в config
Решение: Добавить в .env:
BOT_USERNAME=your_bot_username
```

**3. Ошибка: "Handler not found for callback referral_history"**
```
Причина: Router не зарегистрирован
Решение: В main.py добавить:
from handlers import referral
dp.include_router(referral.router)
```

**4. Реферальная ссылка не работает**
```
Причина: Неправильный формат ссылки
Правильно: t.me/bot_username?start=ref_ABC12345
Неправильно: t.me/@bot_username?start=ref_ABC12345 (лишняя @)
```

**5. Комиссия не начисляется**
```
Проверить:
1. referral_enabled = "1" в settings
2. У пользователя заполнено referred_by
3. commission_percent > 0
4. В логах есть "[REFERRAL]" записи
```

---

## 🔧 РАСШИРЕНИЕ И КАСТОМИЗАЦИЯ

### Изменение логики начисления

**Пример: Начислять только рубли, без генераций**

В `payment.py` закомментировать блок:
```python
async def _process_referral_commission(...):
    await db.add_referral_balance(referrer_id, earnings)  # ✅ Рубли
    
    # ❌ УБРАТЬ КОНВЕРТАЦИЮ В ГЕНЕРАЦИИ
    # tokens_to_give = await _convert_earnings_to_tokens(earnings)
    # if tokens_to_give > 0:
    #     await db.add_tokens(referrer_id, tokens_to_give)
    
    # В логе указать tokens_given=0
    await db.log_referral_earning(..., tokens=0)
```

### Добавление уровней комиссии

**Пример: Разный процент в зависимости от количества рефералов**

В `payment.py`:
```python
async def _process_referral_commission(...):
    referrer = await db.get_user(referrer_id)
    referrals_count = referrer.get('referrals_count', 0)
    
    # Прогрессивная шкала
    if referrals_count >= 50:
        commission_percent = 20
    elif referrals_count >= 20:
        commission_percent = 15
    elif referrals_count >= 5:
        commission_percent = 12
    else:
        commission_percent = 10
    
    earnings = int(amount * commission_percent / 100)
    # ... остальная логика
```

---

## 🐛 ОТЛАДКА И ДИАГНОСТИКА

### Логирование

**Все критические точки логируются в payment.py:**

```python
logger.info(f"[REFERRAL] Расчёт: {amount} руб * {commission_percent}% = {earnings} руб")
logger.info(f"[REFERRAL] Начислено {earnings} руб на реф. баланс реферера {referrer_id}")
logger.info(f"[REFERRAL] Конвертация: {earnings} руб = {tokens_to_give} генераций")
logger.info(f"[REFERRAL] ✅ Запись в referral_earnings создана")
```

**Поиск проблем:**
```bash
# Все реферальные операции
grep "\[REFERRAL\]" bot.log

# Конкретный пользователь
grep "user_id: 123456" bot.log | grep REFERRAL

# Ошибки начисления
grep "Failed to process referral commission" bot.log
```

### SQL-диагностика

**Проверка данных:**
```sql
-- Пользователи с рефералами
SELECT user_id, username, referrals_count, referral_balance, referral_total_earned
FROM users WHERE referrals_count > 0;

-- Последние начисления
SELECT * FROM referral_earnings ORDER BY created_at DESC LIMIT 10;

-- Ожидающие выплаты
SELECT u.username, p.amount, p.requested_at
FROM referral_payouts p
JOIN users u ON p.user_id = u.user_id
WHERE p.status = 'pending';

-- Проверка связей
SELECT 
    u1.user_id as referrer_id,
    u1.username as referrer_name,
    u1.referrals_count,
    u2.user_id as referred_id,
    u2.username as referred_name
FROM users u1
LEFT JOIN users u2 ON u2.referred_by = u1.user_id
WHERE u1.referrals_count > 0;
```

---

## 💡 BEST PRACTICES

### 1. Безопасность

✅ **Всегда валидировать ввод:**
```python
# Номер карты
card = re.sub(r'[^\d]', '', input)
if len(card) not in [16, 18, 19]:
    return error

# Телефон
if len(phone) != 12 or not phone.startswith('+7'):
    return error
```

✅ **Маскировать реквизиты:**
```python
# Никогда не показывать полные реквизиты в логах
logger.info(f"Выплата на карту ****{details[-4:]}")
```

✅ **Проверять баланс перед операциями:**
```python
# Финальная проверка ПЕРЕД транзакцией
balance = await db.get_referral_balance(user_id)
if amount > balance:
    return error
```

### 2. Производительность

✅ **Использовать индексы:**
```sql
CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_users_referred_by ON users(referred_by);
CREATE INDEX idx_earnings_referrer ON referral_earnings(referrer_id);
CREATE INDEX idx_payouts_status ON referral_payouts(status);
```

✅ **Ограничивать выборки:**
```python
# Не SELECT *, а конкретные поля
# Не все записи, а LIMIT
earnings = await db.get_user_referral_earnings(user_id)  # LIMIT 20 внутри
```

### 3. Пользовательский опыт

✅ **Понятные сообщения:**
```python
# Плохо
"Error: insufficient funds"

# Хорошо
"⚠️ Недостаточно средств.\n"
f"Доступно: {balance} руб.\n"
f"Минимум для вывода: {min_payout} руб."
```

✅ **Визуальная иерархия:**
```python
text = (
    "💎 **ОБМЕН НА ГЕНЕРАЦИИ**\n\n"  # Заголовок жирный
    "─────────────────\n"             # Разделитель
    f"💰 Баланс: **{balance} руб.**\n"  # Важное жирное
    f"Курс: {rate} руб/генерация\n"    # Обычное
)
```

✅ **Подтверждение критичных действий:**
```python
# Всегда показывать подтверждение перед:
# - Выводом денег
# - Обменом баланса
# - Изменением реквизитов
```

---

## 📦 АКТУАЛЬНЫЕ ФАЙЛЫ В GITHUB

### Основные файлы реализации

**Database:**
- `bot/database/models.py` - SQL-схемы и запросы
- `bot/database/db.py` - Методы работы с БД

**Handlers:**
- `bot/handlers/user_start.py` - Профиль и старт
- `bot/handlers/payment.py` - Начисление комиссий
- `bot/handlers/referral.py` - Реферальные действия
- `bot/handlers/admin.py` - Админ-панель

**States:**
- `bot/states/fsm.py` - ReferralStates, AdminStates

**Config:**
- `bot/config.py` - Конфигурация (BOT_USERNAME)

**Main:**
- `bot/main.py` - Регистрация роутеров

---

## ✅ ИТОГОВЫЙ ЧЕКЛИСТ

### Реализовано

- [x] Создание 4 новых таблиц БД
- [x] Расширение таблицы users
- [x] 7 настроек в settings
- [x] Генерация уникальных реферальных кодов
- [x] Обработка регистрации по реферальной ссылке
- [x] Начисление бонусов при регистрации
- [x] Автоматическое начисление комиссии от покупок
- [x] Конвертация рублей в генерации
- [x] Логирование всех операций
- [x] Обмен реферального баланса на генерации
- [x] Запрос выплаты с валидацией
- [x] 4 способа привязки реквизитов
- [x] Валидация телефона, карты, YooMoney
- [x] Маскирование реквизитов
- [x] История операций (earnings, exchanges, payouts)
- [x] Профиль с реферальной информацией
- [x] 4 кнопки реферальных действий
- [x] FSM состояния для всех флоу
- [x] Обработка ошибок
- [x] Логирование для отладки
- [x] Админ-панель (базовая)

---

## 🎓 FAQ

**Q: Можно ли изменить процент комиссии только для некоторых пользователей?**  
A: Да. Добавьте поле `custom_commission_percent` в таблицу users. В `_process_referral_commission()` сначала проверяйте это поле, если NULL — используйте дефолтное из settings.

**Q: Как сделать многоуровневую реферальную систему (2 уровня)?**  
A: Добавьте поле `referrer_level_2` в users. При регистрации по ссылке находите реферера, а затем его реферера (referred_by). Начисляйте меньший процент второму уровню.

**Q: Можно ли выплачивать автоматически через API банка?**  
A: Да. В `confirm_payout()` вместо создания заявки вызывайте API банка/платёжной системы, затем сразу меняйте status на 'completed'.

**Q: Как запретить вывод средств до N рефералов?**  
A: В `request_payout()` добавьте проверку:
```python
referrals_count = user_data.get('referrals_count', 0)
if referrals_count < 5:
    await callback.answer("⚠️ Минимум 5 рефералов для вывода")
    return
```

**Q: Как сделать лимит на вывод в день?**  
A: Добавьте поле `last_payout_date` и `payouts_today` в users. Проверяйте при запросе выплаты.

---

## 📞 SUPPORT

При возникновении проблем проверьте:

1. **Логи:** `grep REFERRAL bot.log`
2. **База данных:** SQL-диагностика (см. раздел выше)
3. **Callback handlers:** Все ли зарегистрированы
4. **States:** Правильно ли установлены и очищены
5. **Settings:** Корректны ли значения в БД

**Типичная последовательность отладки:**
```
1. Проверить логи на ошибки Python
2. Проверить БД на наличие полей
3. Проверить handlers на регистрацию
4. Проверить settings на корректные значения
5. Проверить пользовательские данные в users
```

---

## 📝 CHANGELOG

**v1.0.0 (03.12.2025):**
- ✅ Базовая реферальная система
- ✅ Начисление % от покупок
- ✅ Вывод денег (4 способа)
- ✅ Обмен на генерации
- ✅ История операций
- ✅ Админ-панель (базовая)

---

## 🎬 ЗАКЛЮЧЕНИЕ

**Реферальная программа полностью готова к работе:**

✅ База данных с 4 новыми таблицами  
✅ 25+ методов для работы с рефералами  
✅ Полный UI с 4 кнопками и историей  
✅ Начисление % от покупок автоматическое  
✅ Вывод денег с ручной обработкой админом  
✅ Обмен на генерации мгновенный  
✅ Настройки через settings гибкие  
✅ Логирование всех операций подробное  

**Готово к использованию в production и легко масштабируется!**

---

*Документация актуальна на: 03.12.2025*  
*Версия системы: 1.0.0*  
*Репозиторий: https://github.com/severand/InteriorBot-v2*
