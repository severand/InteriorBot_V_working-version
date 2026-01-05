# ========================================
# Дата создания: 2025-12-10 22:41 (UTC+3)
# Описание: Модуль текстовых промптов и шаблонов для работы с Replicate API
# [2025-12-23 15:30] ОБНОВЛЕНО: Добавлена интеграция с translator.py для перевода на английский
# [2026-01-03 21:15] ОБНОВЛЕНО: Добавлен APPLY_STYLE_PROMPT для примерки дизайна (Sample Design)
# [2026-01-03 19:30] 🔥 КРИТИЧНО: Обновлен APPLY_STYLE_PROMPT для ПОЛНОЙ трансформации (мебель + стиль)
# [2026-01-03 19:37] 🔧 CRITICAL FIX: Добавлено жесткое сохранение геометрии и размеров комнаты
# [2026-01-03 22:51] ✨ ENHANCED: Обновлен APPLY_STYLE_PROMPT для максимального реализма
# [2026-01-03 23:04] 🔧 HOTFIX: Исправлена синтаксис кортежа APPLY_STYLE_PROMPT
# [2026-01-05 12:10] 🏠 ADD: APPLY_FACADE_STYLE_PROMPT для дизайна фасадов
# [2026-01-05 13:32] 🏗️ OPTIMIZE: Replace APPLY_FACADE_STYLE_PROMPT with V3 (MINIMAL_CLEAR)
# [2026-01-05 13:40] 🏗️ FALLBACK: Replace V3 (MINIMAL_CLEAR) with V1 (CONSTRAINT_BASED) - more detailed
# ========================================

import logging
import asyncio
from services.design_styles import get_room_name, get_style_description
from services.translator import translate_prompt_to_english

logger = logging.getLogger(__name__)

# ========================================
# ПРОМПТ TEMPLATE ДЛЯ ДИЗАЙНА
# ========================================

