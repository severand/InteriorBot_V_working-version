# Миграционный гайд: Replicate → Kie.ai

> **Важно:** этот гайд описывает, как минимально обновить код без риска нарушить всё. Если что-то не работает, всегда можно вернуться к Replicate, на старой ветке **`main`**.

## Общие Принципы

- **Новая ветка:** `feat/kie-api-integration`
- **Старая ветка:** `main` (Replicate)
- **Деструктивные алтерации:** Книгогонь
- **Остается детдется:** Всё в replicate_api.py

---

## ШАГ 1: Обновить `.env` файл

### Новые переменные:

```bash
# Kie.ai API конфигурация
KIE_API_KEY=sk_kie_your_key_here            # Получить на https://kie.ai/account
USE_KIE_API=False                           # False = Replicate (current), True = Kie.ai (new)
KIE_INTERIOR_MODEL=flux_kontext              # модель генерации
KIE_FLUX_STRENGTH=0.7                       # 0.1-1.0
KIE_FLUX_STEPS=25                           # 20-50
KIE_VERBOSE=False                           # True для дебаггинга

# Старые переменные (остаются для fallback):
REPLICATE_API_TOKEN=your_key_here           # Остается для страховки
```

**Почему `USE_KIE_API=False`?**
- Энто означает "оставаться на Replicate по умолчанию"
- Это безопасные обновления
- Можно тестировать в конца цепи

---

## ШАГ 2: Копировать НОВЫЕ файлы

**НИЧЕГО НЕ ДЕЛАТЕ!!!**

Все файлы уже с другой ветки:

- ✅ `bot/services/kie_api.py` - Клиент Kie.ai API
- ✅ `bot/config_kie.py` - Конфигурация
- ✅ `docs/KIE_API_INTEGRATION.md` - Документация
- ✅ `test_kie_api.py` - Тесты

Директории не изменены:
- ✅ `bot/services/replicate_api.py` - Остаысь как есть (унтактные fallback)
- ✅ `bot/handlers/` - Унтактные на настоящий момент

---

## ШАГ 3: ОБНОВИТЕ `bot/handlers/creation.py`

### Найти это:

```python
# БЫЛО НАУ - СНАША (три места в файле)
from services.replicate_api import generate_image_auto

# ... в некоторох функциях:
result = await generate_image_auto(
    photo_file_id=photo_file_id,
    room=room,
    style=style,
    bot_token=bot_token,
)
```

### Заменить на:

```python
# НОВО НАУ
# В первых строках файла:
from config_kie import config_kie
from services.replicate_api import generate_image_auto
from services.kie_api import generate_interior_with_flux  # НОВО

# ... в те же функциях:
if config_kie.USE_KIE_API:
    # Когда Киеай включен
    result = await generate_interior_with_flux(
        photo_file_id=photo_file_id,
        room=room,
        style=style,
        bot_token=bot_token,
        strength=config_kie.KIE_FLUX_STRENGTH,
    )
else:
    # Где Replicate (по умолчанию)
    result = await generate_image_auto(
        photo_file_id=photo_file_id,
        room=room,
        style=style,
        bot_token=bot_token,
    )
```

### Найти и обновить плацы:

```bash
# Текущая ветка main:
grep -n "generate_image_auto" bot/handlers/creation.py

# строки будут показаны
```

---

## ШАГ 4: ТЕСТЫ

### Локально (читай файл:

```bash
# Проверить всё НОВОЕ
$ python test_kie_api.py

# Ожидать вывод:
# ✅ Tests: 8/8 passed
# ✅ API key found
# ✅ All modules imported
# ✅ Config validated
```

### Минимальные тесты:

```python
# пытон3 -c "from bot.config_kie import config_kie; print(config_kie.USE_KIE_API)"
# False (expected)

# python3 -c "from bot.services.kie_api import KieApiClient; print('OK')"
# OK (modules working)
```

---

