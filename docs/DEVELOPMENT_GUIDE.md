# 🛠️ DEVELOPMENT_GUIDE - Полный гайд для разработчиков

**Назначение:** Пошаговый гайд для подъёма проекта локально, настройки окружения, отладки и типичного рабочего процесса.  
**Уровень:** От новичка до опытного разработчика  
**Время на прочтение:** ~30 минут  
**Последнее обновление:** December 12, 2025  

---

## 📋 Содержание

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Project Structure](#project-structure)
4. [Running the Bot](#running-the-bot)
5. [Development Workflow](#development-workflow)
6. [Debugging](#debugging)
7. [Testing](#testing)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## 📦 Prerequisites

### System Requirements

```bash
# Minimum specs
- OS: Ubuntu 20.04+, macOS 11+, Windows 10+ (WSL2)
- Python: 3.10+
- RAM: 2GB minimum (4GB recommended)
- Disk: 500MB free space
- Network: Stable internet connection
```

### Required Software

```bash
# Check Python version
python3 --version  # Should be 3.10 or higher

# Install pip (if not included)
python3 -m ensurepip --default-pip

# Install pip tools
pip install --upgrade pip setuptools wheel
```

### Required Credentials

Before starting, obtain these from external services:

```
1. Telegram Bot Token
   └─ From: @BotFather on Telegram
   └─ How: /newbot command
   └─ Format: Looks like "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

2. Replicate API Token
   └─ From: https://replicate.com/account
   └─ How: Create account, generate API token
   └─ Format: Looks like "r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

3. YooKassa Credentials
   └─ From: https://yookassa.ru/
   └─ How: Create merchant account
   └─ Credentials: Shop ID + Secret Key
```

### Optional but Recommended

```bash
# Git (for version control)
sudo apt-get install git  # Ubuntu/Debian
brew install git          # macOS

# VS Code (editor)
# Download from https://code.visualstudio.com/

# Docker (for isolated database)
sudo apt-get install docker.io docker-compose  # Ubuntu/Debian
brew install --cask docker                      # macOS
```

---

## 🚀 Local Setup

### Step 1: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/severand/InteriorBot.git
cd InteriorBot

# Or if you have SSH set up
git clone git@github.com:severand/InteriorBot.git
cd InteriorBot
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# Verify activation (should show "(venv)" in terminal)
which python  # or "where python" on Windows
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "aiogram|aiosqlite|replicate|yookassa"
```

### Step 4: Setup Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or vim, or use VS Code
```

**Contents of .env:**

```env
# Telegram
BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
BOT_LINK=your_bot_username  # Without @

# AI Generation
REPLICATE_API_TOKEN=YOUR_REPLICATE_API_TOKEN

# Payments
YOOKASSA_SHOP_ID=YOUR_SHOP_ID
YOOKASSA_SECRET_KEY=YOUR_SECRET_KEY

# Admin IDs (comma-separated)
ADMIN_IDS=123456789,987654321

# Optional
DEBUG=true          # Enable debug logging
LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR
```

⚠️ **Security:** Never commit .env file! It's in .gitignore for a reason.

### Step 5: Initialize Database

```bash
# Create tables
python -c "from bot.database.db import Database; import asyncio; asyncio.run(Database.init_db())"

# Or run initialization script
python scripts/init_db.py  # If exists

# Verify database was created
ls -la bot.db  # Should show bot.db file
```

### Step 6: Test Bot Connection

```bash
# Quick connectivity test
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('BOT_TOKEN')
if token:
    print(f'✅ BOT_TOKEN loaded: {token[:20]}...')
else:
    print('❌ BOT_TOKEN not found in .env')
"
```

---

## 📁 Project Structure

### Key Directories During Development

```
InteriorBot/
├── bot/
│   ├── main.py              ← Entry point (modify rarely)
│   ├── config.py            ← Configuration (modify for constants)
│   ├── database/
│   │   ├── db.py            ← Database layer (understand, don't modify often)
│   │   └── models.py        ← SQL queries (reference, modify carefully)
│   ├── handlers/            ← WHERE YOU'LL SPEND 70% OF TIME
│   │   ├── user_start.py    ← User initialization
│   │   ├── creation.py      ← Design generation flow
│   │   └── payment.py       ← Payment processing
│   ├── services/
│   │   ├── replicate_api.py ← AI integration (don't modify)
│   │   └── payment_api.py   ← Payment API (reference only)
│   ├── keyboards/
│   │   └── inline.py        ← UI buttons (modify for UI changes)
│   ├── states/
│   │   └── fsm.py           ← FSM states (modify when adding states)
│   └── utils/
│       ├── texts.py         ← Messages (modify for text changes)
│       ├── navigation.py    ← Navigation helpers
│       └── helpers.py       ← Utility functions
├── bot.db                   ← SQLite database (don't commit)
├── .env                     ← Your secrets (don't commit)
├── requirements.txt         ← Dependencies (commit)
├── .gitignore               ← Ignore patterns (commit)
└── docs/                    ← Documentation (you are here)
    ├── README.md            ← Start here
    ├── ARCHITECTURE.md      ← System design
    ├── DEVELOPMENT_GUIDE.md ← This file
    ├── API_REFERENCE.md     ← All handlers
    ├── FSM_GUIDE.md         ← State machine
    ├── DEPLOYMENT.md        ← Production setup
    ├── TROUBLESHOOTING.md   ← Common issues
    └── DEVELOPMENT_RULES.md ← Code standards
```

### Files You'll Modify Often

```
🔴 High frequency (several times per day)
├── bot/handlers/*.py        ← New features, bug fixes
├── bot/keyboards/inline.py  ← UI adjustments
├── bot/utils/texts.py       ← Message updates
└── bot/states/fsm.py        ← State additions

🟡 Medium frequency (few times per week)
├── bot/config.py            ← Constants, admin IDs
├── bot/utils/helpers.py     ← Utility functions
└── requirements.txt         ← New dependencies

🟢 Low frequency (rarely)
├── bot/main.py              ← Router registration
├── bot/database/db.py       ← Database queries
└── bot/services/*.py        ← External integrations
```

---

## ▶️ Running the Bot

### Start Bot Locally

```bash
# Make sure venv is activated
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run the bot
python bot/main.py

# Expected output:
# 2025-12-12 14:30:45,123 - aiogram.dispatcher - INFO - Starting polling
# ✅ Bot is running...
# (Ctrl+C to stop)
```

### Start with Debug Logging

```bash
# Enable debug mode
export DEBUG=1          # Linux/macOS
set DEBUG=1            # Windows CMD
$env:DEBUG="1"        # Windows PowerShell

# Run with debug
python bot/main.py

# You'll see much more detailed logs
```

### Test Bot on Telegram

```
1. Open Telegram
2. Find your bot (by username from @BotFather)
3. Send: /start
4. Expected: Main menu with [Create Design] and [Profile] buttons
5. If nothing happens: Check logs, see TROUBLESHOOTING
```

### Monitor Bot in Real-time

```bash
# Terminal 1: Run bot
python bot/main.py

# Terminal 2: Monitor logs
tail -f bot.log  # If logging to file

# Or filter for errors
python bot/main.py 2>&1 | grep -i error
```

---

## 💻 Development Workflow

### Typical Day-to-Day Process

```
┌─────────────────────────────────────────────────────────────┐
│ STANDARD DEVELOPMENT WORKFLOW                               │
└─────────────────────────────────────────────────────────────┘

1. START OF DAY
   ├─ Pull latest: git pull origin main
   ├─ Activate venv: source venv/bin/activate
   ├─ Start bot: python bot/main.py
   └─ Have Telegram open with test account

2. MAKE CHANGES
   ├─ Edit file (e.g., bot/handlers/creation.py)
   ├─ Save file (Ctrl+S)
   ├─ Bot auto-reloads if using development server
   │  └─ Or manually restart: Ctrl+C then python bot/main.py
   └─ Test in Telegram immediately

3. DEBUG IF NEEDED
   ├─ Look at logs (terminal output)
   ├─ Add print() statements if needed
   ├─ Check error messages carefully
   └─ Refer to TROUBLESHOOTING.md

4. COMMIT CHANGES
   ├─ Review: git diff
   ├─ Stage: git add .
   ├─ Commit: git commit -m "feat: description"
   └─ Push: git push origin main

5. VERIFY ON MAIN
   ├─ Test bot on production token (if different)
   ├─ Check logs for errors
   └─ Document any issues
```

### Code Editing Best Practices

**Opening the project:**
```bash
# VS Code (recommended)
code .

# Terminal + vim/nano
vim bot/handlers/creation.py

# Or any other editor
pycharm .
subl .
```

**While editing:**
```python
# ✅ DO: Use type hints
async def style_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    ...

# ❌ DON'T: Skip type hints
async def style_chosen(callback, state):
    ...

# ✅ DO: Add docstrings
async def generate_image(photo_id: str, room: str, style: str) -> Optional[str]:
    """Generate interior design image using Replicate AI."""
    ...

# ✅ DO: Use async/await correctly
await db.decrease_balance(user_id)
await callback.answer()

# ❌ DON'T: Mix async/sync
result = db.decrease_balance(user_id)  # Wrong!
```

---

## 🔍 Debugging

### Enable Debug Logging

```python
# In bot/main.py, add at the top:
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

### Add Debug Prints

```python
# In any handler:
@router.callback_query(F.data == 'create_design')
async def start_creation(callback: CallbackQuery, state: FSMContext):
    logger.info(f"🔍 [DEBUG] User {callback.from_user.id} clicked create_design")
    
    data = await state.get_data()
    logger.debug(f"State data before: {data}")
    
    await state.set_state(CreationStates.waiting_for_photo)
    
    logger.debug(f"State set to: waiting_for_photo")
    await callback.answer()
```

### Log Database Operations

```python
# In bot/database/db.py:
logger.debug(f"Executing query: {sql_query}")
result = await db.execute(sql_query)
logger.debug(f"Query result: {result}")
```

### Inspect State Data

```python
# Add this anywhere to see current state:
data = await state.get_data()
logger.warning(f"📊 CURRENT STATE: {json.dumps(data, indent=2, default=str)}")

# See FSM state
fcm_state = await state.get_state()
logger.warning(f"📊 FSM STATE: {fsm_state}")
```

### Common Debug Scenarios

**Scenario 1: Payment not working**
```python
# Add logs in payment.py:check_payment()
logger.info(f"Checking payment for user {user_id}")
payment_data = db.get_last_pending_payment(user_id)
logger.debug(f"Last pending payment: {payment_data}")

if not payment_data:
    logger.warning(f"No pending payment found for user {user_id}")
    return

status = find_payment(payment_data['yookassa_payment_id'])
logger.info(f"Payment status from YooKassa: {status}")
```

**Scenario 2: Generation failing**
```python
# Add logs in creation.py:style_chosen()
logger.info(f"Starting generation for user {user_id}")
logger.debug(f"Photo ID: {photo_id}, Room: {room}, Style: {style}")

try:
    image_url = await generate_image(photo_id, room, style, BOT_TOKEN)
    if not image_url:
        logger.error("generate_image returned None!")
        return
    logger.info(f"✅ Image generated: {image_url}")
except Exception as e:
    logger.exception(f"❌ Generation failed: {e}")
```

**Scenario 3: Menu message ID issues**
```python
# Add logs in any navigation function
data = await state.get_data()
menu_message_id = data.get('menu_message_id')
logger.warning(f"Menu message ID: {menu_message_id}")

if not menu_message_id:
    logger.error("⚠️  No menu_message_id found! This will create a new message.")
else:
    logger.info(f"✅ Using existing menu message {menu_message_id}")
```

---

## 🧪 Testing

### Manual Testing Checklist

```bash
# ✅ Bot responds to /start
/start → Should show main menu

# ✅ Profile shows correct balance
Click Profile → Should show "Balance: X generations"

# ✅ Photo upload works
Click Create Design → Upload photo → Should show room options

# ✅ Room selection works
Select room → Should show style options

# ✅ Generation works
Select style → Should generate image (30-60 sec)

# ✅ Balance decreases after generation
Profile → Should show balance decreased by 1

# ✅ Payment creation works
Click Buy → Select package → Should show YooKassa button

# ✅ Admin bypass works (if you're admin)
With admin ID → Should generate without balance deduction
```

### Test Different User Scenarios

```
1. NEW USER
   └─ /start → Should create with balance=3

2. EXISTING USER
   └─ /start → Should show existing balance

3. ZERO BALANCE USER
   └─ Try to generate → Should be redirected to payment

4. ADMIN USER
   └─ Generate → Should not deduct balance

5. CONCURRENT USERS
   └─ Multiple users testing simultaneously
```

### Automated Testing (Future)

```python
# Example test file: tests/test_handlers.py
import pytest
from aiogram import types
from bot.handlers import user_start

@pytest.mark.asyncio
async def test_cmd_start():
    """Test /start command"""
    # Setup
    update = types.Update(message=types.Message())
    # Execute
    result = await user_start.cmd_start(update.message)
    # Assert
    assert result is not None

# Run tests
pytest tests/
```

---

## 🎯 Common Tasks

### Task 1: Add New Message

**Goal:** Add a new welcome message

```python
# 1. Add to bot/utils/texts.py
WELCOME_MESSAGE = "Welcome to InteriorBot! 🎨"

# 2. Use in handler (bot/handlers/user_start.py)
from utils.texts import WELCOME_MESSAGE

await message.answer(WELCOME_MESSAGE, reply_markup=keyboard)
```

### Task 2: Add New Button

**Goal:** Add "Settings" button to main menu

```python
# 1. Add callback in keyboard (bot/keyboards/inline.py)
def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎨 Create Design", callback_data="create_design"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="show_settings"),  # NEW
        ],
        [
            InlineKeyboardButton(text="👤 Profile", callback_data="show_profile"),
        ]
    ])

# 2. Add handler (bot/handlers/user_start.py)
@router.callback_query(F.data == "show_settings")
async def show_settings(callback: CallbackQuery, state: FSMContext):
    await edit_menu(
        callback=callback,
        state=state,
        text="⚙️ Settings:\n\nChoose an option:",
        keyboard=get_settings_keyboard()
    )

# 3. Create keyboard for settings (bot/keyboards/inline.py)
def get_settings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ])
```

### Task 3: Add New FSM State

**Goal:** Add settings editing state

```python
# 1. Add state (bot/states/fsm.py)
class CreationStates(StatesGroup):
    waiting_for_photo = State()
    choose_room = State()
    choose_style = State()
    editing_settings = State()  # NEW

