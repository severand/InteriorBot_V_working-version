# ========================================
# prompts.py
# Дата создания: 2025-12-10 22:41 (UTC+3)
# Описание: Модуль текстовых промптов и шаблонов для работы с Replicate API

# ========================================

import logging
import asyncio
from services.design_styles import get_room_name, get_style_description, get_style_name
from services.translator import translate_prompt_to_english

from services.room_furniture import build_furniture_block


logger = logging.getLogger(__name__)

# ========================================
# ПРОМПТ TEMPLATE ДЛЯ СОЗДАНИЯ НОВОГО ДИЗАЙНА
# ========================================

CUSTOM_PROMPT_TEMPLATE = f"""
Professional interior redesign of {{room_name}} in {{style_name}} style. 
Transform ONLY the visual style while strictly preserving ALL architectural
 structure, dimensions, and layout.

CRITICAL - PRESERVE EXACT STRUCTURE (HIGHEST PRIORITY):
- Keep EXACT room dimensions: same length, width, and height - do NOT enlarge or shrink space
- Keep EXACT ceiling height - do NOT raise ceiling or add ceiling levels
- Keep door SIMPLE if original door is simple - do NOT add ornate carvings, do NOT change door to decorative baroque/classical style
- Preserve ALL door positions, sizes, and locations - do NOT move or resize doors
- Preserve ALL window positions, sizes, and locations - do NOT move, resize, add or remove windows
- If NO windows exist, do NOT add windows - keep walls solid
- Maintain EXACT room geometry: same wall angles, corners, and proportions
- Keep floor area IDENTICAL - same square meters as original
- Preserve ALL architectural elements: columns, niches, protruding corners exactly as shown
- Do NOT change spatial layout or floor plan
- PRESERVE EXACT FLOOR MATERIAL AND PATTERN - if original has tiles, keep tiles; if wood, keep wood; maintain same pattern and layout
- Do NOT add architectural decorative elements: no columns, no arches, no pilasters, no structural ornamentation
- Keep door in same style category (simple door stays simple, decorative stays decorative)

{{ROOM_SPECIFIC_REQUIREMENTS}}

 {{furniture_block}}

REDESIGN REQUIREMENTS (VISUAL STYLE ONLY):
- Replace existing furniture with new {{style_name}} furniture pieces scaled appropriately for THIS space size
- Change wall color, finishes, and materials to match {{style_name}} aesthetic
- Update ceiling finish and lighting fixtures suitable for EXISTING ceiling height
- Add window treatments (curtains/blinds) ONLY if windows exist in original space
- Install window sills if absent and windows exist
- Add radiator covers if radiators are visible
- Create focal point with accent elements and statement pieces appropriate for space scale
- Apply {{style_name}} color palette, materials, and decorative elements

STRICT DESIGN CONSTRAINTS:
- Scale ALL new furniture to fit ACTUAL room size - no oversized pieces
- NO floor rugs or carpets
- Ensure windows remain unblocked by furniture
- Design must be realistic and proportional to ACTUAL room dimensions
- All elements must respect the COMPACT/SPACIOUS nature of original space
- Floor material changes are FORBIDDEN - preserve original floor type and pattern

VISUAL QUALITY:
Photorealistic interior design photography, eye-level view matching 
original perspective, balanced composition, natural lighting matching 
original light sources, 8K resolution, sharp focus, realistic textures and 
materials, high-end interior design magazine quality, 
professional architectural photography style.

Your result: create a unique design, unique online,
 a practical, livable remodeling project {{room_name}} that respects 
 the original architectural and space constraints while 
 ensuring the highest quality of contemporary interior design {{style_name}}.

""".strip()

# ========================================
# ROOM-SPECIFIC ДОПОЛНЕНИЯ
# ========================================

