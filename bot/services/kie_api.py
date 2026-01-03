# ========================================
# ФАЙЛ: bot/services/kie_api.py
# НАЗНАЧЕНИЕ: Интеграция с Kie.ai API (Nano Banana)
# ВЕРСИЯ: 3.7 (2026-01-02 21:04) - ENHANCEMENT: Добавить префикс промпта + лог финального промпта
# АВТОР: Project Owner
# https://docs.kie.ai/market/google/nano-banana
# https://docs.kie.ai/market/google/nano-banana-edit
# https://docs.kie.ai/market/google/pro-image-to-image [НОВОЕ 2025-12-24]
# ========================================
# [2025-12-23 15:30] ОБНОВЛЕНО: интеграция с translator.py
# [2025-12-23 23:02] ДОБАВЛЕНО: generate_interior_with_text_nano_banana() для поддержки текстовых промптов
# [2025-12-23 23:20] ИСПРАВЛЕНО: переместить импорт translate_to_english в начало файла
# [2025-12-24 08:18] ДОБАВЛЕНО: Поддержка KIE.AI PRO режима (nano-banana-pro)
# [2025-12-30 10:36] 🔙 REVERT: Отменить HOTFIX SSL проверку (проблема была в VPN, не в коде)
# [2026-01-02 20:55] 🔥 CRITICAL FIX: В текстовом редакторе отправлять ТОЛЬКО user_prompt БЕЗ добавления контекста
# [2026-01-02 21:04] ✨ ENHANCEMENT: Добавить префикс \"Create ultra-photorealistic image\" + детальный лог финального промпта

import os
import logging
import httpx
import json
import asyncio
import time
from typing import Optional, Dict, Any, List
from config import config
from config_kie import config_kie

from services.design_styles import get_room_name, get_style_description, is_valid_room, is_valid_style
from services.prompts import build_design_prompt, build_clear_space_prompt
from services.translator import translate_prompt_to_english as translate_to_english

logger = logging.getLogger(__name__)

# ========================================
# КОНФИГУРАЦИЯ KIE.AI (NANO BANANA)
# ========================================

KIE_API_BASE_URL = "https://api.kie.ai"
KIE_API_CREATE_ENDPOINT = "api/v1/jobs/createTask"
KIE_API_STATUS_ENDPOINT = "api/v1/jobs/recordInfo"  # ✅ ПРАВИЛЬНЫЙ ENDPOINT!
KIE_API_POLLING_INTERVAL = 3  # Проверять каждые 3 секунды
KIE_API_MAX_POLLS = 100  # Макс 100 попыток = 5 минут

# Модели
# [НОВОЕ 2025-12-24] ДОБАВЛЕНЫ PRO модели: nano-banana-pro
MODELS = {
    "image_generation": {
        "nano_banana": "google/nano-banana",
        "nano_banana_edit": "google/nano-banana-edit",
        "nano_banana_pro": "nano-banana-pro",  # [НОВОЕ 2025-12-24]
        "nano_banana_pro_edit": "nano-banana-pro",  # [НОВОЕ 2025-12-24]
    },
}

# [2026-01-02 21:04] ✨ ПРЕФИКС ДЛЯ ТЕКСТОВОГО РЕДАКТОРА
#TEXT_EDITOR_PROMPT_PREFIX = "Create ultra-photorealistic image. Apply the following prompt: "
TEXT_EDITOR_PROMPT_PREFIX = "Create an ultra-photorealistic image just like you'd find in a glossy magazine, preserving all the details and settings of the original photo. Follow the next prompt: "


