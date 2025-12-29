# 🌐 GUIDE: Prompt Translation System

**Дата создания**: 2025-12-23  
**Версия**: 1.0  
**Статус**: ✅ Production Ready

---

## 📋 Содержание

1. [Обзор](#обзор)
2. [Архитектура](#архитектура)
3. [Быстрый старт](#быстрый-старт)
4. [Конфигурация](#конфигурация)
5. [Providers (Провайдеры)](#providers-провайдеры)
6. [Примеры использования](#примеры-использования)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Обзор

### Что это?

Система **автоматического перевода промптов** с русского языка на английский **перед отправкой в генеративные API** (KIE.AI, Replicate).

### Зачем это нужно?

- ✅ **Улучшение качества генерации**: Нейросети лучше понимают английский
- ✅ **Унифицированный язык**: Все промпты отправляются на одном языке
- ✅ **Кэширование**: Переводы кэшируются для оптимизации
- ✅ **Fallback система**: Если перевод не удался - используется оригинальный текст
- ✅ **Multi-provider**: Поддержка 3+ провайдеров перевода

---

## 🏗️ Архитектура

### Компоненты системы

```
┌─────────────────────────────────────────────────────┐
│          USER REQUEST (Телеграм Бот)               │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│     prompts.py                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ build_design_prompt(style, room, translate)    │ │
│  │ - Собирает промпт                              │ │
│  │ - [NEW] Вызывает translator.translate_prompt   │ │
│  └────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│    translator.py (Модуль перевода)                 │
│  ┌────────────────────────────────────────────────┐ │
│  │ async translate_prompt_to_english()            │ │
│  │  1. Проверка кэша                              │ │
│  │  2. Основной провайдер (Google/Yandex)        │ │
│  │  3. Fallback: LibreTranslate                   │ │
│  │  4. Fallback: Вернуть оригинальный текст      │ │
│  └────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌──────────┐
    │ Google  │ │ Yandex  │ │ Libre    │
    │Translate│ │Translate│ │Translate │
    └─────────┘ └─────────┘ └──────────┘
              Translation API
                     │
                     ▼
         ┌──────────────────────┐
         │ ENGLISH PROMPT       │
         │ (Translated)         │
         └──────────────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │     kie_api.py               │
      │  ┌──────────────────────┐    │
      │  │ edit_image()         │    │
      │  │ (send to KIE.AI)     │    │
      │  └──────────────────────┘    │
      └──────────────────────────────┘
```

### Файлы системы

| Файл | Описание |
|------|----------|
| `bot/services/translator.py` | **Основной модуль** - многопровайдерная система перевода |
| `bot/services/prompts.py` | **Обновлено** - добавлена интеграция translator.py |
| `bot/services/kie_api.py` | **Обновлено** - использует async функции с переводом |
| `.env.example` | Конфигурация для всех провайдеров перевода |

---

## 🚀 Быстрый старт

### 1️⃣ Установка зависимостей

```bash
# Должны быть установлены (уже в requirements.txt):
pip install aiohttp
```

### 2️⃣ Конфигурация `.env`

```bash
# Copy template
cp bot/.env.example bot/.env

# Edit .env и установите переменные:
USE_PROMPT_TRANSLATION=True
TRANSLATION_PROVIDER=google_translate
GOOGLE_TRANSLATE_API_KEY=your_key_here
```

### 3️⃣ Проверка работы

```python
import asyncio
from services.translator import translate_prompt_to_english

async def test():
    russian_text = "Создай красивый минималистичный дизайн для спальни"
    english_text = await translate_prompt_to_english(russian_text)
    print(f"Original:  {russian_text}")
    print(f"Translated: {english_text}")

asyncio.run(test())
```

---

## ⚙️ Конфигурация

### Основные параметры

```bash
# 1. Включить/выключить перевод
USE_PROMPT_TRANSLATION=True  # False для отключения

# 2. Выбрать основной провайдер
TRANSLATION_PROVIDER=google_translate
# Опции: google_translate | yandex | libre_translate
```

### Специфика провайдеров

#### 🔵 Google Translate (Рекомендуется)

```bash
TRANSLATION_PROVIDER=google_translate
GOOGLE_TRANSLATE_API_KEY=AIzaSy...
```

**Плюсы:**
- Самый точный перевод
- Быстрый ответ
- Поддержка специализированной лексики

**Минусы:**
- Платный (~$1 за 1M символов)
- Требует облачного аккаунта Google

**Получение ключа:**
1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект
3. Активируйте API "Cloud Translation API"
4. Создайте сервис-аккаунт
5. Получите ключ

---

#### 🟡 Yandex Translate

```bash
TRANSLATION_PROVIDER=yandex
YANDEX_TRANSLATE_API_KEY=AQVNbx...
```

**Плюсы:**
- Хорошее качество на русско-английской паре
- Бесплатные триалы
- Адаптирован для русского языка

**Минусы:**
- Платный после триала
- Медленнее Google

**Получение ключа:**
1. Перейдите на [Yandex Cloud](https://cloud.yandex.com/)
2. Создайте облако
3. Активируйте Translate API
4. Получите API ключ

---

#### 🟢 LibreTranslate (Бесплатный)

```bash
TRANSLATION_PROVIDER=libre_translate
LIBRE_TRANSLATE_URL=https://libretranslate.de/translate
LIBRE_TRANSLATE_API_KEY=  # Опционально
```

**Плюсы:**
- Абсолютно бесплатный
- Open-source
- Можно развернуть локально
- Нет лимитов

**Минусы:**
- Качество переводов ниже
- Публичный сервер может быть перегружен
- Медленнее платных вариантов

**Использование:**

```bash
# Вариант 1: Публичный сервер (SLOWEST)
LIBRE_TRANSLATE_URL=https://libretranslate.de/translate

# Вариант 2: Локальный сервер (FAST)
# 1. Установить Docker
# 2. Запустить:
docker run -d -p 5000:5000 libretranslate/libretranslate
# 3. В .env:
LIBRE_TRANSLATE_URL=http://localhost:5000/translate
```

---

## 💾 Providers (Провайдеры)

### Логика выбора провайдера

1. **Основной провайдер** (TRANSLATION_PROVIDER)
   - Если успешно → используем результат ✅
   - Если ошибка → переходим к fallback 🔄

2. **Fallback: LibreTranslate**
   - Если успешно → используем результат ✅
   - Если ошибка → переходим дальше 🔄

3. **Последняя попытка**
   - Возвращаем оригинальный русский текст (без перевода)
   - Логируем ошибку ⚠️

### Кэширование

```python
# Переводы кэшируются в памяти приложения
_TRANSLATION_CACHE = {}

# Первый вызов: переводится + кэшируется
await translate_prompt_to_english("Текст")  # API call

# Второй вызов: берется из кэша (мгновенно)
await translate_prompt_to_english("Текст")  # Cache hit ✅
```

---

## 📖 Примеры использования

### Пример 1: Автоматический перевод при генерации

```python
from services.prompts import build_design_prompt
from services.kie_api import generate_interior_with_nano_banana

# В kie_api.py это уже сделано:
# prompt = await build_design_prompt(style, room, translate=True)
# ↑ Автоматически переводит на английский
```

### Пример 2: Явное использование translator

```python
from services.translator import translate_prompt_to_english

async def my_function():
    russian_prompt = "Создай скандинавский минимализм в спальне"
    english_prompt = await translate_prompt_to_english(russian_prompt)
    
    # Отправляем на английском
    api_result = await some_api.generate(english_prompt)
    return api_result
```

### Пример 3: Отключение перевода

```python
# В .env:
USE_PROMPT_TRANSLATION=False

# Или в коде:
from services.prompts import build_design_prompt

prompt = await build_design_prompt(
    style='modern',
    room='bedroom',
    translate=False  # Без перевода
)
```

### Пример 4: Статистика переводов

```python
from services.translator import get_translation_stats

stats = await get_translation_stats()
print(stats)
# {
#     'translation_enabled': True,
#     'primary_provider': 'google_translate',
#     'cache_size': 42,
#     'google_api_configured': True,
#     'yandex_api_configured': False,
#     'libre_translate_configured': True
# }
```

---

## 🔧 Troubleshooting

### ❓ Перевод не работает

**Признаки:**
- `❌ Translation disabled - returning original text`
- `⚠️ Translation failed`

**Решение:**

```bash
# 1. Проверить USE_PROMPT_TRANSLATION
echo $USE_PROMPT_TRANSLATION  # Должно быть True

# 2. Проверить конфигурацию провайдера
echo $TRANSLATION_PROVIDER  # google_translate, yandex, или libre_translate

# 3. Проверить API ключ
echo $GOOGLE_TRANSLATE_API_KEY
# Должен быть непустой для выбранного провайдера

# 4. Посмотреть логи
grep "TRANSLATOR" app.log
```

### ❓ Медленный перевод

**Причины и решения:**

| Причина | Решение |
|---------|----------|
| Используется публичный LibreTranslate | Переключиться на Google/Yandex или развернуть локальный |
| API перегружен | Добавить retry механизм в `translator.py` |
| Сеть медленная | Оптимизировать размер промпта |

### ❓ Неправильный перевод

**Решение:**

```python
# Очистить кэш и попробовать еще раз
from services.translator import clear_translation_cache

clear_translation_cache()

# Или переключиться на другого провайдера
# В .env: TRANSLATION_PROVIDER=yandex
```

### ❓ API ошибка при переводе

**Логирование:**

```python
# translator.py логирует все ошибки подробно:
# ❌ [PRIMARY] Google Translate error: ...
# ❌ [FALLBACK] LibreTranslate error: ...
# ❌ TRANSLATION FAILED - Returning original Russian text
```

---

## 📊 Мониторинг

### Логирование системы перевода

```python
# Включить DEBUG логирование
# В config.py или main.py:
import logging
logging.getLogger('services.translator').setLevel(logging.DEBUG)
```

### Метрики для отслеживания

```
📊 METRICS:
- Cache hits: Сколько переводов взято из кэша
- Provider success rate: Процент успешных переводов по провайдеру
- Average translation time: Среднее время перевода
- Fallback count: Сколько раз использовался fallback
```

---

## 🔄 Миграция с текущей системы

Если у вас были `build_design_prompt()` без параметра `translate`:

```python
# СТАРО (синхронно):
prompt = build_design_prompt_sync(style, room)

# НОВО (асинхронно с переводом):
prompt = await build_design_prompt(style, room, translate=True)
```

**Обратная совместимость:**

```python
# Старый код все еще работает:
prompt = build_design_prompt_sync(style, room)  # ✅ Работает

# Новый код с переводом:
prompt = await build_design_prompt(style, room)  # ✅ Работает + переводит
```

---

## 📞 Support

Если возникли вопросы:

1. Проверьте логи: `grep -i "translation" app.log`
2. Воспроизведите ошибку с `LOG_LEVEL=DEBUG`
3. Обратитесь с примером ошибки и конфигом

---

## ✅ Checklist для деплоя

- [ ] `.env` файл обновлен с переменными перевода
- [ ] Выбран провайдер (google_translate по умолчанию)
- [ ] API ключ получен и установлен
- [ ] `aiohttp` в requirements.txt
- [ ] Проведено тестирование на локальной машине
- [ ] Логирование настроено
- [ ] Fallback провайдеры готовы (LibreTranslate)
- [ ] Документация обновлена

---

**Создано**: 2025-12-23  
**Статус**: ✅ Production Ready  
**Версия**: 1.0