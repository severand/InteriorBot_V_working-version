# ========================================
# ФАЙЛ: bot/config_kie.py
# НАЗНАЧЕНИЕ: Конфигурация Nano Banana API по Kie.ai
# ВЕРСИЯ: 2.2 (2025-12-24) - ДОБАВЛЕНА ПОДДЕРЖКА PRO РЕЖИМА
# ========================================
# ИНСТРУКЦИЯ:
# 1. Добавить в .env файл:
#    KIE_API_KEY=your_kie_api_key_here
#    USE_KIE_API=True
#    USE_PRO_MODEL=False  # [НОВОЕ 2025-12-24]
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
    [НОВОЕ 2025-12-24] Добавлена поддержка PRO режима.
    """

    # ===== ОСНОВНАЯ КОНФИГУРАЦИЯ =====
    KIE_API_KEY: Optional[str] = os.getenv('KIE_API_KEY')
    USE_KIE_API: bool = os.getenv('USE_KIE_API', 'False').lower() == 'true'

    # ===== NANO BANANA КОНФИГУРАЦИЯ =====
    KIE_API_BASE_URL: str = "https://api.kie.ai"
    
    # Параметры Nano Banana
    KIE_NANO_BANANA_FORMAT: str = os.getenv('KIE_NANO_BANANA_FORMAT', 'png')
    KIE_NANO_BANANA_SIZE: str = os.getenv('KIE_NANO_BANANA_SIZE', 'auto')

    # Fallback стратегия
    KIE_FALLBACK_TO_REPLICATE: bool = os.getenv('KIE_FALLBACK_TO_REPLICATE', 'True').lower() == 'true'

    # Логирование
    KIE_VERBOSE: bool = os.getenv('KIE_VERBOSE', 'False').lower() == 'true'

    # ===== PRO РЕЖИМ [НОВОЕ 2025-12-24] =====
    # Переключение между BASE и PRO режимом
    USE_PRO_MODEL: bool = os.getenv('USE_PRO_MODEL', 'False').lower() == 'true'
    
    # Параметры для PRO режима
    # aspect_ratio: 1:1, 16:9, 9:16, 4:3, 3:4 и т.д.
    KIE_NANO_BANANA_PRO_ASPECT: str = os.getenv('KIE_NANO_BANANA_PRO_ASPECT', '16:9')
    
    # resolution: 1K (1024), 2K (2048), 4K (4096)
    KIE_NANO_BANANA_PRO_RESOLUTION: str = os.getenv('KIE_NANO_BANANA_PRO_RESOLUTION', '1K')
    
    # Таймауты для разных режимов
    # BASE: 300 сек (5 минут)
    # PRO: 600 сек (10 минут) - потому что качество требует больше времени
    KIE_API_TIMEOUT_BASE: int = int(os.getenv('KIE_API_TIMEOUT_BASE', '300'))
    KIE_API_TIMEOUT_PRO: int = int(os.getenv('KIE_API_TIMEOUT_PRO', '600'))
    
    @property
    def KIE_API_TIMEOUT(self) -> int:
        """
        Динамический таймаут в зависимости от режима.
        [НОВОЕ 2025-12-24] Автоматически выбирает таймаут
        """
        if self.USE_PRO_MODEL:
            return self.KIE_API_TIMEOUT_PRO
        else:
            return self.KIE_API_TIMEOUT_BASE

    @classmethod
    def validate(cls) -> bool:
        """Проверить корректность конфигурации."""
        if cls.USE_KIE_API and not cls.KIE_API_KEY:
            print("⚠️  WARNING: USE_KIE_API=True бут KIE_API_KEY not set!")
            return False
        return True

    @classmethod
    def info(cls) -> str:
        """Полная информация о конфигурации."""
        mode = "PRO 🕹" if cls.USE_PRO_MODEL else "BASE 📋"
        return f"""
✅ KIE.AI NANO BANANA API КОНФИГ:
  Mode: {mode}
  API KEY installed: {bool(cls.KIE_API_KEY)}
  USE_KIE_API: {cls.USE_KIE_API}
  Format: {cls.KIE_NANO_BANANA_FORMAT}
  Size (BASE): {cls.KIE_NANO_BANANA_SIZE}
  PRO Aspect: {cls.KIE_NANO_BANANA_PRO_ASPECT}
  PRO Resolution: {cls.KIE_NANO_BANANA_PRO_RESOLUTION}
  Timeout (BASE): {cls.KIE_API_TIMEOUT_BASE}s
  Timeout (PRO): {cls.KIE_API_TIMEOUT_PRO}s
  Fallback: {cls.KIE_FALLBACK_TO_REPLICATE}
        """


config_kie = KieConfig()

if __name__ == "__main__":
    print(config_kie.info())
    print(f"Valid: {config_kie.validate()}")
    print(f"Current timeout: {config_kie.KIE_API_TIMEOUT}s")