class KieApiClient:
    """
    Клиент для работы с Kie.ai API (Nano Banana).
    [НОВОЕ 2025-12-24] Поддерживает новые PRO модели.
    """

    def __init__(self, api_key: Optional[str] = None, use_pro: bool = False):
        self.api_key = api_key or os.getenv('KIE_API_KEY') or getattr(config, 'KIE_API_KEY', None)
        self.base_url = KIE_API_BASE_URL
        self.use_pro = use_pro or config_kie.USE_PRO_MODEL  # [НОВОЕ 2025-12-24]
        self.timeout = config_kie.KIE_API_TIMEOUT  # динамический тайм-аут [НОВОЕ 2025-12-24]

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
            logger.error(f"❌ Тайм-аут (>{self.timeout}s)")
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
        Креатить задачу генерации.

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
        
        # [НОВОЕ 2025-12-24] Логирование режима
        mode_str = "🔝 PRO" if self.use_pro else "📋 BASE"
        logger.info(f"Mode: {mode_str}")
        
        if input_data.get('image_urls'):
            logger.info(f"Image URLs: {input_data.get('image_urls', [])}")
        elif input_data.get('image_input'):
            logger.info(f"Image Input: {input_data.get('image_input', [])}")
        
        logger.info(f"Output Format: {input_data.get('output_format')}")
        
        if input_data.get('image_size'):
            logger.info(f"Image Size (BASE): {input_data.get('image_size')}")
        if input_data.get('aspect_ratio'):
            logger.info(f"Aspect Ratio (PRO): {input_data.get('aspect_ratio')}")
        if input_data.get('resolution'):
            logger.info(f"Resolution (PRO): {input_data.get('resolution')}")
        
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

        logger.error(f"❌ Тайм-аут: результат не получен за {max_polls * poll_interval}s")
        return None


