# ========================================
# ФАЙЛ: bot/services/translator.py
# НАЗНАЧЕНИЕ: Система перевода промтов на английский
# ВЕРСИЯ: 2.0 (2025-12-23) - ARGOS TRANSLATE
# АВТОР: Project Owner
# ========================================
# НАЗНАЧЕНИЕ:
#   Переводит текстовые промпты с русского на английский
#   перед отправкой в KIE.AI и Replicate API для улучшения качества генерации
#
# РЕАЛИЗАЦИЯ:
#   - Argos Translate (локальная, offline, бесплатная)
#   - Простая проверка: если уже английский -> не переводим
#   - Кэширование результатов
#
# ИСПОЛЬЗОВАНИЕ:
#   from services.translator import translate_prompt_to_english
#   english_prompt = await translate_prompt_to_english(russian_prompt)
# ========================================

import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

# ========================================
# КОНФИГУРАЦИЯ
# ========================================

USE_TRANSLATION = os.getenv('USE_PROMPT_TRANSLATION', 'True').lower() == 'true'

# Логирование конфига
logger.info("="*70)
logger.info("🌐 PROMPT TRANSLATOR INITIALIZED (Argos Translate)")
logger.info(f"   Translation enabled: {USE_TRANSLATION}")
logger.info(f"   Provider: Argos Translate (Local, Offline, Free)")
logger.info("="*70)

# ========================================
# ИНИЦИАЛИЗАЦИЯ ARGOS TRANSLATE
# ========================================

try:
    from argostranslate import package, translate
    
    # Загружаем языковые модели при старте
    logger.info("📦 Initializing Argos Translate language models...")
    
    # Проверяем установлены ли модели
    installed_languages = package.get_installed_languages()
    ru_en_available = False
    
    for lang in installed_languages:
        if lang.code == 'ru':
            for target in lang.translations_to:
                if target.code == 'en':
                    ru_en_available = True
                    logger.info(f"✅ Russian → English model found")
                    break
    
    if not ru_en_available:
        logger.warning("⚠️  Russian → English model not installed")
        logger.warning("   Installing: python -m argostranslate install translations")
    
    ARGOS_AVAILABLE = True
    
except ImportError:
    logger.error("❌ Argos Translate not installed!")
    logger.error("   Install it: pip install argostranslate")
    ARGOS_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Error initializing Argos Translate: {e}")
    ARGOS_AVAILABLE = False


# ========================================
# КЭШИРОВАНИЕ ПЕРЕВОДОВ
# ========================================

_TRANSLATION_CACHE = {}  # {russian_text: english_text}


# ========================================
# ДЕТЕКТИРОВАНИЕ АНГЛИЙСКОГО ТЕКСТА
# ========================================

def _is_english(text: str) -> bool:
    """
    Простая проверка: является ли текст английским.
    
    Проверяет:
    1. Содержит ли текст только ASCII символы (или минимум ASCII)
    2. Не содержит кириллицу
    
    Returns:
        True если текст на английском, False если нужен перевод
    """
    # Проверяем наличие кириллицы (русские буквы)
    cyrillic_count = sum(1 for char in text if ord(char) >= 0x0400 and ord(char) <= 0x04FF)
    
    # Если более 5% текста кириллица - это русский текст
    if cyrillic_count > len(text) * 0.05:
        return False  # Это русский текст
    
    return True  # Похоже на английский


# ========================================
# ОСНОВНАЯ ФУНКЦИЯ ПЕРЕВОДА
# ========================================

