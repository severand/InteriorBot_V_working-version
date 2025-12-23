# ========================================
# ФАЙЛ: bot/services/kie_api.py
# НАЗНАЧЕНИЕ: Интеграция с Kie.ai API (Nano Banana)
# ВЕРСИЯ: 2.2 (2025-12-23) - FIXES
# АВТОР: Project Owner
# ========================================

import os
import logging
import httpx
import json
import asyncio
import time
from typing import Optional, Dict, Any, List
from config import config

from services.design_styles import get_room_name, get_style_description, is_valid_room, is_valid_style
from services.prompts import build_design_prompt, build_clear_space_prompt

logger = logging.getLogger(__name__)

# ========================================
# КОНФИГУРАЦИЯ KIE.AI (NANO BANANA)
# ========================================

KIE_API_BASE_URL = "https://api.kie.ai"  # Базовый URL API
KIE_API_ENDPOINT = "api/v1/jobs/createTask"  # КОРРЕКТНЫЙ ENDPOINT
KIE_API_TIMEOUT = 300  # Таймаут 5 минут для генерации
KIE_API_POLLING_INTERVAL = 2  # Проверять статус каждые 2 секунды
KIE_API_MAX_POLLS = 150  # Макс 150 попыток = 5 минут

# Модели для разных типов генерации
MODELS = {
    "image_generation": {
        "nano_banana": "google/nano-banana",  # Текст в изображение
        "nano_banana_edit": "google/nano-banana-edit",  # Редактирование изображений
    },
}