# 2. Use in handler (bot/handlers/user_start.py)
@router.callback_query(F.data == "edit_setting")
async def start_editing(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.editing_settings)
    await callback.message.edit_text("Enter new value:")

# 3. Handle state (bot/handlers/user_start.py)
@router.message(CreationStates.editing_settings)
async def process_setting(message: Message, state: FSMContext):
    # Process the input
    await state.set_state(None)
    # Show confirmation
```

### Task 4: Modify Balance Logic

**Goal:** Change free generations from 3 to 5 for new users

```python
# bot/config.py
FREE_GENERATIONS = 5  # Changed from 3

# bot/database/models.py
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 5,  # Changed from 3
    reg_date DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

# If already deployed, run migration:
# ALTER TABLE users SET balance = 5 WHERE balance = 3;
```

### Task 5: Change Payment Prices

**Goal:** Change 10-gen package from 290₽ to 199₽

```python
# bot/config.py
PAYMENT_PACKAGES = {
    'small': {
        'tokens': 10,
        'price': 199,  # Changed from 290
        'name': '10 generations',
    },
    # ... rest unchanged
}
```

---

## ⚠️ Troubleshooting

### Problem: Bot doesn't respond to /start

**Symptoms:**
- Send /start, nothing happens
- No error in logs

**Solutions:**
```bash
# 1. Check bot token
echo $BOT_TOKEN  # Should show something like "123456:ABC..."

