# ========================================
# ОПРЕДЕЛЕНИЕ МЕБЕЛИ ДЛЯ КОМНАТ
# ========================================
# [2026-01-06] НОВОЕ: Система минимальных наборов мебели для каждой комнаты

ROOM_FURNITURE = {
    'kitchen': [
        'kitchen stove or cooktop',
        'refrigerator',
        'kitchen sink with faucet',
        'kitchen table or island',
        'kitchen chairs (4-6 pieces)',
        'kitchen cabinets and shelves',
        'countertops',
        'microwave',
        'kitchen wall cabinets with facades up to the ceiling',
        'kitchen apron on the wall',
        'range hood or ventilation'
    ],
    'bedroom': [
        'bed with headboard and mattress',
        'two nightstands',
        'dresser or chest of drawers',
        'wardrobe or closet',
        'bedside lamps',
        'mirror'
    ],
    'living_room': [
        'sofa',
        'coffee table',
        'armchair or accent chair',
        'TV stand or media console',
        'bookshelf',
        'floor lamp or table lamps',
        'side table'
    ],
    'dining_room': [
        'dining table',
        'dining chairs (4-8 pieces)',
        'sideboard or buffet',
        'chandelier or ceiling light',
        'area rug'
    ],
    'home_office': [
        'desk with work surface',
        'office chair',
        'shelving for storage',
        'task lighting',
        'file cabinet or storage'
    ],
    'bathroom_full': [
        'bathtub with faucet',
        'bathroom sink and vanity',
        'toilet',
        'mirror',
        'storage cabinet',
        'lighting fixtures'
    ],

# туалет
    'toilet': [
        'toilet',
        'small sink',
        'mirror',
        'wide washing machine',
         'sink shelf',
         'wall cabinets',
         'radiator wall-mounted',
         'towel warmer opposite the sink',
        'towel warmer',
        'wall-mounted storage'
    ],

#Прихожая
     'entryway': [
        'Soft ottoman or ottomans',
        'Soft sofa with a backrest, if space allows',
        'Wall-mounted clothes rack',
        'Hat rack',
        'Key holder',
        'Mirror or tall full-length mirror',
        'If there s a radiator, cover it with paneling',
        'If possible, a closet',
        'Shelf for storing shoes',
         'wardrobe',
        'Shelves',
        'Drawers',
        'Shoe racks'
     ],

# гардеробная
    'wardrobe': [
        'hanging rods',
        'shelving units',
        'drawers',
        'shoe racks',
        'mirrors'
    ],
    'nursery': [
        'baby crib or bed',
        'changing table',
        'dresser',
        'soft lighting',
        'storage for toys'
    ],
    'teen_room_boy': [
        'bed',
        'desk for study',
        'gaming chair or seating',
        'shelving for interests',
        'sports or hobby storage'
    ],
    'teen_room_girl': [
        'bed',
        'vanity or desk',
        'comfortable seating',
        'wardrobe',
        'decorative shelving'
    ],
    'man_cave': [
        'entertainment system or TV',
        'comfortable seating (sofa, recliner)',
        'bar counter or small table',
        'bar stools',
        'side tables'
    ],





}