ROOM_SPECIFIC_REQUIREMENTS = {

    'entryway': """
ENTRYWAY SPECIFIC REQUIREMENTS:
- Use high-traffic, durable flooring materials (preserve existing type but ensure durability is visible)
- Include practical storage solutions: coat hooks, shoe storage, console table with drawers
- Ensure surfaces appear easy-to-clean and resistant to outdoor dirt/moisture
- Maintain welcoming, well-lit atmosphere with adequate lighting
- Keep compact, space-efficient furniture appropriate for entryway use
""",

    'bathroom': """
BATHROOM SPECIFIC REQUIREMENTS (CRITICAL):
- PRESERVE wall tiles if they exist in original photo - maintain same tile coverage areas
- If original has tiled walls, KEEP tiled walls - only change tile style/color to match {{style_name}}
- ALL materials must appear waterproof and moisture-resistant
- Maintain existing wet zones (shower/bath area) exactly as positioned in original
- Keep existing plumbing fixture positions (sink, toilet, shower) - only update their style
- Anti-slip flooring appearance is mandatory
- Include visible moisture-resistant finishes
- Do NOT add fabric elements, wood furniture, or moisture-sensitive materials
- Ensure proper ventilation visible (exhaust fan or window)
- Ceramic, porcelain, glass, and waterproof materials only
""",


'kitchen': """
KITCHEN SPECIFIC REQUIREMENTS (CRITICAL):
- PRESERVE existing kitchen layout: if original has L-shape/U-shape/galley, maintain that exact configuration
- KEEP kitchen cabinets in same positions - only update cabinet style/color to match {{style_name}}
- PRESERVE backsplash/splashback area if it exists - maintain same coverage, only update tile/material style
- PRESERVE countertop positions - only update material/color to match {{style_name}}
- Keep all appliances (stove, hood, sink) in exact original positions - only update their style

MODERN KITCHEN DESIGN ELEMENTS (HIGH-END QUALITY):
- Use handleless/integrated handle cabinets OR sleek contemporary handles (slim metal profiles)
- Premium countertop materials: quartz, granite, or marble appearance with clean edges
- Contemporary backsplash: subway tiles, large format tiles, or stone slabs matching modern aesthetic
- Integrated/built-in appliances with flush installation (oven, microwave, dishwasher)
- Under-cabinet LED lighting visible as subtle glow
- Soft-close cabinet mechanisms suggested by clean, seamless appearance
- Contemporary fixtures: modern faucet in black/chrome/brass finish with clean lines
- Glass-front cabinets for upper storage (if space allows)
- Minimalist hardware: either handleless design OR slim, contemporary pulls
- Task lighting over work zones: pendant lights or track lighting
- Clean, uncluttered countertops with minimal visible items

MATERIAL QUALITY AND FINISH:
- High-gloss or matte lacquer cabinet finishes in contemporary colors
- Stone or quartz countertops with waterfall edges (if design allows)
- Stainless steel, black, or panel-ready appliances for integrated look
- Large format tiles or engineered wood for flooring (preserve existing material)
- Backsplash extending full height between countertop and upper cabinets
- Grout lines minimal and clean

FUNCTIONAL MODERN FEATURES:
- Maintain existing work triangle (stove-sink-fridge) configuration
- Adequate task lighting over prep areas
- Pull-out organizers suggested in lower cabinets
- Vertical storage solutions for maximizing space
- Contemporary range hood that complements cabinet style
- Touchless or modern single-lever faucets

DINING/SEATING AREA - MANDATORY INCLUSION (CRITICAL):
- REQUIRED: Include dining furniture if space permits - this is a MANDATORY element, NOT optional
- Analyze available floor space in original photo and determine appropriate seating configuration:
  
  FOR SMALL KITCHENS (compact spaces, <8m² floor area):
  - 2-4 person compact dining table OR high-top bar counter with 2-3 stools
  - Minimalist chairs matching cabinet style
  - Position along one wall to not block kitchen work zones
  
  FOR MEDIUM KITCHENS (standard spaces, 8-15m² floor area):
  - 4-6 person dining table matching {{style_name}} aesthetic
  - 4-6 contemporary chairs with clean lines
  - Position to allow comfortable circulation
  
  FOR LARGE KITCHENS (spacious layouts, >15m² floor area):
  - 6-8 person dining table OR breakfast nook with seating
  - Additional options: island with overhang seating + separate dining table
  - Multiple seating zones for flexibility
  
- Choose seating style matching {{style_name}}:
  * Modern/Contemporary: Sleek table with upholstered or wooden chairs
  * Scandinavian: Light wood table with natural finish chairs
  * Minimalist: Geometric dining set with clean lines
  * Industrial: Metal frame table with upholstered seating
  * Mediterranean: Warm wood table with woven or rattan chairs

SEATING POSITIONING RULES:
- Dining furniture MUST be visible and prominent in the final image
- Position to avoid blocking work triangle (stove-sink-fridge)
- Maintain traffic flow to/from kitchen entrance
- Ensure adequate clearance (at least 90cm) around dining table for chair movement
- If island exists: can include bar seating on kitchen side + dining table elsewhere
- If breakfast nook: incorporate into overall kitchen layout naturally

CRITICAL MUST-HAVE REQUIREMENT:
- Final image MUST include dining/seating furniture as functional kitchen component
- If seating is missing, the design is INCOMPLETE
- Dining area appearance must match overall {{style_name}} design aesthetic
- All seating must be proportional to actual room dimensions shown in original photo

FUNCTIONAL CONSTRAINTS:
- Heat-resistant and grease-resistant materials only
- Easy-to-clean surfaces throughout
- NO fabric elements on seating EXCEPT cushions on chairs/stools (if applicable)
- NO large rugs or floor carpets
- Practical, functional design with contemporary aesthetics
- Professional, high-end kitchen showroom quality
""",

'toilet': """
RESTROOM/POWDER ROOM SPECIFIC REQUIREMENTS:
- Create elegant, compact bathroom space for quick use
- PRESERVE wall tiles if they exist - maintain same tile coverage areas
- ALL materials must appear waterproof and moisture-resistant
- Minimal space requirements: typically just sink and toilet
- Keep existing plumbing fixture positions (sink, toilet) - only update their style
- Anti-slip flooring appearance is mandatory
- Contemporary fixtures with clean lines appropriate for compact space
- Excellent task lighting around mirror/sink area
- Keep surfaces uncluttered and easy-to-clean
- NO storage requirements beyond essential items
- Professional, polished appearance for guest areas
- Ceramic, porcelain, glass, and waterproof materials only
""",

    'living_room': """
LIVING ROOM SPECIFIC REQUIREMENTS:
- Design for social interaction and comfortable seating arrangements
- Include focal point (TV area, fireplace, or feature wall) if present in original
- Balance aesthetics with functionality for entertainment and relaxation
- Ensure adequate seating scaled to actual room size
- Include coffee table and side tables appropriately sized
- Maintain traffic flow paths through the space
- Lighting should support multiple activities (ambient + task lighting)
""",

    'bedroom': """
BEDROOM SPECIFIC REQUIREMENTS:
- Emphasize comfort, relaxation, and tranquil atmosphere
- Soft textiles welcome: curtains, bedding, cushions (NO floor rugs)
- Warm, cozy lighting scheme (bedside lamps, ambient lighting)
- Calm, soothing color palette appropriate for rest
- Include nightstands on both sides of bed if space allows
- Ensure bed is appropriately sized for actual room dimensions
- Consider storage solutions (wardrobe/closet) if present in original
""",

    'kids_room': """
KIDS ROOM SPECIFIC REQUIREMENTS (SAFETY CRITICAL):
- SAFETY FIRST: Furniture with rounded corners, no sharp edges visible
- Non-toxic, child-safe materials appearance
- Durable, easy-to-clean surfaces that can withstand active use
- Bright, age-appropriate colors that stimulate creativity
- Include ample storage solutions for toys, books, and clothes
- Ensure furniture is sturdy and appears stable (no tippy pieces)
- Consider growth: avoid overly juvenile themes if for older children
- Safety features visible: corner guards, secure mounting for shelves
""",

    'home_office': """
HOME OFFICE SPECIFIC REQUIREMENTS:
- Design for focus, productivity, and professional appearance
- Excellent lighting: natural light preservation + adequate task lighting over desk
- Ergonomic desk and chair appropriately sized for space
- Minimal visual distractions, professional color palette
- Include adequate storage for books/files/supplies
- Cable management solutions visible (desk grommets, cable trays)
- Consider video call background if desk faces wall
- Proper desk positioning relative to windows (avoid screen glare)
""",

    'balcony': """
BALCONY/OUTDOOR SPACE SPECIFIC REQUIREMENTS (CRITICAL):
- ALL furniture and materials must appear weather-resistant and UV-protected
- Use ONLY outdoor-rated furniture suitable for exterior use
- Outdoor textiles only: weather-resistant cushions, fade-resistant fabrics
- Flooring must be exterior-grade (composite decking, outdoor tiles, existing material)
- Include drainage considerations - avoid items that block water flow
- Consider sun/shade requirements for plants and seating
- NO indoor furniture, regular fabrics, or non-weatherproof materials
- Ensure railing/barrier preservation exactly as in original
""",

    'dining_room': """
DINING ROOM SPECIFIC REQUIREMENTS:
- Create inviting atmosphere optimized for dining and conversation
- Dining table sized appropriately for actual space (measure carefully)
- Adequate seating for realistic number of people for room size
- Lighting centered over dining table (chandelier or pendant)
- Easy-to-clean flooring for food spills (preserve existing material)
- Consider sideboard/buffet for storage if space allows
- Ensure chairs can be pulled out without hitting walls
- Maintain circulation space around table (minimum 90cm clearance)
""",


 'walk_in_closet': """ 
WALK-IN CLOSET SPECIFIC REQUIREMENTS:
- Maximize storage with custom organization systems
- Excellent zoned lighting for visibility in each area
- Include full-length mirrors for outfit viewing
- Proper ventilation to prevent odors and moisture
- Durable materials for high-use areas
- Efficient use of vertical space with shelving
- Consider hanging rods, drawers, and shoe storage
""",


'studio': """
STUDIO/OPEN PLAN APARTMENT SPECIFIC REQUIREMENTS (CRITICAL):
- Maximize functionality in compact, multi-purpose space
- Use ZONE-BASED DESIGN: clearly define sleeping, living, and kitchen areas through layout and styling
- OPEN PLAN LAYOUT: maintain unobstructed sightlines and open flow between zones
- NO physical walls or partitions - use furniture placement and color to define zones

SLEEPING ZONE:
- Bed appropriately sized for space (twin or full, not oversized)
- Minimal nightstands or integrated wall shelving
- Headboard or accent wall to define sleeping area
- Consider privacy with sheer curtains or room dividers if needed

LIVING/WORK ZONE:
- Compact sofa or seating area scaled to actual space
- Small coffee table or side table
- TV area or work desk positioned to not dominate space
- Adequate task and ambient lighting

KITCHEN ZONE:
- Kitchenette: compact, efficient layout
- PRESERVE backsplash and countertop materials
- Minimal, streamlined cabinetry to save visual space
- Modern appliances appropriately sized (compact fridge, slim range)
- Open shelving or glass-front cabinets for visual lightness

STORAGE SOLUTIONS (HIGH PRIORITY):
- Vertical storage utilizing walls and ceiling
- Built-in shelving and compact cabinetry
- Under-bed storage solutions
- Wall-mounted units and storage
- Minimize floor clutter for spacious appearance

VISUAL CONTINUITY:
- Consistent flooring throughout space (preserve existing material)
- Cohesive color palette tying zones together
- Unified lighting scheme with layered ambient + task lighting
- Minimal visual separation creates sense of larger space
- Furniture scaled to space to avoid overcrowding

LIGHTING DESIGN:
- Ambient ceiling lighting for overall space
- Task lighting for kitchen and work areas
- Accent lighting to define zones
- Minimize dark corners to maximize perceived space

CRITICAL CONSTRAINTS:
- NO floor rugs or heavy carpeting - preserve flooring material
- Furniture must be appropriately scaled for compact space
- Open sight lines and clear pathways maintained
- Multi-functional furniture where possible
- Professional, contemporary studio living aesthetic
- Clean, uncluttered appearance despite compact nature
""",
}

