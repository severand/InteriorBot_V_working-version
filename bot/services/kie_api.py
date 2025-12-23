# ========================================
# ФАЙЛ: bot/services/kie_api.py
# НАЗНАЧЕНИЕ: Интеграция с Kie.ai API (Nano Banana)
# ВЕРСИЯ: 2.0 (2025-12-23) - ИСПРАВЛЕНЫ ENDPOINTS И ПАРАМЕТРЫ
# АВТОР: Project Owner
# ========================================
# ВАЖНО: Это АЛЬТЕРНАТИВА к Replicate
# Kie.ai предоставляет:
# - Flux Kontext API для изображений (редактирование)
# - 4O Image API для генерации/редактирования
# ========================================

import os
import logging
import httpx
import json
from typing import Optional, Dict, Any, List
from config import config

from services.design_styles import get_room_name, get_style_description, is_valid_room, is_valid_style
from services.prompts import build_design_prompt, build_clear_space_prompt

logger = logging.getLogger(__name__)

# ========================================
# КОНФИГУРАЦИЯ KIE.AI (NANO BANANA)
# ========================================

KIE_API_BASE_URL = "https://api.kie.ai"  # Базовый URL API
KIE_API_TIMEOUT = 300  # Таймаут 5 минут для генерации

# Модели для разных типов генерации
MODELS = {
    "image_generation": {
        "flux_kontext": "flux-kontext",      # Для изменения интерьера (основной)
        "4o_image": "4o-image",             # Для генерации и редактирования
        "nano_banana": "google/nano-banana", # Текст в изображение
        "nano_banana_edit": "google/nano-banana-edit",  # Редактирование изображений
    },
}


class KieApiClient:
    """
    Клиент для работы с Kie.ai API (Nano Banana).
    Предоставляет методы для генерации изображений и видео.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента.

        Args:
            api_key: API ключ Kie.ai (если не передан, берется из конфига)
        """
        self.api_key = api_key or os.getenv('KIE_API_KEY') or getattr(config, 'KIE_API_KEY', None)
        self.base_url = KIE_API_BASE_URL
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
                logger.debug(f"📤 {method} {url}")

                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    logger.error(f"❌ Неподдерживаемый HTTP метод: {method}")
                    return None

                logger.debug(f"📥 Status: {response.status_code}")

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

    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Получить информацию об аккаунте и балансе.

        Returns:
            Данные аккаунта или None
        """
        logger.info("📊 Получение информации об аккаунте...")
        return await self._make_request("GET", "account/info")

    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о модели.

        Args:
            model_id: ID модели

        Returns:
            Данные модели или None
        """
        logger.info(f"📋 Получение информации о модели: {model_id}")
        return await self._make_request("GET", f"models/{model_id}")

    async def check_credits(self) -> Optional[int]:
        """
        Проверить количество доступных кредитов.

        Returns:
            Количество кредитов или None
        """
        account_info = await self.get_account_info()
        if account_info and "credits" in account_info:
            credits = account_info["credits"]
            logger.info(f"💰 Доступно кредитов: {credits}")
            return credits
        logger.warning("⚠️ Не удалось получить информацию о кредитах")
        return None


class FluxKontextClient(KieApiClient):
    """
    Специализированный клиент для Flux Kontext API.
    Используется для context-aware редактирования изображений (интерьер).
    """

    async def generate_interior_design(
        self,
        image_url: str,
        prompt: str,
        strength: float = 0.7,
        steps: int = 25,
        guidance_scale: float = 7.5,
    ) -> Optional[str]:
        """
        Генерация дизайна интерьера с Flux Kontext.

        Args:
            image_url: URL исходного изображения
            prompt: Текстовый промпт с описанием желаемого дизайна
            strength: Сила воздействия (0.1-1.0, по умолчанию 0.7)
            steps: Количество шагов генерации (20-50)
            guidance_scale: Масштаб guidance (1.0-20.0)

        Returns:
            URL сгенерированного изображения или None
        """
        logger.info("="*70)
        logger.info("🎨 ГЕНЕРАЦИЯ С FLUX KONTEXT (Kie.ai)")
        logger.info(f"   Промпт: {prompt[:100]}...")
        logger.info(f"   Strength: {strength}")
        logger.info("="*70)

        if not self.api_key:
            logger.error("❌ KIE_API_KEY не установлен")
            return None

        data = {
            "model": MODELS["image_generation"]["flux_kontext"],
            "input": {
                "image_url": image_url,
                "prompt": prompt,
                "strength": strength,
                "steps": steps,
                "guidance_scale": guidance_scale,
                "output_format": "png",
            }
        }

        logger.info(f"⏳ Запуск Flux Kontext...")
        response = await self._make_request("POST", "generate", data)

        if response and "output" in response:
            result_url = response["output"]
            logger.info(f"✅ Генерация успешна: {result_url}")
            return result_url

        logger.error("❌ Ошибка генерации: неверный ответ API")
        return None


