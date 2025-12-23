# ========================================
# ФАЙЛ: bot/services/kie_api.py
# НАЗНАЧЕНИЕ: Интеграция с Kie.ai API (Nano Banana)
# ВЕРСИЯ: 3.4 (2025-12-23 23:20) - ИСПРАВЛЕНЫ ИМПОРТЫ ДЛЯ ТЕКСТОВЫХ ПРОМПТОВ
# АВТОР: Project Owner
# https://docs.kie.ai/market/google/nano-banana
# https://docs.kie.ai/market/google/nano-banana-edit
# ========================================
# [2025-12-23 15:30] ОБНОВЛЕНО: интеграция с translator.py
# [2025-12-23 23:02] ДОБАВЛЕНО: generate_interior_with_text_nano_banana() для поддержки текстовых промптов
# [2025-12-23 23:20] ИСПРАВЛЕНО: переместить импорт translate_to_english в начало файла

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
from services.translator import translate_to_english  # ✅ ИМПОРТ В НАЧАЛО!

logger = logging.getLogger(__name__)

# ========================================
# КОНФИГУРАЦИЯ KIE.AI (NANO BANANA)
# ========================================

KIE_API_BASE_URL = "https://api.kie.ai"
KIE_API_CREATE_ENDPOINT = "api/v1/jobs/createTask"
KIE_API_STATUS_ENDPOINT = "api/v1/jobs/recordInfo"  # ✅ ПРАВИЛЬНЫЙ ENDPOINT!
KIE_API_TIMEOUT = 300  # 5 минут

KIE_API_POLLING_INTERVAL = 3  # Проверять каждые 3 секунды
KIE_API_MAX_POLLS = 100  # Макс 100 попыток = 5 минут

# Модели
MODELS = {
    "image_generation": {
        "nano_banana": "google/nano-banana",
        "nano_banana_edit": "google/nano-banana-edit",
    },
}


