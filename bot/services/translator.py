# ========================================
# ФАЙЛ: bot/services/translator.py
# НАЗНАЧЕНИЕ: Система перевода промтов на английский
# ВЕРСИЯ: 1.0 (2025-12-23)
# АВТОР: Project Owner
# ========================================
# НАЗНАЧЕНИЕ:
#   Переводит текстовые промпты с русского на английский
#   перед отправкой в KIE.AI и Replicate API для улучшения качества генерации
#
# ПОДДЕРЖИВАЕМЫЕ ПРОВАЙДЕРЫ ПЕРЕВОДА:
#   1. Google Translate API (основной, платный)
#   2. LibreTranslate (открытый, бесплатный) - fallback
#   3. Яндекс Переводчик (платный) - альтернатива
#
# ИСПОЛЬЗОВАНИЕ:
#   from services.translator import translate_prompt_to_english
#   english_prompt = await translate_prompt_to_english(russian_prompt)
# ========================================

import logging
import aiohttp
from typing import Optional
from config import config
import os

logger = logging.getLogger(__name__)

# ========================================
# КОНФИГУРАЦИЯ
# ========================================

USE_TRANSLATION = os.getenv('USE_PROMPT_TRANSLATION', 'True').lower() == 'true'
TRANSLATION_PROVIDER = os.getenv('TRANSLATION_PROVIDER', 'google_translate')  # google_translate, libre_translate, yandex

# Google Translate API
GOOGLE_TRANSLATE_API_KEY = os.getenv('GOOGLE_TRANSLATE_API_KEY')
GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"

# LibreTranslate (open-source)
LIBRE_TRANSLATE_URL = os.getenv('LIBRE_TRANSLATE_URL', 'https://libretranslate.de/translate')
LIBRE_TRANSLATE_API_KEY = os.getenv('LIBRE_TRANSLATE_API_KEY', '')

# Яндекс Переводчик
YANDEX_TRANSLATE_API_KEY = os.getenv('YANDEX_TRANSLATE_API_KEY')
YANDEX_TRANSLATE_URL = "https://api.yandex.cloud/translate/v2/translate"

# Логирование конфига
logger.info("="*70)
logger.info("🌐 PROMPT TRANSLATOR INITIALIZED")
logger.info(f"   Translation enabled: {USE_TRANSLATION}")
logger.info(f"   Primary provider: {TRANSLATION_PROVIDER}")
logger.info(f"   Google Translate API key: {bool(GOOGLE_TRANSLATE_API_KEY)}")
logger.info(f"   LibreTranslate configured: {bool(LIBRE_TRANSLATE_URL)}")
logger.info(f"   Yandex Translate API key: {bool(YANDEX_TRANSLATE_API_KEY)}")
logger.info("="*70)


# ========================================
# КЭШИРОВАНИЕ ПЕРЕВОДОВ
# ========================================

_TRANSLATION_CACHE = {}  # {russian_text: english_text}


# ========================================
# ОСНОВНАЯ ФУНКЦИЯ ПЕРЕВОДА
# ========================================

async def translate_prompt_to_english(russian_text: str) -> str:
    """
    Переводит промпт с русского на английский.
    
    Логика:
    1. Если translation отключен → возвращает исходный текст
    2. Если текст в кэше → возвращает из кэша
    3. Попытка основного провайдера (Google/Yandex/LibreTranslate)
    4. Fallback: LibreTranslate
    5. Fallback: возвращает исходный текст (без перевода)
    
    Args:
        russian_text: Текст промпта на русском языке
        
    Returns:
        Переведённый текст на английский или исходный текст
        
    Логирование:
        - Каждый перевод логируется с временем выполнения
        - Ошибки записываются с полной информацией
    """
    
    # Если перевод отключен
    if not USE_TRANSLATION:
        logger.debug(f"⏭️  Translation disabled, returning original text")
        return russian_text
    
    # Если текст короче 10 символов - не переводим
    if len(russian_text.strip()) < 10:
        logger.debug(f"⏭️  Text too short, returning original")
        return russian_text
    
    # Проверка кэша
    if russian_text in _TRANSLATION_CACHE:
        logger.debug(f"✅ Translation found in cache (length={len(russian_text)})")
        return _TRANSLATION_CACHE[russian_text]
    
    logger.info("="*70)
    logger.info(f"🌐 TRANSLATING PROMPT TO ENGLISH")
    logger.info(f"   Length: {len(russian_text)} chars")
    logger.info(f"   Provider: {TRANSLATION_PROVIDER}")
    logger.info("-"*70)
    
    result = None
    
    # ========================================
    # ПОПЫТКА 1: Основной провайдер
    # ========================================
    try:
        if TRANSLATION_PROVIDER == 'google_translate':
            result = await _translate_google(russian_text)
        elif TRANSLATION_PROVIDER == 'yandex':
            result = await _translate_yandex(russian_text)
        elif TRANSLATION_PROVIDER == 'libre_translate':
            result = await _translate_libre(russian_text)
        
        if result:
            logger.info(f"✅ [PRIMARY] Translation successful")
            logger.info(f"   Result length: {len(result)} chars")
            
            # Кэшируем результат
            _TRANSLATION_CACHE[russian_text] = result
            logger.info("="*70)
            return result
        else:
            logger.warning(f"⚠️  [PRIMARY] No result from {TRANSLATION_PROVIDER}")
    
    except Exception as e:
        logger.error(f"❌ [PRIMARY] Error with {TRANSLATION_PROVIDER}: {str(e)[:100]}")
    
    # ========================================
    # FALLBACK: LibreTranslate
    # ========================================
    logger.info(f"🔄 Attempting FALLBACK: LibreTranslate")
    try:
        result = await _translate_libre(russian_text)
        if result:
            logger.info(f"✅ [FALLBACK] LibreTranslate successful")
            
            # Кэшируем результат
            _TRANSLATION_CACHE[russian_text] = result
            logger.info("="*70)
            return result
        else:
            logger.warning(f"⚠️  [FALLBACK] LibreTranslate returned empty result")
    
    except Exception as e:
        logger.error(f"❌ [FALLBACK] LibreTranslate error: {str(e)[:100]}")
    
    # ========================================
    # ПОЛНАЯ ОШИБКА: Возвращаем исходный текст
    # ========================================
    logger.warning("")
    logger.warning("="*70)
    logger.warning("❌ TRANSLATION FAILED - Returning original Russian text")
    logger.warning("="*70)
    
    # Кэшируем "не переведено" чтобы не пытаться заново
    _TRANSLATION_CACHE[russian_text] = russian_text
    
    return russian_text


