# bot/states/fsm.py
# --- ОБНОВЛЕН: 2025-12-09 16:24 - Удалены дублирующиеся состояния AdminStates ---
# [2025-12-09 16:24] Состояния AdminStates были определены дважды - оставлено одно определение
# [2025-12-09 16:24] Удалены дублирующиеся: waiting_for_user_id, adding_balance, removing_balance, setting_balance
# [2025-12-24 13:35] PHASE 3: Добавлены состояния ProModeStates для PRO MODE интеграции

from aiogram.fsm.state import StatesGroup, State

# Класс состояний для процесса генерации дизайна
class CreationStates(StatesGroup):
    # 1. Ждем фотографию комнаты от пользователя
    waiting_for_photo = State()

    # 2. НОВОЕ: Экран "Что на фото" - выбор между интерьером и экстерьером
    what_is_in_photo = State()

    # 3. Ждем, когда пользователь выберет тип комнаты (спальня, гостиная и т.д.)
    choose_room = State()

    # 4. Ждем, когда пользователь выберет стиль (скандинавский, хай-тек и т.д.)
    choose_style = State()

    # 5. НОВОЕ: Ждем текстовое описание для "Другого помещения"
    waiting_for_room_description = State()

    # 6. НОВОЕ: Ждем текстовый промпт для экстерьера (дом/участок)
    waiting_for_exterior_prompt = State()


# Класс состояний для админ-панели
class AdminStates(StatesGroup):
    """Состояния админ-панели"""
    waiting_for_user_id = State()
    waiting_for_search = State()  # ожидание поискового запроса
    adding_balance = State()
    removing_balance = State()
    setting_balance = State()


# Класс состояний для реферальной системы
class ReferralStates(StatesGroup):
    """Состояния для реферальной системы"""
    entering_payout_amount = State()      # Ввод суммы выплаты
    entering_exchange_amount = State()    # Ввод количества генераций для обмена
    entering_card_number = State()        # Ввод номера карты
    entering_yoomoney = State()           # Ввод YooMoney
    entering_phone = State()              # Ввод телефона для СБП
    entering_other_method = State()       # Ввод другого способа


# Класс состояний для PRO MODE
class ProModeStates(StatesGroup):
    """
    Машина состояний для PRO MODE
    
    Описание:
    - choosing_mode: Выбор между СТАНДАРТ и PRO
    - choosing_pro_params: Выбор параметров PRO (соотношение, разрешение)
    
    Вход:
    - callback: profile_settings нажать "⚙️ НАСТРОЙКИ РЕЖИМА"
    
    Выход:
    - state.set_state(None) и возврат в профиль
    """
    
    # State 1: Выбор режима (СТАНДАРТ vs PRO)
    choosing_mode = State()
    
    # State 2: Выбор параметров PRO (соотношение + разрешение)
    choosing_pro_params = State()


# Класс состояний для других процессов
class OtherStates(StatesGroup):
    pass
