# https://replicate.com/google/nano-banana
# Модель google/nano-banana для генерации дизайна интерьеров

import os
import logging
import httpx
from config import config

logger = logging.getLogger(__name__)

MODEL_ID = "google/nano-banana"

# ========================================
# КОМНАТЫ
# ========================================

ROOM_NAMES = {
    'living_room': 'living room',
    'bedroom': 'bedroom',
    'kitchen': 'kitchen',
    'dining_room': 'dining room',
    'home_office': 'home office workspace',
    'bathroom_full': 'full bathroom with bathtub',
    'toilet': 'toilet room (WC)',
    'wardrobe': 'walk-in wardrobe closet',
    'nursery': 'nursery room for a baby',
    'teen_room_boy': 'teenager boy room',
    'teen_room_girl': 'teenager girl room',
    'man_cave': 'man cave den',
}

# ========================================
# ПРОМПТ TEMPLATE
# ========================================

CUSTOM_PROMPT_TEMPLATE = """
You are a professional DESIGNER and ARCHITECT – a world-renowned creator of interiors and designs.

You know all the latest trends in interior design – from a basement to a ducal villa.

You create practical, tangible design masterpieces for ordinary people.

Create a unique design for this {room_name} in this style. 
Replace all the furniture in the photo with new ones.

- Create furniture in accordance with the chosen style.
- Create new furnishings.
- Maintain the {room_name} proportions.
- Maintain the length and width of the {room_name}.
- Create a ceiling in the {room_name}.
- Create a new wall color in the {room_name}.
- Create clear and expressive lines in the {room_name}.
- Place accents and create a bright spot in the {room_name}.


You can't:
- Creating rugs on the floor in {room_name}.
- Changing the position of doors in {room_name}.
- Changing the position of windows in {room_name}.
- Enlarging or decreasing the area of the {room_name}.
- Removing walls or protruding corners.
- Changing the geometry of the {room_name}.
- Building new walls.
- Creating new windows.
- Creating new doors.
- Blocking windows with furniture.
- Redrawing an old design.


{style_description}
""".strip()



# ========================================
# СТИЛИ
# ========================================

