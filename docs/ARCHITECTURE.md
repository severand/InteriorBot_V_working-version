# 🏗️ ARCHITECTURE - Полная архитектура InteriorBot v1

**Документация уровня: Deep Technical**  
**Последнее обновление:** December 12, 2025  
**Версия:** 2.0

---

## 📋 Оглавление

1. [System Overview](#system-overview)
2. [Project Structure](#project-structure)
3. [Component Architecture](#component-architecture)
4. [Database Schema](#database-schema)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [FSM State Machine](#fsm-state-machine)
7. [API Integration](#api-integration)
8. [Error Handling](#error-handling)
9. [Security](#security)
10. [Performance](#performance)

---

## 🎯 System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TELEGRAM CLIENT (User)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ (TelegramBotAPI)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BOT/MAIN.PY                                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  aiogram     │  │  Dispatcher  │  │  Long Poll   │         │
│  │  3.x Engine  │  │  (routers)   │  │  Manager     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────┬──────────────────┬─────────────────┬──────────────────────┘
     │                  │                 │
     ▼                  ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ user_start   │  │ creation     │  │ payment      │
│ .router      │  │ .router      │  │ .router      │
│              │  │              │  │              │
│ 3 handlers   │  │ 6 handlers   │  │ 3 handlers   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────────┬────┴────────┬────────┘
                    ▼             ▼
        ┌────────────────────────────────┐
        │   Services Layer               │
        │ ┌──────────────┐ ┌──────────┐ │
        │ │ replicate_   │ │ payment_ │ │
        │ │ api.py       │ │ api.py   │ │
        │ └──────────────┘ └──────────┘ │
        └────┬───────────────────┬──────┘
             │                   │
             ▼                   ▼
      ┌─────────────┐     ┌──────────────┐
      │ Replicate   │     │ YooKassa     │
      │ AI API      │     │ Payment API  │
      └─────────────┘     └──────────────┘
             │
             ▼
      ┌─────────────┐
      │ Telegram    │
      │ File API    │
      └─────────────┘
                    ┌──────────────────────┐
                    │                      │
                    ▼                      ▼
        ┌─────────────────────┐  ┌──────────────────┐
        │  Database Layer     │  │  Keyboard/States │
        │                     │  │                  │
        │ ┌───────────────┐   │  │ ┌──────────────┐ │
        │ │ db.py         │   │  │ │ keyboards/   │ │
        │ │ (async ops)   │   │  │ │ inline.py    │ │
        │ └───────────────┘   │  │ └──────────────┘ │
        │ ┌───────────────┐   │  │ ┌──────────────┐ │
        │ │ models.py     │   │  │ │ states/fsm   │ │
        │ │ (SQL queries) │   │  │ │ .py          │ │
        │ └───────────────┘   │  │ └──────────────┘ │
        └─────────────┬────────┘  └──────────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │    SQLite Database      │
        │  (bot.db)               │
        │                         │
        │ ┌─────────────────────┐ │
        │ │ users table         │ │
        │ │ - user_id (PK)      │ │
        │ │ - username          │ │
        │ │ - balance           │ │
        │ │ - reg_date          │ │
        │ └─────────────────────┘ │
        │                         │
        │ ┌─────────────────────┐ │
        │ │ payments table      │ │
        │ │ - id (PK)           │ │
        │ │ - user_id (FK)      │ │
        │ │ - yookassa_id       │ │
        │ │ - amount            │ │
        │ │ - tokens            │ │
        │ │ - status            │ │
        │ │ - created_at        │ │
        │ └─────────────────────┘ │
        └─────────────────────────┘
```

### Design Principles

1. **Asynchronous First** - All I/O operations are async
2. **Single Responsibility** - Each module has one clear purpose
3. **Single Menu Pattern** - All navigation edits one message
4. **Type Safety** - Full type hints throughout
5. **State Isolation** - FSM state managed separately from persistent data
6. **Error Resilience** - Graceful degradation and error handling
7. **Admin Exception** - Special handling for admin users

---

## 📁 Project Structure

### Complete Directory Tree

```
InteriorBot/
│
├── bot/                                 # Main application package
│   ├── __init__.py
│   ├── main.py                         # Entry point - Bot initialization & polling
│   ├── config.py                       # Configuration, constants, admin IDs
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                       # Database class (async layer)
│   │   │   └── Methods:
│   │   │       ├── init_db()           # Create tables
│   │   │       ├── create_user()       # New user registration
│   │   │       ├── get_user()          # Fetch user data
│   │   │       ├── get_balance()       # Get generation balance
│   │   │       ├── decrease_balance()  # Deduct balance
│   │   │       ├── increase_balance()  # Add balance
│   │   │       ├── create_payment()    # Record payment
│   │   │       ├── get_last_pending_payment()
│   │   │       ├── set_payment_success()
│   │   │       └── add_tokens()        # Alias for increase_balance
│   │   │
│   │   └── models.py                   # SQL queries & schema
│   │       ├── CREATE_USERS_TABLE
│   │       ├── CREATE_PAYMENTS_TABLE
│   │       ├── INSERT_USER
│   │       ├── SELECT_USER
│   │       └── ... (18 SQL queries total)
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   │
│   │   ├── user_start.py               # User initialization & navigation
│   │   │   └── Handlers:
│   │   │       ├── cmd_start()         # /start command
│   │   │       ├── back_to_main_menu() # Navigation to main
│   │   │       ├── show_profile()      # Profile display
│   │   │       ├── buy_generations_handler()  # Redirect to payment
│   │   │       ├── start_creation()    # Init design creation
│   │   │       └── ... (2 more)
│   │   │
│   │   ├── creation.py                 # Design generation flow (FSM)
│   │   │   └── Handlers:
│   │   │       ├── go_to_main_menu()   # Main menu fallback
│   │   │       ├── choose_new_photo()  # Photo upload init
│   │   │       ├── photo_uploaded()    # Photo processing (state: waiting_for_photo)
│   │   │       ├── room_chosen()       # Room type selection (state: choose_room)
│   │   │       ├── back_to_room_selection()  # Back navigation
│   │   │       ├── style_chosen()      # Style selection & GENERATION (state: choose_style)
│   │   │       ├── change_style_after_gen()  # Alternative style
│   │   │       ├── show_profile_handler()
│   │   │       └── block_all_text_messages()  # Block spam
│   │   │
│   │   └── payment.py                  # Payment processing
│   │       └── Handlers:
│   │           ├── show_packages()     # Show pricing tiers
│   │           ├── create_payment()    # Create YooKassa payment
│   │           ├── check_payment()     # Verify payment status
│   │           ├── back_to_main_menu()  # Navigation
│   │           └── show_profile_payment()  # Profile from payment
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   │
│   │   ├── replicate_api.py            # AI image generation
│   │   │   └── Functions:
│   │   │       ├── generate_image()    # Main generation function
│   │   │       │   ├── Get image from Telegram
│   │   │       │   ├── Encode to base64
│   │   │       │   ├── Build AI prompt
│   │   │       │   ├── Call Replicate API
│   │   │       │   ├── Handle errors
│   │   │       │   └── Return image URL
│   │   │       └── Error handling: httpx, timeout, API errors
│   │   │
│   │   └── payment_api.py              # YooKassa integration
│   │       └── Functions:
│   │           ├── create_payment_yookassa()  # Create payment
│   │           │   ├── Init YooKassa client
│   │           │   ├── Create payment object
│   │           │   └── Return payment data
│   │           └── find_payment()      # Check payment status
│   │               └── Return True if succeeded, False if pending
│   │
│   ├── keyboards/
│   │   ├── __init__.py
│   │   │
│   │   └── inline.py                   # Inline keyboard builders
│   │       └── Functions:
│   │           ├── get_main_menu_keyboard()   # 2 buttons: Create, Profile
│   │           ├── get_profile_keyboard()     # 2 buttons: Buy, Menu
│   │           ├── get_room_keyboard()        # 4 rooms + 2 nav
│   │           ├── get_style_keyboard()       # 10 styles (2 per row) + 2 nav
│   │           ├── get_payment_keyboard()     # 3 packages + 2 nav
│   │           ├── get_payment_check_keyboard()  # Payment URL + Check button
│   │           └── get_post_generation_keyboard()  # 4 post-gen options
│   │
│   ├── states/
│   │   ├── __init__.py
│   │   │
│   │   └── fsm.py                      # FSM State definitions
│   │       └── CreationStates (StatesGroup):
│   │           ├── waiting_for_photo     # Awaiting user photo
│   │           ├── choose_room           # Room type selection
│   │           └── choose_style          # Style selection (generation trigger)
│   │
│   └── utils/
│       ├── __init__.py
│       │
│       ├── texts.py                    # All bot messages (templates)
│       │   ├── START_TEXT
│       │   ├── MAIN_MENU_TEXT
│       │   ├── PROFILE_TEXT  (uses .format())
│       │   ├── CHOOSE_STYLE_TEXT
│       │   ├── NO_BALANCE_TEXT
│       │   ├── GENERATION_PROCESSING_TEXT
│       │   └── ... (20+ message templates)
│       │
│       ├── navigation.py               # Navigation helpers
│       │   └── Functions:
│       │       ├── edit_menu()         # Edit existing menu message
│       │       ├── show_main_menu()    # Show main menu from any state
│       │       └── show_single_menu()  # Single menu pattern logic
│       │
│       └── helpers.py                  # Utility functions
│           └── Functions:
│               ├── format_balance()    # Format balance for display
│               ├── get_room_name()     # Translate room type
│               └── get_style_name()    # Translate style name
│
├── bot.db                              # SQLite database (created at runtime)
├── bot.log                             # Application logs (optional)
│
├── requirements.txt                    # Python dependencies
│   ├── aiogram==3.x.x
│   ├── aiosqlite==0.19.x
│   ├── replicate==0.x.x
│   ├── yookassa==3.x.x
│   ├── httpx==0.x.x
│   ├── python-dotenv==1.x.x
│   └── ... (7 total)
│
├── .env                                # Environment variables (LOCAL ONLY)
│   ├── BOT_TOKEN=xxx
│   ├── REPLICATE_API_TOKEN=xxx
│   ├── YOOKASSA_SHOP_ID=xxx
│   └── YOOKASSA_SECRET_KEY=xxx
│
├── .env.example                        # Template for .env
├── .gitignore                          # Git ignore rules
│   ├── *.db (don't commit database)
│   ├── .env (don't commit secrets)
│   ├── __pycache__/
│   └── venv/
│
└── README.md                           # Project overview
```

### Key File Relationships

```
main.py
├── imports: config (BOT_TOKEN, ADMIN_IDS)
├── imports: database.db (Database class)
├── imports: handlers.user_start
├── imports: handlers.creation
├── imports: handlers.payment
└── registers: routers, starts dispatcher

handlers/user_start.py
├── imports: database (db global instance)
├── imports: states.fsm (CreationStates)
├── imports: keyboards.inline (keyboard functions)
├── imports: utils.texts (message templates)
└── imports: utils.navigation (navigation helpers)

handlers/creation.py
├── imports: services.replicate_api (generate_image)
├── imports: database (db global instance)
├── imports: states.fsm (CreationStates)
└── dependencies: keyboards, texts, navigation

handlers/payment.py
├── imports: services.payment_api (create_payment, find_payment)
├── imports: database (db global instance)
└── dependencies: keyboards, texts, navigation

services/replicate_api.py
├── imports: replicate (Python SDK)
├── imports: httpx (HTTP client)
└── imports: config (REPLICATE_API_TOKEN)

services/payment_api.py
├── imports: yookassa (Payment SDK)
└── imports: config (YOOKASSA credentials)

database/db.py
├── imports: aiosqlite (async SQLite driver)
├── imports: config (DB_PATH, FREE_GENERATIONS)
└── imports: database.models (SQL queries)
```

---

## 🔧 Component Architecture

### 1. Handlers Architecture

#### user_start.py - User Initialization & Navigation

**Responsibility:** Handle user lifecycle events and main navigation.

```python
# Router Priority: 1 (first in pipeline)

# Commands
@router.command('start')
├── Purpose: User initialization
├── Actions:
│   ├── Check if user exists in DB
│   ├── Create user with 3 free generations if new
│   ├── Clear previous FSM state
│   ├── Show main menu
│   └── Save menu_message_id to state
└── Result: User sees main menu with profile status

# Callbacks
@router.callback_query(F.data == 'main_menu')
├── Priority: Highest (multiple handlers)
├── Actions:
│   ├── Clear FSM state (keep menu_message_id)
│   ├── Edit existing menu message
│   └── Show main menu buttons
└── Result: Return to main menu

@router.callback_query(F.data == 'show_profile')
├── Actions:
│   ├── Fetch user from DB
│   ├── Format profile with balance
│   ├── Show profile menu
│   └── Edit menu message
└── Result: User sees balance and profile options

@router.callback_query(F.data == 'create_design')
├── Actions:
│   ├── Clear previous design data
│   ├── Set FSM state to waiting_for_photo
│   ├── Show photo upload instructions
│   └── Edit menu message
└── Result: Ready for photo input

@router.callback_query(F.data == 'buy_generations')
├── Actions:
│   ├── Redirect to payment router
│   └── Show payment packages
└── Result: User sees pricing options
```

**State Management:**
```python
data = {
    'menu_message_id': int,      # Always preserved
    'user_id': int,              # For context
}
state_fsm: None  # No FSM state at this handler level
```

#### creation.py - Design Generation (FSM Flow)

**Responsibility:** Handle the entire design creation flow through FSM states.

```python
# Router Priority: 2 (second in pipeline)
# Manages FSM states: waiting_for_photo → choose_room → choose_style

# STATE 1: waiting_for_photo
@message_handler(content_types=['photo'], state=CreationStates.waiting_for_photo)
├── Trigger: User uploads photo
├── Validations:
│   ├── Check for media group (album) → reject if found
│   ├── Check balance (skip if admin)
│   └── Check photo quality/size
├── Actions:
│   ├── Save photo_id to state.data
│   ├── Show room type options
│   ├── Set state to choose_room
│   └── Edit menu message
└── Result: User sees 4 room types to choose from

# STATE 2: choose_room
@callback_query(F.data.startswith('room_'), state=CreationStates.choose_room)
├── Trigger: User selects room type (living_room, bedroom, kitchen, office)
├── Validations:
│   ├── Verify balance again (can change between states)
│   └── Validate room_type value
├── Actions:
│   ├── Extract room_type from callback_data
│   ├── Save room to state.data
│   ├── Show design style options
│   ├── Set state to choose_style
│   └── Edit menu message
└── Result: User sees 10 design styles

# STATE 3: choose_style (GENERATION TRIGGER)
@callback_query(F.data.startswith('style_'), state=CreationStates.choose_style)
├── Trigger: User selects style (modern, minimalist, scandinavian, etc.)
├── Validations:
│   ├── Final balance check (critical)
│   ├── Validate style value
│   └── Check if admin (skip deduction)
├── Actions:
│   ├── Extract style from callback_data
│   ├── Get photo_id and room from state.data
│   ├── Show "Processing..." message
│   ├── Deduct balance from DB (if not admin)
│   ├── Call generate_image(photo_id, room, style, bot_token)
│   ├── Send generated image to user
│   ├── Show post-generation menu
│   ├── Clear FSM state
│   └── Clear state.data (except menu_message_id)
└── Result: User sees generated design image

# Alternative: change_style_after_gen
@callback_query(F.data == 'change_style', state=None)
├── Condition: User wants to try different style for same photo
├── Actions:
│   ├── photo_id and room still in state.data
│   ├── Set state back to choose_style
│   ├── Show style options again
│   └── Edit menu message
└── Result: User selects new style for same photo/room

# Error Handlers
@message_handler(F.text, state=CreationStates.waiting_for_photo)
├── Block: Delete any text messages
└── Effect: Force button usage only

@message_handler(F.video | F.document, state=CreationStates.waiting_for_photo)
├── Block: Delete non-photo files
└── Effect: Prevent spam and confusion
```

**State Transitions Diagram:**
```
┌──────────┐
│ NO STATE │
│ (start)  │
└────┬─────┘
     │ callback: create_design
     ▼
┌─────────────────────┐
│ waiting_for_photo   │
│ (awaiting photo)    │
└────┬────────────────┘
     │ message: photo received
     │ + balance > 0 (or admin)
     ▼
┌─────────────────────┐
│ choose_room         │
│ (select room type)  │
└────┬────────────────┘
     │ callback: room_*
     │ + balance > 0 (or admin)
     ▼
┌─────────────────────┐
│ choose_style        │
│ (select style)      │
└────┬────────────────┘
     │ callback: style_*
     │ (GENERATION HAPPENS HERE)
     │ + balance > 0 (or admin)
     ▼
┌──────────┐
│ NO STATE │
│ (result) │
└──────────┘

┌─────────────┐
│ choose_room │ ◄─ callback: back_to_room
└─────────────┘
```

**State Data Lifecycle:**
```python
# Created during photo upload
state.data = {
    'menu_message_id': int,    # Preserved from user_start
    'photo_id': 'AgAC...',     # Telegram file_id
    'media_group_id': 'xxx',   # Album protection (temporary)
}

# Extended during room selection
state.data = {
    'menu_message_id': int,
    'photo_id': 'AgAC...',
    'room': 'living_room',     # Saved room type
}

# Used during generation
state.data = {
    'menu_message_id': int,
    'photo_id': 'AgAC...',
    'room': 'living_room',
    'style': 'scandinavian',   # (temporary, not saved)
}

# Cleared after generation (except menu_message_id)
state.data = {
    'menu_message_id': int,    # Preserved
}
```

#### payment.py - Payment Processing

**Responsibility:** Handle payment creation and verification.

```python
# Router Priority: 3 (last in pipeline)

@callback_query(F.data == 'buy_generations')
├── Actions:
│   ├── Show 3 payment packages
│   ├── Edit menu message
│   └── Display keyboard with prices
└── Result: User sees pricing options

@callback_query(F.data.startswith('pay_'))
├── Trigger: User selects package (pay_10_290, pay_25_490, pay_60_990)
├── Actions:
│   ├── Parse callback_data → tokens, price
│   ├── Call create_payment_yookassa(amount, user_id, tokens)
│   ├── Get payment_id and confirmation_url from YooKassa
│   ├── Save to DB: create_payment(user_id, payment_id, amount, tokens)
│   ├── Show payment message with button
│   └── Edit menu message
└── Result: User sees "Pay Now" button and "Check Payment" button

@callback_query(F.data == 'check_payment')
├── Trigger: User clicks "I paid!" button
├── Actions:
│   ├── Get last pending payment: db.get_last_pending_payment(user_id)
│   ├── Call find_payment(payment_id) → check YooKassa status
│   ├── If status == 'succeeded':
│   │   ├── Update DB: set_payment_success(payment_id)
│   │   ├── Add tokens to balance: db.add_tokens(user_id, tokens)
│   │   ├── Show success message with new balance
│   │   └── Return to main menu
│   └── If status == 'pending':
│       ├── Show "Payment not received yet" message
│       └── Return to payment menu
└── Result: Balance updated or retry message shown
```

**Payment Flow State Machine:**
```
┌─────────────┐
│ Show Packages│
│ (3 options) │
└──────┬──────┘
       │ User selects package
       ▼
┌────────────────────┐
│ Create Payment     │
│ (YooKassa)         │
└──────┬─────────────┘
       │ Payment ID generated
       ▼
┌────────────────────┐
│ Payment Pending    │
│ (DB saved, awaiting user payment)
└──────┬─────────────┘
       │ User pays online
       │ or clicks "Check"
       ▼
┌────────────────────┐
│ Status Check       │
│ (YooKassa API)     │
└──────┬─────────────┘
       │
       ├─ succeeded ──┐
       │              ▼
       │        ┌──────────────┐
       │        │ Add Tokens   │
       │        │ Update DB    │
       │        └──────┬───────┘
       │               │
       │               ▼
       │        ┌──────────────┐
       │        │ Main Menu    │
       │        │ (success)    │
       │        └──────────────┘
       │
       └─ pending ─┐
                   ▼
        ┌──────────────────┐
        │ Show "Try Again" │
        │ (retry button)   │
        └──────────────────┘
```

### 2. Services Architecture

#### replicate_api.py - AI Image Generation

**Responsibility:** Integrate with Replicate AI for image generation.

**Function: generate_image()**
```python
async def generate_image(
    photo_id: str,           # Telegram file_id of uploaded photo
    room: str,              # Type: living_room, bedroom, kitchen, office
    style: str,             # Type: modern, minimalist, scandinavian, etc.
    bot_token: str          # Telegram Bot API token
) -> Optional[str]:         # Returns image URL or None on error
```

**Process Flow:**
```
1. GET IMAGE FROM TELEGRAM
   └─ Use Telegram Bot API
      └─ URL: https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}
      └─ Download to bytes

2. ENCODE TO BASE64
   └─ base64.b64encode(image_bytes)
   └─ Result: data:image/jpeg;base64,{base64_string}

3. BUILD PROMPT
   └─ Template: "Interior design of a [room] in [style] style, high quality, photorealistic"
   └─ Example: "Interior design of a living_room in scandinavian style, high quality, photorealistic"

4. CALL REPLICATE API
   └─ Model: adirik/interior-design
   └─ Input parameters:
      ├─ image: base64 encoded image data
      ├─ prompt: AI prompt
      ├─ room_type: room type identifier
      ├─ num_inference_steps: 50 (quality vs speed)
      └─ guidance_scale: 7.5 (prompt adherence)

5. WAIT FOR RESULT
   └─ Replicate returns output array
   └─ Extract image URL from output

6. RETURN URL
   └─ User can display or download image
```

**Error Handling:**
```python
try:
    # Get image from Telegram
except httpx.TimeoutException:
    logger.error(f"Timeout downloading from Telegram")
    return None
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error from Telegram: {e.status_code}")
    return None

try:
    # Call Replicate API
except replicate.error.ReplicateError as e:
    logger.error(f"Replicate API error: {e}")
    return None
except asyncio.TimeoutError:
    logger.error(f"Replicate generation timeout (60s)")
    return None

# All exceptions caught → return None
# Caller handles None gracefully
```

**Room Type Mapping:**
```python
ROOM_TYPES = {
    'living_room': 'living room',
    'bedroom': 'bedroom',
    'kitchen': 'kitchen',
    'office': 'office',
}
```

**Style Mapping:**
```python
STYLE_TYPES = [
    ('modern', 'Modern'),
    ('minimalist', 'Minimalist'),
    ('scandinavian', 'Scandinavian'),
    ('industrial', 'Industrial/Loft'),
    ('rustic', 'Rustic'),
    ('japandi', 'Japandi'),
    ('boho', 'Boho/Eclectic'),
    ('mediterranean', 'Mediterranean'),
    ('midcentury', 'Mid-century/Vintage'),
    ('artdeco', 'Art Deco'),
]
```

#### payment_api.py - YooKassa Integration

**Responsibility:** Create and verify payments through YooKassa.

**Function 1: create_payment_yookassa()**
```python
async def create_payment_yookassa(
    amount: int,            # Price in rubles (290, 490, 990)
    user_id: int,          # Telegram user ID
    tokens: int            # Tokens to grant (10, 25, 60)
) -> Optional[Dict]:       # Returns payment data or None

# Returns:
{
    'id': 'payment_id_from_yookassa',
    'amount': 490,
    'tokens': 25,
    'confirmation_url': 'https://yookassa.ru/auth/...'
}
```

**Process:**
```python
1. Initialize YooKassa client with credentials
   └─ Shop ID: from .env
   └─ Secret Key: from .env

2. Create payment object
   └─ Amount: {value: "490", currency: "RUB"}
   └─ Confirmation type: redirect
   └─ Capture: true (immediate)
   └─ Description: "25 generations for user 123456789"

3. Submit to YooKassa
   └─ Payment.create() method
   └─ Returns payment object

4. Extract data
   └─ payment.id (unique YooKassa payment ID)
   └─ payment.confirmation.confirmation_url (redirect link)

5. Return dict with payment info
```

**Function 2: find_payment()**
```python
async def find_payment(
    payment_id: str         # YooKassa payment ID
) -> bool:                  # True if succeeded, False otherwise

# Returns: True if status == 'succeeded', False if pending or failed
```

**Process:**
```python
1. Query YooKassa for payment status
   └─ Payment.find_one(payment_id)

2. Check status
   └─ 'succeeded': Payment completed
   └─ 'pending': Awaiting user payment
   └─ 'failed': Payment failed
   └─ 'canceled': User canceled

3. Return boolean
   └─ True only if succeeded
```

**Pricing Structure (config.py):**
```python
PAYMENT_PACKAGES = {
    'small': {
        'tokens': 10,
        'price': 290,  # rubles
        'name': '10 generations',
    },
    'medium': {
        'tokens': 25,
        'price': 490,
        'name': '25 generations',
    },
    'large': {
        'tokens': 60,
        'price': 990,
        'name': '60 generations',
    },
}
```

### 3. Database Architecture

#### db.py - Async Database Layer

**Initialization:**
```python
class Database:
    @staticmethod
    async def init_db():
        """Create tables if not exist"""
        async with aiosqlite.connect(config.DB_PATH) as db:
            await db.execute(models.CREATE_USERS_TABLE)
            await db.execute(models.CREATE_PAYMENTS_TABLE)
            await db.commit()
```

**Core Methods:**

```python
# User Management
async def create_user(user_id: int, username: str) -> bool:
    """Create new user with 3 free generations"""
    # Inserts: (user_id, username, balance=3, reg_date=NOW)

async def get_user(user_id: int) -> Optional[Dict]:
    """Fetch user record"""
    # Returns: {user_id, username, balance, reg_date} or None

async def get_balance(user_id: int) -> int:
    """Get user's generation balance"""
    # Returns: balance value or 0 if not found

# Balance Operations
async def decrease_balance(user_id: int) -> bool:
    """Deduct 1 from balance (for generation)"""
    # WHERE user_id, SET balance = balance - 1

async def increase_balance(user_id: int, amount: int) -> bool:
    """Add to balance (for payment)"""
    # WHERE user_id, SET balance = balance + amount

# Payment Management
async def create_payment(
    user_id: int,
    payment_id: str,
    amount: int,
    tokens: int
) -> bool:
    """Record new payment attempt"""
    # Inserts: (user_id, payment_id, amount, tokens, status='pending', created_at=NOW)

async def get_last_pending_payment(user_id: int) -> Optional[Dict]:
    """Get most recent unconfirmed payment"""
    # Returns: {id, user_id, yookassa_payment_id, amount, tokens, status} or None
    # WHERE user_id AND status='pending' ORDER BY created_at DESC LIMIT 1

async def set_payment_success(payment_id: str) -> bool:
    """Mark payment as succeeded"""
    # WHERE yookassa_payment_id, SET status='succeeded'

async def add_tokens(user_id: int, tokens: int) -> bool:
    """Alias for increase_balance"""
    # Same as increase_balance
```

**Query Implementation (models.py):**

```python
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 3,
    reg_date DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    yookassa_payment_id TEXT UNIQUE NOT NULL,
    amount INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
"""

# Example query
SELECT_USER = "SELECT user_id, username, balance, reg_date FROM users WHERE user_id = ?"
INSERT_USER = "INSERT INTO users (user_id, username) VALUES (?, ?)"
UPDATE_BALANCE = "UPDATE users SET balance = balance - 1 WHERE user_id = ?"
```

---

## 📊 Database Schema

### Tables Detailed

#### users table

| Column | Type | Constraints | Purpose |
|--------|------|-------------|----------|
| user_id | INTEGER | PRIMARY KEY | Telegram user ID (unique identifier) |
| username | TEXT | | Telegram username |
| balance | INTEGER | DEFAULT 3 | Available generation tokens |
| reg_date | DATETIME | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |

**Indexes:**
- PRIMARY KEY on user_id (automatic)

**Sample Data:**
```sql
user_id | username   | balance | reg_date
--------|------------|---------|------------------
123456  | john_smith | 5       | 2025-01-15 10:30:00
789012  | jane_doe   | 0       | 2025-01-14 15:45:00
345678  | admin_user | 9999    | 2025-01-01 00:00:00
```

#### payments table

| Column | Type | Constraints | Purpose |
|--------|------|-------------|----------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal payment ID |
| user_id | INTEGER | FOREIGN KEY | Link to users table |
| yookassa_payment_id | TEXT | UNIQUE NOT NULL | Payment ID from YooKassa |
| amount | INTEGER | NOT NULL | Price in rubles |
| tokens | INTEGER | NOT NULL | Tokens to grant on success |
| status | TEXT | DEFAULT 'pending' | pending, succeeded, or failed |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Payment creation time |

**Indexes:**
- PRIMARY KEY on id (automatic)
- UNIQUE on yookassa_payment_id
- FOREIGN KEY on user_id

**Sample Data:**
```sql
id | user_id | yookassa_payment_id | amount | tokens | status    | created_at
---|---------|---------------------|--------|--------|-----------|------------------
1  | 123456  | pypl_2025_0001     | 290    | 10     | succeeded | 2025-01-15 10:31:00
2  | 123456  | pypl_2025_0002     | 490    | 25     | pending   | 2025-01-15 10:35:00
3  | 789012  | pypl_2025_0003     | 990    | 60     | succeeded | 2025-01-14 15:46:00
```

**Relationships:**
```
users
  │
  │ (1:N) user_id
  │
  └──────► payments
           (many payments per user)
```

---

## 🔄 Data Flow Diagrams

### Flow 1: First Time User Experience

```
User sends /start
    │
    ▼
bot/main.py
Dispatcher routes to user_start.router
    │
    ▼
cmd_start() handler
    │
    ├─ Check: user exists in DB?
    │  ├─ NO: create_user(user_id, username)
    │  │      └─ balance = 3, reg_date = NOW
    │  └─ YES: continue
    │
    ├─ Clear FSM state
    │
    ├─ Generate main menu keyboard
    │
    ├─ Send message: "Welcome! Choose action:"
    │      with buttons: [Create Design] [Profile]
    │
    ├─ Save menu_message_id to state.data
    │
    └─ User sees: Main menu
       Balance: 3 free generations available ✅
```

### Flow 2: Create Design (Success Path)

```
User clicks [Create Design]
    │
    ▼
user_start.py:start_creation()
    │
    ├─ Clear design data from state
    ├─ Set FSM state = waiting_for_photo
    └─ Show: "Upload a room photo"
    
        │
        ▼
    User sends PHOTO
        │
        ▼
    creation.py:photo_uploaded()
        │
        ├─ Validate: Not an album?
        ├─ Validate: balance > 0 (skip if admin)
        ├─ Save photo_id to state.data
        ├─ Set FSM state = choose_room
        └─ Show room options: [🛋 Living] [🛏 Bedroom] [🍽 Kitchen] [🖥 Office]
        
            │
            ▼
        User selects ROOM (e.g., Living Room)
            │
            ▼
        creation.py:room_chosen()
            │
            ├─ Validate: balance > 0 (skip if admin)
            ├─ Save room = 'living_room' to state.data
            ├─ Set FSM state = choose_style
            └─ Show 10 design styles (2 per row)
            
                │
                ▼
            User selects STYLE (e.g., Scandinavian)
                │
                ▼
            creation.py:style_chosen()
                │
                ├─ CRITICAL: Final balance check
                ├─ Get: photo_id, room from state
                ├─ Get: style from callback_data
                │
                ├─ [NOT ADMIN] Deduct balance:
                │   db.decrease_balance(user_id)
                │   └─ balance: 3 → 2 ✅
                │
                ├─ Show: ⏳ "Generating design..."
                │
                ├─ Call AI:
                │   services.replicate_api.generate_image(
                │       photo_id='AgAC...',
                │       room='living_room',
                │       style='scandinavian',
                │       bot_token=BOT_TOKEN
                │   )
                │
                ├─ Get image URL from Replicate
                │
                ├─ Send generated image to user
                │
                ├─ Show post-gen menu:
                │   [🔄 Other Style] [📸 New Photo] [👤 Profile] [🏠 Home]
                │
                ├─ Clear FSM state (FSM = None)
                ├─ Clear state.data (except menu_message_id)
                │
                └─ User sees: ✅ Generated design image
                   Remaining balance: 2 generations
```

### Flow 3: Payment (Success Path)

```
User clicks [Buy Generations]
    │
    ▼
payment.py:show_packages()
    │
    ├─ Show 3 packages:
    │   [10 gen - 290₽] [25 gen - 490₽] [60 gen - 990₽]
    │
    └─ User selects one (e.g., 25 gen - 490₽)
        │
        ▼
    payment.py:create_payment()
        │
        ├─ Parse: tokens=25, price=490
        │
        ├─ Call YooKassa:
        │   services.payment_api.create_payment_yookassa(
        │       amount=490,
        │       user_id=123456,
        │       tokens=25
        │   )
        │
        ├─ Receive from YooKassa:
        │   payment_id = 'pypl_abc123def456'
        │   confirmation_url = 'https://yookassa.ru/auth/...'
        │
        ├─ Save to DB:
        │   db.create_payment(
        │       user_id=123456,
        │       payment_id='pypl_abc123def456',
        │       amount=490,
        │       tokens=25
        │   )
        │   └─ Status: 'pending' ✅
        │
        ├─ Show payment message:
        │   [💰 Pay Now (link)] [🔄 I paid! (check)]
        │
        └─ User sees: Payment options
            │
            ├─ Option A: Click [💰 Pay Now]
            │   └─ Redirected to YooKassa payment page
            │      └─ User pays online
            │         └─ (YooKassa stores payment info)
            │
            └─ Option B: After paying, click [🔄 I paid!]
                │
                ▼
            payment.py:check_payment()
                │
                ├─ Get: last pending payment for user
                │   db.get_last_pending_payment(user_id)
                │   └─ Returns: {id, payment_id='pypl_abc123def456', status='pending', ...}
                │
                ├─ Query YooKassa:
                │   services.payment_api.find_payment('pypl_abc123def456')
                │
                ├─ YooKassa returns: status = 'succeeded' ✅
                │
                ├─ Update DB:
                │   db.set_payment_success('pypl_abc123def456')
                │   └─ Status: 'pending' → 'succeeded'
                │
                ├─ Add tokens:
                │   db.add_tokens(user_id=123456, tokens=25)
                │   └─ Balance: 2 → 27 ✅
                │
                ├─ Show success message:
                │   "✅ Payment successful!
                │    Your balance: 27 generations"
                │
                ├─ Return to main menu
                │
                └─ User sees: ✅ Payment confirmed + new balance
```

---

## 🎮 FSM State Machine

### State Definitions (states/fsm.py)

```python
class CreationStates(StatesGroup):
    """FSM states for design creation process"""
    
    # State 1: Awaiting photo upload
    waiting_for_photo = State()
    
    # State 2: Awaiting room type selection
    choose_room = State()
    
    # State 3: Awaiting style selection (triggers generation)
    choose_style = State()
```

### State Transitions & Triggers

```
┌─────────────────────────────────────────────────────────────────┐
│ STATE MACHINE: Design Creation Flow                            │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ NO STATE (initial state after /start or clear)                 │
└──────────────────────┬───────────────────────────────────────────┘
                       │
        EVENT: callback_query('create_design')
        CONDITIONS: None required
        │
        ▼
┌──────────────────────────────────────────────────────────────────┐
│ waiting_for_photo                                               │
│ (User can: upload photo, go back to menu)                      │
│                                                                 │
│ Context:                                                        │
│   - menu_message_id: int (preserved from /start)               │
│   - Nothing else yet                                            │
└───────┬──────────────────────────────────────────┬──────────────┘
        │                                          │
EVENT: message(photo)          EVENT: callback('main_menu')
CONDITION: balance > 0 (or admin)      → Clear state
        │                                → Go to main menu
        │                                │
        ▼                                ▼
┌────────────────────────┐         NO STATE
│ choose_room            │
│ (show 4 room options) │
│                       │
│ Context:              │
│   - photo_id: str    │
│   - menu_message_id  │
└───────┬──────────────┘
        │
EVENT: callback('room_*')
CONDITION: balance > 0 (or admin)
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│ choose_style                                                   │
│ (show 10 style options)                                        │
│                                                                │
│ Context:                                                       │
│   - photo_id: str                                             │
│   - room: str                                                 │
│   - menu_message_id                                           │
│                                                                │
│ Special: ← callback('back_to_room')                          │
│   Can go back to choose_room state                            │
│   └─ photo_id preserved                                      │
└────┬──────────────────────────────────────────┬──────────────┘
     │                                          │
EVENT: callback('style_*')          EVENT: callback('main_menu')
CONDITION: balance > 0 (or admin)          → Clear state
[GENERATION HAPPENS HERE]                  → Go to main menu
Deduct balance by 1                        │
Get image from Replicate                   ▼
Send to user                          NO STATE
Clear state                           
     │
     ▼
NO STATE
(ready for next action)
```

### State Data Management

```python
# state.data is a dictionary containing:
# - FSM-specific context (not persisted to DB)
# - Preserved across state transitions (except during clear())
# - Cleared with state.clear() or state.set_state(None)

# CRITICAL: menu_message_id
# ├─ Created in cmd_start() when message is sent
# ├─ Saved to state.data
# ├─ MUST be preserved during navigation (use set_state(None) not clear())
# └─ Allows edit_menu() to modify the same message

# Lifecycle:
wait_for_photo_state_data = {
    'menu_message_id': 12345,      # ← Preserved
    'user_id': 123456,
}

room_state_data = {
    'menu_message_id': 12345,      # ← Preserved
    'photo_id': 'AgAC...',         # ← Added
}

style_state_data = {
    'menu_message_id': 12345,      # ← Preserved
    'photo_id': 'AgAC...',         # ← From previous state
    'room': 'living_room',         # ← Added
}

after_generation = {
    'menu_message_id': 12345,      # ← Still preserved for next cycle
}
```

---

## 🔐 API Integration

### Replicate AI API

**Endpoint:** `replicate.run()`  
**Model:** `adirik/interior-design`  
**Method:** POST (via replicate library)

**Input Parameters:**
```python
{
    'image': 'data:image/jpeg;base64,{BASE64_DATA}',
    'prompt': 'Interior design of a living room in scandinavian style, ...',
    'room_type': 'living_room',
    'num_inference_steps': 50,    # Higher = better quality, slower
    'guidance_scale': 7.5          # How closely to follow prompt
}
```

**Output:**
```python
[
    'https://replicate.delivery/..../output.png'  # Image URL
]
```

**Error Handling:**
- `replicate.error.ReplicateError` - API errors
- `httpx.TimeoutException` - Download timeout
- `asyncio.TimeoutError` - Generation timeout (60 sec)

### YooKassa Payment API

**Endpoint:** `Payment.create()` / `Payment.find_one()`  
**Auth:** HTTP Basic Auth with Shop ID + Secret Key

**Create Payment:**
```python
Payment.create({
    'amount': {'value': '490', 'currency': 'RUB'},
    'confirmation': {
        'type': 'redirect',
        'return_url': 'https://t.me/interior_design_bot'
    },
    'capture': True,
    'description': 'Tokens for user 123456'
})

# Returns:
Payment(
    id='27a514ad-0041-504a-9f06-a0e3bfb17fa4',
    amount=Amount(value=Decimal('490'), currency='RUB'),
    status='pending',
    confirmation=Confirmation(
        type='redirect',
        confirmation_url='https://yookassa.ru/auth/...'
    )
)
```

**Find Payment:**
```python
Payment.find_one('27a514ad-0041-504a-9f06-a0e3bfb17fa4')

# Returns:
Payment(
    id='27a514ad-0041-504a-9f06-a0e3bfb17fa4',
    status='succeeded'  # or 'pending', 'failed', 'canceled'
)
```

### Telegram Bot API

**Used for:**
- Sending messages: `message.answer()`
- Editing messages: `bot.edit_message_text()`
- Deleting messages: `bot.delete_message()`
- Getting file: `bot.get_file()` then `bot.download_file()`

---

## ⚠️ Error Handling

### Error Hierarchy

```
Exception
├── aiogram.exceptions.*
│   ├── TelegramAPIError  - Telegram API errors
│   ├── TelegramNotFound  - 404 errors (message deleted, etc.)
│   └── TelegramBadRequest - 400 errors (invalid params)
│
├── replicate.error.ReplicateError
│   ├── Network timeout
│   ├── API rate limit
│   └── Model error
│
├── httpx exceptions
│   ├── TimeoutException  - Download timeout
│   ├── HTTPStatusError  - HTTP errors
│   └── ConnectError  - Connection errors
│
├── yookassa exceptions
│   ├── RequestError  - API errors
│   └── Conflict  - Duplicate payment ID
│
├── aiosqlite.OperationalError
│   ├── Database locked
│   ├── Disk full
│   └── Corrupted database
│
└── General
    ├── asyncio.TimeoutError
    ├── ValueError  - Invalid input
    └── Exception  - Unknown error
```

### Graceful Degradation

```python
# Photo upload fails
if generation_failed:
    └─ Show: "Generation failed. Please try again later."
    └─ Keep: balance unchanged
    └─ Allow: retry

# Payment check fails (network issue)
if payment_check_failed:
    └─ Show: "Cannot verify payment. Try again later."
    └─ Keep: payment in pending state
    └─ Allow: retry

# Database error
if db_error:
    └─ Log: detailed error
    └─ Show: "Technical error. Try again."
    └─ Notify: admin

# Image download fails
if download_failed:
    └─ Show: "Failed to process photo. Upload another."
    └─ Remain: in waiting_for_photo state
```

---

## 🔒 Security

### Admin Protection

```python
if user_id in config.ADMIN_IDS:
    # Admins can generate without balance deduction
    # Admins bypass all balance checks
    # Admins see extra admin menu (future)
```

### Input Validation

```python
# Callback data validation
if callback_data not in ALLOWED_VALUES:
    return  # Silently ignore invalid input

# Room type validation
if room not in ['living_room', 'bedroom', 'kitchen', 'office']:
    return  # Reject invalid room

# Style validation
if style not in [s[0] for s in STYLE_TYPES]:
    return  # Reject invalid style

# Amount validation (prevent tampering)
if amount not in [290, 490, 990]:
    return  # Reject invalid amount
```

### Secrets Management

```python
# .env file NEVER committed
.gitignore:
    .env
    *.db  # Database never committed

# Tokens accessed via config.py
BOT_TOKEN = os.getenv('BOT_TOKEN')         # From .env
REPLICATE_API_TOKEN = os.getenv('...')     # From .env
YOOKASSA_SHOP_ID = os.getenv('...')        # From .env
YOOKASSA_SECRET_KEY = os.getenv('...')     # From .env

# NEVER hardcoded
```

### Rate Limiting (Future)

```python
# Could implement:
# - Max generations per hour
# - Max payments per day
# - Cooldown between generations
# - IP-based limits
```

---

## ⚡ Performance

### Optimization Strategies

1. **Async Everything**
   - No blocking I/O operations
   - All database calls are async
   - All HTTP requests are async

2. **Single Message Editing**
   - Reduces Telegram API calls
   - Cleaner UI (no message spam)
   - Faster navigation

3. **Balance Checks**
   - Checked multiple times to catch edge cases
   - Not expensive (single DB query)

4. **Payload Optimization**
   - Generated images downloaded, not stored in DB
   - Only metadata stored (payment records)
   - Minimal state data

### Benchmarks (Expected)

```
Operation                      Time       Notes
─────────────────────────────────────────────────
/start initialization           ~200ms     DB query + message send
Photo processing               ~500ms     Validation + state update
AI generation                  ~30-60s    Replicate processing
Payment creation               ~300ms     YooKassa API call
Payment verification           ~200ms     Status check
Database operations            ~10-50ms   SQLite in-process
Telegram API calls             ~100-200ms Network latency
```

### Scaling Considerations

```
For 10,000 users:
├─ Database: SQLite adequate (~1MB database)
├─ Memory: Minimal (no user session caching)
├─ Disk: Minimal (only DB file)
└─ API limits:
    ├─ Telegram: 30 messages/sec (plenty)
    ├─ Replicate: Rate limited per API key
    └─ YooKassa: Rate limited per merchant

For 100,000+ users:
├─ Database: Migrate to PostgreSQL
├─ Memory: Add session caching
├─ Disk: Cache generated images
└─ API: Implement request queuing
```

---

## 📝 Summary

**Architecture Type:** Event-driven, asynchronous  
**Design Pattern:** Single Menu Pattern + FSM  
**Technology Stack:** aiogram 3.x + aiosqlite + external APIs  
**Data Flow:** Telegram → Handlers → Services → External APIs → DB  
**State Management:** Hybrid (FSM for flow, DB for persistence)  
**Error Handling:** Graceful with user-friendly messages  
**Security:** Admin checks, input validation, secrets in .env  
**Performance:** Async-first, optimized for Telegram limitations  

---

**Document Version:** 2.0 Professional  
**Last Updated:** December 12, 2025  
**Status:** ✅ Complete & Production-Ready