# ========================================
# 🎁 ПРОМПТ ДЛЯ ПРИМЕРКИ ДИЗАЙНА (SAMPLE DESIGN - TRY-ON)
# ========================================
# Описание: Полностью преобразить комнату по образцу - заменить ВСЮ мебель, декор, стиль
# Используется в: SCREEN 11 - Кнопка "🎨 Примерить дизайн"
# Вход: основное фото комнаты + образец дизайна
# Выход: новый дизайн с ПОЛНОЙ трансформацией по образцу

APPLY_STYLE_PROMPT = (
     "You are a professional interior designer. "
     "Completely transform the room in the first image "
     "to match the reference design shown in the second image. "
     "Take a sample of the walls and copy them completely onto the walls of the first image."
    
     

 )

# ========================================
# 🏠 ПРОМПТ ДЛЯ ДИЗАЙНА ФАСАДОВ (VERSION 1-STRICT - ULTRA-DETAILED)
# ========================================
# Выход: фасад с ПОЛНОЙ трансформацией по образцу + СТРОГОЕ сохранение структуры
# ПОДХОД: Аналогично APPLY_STYLE_PROMPT но для архитектуры
# ЦЕЛЕВОЙ РЕЗУЛЬТАТ: Копия образца на структуре оригинала
# Размер: ~2000+ символов (детальный, как для комнат)

