# ========================================
# ФАЙЛ: bot/services/api_fallback.py
# НАЗНАЧЕНИЕ: Smart Fallback система для генерации дизайна
# ВЕРСИЯ: 1.0 (2025-12-23)
# АВТОР: Project Owner
# ========================================
# ЛОГИКА:
# 1. Попытка 1: KIE.AI (если USE_KIE_API=True)
# 2. Попытка 2: Replicate (всегда)
# 3. Результат: URL или None
#
# ИСПОЛЬЗОВАНИЕ:
# from services.api_fallback import smart_generate_interior
# url = await smart_generate_interior(photo_id, room, style, bot_token)
# ========================================

import os
import logging
from typing import Optional
from config import config

# Import обе системы генерации
from services.kie_api import (
    generate_interior_with_flux,
    generate_interior_with_nano_banana,
    clear_space_with_kie,
)
from services.replicate_api import (
    generate_image_auto,
    generate_with_text_prompt,
    clear_space_image,
)

logger = logging.getLogger(__name__)

# ========================================
# КОНФИГУРАЦИЯ FALLBACK
# ========================================

# Читаем флаг USE_KIE_API из конфига
USE_KIE_API = os.getenv('USE_KIE_API', 'False').lower() == 'true'
KIE_API_KEY = os.getenv('KIE_API_KEY')

# Логирование конфига при старте модуля
logger.info("=" * 70)
logger.info("🔄 SMART FALLBACK SYSTEM INITIALIZED")
logger.info(f"   USE_KIE_API: {USE_KIE_API}")
logger.info(f"   KIE_API_KEY configured: {bool(KIE_API_KEY)}")
logger.info(f"   Fallback chain: KIE.AI → Replicate")
logger.info("=" * 70)


# ========================================
# ОСНОВНАЯ ЛОГИКА: ГЕНЕРАЦИЯ ДИЗАЙНА
# ========================================

async def smart_generate_interior(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
) -> Optional[str]:
    """
    Smart Fallback для генерации дизайна интерьера.

    Попытка 1: KIE.AI Flux Kontext (если включен)
    Попытка 2: Replicate nano-banana (всегда)

    Args:
        photo_file_id: ID фото из Telegram
        room: Тип комнаты
        style: Стиль дизайна
        bot_token: Токен бота Telegram

    Returns:
        URL сгенерированного изображения или None

    Логирование:
        - Каждая попытка логируется
        - Время выполнения трассируется
        - Ошибки записываются с полной информацией
    """
    logger.info("=" * 70)
    logger.info("🎨 SMART GENERATE INTERIOR [FALLBACK SYSTEM]")
    logger.info(f"   Room: {room}")
    logger.info(f"   Style: {style}")
    logger.info(f"   Photo: {photo_file_id[:20]}...")
    logger.info("=" * 70)

    result_url = None

    # ========================================
    # ПОПЫТКА 1: KIE.AI Flux Kontext
    # ========================================
    if USE_KIE_API and KIE_API_KEY:
        logger.info("")
        logger.info("🔄 [ATTEMPT 1/2] KIE.AI Flux Kontext")
        logger.info("-" * 70)

        try:
            logger.info("⏳ Запуск KIE.AI Flux Kontext...")
            result_url = await generate_interior_with_flux(
                photo_file_id=photo_file_id,
                room=room,
                style=style,
                bot_token=bot_token,
                strength=0.7,
            )

            if result_url:
                logger.info("✅ [ATTEMPT 1] SUCCESS - KIE.AI Flux Kontext")
                logger.info(f"   Result: {result_url[:80]}...")
                logger.info("=" * 70)
                return result_url
            else:
                logger.warning("⚠️ [ATTEMPT 1] FAILED - No result from KIE.AI")

        except Exception as e:
            logger.error(f"❌ [ATTEMPT 1] ERROR - KIE.AI Flux Kontext")
            logger.error(f"   Exception: {str(e)[:200]}")

    else:
        if not USE_KIE_API:
            logger.info("⏭️  [ATTEMPT 1] SKIPPED - USE_KIE_API=False")
        else:
            logger.warning("⏭️  [ATTEMPT 1] SKIPPED - KIE_API_KEY not configured")

    # ========================================
    # ПОПЫТКА 2: Replicate nano-banana
    # ========================================
    logger.info("")
    logger.info("🔄 [ATTEMPT 2/2] Replicate nano-banana (FALLBACK)")
    logger.info("-" * 70)

    try:
        logger.info("⏳ Запуск Replicate nano-banana...")
        result_url = await generate_image_auto(
            photo_file_id=photo_file_id,
            room=room,
            style=style,
            bot_token=bot_token,
        )

        if result_url:
            logger.info("✅ [ATTEMPT 2] SUCCESS - Replicate nano-banana")
            logger.info(f"   Result: {result_url[:80]}...")
            logger.info("=" * 70)
            return result_url
        else:
            logger.error("❌ [ATTEMPT 2] FAILED - No result from Replicate")

    except Exception as e:
        logger.error(f"❌ [ATTEMPT 2] ERROR - Replicate nano-banana")
        logger.error(f"   Exception: {str(e)[:200]}")

    # ========================================
    # ПОЛНАЯ ОШИБКА
    # ========================================
    logger.error("")
    logger.error("=" * 70)
    logger.error("❌ SMART GENERATE FAILED - ALL ATTEMPTS EXHAUSTED")
    logger.error(f"   Room: {room}, Style: {style}")
    logger.error("=" * 70)

    return None


