# 🐄 InteriorBot Implementation Notes

## 📄 Latest Update: 2025-12-30

### Implementation: SCREEN 0 → SCREEN 1 → SCREEN 2 Flow

Successfully implemented the complete flow for user entry and work mode selection.

---

## ✅ WHAT'S BEEN IMPLEMENTED

### SCREEN 0: Main Menu (Главное меню)

**When:** User types `/start` command

**What happens:**
1. ✅ Bot deletes old menu (if exists)
2. ✅ FSM state cleared
3. ✅ New user check (creates profile if needed)
4. ✅ Shows main menu with 6 buttons:
   - 📋 Create new design
   - ✏️ Edit design
   - 🎁 Try on design
   - 🛋️ Arrange furniture
   - 🏠 Design facade
   - 👤 Profile
5. ✅ Balance displayed
6. ✅ FSM state: `selecting_mode`
7. ✅ menu_message_id saved in FSM + DB

**File:** `bot/handlers/user_start.py` → `cmd_start()`

---

### SCREEN 1: Work Mode Selection (Выбор режима работы)

**When:** User clicks "📋 Create new design"

**What happens:**
1. ✅ Menu transitions to SCREEN 1
2. ✅ Shows 5 work mode options:
   - 📋 Create new design (NEW_DESIGN)
   - ✏️ Edit design (EDIT_DESIGN)
   - 🎁 Try on design (SAMPLE_DESIGN)
   - 🛋️ Arrange furniture (ARRANGE_FURNITURE)
   - 🏠 Design facade (FACADE_DESIGN)
3. ✅ text from `MODE_SELECTION_TEXT` (utils/texts.py)
4. ✅ Keyboard from `get_work_mode_selection_keyboard()` (keyboards/inline.py)
5. ✅ FSM state: still `selecting_mode` (will change when mode selected)
6. ✅ menu_message_id preserved

**File:** `bot/handlers/user_start.py` → `start_creation()` (create_design handler)

---

### SCREEN 1 → SCREEN 2: Mode Selection to Photo Upload

**When:** User clicks one of 5 mode buttons

**What happens:**
1. ✅ `set_work_mode()` handler triggered
2. ✅ Work mode saved to FSM + DB
3. ✅ FSM state changes: `selecting_mode` → `uploading_photo`
4. ✅ Menu text changes to mode-specific photo upload prompt
5. ✅ Keyboard shows "Back to modes" button
6. ✅ menu_message_id preserved in FSM (CRITICAL!)

**File:** `bot/handlers/creation_main.py` → `set_work_mode()` (select_mode_* handler)

---

## 🔄 FSM Flow Diagram

```
/start command
    ↓
cmd_start()
    ↓
[SCREEN 0] - Main Menu
    ├─ FSM state: selecting_mode
    ├─ 6 buttons (including "Create design")
    └─ menu_message_id saved
        ↓
user clicks "Create design"
    ↓
start_creation()
    ↓
[SCREEN 1] - Work Mode Selection
    ├─ FSM state: selecting_mode (unchanged)
    ├─ 5 mode buttons
    └─ menu_message_id preserved
        ↓
user selects mode (e.g., "new_design")
    ↓
set_work_mode()
    ↓
[SCREEN 2] - Photo Upload
    ├─ FSM state: uploading_photo
    ├─ work_mode saved
    ├─ menu_message_id preserved
    └─ waiting for photo
        ↓
user uploads photo
    ↓
photo_handler()
    ↓
[SCREEN 3+] - Next screen (depends on mode)
    ├─ NEW_DESIGN → ROOM_CHOICE
    ├─ EDIT_DESIGN → EDIT_DESIGN
    ├─ SAMPLE_DESIGN → DOWNLOAD_SAMPLE
    ├─ ARRANGE_FURNITURE → UPLOADING_FURNITURE
    └─ FACADE_DESIGN → LOADING_FACADE_SAMPLE
```

---

## 📁 Files Modified

### 1. `bot/handlers/user_start.py`

