# 🔌 DESIGN ANALYSIS API REFERENCE

## 📁 Оглавление

1. [сервисы](#сервисы)
2. [Handlers](#handlers)
3. [Типы данных](#типы-данных)
4. [Ошибки](#ошибки)

---

## 📦 СЕРВИСЫ

### `vision_analysis.py`

#### Класс `DesignAnalyzer`

Майн класс для анализа дизайна с поддержкой нескольких Vision AI провайдеров.

```python
class DesignAnalyzer:
    def __init__(self, provider: str = 'gpt'):
        """
        Основные параметры:
        provider: 'gpt', 'claude', или 'gemini'
        """
```

#### Метод `analyze(image_url: str) -> dict`

Главные метод для анализа дизайна.

**Параметры:**
```python
image_url: str  # URL изображения
```

**Возвращает:**
```python
{
    'style': str,           # Название стиля (гч. "Скандинавский")
    'walls': {
        'color': str,       # Описание цвета
        'ral_code': str,    # RAL код (gч. "RAL 7016")
        'material': str,    # Материал отделки
        'texture': str      # Текстура
    },
    'floor': {
        'material': str,    # Материал пола
        'color': str,       # Описание цвета
        'pattern': str      # Принт / укладка
    },
    'ceiling': {
        'type': str,        # Натягной, гипсокартон, ит.д.
        'color': str,       # Описание цвета
        'features': str     # Особенности
    },
    'furniture': [
        {
            'item': str,        # Название предмета
            'material': str,    # Материал
            'color': str        # Описание цвета
        }
    ],
    'lighting': {
        'types': [str],     # ['Настольная лампа', …]
        'description': str  # Описание
    },
    'decor': [
        {
            'item': str,
            'description': str
        }
    ],
    'full_description': str # Полное текстовое описание
}
```

**Пример использования:**
```python
from services.vision_analysis import DesignAnalyzer

analyzer = DesignAnalyzer(provider='gpt')
result = await analyzer.analyze('https://example.com/image.jpg')

print(result['style'])          # "Новое миграция"
print(result['walls']['ral_code'])  # "RAL 7016"
```

#### Метод `_analyze_with_gpt()`
Приватный метод для GPT-4 Vision.

#### Метод `_analyze_with_claude()`
Приватный метод для Claude Vision.

#### Метод `_analyze_with_gemini()`
Приватный метод для Gemini Vision.

---

### `design_parser.py`

#### Класс `DesignParser`

Парсинг и валидация результатов анализа.

#### Метод `parse_json(response: str) -> dict`

Парсит JSON ответ от API.

```python
parser = DesignParser()
result = parser.parse_json(api_response)
```

#### Метод `format_for_telegram(data: dict) -> str`

Форматирует данные для Telegram.

```python
formatted = parser.format_for_telegram(analysis_data)
await message.answer(formatted, parse_mode="Markdown")
```

**Данные возвращаются в виде:**
```
🎨 **ОПИСАНОО ДИЗАЙНА**

**Стиль**: ...
**СТЕНЫ**: ...
...
```

#### Метод `validate_data(data: dict) -> bool`

Проверяет требуемые поля.

#### Метод `normalize_ral_code(ral: str) -> str`

Нормализует RAL коды.

```python
normalized = parser.normalize_ral_code("ral 7016")  # "RAL 7016"
```

---

### `design_cache.py`

#### Класс `DesignCache`

Кэширование результатов анализа.

#### Метод `get(image_hash: str) -> dict | None`

Получает закэшированные результаты.

```python
cache = DesignCache()
result = cache.get(image_hash)
if result:
    # Уже анализировано
    print(result)
else:
    # Не в кэше, нужно анализировать
    pass
```

#### Метод `set(image_hash: str, data: dict, ttl: int = 86400) -> bool`

Сохраняет в кэш.

```python
cache.set(
    image_hash="abcd1234",
    data=analysis_data,
    ttl=86400  # 24 часа
)
```

#### Метод `calculate_hash(image_url: str) -> str`

Начисляет hash изображения.

```python
hash_val = cache.calculate_hash("https://example.com/image.jpg")
# абцд123456789...
```

---

## 🎛️ HANDLERS

### `design_analysis.py`

#### Функция `get_design_description_handler()`

Обрабатывает нажатие на кнопку "📋 Описание дизайна".

**Маршрутизация:**
```python
@router.callback_query(
    StateFilter(CreationStates.post_generation_sample),
    F.data == "get_design_description"
)
```

**Поток грамм состояний:**
```
1. Получаем URL изображения из state
2. Показываем "⏳ Анализирую..."
3. Вызываем vision_analysis.analyze()
4. Парсим результаты
5. Форматируем для Telegram
6. Отправляем пользователю
7. На основании: сохраняем в БД
```

---

## 📄 ТИПЫ ДАННЫХ

### `AnalysisResult` тип

```python
from typing import TypedDict

class WallsInfo(TypedDict):
    color: str
    ral_code: str
    material: str
    texture: str

class FloorInfo(TypedDict):
    material: str
    color: str
    pattern: str

class CeilingInfo(TypedDict):
    type: str
    color: str
    features: str

class FurnitureItem(TypedDict):
    item: str
    material: str
    color: str

class LightingInfo(TypedDict):
    types: list[str]
    description: str

class DecorItem(TypedDict):
    item: str
    description: str

class AnalysisResult(TypedDict):
    style: str
    walls: WallsInfo
    floor: FloorInfo
    ceiling: CeilingInfo
    furniture: list[FurnitureItem]
    lighting: LightingInfo
    decor: list[DecorItem]
    full_description: str
```

---

## ⚠️ ОШИБКИ

### `AnalysisError`

Базовая ошибка анализа.

```python
try:
    result = await analyzer.analyze(image_url)
except AnalysisError as e:
    logger.error(f"Ошибка анализа: {e}")
    await message.answer("❌ Ошибка при анализе")
```

### `InvalidImageError`

Невалидное изображение.

### `ProviderError`

Ошибка провайдера API.

### `ParseError`

Ошибка парсинга результатов.

---

## ✅ ПОЛНЫЕ ПРИМЕРЫ КОДА

### Пример 1: Основное использование

```python
from services.vision_analysis import DesignAnalyzer
from services.design_parser import DesignParser
from services.design_cache import DesignCache

# Объекты
async def analyze_design(image_url: str):
    # Объекты
    analyzer = DesignAnalyzer(provider='gpt')
    parser = DesignParser()
    cache = DesignCache()
    
    # Проверим кэш
    image_hash = cache.calculate_hash(image_url)
    cached = cache.get(image_hash)
    
    if cached:
        result = cached
    else:
        # Анализируем
        result = await analyzer.analyze(image_url)
        
        # Парсим
        result = parser.parse_json(result)
        
        # Валидируем
        if not parser.validate_data(result):
            raise ParseError("Невалидные данные")
        
        # Кэшируем
        cache.set(image_hash, result)
    
    return result

# В handler
@router.callback_query(...)
async def handler(callback, state):
    data = await state.get_data()
    image_url = data.get('last_generated_image_url')
    
    result = await analyze_design(image_url)
    formatted = parser.format_for_telegram(result)
    
    await callback.message.answer(formatted, parse_mode="Markdown")
```

### Пример 2: Обработка ошибок

```python
try:
    result = await analyze_design(image_url)
    formatted = parser.format_for_telegram(result)
    await message.answer(formatted, parse_mode="Markdown")
    
except ProviderError as e:
    logger.error(f"Ошибка API: {e}")
    await message.answer(
        "❌ Ошибка анализа. "
        "Попробуйте после."
    )
    
except ParseError as e:
    logger.error(f"Ошибка парсинга: {e}")
    await message.answer(
        "❌ Не могли проанализировать изображение."
    )
    
except Exception as e:
    logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
    await message.answer("❌ Неизвестная ошибка")
```

---

## 📝 ЗАМЕЧАНИя

- Настройки provider: используй `.env` на производстве
- Кэш ставит TTL в 24h (Redis действует только если он настроен)
- Мючайтесь что результаты парсятся как JSON (От API)

