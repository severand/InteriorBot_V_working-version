# ========================================
# ФАЙЛ ОБЪЕДИНЈН: 2025-12-05 14:02 (UTC+3)
# ========================================
# ОСНОВА: PyCharm (рабочая версия)
# ДОБАВЛЕНО из GitHub: функция clear_space_image() (2025-12-05)
# ========================================
# ОБНОВЛЕНО: 2025-12-10 22:43 (UTC+3)
# ИЗМЕНЕНИЕ: Вынесены ROOM_NAMES, STYLE_PROMPTS, CUSTOM_PROMPT_TEMPLATE в отдельные модули
#           Теперь используются функции из design_styles.py и prompts.py
#           Удалена функция get_prompt() - заменена на build_design_prompt()
# ========================================
# [‵2025-12-23 15:30] ОБНОВЛЕНО: интеграция с translator.py для автоматического перевода

import os
import logging
import httpx
from config import config
from services.design_styles import get_room_name, get_style_description, is_valid_room, is_valid_style
from services.prompts import build_design_prompt, build_clear_space_prompt
from services.translator import translate_prompt_to_english

logger = logging.getLogger(__name__)

# ========================================
# ПЕРЕКЛЮЧАТЕЛЬ МЕЖДУ ВЕРСИЯМИ
# ========================================
# False  -> обычная nano-banana
# True   -> nano-banana-pro
USE_NANO_BANANA_PRO = False  # ← Ставь True/False для переключения

# ========================================
# МОДЕЛИ
# ========================================

MODEL_ID = "google/nano-banana"
MODEL_ID_PRO = "google/nano-banana-pro"

# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================