# ========================================
# ЛОГИКА: ГЕНЕРАЦИЯ С ТЕКСТОВЫМ ПРОМПТОМ
# ========================================

async def smart_generate_with_text(
    photo_file_id: str,
    user_prompt: str,
    bot_token: str,
    scene_type: str = "custom",
) -> Optional[str]:
    """
    Smart Fallback для генерации с пользовательским текстовым промптом.

    Используется для:
    - Экстерьера (дом, участок)
    - "Другого помещения"

    Попытка 1: KIE.AI Nano Banana Edit (если включен)
    Попытка 2: Replicate nano-banana (всегда)

    Args:
        photo_file_id: ID фото из Telegram
        user_prompt: Текстовый промпт от пользователя
        bot_token: Токен бота Telegram
        scene_type: Тип сцены (house_exterior, plot_exterior, other_room, custom)

    Returns:
        URL сгенерированного изображения или None
    """
    logger.info("=" * 70)
    logger.info("✍️  SMART GENERATE WITH TEXT [FALLBACK SYSTEM]")
    logger.info(f"   Scene: {scene_type}")
    logger.info(f"   Prompt: {user_prompt[:50]}...")
    logger.info(f"   Photo: {photo_file_id[:20]}...")
    logger.info("=" * 70)

    result_url = None

    # ========================================
    # ПОПЫТКА 1: KIE.AI Nano Banana Edit
    # ========================================
    if USE_KIE_API and KIE_API_KEY:
        logger.info("")
        logger.info("🔄 [ATTEMPT 1/2] KIE.AI Nano Banana Edit")
        logger.info("-" * 70)

        try:
            logger.info("⏳ Запуск KIE.AI Nano Banana Edit...")
            result_url = await generate_interior_with_nano_banana(
                photo_file_id=photo_file_id,
                room=f"custom_{scene_type}",
                style="text_prompt",
                bot_token=bot_token,
            )

            if result_url:
                logger.info("✅ [ATTEMPT 1] SUCCESS - KIE.AI Nano Banana Edit")
                logger.info(f"   Result: {result_url[:80]}...")
                logger.info("=" * 70)
                return result_url
            else:
                logger.warning("⚠️ [ATTEMPT 1] FAILED - No result from KIE.AI")

        except Exception as e:
            logger.error(f"❌ [ATTEMPT 1] ERROR - KIE.AI Nano Banana Edit")
            logger.error(f"   Exception: {str(e)[:200]}")

    else:
        if not USE_KIE_API:
            logger.info("⏭️  [ATTEMPT 1] SKIPPED - USE_KIE_API=False")
        else:
            logger.warning("⏭️  [ATTEMPT 1] SKIPPED - KIE_API_KEY not configured")

    # ========================================
    # ПОПЫТКА 2: Replicate nano-banana
    # ========================================
    logger.info("")
    logger.info("🔄 [ATTEMPT 2/2] Replicate nano-banana (FALLBACK)")
    logger.info("-" * 70)

    try:
        logger.info("⏳ Запуск Replicate generate_with_text_prompt...")
        result_url = await generate_with_text_prompt(
            photo_file_id=photo_file_id,
            user_prompt=user_prompt,
            bot_token=bot_token,
            scene_type=scene_type,
        )

        if result_url:
            logger.info("✅ [ATTEMPT 2] SUCCESS - Replicate nano-banana")
            logger.info(f"   Result: {result_url[:80]}...")
            logger.info("=" * 70)
            return result_url
        else:
            logger.error("❌ [ATTEMPT 2] FAILED - No result from Replicate")

    except Exception as e:
        logger.error(f"❌ [ATTEMPT 2] ERROR - Replicate nano-banana")
        logger.error(f"   Exception: {str(e)[:200]}")

    # ========================================
    # ПОЛНАЯ ОШИБКА
    # ========================================
    logger.error("")
    logger.error("=" * 70)
    logger.error("❌ SMART GENERATE WITH TEXT FAILED - ALL ATTEMPTS EXHAUSTED")
    logger.error(f"   Scene: {scene_type}, Prompt: {user_prompt[:50]}...")
    logger.error("=" * 70)

    return None