APPLY_FACADE_STYLE_PROMPT = (
    "You are a professional architect and facade designer. "
    "Completely transform the house facade in the first image to match the reference design shown in the second image. "
    
    "WHAT TO CHANGE (transform everything):\n"
    "- Replace ALL facade materials (brick, stone, stucco, siding, panels, etc.) with materials from the reference\n"
    "- Replace ALL window frames, styles, and treatments to match the reference design\n"
    "- Replace ALL door designs, styles, and materials to match the reference\n"
    "- Apply the exact color scheme, textures, and material finishes from the reference facade\n"
    "- Match the architectural style (modern, classic, contemporary, traditional, etc.) from the reference\n"
    "- Recreate all decorative elements: cornices, moldings, trim, shutters, columns from the reference\n"
    "- Apply the same roof style, material, and color from the reference design\n"
    "- Match balcony railings, terraces, and external architectural features\n"
    "- Recreate landscaping elements visible on the facade (plants, lighting, etc.)\n"
    "- Apply the same lighting fixtures, house numbers, and exterior accessories\n"
    "- Match the foundation finish and base treatment from the reference\n"
    
    "WHAT TO PRESERVE (keep EXACTLY from original - DO NOT CHANGE):\n"
    "- MUST maintain the exact building dimensions - width, height, and depth\n"
    "- MUST keep the same building geometry and wall layout EXACTLY\n"
    "- MUST preserve the exact NUMBER of windows - DO NOT ADD OR REMOVE WINDOWS\n"
    "- MUST preserve the exact POSITIONS of all windows - DO NOT MOVE THEM\n"
    "- MUST preserve the exact SIZE and PROPORTIONS of each window - DO NOT RESIZE\n"
    "- MUST preserve the exact NUMBER of doors - DO NOT ADD OR REMOVE DOORS\n"
    "- MUST preserve the exact POSITIONS of all doors - DO NOT MOVE THEM\n"
    "- MUST preserve the exact SIZE of each door - DO NOT RESIZE\n"
    "- MUST maintain the overall building proportions and architectural structure - NO CHANGES ALLOWED\n"
    "- MUST NOT enlarge or decrease the building footprint or height\n"
    "- MUST NOT change the roof angle, pitch, or structural shape\n"
    "- MUST NOT remove or add walls, corners, or architectural protrusions\n"
    "- MUST NOT distort or warp the building's original geometry\n"
    "- MUST keep the exact number of floors/stories\n"
    "- MUST preserve any balconies, terraces, or bay windows in their EXACT positions\n"
    "- Adapt decorative elements scale to fit the current building size EXACTLY\n"
    
    "STRICT RULES (CRITICAL - DO NOT BREAK):\n"
    "- The building's structural geometry CANNOT be changed\n"
    "- Window and door positions, quantities, and sizes are FIXED and IMMUTABLE\n"
    "- Building dimensions and proportions are SACRED - maintain them precisely\n"
    "- Only facade materials, colors, and decorative styling can change\n"
    "- Preserve the exact aspect ratio and proportions of the original building\n"
    "- The number of architectural elements (windows, doors, floors) MUST stay the same\n"
    "- DO NOT generate half of the building or cut off parts\n"
    "- DO NOT create a completely new building - transform the existing one\n"
    
    "GOAL: Create an ultra-photorealistic architectural design for a glossy architecture magazine that will look exactly as if the reference facade style was applied to THAT SPECIFIC BUILDING, while maintaining the exact dimensions, geometry, window/door layout, and structural integrity of the original house."
)