class NanoBananaClient(KieApiClient):
    """
    Клиент для Google Nano Banana через Kie.ai
    [НОВОЕ 2025-12-24] Поддерживает PRO модели.
    """

    async def text_to_image(
        self,
        prompt: str,
        output_format: str = "png",
        image_size: str = "16:9",
        use_pro: Optional[bool] = None,  # [НОВОЕ 2025-12-24]
        aspect_ratio: Optional[str] = None,  # [НОВОЕ 2025-12-24]
        resolution: Optional[str] = None,  # [НОВОЕ 2025-12-24]
    ) -> Optional[str]:
        """
        Генерация изображения из текста.
        [НОВОЕ 2025-12-24] Поддерживает PRO режим.
        """
        logger.info("="*70)
        
        # Установить режим
        use_pro_mode = use_pro if use_pro is not None else config_kie.USE_PRO_MODEL
        
        if use_pro_mode:
            logger.info("🔝 ГЕНЕРАЦИЯ ТЕКСТ→ИЗОБРАЖЕНИЕ (Google Nano Banana PRO)")
        else:
            logger.info("📋 ГЕНЕРАЦИЯ ТЕКСТ→ИЗОБРАЖЕНИЕ (Google Nano Banana BASE)")
        
        logger.info(f"   Промпт: {prompt[:100]}...")
        logger.info(f"   Размер: {aspect_ratio if use_pro_mode else image_size}")
        logger.info("="*70)

        if not self.api_key:
            logger.error("❌ KIE_API_KEY не установлен")
            return None

        # [НОВОЕ 2025-12-24] Условная логика для PRO и BASE режимов
        if use_pro_mode:
            input_data = {
                "prompt": prompt,
                "output_format": output_format,
                "aspect_ratio": aspect_ratio or config_kie.KIE_NANO_BANANA_PRO_ASPECT,
                "resolution": resolution or config_kie.KIE_NANO_BANANA_PRO_RESOLUTION,
            }
            model = MODELS["image_generation"]["nano_banana_pro"]
        else:
            input_data = {
                "prompt": prompt,
                "output_format": output_format,
                "image_size": image_size,
            }
            model = MODELS["image_generation"]["nano_banana"]

        task_id = await self.create_generation_task(
            model=model,
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
        use_pro: Optional[bool] = None,  # [НОВОЕ 2025-12-24]
        aspect_ratio: Optional[str] = None,  # [НОВОЕ 2025-12-24]
        resolution: Optional[str] = None,  # [НОВОЕ 2025-12-24]
    ) -> Optional[str]:
        """
        Редактирование изображения.
        [НОВОЕ 2025-12-24] Поддерживает PRO режим.
        """
        logger.info("="*70)
        
        # Установить режим
        use_pro_mode = use_pro if use_pro is not None else config_kie.USE_PRO_MODEL
        
        if use_pro_mode:
            logger.info("🔝 ПОВТОРНОЕ РЕНДЕРИНГ (Google Nano Banana PRO)")
        else:
            logger.info("📋 ПОВТОРНОЕ РЕНДЕРИНГ (Google Nano Banana BASE)")
        
        logger.info(f"   Промпт: {prompt[:100]}...")
        logger.info(f"   Кол-во изображений: {len(image_urls)}")
        logger.info("="*70)

        if not self.api_key:
            logger.error("❌ KIE_API_KEY не установлен")
            return None

        # [НОВОЕ 2025-12-24] КРИТИЧНОЕ: Ключи параметров разные!
        # BASE: image_urls, image_size
        # PRO: image_input, aspect_ratio, resolution
        if use_pro_mode:
            input_data = {
                "image_input": image_urls,  # ✅ ПРО: image_input (NOT image_urls!)
                "prompt": prompt,
                "output_format": output_format,
                "aspect_ratio": aspect_ratio or config_kie.KIE_NANO_BANANA_PRO_ASPECT,
                "resolution": resolution or config_kie.KIE_NANO_BANANA_PRO_RESOLUTION,
            }
            model = MODELS["image_generation"]["nano_banana_pro_edit"]
        else:
            input_data = {
                "image_urls": image_urls,  # ✅ BASE: image_urls
                "prompt": prompt,
                "output_format": output_format,
                "image_size": image_size,
            }
            model = MODELS["image_generation"]["nano_banana_edit"]

        task_id = await self.create_generation_task(
            model=model,
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
    """
    Получить URL файла из Telegram.
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
        logger.error(f"❌ Ошибка при получении URL: {e}")
        return None


async def generate_interior_with_nano_banana(
    photo_file_id: str,
    room: str,
    style: str,
    bot_token: str,
    use_pro: Optional[bool] = None,  # [НОВОЕ 2025-12-24]
) -> Optional[str]:
    """
    Генерация дизайна интерьера через Nano Banana (Kie.ai).
    [2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод на английский
    [2025-12-23 23:02] ПРИМЕЧАНИЕ: Это использует предустановленный style (room + style from design_styles)
    [НОВОЕ 2025-12-24] ДОБАВЛЕНА поддержка PRO режима
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

        # [НОВОЕ 2025-12-24] Передать режим PRO в клиент
        use_pro_mode = use_pro if use_pro is not None else config_kie.USE_PRO_MODEL
        
        client = NanoBananaClient(use_pro=use_pro_mode)
        result = await client.edit_image(
            image_urls=[image_url],
            prompt=prompt,
            output_format="png",
            image_size="auto",
            use_pro=use_pro_mode,  # [НОВОЕ 2025-12-24]
            aspect_ratio=config_kie.KIE_NANO_BANANA_PRO_ASPECT if use_pro_mode else None,
            resolution=config_kie.KIE_NANO_BANANA_PRO_RESOLUTION if use_pro_mode else None,
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
    use_pro: Optional[bool] = None,  # [НОВОЕ 2025-12-24]
) -> Optional[str]:
    """
    Генерация дизайна с текстовым промптом от пользователя через Nano Banana.
    
    [2025-12-23 23:02] ДОБАВЛЕНО: Новая функция для поддержки текстовых промптов
    [2025-12-23 23:20] ИСПРАВЛЕНО: переместить импорт в начало файла
    [НОВОЕ 2025-12-24] ДОБАВЛЕНА поддержка PRO режима
    [2026-01-02 20:55] 🔥 CRITICAL FIX: Отправлять ТОЛЬКО user_prompt БЕЗ добавления контекста
    [2026-01-02 21:04] ✨ ENHANCEMENT: Добавить префикс \"Create ultra-photorealistic image\" + детальный лог финального промпта
    
    Используется для:
    - ТЕКСТОВЫЙ РЕДАКТОР (edit_design режим) - user_prompt с префиксом!
    - \"Другого помещения\" - с контекстом scene_type
    - Экстерьера (дом, участок) - с контекстом scene_type
    
    Args:
        photo_file_id: ID фото из Telegram
        user_prompt: Текстовый промпт от пользователя (ВАЖНО!)
        bot_token: Токен бота Telegram
        scene_type: Тип сцены (НЕ используется в текстовом редакторе!)
        use_pro: Использовать PRO режим [НОВОЕ 2025-12-24]
    
    Returns:
        URL сгенерированного изображения или None
    """
    logger.info("="*70)
    logger.info("✏️  ГЕНЕРАЦИЯ С ТЕКСТОВЫМ ПРОМПТОМ [NANO BANANA via Kie.ai]")
    logger.info(f"   Пользовательский промпт: {user_prompt[:100]}...")
    logger.info("="*70)

    try:
        logger.info("📃 Получение фото из Telegram...")
        image_url = await get_telegram_file_url(photo_file_id, bot_token)

        if not image_url:
            logger.error("❌ Не удалось получить URL фото")
            return None

        # ✅ ИСПРАВЛЕНО: Импорт в начало файла, используем напрямую
        logger.info("📄 Перевод промпта на английский...")
        try:
            english_prompt = await translate_to_english(user_prompt)
            logger.info(f"✅ Промпт переведен на английский")
        except Exception as translate_error:
            logger.warning(f"⚠️  Не удалось перевести, используем оригинальный: {translate_error}")
            english_prompt = user_prompt

        # [2026-01-02 21:04] ✨ ENHANCEMENT: Добавить префикс для текстового редактора
        final_prompt = f"{TEXT_EDITOR_PROMPT_PREFIX}{english_prompt}"
        
        # [2026-01-02 21:04] 📋 ДЕТАЛЬНЫЙ ЛОГ ФИНАЛЬНОГО ПРОМПТА
        logger.info("")
        logger.info("="*70)
        logger.info("📋 ФИНАЛЬНЫЙ ПРОМПТ ДЛЯ МОДЕЛИ (ТЕКСТОВЫЙ РЕДАКТОР)")
        logger.info("="*70)
        logger.info("")
        logger.info("🔤 СТРУКТУРА ПРОМПТА:")
        logger.info(f"   [ПРЕФИКС] {TEXT_EDITOR_PROMPT_PREFIX}")
        logger.info(f"   [ПОЛЬЗОВАТЕЛЬСКИЙ ТЕКСТ] {english_prompt}")
        logger.info("")
        logger.info("📄 ПОЛНЫЙ ПРОМПТ (как получит модель):")
        logger.info("-"*70)
        for line in final_prompt.split('\n'):
            if line.strip():
                logger.info(f"   {line}")
        logger.info("-"*70)
        logger.info("")
        logger.info(f"✅ Длина промпта: {len(final_prompt)} символов")
        logger.info("="*70)
        logger.info("")

        # [НОВОЕ 2025-12-24] Передать режим PRO в клиент
        use_pro_mode = use_pro if use_pro is not None else config_kie.USE_PRO_MODEL
        
        client = NanoBananaClient(use_pro=use_pro_mode)
        result = await client.edit_image(
            image_urls=[image_url],
            prompt=final_prompt,  # ✅ ФИНАЛЬНЫЙ ПРОМПТ С ПРЕФИКСОМ!
            output_format="png",
            image_size="auto",
            use_pro=use_pro_mode,  # [НОВОЕ 2025-12-24]
            aspect_ratio=config_kie.KIE_NANO_BANANA_PRO_ASPECT if use_pro_mode else None,
            resolution=config_kie.KIE_NANO_BANANA_PRO_RESOLUTION if use_pro_mode else None,
        )

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации с текстовым промптом: {e}")
        return None


async def clear_space_with_kie(
    photo_file_id: str,
    bot_token: str,
    use_pro: Optional[bool] = None,  # [НОВОЕ 2025-12-24]
) -> Optional[str]:
    """
    Очистка пространства через Nano Banana.
    [2025-12-23 15:30] ОБНОВЛЕНО: автоматический перевод
    """
    logger.info("="*70)
    logger.info("📋 ОЧИСТКА ПРОСТРАНСТВА [Kie.ai]")
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

        # [НОВОЕ 2025-12-24] Передать режим PRO в клиент
        use_pro_mode = use_pro if use_pro is not None else config_kie.USE_PRO_MODEL
        
        client = NanoBananaClient(use_pro=use_pro_mode)
        result = await client.edit_image(
            image_urls=[image_url],
            prompt=prompt,
            output_format="png",
            image_size="auto",
            use_pro=use_pro_mode,  # [НОВОЕ 2025-12-24]
            aspect_ratio=config_kie.KIE_NANO_BANANA_PRO_ASPECT if use_pro_mode else None,
            resolution=config_kie.KIE_NANO_BANANA_PRO_RESOLUTION if use_pro_mode else None,
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
