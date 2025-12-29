# KIE.AI Integration Guide

## 📋 Оглавление

1. [Обзор](#обзор)
2. [Быстрый старт](#быстрый-старт)
3. [API Endpoints](#api-endpoints)
4. [Архитектура интеграции](#архитектура-интеграции)
5. [Примеры использования](#примеры-использования)
6. [Troubleshooting](#troubleshooting)
7. [Производительность](#производительность)

---

## 🎯 Обзор

### Что такое KIE.AI?

[KIE.AI](https://kie.ai) — это платформа для доступа к Google Nano Banana API для генерации и редактирования изображений.

### Преимущества KIE.AI

- ⚡ **Быстро**: ~20-30 секунд на генерацию
- 💰 **Дешево**: Доступные цены
- 🌍 **Доступно**: Работает из России через VPN
- 🔄 **Надежно**: Polling механизм с автоматическими повторами

### Модели

- **`google/nano-banana`** — Генерация изображений из текста
- **`google/nano-banana-edit`** — Редактирование существующих изображений (используется в боте)

---

## 🚀 Быстрый старт

### 1. Получить API ключ

1. Зарегистрироваться на [https://kie.ai](https://kie.ai)
2. Получить API ключ в личном кабинете
3. Добавить в `.env`:
   ```bash
   KIE_API_KEY=your_api_key_here
   ```

### 2. Установить зависимости

```bash
pip install httpx asyncio
```

### 3. Базовый пример

```python
from services.kie_api import NanoBananaClient

client = NanoBananaClient()

# Генерация изображения
result_url = await client.text_to_image(
    prompt="A modern living room with Scandinavian style",
    output_format="png",
    image_size="16:9"
)

print(f"Result: {result_url}")
```

---

## 📡 API Endpoints

### Base URL

```
https://api.kie.ai
```

### 1. Создание задачи генерации

**Endpoint:**
```
POST /api/v1/jobs/createTask
```

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "google/nano-banana-edit",
  "input": {
    "image_urls": ["https://example.com/image.jpg"],
    "prompt": "Transform this room into modern style",
    "output_format": "png",
    "image_size": "auto"
  }
}
```

**Response:**
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "b254d74d61b531d315431c3229917857"
  }
}
```

---

### 2. Получение результата задачи

**Endpoint:**
```
GET /api/v1/jobs/recordInfo?taskId={TASK_ID}
```

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
```

**Response (в процессе):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "b254d74d61b531d315431c3229917857",
    "model": "google/nano-banana-edit",
    "state": "generating",
    "createTime": 1766495357000,
    "updateTime": 1766495370000
  }
}
```

**Response (успешно):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "b254d74d61b531d315431c3229917857",
    "model": "google/nano-banana-edit",
    "state": "success",
    "resultJson": "{\"resultUrls\":[\"https://tempfile.aiquickdraw.com/workers/nano/image_1766495357304_8pqhnm.png\"]}",
    "completeTime": 1766495384000,
    "createTime": 1766495357000,
    "updateTime": 1766495384000
  }
}
```

**Response (ошибка):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "b254d74d61b531d315431c3229917857",
    "state": "fail",
    "failMsg": "Invalid image URL",
    "failCode": "400"
  }
}
```

---

### Статусы задачи

| Статус | Описание |
|--------|----------|
| `waiting` | Задача в очереди |
| `queuing` | Задача обрабатывается |
| `generating` | Генерация в процессе |
| `success` | Генерация успешна, результат в `resultJson` |
| `fail` | Генерация провалена, ошибка в `failMsg` |

---

## 🏗️ Архитектура интеграции

### Структура файлов

```
bot/
├── services/
│   ├── kie_api.py          # Основной клиент KIE.AI
│   ├── api_fallback.py     # Fallback система (KIE.AI → Replicate)
│   ├── replicate_api.py    # Резервный клиент Replicate
│   └── prompts.py          # Генерация промптов
```

### Класс `KieApiClient`

**Основные методы:**

```python
class KieApiClient:
    async def create_generation_task(
        model: str,
        input_data: Dict[str, Any]
    ) -> Optional[str]:
        """Создать задачу генерации"""
        
    async def get_task_status(
        task_id: str
    ) -> Optional[Dict[str, Any]]:
        """Получить статус задачи"""
        
    async def poll_task_result(
        task_id: str,
        max_polls: int = 100,
        poll_interval: int = 3
    ) -> Optional[str]:
        """Ожидать результат с polling"""
```

### Класс `NanoBananaClient`

**Наследует `KieApiClient`, добавляет удобные методы:**

```python
class NanoBananaClient(KieApiClient):
    async def text_to_image(
        prompt: str,
        output_format: str = "png",
        image_size: str = "16:9"
    ) -> Optional[str]:
        """Генерация изображения из текста"""
        
    async def edit_image(
        image_urls: List[str],
        prompt: str,
        output_format: str = "png",
        image_size: str = "auto"
    ) -> Optional[str]:
        """Редактирование изображения"""
```

---

## 📝 Примеры использования

### Пример 1: Генерация дизайна интерьера

```python
from services.kie_api import generate_interior_with_nano_banana

result_url = await generate_interior_with_nano_banana(
    photo_file_id="AgACAgIAAxkBAAIZRGlKgAu...",
    room="bedroom",
    style="scandinavian",
    bot_token=BOT_TOKEN
)

if result_url:
    print(f"Success: {result_url}")
else:
    print("Generation failed")
```

### Пример 2: Очистка пространства

```python
from services.kie_api import clear_space_with_kie

result_url = await clear_space_with_kie(
    photo_file_id="AgACAgIAAxkBAAIZRGlKgAu...",
    bot_token=BOT_TOKEN
)

if result_url:
    print(f"Cleared image: {result_url}")
```

### Пример 3: Прямое использование клиента

```python
from services.kie_api import NanoBananaClient

client = NanoBananaClient(api_key="your_key")

# Редактирование изображения
result = await client.edit_image(
    image_urls=["https://example.com/room.jpg"],
    prompt="Modern minimalist bedroom with white walls",
    output_format="png"
)

print(result)
# Output: https://tempfile.aiquickdraw.com/workers/nano/image_xxx.png
```

---

## 🔧 Troubleshooting

### Проблема 1: 401 Unauthorized

**Симптомы:**
```json
{"code":401,"msg":"You do not have access permissions"}
```

**Решение:**
- Проверить API ключ в `.env`
- Убедиться, что header `Authorization: Bearer {key}` передается
- Проверить баланс аккаунта на KIE.AI

---

### Проблема 2: 404 Not Found

**Симптомы:**
```json
{"status":404,"error":"Not Found","path":"/api/v1/jobs/getResult"}
```

**Решение:**
- Использовать правильный endpoint: `/api/v1/jobs/recordInfo`
- НЕ использовать `/api/v1/jobs/getResult` (устаревший)

---

### Проблема 3: Таймаут генерации

**Симптомы:**
```
❌ Таймаут: результат не получен за 300s
```

**Решение:**
1. Увеличить `KIE_API_MAX_POLLS` в `kie_api.py`:
   ```python
   KIE_API_MAX_POLLS = 150  # 7.5 минут вместо 5
   ```

2. Или увеличить `poll_interval`:
   ```python
   KIE_API_POLLING_INTERVAL = 5  # 5 секунд вместо 3
   ```

---

### Проблема 4: Геоблокировка (Россия)

**Симптомы:**
- Запросы не проходят без VPN
- 403 Forbidden

**Решение:**
1. **Локально**: Включить VPN (США/Европа)
2. **На сервере**: Использовать proxy или VPN на уровне системы
3. **Альтернатива**: Использовать Replicate (работает без VPN)

---

### Проблема 5: resultJson пустой

**Симптомы:**
```python
resultJson: None
```

**Решение:**
- Подождать дольше (статус ещё не `success`)
- Проверить `state` и `failMsg` для диагностики

---

## 📊 Производительность

### Тайминги

| Этап | Время |
|------|-------|
| Создание задачи (`createTask`) | ~500ms |
| Polling интервал | 3s |
| Генерация (среднее) | 20-30s |
| Общее время | ~25-35s |

### Сравнение с Replicate

| Метрика | KIE.AI | Replicate |
|---------|--------|----------|
| Время генерации | 20-30s | 12-20s |
| Стоимость | Низкая | Средняя |
| Доступность (РФ) | Требует VPN | Работает напрямую |
| Надежность | Высокая | Высокая |

### Оптимизация

**1. Уменьшить polling интервал (не рекомендуется):**
```python
KIE_API_POLLING_INTERVAL = 2  # Быстрее, но больше запросов
```

**2. Использовать callback URL (advanced):**
```python
task_id = await client.create_generation_task(
    model="google/nano-banana-edit",
    input_data=input_data,
    callback_url="https://your-domain.com/callback"  # KIE.AI отправит результат сюда
)
```

---

## 🎯 Best Practices

### 1. Обработка ошибок

```python
try:
    result = await client.edit_image(...)
    if not result:
        # Fallback на Replicate
        result = await replicate_fallback(...)
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Уведомить пользователя
```

### 2. Логирование

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Для отладки
```

### 3. Retry логика

```python
for attempt in range(3):
    result = await client.edit_image(...)
    if result:
        break
    await asyncio.sleep(5)
```

---

## 📚 Ссылки

### Официальная документация

- **KIE.AI Docs**: [https://docs.kie.ai](https://docs.kie.ai)
- **Nano Banana Model**: [https://docs.kie.ai/market/google/nano-banana](https://docs.kie.ai/market/google/nano-banana)
- **Get Task Details**: [https://docs.kie.ai/market/common/get-task-detail](https://docs.kie.ai/market/common/get-task-detail)

### Полезные статьи

- [Google Nano Banana Overview](https://kie.ai/nano-banana)
- [API Rate Limits](https://docs.kie.ai/rate-limits)

---

## 📞 Контакты и поддержка

- **Email**: support@kie.ai
- **Discord**: [KIE.AI Community](https://discord.gg/kie-ai)
- **GitHub Issues**: [InteriorBot Issues](https://github.com/severand/InteriorBot/issues)

---

## 📜 История изменений

### v3.0 (2025-12-23)
- ✅ Исправлен endpoint на `/api/v1/jobs/recordInfo`
- ✅ Добавлен парсинг `resultJson` → `resultUrls`
- ✅ Улучшена обработка статусов (`waiting`, `success`, `fail`)
- ✅ Добавлен `import asyncio`
- ✅ Проверена работа с VPN из России

### v2.2 (2025-12-23)
- Попытка использовать `/api/v1/jobs/getResult` (не сработал)
- Добавлено несколько вариантов endpoint'ов

### v2.0 (2025-12-23)
- Первая рабочая интеграция с KIE.AI
- Базовый polling механизм

---

## ✅ Чеклист интеграции

- [x] Получен API ключ
- [x] Добавлен в `.env`
- [x] Установлены зависимости
- [x] Проверена работа `createTask`
- [x] Проверена работа `recordInfo`
- [x] Парсинг `resultJson` работает
- [x] Polling возвращает результат
- [x] Fallback на Replicate настроен
- [x] VPN настроен (если РФ)
- [x] Логирование работает
- [x] Обработка ошибок добавлена

---

**Документ обновлен:** 2025-12-23  
**Автор:** Project Owner  
**Версия:** 3.0