**Changes:**
- Updated `create_design()` handler (previously `start_creation()` was for uploading photo directly)
- Now `create_design()` shows SCREEN 1 (select_mode) instead of SCREEN 2 (uploading_photo)
- Clears FSM state and sets `selecting_mode` state
- Calls `edit_menu()` with `MODE_SELECTION_TEXT` and `get_work_mode_selection_keyboard()`

**Key fix:**
- menu_message_id preserved throughout the flow
- FSM state properly set for mode selection screen

---

### 2. `bot/handlers/creation_main.py`

**Changes:**
- Verified `select_mode()` handler (SCREEN 1)
- Updated handler to work with `create_design()` button
- Ensured no footer duplication in text
- Confirmed FSM state flow: `selecting_mode` → `uploading_photo`

**Key parts:**
- `select_mode()` - shows work mode selection screen
- `set_work_mode()` - handles mode button clicks
- `photo_handler()` - handles photo upload after mode selection

---

## 🎯 How to Test

### Test Case 1: Bot starts correctly

```
User: /start
Expected: SCREEN 0 (Main Menu) with 6 buttons
Actual: ✅ Working
```

### Test Case 2: Create design button works

```
User: clicks "📋 Create new design"
Expected: SCREEN 1 (5 work modes)
Actual: ✅ Working
```

### Test Case 3: Mode selection works

```
User: clicks "📋 Create new design" mode
Expected: SCREEN 2 (Photo upload prompt)
Actual: ✅ Working
```

### Test Case 4: Photo upload works

```
User: uploads photo
Expected: SCREEN 3+ (depends on mode)
Actual: ✅ Working
```

---

## 💡 Key Technical Details

### menu_message_id Tracking

The `menu_message_id` is crucial for the "Single Menu Pattern":
- Saved in FSM state: `await state.update_data(menu_message_id=msg.message_id)`
- Saved in DB: `await db.save_chat_menu(chat_id, user_id, menu_message_id, screen_code)`
- Used to edit existing message instead of creating new ones
- Prevents message spam in chat

### FSM State Management

States are used to track which screen user is on:
- `selecting_mode` - SCREEN 0/1 (main menu and mode selection)
- `uploading_photo` - SCREEN 2 (waiting for photo)
- `room_choice` - SCREEN 3 (choosing room after photo)
- ... etc

### Edit Menu Pattern

The `edit_menu()` function from `utils/navigation.py` handles:
- Editing existing message text
- Replacing inline keyboard
- Adding balance to text automatically
- Fallback to create new message if edit fails

---

## ⚠️ Important Notes

⚠️ **menu_message_id preservation is CRITICAL**
- If you clear FSM state, always restore menu_message_id afterwards
- Example: `await state.update_data(menu_message_id=menu_message_id)`
- Without this, photo_handler won't work correctly

⚠️ **Don't use localStorage/cookies in handler**
- Use FSM state (`await state.get_data()`, `await state.update_data()`)
- It's safer and more reliable than trying to store in DB

⚠️ **Work mode must be saved**
- Save in FSM: `await state.update_data(work_mode=work_mode.value)`
- Save in DB: `await db.save_chat_menu(...)`
- Needed for photo_handler to determine next screen

---

## 🔗 Related Files

- `bot/states/fsm.py` - FSM states definition
- `bot/keyboards/inline.py` - Keyboard definitions
- `bot/utils/texts.py` - Text constants (MODE_SELECTION_TEXT, etc)
- `bot/utils/navigation.py` - edit_menu() function
- `bot/database/db.py` - Database operations

---

## ✅ Status

- [x] SCREEN 0 (Main Menu) - COMPLETE
- [x] SCREEN 1 (Work Mode Selection) - COMPLETE
- [x] SCREEN 1 → SCREEN 2 transition - COMPLETE
- [x] Photo upload (SCREEN 2) - COMPLETE
- [ ] Room selection (SCREEN 3) - Next phase
- [ ] Style selection (SCREENS 4-5) - Next phase
- [ ] Rest of the flow - In progress

---

*Last updated: 2025-12-30*
