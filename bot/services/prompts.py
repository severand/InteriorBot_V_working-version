# ========================================
# Дата создания: 2025-12-10 22:41 (UTC+3)
# Описание: Модуль текстовых промптов и шаблонов для работы с Replicate API
# [2025-12-23 15:30] ОБНОВЛЕНО: Добавлена интеграция с translator.py для перевода на английский
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
# ПРОМПТ ДЛЯ ОЧИСТКИ ПРОСТРАНСТВА
# ========================================

CLEAR_SPACE_PROMPT = (
    "Completely remove all interior details from this space."
)


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