class GPT4OImageClient(KieApiClient):
    """
    Специализированный клиент для 4O Image API.
    Используется для свободной генерации и редактирования изображений.
    """

    async def generate_image(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "hd",
        n: int = 1,
    ) -> Optional[List[str]]:
        """
        Генерация изображения с GPT-4O.

        Args:
            prompt: Текстовый промпт
            image_url: URL исходного изображения (если нужна модификация)
            size: Размер изображения ("1024x1024", "1024x1792", "1792x1024")
            quality: Качество ("standard", "hd")
            n: Количество изображений для генерации (1-10)

        Returns:
            Список URL сгенерированных изображений или None
        """
        logger.info("="*70)
        logger.info("🖼️  ГЕНЕРАЦИЯ С 4O IMAGE (Kie.ai)")
        logger.info(f"   Промпт: {prompt[:100]}...")
        logger.info(f"   Размер: {size}")
        logger.info(f"   Качество: {quality}")
        logger.info("="*70)

        if not self.api_key:
            logger.error("❌ KIE_API_KEY не установлен")
            return None

        data = {
            "model": MODELS["image_generation"]["4o_image"],
            "input": {
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "n": n,
                "response_format": "url",
            }
        }

        if image_url:
            data["input"]["image_url"] = image_url

        logger.info(f"⏳ Запуск 4O Image...")
        response = await self._make_request("POST", "generate", data)

        if response and "data" in response:
            urls = [item["url"] for item in response["data"] if "url" in item]
            logger.info(f"✅ Генерация успешна: {len(urls)} изображений")
            return urls if urls else None

        logger.error("❌ Ошибка генерации: неверный ответ API")
        return None