#======================================================
# ПРЕФИКС ДЛЯ ТЕКСТОВОГО РЕДАКТОРА
#======================================================
TEXT_EDITOR_PROMPT_PREFIX = """Photorealistic edit preserving ALL existing elements in the image. 
Match the EXACT style, colors, materials, and lighting already present in this photo. 
Change ONLY what is specified in the following instruction, keep everything else identical. 
Maintain architectural structure, proportions, and perspective. 
Seamlessly blend the edit with existing design. 
High-end interior design magazine quality, 8K resolution, sharp focus, realistic textures.

Follow this instruction: """


# ========================================
# ПРОМПТ ДЛЯ ОЧИСТКИ ПРОСТРАНСТВА
# ========================================

CLEAR_SPACE_PROMPT = "Completely remove all interior details from this space."


# ========================================
# ФУНКЦИИ СБОРКИ ПРОМПТОВ
# ========================================

async def build_design_prompt(style: str, room: str, translate: bool = True) -> str:
    """
    Собирает полный промпт для дизайна на основе стиля и комнаты + переводит на английский.
    
    [2025-12-23 15:30] ОБНОВЛЕНО: Добавлен параметр translate и автоматический перевод
    
    Логика:
    - Получает описание стиля из STYLE_PROMPTS (или дефолт)
    - Получает название комнаты из ROOM_NAMES (или room.replace('_', ' '))
    - Подставляет оба параметра в CUSTOM_PROMPT_TEMPLATE
    - **НОВОЕ**: Переводит промпт на английский язык
    
    Args:
        style: код стиля (ключ из STYLE_PROMPTS)
        room: код комнаты (ключ из ROOM_NAMES)
        translate: включить ли перевод на английский (по умолчанию True)
        
    Returns:
        Готовый промпт для KIE.AI/Replicate API на английском языке (~2500+ символов)
        
    Raises:
        TypeError: если style или room не строка
        
    Пример:
        >>> prompt = await build_design_prompt('modern', 'bedroom')
        >>> print(prompt[:100])
        "You are a professional interior designer..."  # ← НА АНГЛИЙСКОМ!
    """
    try:
        style_desc = get_style_description(style)
        room_name = get_room_name(room)
        furniture_block = build_furniture_block(room, style)
        style_name = get_style_name(style)
        room_specific = ROOM_SPECIFIC_REQUIREMENTS.get(room, '')

        final_prompt = CUSTOM_PROMPT_TEMPLATE.format(
            room_name=room_name,
            furniture_block=furniture_block,  # ← НОВОЕ!
            style_description=style_desc,
            style_name = style_name,
            ROOM_SPECIFIC_REQUIREMENTS=room_specific
        )
        
        # [2025-12-23] НОВОЕ: Перевод на английский
        if translate:
            logger.info(f"🌐 Translating design prompt for {room} / {style} to English...")
            final_prompt = await translate_prompt_to_english(final_prompt)
            logger.info(f"✅ Design prompt translated successfully")
        
        return final_prompt

    except Exception as e:
        logger.error(f"❌ Ошибка при сборке дизайн-промпта: style={style}, room={room}, error={e}")
        raise


