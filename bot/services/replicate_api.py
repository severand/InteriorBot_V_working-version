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
# You're a truly amazing designer; all of Europe's bohemians are in awe of you!

CUSTOM_PROMPT_TEMPLATE = """ 
Create a completely different design for this space, unique and unmatched online.
- Create new furniture
- Create new furnishings
- Create new interior details
- Create a different ceiling
- Create clear and expressive lines
- Add accents and create a bright spot

Prohibited:
1. Carpets on the floor
2. Changing the position of doors or windows.
3. Increasing or decreasing the area of the room.
4. Demolishing walls or protruding corners.
5. Altering the geometry
5. Inventing and building new walls and windows.

""".strip()

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

# ========================================
# СТИЛИ (НЕ ТРОГАЙ - используются для подстановки)
# ========================================

STYLE_PROMPTS = {
    'modern': 'A minimalist, practical style with an emphasis on functionality and '
              'clean lines. Neutral tones (warm white, light gray, beige, taupe)'
              ' with one or two bold accent colors. Low-profile sofas with clean lines, '
              'simple coffee tables, minimalist shelving. '
              'A combination of smooth matte surfaces with glossy accents, subtle metal details '
              '(chrome, satin nickel). Simple geometric shapes, no excessive ornamentation. '
              'Soft natural light, recessed lighting, and minimalist floor lamps.'
              ' One or two abstract artworks, simple potted plants, and a clean,'
              ' clutter-free space. Overall impression: bright, spacious, cozy, and fresh.',

    'minimalist': 'An extreme, ascetic style with maximum emphasis on empty space and the absence of '
                  'visual noise. Color palette: white, light gray, soft beige, black accents only '
                  'where necessary. Very low furniture, simple, hidden storage,'
                  ' handleless cabinets, a minimum of items. Natural mineral materials, linen, '
                  'cotton, contrasting textures. Regular geometric shapes, clean lines, '
                  'semi-symmetrical compositions. Plenty of empty space, "breathing," '
                  'makes the room seem larger than it is. One or two carefully chosen '
                  'items: one painting, one plant, one sculptural lamp. '
                  'Diffused indirect lighting, natural light, soft shadows. '
                  'Overall impression: calm, uncluttered, meditative, monastic',


    'scandinavian': 'A cozy, functional style that combines the purity of Scandinavian '
                    'minimalism with warmth and comfort. White walls, light, warm parquet flooring, '
                    'soft gray and beige textiles, and muted pastel accents. '
                    'Low furniture with rounded edges, wooden legs, simple, functional shapes,'
                    ' and sofas with cozy pillows. Natural wood, cotton, linen, wool, '
                    'and ceramics are featured. Abundant natural light, sheer curtains, '
                    'and simple lamps made of wood and fabric are featured. Cozy throws, '
                    'knitted blankets, and soft pillows are added. One or two green plants '
                    'add a fresh touch. Minimalistic graphic art, simple wooden frames,'
                    ' and candles are featured. Overall impression: warm, welcoming, and calm, '
                    'evoking a Scandinavian atmosphere of comfort (hygge)',

    'industrial': ' raw, urban style with elements of industrial aesthetics,'
                  ' suitable for spacious spaces. Shades of gray, black, '
                  'warm brown wood, deep charcoal, and rust. '
                  'Exposed concrete or brickwork (natural or faux),'
                  ' rough plaster. Heavy leather furniture, wooden tables with massive legs, '
                  'chairs with metal legs. Black metal, steel, untreated wood, leather, concrete. '
                  'Exposed metal pipes, beams, and factory-style industrial lighting fixtures. '
                  'Vintage posters, old signs, industrial clocks, open shelving with exposed brick.'
                  ' Theatrical accent lighting, industrial pendant lamps. '
                  'Overall impression: dark, sophisticated, authentic, yet vibrant and cozy',


    'rustic': 'A warm, rustic style that combines natural materials with contemporary design.'
              'Warm neutrals (cream, beige, warm gray), natural brown wood tones. '
              'Exposed wooden beams on the ceiling, wood paneling, solid wooden tables and furniture.'
              ' Natural wood, stone, clay, textured plaster, and linen. '
              'Whitewashed or cream-colored walls with decorative plaster, '
              'sometimes with exposed stone on one wall. Solid, comfortable furniture, '
              'fabric sofas, wooden tables, wicker chairs. '
              'Ceramics, clay pots, dried flowers, herbs, old candles in holders, wicker baskets. '
              'Rough linen, cotton, knitted throws. Soft golden lighting, '
              'candles, a chandelier made of metal and wood. '
              'Overall impression: comfortable, cozy, like a country house, a rustic atmosphere '
              'with a modern flair',

    'japandi': 'A hybrid style combining Scandinavian minimalism with Japanese simplicity and '
               'Zen philosophy. Warm off-white (cream, sand), light oak, soft charcoal, '
               'accents in natural brown tones. Low-profile furniture, simple linear shapes, '
               'rounded corners, minimal decoration, almost "floating" furniture. '
               'Light natural wood, linen, cotton, paper (rice paper lampshades). '
               'Maximum harmony, very few objects, each with a special meaning. '
               'One or two carefully placed plants, perhaps a bonsai or a simple branch in a '
               'ceramic vase. Light wood or tatami-inspired texture on the floor. '
               'Natural light, soft paper lamps, diffused lighting. Almost no decor,'
               ' perhaps just calligraphy or minimalist art. Overall impression: calm, zen, '
               'warm, harmonious, orderly, meditative',

    'boho': 'A creative, layered style with a traveler-artist vibe. '
            'Warm earth tones (terracotta, ocher, rust) with vibrant multicolored '
            'textiles and patterns. Mixed old and new pieces, low seating, wicker '
            'rattan furniture, floor pillows. Brightly colored fabrics, ethnic patterns, '
            'kilims, macramé, layered rugs. LOTS of plants, a botanical riot, hanging plants, '
            'plants on shelves and windowsills. Books, personal items, vintage finds, '
            'ceramics, macramé, garlands, soft lighting. Soft, warm lighting, '
            'garlands or warm fairy lights, candles. Overall impression: lived-in, '
            'creative, a little messy but intentional, relaxed, artistic',

    'mediterranean': 'A sunny, refreshing style with the atmosphere of a summer seaside villa. '
                     'White or cream plastered walls, terracotta or light sand floors, '
                     'accents of deep blue, olive green, and terracotta. '
                     'Natural stone or terracotta tiles create warmth. '
                     'Natural wood, wicker furniture, fabric upholstery, and airy cushions. '
                     'Arched doorways, wooden blinds, and exposed beam ceilings. '
                     'Ceramic dishes, large ceramics, simple wooden tables, linen and cotton '
                     'fabrics, and woven rugs. Ceramic pots with olive trees, '
                     'flowering plants, and grapes. Bright, sunny, and flooded with natural '
                     'daylight. Overall impression: bright, relaxed, resort-like, '
                     'like a Mediterranean villa, cozy and welcoming',

    'midcentury': 'A retro style with simple geometric shapes that has experienced a '
                  'renaissance in popularity. Warm natural wood (teak, rosewood), '
                  'off-white walls, mustard yellow, olive, and burnt orange. '
                  'A sofa with wooden legs, a chest of drawers with tapered legs, '
                  'round or oval tables, and simple armchairs. Iconic mid-century '
                  'silhouettes, gently curved lines, and hairpin legs. '
                  'Rosewood, teak, leather, and metal (brass and copper). '
                  'Geometric patterns in rugs and pillows, 1-2 vintage lamps (star lamps, '
                  'bowling alley-style lamps), and simple abstract art. '
                  'Vintage floor lamps with shades, recessed lighting, and clean natural light. '
                  'Overall impression: clean, geometric, retro, but not outdated, '
                  'stylish, and cozy, like the 1950s and 1960s',

    'artdeco': 'A luxurious, dramatic style with geometric patterns, gold accents, '
               'and glamour. Deep emerald, deep blue, black, white, gold or brass metallic '
               'accents. Velvet, glossy lacquered surfaces, marble or marble effect, '
               'and glass. Geometric silhouettes, rounded shapes, vertical lines (carved details),'
               ' and low sofa backs. Geometric patterns, zigzags, chevrons, abstract designs,'
               ' and a large mirror in a geometric frame. A brass or crystal chandelier, '
               'brass wall sconces, dramatic lighting, warm highlights on metallic surfaces. '
               'Bold artwork, geometric sculpture, and an Art Deco clock. '
               'The overall impression: luxurious, sophisticated, dramatic, theatrical, '
               'and premium, like a vintage casino or bank from the 1930s',
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