# 2. Restart bot
Ctrl+C
python bot/main.py

# 3. Check firewall
# Make sure outgoing connections to Telegram are allowed

# 4. Verify token with curl
curl "https://api.telegram.org/bot$BOT_TOKEN/getMe"
# Should return JSON with bot info
```

### Problem: Generation fails with timeout

**Symptoms:**
- User selects style
- Shows "Generating..." but never returns
- After 60 seconds, error

**Solutions:**
```python
# 1. Check Replicate token
echo $REPLICATE_API_TOKEN

# 2. Test Replicate API
curl -X POST https://api.replicate.com/v1/predictions \
  -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "...model..."}'

# 3. Check photo quality
# Replicate needs clear, well-lit room photos

# 4. Increase timeout in replicate_api.py
timeout=120  # Instead of 60
```

### Problem: Payment verification always fails

**Symptoms:**
- User confirms payment
- Status check returns "not paid"
- Balance doesn't update

**Solutions:**
```python
# 1. Verify YooKassa credentials
echo $YOOKASSA_SHOP_ID
echo $YOOKASSA_SECRET_KEY

# 2. Check if payment actually exists
# Log payment_id when creating
logger.info(f"Payment created: {payment_data['id']}")

# 3. Test YooKassa API
from yookassa import Payment
payment = Payment.find_one('payment_id_here')
print(payment.status)