async def build_apply_style_prompt(translate: bool = True) -> str:
    """
    🎁 [2026-01-03 21:15] НОВОЕ: Собирает промпт для примерки дизайна (Try-On)
    🔧 [2026-01-03 19:37] CRITICAL FIX: Добавлено жесткое сохранение геометрии
    ✨ [2026-01-03 22:51] ENHANCED: Обновлен для максимального фотореализма
    🔧 [2026-01-03 23:04] HOTFIX: Исправлена синтаксис кортежа -> строка
    
    Описание:
    ПОЛНОСТьЮ преобразует комнату по образцу:
    - Заменяет ВСЮ мебель на мебель из образца
    - Применяет стиль, цвета, материалы из образца
    - СОХРАНЯЕТ ТОЛЬКО геометрию комнаты и расположение окон/дверей
    - Адаптирует масштаб мебели под площадь комнаты
    - Создает ультра фотореалистичный дизайн для журнального качества
    
    Используется в:
    - SCREEN 11: Кнопка "🎨 Примерить дизайн"
    - Функция: apply_style_to_room() в kie_api.py
    - Вход: [основное фото, образец фото]
    - Выход: ПОЛНАЯ трансформация комнаты по образцу с максимальным реализмом
    
    Args:
        translate: включить ли перевод на английский (по умолчанию True)
    
    Returns:
        Готовый промпт на английском языке (для KIE.AI) - ~200+ символов
    
    Пример:
        >>> prompt = await build_apply_style_prompt()
        >>> # Результат: "Create an ultra-photorealistic design..."
    """
    prompt = APPLY_STYLE_PROMPT
    
    if translate:
        logger.info(f"🌐 Translating apply-style prompt to English...")
        prompt = await translate_prompt_to_english(prompt)
        logger.info(f"✅ Apply-style prompt translated successfully")
    
    return prompt


