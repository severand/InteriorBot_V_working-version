import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ===== LOGGER SETUP =====
logger = logging.getLogger('InteriorBot')
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)

# Add handler to logger
if not logger.handlers:
    logger.addHandler(console_handler)

# --- АДМИНИСТРАТОРЫ ----
ADMIN_IDS = [
    7884972750,
    827652042,
    5426993389,
    579220409,  # Vlad
    7719810373,  # самсунг старый
    # 6999935990  # добавлено из GitHub (закомментировано)
]


class Config:
    """Configuration class for bot settings"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
    YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
    YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

    # Имя бота для реферальных ссылок
    BOT_USERNAME = os.getenv('BOT_USERNAME', 'InteriorBot')  # БЕЗ @

    # Database settings
    DB_PATH = 'bot.db'

    # Free generations for new users
    FREE_GENERATIONS = 3

    PAYMENT_PACKAGES = {
        'small': {'tokens': 10, 'price': 390, 'name': '10 генераций'},
        'medium': {'tokens': 25, 'price': 877, 'name': '25 генераций'},
        'large': {'tokens': 60, 'price': 1785, 'name': '60 генераций'},
    }

    # ========================================
    # НАСТРОЙКА МОДЕЛИ ГЕНЕРАЦИИ
    # ========================================

    # Переключение между моделями:
    # False = google/nano-banana (базовая версия, быстрее, дешевле)
    # True = google/nano-banana-pro (продвинутая версия, качественнее, медленнее)

    USE_PRO_MODEL = True  # По умолчанию используется базовая модель

    # Для переключения через .env файл раскомментируйте:
    # USE_PRO_MODEL = os.getenv('USE_PRO_MODEL', 'False').lower() == 'true'


# ===== РЕЖИМ ТЕСТИРОВАНИЯ =====
TESTING_MODE = False  # ← Включаем тестовый режим

# При TESTING_MODE = True:
# - Админы получают бесконечные генерации
# - Обычным пользователям показывается сообщение о недоступности оплаты


config = Config()