CUSTOM_PROMPT_TEMPLATE = """
You are a professional interior designer.
You know all the latest interior design trends.

You create practical design styles for everyday people.

Create a unique design for this room ({room_name}).

Replace all the furniture in the photo with new furniture.

- Create furniture in accordance with the chosen style.
- Create new furniture.
- Maintain the proportions of room ({room_name}).
- Maintain the length and width of room ({room_name}).
- Create a ceiling in room ({room_name}).
- Create a new wall color in room ({room_name}).
- Create clear and expressive lines in room ({room_name}).
- Hang curtains or blinds to match the style.
- If there are no window sills, create some.
- You can create a radiator cover.
- Add accents and create a bright spot in room ({room_name}).

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
# 🎁 ПРОМПТ ДЛЯ ПРИМЕРКИ ДИЗАЙНА (SAMPLE DESIGN - TRY-ON)
# ========================================
# [2026-01-03 21:15] НОВОЕ: Для функции apply_style_to_room()
# [2026-01-03 19:30] 🔥 КРИТИЧНО: Переписан для ПОЛНОЙ трансформации по образцу
# [2026-01-03 19:37] 🔧 CRITICAL FIX: Добавлено жесткое сохранение геометрии
# [2026-01-03 22:51] ✨ ENHANCED: Обновлен для максимального реализма
# [2026-01-03 23:04] 🔧 HOTFIX: Исправлена синтаксис (был кортеж, теперь строка)
# Описание: Полностью преобразить комнату по образцу - заменить ВСЮ мебель, декор, стиль
# Используется в: SCREEN 11 - Кнопка "🎨 Примерить дизайн"
# Вход: основное фото комнаты + образец дизайна
# Выход: новый дизайн с ПОЛНОЙ трансформацией по образцу

APPLY_STYLE_PROMPT = (
     "You are a professional interior designer. "
     "Completely transform the room in the first image to match the reference design shown in the second image. "
     
     "WHAT TO CHANGE (transform everything):\n"
     "- Replace ALL furniture with furniture matching the reference design\n"
     "- Replace ALL decor, accessories, and decorative elements\n"
     "- Apply the exact color scheme, materials, and textures from the reference\n"
     "- Match the lighting, atmosphere, and mood of the reference design\n"
     "- Adopt the same style aesthetic (modern, classic, minimalist, etc.) as the reference\n"
     "- Recreate wall treatments, finishes, and surface materials from the reference\n"
     "- Match flooring style and material to the reference design\n"
     "- Apply the same window treatments (curtains, blinds, etc.)\n"
     "- Recreate ceiling design and lighting fixtures from the reference\n"
     "- Include similar plants, artwork, and decorative accents\n"
     
     "WHAT TO PRESERVE (keep EXACTLY from original - DO NOT CHANGE):\n"
     "- MUST maintain the exact room dimensions and floor area\n"
     "- MUST keep the same room geometry and wall layout EXACTLY\n"
     "- MUST preserve the exact positions of doors and windows - DO NOT MOVE THEM\n"
     "- MUST maintain the overall room proportions and spatial configuration - NO CHANGES ALLOWED\n"
     "- MUST NOT enlarge or decrease the room size\n"
     "- MUST NOT change the room's height or width\n"
     "- MUST NOT remove or add walls\n"
     "- MUST NOT distort or warp the room's original geometry\n"
     "- Adapt furniture scale and placement to fit the current room size EXACTLY\n"
     
     "STRICT RULES (CRITICAL - DO NOT BREAK):\n"
     "- The room's basic structure CANNOT be changed\n"
     "- Window and door positions are FIXED and IMMUTABLE\n"
     "- Room dimensions are SACRED - maintain them precisely\n"
     "- Only furniture arrangement and styling can change\n"
     "- Preserve the exact aspect ratio and proportions of the original room\n"
     
    "GOAL: Create an ultra-photorealistic design for a glossy design magazine that will look exactly as if the reference style was applied to THAT SPECIFIC ROOM, while maintaining the exact dimensions, geometry and structure of the room."
 )

# ========================================
# 🏠 ПРОМПТ ДЛЯ ДИЗАЙНА ФАСАДОВ (VERSION 1 - CONSTRAINT-BASED)
# ========================================
# [2026-01-05 12:10] НОВОЕ: Для функции apply_facade_style_to_house()
# [2026-01-05 13:32] 🏗️ V3 (MINIMAL_CLEAR): 867 символов - НЕ СРАБОТАЛО
# [2026-01-05 13:40] 🏗️ FALLBACK: Переписан на VERSION 1 (CONSTRAINT-BASED)
# Описание: Полностью преобразить фасад дома по образцу с детальной структурой
# Используется в: SCREEN 17 - Кнопка "🎨 Применить фасад"
# Вход: основное фото фасада + образец дизайна фасада
# Выход: новый дизайн фасада с трансформацией по образцу
# ПОДХОД: Constraint-based с явной иерархией элементов и профессиональной терминологией
# ЦЕЛЕВОЙ РЕЗУЛЬТАТ: Predictable, consistent, архитектурно корректные результаты

APPLY_FACADE_STYLE_PROMPT = (
    "You are a professional architect and facade designer with expertise in architectural restoration and transformation. \n\n"
    
    "Your task: Completely transform the house facade in the first image to match the reference facade design shown in the second image. \n\n"
    
    "ARCHITECTURAL STYLE - CRITICAL:\n"
    "Identify and apply the exact architectural style from the reference image:\n"
    "- Classical: symmetrical, ornate details, carnice (карниз), plinth (цоколь), rustic finish (рустовка)\n"
    "- Modern: clean lines, minimal ornamentation, flat surfaces, contemporary materials\n"
    "- Country/Cottage: natural materials, pitched roofs, decorative shutters (ставни)\n"
    "- Eclectic: mixed styles with intentional combinations\n\n"
    
    "CANNOT CHANGE (SACRED - DO NOT MODIFY UNDER ANY CIRCUMSTANCES):\n"
    "- House structure, footprint, and overall building outline\n"
    "- Roof pitch, angle, ridge position, and slope direction\n"
    "- All window and door positions, sizes, and openings - FIXED AND IMMUTABLE\n"
    "- Building dimensions: height, width, depth - MUST PRESERVE EXACTLY\n"
    "- Building geometry and wall layout\n"
    "- Structural elements and load-bearing walls\n\n"
    
    "APPLY FROM REFERENCE - Facade Materials & Cladding (40% of visual impact):\n"
    "- Cladding type: brick, stone, plaster, concrete, wood, or combinations\n"
    "- Cladding color and tone: match exact color palette from reference\n"
    "- Surface texture: smooth, rough, grooved, textured patterns\n"
    "- Rustic finish (рустовка - grooved pattern) if present in reference - CRITICAL for classical style\n"
    "- Brick or stone pattern and bond type if applicable\n"
    "- Material transitions and accents\n\n"
    
    "APPLY FROM REFERENCE - Decorative Elements (15% of visual impact) - Critical for Style:\n"
    "- Cornice (карниз): decorative molding at roof edge - VERY IMPORTANT for character\n"
    "- Plinth (цоколь): baseboard or lower facade element at foundation\n"
    "- Window trim/molding (наличник): decorative frame around each window\n"
    "- Door trim/molding (наличник): decorative frame around each door\n"
    "- Pilasters (пилястры): vertical decorative elements if present in reference\n"
    "- Columns (колонны): round or square columns supporting elements if present\n"
    "- Ornamental details (лепнина): bas-relief, stucco work, medallions\n"
    "- Frieze bands (фризы): horizontal decorative bands\n"
    "- Belt courses (пояски): horizontal stripe patterns\n"
    "- Corner treatments (уголки): quoins or decorative corner elements\n\n"
    
    "APPLY FROM REFERENCE - Functional Elements (10% of visual impact):\n"
    "- Window frame color and material\n"
    "- Door frame color and material\n"
    "- Gutter/water drainage system (водосток): style, material, color\n"
    "- Shutters/blinds (ставни): style, color, material if present in reference\n"
    "- Door canopy (козырек): hood, overhang, or roof element above entrance\n\n"
    
    "APPLY FROM REFERENCE - Windows & Doors (30% of visual impact):\n"
    "- Window style: casement, double-hung, fixed, arched, decorative patterns\n"
    "- Window frame profile and muntins (grid pattern) if present\n"
    "- Door style: panel style, material, hardware style (if visible)\n"
    "- Entrance treatment: special architecture at main entrance\n\n"
    
    "APPLY FROM REFERENCE - Roof & Upper Elements (10% of visual impact):\n"
    "- Roofing material: tiles, shingles, slate color and pattern\n"
    "- Roof edge treatment and overhang style\n"
    "- Chimney treatment if visible in reference\n\n"
    
    "STRICT TECHNICAL RULES (CRITICAL - DO NOT BREAK):\n"
    "- Maintain exact window count and positions - DO NOT ADD OR REMOVE WINDOWS\n"
    "- Maintain exact door count and positions - DO NOT ADD OR REMOVE DOORS\n"
    "- Preserve aspect ratio of all openings\n"
    "- Scale all architectural elements proportionally to current building dimensions\n"
    "- Ensure structural logic: columns support elements above, proper weight distribution\n"
    "- Maintain building's original proportions and mass\n\n"
    
    "QUALITY REQUIREMENTS:\n"
    "- Ultra-photorealistic quality (magazine/professional photography standard)\n"
    "- Shadows and highlights follow logical light direction\n"
    "- Material textures appear natural and convincing\n"
    "- Color palette is cohesive and architecturally appropriate\n"
    "- All details are sharp and well-defined\n"
    "- Result should look like a professional architectural transformation\n\n"
    
    "GOAL: Create a transformation that looks exactly as if a professional architect applied the reference design's aesthetic, materials, and architectural language to THIS SPECIFIC HOUSE while maintaining its exact structure, dimensions, and building geometry. The result should be a photorealistic facade that could be featured in an architectural magazine."
)

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

        final_prompt = CUSTOM_PROMPT_TEMPLATE.format(
            room_name=room_name,
            style_description=style_desc
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
    🏗️ [2026-01-05 13:40] FALLBACK: Переписан на VERSION 1 (CONSTRAINT-BASED)
    
    Описание:
    ПОЛНОСТьЮ преобразует фасад дома по образцу с детальной структурой:
    - Заменяет материалы фасада, окна, двери
    - Применяет стиль архитектуры, цвета из образца
    - СОХРАНЯЕТ ТОЛЬКО геометрию дома и основную структуру
    - Адаптирует дизайн элементы под размер дома
    - Создает ультра фотореалистичный дизайн для журнального качества
    
    ПОДХОД (VERSION 1 - CONSTRAINT-BASED):
    - Явная иерархия элементов с указанием % визуального воздействия
    - Детальное описание ДО НЕ 19 элементов (было в первой версии)
    - Профессиональная терминология: руст, карниз, наличник, цоколь, лепнина, пилястра, водосток, ставни, козырек
    - Strictные правила для Nano Banana
    - Иерархия: 40% облицовка, 30% окна, 15% дверь, 15% декор
    - Четкие CANNOT CHANGE constraints
    
    Используется в:
    - SCREEN 17: Кнопка "🎨 Применить фасад"
    - Функция: apply_facade_style_to_house() в kie_api.py
    - Вход: [основное фото фасада, образец фасада]
    - Выход: ПОЛНАЯ трансформация фасада по образцу
    
    Args:
        translate: включить ли перевод на английский (по умолчанию True)
    
    Returns:
        Готовый промпт на английском языке (для KIE.AI)
    
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


def build_clear_space_prompt_sync() -> str:
    """
    Синхронная версия build_clear_space_prompt БЕЗ перевода (для обратной совместимости).
    
    Returns:
        Промпт БЕЗ перевода
    """
    return CLEAR_SPACE_PROMPT
