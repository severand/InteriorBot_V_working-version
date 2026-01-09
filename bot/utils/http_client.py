# ========================================
# ФАЙЛ: utils/http_client.py
# НАЗНАЧЕНИЕ: Глобальный HTTP клиент (httpx)
# ВЕРСИЯ: 1.0 (2026-01-09 15:30)
# АВТОР: Project Owner
# ========================================

import httpx
import logging
from typing import Optional
from config import config

logger = logging.getLogger(__name__)


class HTTPClientManager:
    """
    Синглтон для управления глобальным HTTP клиентом (httpx).
    
    🎯 НАЗНАЧЕНИЕ:
    - ✅ ОДИН клиент на весь бот (переиспользование соединений)
    - ✅ Избегаем "Превышен таймаут семафора" на Windows
    - ✅ Pooling соединений
    - ✅ Автоматическое управление жизненным циклом
    
    📖 ИСПОЛЬЗОВАНИЕ:
        >>> client = HTTPClientManager.get()
        >>> response = await client.get("https://example.com")
    
    [2026-01-09 15:30] СОЗДАН для замены aiohttp.ClientSession()
    """
    
    _instance: Optional[httpx.AsyncClient] = None

    @classmethod
    def get(cls) -> httpx.AsyncClient:
        """
        Получить (или создать) глобальный HTTP клиент.
        
        Returns:
            httpx.AsyncClient: Синглтон клиента
        """
        if cls._instance is None:
            # 🔧 Настройка клиента
            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            )
            
            timeout = httpx.Timeout(
                timeout=30.0,  # default timeout
                connect=10.0,
                read=20.0,
                write=10.0,
                pool=5.0
            )
            
            cls._instance = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                http2=False,  # Отключаем HTTP/2 для совместимости
            )
            
            logger.info("✅ HTTPClientManager: Создан глобальный клиент")
        
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """
        Закрыть глобальный клиент (вызови в shutdown).
        
        📍 ИСПОЛЬЗОВАНИЕ:
            >>> await app.add_event_handler("shutdown", HTTPClientManager.close)
        """
        if cls._instance is not None:
            await cls._instance.aclose()
            cls._instance = None
            logger.info("✅ HTTPClientManager: Клиент закрыт")

    @classmethod
    def reset(cls) -> None:
        """
        Принудительно пересоздать клиент (для тестов/дебага).
        
        ⚠️ ОСТОРОЖНО: Используй только если знаешь что делаешь!
        """
        if cls._instance is not None:
            try:
                import asyncio
                asyncio.create_task(cls._instance.aclose())
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при закрытии клиента: {e}")
        
        cls._instance = None
        logger.warning("🔄 HTTPClientManager: Клиент пересоздан")