# 4. Verify credentials in YooKassa dashboard
# Go to https://yookassa.ru/merchants and check settings
```

### Problem: Database locked error

**Symptoms:**
- Errors like "database is locked"
- Operations fail randomly

**Solutions:**
```python
# 1. Close other connections
# Make sure only one bot instance is running

# 2. Remove lock file
rm -f bot.db-wal
rm -f bot.db-shm

# 3. Rebuild database
rm bot.db
python -c "from bot.database.db import Database; import asyncio; asyncio.run(Database.init_db())"

# 4. Use connection pool (for future scaling)
# Currently using single connection, may need pooling for multiple workers
```

---

## ✨ Best Practices

### Code Quality

```python
# ✅ DO: Follow PEP 8
async def process_payment(user_id: int, amount: int) -> bool:
    """Process payment and update balance."""
    try:
        result = await db.create_payment(user_id, amount)
        return result
    except Exception as e:
        logger.error(f"Payment failed: {e}")
        return False

# ❌ DON'T: Ignore style guidelines
async def process_payment(uid,amt):
    r=db.create_payment(uid,amt)
    return r

# ✅ DO: Use meaningful variable names
user_has_sufficient_balance = user_balance > 0

# ❌ DON'T: Use cryptic abbreviations
x = b > 0
```

### Error Handling

```python
# ✅ DO: Handle specific exceptions
try:
    image_url = await generate_image(photo_id, room, style)
