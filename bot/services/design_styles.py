# ========================================
#  design_styles.py
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
# НАЗВАНИЯ СТИЛЕЙ
# ========================================

STYLE_NAMES = {
    'modern': 'Modern',
    'minimalist': 'Minimalist',
    'scandinavian': 'Scandinavian',
    'industrial': 'Industrial',
    'rustic': 'Rustic',
    'japandi': 'Japandi',
    'boho': 'Bohemian',
    'midcentury': 'Mid-Century Modern',
    'artdeco': 'Art Deco',
    'coastal': 'Coastal',
    'organic_modern': 'Organic Modern',
    'loft': 'Loft',

    'hitech': 'Hi-Tech',
    'classic': 'Classic',
    'contemporary': 'Contemporary',
     'mediterranean': 'Mediterranean',
    'transitional': 'Transitional',



    'warm_luxury': 'Warm Luxury',
    'neo_art_deco': 'Neo Art Deco',
    'conscious_eclectics': 'Conscious Eclectics',
    'tactile_maximalism': 'Tactile Maximalism',
    'country': 'Country',
    'grunge': 'Grunge',
    'cyberpunk': 'Cyberpunk',
    'eclectic': 'Eclectic',
    'gothic': 'Gothic',
    'futurism': 'Futurism',
    'baroque': 'Baroque',
    'classicism': 'Classicism',
}
#==============================================
# Функция для получения названия стиля
# Возвращает человеко-читаемое название стиля
#================================================
def get_style_name(style_code: str) -> str:
   return STYLE_NAMES.get(style_code, style_code.replace('_', ' ').title())


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

    'artdeco':         'Art Deco style with bold geometric patterns and luxury materials. '
                  'Rich color palette: gold, black, emerald green, sapphire blue, burgundy. '
                  'Symmetrical geometric patterns and sunburst motifs. '
                  'Luxury materials: marble, brass, velvet, mirror, lacquer. '
                  'Streamlined furniture with stepped or curved forms. '
                  'Statement lighting: geometric lamps, chandeliers. '
                  'Bold graphic patterns on wallpaper, rugs, textiles. '
                   'Glamorous accessories: figurines, sculptures, decorative mirrors. '
                   'Overall impression: glamorous, luxurious, geometric, bold.',

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

    'loft':   'A loft is an industrial building (former factory, warehouse, or attic) converted into housing.'
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

    
    'organic modern':   'Style: This is the most viral trend of 2026 – a combination of clean, modern lines with the warmth of natural materials and muted colors.'
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
                'SMALL DETAILS: Plants in ceramic pots (often dry branches), natural materials prominently displayed, minimal decor, but each item has a purpose.',
                'OVERALL IMPRESSION: Premium, calm, natural, like a Scandinavian hotel room.'

    
     'warm_luxury': 'Warm luxury design combining richness with comfort and sophistication. '
                    'Warm color palette: golds, warm browns, deep burgundy, rich creams, terracotta. '
                    'Luxury materials: velvet, silk, marble, brass, leather. '
                    'Layered textures and sumptuous fabrics. '
               'Rich artwork, decorative objects, curated collections. '
               'Warm lighting with statement chandeliers and lamps. '
               'Elegant furniture with curved lines and details. '
               'Mix of antique and contemporary pieces. '
               'Overall impression: luxurious, warm, sophisticated, inviting.',



    'warm_luxury': 'A luxurious, enveloping style combining rich materials with warm, inviting tones creating an atmosphere of refined comfort. '
                   'WALLS: Warm textured plaster (taupe, caramel, warm beige), fabric wall panels, or warm-toned wallpaper with subtle patterns. '
                   'FLOOR: Rich hardwood (walnut, mahogany), plush carpets in warm tones, or warm stone (travertine, warm marble). '
                   'CEILING: Warm white or cream with decorative molding, possibly coffered ceiling, warm integrated lighting. '
                   'COLOR PALETTE: Warm neutrals (caramel, cognac, warm taupe, cream, champagne), accents of deep burgundy, forest green, warm gold. '
                   'FURNITURE: Luxurious upholstered furniture in rich fabrics, deep comfortable seating, refined wood pieces with warm finishes. '
                   'MATERIALS: Velvet, cashmere, silk, rich leather, warm woods (walnut, cherry), brass, warm metals, marble. '
                   'LIGHTING: Warm ambient lighting, brass or gold fixtures, layered lighting creating intimate glow, crystal accents. '
                   'DECOR: Luxurious textiles (throws, pillows), rich artwork, fresh flowers, decorative objects, books in leather bindings. '
                   'Overall impression: enveloping, warm, luxurious yet comfortable, refined elegance, inviting sophistication.',

    'neo_art_deco': 'A contemporary interpretation of Art Deco combining classic geometric glamour with modern sensibility and updated materials. '
                    'WALLS: Bold geometric wallpaper or paint in jewel tones, metallic accents, vertical linear elements, modern interpretation. '
                    'FLOOR: Geometric tiles in bold patterns, polished concrete with inlays, glossy stone, contemporary patterned rugs. '
                    'CEILING: Bold geometric ceiling design, modern metallic fixtures, dramatic contemporary lighting installations. '
                    'COLOR PALETTE: Deep jewel tones (emerald, sapphire, amethyst), black, white, contemporary metallics (rose gold, brushed brass, gunmetal). '
                    'FURNITURE: Geometric modern shapes inspired by Art Deco, luxurious materials, clean lines with vintage references, statement pieces. '
                    'MATERIALS: Velvet, modern metallics, glass, lacquered surfaces, marble, contemporary interpretations of classic materials. '
                    'LIGHTING: Dramatic geometric fixtures, modern takes on classic chandeliers, layered lighting, contemporary metallic finishes. '
                    'DECOR: Bold geometric art, modern sculptures, mirrors with geometric frames, contemporary luxury accessories. '
                    'Overall impression: bold, glamorous, contemporary luxury, geometric sophistication, modern interpretation of classic elegance.',

    'conscious_eclectics': 'A thoughtful, intentional eclectic style combining sustainable materials, vintage finds, and modern pieces with environmental consciousness. '
                           'WALLS: Natural plaster finishes, reclaimed wood panels, eco-friendly paint in earthy tones, mixed sustainable materials. '
                           'FLOOR: Reclaimed wood, sustainable bamboo, natural cork, vintage rugs, eco-friendly materials with character. '
                           'CEILING: Natural finishes, exposed sustainable materials, reclaimed beams, eco-conscious lighting solutions. '
                           'COLOR PALETTE: Natural earth tones (terracotta, sage, ochre, natural white), organic colors, sustainable dyes, vintage color combinations. '
                           'FURNITURE: Mix of vintage pieces, upcycled furniture, sustainable modern designs, handcrafted items, secondhand treasures. '
                           'MATERIALS: Reclaimed wood, natural fibers (organic cotton, linen, jute), recycled materials, vintage fabrics, sustainable sources. '
                           'LIGHTING: Energy-efficient fixtures, vintage lamps, handmade lighting, natural materials, sustainable solutions. '
                           'DECOR: Thrifted and vintage finds, handmade items, plants in reclaimed containers, meaningful collected objects, sustainable art. '
                           'Overall impression: intentional, sustainable, collected with purpose, environmentally conscious, thoughtfully curated personality.',

    'tactile_maximalism': 'A sensory-rich style celebrating abundance of textures, patterns, and tactile materials creating a luxurious, layered environment. '
                          'WALLS: Richly textured surfaces - velvet panels, 3D textured wallpaper, carved wood, mixed materials creating depth. '
                          'FLOOR: Layered rugs with different textures, plush carpeting, tactile materials, multiple textured layers. '
                          'CEILING: Textured finishes, fabric draping, decorative molding, layered visual and tactile interest. '
                          'COLOR PALETTE: Rich, saturated colors (deep jewel tones, warm earth tones), bold color combinations, pattern mixing. '
                          'FURNITURE: Upholstered in rich tactile fabrics (velvet, bouclé, mohair, leather), carved wood details, layered textures. '
                          'MATERIALS: Velvet, bouclé, mohair, leather, silk, wool, carved wood, brass, mixed luxurious tactile materials. '
                          'LIGHTING: Layered lighting, fixtures with textured materials, dramatic shadows creating depth, warm ambient glow. '
                          'DECOR: Abundant layered textiles (throws, pillows in mixed textures), tactile art, sculptures, abundant pattern mixing. '
                          'Overall impression: rich, abundant, sensory experience, luxurious layering, tactile indulgence, maximalist comfort.',

    'country': 'A warm, rustic style inspired by countryside living with natural materials, handcrafted details, and comfortable farmhouse charm. '
               'WALLS: Painted wood panels (white, cream, soft pastels), rustic plaster, shiplap, wallpaper with country patterns. '
               'FLOOR: Wide plank wood floors (natural or painted), terracotta tiles, natural stone, vintage rugs. '
               'CEILING: Exposed wooden beams (natural or painted white), white painted ceiling, rustic chandelier or lantern fixtures. '
               'COLOR PALETTE: Soft country colors (cream, soft blue, sage green, warm white), natural wood tones, floral accents. '
               'FURNITURE: Solid wood farmhouse furniture, painted wooden pieces, comfortable upholstered seating, vintage country finds. '
               'MATERIALS: Natural wood (pine, oak), cotton, linen, wrought iron, ceramic, terracotta, handcrafted materials. '
               'LIGHTING: Rustic chandeliers, lantern-style fixtures, ceramic table lamps, warm country-style lighting. '
               'DECOR: Floral patterns, gingham, checks, vintage country items, fresh flowers, ceramic pieces, handcrafted objects. '
               'Overall impression: warm, welcoming, rustic comfort, countryside charm, handcrafted authenticity, cozy farmhouse living.',

    'grunge': 'A raw, edgy style with distressed materials, dark moody colors, and deliberately unfinished aesthetic inspired by urban decay. '
              'WALLS: Exposed brick (unpainted), distressed concrete, peeling paint textures, raw unfinished surfaces, graffiti or street art. '
              'FLOOR: Worn concrete, distressed wood, industrial flooring, deliberately aged materials, raw finishes. '
              'CEILING: Exposed structures, peeling paint, raw concrete, industrial pipes and ducts visible, unfinished aesthetic. '
              'COLOR PALETTE: Dark moody tones (charcoal, deep gray, black, rust, dark brown), muted colors, distressed finishes. '
              'FURNITURE: Distressed leather, worn metal frames, salvaged industrial pieces, deliberately aged furniture, rough textures. '
              'MATERIALS: Distressed leather, worn metal, raw concrete, aged wood, chain-link, industrial salvage, deliberately weathered materials. '
              'LIGHTING: Bare bulbs, industrial fixtures, exposed wiring, dramatic shadows, moody low lighting, vintage industrial lamps. '
              'DECOR: Street art, band posters, vintage records, musical instruments, urban decay aesthetic, raw artistic expression. '
              'Overall impression: raw, edgy, deliberately unfinished, urban decay aesthetic, rebellious attitude, authentically rough.',

    'cyberpunk': 'A futuristic dystopian style combining high-tech elements with gritty urban aesthetics, neon lighting, and dark industrial base. '
                 'WALLS: Dark surfaces (black, charcoal), metallic panels, exposed tech elements, neon accent strips, urban grid patterns. '
                 'FLOOR: Dark polished concrete, metallic tiles, reflective surfaces, industrial grating, tech-integrated flooring. '
                 'CEILING: Exposed tech infrastructure, LED strip lighting, metallic ducts, neon accents, industrial cyberpunk aesthetic. '
                 'COLOR PALETTE: Dark base (black, charcoal, gunmetal), neon accents (electric blue, hot pink, acid green, purple), metallic chrome. '
                 'FURNITURE: Industrial metal furniture, tech-integrated pieces, sleek dark materials, neon accent lighting, futuristic dystopian style. '
                 'MATERIALS: Brushed metal, chrome, dark glass, carbon fiber, synthetic materials, LED-integrated surfaces, industrial tech. '
                 'LIGHTING: Neon strips (pink, blue, purple), LED accents, dramatic colored lighting, exposed bulbs, cyberpunk glow. '
                 'DECOR: Screens and monitors, tech gadgets, urban tech art, neon signs, futuristic dystopian accessories, cables as design. '
                 'Overall impression: futuristic dystopian, high-tech meets urban grit, neon-lit darkness, cyberpunk atmosphere, tech-noir aesthetic.',

    'gothic': 'A dramatic, dark romantic style with medieval influences, ornate details, and mysterious atmosphere of Gothic architecture. '
              'WALLS: Dark dramatic colors (deep burgundy, charcoal, black), rich textured wallpaper, Gothic arched details, dark wood paneling. '
              'FLOOR: Dark hardwood, black or dark stone tiles, deep colored rugs with ornate patterns, Gothic floor designs. '
              'CEILING: Dark painted ceiling, ornate Gothic molding, arched elements, dramatic ceiling fixtures, medieval-inspired details. '
              'COLOR PALETTE: Deep dramatic colors (burgundy, deep purple, black, charcoal, dark green), metallic accents (aged brass, dark iron). '
              'FURNITURE: Dark carved wood furniture, velvet upholstery in deep colors, ornate Gothic details, throne-like seating, dramatic pieces. '
              'MATERIALS: Dark carved wood, velvet, heavy brocade, wrought iron, aged brass, dark stone, stained glass accents. '
              'LIGHTING: Wrought iron chandeliers, candelabras, dramatic pendant lights, moody atmospheric lighting, candlelight aesthetic. '
              'DECOR: Gothic arches, ornate mirrors, dramatic artwork, candles, medieval-inspired objects, religious iconography, dark romantic elements. '
              'Overall impression: dark, dramatic, romantic mystery, Gothic grandeur, medieval atmosphere, theatrical elegance, moody sophistication.',

    'futurism': 'A bold forward-thinking style with dynamic forms, innovative materials, and celebration of technology and movement. '
                'WALLS: Smooth flowing surfaces, innovative materials, dynamic shapes, white or metallic finishes, futuristic curves. '
                'FLOOR: Seamless flowing flooring, innovative materials, metallic finishes, integrated lighting, futuristic surfaces. '
                'CEILING: Dynamic shapes, flowing forms, integrated LED systems, innovative ceiling design, futuristic architecture. '
                'COLOR PALETTE: White, metallic silver, chrome, occasional bold accent colors (electric blue, bright orange), high-tech palette. '
                'FURNITURE: Dynamic curved forms, innovative shapes, space-age materials, flowing lines, sculptural futuristic pieces. '
                 'MATERIALS: Chrome, brushed aluminum, acrylic, carbon fiber, innovative synthetics, glass, LED-integrated materials. '
                'LIGHTING: Integrated LED systems, dynamic lighting, futuristic fixtures, color-changing technology, innovative lighting solutions. '
                'DECOR: Abstract futuristic art, sculptural objects, tech displays, innovative materials as decoration, forward-thinking design. '
                'Overall impression: innovative, forward-thinking, dynamic movement, space-age aesthetic, technological optimism, futuristic vision.',

    'baroque': 'An opulent, dramatic style with elaborate ornamentation, rich materials, and theatrical grandeur inspired by 17th-century European palaces. '
               'WALLS: Rich dramatic colors or gilded surfaces, ornate molding and trim, detailed carved panels, luxurious wallpaper, frescoed ceilings. '
               'FLOOR: Marble with ornate patterns, inlaid wood parquet in elaborate designs, rich carpets with baroque patterns. '
               'CEILING: Ornately decorated with molding, frescoes or painted details, gilded accents, elaborate ceiling medallions, theatrical grandeur. '
               'COLOR PALETTE: Rich jewel tones (deep red, royal blue, emerald green, purple), gold gilding, ivory, dramatic contrasts. '
               'FURNITURE: Heavily ornate carved wood, gilded details, luxurious upholstery in rich fabrics, curved legs, elaborate baroque forms. '
               'MATERIALS: Carved and gilded wood, marble, velvet, silk, brocade, gold leaf, ornate metals, luxurious baroque materials. '
               'LIGHTING: Crystal chandeliers, ornate candelabras, gilded sconces, theatrical dramatic lighting, baroque grandeur. '
               'DECOR: Ornate gilded mirrors, elaborate artwork in heavy frames, sculptures, fresh flowers in ornate vases, theatrical baroque accessories. '
               'Overall impression: opulent, theatrical, dramatic grandeur, palace-like luxury, elaborate ornamentation, baroque magnificence.',

    'classicism': 'A refined, harmonious style inspired by ancient Greek and Roman architecture with symmetry, proportion, and timeless elegance. '
                  'WALLS: Neutral elegant colors (cream, soft gray, ivory, pale blue), classical molding and columns, balanced proportions. '
                  'FLOOR: Marble or marble-look tiles, herringbone wood parquet, neutral stone, classical symmetrical patterns. '
                  'CEILING: White with classical molding, coffered ceiling with symmetrical design, ceiling medallions, classical proportions. '
                  'COLOR PALETTE: Classical neutrals (cream, ivory, soft gray, white), accents of classical blue or burgundy, gold details. '
                  'FURNITURE: Symmetrical arrangements, classical proportions, refined wood pieces, upholstered seating with classical lines. '
                  'MATERIALS: Marble, fine wood (mahogany, cherry), linen, silk, plaster, classical metals (brass, bronze), quality materials. '
                  'LIGHTING: Symmetrical placement, classical chandeliers, balanced sconces, elegant proportion, classical fixtures. '
                  'DECOR: Classical sculptures or busts, symmetrical arrangements, Greek key patterns, columns or pilasters, refined classical art. '
                  'Overall impression: refined, harmonious, symmetrical elegance, timeless classical beauty, balanced proportions, enduring sophistication.',



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