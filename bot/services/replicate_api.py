# https://replicate.com/google/nano-banana
# Модель google/nano-banana для генерации дизайна интерьеров

import os
import logging
import httpx
from aiogram import Bot
from config import config

logger = logging.getLogger(__name__)

MODEL_ID = "google/nano-banana"

# ========================================
# 🔧 КАСТОМНЫЙ ПРОМПТ (РЕДАКТИРУЕМЫЙ)
# ========================================
#
# ИНСТРУКЦИЯ:
# Редактируй этот промпт как хочешь!
# {room_name} и {style_description} автоматически подставляются из словарей ниже.
#
# Пример использования:
# room_name = "living room" (из ROOM_NAMES)
# style_description = "modern minimalist style..." (из STYLE_PROMPTS)
#

CUSTOM_PROMPT_TEMPLATE = """
You are a world-renowned professional interior designer.

You know all the latest trends in interior design, from basements to ducal villas. 
You create masterpieces for everyday people.

Your task is to create a simple, modern, yet practical design for the client, 
choosing the right materials for the walls, ceiling, and floor depending on the room's purpose.

You select furniture, interior design, paint colors,
 and lighting based on the chosen space and style.
 
If you are redesigning a room from a photo, you have the right to remove unnecessary furniture or
 personal items to create a true design, but do not change the layout of the room.

You detail every detail in the interior so that the client says, "WOW, 
this is exactly what I need."

Prohibited:
1. Rugs on the floor

""".strip()

# ========================================
# СТИЛИ (НЕ ТРОГАЙ - используются для подстановки)
# ========================================

STYLE_PROMPTS = {
    'modern': 'modern minimalist style with clean lines and neutral colors',
    'minimalist': 'minimalist style, simple forms, functional space, uncluttered design',
    'scandinavian': 'Scandinavian style with light wood and natural lighting',
    'industrial': 'industrial loft style with exposed brick and metal fixtures',
    'rustic': 'rustic cozy style with natural wood and warm tones',
    'japandi': 'Japandi style combining Japanese minimalism and Scandinavian design',
    'boho': 'bohemian style with colorful patterns and vintage elements',
    'mediterranean': 'Mediterranean style with terracotta and blue-white colors',
    'midcentury': 'mid-century modern style with retro organic shapes',
    'artdeco': 'Art Deco style with geometric patterns and luxurious details',
}

# ========================================
# КОМНАТЫ (НЕ ТРОГАЙ - используются для подстановки)
# ========================================

ROOM_NAMES = {
    'living_room': 'living room',
    'bedroom': 'bedroom',
    'kitchen': 'kitchen',
    'bathroom': 'bathroom',
    'office': 'office',
    'dining_room': 'dining room',
}


def get_prompt(style: str, room: str) -> str:
    """
    Формирование финального промпта с подстановкой стиля и комнаты.

    🔧 КАК ИЗМЕНИТЬ ПРОМПТ:
    1. Найди CUSTOM_PROMPT_TEMPLATE выше ↑
    2. Редактируй его как хочешь
    3. {room_name} и {style_description} подставятся автоматически!

    Args:
        style: Ключ стиля из STYLE_PROMPTS ('modern', 'scandinavian', и т.д.)
        room: Ключ комнаты из ROOM_NAMES ('living_room', 'bedroom', и т.д.)

    Returns:
        Готовый промпт для отправки в nano-banana
    """
    style_desc = STYLE_PROMPTS.get(style, 'modern minimalist style')
    room_name = ROOM_NAMES.get(room, room.replace('_', ' '))

    # Подстановка значений в кастомный промпт
    final_prompt = CUSTOM_PROMPT_TEMPLATE.format(
        room_name=room_name,
        style_description=style_desc
    )

    logger.info(f"📝 Финальный промпт:\n{final_prompt}")

    return final_prompt


async def get_telegram_file_url(photo_file_id: str, bot_token: str) -> str | None:
    """
    Получение URL файла из Telegram Bot API.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Получаем информацию о файле
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                params={"file_id": photo_file_id}
            )

            if response.status_code != 200:
                logger.error(f"❗ Не удалось получить файл: {response.text}")
                return None

            result = response.json()
            if not result.get('ok'):
                logger.error(f"❗ API ошибка: {result}")
                return None

            file_path = result['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

            logger.info(f"✅ Получен URL файла: {file_url}")
            return file_url

    except Exception as e:
        logger.error(f"❌ Ошибка при получении URL файла: {e}")
        return None


async def generate_image(photo_file_id: str, room: str, style: str, bot_token: str) -> str | None:
    """
    Генерация дизайна интерьера с помощью google/nano-banana.

    Args:
        photo_file_id: file_id фото из Telegram
        room: тип комнаты (living_room, bedroom, kitchen, office)
        style: стиль дизайна (modern, minimalist, scandinavian, и т.д.)
        bot_token: токен бота для получения файла

    Returns:
        URL сгенерированного изображения или None в случае ошибки
    """

    # Проверка наличия API токена
    if not config.REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN не настроен")
        return None

    try:
        import replicate

        # Установка API токена
        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        # Получение URL фото из Telegram
        logger.info(f"📸 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # Формирование промпта с подстановкой стиля и комнаты
        prompt = get_prompt(style, room)
        logger.info(f"🎨 Генерация: {room} → {style}")
        logger.info(f"📝 Промпт: {prompt}")

        # Вызов google/nano-banana
        logger.info(f"⏳ Запуск {MODEL_ID}...")

        output = replicate.run(
            MODEL_ID,
            input={
                "prompt": prompt,
                "image_input": [image_url]  # Используем image_input вместо image
            }
        )

        # Обработка результата
        if output:
            # google/nano-banana возвращает FileOutput объект
            # Проверяем тип результата
            result_url = None

            # Если объект имеет атрибут url (это свойство, не метод!)
            if hasattr(output, 'url'):
                result_url = output.url  # ← БЕЗ СКОБОК!
                logger.info(f"✅ Генерация успешна: {result_url}")
                return result_url

            # Если output - это уже строка
            elif isinstance(output, str):
                logger.info(f"✅ Генерация успешна: {output}")
                return output

            # Пытаемся преобразовать в строку
            else:
                result_url = str(output)
                logger.info(f"✅ Генерация успешна (str): {result_url}")
                return result_url

        logger.error("❌ Пустой результат от Replicate")
        return None

    except ImportError:
        logger.error("❌ Библиотека replicate не установлена. Установите: pip install replicate")
        return None

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации: {e}")
        return None
