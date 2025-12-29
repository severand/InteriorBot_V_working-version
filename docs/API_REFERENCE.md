# 📡 API_REFERENCE - Полный справочник всех обработчиков

**Назначение:** Полная документация по всем обработчикам, callback_data, входным/выходным данным  
**Уровень:** Technical Reference  
**Время на прочтение:** ~45 минут  
**Последнее обновление:** December 12, 2025  

---

## 📋 Содержание

1. [Handler Signatures](#handler-signatures)
2. [Callback Data Reference](#callback-data-reference)
3. [State Data Structures](#state-data-structures)
4. [Error Responses](#error-responses)
5. [Handler Execution Order](#handler-execution-order)
6. [Database Methods](#database-methods)
7. [Service Functions](#service-functions)
8. [Keyboard Functions](#keyboard-functions)

---

## 🎯 Handler Signatures

### USER_START.PY - Initialization & Main Navigation

#### cmd_start()
```python
@router.command('start')
async def cmd_start(message: Message) -> None:
    """
    Handle /start command - user initialization.
    
    Flow:
    1. Check if user exists in DB
    2. Create user with balance=3 if new
    3. Clear FSM state
    4. Show main menu
    
    Args:
        message: Telegram message object from /start command
    
    Side effects:
        - Creates user in DB if not exists
        - Saves menu_message_id to state.data
        - Clears any previous FSM state
    
    Returns:
        None (sends message via message.answer())
    
    Example:
        User sends: /start
        Response: Main menu with 2 buttons
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # Create if new
    user_exists = await db.get_user(user_id)
    if not user_exists:
        await db.create_user(user_id, username)
    
    # Clear state
    await state.set_state(None)
    
    # Show menu
    menu_msg = await message.answer(
        text=START_TEXT,
        reply_markup=get_main_menu_keyboard()
    )
    
    # Save menu_message_id
    await state.update_data(menu_message_id=menu_msg.message_id)
```

#### back_to_main_menu()
```python
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Navigate back to main menu from any state.
    
    Callback Data: "main_menu"
    
    Flow:
    1. Clear FSM state (preserve menu_message_id)
    2. Edit menu message
    3. Show main menu
    
    Args:
        callback: Callback query from button click
        state: FSM context
    
    Returns:
        None (edits existing message)
    
    Notes:
        - Uses state.set_state(None) NOT state.clear()
        - This preserves menu_message_id for cleaner UI
    """
    await state.set_state(None)
    
    await edit_menu(
        callback=callback,
        state=state,
        text=MAIN_MENU_TEXT,
        keyboard=get_main_menu_keyboard()
    )
```

#### show_profile()
```python
@router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Display user profile with balance.
    
    Callback Data: "show_profile"
    
    Args:
        callback: Callback query
        state: FSM context
    
    Response Text Template:
        👤 Your Profile
        Balance: X generations
        User: @username
    
    Buttons:
        💰 Buy Generations | 🏠 Main Menu
    """
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    profile_text = PROFILE_TEXT.format(
        balance=user['balance'],
        username=user['username']
    )
    
    await edit_menu(
        callback=callback,
        state=state,
        text=profile_text,
        keyboard=get_profile_keyboard()
    )
```

#### start_creation()
```python
@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Initialize design creation flow.
    
    Callback Data: "create_design"
    
    State Changes:
        None → waiting_for_photo
    
    Sets State Data:
        - menu_message_id: preserved
    
    Response: Photo upload instruction
    """
    await state.set_state(CreationStates.waiting_for_photo)
    
    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
        ])
    )
```

---

### CREATION.PY - Design Generation (FSM Flow)

#### photo_uploaded()
```python
@router.message(
    content_types=["photo"],
    state=CreationStates.waiting_for_photo
)
async def photo_uploaded(message: Message, state: FSMContext) -> None:
    """
    Handle photo upload in waiting_for_photo state.
    
    Trigger: User sends photo message
    
    State: waiting_for_photo → choose_room
    
    Validations:
        - Check: Not an album (media_group_id)
        - Check: Balance > 0 (skip for admins)
        - Check: Photo file exists
    
    State Data After:
        {
            'menu_message_id': int,
            'photo_id': 'AgAC...',  # Telegram file_id
            'media_group_id': 'xxx'  # For album protection
        }
    
    Response: Room selection buttons (4 options)
    
    Error Cases:
        - Album detected → Delete message, show error
        - Balance <= 0 → Redirect to payment menu
        - Invalid photo → Show error, stay in waiting_for_photo
    """
    user_id = message.from_user.id
    
    # Album protection
    if message.media_group_id:
        data = await state.get_data()
        if data.get('media_group_id') == message.media_group_id:
            await message.delete()
            return
        await state.update_data(media_group_id=message.media_group_id)
    
    # Balance check
    if user_id not in config.ADMIN_IDS:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            # Redirect to payment
            await state.set_state(None)
            # Show payment menu
            return
    
    # Save photo
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(CreationStates.choose_room)
    
    # Show rooms
    await message.answer(
        text=CHOOSE_ROOM_TEXT,
        reply_markup=get_room_keyboard()
    )
```

#### room_chosen()
```python
@router.callback_query(
    F.data.startswith("room_"),
    state=CreationStates.choose_room
)
async def room_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle room type selection.
    
    Trigger: User clicks room button
    Callback Data: "room_living_room", "room_bedroom", etc.
    
    State: choose_room → choose_style
    
    Extracts room_type from callback_data:
        room_living_room → 'living_room'
        room_bedroom → 'bedroom'
        room_kitchen → 'kitchen'
        room_office → 'office'
    
    State Data After:
        {
            'menu_message_id': int,
            'photo_id': 'AgAC...',
            'room': 'living_room'  # Added
        }
    
    Response: Style selection buttons (10 options)
    """
    room_type = callback.data.replace("room_", "")
    
    await state.update_data(room=room_type)
    await state.set_state(CreationStates.choose_style)
    
    await edit_menu(
        callback=callback,
        state=state,
        text=CHOOSE_STYLE_TEXT,
        keyboard=get_style_keyboard()
    )
```

#### style_chosen() - GENERATION TRIGGER
```python
@router.callback_query(
    F.data.startswith("style_"),
    state=CreationStates.choose_style
)
async def style_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle style selection - GENERATES IMAGE HERE.
    
    Trigger: User clicks style button
    Callback Data: "style_modern", "style_minimalist", etc.
    
    State: choose_style → None (FSM cleared)
    
    Critical Flow:
    1. Extract style from callback_data
    2. Get photo_id, room from state.data
    3. Final balance check
    4. Deduct balance (skip for admins)
    5. Show "Processing..." message
    6. Call generate_image() → AI processing
    7. Send generated image to user
    8. Show post-generation menu
    9. Clear FSM state
    
    Extracts style_type:
        style_modern → 'modern'
        style_scandinavian → 'scandinavian'
        etc. (10 total styles)
    
    Time: ~30-60 seconds for generation
    
    Response on Success:
        Generated image + post-gen menu buttons
    
    Response on Failure:
        "Generation failed. Please try again."
    
    Balance Impact:
        user_balance: X → X-1 (only if not admin)
    """
    user_id = callback.from_user.id
    style = callback.data.replace("style_", "")
    
    # Get context
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')
    
    # Final balance check
    if user_id not in config.ADMIN_IDS:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await callback.answer("No generations left")
            return
        
        # Deduct balance
        await db.decrease_balance(user_id)
    
    # Show processing
    await callback.message.edit_text("⏳ Generating design...")
    
    # Generate
    try:
        image_url = await generate_image(
            photo_id=photo_id,
            room=room,
            style=style,
            bot_token=config.BOT_TOKEN
        )
        
        if not image_url:
            raise Exception("No image URL returned")
        
        # Send image
        await callback.message.delete()
        await callback.message.chat.send_photo(
            photo=image_url,
            caption=f"🎨 {style.title()} style for {room}"
        )
        
        # Show post-gen menu
        await callback.message.answer(
            text="Like this design?",
            reply_markup=get_post_generation_keyboard()
        )
    
    except Exception as e:
        logger.error(f"Generation error: {e}")
        await callback.message.edit_text(
            text="❌ Generation failed. Try another style or upload new photo.",
            reply_markup=get_post_generation_keyboard()
        )
    
    finally:
        # Clear FSM state
        await state.set_state(None)
        # Keep only menu_message_id
        await state.update_data(photo_id=None, room=None)
```

---

### PAYMENT.PY - Payment Processing

#### show_packages()
```python
@router.callback_query(F.data == "buy_generations")
async def show_packages(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Display payment packages.
    
    Callback Data: "buy_generations"
    
    Response: 3 package options
        [10 gen - 290₽] [25 gen - 490₽] [60 gen - 990₽]
    
    Buttons: Callback data format: "pay_{tokens}_{price}"
        pay_10_290, pay_25_490, pay_60_990
    """
    await edit_menu(
        callback=callback,
        state=state,
        text="💰 Choose a package:",
        keyboard=get_payment_keyboard()
    )
```

#### create_payment()
```python
@router.callback_query(F.data.startswith("pay_"))
async def create_payment(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Create YooKassa payment.
    
    Trigger: User clicks payment package
    Callback Data: "pay_10_290", "pay_25_490", "pay_60_990"
    
    Parse callback_data:
        pay_TOKENS_PRICE → tokens=10, price=290
    
    Flow:
    1. Parse callback data → tokens, price
    2. Call YooKassa API: create_payment_yookassa()
    3. Get payment_id, confirmation_url
    4. Save to DB: create_payment()
    5. Show payment link + check button
    
    Response:
        💰 Payment link [Pay Now] [I paid!]
    
    DB Entry Created:
        payments table ← new record with status='pending'
    """
    user_id = callback.from_user.id
    
    # Parse
    _, tokens_str, price_str = callback.data.split("_")
    tokens = int(tokens_str)
    price = int(price_str)
    
    # Create payment
    payment_data = await create_payment_yookassa(
        amount=price,
        user_id=user_id,
        tokens=tokens
    )
    
    if not payment_data:
        await callback.answer("❌ Payment creation failed")
        return
    
    payment_id = payment_data['id']
    confirmation_url = payment_data['confirmation_url']
    
    # Save to DB
    await db.create_payment(
        user_id=user_id,
        payment_id=payment_id,
        amount=price,
        tokens=tokens
    )
    
    # Show payment
    await edit_menu(
        callback=callback,
        state=state,
        text=PAYMENT_CREATED.format(tokens=tokens, price=price),
        keyboard=get_payment_check_keyboard(confirmation_url)
    )
```

#### check_payment()
```python
@router.callback_query(F.data == "check_payment")
async def check_payment(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Verify payment status with YooKassa.
    
    Callback Data: "check_payment"
    
    Flow:
    1. Get last pending payment: get_last_pending_payment()
    2. Query YooKassa: find_payment()
    3. If succeeded:
        - Update DB status to 'succeeded'
        - Add tokens to balance
        - Show success message
        - Return to main menu
    4. If pending:
        - Show "Payment not received yet"
        - Allow retry
    
    Response on Success:
        ✅ Payment confirmed!
        New balance: X generations
        🏠 Main Menu button
    
    Response on Pending:
        ⏳ Payment not received yet
        🔄 Check Again button
    
    Balance Impact:
        On success: user_balance += tokens
    """
    user_id = callback.from_user.id
    
    # Get pending payment
    payment = await db.get_last_pending_payment(user_id)
    
    if not payment:
        await callback.answer("❌ No pending payment found")
        return
    
    # Check with YooKassa
    is_paid = await find_payment(payment['yookassa_payment_id'])
    
    if is_paid:
        # Update DB
        await db.set_payment_success(payment['yookassa_payment_id'])
        await db.add_tokens(user_id, payment['tokens'])
        
        # Show success
        new_balance = await db.get_balance(user_id)
        await edit_menu(
            callback=callback,
            state=state,
            text=f"✅ Payment confirmed!\nNew balance: {new_balance}",
            keyboard=get_main_menu_keyboard()
        )
    else:
        # Still pending
        await callback.answer(
            "⏳ Payment not received yet. Try again in a moment.",
            show_alert=True
        )
```

---

## 🔗 Callback Data Reference

### All Callback Types

```
Format: callback_query(F.data == "callback_data")

MAIN NAVIGATION:
├─ main_menu              → Return to main menu
├─ show_profile           → Show profile with balance
├─ create_design          → Start design creation
└─ buy_generations        → Show payment packages

CREATION FLOW (FSM):
├─ room_living_room       → Select living room
├─ room_bedroom           → Select bedroom
├─ room_kitchen           → Select kitchen
├─ room_office            → Select office
├─ back_to_room           → Back to room selection
├─ style_modern           → Generate modern style
├─ style_minimalist       → Generate minimalist style
├─ style_scandinavian     → Generate scandinavian style
├─ style_industrial       → Generate industrial style
├─ style_rustic           → Generate rustic style
├─ style_japandi          → Generate japandi style
├─ style_boho             → Generate boho style
├─ style_mediterranean    → Generate mediterranean style
├─ style_midcentury       → Generate midcentury style
└─ style_artdeco          → Generate artdeco style

POST-GENERATION:
├─ change_style           → Try different style
└─ create_design          → New photo

PAYMENT:
├─ pay_10_290             → Buy 10 gen for 290₽
├─ pay_25_490             → Buy 25 gen for 490₽
├─ pay_60_990             → Buy 60 gen for 990₽
└─ check_payment          → Verify payment status
```

---

## 📊 State Data Structures

### waiting_for_photo state
```python
state.data = {
    'menu_message_id': 12345,        # Telegram message ID
    'user_id': 123456789,            # (optional, for context)
}
```

### choose_room state
```python
state.data = {
    'menu_message_id': 12345,
    'photo_id': 'AgACAgIAAxkBAAI...',  # Telegram file_id
    'media_group_id': 'g123',          # Album protection
}
```

### choose_style state
```python
state.data = {
    'menu_message_id': 12345,
    'photo_id': 'AgACAgIAAxkBAAI...',
    'room': 'living_room',  # living_room, bedroom, kitchen, office
}
```

### After generation (None state)
```python
state.data = {
    'menu_message_id': 12345,  # Only this remains
}
```

---

## ⚠️ Error Responses

### Common Error Messages

```python
# No balance
"❌ You have no generations left. Buy more to continue."

# Generation failed
"❌ Generation failed. Please try again later."

# Payment failed
"❌ Payment creation failed. Try again."

# Album detected
"⚠️  Please send photos one at a time, not as an album."

# Invalid input
"❌ Invalid selection. Please try again."

# Timeout
"⏳ Request timed out. Please try again."
```

### Error Handling Pattern

```python
try:
    result = await some_operation()
except asyncio.TimeoutError:
    logger.error("Timeout")
    await callback.answer("⏳ Request timed out")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    await callback.answer("❌ Something went wrong")
```

---

## ⚙️ Handler Execution Order

### Router Priority

```
1. user_start.router  (Priority 1 - first check)
2. creation.router    (Priority 2 - second check)
3. payment.router     (Priority 3 - last check)

This ensures /start always gets processed first,
FSM handlers get priority over payment,
and payment handlers as fallback.
```

### Command vs Callback vs Message Processing

```
@router.command('start')           ← Commands (highest priority)
@router.callback_query()           ← Callbacks (medium priority)
@router.message()                  ← Messages (lowest priority)

Example:
  User sends: /start
  → @router.command('start') executes immediately
  → Other handlers never checked
```

---

## 💾 Database Methods Reference

### User Operations

```python
# Create new user
await db.create_user(user_id: int, username: str) -> bool
# Returns: True if success, False if error
# Side effect: Creates row with balance=3

# Get user
await db.get_user(user_id: int) -> Optional[Dict]
# Returns: {'user_id': int, 'username': str, 'balance': int, 'reg_date': str}
#          or None if not found

# Get balance
await db.get_balance(user_id: int) -> int
# Returns: balance value or 0 if not found

# Decrease balance (for generation)
await db.decrease_balance(user_id: int) -> bool
# Returns: True if success
# Side effect: balance = balance - 1

# Increase balance (for payment)
await db.increase_balance(user_id: int, amount: int) -> bool
# Returns: True if success
# Side effect: balance = balance + amount
```

### Payment Operations

```python
# Create payment record
await db.create_payment(
    user_id: int,
    payment_id: str,        # YooKassa ID
    amount: int,           # Price in rubles
    tokens: int           # Tokens to grant
) -> bool
# Returns: True if success
# Status: always 'pending' initially

# Get last pending payment
await db.get_last_pending_payment(user_id: int) -> Optional[Dict]
# Returns: {'id': int, 'user_id': int, 'yookassa_payment_id': str, ...}
#          or None if not found
# Query: WHERE user_id AND status='pending' ORDER BY created_at DESC LIMIT 1

# Set payment as succeeded
await db.set_payment_success(payment_id: str) -> bool
# Returns: True if success
# Side effect: status = 'pending' → 'succeeded'

# Add tokens (alias for increase_balance)
await db.add_tokens(user_id: int, tokens: int) -> bool
# Same as increase_balance()
```

---

## 🔧 Service Functions Reference

### Replicate API (generate_image)

```python
async def generate_image(
    photo_id: str,           # Telegram file_id
    room: str,              # 'living_room', 'bedroom', 'kitchen', 'office'
    style: str,             # 'modern', 'minimalist', etc. (10 options)
    bot_token: str          # Telegram bot token
) -> Optional[str]:         # Returns image URL or None

# Parameters validation:
  room must be in: living_room, bedroom, kitchen, office
  style must be in: modern, minimalist, scandinavian, industrial, rustic,
                    japandi, boho, mediterranean, midcentury, artdeco

# Returns:
  Success: 'https://replicate.delivery/...../output.png'
  Failure: None

# Errors raised (caught internally):
  - asyncio.TimeoutError (60 sec timeout)
  - replicate.error.ReplicateError
  - httpx.TimeoutException
  - httpx.HTTPStatusError
```

### YooKassa Payment API

```python
async def create_payment_yookassa(
    amount: int,            # Price in rubles (290, 490, 990)
    user_id: int,          # Telegram user ID
    tokens: int            # Tokens to grant (10, 25, 60)
) -> Optional[Dict]:        # Returns payment data or None

# Returns:
  {
    'id': 'payment_id_from_yookassa',
    'amount': 490,
    'tokens': 25,
    'confirmation_url': 'https://yookassa.ru/auth/...'
  }

async def find_payment(payment_id: str) -> bool:
  # Returns: True if status='succeeded', False otherwise
  # Checks: pending, failed, canceled → all return False
```

---

## 🎨 Keyboard Functions Reference

### All Keyboard Builders

```python
# Main menu (2 buttons)
get_main_menu_keyboard() -> InlineKeyboardMarkup
# Buttons: [Create Design] [Profile]
# callback_data: create_design, show_profile

# Profile (2 buttons)
get_profile_keyboard() -> InlineKeyboardMarkup
# Buttons: [Buy Generations] [Main Menu]
# callback_data: buy_generations, main_menu

# Room selection (5 buttons)
get_room_keyboard() -> InlineKeyboardMarkup
# Buttons:
#   [Living Room] [Bedroom]
#   [Kitchen] [Office]
#   [Main Menu]
# callback_data: room_living_room, room_bedroom, room_kitchen, room_office, main_menu

# Style selection (12 buttons)
get_style_keyboard() -> InlineKeyboardMarkup
# Buttons (2 per row):
#   [Modern] [Minimalist]
#   [Scandinavian] [Industrial]
#   [Rustic] [Japandi]
#   [Boho] [Mediterranean]
#   [Midcentury] [ArtDeco]
#   [Back to Rooms] [Main Menu]
# callback_data: style_modern, style_minimalist, ..., back_to_room, main_menu

# Payment packages (4 buttons)
get_payment_keyboard() -> InlineKeyboardMarkup
# Buttons:
#   [10 gen - 290₽] [25 gen - 490₽] [60 gen - 990₽]
#   [Main Menu]
# callback_data: pay_10_290, pay_25_490, pay_60_990, main_menu

# Payment check (4 buttons)
get_payment_check_keyboard(url: str) -> InlineKeyboardMarkup
# Parameters:
#   url: confirmation URL from YooKassa
# Buttons:
#   [Pay Now (url)] [I paid!]
#   [Main Menu]
# callback_data: check_payment, main_menu

# Post-generation (4 buttons)
get_post_generation_keyboard() -> InlineKeyboardMarkup
# Buttons:
#   [Other Style] [New Photo]
#   [Profile] [Main Menu]
# callback_data: change_style, create_design, show_profile, main_menu
```

---

**Document Status:** ✅ Complete  
**Last Updated:** December 12, 2025  
**Version:** 2.0 Professional