class KieApiClient:
    """
    Клиент для работы с Kie.ai API (Nano Banana).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('KIE_API_KEY') or getattr(config, 'KIE_API_KEY', None)
        self.base_url = KIE_API_BASE_URL
        self.timeout = KIE_API_TIMEOUT

        if not self.api_key:
            logger.warning("⚠️  KIE_API_KEY не установлен")

    def _get_headers(self) -> Dict[str, str]:
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
        """Выполнить HTTP запрос к API."""
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
                    logger.error(f"❌ Неподдерживаемый метод: {method}")
                    return None

                logger.debug(f"📃 Status: {response.status_code}")

                if response.status_code not in [200, 201, 202]:
                    logger.error(f"❌ API ошибка: {response.status_code} - {response.text}")
                    return None

                return response.json()

        except httpx.TimeoutException:
            logger.error(f"❌ Таймаут (>{self.timeout}s)")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {e}")
            return None

    async def create_generation_task(
        self,
        model: str,
        input_data: Dict[str, Any],
        callback_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Создать задачу генерации.

        Returns:
            Task ID или None
        """
        data = {
            "model": model,
            "input": input_data,
        }

        if callback_url:
            data["callBackUrl"] = callback_url

        # 🔥 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ЗАПРОСА
        logger.info("")
        logger.info("="*70)
        logger.info("📄 KIE.AI REQUEST DETAILS")
        logger.info("="*70)
        logger.info(f"Model: {model}")
        logger.info(f"Image URLs: {input_data.get('image_urls', [])}")
        logger.info(f"Output Format: {input_data.get('output_format')}")
        logger.info(f"Image Size: {input_data.get('image_size')}")
        logger.info("")
        logger.info("📄 FULL PROMPT SENT TO KIE.AI:")
        logger.info("-"*70)
        prompt = input_data.get('prompt', '')
        # Логируем промпт построчно для читаемости
        for line in prompt.split('\n'):
            if line.strip():
                logger.info(f"   {line}")
        logger.info("-"*70)
        logger.info("="*70)
        logger.info("")

        logger.debug(f"📄 Отправка задачи...")
        response = await self._make_request("POST", KIE_API_CREATE_ENDPOINT, data)

        if response and response.get("code") == 200 and "data" in response:
            task_id = response["data"].get("taskId")
            logger.debug(f"✅ Task ID: {task_id}")
            return task_id

        logger.error(f"❌ Не удалось создать задачу: {response}")
        return None

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить статус и результат задачи через recordInfo.

        Returns:
            Dict с полями: state, resultJson, failMsg, etc.
        """
        params = {"taskId": task_id}
        response = await self._make_request("GET", KIE_API_STATUS_ENDPOINT, params=params)

        if response and response.get("code") == 200:
            return response.get("data", {})

        logger.error(f"❌ Не удалось получить статус: {response}")
        return None

    async def poll_task_result(
        self,
        task_id: str,
        max_polls: int = KIE_API_MAX_POLLS,
        poll_interval: int = KIE_API_POLLING_INTERVAL,
    ) -> Optional[str]:
        """
        Ожидать результат генерации (polling).

        Returns:
            URL результата или None
        """
        logger.info(f"⏳ Ожидание результата (Task: {task_id})...")

        for attempt in range(max_polls):
            status_data = await self.get_task_status(task_id)

            if not status_data:
                logger.debug(f"⏳ [{attempt+1}/{max_polls}] Нет данных, повтор через {poll_interval}s...")
                await asyncio.sleep(poll_interval)
                continue

            state = status_data.get("state")
            logger.debug(f"📈 [{attempt+1}/{max_polls}] State: {state}")

            # ✅ Успешная генерация
            if state == "success":
                result_json_str = status_data.get("resultJson")
                if result_json_str:
                    try:
                        result_json = json.loads(result_json_str)
                        result_urls = result_json.get("resultUrls", [])
                        
                        if result_urls and len(result_urls) > 0:
                            result_url = result_urls[0]
                            logger.info(f"✅ Результат готов: {result_url}")
                            return result_url
                        else:
                            logger.error("❌ resultUrls пустой")
                            return None
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Не удалось распарсить resultJson: {e}")
                        return None
                else:
                    logger.error("❌ resultJson отсутствует")
                    return None

            # ❌ Ошибка генерации
            elif state == "fail":
                fail_msg = status_data.get("failMsg", "Unknown error")
                logger.error(f"❌ Генерация провалилась: {fail_msg}")
                return None

            # ⏳ Генерация в процессе
            elif state in ["waiting", "queuing", "generating"]:
                elapsed = (attempt + 1) * poll_interval
                remaining = (max_polls - attempt - 1) * poll_interval
                logger.debug(f"⏳ [{attempt+1}/{max_polls}] State={state}, Elapsed: {elapsed}s, Remaining: {remaining}s")
                await asyncio.sleep(poll_interval)

            else:
                logger.warning(f"⚠️  Неизвестный state: {state}")
                await asyncio.sleep(poll_interval)

        logger.error(f"❌ Таймаут: результат не получен за {max_polls * poll_interval}s")
        return None


class NanoBananaClient(KieApiClient):
    """
    Клиент для Google Nano Banana через Kie.ai
    """

    async def text_to_image(
        self,
        prompt: str,
        output_format: str = "png",
        image_size: str = "16:9",
    ) -> Optional[str]:
        """Генерация изображения из текста."""
        logger.info("="*70)
        logger.info("🎈 ГЕНЕРАЦИЯ ТЕКСТ→ИЗОБРАЖЕНИЕ (Google Nano Banana)")
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

        task_id = await self.create_generation_task(
            model=MODELS["image_generation"]["nano_banana"],
            input_data=input_data,
        )

        if not task_id:
            return None

        result_url = await self.poll_task_result(task_id)
        return result_url

    async def edit_image(
        self,
        image_urls: List[str],
        prompt: str,
        output_format: str = "png",
        image_size: str = "auto",
    ) -> Optional[str]:
        """Редактирование изображения."""
        logger.info("="*70)
        logger.info("✍️  ПОВТОРНОЕ РЕНДЕРИНГ (Google Nano Banana Edit)")
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

        task_id = await self.create_generation_task(
            model=MODELS["image_generation"]["nano_banana_edit"],
            input_data=input_data,
        )

        if not task_id:
            return None

        result_url = await self.poll_task_result(task_id)
        return result_url


# ========================================
# ИНТЕГРИРОВАННЫЕ ФУНКЦИИ ДЛЯ БОТА
# ========================================

async def get_telegram_file_url(photo_file_id: str, bot_token: str) -> Optional[str]:
    """Получить URL файла из Telegram."""
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
        logger.error(f"❌ Ошибка при получении URL: {e}")
        return None


async def generate_interior_with_nano_banana(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
) -> Optional[str]:
    """
    Генерация дизайна интерьера через Nano Banana (Kie.ai).
    [2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод на английский
    [2025-12-23 23:02] ПРИМЕЧАНИЕ: Это использует предустановленный style (room + style from design_styles)
    """
    logger.info("="*70)
    logger.info("⚡ ГЕНЕРАЦИЯ ДИЗАЙНА [NANO BANANA via Kie.ai]")
    logger.info(f"   Комната: {room}")
    logger.info(f"   Стиль: {style}")
    logger.info("="*70)

    try:
        logger.info("📃 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # [2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод на английский
        prompt = await build_design_prompt(style, room, translate=True)
        logger.info(f"📄 Промпт сгенерирован и переведен (длина: {len(prompt)} символов)")

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


async def generate_interior_with_text_nano_banana(
    photo_file_id: str,
    user_prompt: str,
    bot_token: str,
    scene_type: str = "custom",
) -> Optional[str]:
    """
    Генерация дизайна с текстовым промптом от пользователя через Nano Banana.
    
    [2025-12-23 23:02] ДОБАВЛЕНО: Новая функция для поддержки текстовых промптов
    [2025-12-23 23:20] ИСПРАВЛЕНО: переместить импорт в начало файла
    
    Используется для:
    - "Другого помещения"
    - Экстерьера (дом, участок)
    - Любого кастомного текстового введения
    
    Args:
        photo_file_id: ID фото из Telegram
        user_prompt: Текстовый промпт от пользователя (ВАЖНО!)
        bot_token: Токен бота Telegram
        scene_type: Тип сцены (house_exterior, plot_exterior, other_room, custom)
    
    Returns:
        URL сгенерированного изображения или None
    """
    logger.info("="*70)
    logger.info("✍️  ГЕНЕРАЦИЯ С ТЕКСТОВЫМ ПРОМПТОМ [NANO BANANA via Kie.ai]")
    logger.info(f"   Сцена: {scene_type}")
    logger.info(f"   Пользовательский промпт: {user_prompt[:100]}...")
    logger.info("="*70)

    try:
        logger.info("📃 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # ✅ ИСПРАВЛЕНО: Импорт в начало файла, используем напрямую
        logger.info("📝 Перевод промпта на английский...")
        try:
            english_prompt = await translate_to_english(user_prompt)
            logger.info(f"✅ Промпт переведен на английский")
        except Exception as translate_error:
            logger.warning(f"⚠️  Не удалось перевести, используем оригинальный: {translate_error}")
            english_prompt = user_prompt

        # Добавляем контекст генерации к промпту
        full_prompt = f"Create a photorealistic {scene_type} design based on the user's request: {english_prompt}"
        
        logger.info(f"📄 Полный промпт для KIE.AI:")
        logger.info(f"   {full_prompt}")

        client = NanoBananaClient()
        result = await client.edit_image(
            image_urls=[image_url],
            prompt=full_prompt,
            output_format="png",
            image_size="auto",
        )

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации с текстовым промптом: {e}")
        return None


async def clear_space_with_kie(
    photo_file_id: str,
    bot_token: str,
) -> Optional[str]:
    """
    Очистка пространства через Nano Banana.
    [2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод
    """
    logger.info("="*70)
    logger.info("🧾 ОЧИСТКА ПРОСТРАНСТВА [Kie.ai]")
    logger.info("="*70)

    try:
        logger.info("📃 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # [2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод
        prompt = await build_clear_space_prompt(translate=True)
        logger.info(f"📄 Промпт очистки (переведен): {prompt}")

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
    async def test():
        client = KieApiClient()
        logger.info("KieApiClient initialized")

    asyncio.run(test())