async def translate_prompt_to_english(russian_text: str) -> str:
    """
    Переводит промпт с русского на английский (если нужно).
    
    Логика:
    1. Если translation отключен → возвращает исходный текст
    2. Если текст уже на английском → возвращает как есть
    3. Если текст в кэше → возвращает из кэша
    4. Если Argos не установлен → возвращает оригинальный текст
    5. Переводит с помощью Argos Translate (локально, offline)
    
    Args:
        russian_text: Текст промпта (русский или английский)
        
    Returns:
        Текст на английском (переведенный или оригинальный)
    """
    
    # Если перевод отключен
    if not USE_TRANSLATION:
        logger.debug(f"⏭️  Translation disabled, returning original text")
        return russian_text
    
    # Если текст короче 10 символов - не переводим
    if len(russian_text.strip()) < 10:
        logger.debug(f"⏭️  Text too short, returning original")
        return russian_text
    
    # Проверяем кэш
    if russian_text in _TRANSLATION_CACHE:
        logger.debug(f"✅ Translation found in cache (length={len(russian_text)})")
        return _TRANSLATION_CACHE[russian_text]
    
    # Проверяем: это уже английский текст?
    if _is_english(russian_text):
        logger.debug(f"🇬🇧 Text is already in English, returning as is")
        _TRANSLATION_CACHE[russian_text] = russian_text
        return russian_text
    
    # Если Argos не доступен
    if not ARGOS_AVAILABLE:
        logger.warning(f"⚠️  Argos Translate not available, returning original text")
        _TRANSLATION_CACHE[russian_text] = russian_text
        return russian_text
    
    logger.info("="*70)
    logger.info(f"🌐 TRANSLATING PROMPT TO ENGLISH")
    logger.info(f"   Length: {len(russian_text)} chars")
    logger.info(f"   Provider: Argos Translate (Local)")
    logger.info("-"*70)
    
    try:
        from argostranslate import translate
        
        logger.debug("🔄 Translating with Argos Translate...")
        
        # Переводим с русского на английский
        translated_text = translate.translate_text(russian_text, 'ru', 'en')
        
        if translated_text and translated_text.strip():
            logger.info(f"✅ Translation successful")
            logger.info(f"   Result length: {len(translated_text)} chars")
            
            # Кэшируем результат
            _TRANSLATION_CACHE[russian_text] = translated_text
            logger.info("="*70)
            return translated_text
        else:
            logger.warning(f"⚠️  Translation returned empty result")
            _TRANSLATION_CACHE[russian_text] = russian_text
            logger.info("="*70)
            return russian_text
    
    except Exception as e:
        logger.error(f"❌ Translation error: {e}")
        logger.warning(f"⚠️  Returning original Russian text")
        
        # Кэшируем "не переведено" чтобы не пытаться заново
        _TRANSLATION_CACHE[russian_text] = russian_text
        logger.info("="*70)
        return russian_text


# ========================================
# УТИЛИТЫ
# ========================================

def clear_translation_cache():
    """
    Очищает кэш переводов.
    Используй при необходимости сброса.
    """
    global _TRANSLATION_CACHE
    _TRANSLATION_CACHE.clear()
    logger.info("✅ Translation cache cleared")


async def get_translation_stats() -> dict:
    """
    Получить статистику переводов.
    
    Returns:
        Dict с информацией о кэше и статусе
    """
    return {
        "translation_enabled": USE_TRANSLATION,
        "provider": "Argos Translate (Local, Offline, Free)",
        "argos_available": ARGOS_AVAILABLE,
        "cache_size": len(_TRANSLATION_CACHE),
        "cached_prompts": list(_TRANSLATION_CACHE.keys())[:5],  # Первые 5
    }


if __name__ == "__main__":
    # Тест
    import asyncio
    
    async def test():
        # Тест 1: Русский текст (должен перевестись)
        text_ru = "Создай уникальный дизайн для этой комнаты с минимализмом"
        result = await translate_prompt_to_english(text_ru)
        print(f"\n✅ Test 1 - Russian text:")
        print(f"Original:  {text_ru}")
        print(f"Translated: {result}")
        
        # Тест 2: Английский текст (не должен переводиться)
        text_en = "You are a professional interior designer with expertise"
        result = await translate_prompt_to_english(text_en)
        print(f"\n✅ Test 2 - English text:")
        print(f"Original:  {text_en}")
        print(f"Result:    {result}")
        
        # Тест 3: Смешанный текст (должен перевестись)
        text_mixed = "Добавь contemporary design style в спальню с natural light"
        result = await translate_prompt_to_english(text_mixed)
        print(f"\n✅ Test 3 - Mixed text:")
        print(f"Original:  {text_mixed}")
        print(f"Translated: {result}")
        
        stats = await get_translation_stats()
        print(f"\n📊 Statistics:")
        print(f"   Provider: {stats['provider']}")
        print(f"   Argos available: {stats['argos_available']}")
        print(f"   Cache size: {stats['cache_size']}")
    
    asyncio.run(test())
