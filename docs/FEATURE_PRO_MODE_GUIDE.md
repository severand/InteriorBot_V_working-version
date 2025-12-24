# 🔧 KIE.AI PRO MODE ГНДОВА

**Ветка:** `feature/kie-pro-mode-integration`  
**Дата:** 2025-12-24  
**Статус:** ✅ ГОТОВО К ТЕСТИРОВАНИЮ  

---

## 🜟 ОБЗОР

Это руководство рассказывает о включении поддержки **KIE.AI PRO режима** в проект InteriorBot.

### Сравнение режимов:

| Аспект | BASE | PRO |
|----------|------|-----|
| **Модель** | `google/nano-banana` | `nano-banana-pro` |
| **Скорость** | быстро | медленнее |
| **Качество** | хорошее | отличное |
| **Цена** | дешевле | дороже |
| **Параметры** | `image_size` | `aspect_ratio`, `resolution` |
| **Таймаут** | 300s | 600s |

---

## 💅 ЧТО БЫЛО ИЗМЕНЕНО

### Коммиты:

#### 1️⃣ **Коммит 1:** Конфигурация (.env)
- Добавлен `USE_PRO_MODEL` для переключения режимов
- Добавлены PRO параметры (`aspect_ratio`, `resolution`)
- Добавлены разные таймауты

**Файл:** `bot/.env.example`

#### 2️⃣ **Коммит 2:** Конфигурация Класса
- Новые модели в `KieConfig`
- Проперти для PRO режима
- Динамическое выбрание таймаута

**Файл:** `bot/config_kie.py`

#### 3️⃣ **Коммит 3:** ГЛАВНАЯ реализация 🔥

- Поддержка PRO моделей в `MODELS`
- Хранение параметра `use_pro` в `KieApiClient`
- Обновление `text_to_image()` для PRO
- **КЛЮЧЕВОЕ:** Обновление `edit_image()` с условной логикой
  - **BASE:** `image_urls`, `image_size`
  - **PRO:** `image_input`, `aspect_ratio`, `resolution`
- Обновление 3 интеграционных функций:
  - `generate_interior_with_nano_banana()`
  - `generate_interior_with_text_nano_banana()`
  - `clear_space_with_kie()`
- Обратная совместимость (старый код работает)

**Файл:** `bot/services/kie_api.py` (2400+ строк)

---

## ✅ КАК ИСПОЛЬЗОВАТЬ

### Опция 1: ПО УМОЛЧАНИЮ

Установите в `.env`:

```bash
USE_PRO_MODEL=False  # используются BASE режим
```

Всё работает как раньше (без изменений в коде).

### Опция 2: ВКЛЮЧИТЬ PRO ГЛОБАЛЬНО

Установите в `.env`:

```bash
USE_PRO_MODEL=True
KIE_NANO_BANANA_PRO_ASPECT=16:9      # аспект-рейтио
# ОПЦИОНО: 1:1, 16:9, 9:16, 4:3, 3:4, и т.d.
KIE_NANO_BANANA_PRO_RESOLUTION=1K   # 1K (1024), 2K (2048), 4K (4096)
```

Это будет использовать PRO режим для **всех** генераций.

### Опция 3: ПЕРЕКЛЮЧАТЬ НА УРОВНЕ КОДА

```python
from services.kie_api import generate_interior_with_nano_banana

# BASE режим
result_base = await generate_interior_with_nano_banana(
    photo_file_id=file_id,
    room="bedroom",
    style="modern",
    bot_token=token,
    use_pro=False  # ✅ явно
)

# PRO режим
result_pro = await generate_interior_with_nano_banana(
    photo_file_id=file_id,
    room="bedroom",
    style="modern",
    bot_token=token,
    use_pro=True  # ✅ теперь PRO!
)
```

---

## 📤 ОТОБРАЖЕНИЕ ЛОГОВ

### BASE режим:

```
======================================================================
📋 ПОВТОРНОЕ РЕНДЕРИНГ (Google Nano Banana BASE)
   Промпт: Make this bedroom look modern...
   Кол-во изображений: 1
======================================================================
Model: google/nano-banana-edit
Mode: 📋 BASE
Image URLs: ['https://...']
Image Size (BASE): auto
```

### PRO режим:

```
======================================================================
🔧 ПОВТОРНОЕ РЕНДЕРИНГ (Google Nano Banana PRO)
   Промпт: Make this bedroom look modern...
   Кол-во изображений: 1
======================================================================
Model: nano-banana-pro
Mode: 🔧 PRO
Image Input: ['https://...']
Aspect Ratio (PRO): 16:9
Resolution (PRO): 1K
```

---

## ⚠️ КОНЦО: ГЛАВНОЕ ОТЛИЧИЕ

### Основное отличие:

```python
# ⚠️ BASE ИСПОЛЬЗУЕТ image_urls
input_data = {
    "image_urls": [...],    # ✅ НЕ image_input!
    "image_size": "auto",
    "prompt": "...",
}

# ⚠️ PRO ИСПОЛЬЗУЕТ image_input
input_data = {
    "image_input": [...],   # ✅ НЕ image_urls!
    "aspect_ratio": "16:9",
    "resolution": "1K",
    "prompt": "...",
}
```

**это автоматически обрабатывается** (см. отрывки `if use_pro_mode`).

---

## 🚀 ТЕСТИРОВАНИЕ

### Unit Тесты:

```bash
# Проверить конфиг
python bot/config_kie.py

# Ожидаемые выходы (USE_PRO_MODEL=False):
# ✅ KIE.AI NANO BANANA API КОНФИГ:
#   Mode: 📋 BASE
#   Timeout (BASE): 300s
#   Timeout (PRO): 600s
#   Current timeout: 300s

# Ожидаемые выходы (USE_PRO_MODEL=True):
# ✅ KIE.AI NANO BANANA API КОНФИГ:
#   Mode: 🔧 PRO
#   Current timeout: 600s
```

### Integration Тесты:

Протестируйте бот с настоящим изображением:

1. **SET:** `USE_PRO_MODEL=False` → тестируют BASE режим
   - Модель: `google/nano-banana-edit`
   - Параметры: `image_urls`, `image_size`
   - Таймаут: 300s

2. **SET:** `USE_PRO_MODEL=True` → тестируют PRO режим
   - Модель: `nano-banana-pro`
   - Параметры: `image_input`, `aspect_ratio`, `resolution`
   - Таймаут: 600s

---

## ✅ КОММИТЫ НА GITHUB

```
feature/kie-pro-mode-integration
├─ e42dbc33 feat: Add KIE.AI PRO mode environment variables
├─ 12ccd543 feat: Update config_kie.py to support PRO mode
└─ 4a83fce0 feat: Add full PRO mode support to kie_api.py
```

---

## 🚅 НЕОБХОДИМЮЕ ВДОКОвНОВО

### ДЛЯ MERGE В MAIN:

- ✅ Все обновления API готовы
- ✅ Не уничтожена вся старая функциональность
- ✅ Обратная совместимость (все параметры Optional)
- ✅ Недеструктивные изменения

### ОПЦИОНАЛЬНО: Которые ещё стоит сделать

- [ ] Обновить `api_fallback.py` (Replicate fallback)
- [ ] Написать unit тесты
- [ ] Написать integration тесты
- [ ] Обновить документацию

---

## 🙋 ПОМОЩЬ

### Если что-то не работает:

1. Проверьте логи на **Mode** (🔧 PRO vs 📋 BASE)
2. Открыть Issue с отрывками Логов
3. Проверьте, что `.env` имеет все новые переменные

### Ограничения:

- PRO режим требует дополнительно 300 секунд (до 10 мин общ)
- Обусловить API rate limits
- PRO не супортирует `image_urls` (только `image_input`)

---

**Готово к тестированию!** 🚉