# ========================================
# ЛОГИКА: ОЧИСТКА ПРОСТРАНСТВА
# ========================================

async def smart_clear_space(
    photo_file_id: str,
    bot_token: str,
) -> Optional[str]:
    """
    Smart Fallback для очистки пространства от мебели.

    Попытка 1: KIE.AI Flux Kontext (если включен)
    Попытка 2: Replicate nano-banana (всегда)

    Args:
        photo_file_id: ID фото из Telegram
        bot_token: Токен бота Telegram

    Returns:
        URL очищенного изображения или None
    """
    logger.info("=" * 70)
    logger.info("🧽 SMART CLEAR SPACE [FALLBACK SYSTEM]")
    logger.info(f"   Photo: {photo_file_id[:20]}...")
    logger.info("=" * 70)

    result_url = None

    # ========================================
    # ПОПЫТКА 1: KIE.AI Flux Kontext
    # ========================================
    if USE_KIE_API and KIE_API_KEY:
        logger.info("")
        logger.info("🔄 [ATTEMPT 1/2] KIE.AI Flux Kontext")
        logger.info("-" * 70)

        try:
            logger.info("⏳ Запуск KIE.AI Flux Kontext для очистки...")
            result_url = await clear_space_with_kie(
                photo_file_id=photo_file_id,
                bot_token=bot_token,
            )

            if result_url:
                logger.info("✅ [ATTEMPT 1] SUCCESS - KIE.AI Flux Kontext")
                logger.info(f"   Result: {result_url[:80]}...")
                logger.info("=" * 70)
                return result_url
            else:
                logger.warning("⚠️ [ATTEMPT 1] FAILED - No result from KIE.AI")

        except Exception as e:
            logger.error(f"❌ [ATTEMPT 1] ERROR - KIE.AI Flux Kontext")
            logger.error(f"   Exception: {str(e)[:200]}")

    else:
        if not USE_KIE_API:
            logger.info("⏭️  [ATTEMPT 1] SKIPPED - USE_KIE_API=False")
        else:
            logger.warning("⏭️  [ATTEMPT 1] SKIPPED - KIE_API_KEY not configured")

    # ========================================
    # ПОПЫТКА 2: Replicate nano-banana
    # ========================================
    logger.info("")
    logger.info("🔄 [ATTEMPT 2/2] Replicate nano-banana (FALLBACK)")
    logger.info("-" * 70)

    try:
        logger.info("⏳ Запуск Replicate clear_space_image...")
        result_url = await clear_space_image(
            photo_file_id=photo_file_id,
            bot_token=bot_token,
        )

        if result_url:
            logger.info("✅ [ATTEMPT 2] SUCCESS - Replicate nano-banana")
            logger.info(f"   Result: {result_url[:80]}...")
            logger.info("=" * 70)
            return result_url
        else:
            logger.error("❌ [ATTEMPT 2] FAILED - No result from Replicate")

    except Exception as e:
        logger.error(f"❌ [ATTEMPT 2] ERROR - Replicate nano-banana")
        logger.error(f"   Exception: {str(e)[:200]}")

    # ========================================
    # ПОЛНАЯ ОШИБКА
    # ========================================
    logger.error("")
    logger.error("=" * 70)
    logger.error("❌ SMART CLEAR SPACE FAILED - ALL ATTEMPTS EXHAUSTED")
    logger.error("=" * 70)

    return None


# ========================================
# ИНФОРМАЦИЯ О СИСТЕМЕ
# ========================================

async def get_fallback_status() -> dict:
    """
    Получить статус fallback системы.

    Returns:
        Dict с информацией о доступных провайдерах
    """
    return {
        "kie_api_enabled": USE_KIE_API,
        "kie_api_key_configured": bool(KIE_API_KEY),
        "replicate_available": bool(os.getenv('REPLICATE_API_TOKEN')),
        "primary_provider": "KIE.AI Flux Kontext" if USE_KIE_API else "Replicate nano-banana",
        "fallback_provider": "Replicate nano-banana",
        "fallback_chain": "KIE.AI → Replicate",
    }


if __name__ == "__main__":
    # Для тестирования статуса
    import asyncio

    async def test():
        status = await get_fallback_status()
        logger.info(f"Fallback Status: {status}")

    asyncio.run(test())
