# ========================================
# ФАЙЛ: bot/config_kie.py
# НАЗНАЧЕНИЕ: Конфигурация Nano Banana API по Kie.ai
# ВЕРСИЯ: 2.1 (2025-12-23) - ОНЛИ NANO BANANA
# ========================================
# ИНСТРУКЦИЯ:
# 1. Добавить в .env файл:
#    KIE_API_KEY=your_kie_api_key_here
#    USE_KIE_API=True
#
# 2. В bot/main.py импортировать:
#    from bot.config_kie import config_kie
#
# ========================================

import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class KieConfig:
    """
    Конфигурация для Kie.ai Nano Banana API.
    """

    # ===== ОСНОВНАЯ КОНФИГУРАЦИЯ =====
    KIE_API_KEY: Optional[str] = os.getenv('KIE_API_KEY')
    USE_KIE_API: bool = os.getenv('USE_KIE_API', 'False').lower() == 'true'

    # ===== NANO BANANA КОНФИГУРАЦИЯ =====
    KIE_API_BASE_URL: str = "https://api.kie.ai"
    KIE_API_TIMEOUT: int = 300
    
    # Параметры Nano Banana
    KIE_NANO_BANANA_FORMAT: str = os.getenv('KIE_NANO_BANANA_FORMAT', 'png')
    KIE_NANO_BANANA_SIZE: str = os.getenv('KIE_NANO_BANANA_SIZE', 'auto')

    # Fallback стратегия
    KIE_FALLBACK_TO_REPLICATE: bool = os.getenv('KIE_FALLBACK_TO_REPLICATE', 'True').lower() == 'true'

    # Логирование
    KIE_VERBOSE: bool = os.getenv('KIE_VERBOSE', 'False').lower() == 'true'

    @classmethod
    def validate(cls) -> bool:
        """Проверить корректность конфигурации."""
        if cls.USE_KIE_API and not cls.KIE_API_KEY:
            print("⚠️ WARNING: USE_KIE_API=True бут KIE_API_KEY not set!")
            return False
        return True

    @classmethod
    def info(cls) -> str:
        """Полная информация о конфигурации."""
        return f"""
✅ KIE.AI NANO BANANA API КОНФИГ:
  API KEY installed: {bool(cls.KIE_API_KEY)}
  USE_KIE_API: {cls.USE_KIE_API}
  Format: {cls.KIE_NANO_BANANA_FORMAT}
  Size: {cls.KIE_NANO_BANANA_SIZE}
  Timeout: {cls.KIE_API_TIMEOUT}s
  Fallback: {cls.KIE_FALLBACK_TO_REPLICATE}
        """


config_kie = KieConfig()

if __name__ == "__main__":
    print(config_kie.info())
    print(f"Valid: {config_kie.validate()}")