async def build_apply_facade_style_prompt(translate: bool = True) -> str:
    """
    🏠 [2026-01-05 12:10] НОВОЕ: Собирает промпт для примерки фасада (Facade Try-On)
    🔴 [2026-01-05 14:05] EMERGENCY: Упрощен до V0 (ULTRA-MINIMAL) - не сработало
    🏗️ [2026-01-05 17:25] V1-STRICT: Полная переработка - детальный архитектурный промпт
    
    Описание:
    МАКСИМАЛЬНО ДЕТАЛЬНЫЙ архитектурный промпт для фасадов:
    - ПОЛНАЯ трансформация материалов, цветов, стилей по образцу
    - СТРОГОЕ сохранение геометрии здания, количества/позиций окон/дверей
    - Адаптирует декоративные элементы под размер здания
    - Создает ультра фотореалистичный фасад журнального качества
    
    Используется в:
    - SCREEN 17: Кнопка "🎨 Применить фасад"
    - Функция: apply_facade_style_to_house() в kie_api.py
    - Вход: [основное фото фасада, образец фасада]
    - Выход: ПОЛНАЯ трансформация фасада с СТРОГИМ сохранением структуры
    
    Args:
        translate: включить ли перевод на английский (по умолчанию True)
    
    Returns:
        Готовый промпт на английском языке (для KIE.AI) - ~2000+ символов
    
    Пример:
        >>> prompt = await build_apply_facade_style_prompt()
        >>> # Результат: "You are a professional architect..."
    """
    prompt = APPLY_FACADE_STYLE_PROMPT
    
    if translate:
        logger.info(f"🌐 Translating apply-facade-style prompt to English...")
        prompt = await translate_prompt_to_english(prompt)
        logger.info(f"✅ Apply-facade-style prompt translated successfully")
    
    return prompt


async def build_clear_space_prompt(translate: bool = True) -> str:
    """
    Возвращает промпт для очистки пространства от мебели и предметов.
    [2025-12-23 15:30] ОБНОВЛЕНО: Добавлен автоматический перевод на английский

    Используется функцией clear_space_image() из replicate_api.py
    для удаления всех объектов и оставления чистого помещения.

    Args:
        translate: включить ли перевод на английский (по умолчанию True)
        
    Returns:
        Промпт для KIE.AI/Replicate API на английском языке (строка)
    """
    prompt = CLEAR_SPACE_PROMPT
    
    if translate:
        logger.info(f"🌐 Translating clear space prompt to English...")
        prompt = await translate_prompt_to_english(prompt)
        logger.info(f"✅ Clear space prompt translated successfully")
    
    return prompt


# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (СИНХРОННЫЕ)
# ========================================

def build_design_prompt_sync(style: str, room: str) -> str:
    """
    Синхронная версия build_design_prompt БЕЗ перевода (для обратной совместимости).
    
    Используйте эту функцию если у вас нет async контекста.
    Для получения перевода используйте async build_design_prompt().
    
    Args:
        style: код стиля
        room: код комнаты
        
    Returns:
        Промпт БЕЗ перевода
    """
    try:
        style_desc = get_style_description(style)
        room_name = get_room_name(room)

        final_prompt = CUSTOM_PROMPT_TEMPLATE.format(
            room_name=room_name,
            style_description=style_desc
        )
        return final_prompt

    except Exception as e:
        logger.error(f"❌ Ошибка при сборке дизайн-промпта (sync): style={style}, room={room}, error={e}")
        raise



# Синхронная версия build_clear_space_prompt БЕЗ перевода (для обратной совместимости).
# Returns: Промпт БЕЗ перевода

def build_clear_space_prompt_sync() -> str:
    return CLEAR_SPACE_PROMPT
