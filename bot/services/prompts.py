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
# 🏠 ПРОМПТ ДЛЯ ДИЗАЙНА ФАСАДОВ
# ========================================
# [2026-01-05 12:10] НОВОЕ: Для функции apply_facade_style_to_house()
# Описание: Полностью преобразить фасад дома по образцу
# Используется в: SCREEN 17 - Кнопка "🎨 Применить фасад"
# Вход: основное фото фасада + образец дизайна фасада
# Выход: новый дизайн фасада с трансформацией по образцу

APPLY_FACADE_STYLE_PROMPT = (
     "You are a professional architect and exterior designer. "
     "Completely transform the house facade in the first image to match the reference facade design shown in the second image. "
     
     "WHAT TO CHANGE (transform everything):\n"
     "- Replace the facade materials, cladding, and surface finishes to match the reference\n"
     "- Transform all windows and doors to match the reference design\n"
     "- Redesign the roof style and materials to match the reference\n"
     "- Update all decorative elements, trims, and architectural details\n"
     "- Apply the exact color scheme and color palette from the reference\n"
     "- Add landscaping, plants, and outdoor elements matching the reference\n"
     "- Update the entryway, porch, and entrance area to match the reference\n"
     "- Redesign any balconies, terraces, or outdoor structures\n"
     "- Apply the same architectural style (modern, classic, cottage, etc.)\n"
     "- Recreate lighting fixtures and outdoor lighting\n"
     "- Match the overall aesthetic and mood of the reference design\n"
     
     "WHAT TO PRESERVE (keep EXACTLY from original - DO NOT CHANGE):\n"
     "- MUST maintain the exact house dimensions and footprint\n"
     "- MUST keep the same building geometry and wall layout EXACTLY\n"
     "- MUST preserve the exact positions of structural elements\n"
     "- MUST maintain the overall structure and form of the house - NO CHANGES ALLOWED\n"
     "- MUST NOT change the house's overall dimensions or proportions\n"
     "- MUST NOT remove or add structural walls or extensions\n"
     "- MUST NOT distort or warp the building's original geometry\n"
     "- Adapt all design elements to fit the current house structure EXACTLY\n"
     
     "STRICT RULES (CRITICAL - DO NOT BREAK):\n"
     "- The house's basic structure CANNOT be changed\n"
     "- Building dimensions are SACRED - maintain them precisely\n"
     "- Only facade styling, colors, and materials can change\n"
     "- Preserve the exact aspect ratio and proportions of the original facade\n"
     "- The house's footprint is FIXED and IMMUTABLE\n"
     
    "GOAL: Create an ultra-photorealistic house facade for a glossy architectural magazine that will look exactly as if the reference design was applied to THAT SPECIFIC HOUSE, while maintaining the exact dimensions, geometry and structure of the building."
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
    
    Описание:
    ПОЛНОСТьЮ преобразует фасад дома по образцу:
    - Заменяет материалы фасада, окна, двери
    - Применяет стиль архитектуры, цвета из образца
    - СОХРАНЯЕТ ТОЛЬКО геометрию дома и основную структуру
    - Адаптирует дизайн элементы под размер дома
    - Создает ультра фотореалистичный дизайн для журнального качества
    
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
        >>> # Результат: "Create an ultra-photorealistic house facade..."
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