STYLE_PROMPTS = {
    'modern': 'A minimalist, practical style with an emphasis on functionality '
              'and clean lines. Neutral tones (warm white, light gray, beige, taupe)'
              ' with one or two bold accent colors. Low-profile sofas with clean lines, '
              'simple coffee tables, minimalist shelving. A combination of smooth matte '
              'surfaces with glossy accents, subtle metal details (chrome, satin nickel). '
              'Simple geometric shapes, no excessive ornamentation. Soft natural light, '
              'recessed lighting, minimalist floor lamps. One or two abstract pieces of art, '
              'simple plantings in containers, no clutter. Overall impression: bright, spacious, '
              'cozy, fresh.',


    'minimalist': 'An extreme, ascetic style with maximum emphasis on empty space and the '
                  'absence of visual noise. Color palette: white, light gray, soft beige, '
                  'black accents only where necessary. Very low furniture, simple, '
                  'hidden storage, handleless cabinets, a minimum of items. '
                  'Natural mineral materials, linen, cotton, contrasting textures. '
                  'Regular geometric shapes, strict lines, semi-symmetrical compositions. '
                  'Plenty of empty space, "breathing," the room seems larger than it is. '
                  'One or two carefully selected items: one painting, one plant, one sculptural '
                  'lamp. Diffused indirect lighting, natural light, soft shadows. '
                  'Overall impression: calm, uncluttered, meditative, monastic.',

    'scandinavian': 'A cozy, functional style that combines the purity of Scandinavian minimalism '
                    'with warmth and comfort. White walls, light, warm parquet floors, '
                    'soft gray and beige textiles, and muted pastel accents. '
                    'Low furniture with rounded edges, wooden legs, simple, functional forms, '
                    'and sofas with cozy pillows. Natural wood, cotton, linen, wool, '
                    'and ceramics are featured. Abundant natural light, sheer curtains, '
                    'and simple lamps made of wood and fabric are featured. Cozy throws, '
                    'knitted blankets, and soft pillows are present. '
                    'One or two green plants add a touch of freshness. '
                    'Minimalistic graphic art, simple wooden frames, and candles are featured. '
                    'Overall, the space is warm, welcoming, and calm, evoking a sense of '
                    'Scandinavian comfort (hygge).',

    'industrial': 'A raw, urban style with elements of industrial aesthetics, '
                  'suitable for spacious spaces. Shades of gray, black, warm brown wood, '
                  'deep charcoal, and rust. Exposed concrete or brickwork (natural or simulated), '
                  'rough plaster. Heavy leather furniture, wooden tables with massive legs, '
                  'chairs with metal legs. Black metal, steel, untreated wood, leather, concrete.'
                  ' Exposed metal pipes, beams, industrial-style lighting fixtures. '
                  'Vintage posters, old signs, industrial clocks, open shelves with exposed brickwork.'
                  ' Theatrical lighting with accent lighting, pendant industrial lamps. '
                  'Overall impression: dark, sophisticated, authentic, yet lively and cozy.',

    'rustic': 'A warm, rustic style that combines natural materials with contemporary design. '
              'Warm neutrals (cream, beige, warm gray), natural brown wood tones. '
              'Visible wooden beams on the ceiling, wood paneling, massive wooden '
              'tables and furniture. Natural wood, stone, clay, textured plaster, linen. '
              'Whitewashed or cream walls with decorative plaster, sometimes stonework '
              'on one wall. Massive, comfortable furniture, fabric sofas, wooden tables, '
              'wicker chairs. Ceramics, clay pots, dried flowers, herbs, old candles '
              'in candlesticks, wicker baskets. Rough linen, cotton, knitted blankets. '
              'Soft golden lighting, candles, a chandelier made of metal and wood. '
              'Overall impression: comfortable, cozy, like a country house, '
              'a village atmosphere with a modern taste.',


    'japandi': 'Photorealistic Japandi style redesign of the same {room_name}, '
               'keeping the room’s original structure and perspective unchanged. '
               'Japandi = Scandinavian + Japanese minimalism. '
               'Color palette: warm off‑white, sand, light oak wood, soft charcoal accents. '
               'Low furniture, simple linear forms, rounded corners, very little decor. '
               'Natural materials: light wood, linen, cotton, paper lamps. '
               'Add 1–2 carefully placed plants, maybe a bonsai or simple branch in a ceramic vase. '
               'Floor can be light wood or tatami‑inspired texture. '
               'Overall feeling: calm, zen, warm, extremely tidy and harmonious.',


    'mediterranean': 'A sunny, refreshing style evoking the atmosphere of a summer Mediterranean seaside villa. '
                     'WALLS: White or cream rough textured plaster (stucco), sometimes with arched niches or doorways. '
                     'FLOOR: Terracotta tiles, natural stone tiles, or light sand-colored ceramic tiles. '
                     'CEILING: White plastered ceiling, possibly with exposed dark wooden beams creating contrast. '
                     'COLOR PALETTE: Dominant white and cream, accents of deep cobalt blue, turquoise, olive green, warm terracotta. '
                     'FURNITURE: Natural wood furniture (pine, oak), wicker rattan chairs, fabric upholstery in natural linen or cotton, simple wooden tables. '
                     'MATERIALS: Natural stone, terracotta clay, natural wood, linen, cotton, wrought iron. '
                     'ARCHITECTURAL DETAILS: Arched doorways or windows, wooden slatted shutters, wrought iron railings. '
                     'LIGHTING: Bright, sunny, flooded with natural daylight, simple wrought iron chandeliers or lanterns. '
                     'DECOR: Ceramic pots with olive trees or citrus plants, flowering plants (bougainvillea, geraniums), woven rugs, ceramic dishes displayed, simple linen curtains. '
                     'Overall impression: bright, relaxed, breezy, resort-like, like a Mediterranean coastal villa, cozy and welcoming.',

    'boho': 'A creative, layered eclectic style with a free-spirited traveler-artist vibe. '
            'WALLS: Warm white, cream, or textured plaster in earthy tones, possibly with woven wall hangings or tapestries. '
            'FLOOR: Natural wood, terracotta tiles, or multiple layered vintage rugs covering the floor. '
            'CEILING: White or cream, possibly with exposed natural wood beams, draped fabric or macramé hangings. '
            'COLOR PALETTE: Warm earth tones (terracotta, ocher, rust, burnt orange) with vibrant multicolored textiles and ethnic patterns. '
            'FURNITURE: Mixed old and new pieces, low seating (floor cushions, poufs), wicker rattan furniture, vintage wooden pieces, layered textiles. '
            'MATERIALS: Natural fibers (jute, rattan, macramé), colorful woven fabrics, ethnic textiles (kilims, ikat), leather, wood. '
            'PLANTS: LOTS of plants everywhere - hanging plants (pothos, string of pearls), plants on shelves, floor plants, botanical abundance. '
            'LIGHTING: Soft warm lighting, string fairy lights, Moroccan-style lanterns, candles, rattan pendant lamps. '
            'DECOR: Books stacked everywhere, personal travel finds, vintage ceramics, macramé wall hangings, woven baskets, patterned pillows, throws, dreamcatchers. '
            'Overall impression: lived-in, creative, intentionally layered, relaxed, artistic, bohemian paradise.',

    'mediterranean': 'A sunny, refreshing style evoking the atmosphere of a summer Mediterranean seaside villa. '
                     'WALLS: White or cream rough textured plaster (stucco), sometimes with arched niches or doorways. '
                     'FLOOR: Terracotta tiles, natural stone tiles, or light sand-colored ceramic tiles. '
                     'CEILING: White plastered ceiling, possibly with exposed dark wooden beams creating contrast. '
                     'COLOR PALETTE: Dominant white and cream, accents of deep cobalt blue, turquoise, olive green, warm terracotta. '
                     'FURNITURE: Natural wood furniture (pine, oak), wicker rattan chairs, fabric upholstery in natural linen or cotton, simple wooden tables. '
                     'MATERIALS: Natural stone, terracotta clay, natural wood, linen, cotton, wrought iron. '
                     'ARCHITECTURAL DETAILS: Arched doorways or windows, wooden slatted shutters, wrought iron railings. '
                     'LIGHTING: Bright, sunny, flooded with natural daylight, simple wrought iron chandeliers or lanterns. '
                     'DECOR: Ceramic pots with olive trees or citrus plants, flowering plants (bougainvillea, geraniums), woven rugs, ceramic dishes displayed, simple linen curtains. '
                     'Overall impression: bright, relaxed, breezy, resort-like, like a Mediterranean coastal villa, cozy and welcoming.',

    'midcentury': 'A retro style from the 1950s-1960s with simple geometric shapes and iconic silhouettes. '
                  'WALLS: Off-white or cream walls, sometimes with wood paneling accent wall (walnut or teak). '
                  'FLOOR: Warm medium-toned wood flooring (teak, walnut), or terrazzo tiles. '
                  'CEILING: Simple white ceiling, possibly with a statement starburst light fixture. '
                  'COLOR PALETTE: Warm natural wood (teak, rosewood, walnut), off-white walls, mustard yellow, olive green, burnt orange, teal accents. '
                  'FURNITURE: Iconic mid-century pieces - sofa with tapered wooden legs, low-profile sideboard with hairpin legs, Eames-style chairs, round or oval coffee tables, sunburst clocks. '
                  'SHAPES: Organic curved lines, tapered legs, gentle curves mixed with geometric shapes. '
                  'MATERIALS: Teak, rosewood, walnut wood, leather upholstery, metal (brass, copper), vinyl. '
                  'LIGHTING: Iconic vintage floor lamps (arc lamps, tripod lamps), starburst ceiling fixtures, Sputnik chandeliers, simple pendant lamps with colored glass shades. '
                  'DECOR: Geometric patterns in rugs and pillows (chevrons, abstract shapes), simple abstract art (Mondrian-style), vintage posters, analog clocks, indoor plants in ceramic pots. '
                  'Overall impression: clean, geometric, retro but timeless, stylish and cozy, nostalgic 1950s-1960s atmosphere.',

    'artdeco': 'IMPORTANT: Keep the room structure, doors, and windows EXACTLY as they are. Change ONLY interior design elements. '
               'A luxurious, glamorous, dramatic style with geometric patterns and Art Deco elegance from the 1920s-1930s. '
               'WALLS: Deep rich colors (emerald green, sapphire blue, deep burgundy) or black with gold/brass trim and molding. '
               'FLOOR: Black and white geometric marble tiles (checkerboard or chevron), or polished dark wood parquet in herringbone pattern. '
               'CEILING: Possibly coffered ceiling, or smooth with dramatic chandelier as focal point, gold or brass details. '
               'COLOR PALETTE: Deep jewel tones (emerald, sapphire, deep blue), black, white, gold or brass metallic accents, deep burgundy. '
               'FURNITURE: Luxurious velvet upholstered sofas and chairs, low profile backs, geometric silhouettes, rounded shapes, lacquered surfaces, mirrored furniture. '
               'MATERIALS: Rich velvet, glossy lacquered wood, marble or marble-effect surfaces, brass and gold metals, mirror glass. '
               'PATTERNS: Bold geometric patterns (zigzags, chevrons, sunbursts, fan shapes), Art Deco motifs, symmetrical designs. '
               'LIGHTING: Dramatic statement chandelier (crystal or brass), brass or gold wall sconces, theatrical lighting highlighting metallic surfaces. '
               'DECOR: Large geometric-framed mirror (sunburst or fan shape), bold geometric artwork, Art Deco sculptures, vintage bar cart, decorative clock with geometric design. '
               'REMEMBER: DO NOT change room orientation, doors, windows, or structural elements. '
               'Overall impression: luxurious, sophisticated, dramatic, theatrical, glamorous, premium 1920s-1930s elegance like a vintage luxury hotel or casino.',

    'hitech': 'A futuristic, high-technology style with sleek surfaces and innovative materials. '
              'WALLS: Smooth glossy white, light gray, or metallic silver panels, sometimes with integrated LED lighting. '
              'FLOOR: Polished concrete, glossy large-format tiles, or metallic epoxy resin. '
              'CEILING: Flat white or gray with integrated LED strip lighting, possibly multi-level with hidden lighting. '
              'COLOR PALETTE: White, light gray, metallic silver, chrome, black accents, occasional bold color (electric blue, neon green). '
              'FURNITURE: Ultra-modern streamlined furniture with glossy surfaces, transparent acrylic chairs, modular systems, ergonomic designs, built-in technology. '
              'MATERIALS: Chrome, stainless steel, glass, glossy plastic, polished concrete, carbon fiber, LED-integrated surfaces. '
              'TECHNOLOGY: Visible high-tech elements - smart screens, touch panels, LED strips, futuristic lighting controls, minimalist tech gadgets. '
              'LIGHTING: Dramatic LED strip lighting (white or RGB), spotlights, futuristic pendant lamps with metallic finishes, color-changing systems. '
              'DECOR: Minimal decor, abstract digital art on screens, geometric metal sculptures, high-tech gadgets as design elements. '
              'Overall impression: futuristic, sterile yet sophisticated, cutting-edge technology showcase, like a sci-fi spaceship or tech headquarters.',

    'classic': 'A timeless, elegant traditional style with refined details and luxurious materials. '
               'WALLS: Light neutral walls (cream, ivory, soft beige), possibly with decorative molding, wainscoting, or damask wallpaper accent. '
               'FLOOR: Parquet flooring in warm wood tones (oak, cherry), herringbone or chevron pattern, or marble tiles. '
               'CEILING: White with decorative crown molding, possibly coffered ceiling or ceiling medallion around chandelier. '
               'COLOR PALETTE: Soft neutrals (cream, ivory, beige, warm white), accents of deep burgundy, forest green, navy blue, gold details. '
               'FURNITURE: Traditional elegant furniture - tufted upholstered sofa, carved wood details, wingback chairs, antique-style cabinets, round pedestal tables. '
               'MATERIALS: Rich fabrics (velvet, silk, brocade), carved natural wood (mahogany, cherry, walnut), marble, brass, crystal. '
               'DETAILS: Ornate carved wood details, decorative molding, elegant draperies with tassels and valances, traditional patterns. '
               'LIGHTING: Crystal chandelier as centerpiece, elegant table lamps with fabric shades, brass wall sconces, warm ambient lighting. '
               'DECOR: Ornate framed mirrors, classic oil paintings, decorative vases, fresh flowers, books in leather bindings, Persian or Oriental rugs. '
               'Overall impression: elegant, sophisticated, timeless, luxurious, refined traditional European elegance.',

    'contemporary': 'A modern, current style that blends elements from various modern styles with flexibility and comfort. '
                    'WALLS: Neutral walls (white, light gray, greige), smooth finish, possibly one accent wall in bold color or texture. '
                    'FLOOR: Wide-plank wood flooring in natural or gray tones, polished concrete, or large neutral tiles. '
                    'CEILING: Simple white or gray, possibly with architectural details like exposed beams or modern molding. '
                    'COLOR PALETTE: Neutral base (white, gray, beige, greige) with bold accent colors (teal, coral, deep blue, chartreuse). '
                    'FURNITURE: Clean-lined comfortable furniture mixing materials, curved sofas, mix of wood and metal, flexible modular pieces, variety of textures. '
                    'MATERIALS: Mix of natural and man-made - wood, metal, glass, concrete, leather, velvet, linen. '
                    'STYLE MIX: Combines modern, minimalist, and traditional elements in an eclectic yet cohesive way. '
                    'LIGHTING: Variety of lighting - recessed lights, statement pendant lamps, floor lamps, natural light, mix of styles. '
                    'DECOR: Mix of styles - modern art, sculptural objects, plants, patterned textiles, personal items, curated accessories. '
                    'Overall impression: current, sophisticated, comfortable, livable, curated but not overly designed, flexible modern living.',

    'eclectic': 'A bold, personalized style mixing different periods, styles, and cultures in a cohesive and intentional way. '
                'WALLS: Varied - could be neutral base with colorful accent wall, gallery wall mixing styles, or bold wallpaper mixed with plain walls. '
                'FLOOR: Mix of flooring materials or layered rugs from different cultures (Persian, Moroccan, tribal), warm wood or neutral base. '
                'CEILING: Simple or with one statement element (chandelier, coffered detail, or painted accent). '
                'COLOR PALETTE: Bold and varied - rich jewel tones, warm earth tones, unexpected color combinations, pattern mixing. '
                'FURNITURE: Intentional mix of periods and styles - vintage armchair with modern sofa, antique table with contemporary chairs, global finds. '
                'MATERIALS: Diverse mix - wood, metal, glass, leather, velvet, natural fibers, carved details, smooth surfaces. '
                'PATTERNS: Confident pattern mixing - florals with geometrics, stripes with ethnic prints, textured fabrics with smooth surfaces. '
                'LIGHTING: Mix of lighting styles - vintage chandelier with modern floor lamp, various periods and styles working together. '
                'DECOR: Curated collection from travels and different periods - artwork from various eras, global textiles, vintage finds, modern sculptures, books, plants. '
                'Overall impression: confident, collected over time, personalized, sophisticated pattern and style mixing, worldly and well-traveled.',

    'transitional': 'A balanced style bridging traditional elegance with contemporary simplicity, combining the best of both worlds. '
                    'WALLS: Neutral sophisticated colors (soft gray, warm beige, greige, ivory), smooth finish with subtle texture. '
                    'FLOOR: Medium to dark wood flooring, neutral stone, or plush neutral carpet. '
                    'CEILING: White with simple crown molding, clean lines, possibly one traditional element like ceiling medallion. '
                    'COLOR PALETTE: Neutral sophisticated palette (grays, beiges, creams, warm whites) with subtle accent colors (soft blue, sage, warm taupe). '
                    'FURNITURE: Mix of traditional forms with contemporary simplicity - tufted sofa with clean lines, classic shapes in modern fabrics, streamlined traditional pieces. '
                    'MATERIALS: Mix of traditional and modern - wood with metal accents, linen with leather, glass with natural stone, quality materials in both styles. '
                    'BALANCE: Even balance between ornate and simple - some curves with some straight lines, some pattern with solid colors, some texture with smooth surfaces. '
                    'LIGHTING: Mix of styles - traditional chandelier in modern finish (brushed nickel), contemporary table lamps with classic shades, combination of ambient and task lighting. '
                    'DECOR: Balanced decor - modern art in traditional frames, classic mirrors in contemporary spaces, mix of old and new accessories, subtle patterns, quality textiles. '
                    'Overall impression: sophisticated, balanced, timeless yet current, comfortable elegance, neither too traditional nor too modern.',

    'coastal': 'A breezy, relaxed style inspired by beach houses and seaside living with a fresh, airy atmosphere. '
               'WALLS: White or very light colors (soft blue, seafoam, sandy beige), shiplap or beadboard paneling, light and airy. '
               'FLOOR: Light weathered wood (whitewashed or natural), light tile, or white-painted floorboards. '
               'CEILING: White, possibly with exposed white-painted beams or shiplap ceiling. '
               'COLOR PALETTE: Whites and creams as base, soft coastal blues (sky blue, aqua, seafoam), sandy beiges, coral accents, driftwood grays. '
               'FURNITURE: Casual comfortable furniture in light colors, slipcovered sofas in white or blue stripes, weathered wood tables, wicker and rattan pieces. '
               'MATERIALS: Natural fibers (jute, sisal, rattan), weathered or whitewashed wood, linen, cotton, rope details, natural textures. '
               'NAUTICAL ELEMENTS: Subtle nautical touches - rope details, stripes, anchors as subtle accents (not overdone), coastal artwork. '
               'LIGHTING: Abundant natural light, sheer white curtains or woven shades, coastal-inspired fixtures (glass pendants, rope-wrapped fixtures, lantern-style lights). '
               'DECOR: Beach-inspired decor - coral and shells (tastefully displayed), driftwood, coastal artwork, striped textiles, plants in natural baskets, blue and white ceramics. '
               'Overall impression: breezy, relaxed, fresh, airy, vacation-like, casual elegance, like a sophisticated beach house.',
}