# ========================================
# ПРОВАЙДЕРЫ ПЕРЕВОДА
# ========================================

async def _translate_google(text: str) -> Optional[str]:
    """
    Перевод с использованием Google Translate API.
    
    Требует: GOOGLE_TRANSLATE_API_KEY
    Документация: https://cloud.google.com/translate/docs/basic/setup
    """
    if not GOOGLE_TRANSLATE_API_KEY:
        logger.warning("⏭️  Google Translate API key not configured")
        return None
    
    try:
        logger.debug("⏳ Google Translate API request...")
        
        async with aiohttp.ClientSession() as session:
            params = {
                'key': GOOGLE_TRANSLATE_API_KEY,
                'q': text,
                'source_language': 'ru',
                'target_language': 'en',
            }
            
            async with session.post(
                GOOGLE_TRANSLATE_URL,
                json=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    translations = data.get('data', {}).get('translations', [])
                    if translations:
                        return translations[0].get('translatedText')
                else:
                    logger.error(f"Google Translate API returned {resp.status}")
        
        return None
    
    except Exception as e:
        logger.error(f"Google Translate error: {e}")
        return None


async def _translate_yandex(text: str) -> Optional[str]:
    """
    Перевод с использованием Yandex Translate API.
    
    Требует: YANDEX_TRANSLATE_API_KEY
    Документация: https://cloud.yandex.com/docs/translate/api-ref/
    """
    if not YANDEX_TRANSLATE_API_KEY:
        logger.warning("⏭️  Yandex Translate API key not configured")
        return None
    
    try:
        logger.debug("⏳ Yandex Translate API request...")
        
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Api-Key {YANDEX_TRANSLATE_API_KEY}',
                'Content-Type': 'application/json',
            }
            
            payload = {
                'sourceLanguageCode': 'ru',
                'targetLanguageCode': 'en',
                'texts': [text]
            }
            
            async with session.post(
                YANDEX_TRANSLATE_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    translations = data.get('translations', [])
                    if translations:
                        return translations[0].get('text')
                else:
                    logger.error(f"Yandex Translate API returned {resp.status}")
        
        return None
    
    except Exception as e:
        logger.error(f"Yandex Translate error: {e}")
        return None


async def _translate_libre(text: str) -> Optional[str]:
    """
    Перевод с использованием LibreTranslate (open-source).
    
    Бесплатный вариант, но может быть медленнее.
    Можно развернуть свой сервер: https://github.com/LibreTranslate/LibreTranslate
    """
    if not LIBRE_TRANSLATE_URL:
        logger.warning("⏭️  LibreTranslate URL not configured")
        return None
    
    try:
        logger.debug("⏳ LibreTranslate API request...")
        
        async with aiohttp.ClientSession() as session:
            payload = {
                'q': text,
                'source': 'ru',
                'target': 'en',
            }
            
            if LIBRE_TRANSLATE_API_KEY:
                payload['api_key'] = LIBRE_TRANSLATE_API_KEY
            
            async with session.post(
                LIBRE_TRANSLATE_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15)  # LibreTranslate медленнее
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('translatedText') or data.get('translated')
                else:
                    logger.error(f"LibreTranslate returned {resp.status}")
        
        return None
    
    except Exception as e:
        logger.error(f"LibreTranslate error: {e}")
        return None


# ========================================
# УТИЛИТЫ
# ========================================

def clear_translation_cache():
    """
    Очищает кэш переводов.
    Используй при переключении между провайдерами.
    """
    global _TRANSLATION_CACHE
    _TRANSLATION_CACHE.clear()
    logger.info("✅ Translation cache cleared")


async def get_translation_stats() -> dict:
    """
    Получить статистику переводов.
    
    Returns:
        Dict с информацией о кэше и провайдерах
    """
    return {
        "translation_enabled": USE_TRANSLATION,
        "primary_provider": TRANSLATION_PROVIDER,
        "cache_size": len(_TRANSLATION_CACHE),
        "cached_prompts": list(_TRANSLATION_CACHE.keys())[:5],  # Первые 5
        "google_api_configured": bool(GOOGLE_TRANSLATE_API_KEY),
        "yandex_api_configured": bool(YANDEX_TRANSLATE_API_KEY),
        "libre_translate_configured": bool(LIBRE_TRANSLATE_URL),
    }


if __name__ == "__main__":
    # Тест
    import asyncio
    
    async def test():
        text = "Создай уникальный дизайн для этой комнаты"
        result = await translate_prompt_to_english(text)
        print(f"Original: {text}")
        print(f"Translated: {result}")
        
        stats = await get_translation_stats()
        print(f"Stats: {stats}")
    
    asyncio.run(test())