## ШАГ 5: ПЕРЕКЛЮЧЕНИЕ

### КГда протеливан цепи и логи чисты:

```bash
# .env:
USE_KIE_API=True  # ОК!
```

### Перезагружай бот:

```bash
# Приготовьте допрос:
$ pip install -q python-dotenv httpx  # зависимости алтрется

# Тестировать при USE_KIE_API=True:
$ python test_kie_api.py
```

---

## ЕНЫ НОВАЁ ФИНКЦиональностю

### Основная
```python
from bot.services.kie_api import generate_interior_with_flux

result = await generate_interior_with_flux(
    photo_file_id=photo_file_id,
    room="bedroom",
    style="modern",
    bot_token=bot_token,
    strength=0.7,
)
```

### Альтернативная
```python
from bot.services.kie_api import generate_interior_with_gpt4o

result = await generate_interior_with_gpt4o(
    photo_file_id=photo_file_id,
    room="bedroom",
    style="modern",
    bot_token=bot_token,
)

# result - список URL, выбери рвый:
result_url = result[0] if result else None
```

### Очистка
```python
from bot.services.kie_api import clear_space_with_kie

result = await clear_space_with_kie(
    photo_file_id=photo_file_id,
    bot_token=bot_token,
)
```

---

## ОЯТ ЕойЗ ДЕНИЕ

### Если провал Киеай:

```python
if config_kie.USE_KIE_API:
    result = await generate_interior_with_flux(...)
    if result is None:  # Fallback автоматически
        result = await generate_image_auto(...)
else:
    result = await generate_image_auto(...)
```

### Контроль кредитов:

```python
from bot.services.kie_api import KieApiClient

client = KieApiClient()
credits = await client.check_credits()

if credits < 100:  # три баллах
    logger.warning(f"На КиеАй осталось {credits} кредитов")
    # На реринух Replicate
    config_kie.USE_KIE_API = False
```

---

## ТРУБЛЕШУТИНГ

### Ошибка: KIE_API_KEY not configured

```bash
# Ошибка:
# ❌ KIE_API_KEY not configured in .env

# Решение:
1. Открыть .env
2. Обновить KIE_API_KEY
3. Перезагружать
```

### Ошибка: API timeout

```bash
# Ошибка:
# ❌ API timeout (>300s)

# Решение:
1. Проверить интернет
2. Проверить Kie.ai статус (https://kie.ai/status)
3. От FallBack на Replicate
```

### Ошибка: Insufficient credits

```bash
# Ошибка:
# ❌ Insufficient credits: 0

# Решение:
1. Открыть https://kie.ai/account
2. Онаполнить аккаунт
3. Вернуться к Replicate в .env
```

---

## ПОТОЖУ НЕОЖОМЫЕ

Стандарттно порядок проверки:

1. роверить `. env`
2. Оториться `python test_kie_api.py`
3. Убежиться в лога (КОХ Ати Verbose)
4. Фалбацк к Replicate работает автоматически

---

## Отрать НАЗАД

### Если нужно вернуться к Replicate:

```bash
# Откатиться на ветку main:
$ git checkout main
$ git pull origin main

# Исправить .env:
# USE_KIE_API=False или удалить контроль

# Перезагружать бот
```

---

## ПОТЕНЦИАЛЬНЫЕ БУДУЩИЕ МОДИФИКАЦИИ

- [ ] Кеширование результатов генерации
- [ ] Автоматическая копиля Replicate - KIE
- [ ] Мониторинг метрик API
- [ ] Аналитика генераций

---

## ОТКУНІЯ ПОМОЩЬ

- Комплетная документация: `docs/KIE_API_INTEGRATION.md`
- Код клиента: `bot/services/kie_api.py`
- Конфигурация: `bot/config_kie.py`
- API индекс докс: https://docs.kie.ai

---

**Состояние:** Оторова К активации |
**Нативная:** 2025-12-23