async def get_telegram_file_url(photo_file_id: str, bot_token: str) -> str | None:
    """
    Получение URL файла из Telegram Bot API.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                params={"file_id": photo_file_id}
            )

            if response.status_code != 200:
                logger.error(f"❌ Не удалось получить файл: {response.text}")
                return None

            result = response.json()
            if not result.get('ok'):
                logger.error(f"❌ API ошибка: {result}")
                return None

            file_path = result['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

            logger.info(f"✅ Получен URL файла: {file_url}")
            return file_url

    except Exception as e:
        logger.error(f"❌ Ошибка при получении URL файла: {e}")
        return None


# ========================================
# ОРИГИНАЛЬНАЯ ЛОГИКА ДЛЯ ОБЫЧНОЙ МОДЕЛИ
# ========================================

async def generate_image(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str
) -> str | None:
    """
    Генерация дизайна интерьера с помощью google/nano-banana.
    [‵2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод на английский
    """
    logger.info("=" * 70)
    logger.info("🎈 ГЕНЕРАЦИЯ ДИЗАЙНА [STANDARD via Replicate]")
    logger.info(f"   Комната: {room} → {get_room_name(room)}")
    logger.info(f"   Стиль: {style}")
    logger.info("=" * 70)

    if not is_valid_room(room):
        logger.warning(f"⚠️  Комната '{room}' не найдена в ROOM_NAMES")

    if not is_valid_style(style):
        logger.warning(f"⚠️  Стиль '{style}' не найден в STYLE_PROMPTS")

    if not config.REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN не настроен")
        return None

    try:
        import replicate

        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        logger.info("📃 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # [‵2025-12-23 15:30] ОБНОВЛЕНО: async с переводом
        prompt = await build_design_prompt(style, room, translate=True)
        logger.info(f"📄 Промпт сгенерирован и переведен (длина: {len(prompt)} символов)")
        logger.info(f"\ud83d\udc4b Начало промпта:\n{prompt[:500]}...")

        logger.info(f"⏳ Запуск {MODEL_ID}...")
        output = replicate.run(
            MODEL_ID,
            input={
                "prompt": prompt,
                "image_input": [image_url]
            }
        )

        if output:
            if hasattr(output, 'url'):
                result_url = output.url
            elif isinstance(output, str):
                result_url = output
            else:
                result_url = str(output)

            logger.info(f"✅ Генерация успешна: {result_url}")
            return result_url

        logger.error("❌ Пустой результат от Replicate")
        return None

    except ImportError:
        logger.error("❌ Библиотека replicate не установлена. Установите: pip install replicate")
        return None

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации: {e}")
        return None


# ========================================
# PRO-ВЕРСИЯ
# ========================================

async def generate_image_pro(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
    resolution: str = "1K",
    aspect_ratio: str = "1:1",
    output_format: str = "png",
    safety_filter_level: str = "block_only_high"
) -> str | None:
    """
    Генерация дизайна интерьера с помощью google/nano-banana-pro.
    [‵2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод на английский
    """
    logger.info("=" * 70)
    logger.info("🚀 ГЕНЕРАЦИЯ ДИЗАЙНА [PRO via Replicate]")
    logger.info(f"   Модель: {MODEL_ID_PRO}")
    logger.info(f"   Комната: {room} → {get_room_name(room)}")
    logger.info(f"   Стиль: {style}")
    logger.info(f"   Resolution: {resolution}")
    logger.info(f"   Aspect Ratio: {aspect_ratio}")
    logger.info(f"   Output Format: {output_format}")
    logger.info(f"   Safety Filter: {safety_filter_level}")
    logger.info("=" * 70)

    if not is_valid_room(room):
        logger.warning(f"⚠️  [PRO] Комната '{room}' не найдена в ROOM_NAMES")

    if not is_valid_style(style):
        logger.warning(f"⚠️  [PRO] Стиль '{style}' не найден в STYLE_PROMPTS")

    if not config.REPLICATE_API_TOKEN:
        logger.error("❌ [PRO] REPLICATE_API_TOKEN не настроен")
        return None

    try:
        import replicate

        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        logger.info("📃 [PRO] Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ [PRO] Не удалось получить URL фото")
            return None

        # [‵2025-12-23 15:30] ОБНОВЛЕНО: async с переводом
        prompt = await build_design_prompt(style, room, translate=True)
        logger.info(f"📄 [PRO] Промпт сгенерирован и переведен")
        logger.info(f"\ud83d\udc4b [PRO] Начало промпта:\n{prompt[:500]}...")

        logger.info(f"⏳ [PRO] Запуск {MODEL_ID_PRO}...")
        output = replicate.run(
            MODEL_ID_PRO,
            input={
                "prompt": prompt,
                "resolution": resolution,
                "image_input": [image_url],
                "aspect_ratio": aspect_ratio,
                "output_format": output_format,
                "safety_filter_level": safety_filter_level,
            }
        )

        if not output:
            logger.error("❌ [PRO] Пустой результат от Replicate PRO")
            return None

        # ИСПРАВЛЕНО: output.url - это АТРИБУТ, НЕ МЕТОД!
        try:
            result_url = output.url  # БЕЗ СКОБОК!
        except Exception as e:
            logger.error(f"❌ [PRO] Ошибка при получении output.url: {e}")
            logger.error(f"    Тип output: {type(output)}")
            return None

        logger.info(f"✅ [PRO] Генерация успешна!")
        logger.info(f"    URL: {result_url}")
        logger.info(f"    Формат: {output_format}")
        logger.info(f"    Resolution: {resolution}")

        return result_url

    except ImportError:
        logger.error("❌ [PRO] Библиотека replicate не установлена. Установите: pip install replicate")
        return None

    except Exception as e:
        logger.error(f"❌ [PRO] Ошибка при генерации: {e}")
        return None


# ========================================
# ОБЁРТКА С УЧЕТОМ ФЛАГА
# ========================================

async def generate_image_auto(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
    **pro_kwargs
) -> str | None:
    """
    Обёртка: в зависимости от флага USE_NANO_BANANA_PRO
    вызывает либо обычную, либо PRO-версию.
    """
    if USE_NANO_BANANA_PRO:
        logger.info("🔄 [AUTO] Отправляем в PRO версию nano-banana-pro")
        return await generate_image_pro(
            photo_file_id=photo_file_id,
            room=room,
            style=style,
            bot_token=bot_token,
            **pro_kwargs
        )
    else:
        logger.info("🔄 [AUTO] Отправляем в стандартную версию nano-banana")
        return await generate_image(
            photo_file_id=photo_file_id,
            room=room,
            style=style,
            bot_token=bot_token
        )


# ========================================
# ДОБАВЛЕНО ИЗ GITHUB: 2025-12-05 14:02
# Функция очистки пространства от мебели
# ОБНОВЛЕНО: 2025-12-10 - использует build_clear_space_prompt() из prompts.py
# [‵2025-12-23 15:30] ОБНОВЛЕНО: async с переводом
# ========================================

async def clear_space_image(photo_file_id: str, bot_token: str) -> str | None:
    """
    Очистка пространства от мебели и предметов.
    Использует промпт без стилей для удаления всех объектов.

    ИсТОЧНИК: GitHub версия (2025-12-05)
    АДАПТИРОВАНО: Использует nano-banana вместо FLUX
    """
    logger.info("=" * 70)
    logger.info("🧾 ОЧИСТКА ПОСТРАНСТВА [via Replicate]")
    logger.info("=" * 70)

    if not config.REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN не настроен")
        return None

    try:
        import replicate
        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        logger.info("📃 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # [‵2025-12-23 15:30] ОБНОВЛЕНО: async с переводом
        prompt = await build_clear_space_prompt(translate=True)
        logger.info(f"📄 Промпт очистки (переведен): {prompt}")

        logger.info(f"⏳ Запуск {MODEL_ID}...")

        output = replicate.run(
            MODEL_ID,
            input={
                "prompt": prompt,
                "image_input": [image_url]
            }
        )

        if output:
            if hasattr(output, 'url'):
                result_url = output.url
            elif isinstance(output, str):
                result_url = output
            else:
                result_url = str(output)

            logger.info(f"✅ Очистка успешна: {result_url}")
            return result_url

        logger.error("❌ Пустой результат от Replicate")
        return None

    except ImportError:
        logger.error("❌ Библиотека replicate не установлена. Установите: pip install replicate")
        return None

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке: {e}")
        return None


# ========================================
# ДОБАВЛЕНО: 2025-12-08 13:50
# Функция генерации с пользовательским текстовым промптом
# Используется для экстерьера (дом/участок) и "Другого помещения"
# [‵2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод пользовательского текста
# ========================================

async def generate_with_text_prompt(
    photo_file_id: str,
    user_prompt: str,
    bot_token: str,
    scene_type: str = "custom"
) -> str | None:
    """
    Генерация дизайна с пользовательским текстовым промптом.

    Используется для:
    - Экстерьера (дом, участок) - пользователь описывает желаемые изменения
    - "Другого помещения" - пользователь описывает тип помещения и стил

    Args:
        photo_file_id: ID фото из Telegram
        user_prompt: Текстовый промпт от пользователя
        bot_token: Токен бота
        scene_type: Тип сцены ("house_exterior", "plot_exterior", "other_room", "custom")

    Returns:
        URL сгенерированного изображения или None при ошибке

    СОЗДАНО: 2025-12-08 по аналогии с clear_space_image()
    [‵2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод пользовательского текста
    """
    logger.info("=" * 70)
    logger.info("✍️  ГЕНЕРАЦИЯ С ПОЛЬЗОВАТЕЛЬСКИМ ПРОМПТОМ [via Replicate]")
    logger.info(f"   Тип сцены: {scene_type}")
    logger.info(f"   Пользовательский промпт: {user_prompt[:100]}...")
    logger.info("=" * 70)

    if not config.REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN не настроен")
        return None

    try:
        import replicate
        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        logger.info("📃 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # [‵2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод пользовательского текста
        translated_prompt = await translate_prompt_to_english(user_prompt)
        final_prompt = f"Create a photorealistic - {translated_prompt}"

        logger.info(f"📄 Финальный промпт (переведен):\n{final_prompt[:500]}...")
        logger.info(f"⏳ Запуск {MODEL_ID}...")

        output = replicate.run(
            MODEL_ID,
            input={
                "prompt": final_prompt,
                "image_input": [image_url]
            }
        )

        if output:
            if hasattr(output, 'url'):
                result_url = output.url
            elif isinstance(output, str):
                result_url = output
            else:
                result_url = str(output)

            logger.info(f"✅ Генерация с текстовым промптом успешна: {result_url}")
            return result_url

        logger.error("❌ Пустой результат от Replicate")
        return None

    except ImportError:
        logger.error("❌ Библиотека replicate не установлена. Установите: pip install replicate")
        return None

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации с текстовым промптом: {e}")
        return None