class KieApiClient:
    """
    Клиент для работы с Kie.ai API (Nano Banana).
    Предоставляет методы для генерации изображений.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента.

        Args:
            api_key: API ключ Kie.ai (если не передан, берется из конфига)
        """
        self.api_key = api_key or os.getenv('KIE_API_KEY') or getattr(config, 'KIE_API_KEY', None)
        self.base_url = KIE_API_BASE_URL
        self.endpoint = KIE_API_ENDPOINT
        self.timeout = KIE_API_TIMEOUT

        if not self.api_key:
            logger.warning("⚠️ KIE_API_KEY не установлен. Функции Kie.ai будут недоступны.")

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для API запроса."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Выполнить HTTP запрос к API.

        Args:
            method: HTTP метод (GET, POST, etc)
            endpoint: API endpoint
            data: Данные для POST запроса
            params: Query параметры

        Returns:
            JSON ответ или None при ошибке
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"📄 {method} {url}")

                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    logger.error(f"❌ Неподдерживаемый HTTP метод: {method}")
                    return None

                logger.debug(f"📃 Status: {response.status_code}")

                if response.status_code not in [200, 201, 202]:
                    logger.error(f"❌ API ошибка: {response.status_code} - {response.text}")
                    return None

                return response.json()

        except httpx.TimeoutException:
            logger.error(f"❌ Таймаут API запроса (>{self.timeout}s)")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к API: {e}")
            return None

    async def create_generation_task(
        self,
        model: str,
        input_data: Dict[str, Any],
        callback_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Создать задачу генерации.

        Args:
            model: Наименование модели
            input_data: Инпут параметры
            callback_url: Опциональный callback URL

        Returns:
            Task ID или None
        """
        data = {
            "model": model,
            "input": input_data,
        }

        if callback_url:
            data["callBackUrl"] = callback_url

        logger.debug(f"📄 Отправка зандначи генерации...")
        response = await self._make_request("POST", self.endpoint, data)

        if response and response.get("code") == 200 and "data" in response:
            task_id = response["data"].get("taskId")
            logger.debug(f"✅ Task ID: {task_id}")
            return task_id

        logger.error(f"❌ Ошибка создания задачи: {response}")
        return None

    async def get_task_result(
        self,
        task_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Получить результат задачи.
        
        Пытаемся несколько вариантов endpoint'a.

        Args:
            task_id: ID задачи

        Returns:
            Ответ с результатами или None
        """
        # Пытаем несколько вариантов
        endpoints = [
            ("api/v1/jobs/queryJobResult", {"taskId": task_id}),  # Вариант 1
            (f"api/v1/jobs/{task_id}", None),  # Вариант 2
            ("api/v1/jobs/getResult", {"taskId": task_id}),  # Вариант 3 (старый)
        ]

        for endpoint, params in endpoints:
            logger.debug(f"📈 Пытаем {endpoint}...")
            result = await self._make_request("GET", endpoint, params=params)
            
            if result and result.get("code") == 200:
                logger.debug(f"✅ Получен результат от {endpoint}")
                return result

        logger.error("❌ Не удалось получить результат от ни одного endpoint'a")
        return None

    async def poll_task_result(
        self,
        task_id: str,
        max_polls: int = KIE_API_MAX_POLLS,
        poll_interval: int = KIE_API_POLLING_INTERVAL,
    ) -> Optional[str]:
        """
        Ожидать результат генерации (поллинг).

        Args:
            task_id: ID задачи
            max_polls: Макс попыток
            poll_interval: Очередность проверки (сек)

        Returns:
            URL результата или None
        """
        logger.debug(f"⏳ Ожидание результата (Task: {task_id})...")

        for attempt in range(max_polls):
            result = await self.get_task_result(task_id)

            if result and result.get("code") == 200:
                data = result.get("data", {})
                if data.get("status") == "success" and "output" in data:
                    output_url = data["output"]
                    logger.debug(f"✅ Результат готов: {output_url}")
                    return output_url
                elif data.get("status") == "failed":
                    logger.error(f"❌ Генерация не удалась: {data.get('message')}")
                    return None

            # Ожидание перед следующей проверкой
            if attempt < max_polls - 1:
                elapsed = (attempt + 1) * poll_interval
                remaining = (max_polls - attempt - 1) * poll_interval
                logger.debug(f"⏳ [{attempt+1}/{max_polls}] Elapsed: {elapsed}s, Remaining: {remaining}s...")
                await asyncio.sleep(poll_interval)

        logger.error(f"❌ Таймаут: генерация не завершена за {max_polls * poll_interval} сек")
        return None


class NanoBananaClient(KieApiClient):
    """
    Специализированный клиент для Google Nano Banana API.
    Основное:
    - google/nano-banana: текст → изображение
    - google/nano-banana-edit: редактирование изображений
    """

    async def text_to_image(
        self,
        prompt: str,
        output_format: str = "png",
        image_size: str = "16:9",
    ) -> Optional[str]:
        """
        Генерация изображения из текста.

        Args:
            prompt: Текстовый промпт
            output_format: Формат (png, jpeg)
            image_size: Размер (1:1, 9:16, 16:9, 3:4, 4:3, 3:2, 2:3, 5:4, 4:5, 21:9, auto)

        Returns:
            URL сгенерированного изображения или None
        """
        logger.info("="*70)
        logger.info("🎨 ГЕНЕРАЦИЯ ТЕКСТ→ИЗОБРАЖЕНИЕ (Google Nano Banana)")
        logger.info(f"   Промпт: {prompt[:100]}...")
        logger.info(f"   Размер: {image_size}")
        logger.info("="*70)

        if not self.api_key:
            logger.error("❌ KIE_API_KEY не установлен")
            return None

        input_data = {
            "prompt": prompt,
            "output_format": output_format,
            "image_size": image_size,
        }

        logger.info(f"⏳ Отправка задачи генерации...")
        task_id = await self.create_generation_task(
            model=MODELS["image_generation"]["nano_banana"],
            input_data=input_data,
        )

        if not task_id:
            logger.error("❌ Не удалось создать задачу")
            return None

        logger.info(f"⏳ Ожидание результата (Task: {task_id})...")
        result_url = await self.poll_task_result(task_id)

        if result_url:
            logger.info(f"✅ Генерация успешна: {result_url}")
            return result_url

        logger.error("❌ Ошибка генерации: неверный ответ API")
        return None

    async def edit_image(
        self,
        image_urls: List[str],
        prompt: str,
        output_format: str = "png",
        image_size: str = "auto",
    ) -> Optional[str]:
        """
        Редактирование изображения.

        Args:
            image_urls: Список URL изображений (до 10)
            prompt: Текстовый промпт
            output_format: Формат (png, jpeg)
            image_size: Размер

        Returns:
            URL отредактированного изображения или None
        """
        logger.info("="*70)
        logger.info("✍️  РЕДАКТИРОВАНИЕ ИЗОБРАЖЕНИЕ (Google Nano Banana Edit)")
        logger.info(f"   Промпт: {prompt[:100]}...")
        logger.info(f"   Кол-во изображений: {len(image_urls)}")
        logger.info("="*70)

        if not self.api_key:
            logger.error("❌ KIE_API_KEY не установлен")
            return None

        input_data = {
            "image_urls": image_urls,
            "prompt": prompt,
            "output_format": output_format,
            "image_size": image_size,
        }

        logger.info(f"⏳ Отправка задачи редактирования...")
        task_id = await self.create_generation_task(
            model=MODELS["image_generation"]["nano_banana_edit"],
            input_data=input_data,
        )

        if not task_id:
            logger.error("❌ Не удалось создать задачу")
            return None

        logger.info(f"⏳ Ожидание результата (Task: {task_id})...")
        result_url = await self.poll_task_result(task_id)

        if result_url:
            logger.info(f"✅ Редактирование успешно: {result_url}")
            return result_url

        logger.error("❌ Ошибка редактирования: неверный ответ API")
        return None


# ========================================
# ИНТЕГРИРОВАННЫЕ ФУНКЦИИ ДЛЯ БОТА
# ========================================

async def get_telegram_file_url(photo_file_id: str, bot_token: str) -> Optional[str]:
    """
    Получить URL файла из Telegram Bot API.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                params={"file_id": photo_file_id}
            )

            if response.status_code != 200:
                logger.error(f"❌ Не удалось получить файл: {response.text}")
                return None

            result = response.json()
            if not result.get('ok'):
                logger.error(f"❌ API ошибка: {result}")
                return None

            file_path = result['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            logger.info(f"✅ Получен URL файла: {file_url}")
            return file_url

    except Exception as e:
        logger.error(f"❌ Ошибка при получении URL файла: {e}")
        return None


async def generate_interior_with_nano_banana(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
) -> Optional[str]:
    """
    Генерация дизайна интерьера с помощью Nano Banana (быстро и дешево).

    Args:
        photo_file_id: ID фото из Telegram
        room: Тип комнаты
        style: Стиль дизайна
        bot_token: Токен бота

    Returns:
        URL сгенерированного изображения или None
    """
    logger.info("="*70)
    logger.info("⚡ ГЕНЕРАЦИЯ ДИЗАЙНА [NANO BANANA via Kie.ai]")
    logger.info(f"   Комната: {room}")
    logger.info(f"   Стиль: {style}")
    logger.info("="*70)

    try:
        logger.info("📈 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        prompt = build_design_prompt(style, room)
        logger.info(f"📄 Промпт: {prompt[:200]}...")

        client = NanoBananaClient()
        result = await client.edit_image(
            image_urls=[image_url],
            prompt=prompt,
            output_format="png",
            image_size="auto",
        )

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации: {e}")
        return None


async def clear_space_with_kie(
    photo_file_id: str,
    bot_token: str,
) -> Optional[str]:
    """
    Очистка пространства от мебели используя Nano Banana.

    Args:
        photo_file_id: ID фото из Telegram
        bot_token: Токен бота

    Returns:
        URL очищенного изображения или None
    """
    logger.info("="*70)
    logger.info("🧽 ОЧИСТКА ПРОСТРАНСТВА [Kie.ai]")
    logger.info("="*70)

    try:
        logger.info("📈 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        prompt = build_clear_space_prompt()
        logger.info(f"📄 Промпт очистки: {prompt}")

        client = NanoBananaClient()
        result = await client.edit_image(
            image_urls=[image_url],
            prompt=prompt,
            output_format="png",
            image_size="auto",
        )

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке: {e}")
        return None


if __name__ == "__main__":
    # Для тестирования
    async def test():
        client = KieApiClient()
        logger.info("KieApiClient initialized")

    asyncio.run(test())