class NanoBananaClient(KieApiClient):
    """
    Специализированный клиент для Google Nano Banana API.
    Используется для быстрой и дешевой генерации изображений.
    
    Модели:
    - google/nano-banana: текст → изображение
    - google/nano-banana-edit: редактирование изображений
    """

    async def text_to_image(
        self,
        prompt: str,
        output_format: str = "png",
        image_size: str = "1:1",  # 1:1, 9:16, 16:9, 3:4, 4:3, 3:2, 2:3, 5:4, 4:5, 21:9, auto
    ) -> Optional[str]:
        """
        Генерация изображения из текста (Nano Banana).

        Args:
            prompt: Текстовый промпт
            output_format: Формат выхода (png, jpeg)
            image_size: Размер изображения (соотношение сторон)

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

        data = {
            "model": MODELS["image_generation"]["nano_banana"],
            "input": {
                "prompt": prompt,
                "output_format": output_format,
                "image_size": image_size,
            }
        }

        logger.info(f"⏳ Запуск Nano Banana (Text→Image)...")
        response = await self._make_request("POST", "generate", data)

        if response and "output" in response:
            result_url = response["output"]
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
        Редактирование изображения (Nano Banana Edit).

        Args:
            image_urls: Список URL изображений для редактирования (до 10)
            prompt: Текстовый промпт с описанием изменений
            output_format: Формат выхода (png, jpeg)
            image_size: Размер изображения

        Returns:
            URL отредактированного изображения или None
        """
        logger.info("="*70)
        logger.info("✏️  РЕДАКТИРОВАНИЕ ИЗОБРАЖЕНИЯ (Google Nano Banana Edit)")
        logger.info(f"   Промпт: {prompt[:100]}...")
        logger.info(f"   Кол-во изображений: {len(image_urls)}")
        logger.info("="*70)

        if not self.api_key:
            logger.error("❌ KIE_API_KEY не установлен")
            return None

        data = {
            "model": MODELS["image_generation"]["nano_banana_edit"],
            "input": {
                "image_urls": image_urls,
                "prompt": prompt,
                "output_format": output_format,
                "image_size": image_size,
            }
        }

        logger.info(f"⏳ Запуск Nano Banana Edit...")
        response = await self._make_request("POST", "generate", data)

        if response and "output" in response:
            result_url = response["output"]
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
    (ПЕРЕИСПОЛЬЗУЕТСЯ из replicate_api.py)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                params={"file_id": photo_file_id}
            )

            if response.status_code != 200:
                logger.error(f"❗ Не удалось получить файл: {response.text}")
                return None

            result = response.json()
            if not result.get('ok'):
                logger.error(f"❗ API ошибка: {result}")
                return None

            file_path = result['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            logger.info(f"✅ Получен URL файла: {file_url}")
            return file_url

    except Exception as e:
        logger.error(f"❌ Ошибка при получении URL файла: {e}")
        return None


async def generate_interior_with_flux(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
    strength: float = 0.7,
) -> Optional[str]:
    """
    Генерация дизайна интерьера с помощью Flux Kontext (Kie.ai).

    Args:
        photo_file_id: ID фото из Telegram
        room: Тип комнаты
        style: Стиль дизайна
        bot_token: Токен бота
        strength: Сила воздействия (0.1-1.0)

    Returns:
        URL сгенерированного изображения или None
    """
    logger.info("="*70)
    logger.info("🎨 ГЕНЕРАЦИЯ ДИЗАЙНА [FLUX KONTEXT via Kie.ai]")
    logger.info(f"   Комната: {room} → {get_room_name(room)}")
    logger.info(f"   Стиль: {style}")
    logger.info(f"   Strength: {strength}")
    logger.info("="*70)

    if not is_valid_room(room):
        logger.warning(f"⚠️ Комната '{room}' не найдена в ROOM_NAMES")

    if not is_valid_style(style):
        logger.warning(f"⚠️ Стиль '{style}' не найден в STYLE_PROMPTS")

    try:
        logger.info("📸 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        prompt = build_design_prompt(style, room)
        logger.info(f"📄 Промпт: {prompt[:200]}...")

        client = FluxKontextClient()
        result = await client.generate_interior_design(
            image_url=image_url,
            prompt=prompt,
            strength=strength,
            steps=25,
            guidance_scale=7.5,
        )

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации: {e}")
        return None


async def generate_interior_with_gpt4o(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
) -> Optional[List[str]]:
    """
    Генерация дизайна интерьера с помощью 4O Image (Kie.ai).
    Более универсальный вариант, может работать и без исходного изображения.

    Args:
        photo_file_id: ID фото из Telegram
        room: Тип комнаты
        style: Стиль дизайна
        bot_token: Токен бота

    Returns:
        Список URL сгенерированных изображений или None
    """
    logger.info("="*70)
    logger.info("🖼️  ГЕНЕРАЦИЯ ДИЗАЙНА [4O IMAGE via Kie.ai]")
    logger.info(f"   Комната: {room} → {get_room_name(room)}")
    logger.info(f"   Стиль: {style}")
    logger.info("="*70)

    try:
        logger.info("📸 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        prompt = build_design_prompt(style, room)
        logger.info(f"📄 Промпт: {prompt[:200]}...")

        client = GPT4OImageClient()
        result = await client.generate_image(
            prompt=prompt,
            image_url=image_url,
            size="1024x1024",
            quality="hd",
            n=1,
        )

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации: {e}")
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
        logger.info("📸 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        prompt = build_design_prompt(style, room)
        logger.info(f"📄 Промпт: {prompt[:200]}...")

        client = NanoBananaClient()
        
        # Редактирование существующего изображения
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
    Очистка пространства от мебели используя Flux Kontext.
    АНАЛОГ: clear_space_image() из replicate_api.py

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
        logger.info("📸 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        prompt = build_clear_space_prompt()
        logger.info(f"📄 Промпт очистки: {prompt}")

        client = FluxKontextClient()
        result = await client.generate_interior_design(
            image_url=image_url,
            prompt=prompt,
            strength=0.9,  # Более сильное воздействие для очистки
            steps=30,
            guidance_scale=8.5,
        )

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке: {e}")
        return None


# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================

async def check_kie_api_health() -> bool:
    """
    Проверить доступность Kie.ai API и баланс.

    Returns:
        True если API доступен и есть кредиты
    """
    try:
        client = KieApiClient()
        credits = await client.check_credits()
        return credits is not None and credits > 0
    except Exception as e:
        logger.error(f"❌ Ошибка проверки API: {e}")
        return False


if __name__ == "__main__":
    # Для тестирования
    import asyncio

    async def test():
        client = KieApiClient()
        info = await client.get_account_info()
        logger.info(f"Account Info: {info}")

    asyncio.run(test())