# СТИЛЬ-СПЕЦИФИЧНЫЕ ДЕТАЛИ
STYLE_FURNITURE_HINTS = {
    'loft': {
        'kitchen': 'Industrial metal finishes, stainless steel appliances, metal bar stools, exposed brick shelving',
        'bedroom': 'metal bed frame, leather accents, industrial lighting',
        'living_room': 'leather furniture, metal coffee table, industrial lighting fixtures',
        'dining_room': 'industrial metal dining table, leather chairs, exposed bulb fixtures',
        'home_office': 'metal desk, vintage industrial chair, open metal shelving',
        'bathroom_full': 'exposed brick, metal fixtures, industrial mirrors with black frames',
        'toilet': 'metal accents, industrial fixtures, concrete finishes',
        'wardrobe': 'metal rods and frames, industrial shelving, metal hangers',
        'nursery': 'soft industrial accents, metal frame crib, vintage-inspired lighting',
        'teen_room_boy': 'metal accents, industrial desk, exposed lighting, concrete elements',
        'teen_room_girl': 'industrial-chic furniture, metal shelving, string lights on metal frames',
        'man_cave': 'leather seating, metal accents, industrial bar counter, exposed brick backdrop'
    },
    'modern': {
        'kitchen': 'minimalist handle-free cabinets, quartz countertops, sleek appliances',
        'bedroom': 'low-profile platform bed, minimalist nightstands, geometric shapes',
        'living_room': 'simple lines, neutral tones, minimalist furniture, clean aesthetic',
        'dining_room': 'minimalist dining table, modern chairs with clean lines, pendant lighting',
        'home_office': 'minimalist desk with no clutter, ergonomic chair, wall-mounted storage',
        'bathroom_full': 'floating vanity, sleek fixtures, frameless mirror, minimal accessories',
        'toilet': 'wall-mounted toilet, minimalist sink, clean lines throughout',
        'wardrobe': 'handle-free cabinets, minimalist shelving, organized storage systems',
        'nursery': 'minimalist crib, simple storage, neutral color palette, modern lighting',
        'teen_room_boy': 'minimalist bed, clean desk, organized shelving, modern color scheme',
        'teen_room_girl': 'minimalist furniture, geometric patterns, simple desk setup, neutral tones',
        'man_cave': 'minimalist entertainment center, simple seating, sleek media console'
    },
    'scandinavian': {
        'kitchen': 'light wood elements, white or light gray cabinets, cozy seating, natural light',
        'bedroom': 'wooden furniture, soft textiles, warm lighting, light color palette',
        'living_room': 'light wood, natural materials, comfortable seating, hygge atmosphere',
        'dining_room': 'light wood dining table, simple chairs, warm lighting, natural fibers',
        'home_office': 'light wood desk, comfortable chair, natural materials, organized workspace',
        'bathroom_full': 'light wood vanity, simple fixtures, white tiles, natural textures',
        'toilet': 'light wood accents, simple fixtures, bright white space, minimal design',
        'wardrobe': 'light wood cabinetry, natural materials, simple handles, bright interior',
        'nursery': 'light wood crib, soft textiles, warm lighting, cozy Scandinavian feel',
        'teen_room_boy': 'light wood furniture, comfortable seating, natural tones, functional design',
        'teen_room_girl': 'light wood furniture, cozy textiles, warm colors, comfortable space',
        'man_cave': 'light wood furniture, comfortable seating, natural textiles, warm atmosphere'
    },
    'industrial': {
        'kitchen': 'exposed metal, raw concrete, metal shelving, vintage industrial fixtures',
        'bedroom': 'metal frames, concrete elements, industrial lighting, exposed materials',
        'living_room': 'metal and wood combination, concrete accents, industrial-style seating',
        'dining_room': 'raw metal dining table, industrial chairs, exposed ceiling elements',
        'home_office': 'metal desk with wood top, metal shelving, industrial task lighting',
        'bathroom_full': 'exposed metal pipes, concrete surfaces, metal mirrors, industrial fixtures',
        'toilet': 'metal fixtures, concrete walls, industrial minimalism, exposed elements',
        'wardrobe': 'metal rods and frames, exposed brick, industrial shelving, raw materials',
        'nursery': 'metal accents, soft industrial touches, vintage lighting, warm metals',
        'teen_room_boy': 'metal furniture, concrete accents, industrial lighting, raw aesthetic',
        'teen_room_girl': 'softer industrial touches, metal and wood mix, vintage-inspired elements',
        'man_cave': 'metal bar counter, industrial seating, exposed elements, concrete finishes'
    },
    'rustic': {
        'kitchen': 'wooden cabinets, open shelving, rustic farmhouse style, warm finishes',
        'bedroom': 'wooden bed frame, rustic nightstands, natural textures, warm lighting',
        'living_room': 'wooden furniture, natural stone elements, cozy rustic atmosphere',
        'dining_room': 'solid wood dining table, wooden chairs, rustic chandelier, farmhouse style',
        'home_office': 'wooden desk, rustic chair, natural materials, warm wood tones',
        'bathroom_full': 'wooden vanity, rustic mirrors, natural stone elements, warm finishes',
        'toilet': 'wooden accents, rustic fixtures, natural materials, warm atmosphere',
        'wardrobe': 'solid wood cabinetry, rustic handles, natural finishes, open shelving',
        'nursery': 'wooden crib, rustic rocking chair, natural textures, warm lighting',
        'teen_room_boy': 'wooden furniture, rustic decor, natural materials, warm tones',
        'teen_room_girl': 'wooden furniture, rustic touches, natural textiles, cozy warmth',
        'man_cave': 'wooden furniture, rustic bar, stone accents, warm farmhouse feel'
    },
    'japandi': {
        'kitchen': 'light wood, minimal hardware, clean lines, zen-inspired simplicity',
        'bedroom': 'low-profile wooden bed, tatami-inspired textures, zen minimalism',
        'living_room': 'light wood furniture, natural materials, calm zen atmosphere, empty space',
        'dining_room': 'light wood table, simple seating, zen minimalism, natural materials',
        'home_office': 'light wood desk, minimalist chair, zen workspace, organized simplicity',
        'bathroom_full': 'light wood vanity, stone elements, zen spa feeling, natural textures',
        'toilet': 'light wood accents, zen simplicity, natural materials, minimalist fixtures',
        'wardrobe': 'light wood cabinetry, minimal hardware, zen organization, natural finishes',
        'nursery': 'light wood crib, zen minimalism, soft natural colors, calm atmosphere',
        'teen_room_boy': 'light wood furniture, zen minimalism, natural tones, simple design',
        'teen_room_girl': 'light wood furniture, zen-inspired, natural colors, peaceful space',
        'man_cave': 'light wood furniture, zen minimalism, natural materials, calm seating'
    },
    'mediterranean': {
        'kitchen': 'terracotta tiles, wooden furniture, rustic charm, warm earth tones',
        'bedroom': 'natural wood, warm colors, arched elements, rustic Mediterranean feel',
        'living_room': 'terracotta accents, wooden beams, arched doorways, warm lighting',
        'dining_room': 'wooden dining table, terracotta tiles, rustic chairs, Mediterranean charm',
        'home_office': 'wooden desk, terracotta accents, arched windows, warm Mediterranean style',
        'bathroom_full': 'terracotta tiles, wooden vanity, arched mirrors, warm fixtures',
        'toilet': 'terracotta tiles, rustic fixtures, Mediterranean touches, warm finishes',
        'wardrobe': 'wooden cabinetry, terracotta accents, rustic style, Mediterranean warmth',
        'nursery': 'wooden crib, terracotta touches, Mediterranean colors, warm lighting',
        'teen_room_boy': 'wooden furniture, Mediterranean colors, terracotta accents, warm space',
        'teen_room_girl': 'wooden furniture, Mediterranean palette, warm colors, rustic elements',
        'man_cave': 'wooden furniture, terracotta accents, Mediterranean bar, warm atmosphere'
    },
    'boho': {
        'kitchen': 'colorful tiles, woven elements, eclectic decor, plant-filled corner',
        'bedroom': 'layered textiles, plants, bohemian textiles, macramé wall hangings',
        'living_room': 'lots of plants, patterned textiles, vintage pieces, bohemian layering',
        'dining_room': 'colorful textiles, woven chairs, eclectic table, plant decorations',
        'home_office': 'colorful decor, woven storage, lots of plants, eclectic artwork',
        'bathroom_full': 'colorful tiles, woven baskets, plants, bohemian mirrors',
        'toilet': 'colorful accents, woven elements, plant touches, bohemian style',
        'wardrobe': 'colorful textiles, woven baskets, eclectic organization, bohemian flair',
        'nursery': 'woven elements, macramé touches, plants, colorful textiles, bohemian feel',
        'teen_room_boy': 'colorful textiles, woven storage, plants, eclectic bohemian vibe',
        'teen_room_girl': 'lots of plants, patterned fabrics, macramé details, bohemian abundance',
        'man_cave': 'colorful textiles, vintage pieces, plants, bohemian eclectic mix'
    },
    'midcentury': {
        'kitchen': 'warm wood tones (teak, walnut), iconic handles, retro appliances, vintage lighting',
        'bedroom': 'tapered leg bed, retro nightstands, warm wood finishes, iconic designs',
        'living_room': 'Eames-style chairs, wooden furniture with tapered legs, retro aesthetic',
        'dining_room': 'wooden dining table with tapered legs, iconic chairs, starburst fixtures',
        'home_office': 'wooden desk with metal legs, mid-century chair, warm wood tones, iconic design',
        'bathroom_full': 'warm wood vanity, metal fixtures, retro mirrors, vintage tiles',
        'toilet': 'metal fixtures, retro design, warm finishes, iconic simplicity',
        'wardrobe': 'walnut cabinetry, metal handles, tapered legs, mid-century elegance',
        'nursery': 'wooden crib with tapered legs, retro lighting, warm wood finishes',
        'teen_room_boy': 'wooden furniture with tapered legs, warm tones, mid-century modern style',
        'teen_room_girl': 'retro wooden furniture, iconic handles, warm wood tones, mid-century feel',
        'man_cave': 'wooden furniture with metal accents, tapered legs, retro bar area, iconic design'
    },
    'artdeco': {
        'kitchen': 'gold or brass accents, geometric patterns, glossy surfaces, luxurious finishes',
        'bedroom': 'velvet upholstery, gold accents, geometric patterns, luxurious materials',
        'living_room': 'velvet furniture, geometric art deco shapes, brass accents, glamorous design',
        'dining_room': 'luxurious dining table, velvet chairs, brass fixtures, geometric patterns',
        'home_office': 'velvet chair, brass accents, geometric desk design, luxury materials',
        'bathroom_full': 'brass fixtures, geometric mirrors, luxurious surfaces, art deco tiles',
        'toilet': 'brass fixtures, geometric design, luxurious finishes, art deco style',
        'wardrobe': 'mirrored doors, brass accents, geometric patterns, luxurious materials',
        'nursery': 'gold accents, geometric patterns, velvet touches, art deco elegance',
        'teen_room_boy': 'geometric patterns, brass accents, luxurious touches, art deco flair',
        'teen_room_girl': 'velvet accents, gold details, geometric designs, art deco glamour',
        'man_cave': 'velvet furniture, brass bar counter, geometric art deco design, luxurious'
    },
    'hitech': {
        'kitchen': 'glossy white cabinets, smart appliances, LED lighting, futuristic finishes',
        'bedroom': 'glossy surfaces, LED lighting, minimalist tech-integrated design, sleek materials',
        'living_room': 'smart screens, LED accents, glossy furniture, futuristic color scheme',
        'dining_room': 'glossy table, modern chairs, LED lighting, futuristic minimalism',
        'home_office': 'smart desk with integrated technology, ergonomic chair, LED task lighting',
        'bathroom_full': 'glossy surfaces, smart mirrors with LED, modern fixtures, futuristic design',
        'toilet': 'smart fixtures, LED lighting, glossy surfaces, futuristic minimalism',
        'wardrobe': 'smart lighting, glossy surfaces, modern organization, tech-integrated storage',
        'nursery': 'soft LED lighting, glossy surfaces, modern crib, tech-friendly design',
        'teen_room_boy': 'smart screens, LED accents, futuristic furniture, tech integration',
        'teen_room_girl': 'LED lighting, glossy surfaces, futuristic aesthetic, tech elements',
        'man_cave': 'smart entertainment center, LED accents, futuristic seating, tech showcase'
    },
    'classic': {
        'kitchen': 'ornate cabinetry, brass hardware, traditional tiles, elegant fixtures',
        'bedroom': 'tufted upholstery, carved wooden details, ornate mirrors, elegant furnishings',
        'living_room': 'tufted sofa, carved wood details, crystal chandelier, traditional elegance',
        'dining_room': 'carved dining table, ornate chairs, crystal chandelier, traditional luxury',
        'home_office': 'carved wooden desk, leather chair, ornate details, traditional elegance',
        'bathroom_full': 'marble surfaces, brass fixtures, ornate mirrors, elegant traditional style',
        'toilet': 'brass fixtures, ornate details, elegant finishes, traditional luxury',
        'wardrobe': 'carved cabinetry, brass hardware, ornate mirrors, traditional elegance',
        'nursery': 'carved wooden crib, ornate details, elegant finishes, traditional charm',
        'teen_room_boy': 'carved wooden furniture, brass accents, traditional details, elegant style',
        'teen_room_girl': 'tufted seating, ornate mirrors, traditional elegance, refined furnishings',
        'man_cave': 'carved wooden furniture, leather seating, brass accents, classic elegance'
    },
    'contemporary': {
        'kitchen': 'sleek cabinetry, modern appliances, mixed materials, current design trends',
        'bedroom': 'clean-lined bed, mixed materials, modern accents, comfortable contemporary style',
        'living_room': 'mixed textures and materials, current design, comfortable modern aesthetic',
        'dining_room': 'modern dining table, contemporary chairs, mixed materials, current style',
        'home_office': 'contemporary desk, ergonomic chair, modern storage, current design',
        'bathroom_full': 'modern fixtures, mixed materials, contemporary mirrors, current design',
        'toilet': 'modern fixtures, contemporary finishes, current design, clean aesthetic',
        'wardrobe': 'contemporary cabinetry, mixed materials, modern organization, current style',
        'nursery': 'modern crib, contemporary colors, mixed textures, current design trends',
        'teen_room_boy': 'contemporary furniture, mixed materials, current design, modern comfort',
        'teen_room_girl': 'modern furniture, mixed textures, contemporary colors, current aesthetic',
        'man_cave': 'contemporary seating, mixed materials, modern entertainment area, current design'
    },
    'eclectic': {
        'kitchen': 'mixed styles, colorful accents, vintage and modern mix, intentional eclecticism',
        'bedroom': 'mixed period furniture, bold colors, pattern mixing, collected-over-time feel',
        'living_room': 'bold pattern mixing, vintage and modern pieces, collected global treasures',
        'dining_room': 'mixed period chairs, colorful table, eclectic decor, bold pattern mix',
        'home_office': 'mixed styles, vintage and modern, bold accents, personalized eclectic space',
        'bathroom_full': 'mixed fixtures, bold tiles, vintage and modern, eclectic personality',
        'toilet': 'bold accents, mixed styles, eclectic personality, collected elements',
        'wardrobe': 'mixed materials, bold colors, eclectic organization, personalized storage',
        'nursery': 'mixed colors, eclectic decor, bold patterns, collected treasures',
        'teen_room_boy': 'mixed styles, bold accents, eclectic personality, collected interests',
        'teen_room_girl': 'bold pattern mixing, vintage finds, eclectic color scheme, personalized',
        'man_cave': 'mixed styles, bold accents, collected treasures, eclectic personality'
    },
    'transitional': {
        'kitchen': 'balanced traditional and modern, neutral colors, mixed materials, sophisticated',
        'bedroom': 'balanced elegance and comfort, mixed materials, traditional and modern blend',
        'living_room': 'balanced styles, neutral palette, mixed textures, sophisticated comfort',
        'dining_room': 'balanced traditional and modern chairs, neutral table, sophisticated mix',
        'home_office': 'balanced traditional and modern, neutral colors, sophisticated design',
        'bathroom_full': 'balanced fixtures, neutral colors, traditional and modern blend, sophisticated',
        'toilet': 'balanced fixtures, neutral design, traditional-modern blend, sophisticated',
        'wardrobe': 'balanced styles, neutral finishes, traditional and modern mix, sophisticated',
        'nursery': 'balanced traditional and modern, neutral colors, sophisticated comfort',
        'teen_room_boy': 'balanced design, mixed materials, neutral tones, sophisticated blend',
        'teen_room_girl': 'balanced traditional and modern, neutral palette, sophisticated comfort',
        'man_cave': 'balanced styles, neutral tones, traditional and modern comfort mix'
    },
    'coastal': {
        'kitchen': 'light colors, natural materials, breezy coastal feel, weathered finishes',
        'bedroom': 'light furniture, soft coastal colors, breezy atmosphere, natural textures',
        'living_room': 'coastal colors, natural materials, light and airy, relaxed beach atmosphere',
        'dining_room': 'light wood table, coastal colors, natural materials, breezy feel',
        'home_office': 'light wood desk, coastal colors, natural materials, relaxed workspace',
        'bathroom_full': 'light colors, coastal tiles, natural materials, beach house style',
        'toilet': 'light colors, coastal accents, natural finishes, breezy atmosphere',
        'wardrobe': 'light wood cabinetry, natural materials, coastal colors, airy interior',
        'nursery': 'light colors, natural materials, coastal touches, breezy relaxed feel',
        'teen_room_boy': 'light furniture, coastal colors, natural materials, relaxed beach vibe',
        'teen_room_girl': 'light colors, coastal style, natural textures, breezy atmosphere',
        'man_cave': 'light furniture, coastal colors, natural materials, relaxed beach feel'
    },
    'organic modern': {
        'kitchen': 'natural materials, warm neutrals, clean modern lines, organic textures',
        'bedroom': 'natural wood, calm colors, organic shapes, soft modern comfort',
        'living_room': 'natural materials, warm tones, modern clean lines, organic warmth',
        'dining_room': 'natural wood table, organic shapes, warm neutrals, modern comfort',
        'home_office': 'natural wood desk, organic design, clean lines, calm workspace',
        'bathroom_full': 'natural materials, warm neutrals, organic textures, modern simplicity',
        'toilet': 'natural materials, warm finishes, organic design, modern simplicity',
        'wardrobe': 'natural wood cabinetry, organic shapes, warm tones, modern functionality',
        'nursery': 'natural materials, soft warm colors, organic shapes, calming modern feel',
        'teen_room_boy': 'natural wood, warm tones, modern lines, organic comfort and style',
        'teen_room_girl': 'natural materials, warm colors, organic shapes, calm modern space',
        'man_cave': 'natural wood furniture, warm tones, organic comfort, modern simplicity'
    },
}



def get_room_furniture(room_code: str) -> list:
    """Получить базовый список мебели для комнаты"""
    return ROOM_FURNITURE.get(room_code, [])


def get_style_furniture_hints(room_code: str, style_code: str) -> str:
    """Получить стиль-специфичные подсказки для мебели"""
    style_hints = STYLE_FURNITURE_HINTS.get(style_code, {})
    return style_hints.get(room_code, "")


def build_furniture_block(room_code: str, style_code: str) -> str:
    """Построить блок мебели для промпта"""
    base_furniture = get_room_furniture(room_code)
    style_hints = get_style_furniture_hints(room_code, style_code)

    if not base_furniture:
        return ""

    # Базовая мебель
    text = "ESSENTIAL FURNITURE AND ITEMS FOR THIS ROOM:\n"
    text += " - " + "\n - ".join(base_furniture)

    # Стиль-специфичные детали
    if style_hints:
        text += f"\n\nSTYLE-SPECIFIC DETAILS: Render furniture and elements {style_hints}"

    return text
