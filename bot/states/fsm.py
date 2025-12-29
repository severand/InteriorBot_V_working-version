# bot/states/fsm.py
# --- ОБНОВЛЕН: 2025-12-09 16:24 - Удалены дублирующиеся состояния AdminStates ---
# [2025-12-09 16:24] Состояния AdminStates были определены дважды - оставлено одно определение
# [2025-12-09 16:24] Удалены дублирующиеся: waiting_for_user_id, adding_balance, removing_balance, setting_balance
# [2025-12-24 13:35] PHASE 3: Добавлены состояния ProModeStates для PRO MODE интеграции
# [2025-12-29 14:50] PHASE 1.2: Полная реструктуризация FSM для V3 - WorkMode enum + 19 states (18 экранов)

from enum import Enum
from aiogram.fsm.state import StatesGroup, State


# ==================== РЕЖИМЫ РАБОТЫ БОТА (V3) ====================
class WorkMode(str, Enum):
    """
    Режимы работы бота - используются для управления FSM и интерфейсом
    
    Наследует (str, Enum) чтобы можно было:
    - Сохранять в БД как строку
    - Использовать в FSM
    - Передавать через callback_data
    """
    NEW_DESIGN = "new_design"              # Создание нового дизайна
    EDIT_DESIGN = "edit_design"            # Редактирование дизайна
    SAMPLE_DESIGN = "sample_design"        # Примерка дизайна
    ARRANGE_FURNITURE = "arrange_furniture" # Расстановка мебели
    FACADE_DESIGN = "facade_design"        # Дизайн фасада дома


# ==================== КЛАССЫ СОСТОЯНИЙ ====================

class CreationStates(StatesGroup):
    """
    Машина состояний для процесса создания дизайна (V3)
    
    Всего 19 состояний для 18 экранов + 1 главное меню
    Организованы по уровням (УРОВЕНЬ 1-10) для логической структуры
    Каждый уровень соответствует этапу работы с определенным режимом
    """
    
    # ==================== УРОВЕНЬ 1: Выбор режима ====================
    selecting_mode = State()  # SCREEN 1: MAIN_MENU - выбор режима

    # ==================== УРОВЕНЬ 2: Загрузка фото (все режимы) ====================
    uploading_photo = State()  # SCREEN 2: UPLOADING_PHOTO

    # ==================== УРОВЕНЬ 3: Выбор комнаты (NEW_DESIGN) ====================
    room_choice = State()  # SCREEN 3: ROOM_CHOICE - только для NEW_DESIGN

    # ==================== УРОВЕНЬ 4: Выбор стиля (NEW_DESIGN, EDIT_DESIGN) ====================
    choose_style_1 = State()  # SCREEN 4: CHOOSE_STYLE_1 - страница 1
    choose_style_2 = State()  # SCREEN 5: CHOOSE_STYLE_2 - страница 2

    # ==================== УРОВЕНЬ 5: Редактирование (EDIT_DESIGN) ====================
    edit_design = State()  # SCREEN 8: EDIT_DESIGN - меню редактирования
    clear_confirm = State()  # SCREEN 9: CLEAR_CONFIRM - подтверждение очистки

    # ==================== УРОВЕНЬ 6: Текстовый промт (все режимы) ====================
    text_input = State()  # SCREEN 7: TEXT_INPUT - для всех режимов

    # ==================== УРОВЕНЬ 7: После генерации (все режимы) ====================
    post_generation = State()  # SCREEN 6: POST_GENERATION - для всех режимов

    # ==================== УРОВЕНЬ 8: Примерка дизайна (SAMPLE_DESIGN) ====================
    download_sample = State()  # SCREEN 10: DOWNLOAD_SAMPLE - загрузка образца
    generation_try_on = State()  # SCREEN 11: GENERATION_TRY_ON - генерация примерки
    post_generation_sample = State()  # SCREEN 12: POST_GENERATION_SAMPLE - результат примерки

    # ==================== УРОВЕНЬ 9: Расставить мебель (ARRANGE_FURNITURE) ====================
    uploading_furniture = State()  # SCREEN 13: UPLOADING_FURNITURE - загрузка мебели
    generation_furniture = State()  # SCREEN 14: GENERATION_FURNITURE - генерация
    post_generation_furniture = State()  # SCREEN 15: POST_GENERATION_FURNITURE - результат

    # ==================== УРОВЕНЬ 10: Фасад дома (FACADE_DESIGN) ====================
    loading_facade_sample = State()  # SCREEN 16: LOADING_FACADE_SAMPLE - загрузка образца фасада
    generation_facade = State()  # SCREEN 17: GENERATION_FACADE - генерация фасада
    post_generation_facade = State()  # SCREEN 18: POST_GENERATION_FACADE - результат


class AdminStates(StatesGroup):
    """Состояния админ-панели"""
    waiting_for_user_id = State()
    waiting_for_search = State()  # ожидание поискового запроса
    adding_balance = State()
    removing_balance = State()
    setting_balance = State()


class ReferralStates(StatesGroup):
    """Состояния для реферальной системы"""
    entering_payout_amount = State()      # Ввод суммы выплаты
    entering_exchange_amount = State()    # Ввод количества генераций для обмена
    entering_card_number = State()        # Ввод номера карты
    entering_yoomoney = State()           # Ввод YooMoney
    entering_phone = State()              # Ввод телефона для СБП
    entering_other_method = State()       # Ввод другого способа


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


class OtherStates(StatesGroup):
    pass
