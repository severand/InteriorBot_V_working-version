# 🏗️ InteriorBot - Архитектурная документация

**Версия:** 1.0  
**Дата последнего обновления:** 23.12.2025  
**Статус:** Production Ready

---

## 📋 Содержание

- [Обзор системы](#-обзор-системы)
- [Архитектурные принципы](#-архитектурные-принципы)
- [Архитектура по слоям](#-архитектура-по-слоям)
- [Компоненты системы](#-компоненты-системы)
- [Схемы потоков данных](#-схемы-потоков-данных)
- [Модель данных](#-модель-данных)
- [FSM State Machine](#-fsm-state-machine)
- [Single Menu Pattern](#-single-menu-pattern)
- [Внешние интеграции](#-внешние-интеграции)
- [Масштабируемость](#-масштабируемость)
- [Безопасность](#-безопасность)
- [Производительность](#-производительность)
- [Мониторинг и логирование](#-мониторинг-и-логирование)

---

## 🌐 Обзор системы

### Общая схема архитектуры

```mermaid
graph TB
    User[👤 Пользователь Telegram] --> Bot[🤖 Telegram Bot]
    
    Bot --> Dispatcher[Dispatcher aiogram 3.x]
    
    Dispatcher --> R1[Router: user_start]
    Dispatcher --> R2[Router: creation]
    Dispatcher --> R3[Router: payment]
    Dispatcher --> R4[Router: admin]
    Dispatcher --> R5[Router: referral]
    Dispatcher --> R6[Router: webhook]
    
    R1 --> KB[Keyboards]
    R2 --> KB
    R3 --> KB
    R4 --> KB
    R5 --> KB
    
    R1 --> DB[(SQLite Database)]
    R2 --> DB
    R3 --> DB
    R4 --> DB
    R5 --> DB
    R6 --> DB
    
    R2 --> Replicate[🎨 Replicate API]
    R3 --> YooKassa[💰 YooKassa API]
    R6 --> YooKassa
    
    DB --> Users[users]
    DB --> Payments[payments]
    DB --> Referrals[referrals]
    DB --> Menus[chat_menus]
    DB --> Designs[designs]
    
    style Bot fill:#32b8c6,stroke:#1d7480,color:#fff
    style Dispatcher fill:#5e407e,stroke:#3d2952,color:#fff
    style DB fill:#5e8040,stroke:#3d5229,color:#fff
    style Replicate fill:#ff8c42,stroke:#cc7035,color:#fff
    style YooKassa fill:#8b4789,stroke:#5c2e5a,color:#fff
```

### Ключевые характеристики

| Характеристика | Значение |
|----------------|----------|
| **Архитектурный стиль** | Monolithic + Event-Driven |
| **Язык программирования** | Python 3.11+ |
| **Фреймворк** | aiogram 3.x (асинхронный) |
| **База данных** | SQLite (асинхронный доступ через aiosqlite) |
| **Паттерны** | FSM, Repository, Single Menu Pattern, Observer |
| **Тип развёртывания** | Polling / Webhooks |
| **Масштабируемость** | Вертикальная (single instance) |

---

## 🎯 Архитектурные принципы

### 1. **Separation of Concerns (SoC)**

Каждый модуль имеет чёткую зону ответственности:
- **Handlers** — обработка событий Telegram
- **Services** — бизнес-логика и внешние API
- **Database** — доступ к данным
- **Keyboards** — генерация UI
- **Utils** — вспомогательные функции

### 2. **Single Responsibility Principle (SRP)**

Каждый класс/модуль выполняет только одну задачу:
```python
# ✅ Правильно
class Database:
    async def get_user(self, user_id): ...
    async def create_user(self, user_id): ...

class ReplicateAPI:
    async def generate_design(self, image_url, style): ...

# ❌ Неправильно
class UserHandler:
    async def get_user_from_db(self): ...  # Смешение concerns
    async def generate_ai_image(self): ...  # Смешение concerns
```

### 3. **Dependency Injection**

Зависимости передаются явно:
```python
# main.py
db = Database(config.DB_PATH)

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    # db инжектится через aiogram middleware
    user = await db.get_user(callback.from_user.id)
```

### 4. **Async/Await everywhere**

Все I/O операции асинхронные:
```python
# ✅ Асинхронные операции
await db.get_user(user_id)
await replicate_api.generate_design(...)
await bot.send_message(...)

# ❌ Блокирующие операции не используются
user = db.get_user_sync(user_id)  # Блокирует event loop!
```

### 5. **Single Menu Pattern (SMP)**

Одно редактируемое сообщение вместо множества:
```python
# ✅ Правильно
await edit_menu(callback, state, text, keyboard)

# ❌ Неправильно
await callback.message.answer(text)  # Создаёт новое сообщение
```

---

## 🏛️ Архитектура по слоям

```mermaid
graph LR
    subgraph "1. Presentation Layer"
        A[Telegram UI]
        B[Inline Keyboards]
        C[Reply Keyboards]
    end
    
    subgraph "2. Application Layer"
        D[Handlers]
        E[FSM States]
        F[Routers]
        G[Middlewares]
    end
    
    subgraph "3. Business Logic Layer"
        H[Creation Flow]
        I[Payment Flow]
        J[Referral System]
        K[Navigation Utils]
    end
    
    subgraph "4. Data Access Layer"
        L[Database Class]
        M[SQL Models]
        N[Query Builders]
    end
    
    subgraph "5. External Services"
        O[Replicate API]
        P[YooKassa API]
    end
    
    subgraph "6. Data Storage"
        Q[(SQLite DB)]
        R[chat_menus cache]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    F --> G
    E --> H
    E --> I
    E --> J
    H --> K
    I --> K
    J --> K
    H --> L
    I --> L
    J --> L
    L --> M
    M --> N
    N --> Q
    L --> R
    H --> O
    I --> P
    
    style A fill:#32b8c6,stroke:#1d7480,color:#fff
    style Q fill:#5e8040,stroke:#3d5229,color:#fff
    style O fill:#ff8c42,stroke:#cc7035,color:#fff
    style P fill:#8b4789,stroke:#5c2e5a,color:#fff
```

### Описание слоёв

#### 1. Presentation Layer (Уровень представления)

**Ответственность:** Отображение интерфейса пользователю

**Компоненты:**
- `keyboards/inline.py` - Inline-кнопки
- `keyboards/reply.py` - Reply-кнопки (не используются активно)
- `utils/texts.py` - Текстовые шаблоны

**Технологии:**
- Telegram Bot API
- Markdown форматирование
- InlineKeyboardMarkup

#### 2. Application Layer (Уровень приложения)

**Ответственность:** Обработка пользовательских событий

**Компоненты:**
- `handlers/user_start.py` - Старт, главное меню, профиль
- `handlers/creation.py` - Генерация дизайна
- `handlers/payment.py` - Покупка токенов
- `handlers/admin.py` - Административная панель
- `handlers/referral.py` - Реферальная система
- `handlers/webhook.py` - YooKassa webhooks
- `handlers/fallback.py` - Обработка ошибок
- `states/fsm.py` - FSM состояния

**Паттерны:**
- FSM (Finite State Machine)
- Command Pattern
- Chain of Responsibility

#### 3. Business Logic Layer (Уровень бизнес-логики)

**Ответственность:** Реализация бизнес-правил

**Компоненты:**
- `utils/navigation.py` - Навигация, edit_menu
- `utils/helpers.py` - Вспомогательные функции
- Логика реферальных начислений
- Логика расчёта стоимости
- Валидация данных

**Бизнес-правила:**
```python
# Начисление реферальных бонусов
LEVEL_1_PERCENT = 30  # 30% с покупок реферала 1-го уровня
LEVEL_2_PERCENT = 20  # 20% с покупок реферала 2-го уровня
LEVEL_3_PERCENT = 10  # 10% с покупок реферала 3-го уровня
REFERRAL_BONUS = 5    # +5 токенов за регистрацию реферала

# Стоимость генерации
GENERATION_COST = 1   # 1 токен за генерацию

# Начальный баланс
INITIAL_BALANCE = 3   # 3 бесплатных генерации
```

#### 4. Data Access Layer (Уровень доступа к данным)

**Ответственность:** CRUD операции с БД

**Компоненты:**
- `database/db.py` - Класс Database
- `database/models.py` - SQL схемы

**Паттерн:** Repository Pattern

```python
class Database:
    # Users
    async def create_user(self, user_id, username, first_name, referrer_id=None)
    async def get_user(self, user_id)
    async def update_balance(self, user_id, amount)
    
    # Payments
    async def save_payment(self, user_id, payment_id, amount, tokens, status)
    async def get_payment(self, payment_id)
    
    # Referrals
    async def add_referral(self, referrer_id, referral_id, level=1)
    async def get_referrals(self, user_id, level=1)
    
    # Chat Menus (Single Menu Pattern)
    async def save_chat_menu(self, chat_id, user_id, menu_message_id, screen_code)
    async def get_chat_menu(self, chat_id)
    
    # Designs
    async def save_design(self, user_id, original_url, generated_url, room_type, style)
    async def get_user_designs(self, user_id, limit=10)
```

#### 5. External Services Layer (Уровень внешних сервисов)

**Ответственность:** Интеграция с внешними API

**Компоненты:**
- `services/replicate_api.py` - Replicate AI
- `services/payment_api.py` - YooKassa

**Паттерн:** Adapter Pattern

```python
class ReplicateAPI:
    async def generate_design(
        self,
        image_url: str,
        room_type: str,
        style: str,
        prompt_addon: str = ""
    ) -> str:
        """Генерирует дизайн через Replicate API"""
        ...

class YooKassaAPI:
    async def create_payment(
        self,
        amount: float,
        description: str,
        metadata: dict
    ) -> Payment:
        """Создаёт платёж в YooKassa"""
        ...
    
    async def check_payment_status(self, payment_id: str) -> str:
        """Проверяет статус платежа"""
        ...
```

#### 6. Data Storage Layer (Уровень хранения данных)

**Ответственность:** Персистентность данных

**Компоненты:**
- SQLite база данных (`bot.db`)
- In-memory cache для `menu_message_id` (FSM)

---

## 🧩 Компоненты системы

### Дерево зависимостей

```mermaid
graph TD
    Main[main.py] --> Config[config.py]
    Main --> Loader[loader.py]
    Main --> DB[database/db.py]
    
    Loader --> Bot[Bot instance]
    Loader --> Dispatcher[Dispatcher]
    
    Main --> US[handlers/user_start.py]
    Main --> CR[handlers/creation.py]
    Main --> PM[handlers/payment.py]
    Main --> AD[handlers/admin.py]
    Main --> RF[handlers/referral.py]
    Main --> WH[handlers/webhook.py]
    Main --> FB[handlers/fallback.py]
    
    US --> States[states/fsm.py]
    CR --> States
    PM --> States
    AD --> States
    
    US --> KB[keyboards/inline.py]
    CR --> KB
    PM --> KB
    AD --> KB
    RF --> KB
    
    US --> Nav[utils/navigation.py]
    CR --> Nav
    PM --> Nav
    AD --> Nav
    RF --> Nav
    
    US --> Texts[utils/texts.py]
    CR --> Texts
    PM --> Texts
    
    CR --> RepAPI[services/replicate_api.py]
    PM --> PayAPI[services/payment_api.py]
    WH --> PayAPI
    
    DB --> Models[database/models.py]
    
    RepAPI --> Config
    PayAPI --> Config
    DB --> Config
    
    style Main fill:#32b8c6,stroke:#1d7480,color:#fff
    style DB fill:#5e8040,stroke:#3d5229,color:#fff
    style RepAPI fill:#ff8c42,stroke:#cc7035,color:#fff
    style PayAPI fill:#8b4789,stroke:#5c2e5a,color:#fff
```

### Основные компоненты

#### 1. **main.py** - Точка входа

```python
import asyncio
from loader import bot, dp
from database import Database
from handlers import user_start, creation, payment, admin, referral, webhook

async def main():
    # Инициализация БД
    db = Database(Config.DB_PATH)
    await db.init_db()
    
    # Регистрация роутеров
    dp.include_router(user_start.router)
    dp.include_router(creation.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    dp.include_router(referral.router)
    dp.include_router(webhook.router)
    
    # Запуск polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 2. **loader.py** - Инициализация Bot и Dispatcher

```python
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import Config

bot = Bot(token=Config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
```

#### 3. **config.py** - Конфигурация

```python
from dataclasses import dataclass
from os import getenv
from typing import List

@dataclass
class Config:
    BOT_TOKEN: str = getenv("BOT_TOKEN")
    ADMIN_IDS: List[int] = [int(x) for x in getenv("ADMIN_IDS", "").split(",")]
    
    REPLICATE_API_TOKEN: str = getenv("REPLICATE_API_TOKEN")
    
    YOOKASSA_SHOP_ID: str = getenv("YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY: str = getenv("YOOKASSA_SECRET_KEY")
    
    DB_PATH: str = getenv("DB_PATH", "bot.db")
    
    # Реферальная система
    REFERRAL_BONUS: int = int(getenv("REFERRAL_BONUS", "5"))
    REFERRAL_LEVEL_1_PERCENT: int = int(getenv("REFERRAL_LEVEL_1_PERCENT", "30"))
    REFERRAL_LEVEL_2_PERCENT: int = int(getenv("REFERRAL_LEVEL_2_PERCENT", "20"))
    REFERRAL_LEVEL_3_PERCENT: int = int(getenv("REFERRAL_LEVEL_3_PERCENT", "10"))
    
    GENERATION_TIMEOUT: int = int(getenv("GENERATION_TIMEOUT", "300"))
```

---

## 🔄 Схемы потоков данных

### 1. Поток генерации дизайна

```mermaid
sequenceDiagram
    actor User as 👤 Пользователь
    participant Bot as 🤖 Bot
    participant Handler as Creation Handler
    participant DB as 💾 Database
    participant FSM as 🔄 FSM State
    participant Replicate as 🎨 Replicate AI
    
    User->>Bot: /start
    Bot->>DB: create_user(user_id)
    DB-->>Bot: user_data (balance=3)
    Bot->>User: 📱 Главное меню
    
    User->>Bot: [🎨 Создать дизайн]
    Bot->>DB: get_balance(user_id)
    DB-->>Bot: balance=3
    Bot->>FSM: set_state(waiting_for_photo)
    Bot->>User: 📸 Загрузите фото комнаты
    
    User->>Bot: [Отправка фото]
    Handler->>FSM: save(photo_id)
    Handler->>FSM: set_state(choosing_room)
    Handler->>User: 🏠 Выберите тип помещения
    
    User->>Bot: [Гостиная]
    Handler->>FSM: save(room_type="Гостиная")
    Handler->>FSM: set_state(choosing_style)
    Handler->>User: 🎨 Выберите стиль
    
    User->>Bot: [Скандинавский]
    Handler->>DB: get_balance(user_id)
    DB-->>Handler: balance=3
    
    Handler->>DB: decrease_balance(user_id, 1)
    DB-->>Handler: new_balance=2
    
    Handler->>User: ⏳ Генерирую дизайн...
    
    Handler->>FSM: get_data()
    FSM-->>Handler: {photo_id, room_type, style}
    
    Handler->>Bot: download_file(photo_id)
    Bot-->>Handler: photo_bytes
    
    Handler->>Replicate: generate_design(photo, room, style)
    Note over Replicate: 2-5 минут обработки
    Replicate-->>Handler: generated_image_url
    
    Handler->>DB: save_design(user_id, original_url, generated_url, room, style)
    
    Handler->>User: ✨ Ваш новый дизайн [изображение]
    Handler->>FSM: set_state(None)
    Handler->>User: 💾 [Сохранить] [🔄 Ещё раз] [⬅️ В меню]
```

### 2. Поток оплаты через YooKassa

```mermaid
sequenceDiagram
    actor User as 👤 Пользователь
    participant Bot as 🤖 Bot
    participant Handler as Payment Handler
    participant DB as 💾 Database
    participant YK as 💰 YooKassa
    participant Browser as 🌐 Браузер
    
    User->>Bot: [💰 Купить токены]
    Bot->>User: 📦 Выберите пакет
    
    User->>Bot: [25 токенов - 490₽]
    Handler->>YK: create_payment(amount=490, tokens=25)
    YK-->>Handler: {payment_id, confirmation_url}
    
    Handler->>DB: save_payment(user_id, payment_id, 490, 25, "pending")
    
    Handler->>User: 💳 [Оплатить 490₽] [🔍 Проверить оплату]
    
    User->>Browser: Клик по кнопке "Оплатить"
    Browser->>YK: Переход на страницу оплаты
    
    User->>YK: Ввод данных карты
    YK-->>User: Оплата успешна
    YK->>Browser: redirect to return_url
    Browser->>Bot: /start?payment_success
    
    Bot->>Handler: handle_payment_return(user_id)
    Handler->>DB: get_last_pending_payment(user_id)
    DB-->>Handler: payment_id
    
    Handler->>YK: check_payment_status(payment_id)
    YK-->>Handler: status="succeeded"
    
    Handler->>DB: update_payment_status(payment_id, "succeeded")
    Handler->>DB: add_tokens(user_id, 25)
    DB-->>Handler: new_balance=28
    
    Handler->>User: ✅ Оплата успешна! Баланс: 28 токенов
    Handler->>User: 📱 Главное меню
```

### 3. Поток реферальной системы

```mermaid
sequenceDiagram
    actor Referrer as 👤 Реферер
    actor Referral as 🆕 Новый пользователь
    participant Bot as 🤖 Bot
    participant Handler as Referral Handler
    participant DB as 💾 Database
    
    Referrer->>Bot: [👥 Реферальная программа]
    Bot->>DB: get_user(referrer_id)
    DB-->>Bot: user_data
    Bot->>Referrer: 🔗 Ваша реферальная ссылка:\nt.me/bot?start=ref_123456789
    
    Referrer->>Referral: Отправка реферальной ссылки
    
    Referral->>Bot: /start ref_123456789
    Bot->>DB: user_exists(referral_id)?
    DB-->>Bot: false
    
    Bot->>DB: create_user(referral_id, referrer_id=123456789)
    Bot->>DB: add_referral(referrer_id=123456789, referral_id, level=1)
    
    Bot->>DB: add_tokens(referrer_id=123456789, 5)
    DB-->>Bot: new_balance
    
    Bot->>Referrer: 🎉 У вас новый реферал! +5 токенов
    Bot->>Referral: 👋 Добро пожаловать! +3 токена в подарок
    
    Note over Referral,DB: Реферал совершает покупку
    
    Referral->>Bot: Покупка 25 токенов за 490₽
    Bot->>DB: get_referrer(referral_id)
    DB-->>Bot: referrer_id=123456789, level=1
    
    Note over Handler: Расчёт вознаграждения
    Handler->>Handler: reward = 490 * 0.30 = 147₽ (30%)
    Handler->>Handler: tokens = 147 / 19.6 ≈ 7 токенов
    
    Handler->>DB: add_tokens(referrer_id=123456789, 7)
    Handler->>DB: update_referral_earnings(referrer_id, referral_id, 147)
    
    Bot->>Referrer: 💰 Ваш реферал купил токены! +7 токенов
```

### 4. Поток администрирования

```mermaid
sequenceDiagram
    actor Admin as 👨‍💼 Админ
    participant Bot as 🤖 Bot
    participant Handler as Admin Handler
    participant DB as 💾 Database
    participant Users as 👥 Пользователи
    
    Admin->>Bot: [⚙️ Админ-панель]
    Bot->>Handler: check_admin(admin_id)
    Handler->>Handler: admin_id in ADMIN_IDS?
    Handler-->>Bot: true
    
    Bot->>Admin: 🎛️ Админ-панель:\n- 👥 Пользователи\n- 💳 Платежи\n- 📊 Статистика\n- 📢 Рассылка
    
    Admin->>Bot: [👥 Пользователи]
    Bot->>Admin: 🔍 Поиск пользователя или просмотр всех?
    
    Admin->>Bot: [🔍 Поиск]
    Bot->>Admin: Введите ID или username
    
    Admin->>Bot: "@john_doe"
    Handler->>DB: search_user("@john_doe")
    DB-->>Handler: user_data
    
    Bot->>Admin: 👤 Пользователь найден:\nID: 987654321\nИмя: John Doe\nБаланс: 15 токенов\nВсего генераций: 42
    Bot->>Admin: [➕ Добавить токены] [➖ Списать токены] [📊 Статистика]
    
    Admin->>Bot: [➕ Добавить токены]
    Bot->>Admin: Введите количество токенов
    
    Admin->>Bot: "10"
    Handler->>DB: add_tokens(987654321, 10)
    DB-->>Handler: new_balance=25
    
    Bot->>Admin: ✅ Успешно! Новый баланс: 25 токенов
    Bot->>Users: 🎁 Вам начислено 10 токенов от администратора
```

---

## 💾 Модель данных

### ER-диаграмма базы данных

```mermaid
erDiagram
    USERS ||--o{ PAYMENTS : makes
    USERS ||--o{ REFERRALS : refers
    USERS ||--o{ REFERRALS : "referred by"
    USERS ||--o{ DESIGNS : creates
    USERS ||--o{ CHAT_MENUS : has
    
    USERS {
        INTEGER id PK
        TEXT username
        TEXT first_name
        INTEGER balance
        TEXT created_at
        INTEGER referrer_id FK
        REAL total_spent
        INTEGER total_generations
        TEXT language_code
    }
    
    PAYMENTS {
        INTEGER id PK
        TEXT payment_id UK
        INTEGER user_id FK
        REAL amount
        INTEGER tokens
        TEXT status
        TEXT created_at
        TEXT updated_at
    }
    
    REFERRALS {
        INTEGER id PK
        INTEGER referrer_id FK
        INTEGER referral_id FK
        INTEGER level
        REAL earned_total
        TEXT created_at
    }
    
    DESIGNS {
        INTEGER id PK
        INTEGER user_id FK
        TEXT original_photo_url
        TEXT generated_photo_url
        TEXT room_type
        TEXT style
        TEXT created_at
    }
    
    CHAT_MENUS {
        INTEGER chat_id PK
        INTEGER user_id
        INTEGER menu_message_id
        TEXT screen_code
        TEXT updated_at
    }
```

### Описание таблиц

#### 1. **users** - Пользователи

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,              -- Telegram user_id
    username TEXT,                       -- @username
    first_name TEXT,                     -- Имя пользователя
    balance INTEGER DEFAULT 3,           -- Баланс токенов
    created_at TEXT NOT NULL,            -- Дата регистрации
    referrer_id INTEGER,                 -- Кто пригласил
    total_spent REAL DEFAULT 0,          -- Всего потрачено ₽
    total_generations INTEGER DEFAULT 0, -- Всего генераций
    language_code TEXT DEFAULT 'ru',     -- Язык интерфейса
    FOREIGN KEY (referrer_id) REFERENCES users(id)
);

CREATE INDEX idx_users_referrer ON users(referrer_id);
CREATE INDEX idx_users_created ON users(created_at);
```

**Бизнес-правила:**
- `balance` не может быть отрицательным
- При регистрации `balance = 3` (3 бесплатные генерации)
- `total_spent` обновляется при успешной оплате
- `total_generations` инкрементируется при каждой генерации

#### 2. **payments** - Платежи

```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id TEXT UNIQUE NOT NULL,     -- ID платежа в YooKassa
    user_id INTEGER NOT NULL,            -- Кто платит
    amount REAL NOT NULL,                -- Сумма в рублях
    tokens INTEGER NOT NULL,             -- Количество токенов
    status TEXT NOT NULL,                -- pending/succeeded/canceled
    created_at TEXT NOT NULL,            -- Дата создания
    updated_at TEXT,                     -- Дата обновления
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_created ON payments(created_at);
```

**Статусы:**
- `pending` - ожидает оплаты
- `succeeded` - успешно оплачен
- `canceled` - отменён

#### 3. **referrals** - Реферальная система

```sql
CREATE TABLE referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,        -- Реферер (кто пригласил)
    referral_id INTEGER NOT NULL,        -- Реферал (кого пригласили)
    level INTEGER DEFAULT 1,             -- Уровень (1-3)
    earned_total REAL DEFAULT 0,         -- Всего заработано ₽
    created_at TEXT NOT NULL,
    FOREIGN KEY (referrer_id) REFERENCES users(id),
    FOREIGN KEY (referral_id) REFERENCES users(id),
    UNIQUE(referrer_id, referral_id)
);

CREATE INDEX idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX idx_referrals_referral ON referrals(referral_id);
CREATE INDEX idx_referrals_level ON referrals(level);
```

**Уровни:**
- `level = 1` - прямой реферал (30%)
- `level = 2` - реферал 2-го уровня (20%)
- `level = 3` - реферал 3-го уровня (10%)

#### 4. **designs** - История генераций

```sql
CREATE TABLE designs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    original_photo_url TEXT,             -- Исходное фото
    generated_photo_url TEXT,            -- Сгенерированный дизайн
    room_type TEXT NOT NULL,             -- Тип помещения
    style TEXT NOT NULL,                 -- Стиль
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_designs_user ON designs(user_id);
CREATE INDEX idx_designs_created ON designs(created_at);
```

#### 5. **chat_menus** - Единое меню (SMP)

```sql
CREATE TABLE chat_menus (
    chat_id INTEGER PRIMARY KEY,         -- ID чата
    user_id INTEGER NOT NULL,            -- Владелец меню
    menu_message_id INTEGER NOT NULL,    -- ID сообщения с меню
    screen_code TEXT,                    -- Текущий экран
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_chat_menus_user ON chat_menus(user_id);
```

**Коды экранов (`screen_code`):**
- `main_menu` - главное меню
- `profile` - профиль
- `creation_waiting_photo` - ожидание фото
- `creation_choosing_room` - выбор типа комнаты
- `creation_choosing_style` - выбор стиля
- `payment_choosing_package` - выбор пакета токенов
- `admin_panel` - админ-панель
- `referral_stats` - статистика рефералов

---

## 🔄 FSM State Machine

### Диаграмма состояний генерации дизайна

```mermaid
stateDiagram-v2
    [*] --> MainMenu
    
    MainMenu --> WaitingPhoto : [🎨 Создать дизайн]
    
    WaitingPhoto --> ChoosingRoom : Фото загружено
    WaitingPhoto --> MainMenu : [❌ Отмена]
    
    ChoosingRoom --> ChoosingStyle : Комната выбрана
    ChoosingRoom --> WaitingPhoto : [◀️ Назад]
    ChoosingRoom --> MainMenu : [❌ Отмена]
    
    ChoosingStyle --> Generating : Стиль выбран
    ChoosingStyle --> ChoosingRoom : [◀️ Назад]
    ChoosingStyle --> MainMenu : [❌ Отмена]
    
    Generating --> Result : Генерация завершена
    Generating --> Error : Ошибка генерации
    
    Result --> WaitingPhoto : [🔄 Ещё раз]
    Result --> MainMenu : [⬅️ В меню]
    
    Error --> MainMenu : [⬅️ В меню]
```

### Определение состояний (states/fsm.py)

```python
from aiogram.fsm.state import State, StatesGroup

class CreationForm(StatesGroup):
    """Состояния процесса генерации дизайна"""
    waiting_for_photo = State()  # Ожидание загрузки фото
    choosing_room = State()      # Выбор типа помещения
    choosing_style = State()     # Выбор стиля

class AdminForm(StatesGroup):
    """Состояния админ-панели"""
    searching_user = State()     # Поиск пользователя
    adding_balance = State()     # Добавление баланса
    removing_balance = State()   # Списание баланса
    broadcasting_message = State() # Рассылка сообщения

class PaymentForm(StatesGroup):
    """Состояния оплаты"""
    waiting_payment_check = State() # Ожидание проверки оплаты
```

### Переходы между состояниями

```python
# Установка состояния
await state.set_state(CreationForm.waiting_for_photo)

# Сохранение данных в состоянии
await state.update_data(
    photo_id="AgACAgIAAxkBAAI...",
    menu_message_id=12345
)

# Получение данных
data = await state.get_data()
photo_id = data.get('photo_id')

# Переход к следующему состоянию
await state.set_state(CreationForm.choosing_room)

# Сброс состояния (сохраняет данные)
await state.set_state(None)

# Полный сброс (удаляет всё)
await state.clear()
```

---

## 📱 Single Menu Pattern (SMP)

### Концепция

**Проблема:** При создании нового сообщения для каждого экрана чат заполняется старыми сообщениями и неактивными кнопками.

**Решение:** Использовать одно сообщение, которое редактируется при переходах между экранами.

### Реализация

```python
# utils/navigation.py

async def edit_menu(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard,
    show_balance: bool = False,
    parse_mode: str = "Markdown"
):
    """
    Редактирует существующее единое меню.
    
    Args:
        callback: Callback от Telegram
        state: FSM состояние
        text: Новый текст сообщения
        keyboard: Новая клавиатура
        show_balance: Автоматически добавить баланс в текст
        parse_mode: Режим парсинга (Markdown/HTML)
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    # 1. Получаем menu_message_id из FSM
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    # 2. Если нет в FSM, пробуем получить из БД
    if not menu_message_id:
        menu_info = await db.get_chat_menu(chat_id)
        if menu_info:
            menu_message_id = menu_info.get('menu_message_id')
    
    # 3. Если всё ещё нет, используем текущее сообщение
    if not menu_message_id:
        menu_message_id = callback.message.message_id
    
    # 4. Добавляем баланс если нужно
    if show_balance:
        balance = await db.get_balance(user_id)
        text = f"💰 Баланс: {balance} токенов\n\n{text}"
    
    # 5. Пытаемся отредактировать
    try:
        await callback.message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            # Текст не изменился - это нормально
            pass
        elif "message to edit not found" in str(e).lower():
            # Сообщение удалено - создаём новое
            await delete_old_menu_if_exists(callback.message)
            new_msg = await callback.message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            menu_message_id = new_msg.message_id
        else:
            raise
    
    # 6. Сохраняем menu_message_id
    await state.update_data(menu_message_id=menu_message_id)
    await db.save_chat_menu(
        chat_id=chat_id,
        user_id=user_id,
        menu_message_id=menu_message_id,
        screen_code=callback.data  # Сохраняем текущий экран
    )
```

### Использование

```python
# handlers/user_start.py

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    # ✅ Правильно - редактирует существующее меню
    await edit_menu(
        callback=callback,
        state=state,
        text="🏠 Главное меню",
        keyboard=get_main_keyboard(),
        show_balance=True
    )
    
    # ❌ Неправильно - создаёт новое сообщение
    # await callback.message.answer("🏠 Главное меню", reply_markup=keyboard)
```

### Критические правила

```python
# ✅ ПРАВИЛЬНО: При навигации между меню
await state.set_state(None)  # Сбрасывает ТОЛЬКО состояние, данные остаются

# ❌ НЕПРАВИЛЬНО: При навигации между меню
await state.clear()  # Удаляет ВСЁ, включая menu_message_id!

# ✅ ПРАВИЛЬНО: Полный сброс (команда /start, выход)
await state.clear()
```

---

## 🔌 Внешние интеграции

### 1. Replicate AI API

**Назначение:** Генерация дизайна интерьера через AI

**Модель:** `jagilley/controlnet-hough` или аналогичные для интерьера

**Архитектура интеграции:**

```mermaid
sequenceDiagram
    participant Handler
    participant ReplicateAPI
    participant Replicate
    
    Handler->>ReplicateAPI: generate_design(image_url, room, style)
    ReplicateAPI->>ReplicateAPI: Формирование промпта
    ReplicateAPI->>Replicate: predictions.create()
    Replicate-->>ReplicateAPI: prediction_id
    
    loop Ожидание (polling)
        ReplicateAPI->>Replicate: predictions.get(prediction_id)
        Replicate-->>ReplicateAPI: status="processing"
        ReplicateAPI->>ReplicateAPI: sleep(5 сек)
    end
    
    ReplicateAPI->>Replicate: predictions.get(prediction_id)
    Replicate-->>ReplicateAPI: status="succeeded", output=[image_url]
    ReplicateAPI-->>Handler: image_url
```

**Реализация:**

```python
# services/replicate_api.py

import replicate
from config import Config

class ReplicateAPI:
    def __init__(self):
        self.client = replicate.Client(api_token=Config.REPLICATE_API_TOKEN)
    
    async def generate_design(
        self,
        image_url: str,
        room_type: str,
        style: str,
        prompt_addon: str = ""
    ) -> str:
        """
        Генерирует дизайн интерьера.
        
        Args:
            image_url: URL исходного фото комнаты
            room_type: Тип помещения ("Гостиная", "Спальня", ...)
            style: Стиль дизайна ("Скандинавский", "Лофт", ...)
            prompt_addon: Дополнительные параметры промпта
        
        Returns:
            URL сгенерированного изображения
        """
        # Формируем промпт
        prompt = self._build_prompt(room_type, style, prompt_addon)
        
        # Запускаем генерацию
        prediction = self.client.predictions.create(
            version="MODEL_VERSION_HERE",
            input={
                "image": image_url,
                "prompt": prompt,
                "num_samples": 1,
                "image_resolution": "512",
                "ddim_steps": 20,
                "scale": 9,
                "a_prompt": "best quality, extremely detailed, modern",
                "n_prompt": "lowres, bad quality, blurry, distorted"
            }
        )
        
        # Ожидаем завершения (с таймаутом)
        prediction.wait(timeout=Config.GENERATION_TIMEOUT)
        
        if prediction.status == "succeeded":
            return prediction.output[0]
        else:
            raise Exception(f"Generation failed: {prediction.error}")
    
    def _build_prompt(self, room_type: str, style: str, addon: str) -> str:
        """Формирует промпт для генерации"""
        base = f"{style} style {room_type} interior design"
        if addon:
            base += f", {addon}"
        return base
```

### 2. YooKassa Payment API

**Назначение:** Приём платежей за токены

**Архитектура интеграции:**

```mermaid
sequenceDiagram
    participant Handler
    participant YooKassaAPI
    participant YooKassa
    participant User
    
    Handler->>YooKassaAPI: create_payment(amount, tokens)
    YooKassaAPI->>YooKassa: Payment.create()
    YooKassa-->>YooKassaAPI: {payment_id, confirmation_url}
    YooKassaAPI-->>Handler: payment_data
    
    Handler->>User: Отправка ссылки на оплату
    User->>YooKassa: Оплата через браузер
    YooKassa-->>User: Успешно
    YooKassa->>Handler: Redirect to return_url
    
    Handler->>YooKassaAPI: check_payment_status(payment_id)
    YooKassaAPI->>YooKassa: Payment.find_one(payment_id)
    YooKassa-->>YooKassaAPI: {status: "succeeded"}
    YooKassaAPI-->>Handler: "succeeded"
    
    Handler->>Handler: Начисление токенов
```

**Реализация:**

```python
# services/payment_api.py

from yookassa import Configuration, Payment
from config import Config

class YooKassaAPI:
    def __init__(self):
        Configuration.account_id = Config.YOOKASSA_SHOP_ID
        Configuration.secret_key = Config.YOOKASSA_SECRET_KEY
    
    async def create_payment(
        self,
        amount: float,
        tokens: int,
        user_id: int,
        description: str = None
    ) -> dict:
        """
        Создаёт платёж в YooKassa.
        
        Args:
            amount: Сумма в рублях
            tokens: Количество токенов
            user_id: ID пользователя
            description: Описание платежа
        
        Returns:
            dict с payment_id и confirmation_url
        """
        if not description:
            description = f"{tokens} токенов для генерации дизайна"
        
        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{Config.BOT_LINK}?start=payment_success"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": user_id,
                "tokens": tokens
            }
        })
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status
        }
    
    async def check_payment_status(self, payment_id: str) -> str:
        """
        Проверяет статус платежа.
        
        Returns:
            "pending" | "succeeded" | "canceled"
        """
        payment = Payment.find_one(payment_id)
        return payment.status
```

---

## 📈 Масштабируемость

### Текущие ограничения

| Компонент | Ограничение | Причина |
|-----------|-------------|--------|
| **База данных** | ~100K пользователей | SQLite single-file |
| **Параллельные генерации** | 1-2 одновременно | Синхронная обработка |
| **Пропускная способность** | ~100 req/sec | Polling, single instance |
| **Хранилище** | Диск сервера | Локальные файлы |

### Стратегия горизонтального масштабирования

```mermaid
graph TB
    LB[Load Balancer] --> Bot1[Bot Instance 1]
    LB --> Bot2[Bot Instance 2]
    LB --> Bot3[Bot Instance 3]
    
    Bot1 --> Redis[(Redis<br/>FSM Storage)]
    Bot2 --> Redis
    Bot3 --> Redis
    
    Bot1 --> PG[(PostgreSQL<br/>Main Database)]
    Bot2 --> PG
    Bot3 --> PG
    
    Bot1 --> Queue[Task Queue<br/>Celery/RQ]
    Bot2 --> Queue
    Bot3 --> Queue
    
    Queue --> W1[Worker 1]
    Queue --> W2[Worker 2]
    Queue --> W3[Worker 3]
    
    W1 --> Replicate[Replicate API]
    W2 --> Replicate
    W3 --> Replicate
    
    W1 --> S3[S3 Storage]
    W2 --> S3
    W3 --> S3
```

### План миграции на production

#### Этап 1: Миграция БД (до 10K пользователей)
```python
# SQLite → PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    echo=False
)
```

#### Этап 2: Внешнее хранилище FSM (до 50K пользователей)
```python
# MemoryStorage → RedisStorage
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url("redis://localhost:6379")
dp = Dispatcher(storage=storage)
```

#### Этап 3: Очередь задач (до 100K пользователей)
```python
# Celery для фоновых задач
from celery import Celery

app = Celery('interiorbot', broker='redis://localhost:6379')

@app.task
async def generate_design_task(user_id, photo_url, room, style):
    result = await replicate_api.generate_design(...)
    await notify_user(user_id, result)
```

#### Этап 4: Webhooks вместо polling (100K+ пользователей)
```python
# Webhooks для production
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

async def on_startup(bot: Bot):
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")

app = web.Application()
webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
webhook_requests_handler.register(app, path="/webhook")
web.run_app(app, host="0.0.0.0", port=8080)
```

---

## 🔒 Безопасность

### Реализованные меры

#### 1. Защита конфиденциальных данных
```python
# .env файл (не коммитится в Git)
BOT_TOKEN=123456:ABC-DEF...
REPLICATE_API_TOKEN=r8_...
YOOKASSA_SECRET_KEY=live_...

# .gitignore
.env
bot.db
*.log
```

#### 2. Валидация пользовательского ввода
```python
@router.message(AdminForm.adding_balance)
async def process_balance_add(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount <= 0 or amount > 10000:
            raise ValueError("Invalid amount")
    except ValueError:
        await message.answer("❌ Введите число от 1 до 10000")
        return
    
    # Безопасная обработка
    ...
```

#### 3. Проверка прав доступа
```python
@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in Config.ADMIN_IDS:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    # Админ-функционал
    ...
```

#### 4. Rate limiting (планируется)
```python
from aiogram.utils.rate_limit import rate_limit

@router.message()
@rate_limit(limit=10, key="default")  # 10 сообщений в минуту
async def handle_message(message: Message):
    ...
```

#### 5. SQL Injection защита
```python
# ✅ Параметризованные запросы (защита от SQL injection)
async def get_user(self, user_id: int):
    async with aiosqlite.connect(self.db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        return await cursor.fetchone()

# ❌ НЕ делайте так!
async def get_user_UNSAFE(self, user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection!
```

---

## ⚡ Производительность

### Метрики

| Операция | Среднее время | Целевое время |
|----------|---------------|---------------|
| Создание пользователя | ~50ms | <100ms |
| Получение пользователя из БД | ~10ms | <50ms |
| Генерация дизайна (Replicate) | 2-5 мин | <3 мин |
| Создание платежа (YooKassa) | ~200ms | <500ms |
| Редактирование меню | ~50ms | <200ms |

### Оптимизации

#### 1. Кэширование часто используемых данных
```python
# Кэш меню в памяти
menu_cache = {}

async def get_chat_menu_cached(chat_id: int):
    if chat_id in menu_cache:
        return menu_cache[chat_id]
    
    menu = await db.get_chat_menu(chat_id)
    menu_cache[chat_id] = menu
    return menu
```

#### 2. Индексы базы данных
```sql
-- Индексы для быстрого поиска
CREATE INDEX idx_users_referrer ON users(referrer_id);
CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_referrals_referrer ON referrals(referrer_id);
```

#### 3. Асинхронные операции
```python
# ✅ Параллельное выполнение
import asyncio

user, balance, designs = await asyncio.gather(
    db.get_user(user_id),
    db.get_balance(user_id),
    db.get_user_designs(user_id, limit=5)
)

# ❌ Последовательное выполнение (медленно)
user = await db.get_user(user_id)
balance = await db.get_balance(user_id)
designs = await db.get_user_designs(user_id, limit=5)
```

---

## 📊 Мониторинг и логирование

### Система логирования

```python
import logging
from logging.handlers import RotatingFileHandler

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ротация логов (10MB макс, 5 файлов)
handler = RotatingFileHandler(
    'bot.log',
    maxBytes=10*1024*1024,
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Структура логов

```python
# Уровни логирования
logger.debug(f"FSM data: {data}")  # Отладочная информация
logger.info(f"User {user_id} created")  # Информационные сообщения
logger.warning(f"Low balance: {balance}")  # Предупреждения
logger.error(f"Payment failed: {payment_id}")  # Ошибки
logger.critical(f"Database connection lost!")  # Критические ошибки
```

### Метрики для мониторинга

```python
# Пример сбора метрик
class Metrics:
    total_users = 0
    total_generations = 0
    total_payments = 0
    active_users_today = 0
    
    @classmethod
    async def log_generation(cls, user_id: int):
        cls.total_generations += 1
        logger.info(f"Generation #{cls.total_generations} by user {user_id}")
    
    @classmethod
    async def log_payment(cls, user_id: int, amount: float):
        cls.total_payments += 1
        logger.info(f"Payment #{cls.total_payments}: {amount}₽ by user {user_id}")
```

---

## 📝 Changelog

### Version 1.0 (23.12.2025)
- ✅ Создана базовая архитектурная документация
- ✅ Описаны все слои системы
- ✅ Добавлены диаграммы потоков данных
- ✅ Документированы паттерны разработки
- ✅ Описана модель данных
- ✅ Добавлены рекомендации по масштабированию

---

## 🔗 Связанные документы

- [README.md](README.md) - Основная документация проекта
- [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) - Правила разработки
- [FSM_GUIDE.md](FSM_GUIDE.md) - Гайд по FSM
- [REFERRAL_SYSTEM.md](REFERRAL_SYSTEM.md) - Реферальная система
- [DEPLOYMENT.md](DEPLOYMENT.md) - Развёртывание

---

<p align="center">
  <strong>Архитектурная документация InteriorBot v1.0</strong><br/>
  Создано с ❤️ для разработчиков и архитекторов
</p>