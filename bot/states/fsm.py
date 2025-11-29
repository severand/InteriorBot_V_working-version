from aiogram.fsm.state import StatesGroup, State

# Класс состояний для процесса генерации дизайна
class CreationStates(StatesGroup):
    # 1. Ждем фотографию комнаты от пользователя
    waiting_for_photo = State()

    # 2. Ждем, когда пользователь выберет тип комнаты (спальня, гостиная и т.д.)
    choose_room = State()

    # 3. Ждем, когда пользователь выберет стиль (скандинавский, хай-тек и т.д.)
    choose_style = State()


# Класс состояний для других процессов (если понадобятся, например, админка)
class AdminStates(StatesGroup):
    """Состояния админ-панели"""
    waiting_for_user_id = State()
    adding_balance = State()
    removing_balance = State()
    setting_balance = State()
    pass