except asyncio.TimeoutError:
    logger.error("Generation timeout - Replicate taking too long")
    await message.edit_text("Generation taking too long, please try again")
except replicate.error.ReplicateError as e:
    logger.error(f"Replicate API error: {e}")
    await message.edit_text("AI service error, please try later")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    await message.edit_text("Unexpected error occurred")

# ❌ DON'T: Catch all exceptions silently
try:
    image_url = await generate_image(photo_id, room, style)
except:
    pass  # Bug will be invisible!
```

### Git Workflow

```bash
# ✅ DO: Meaningful commit messages
git commit -m "feat: add photo upload validation for albums"
git commit -m "fix: prevent double-generation when clicking style twice"
git commit -m "docs: add troubleshooting guide"

# ❌ DON'T: Vague messages
git commit -m "fix bug"
git commit -m "changes"
git commit -m "asdf"

# ✅ DO: Small, focused commits
git add bot/handlers/creation.py
git commit -m "fix: validate photo before processing"

# ❌ DON'T: Huge commits mixing features
git add .
git commit -m "lots of stuff"
```

### Documentation

```python
# ✅ DO: Document complex logic
async def style_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle style selection and trigger image generation.
    
    Flow:
    1. Validate balance (prevents edge case where user spent balance between states)
    2. Deduct balance (only for non-admin users)
    3. Call Replicate AI API
    4. Send generated image
    5. Clear FSM state for next cycle
    
    Args:
        callback: Telegram callback query
        state: FSM context with photo_id and room
        
    Returns:
        None (result sent via callback.message.edit_text)
    """
    ...

# ❌ DON'T: Leave complex code undocumented
async def style_chosen(callback, state):
    # TODO: fix this
    x = db.get_balance(y)
    if x:
        z = db.decrease_balance(y)
        # ...
```

---

## 📚 Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - Deep technical architecture
- [API_REFERENCE.md](API_REFERENCE.md) - All handlers and callbacks
- [FSM_GUIDE.md](FSM_GUIDE.md) - State machine details
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) - Code standards

---

## 🎓 Quick Reference

### Command Cheat Sheet

```bash
# Development
python bot/main.py                    # Start bot
Ctrl+C                                # Stop bot
source venv/bin/activate              # Activate venv
pip install -r requirements.txt        # Install deps

# Database
sqlite3 bot.db                        # Open database
.tables                               # List tables
SELECT * FROM users;                 # Query users
.quit                                 # Exit sqlite

# Git
git status                            # See changes
git add .                             # Stage all
git commit -m "message"               # Commit
git push origin main                  # Push
git pull origin main                  # Pull

# Debugging
tail -f bot.log                       # View logs
grep ERROR bot.log                    # Find errors
export DEBUG=1                        # Enable debug
python -m pdb bot/main.py             # Debug mode
```

---

**Document Status:** ✅ Complete  
**Last Updated:** December 12, 2025  
**Version:** 2.0 Professional