def get_prompt(style: str, room: str) -> str:
    """
    Формирование финального промпта с подстановкой стиля и комнаты.
    """
    style_desc = STYLE_PROMPTS.get(style, 'modern minimalist style')
    room_name = ROOM_NAMES.get(room, room.replace('_', ' '))

    final_prompt = CUSTOM_PROMPT_TEMPLATE.format(
        room_name=room_name,
        style_description=style_desc
    )

    return final_prompt


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
        room: тип комнаты (living_room, bedroom, kitchen, и т.д.)
        style: стиль дизайна (modern, minimalist, scandinavian, и т.д.)
        bot_token: токен бота для получения файла

    Returns:
        URL сгенерированного изображения или None в случае ошибки
    """
    # Логирование входных параметров
    logger.info("=" * 70)
    logger.info("🎨 ГЕНЕРАЦИЯ ДИЗАЙНА")
    logger.info(f"   Комната: {room} → {ROOM_NAMES.get(room, room)}")
    logger.info(f"   Стиль: {style}")
    logger.info("=" * 70)

    # Проверка валидности параметров
    if room not in ROOM_NAMES:
        logger.warning(f"⚠️ Комната '{room}' не найдена в ROOM_NAMES")
        logger.warning(f"   Доступные: {list(ROOM_NAMES.keys())}")

    if style not in STYLE_PROMPTS:
        logger.warning(f"⚠️ Стиль '{style}' не найден в STYLE_PROMPTS")
        logger.warning(f"   Доступные: {list(STYLE_PROMPTS.keys())}")

    # Проверка API токена
    if not config.REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN не настроен")
        return None

    try:
        import replicate

        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        # Получение URL фото
        logger.info("📸 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # Формирование промпта
        prompt = get_prompt(style, room)
      #  logger.info(f"📝 Промпт сформирован ({prompt} символов)")
        logger.info(f"📄 Начало промпта:\n{prompt[:1500]}...")  # ← ДОБАВИТЬ

        # Запуск генерации
        logger.info(f"⏳ Запуск {MODEL_ID}...")
        output = replicate.run(
            MODEL_ID,
            input={
                "prompt": prompt,
                "image_input": [image_url]
            }
        )

        # Обработка результата
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
