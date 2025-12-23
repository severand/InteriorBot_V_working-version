# 🌐 ARGOS TRANSLATE SETUP

**Дата:** 2025-12-23  
**Версия:** 1.0  
**Статус:** ✅ Production Ready

---

## 🚀 Быстрая установка

### Шаг 1: Установи Argos Translate

```bash
pip install argostranslate
```

### Шаг 2: Скачай языковые модели

```bash
python -m argostranslate install translations
```

**Это скачает:**
- Russian → English (ru-en)
- English → Russian (en-ru)
- И другие языки

**Размер:** ~600 MB (один раз)

### Шаг 3: Проверь установку

```python
import asyncio
from bot.services.translator import translate_prompt_to_english

async def test():
    result = await translate_prompt_to_english("Создай минимализм в спальне")
    print(f"Результат: {result}")

asyncio.run(test())
```

---

## ⚙️ Конфигурация

### В `.env` файле:

```bash
# Перевод промтов
USE_PROMPT_TRANSLATION=True
# TRANSLATION_PROVIDER больше НЕ НУЖЕН (используется Argos локально)
```

**Готово!** API ключи не требуются!

---

## ✅ ЧТО РАБОТАЕТ

### 1. Перевод русского на английский

```python
await translate_prompt_to_english("Сделай японский минимализм")
# → "Make Japanese minimalism"
```

### 2. Автоматическое определение языка

```python
# Если текст уже на английском - НЕ переводится!
await translate_prompt_to_english("You are a professional designer")
# → "You are a professional designer" (без перевода)
```

### 3. Кэширование

```python
# Первый вызов: перевод (~200-500ms)
await translate_prompt_to_english("Текст")  

# Второй вызов: из кэша (мгновенно!)
await translate_prompt_to_english("Текст")  # <10ms
```

---

## 📊 ХАРАКТЕРИСТИКИ ARGOS TRANSLATE

| Параметр | Значение |
|----------|----------|
| **Стоимость** | 🆓 Абсолютно бесплатный |
| **API ключи** | ❌ Не нужны |
| **Интернет** | ❌ Не нужен (работает offline) |
| **Скорость** | ⚡ ~200-500ms за промпт |
| **Качество** | ✅ Хорошее для промптов |
| **Размер модели** | 📦 ~600 MB (один раз) |
| **Установка** | 🔧 3 команды в терминале |
| **Зависимости** | PyTorch (установится автоматически) |

---

## 🔍 ПРИМЕРЫ

### Пример 1: Простой русский текст

```
Вход:  "Создай уникальный дизайн для этой комнаты с минимализмом"
Выход: "Create a unique design for this room with minimalism"
```

### Пример 2: Текст уже на английском (пропускается)

```
Вход:  "You are a professional interior designer"
Выход: "You are a professional interior designer" (без изменений)
```

### Пример 3: Смешанный текст (переводится русская часть)

```
Вход:  "Добавь contemporary style и natural light в интерьер"
Выход: "Add contemporary style and natural light to the interior"
```

---

## 🛠️ TROUBLESHOOTING

### ❌ Ошибка: "ModuleNotFoundError: No module named 'argostranslate'"

```bash
pip install argostranslate
```

### ❌ Ошибка: "Russian → English model not installed"

```bash
python -m argostranslate install translations
```

### ❌ Ошибка: "Translation returned empty result"

**Решение:** Убедись что Python версия 3.8+

```bash
python --version
```

### ⚠️ Первый запуск медленный

**Нормально!** Первый вызов загружает модель в память (~1-2 сек)  
Последующие вызовы быстрые (~200-500ms)

---

## 📋 ИНТЕГРАЦИЯ С ПРОЕКТОМ

**Все уже настроено!** Просто:

1. ✅ Установи: `pip install argostranslate`
2. ✅ Скачай модели: `python -m argostranslate install translations`
3. ✅ Установи `USE_PROMPT_TRANSLATION=True` в `.env`
4. ✅ Готово!

---

## 📊 СТАТИСТИКА ИСПОЛЬЗОВАНИЯ

```python
from services.translator import get_translation_stats

stats = await get_translation_stats()
print(stats)
# {
#     'translation_enabled': True,
#     'provider': 'Argos Translate (Local, Offline, Free)',
#     'argos_available': True,
#     'cache_size': 42,
#     'cached_prompts': [...]
# }
```

---

## 🔄 ОЧИСТКА КЭША

```python
from services.translator import clear_translation_cache

clear_translation_cache()
print("✅ Cache cleared!")
```

---

## 🎯 КОГДА ИСПОЛЬЗУЕТСЯ ПЕРЕВОД

✅ **Переводится:**
- Промпты на русском языке
- Смешанные тексты (русский + английский)

❌ **НЕ переводится:**
- Тексты полностью на английском
- Тексты короче 10 символов
- Если `USE_PROMPT_TRANSLATION=False` в `.env`

---

## ✅ ИТОГО

| Что | Статус |
|-----|--------|
| Установка | ✅ 3 команды |
| Конфигурация | ✅ Одна переменная |
| API ключи | ✅ Не нужны |
| Интернет | ✅ Не нужен |
| Стоимость | ✅ 0 рублей |
| Интеграция | ✅ Уже готова |
| Production ready | ✅ Да |

**Готово к использованию!** 🚀
