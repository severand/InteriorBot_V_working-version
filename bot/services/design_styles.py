# ========================================
# Дата создания: 2025-12-10 22:40 (UTC+3)
# Описание: Модуль стилей и названий комнат для масштабирования дизайн-функционала
# ========================================

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
               'keeping the rooms original structure and perspective unchanged. '
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

    'artdeco': 'Люксовый, драматичный стиль с геометричными узорами, золотыми акцентами и гламуром. '
               'Глубокий изумруд, глубокий синий, чёрный, белый, золотые или латунные металлические '
               'акценты. Велюр, лакированные глянцевые поверхности, мрамор или мраморный эффект, стекло. '
               'Геометричные силуэты, закруглённые формы, вертикальные линии (резные детали), '
               'низкие спинки диванов. Геометричные узоры, зигзаги, шевроны, абстрактные рисунки, '
               'большое зеркало в геометричной раме. Люстра из латуни или хрусталя, настенные латунные бра, '
               'драматичное освещение, тёплые блики на металлических поверхностях. '
               'Смелые произведения искусства, геометричная пластика, часы в стиле ар-деко. '
               'Общее впечатление: роскошное, изысканное, драматичное, театральное, премиум, '
               'как старинное казино или банк 1930х годов',

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

    'Loft':   'A loft is an industrial building (former factory, warehouse, or attic) converted into housing.'
              ' The space itself contains history. Lofts originated from the American tradition of converting '
              'actual industrial buildings into residential spaces.'
              ' WALLS: Exposed brick (natural) or concrete, often preserving the buildings '
              'original surfaces, leaving traces of its former function visible.'
              ' FLOOR: The buildings original covering (concrete, brick, wood planks), often solid wood floors.'
              ' CEILING: Exposed building structures—wooden or metal beams—display all utilities (pipes, wires, ventilation).'
              ' COLOR PALETTE: Neutral—white, gray, brown, and natural colors. Lofts allow for '
              'bright accents (unlike industrial styles), such as vintage pieces in various colors.'
              ' FURNITURE: A mix of old and new—vintage pieces, modern designer furniture, '
              'and designer finds. Furniture often serves as decor.'
               ' MATERIALS: Natural, mixed materials—wood, brick, concrete, metal, '
              'glass. Reclaimed wood is often used.'
               ' LIGHTING: Industrial light fixtures hanging on long cords, with cables often visible.'
               ' SMALL DETAILS: Lots of eclectic decor—paintings, vintage finds, art objects, '
              'and often clutter as part of the style.'
                ' OVERALL IMPRESSION: Lively, creative, like a living space in a converted industrial building.',

    
    'Organic Modern':   'Style: This is the most viral trend of 2026 – a combination of clean, modern lines with the warmth of natural materials and muted colors.'
                        'It balances the natural with the contemporary, the raw with the polished. ' 
                        'The atmosphere is calm and sophisticated, like a trendy spa hotel.'
                     'WALLS: Smooth, matte – cream, warm white, light gray, natural beige, sand. Textured surfaces made of natural materials (raw plaster, clay panels) are allowed for depth.'
                'FLOOR: Natural light wood (beech, ash, pine) with visible grain, polished concrete in light tones, natural stone.'
                'CEILING: White or natural wood, smooth, recessed soft lighting, often featuring light wooden beams.'
                'WINDOWS: Large windows with thin frames, allowing maximum natural light. Decor: Natural linen curtains in cream or sand tones, or minimal curtains.'
                 'COLOR PALETTE: Warm neutrals – cream, oak, natural beige, camel, light brown, light gray. Natural accents – muted green, sand, soft orange.'
                'FURNITURE: Modern, clean lines, made from natural materials – sofas with smooth shapes, wood and steel tables, chairs with organic contours. Often low-profile furniture, creating an airy feel.'
                'MATERIALS: Natural materials with honest textures – untreated wood, stone, concrete, leather, linen, cotton, wool, rattan.'
                'LIGHTING: Warm, soft, recessed or concealed – natural light is maximized, artificial lighting is soft and diffused.'
                'SMALL DETAILS: Plants in ceramic pots (often dry branches), natural materials prominently displayed, minimal decor, but each item has a purpose.'
                'OVERALL IMPRESSION: Premium, calm, natural, like a Scandinavian hotel room.'

}


# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================

def get_room_name(room_code: str) -> str:
    """
    Получить англоязычное название комнаты по коду.
    Args:
        room_code: код комнаты (ключ из ROOM_NAMES)
    Returns:
        Название комнаты на английском или room_code с заменой подчёркиваний
    """
    return ROOM_NAMES.get(room_code, room_code.replace('_', ' '))


def get_style_description(style_code: str) -> str:
    """
    Получить описание стиля по коду.
    Args:
        style_code: код стиля (ключ из STYLE_PROMPTS)
    Returns:
        Описание стиля или дефолтное 'modern minimalist style'
    """
    return STYLE_PROMPTS.get(style_code, 'modern minimalist style')


def is_valid_room(room_code: str) -> bool:
    """
    Проверить, существует ли комната в словаре.
    Args:
        room_code: код комнаты для проверки
    Returns:
        True если комната найдена, False иначе
    """
    return room_code in ROOM_NAMES


def is_valid_style(style_code: str) -> bool:
    """
    Проверить, существует ли стиль в словаре.
    Args:
        style_code: код стиля для проверки
    Returns:
        True если стиль найден, False иначе
    """
    return style_code in STYLE_PROMPTS