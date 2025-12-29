import os
import logging
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image

os.environ["GOOGLE_API_KEY"] = "AIzaSyB1TRiDUhiiDTT0kUPWWpvkfOGnrOQec5E"

#   AIzaSyB1TRiDUhiiDTT0kUPWWpvkfOGnrOQec5E

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nano_banana_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def test_nano_banana_api(
    prompt: str,
    model_type: str = "pro",  # "basic" или "pro"
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    save_path: str = None
) -> dict:
    """
    Тестовая функция для проверки Nano Banana API

    Args:
        prompt: Текстовое описание для генерации
        model_type: "basic" (gemini-2.5-flash-image) или "pro" (gemini-3-pro-image-preview)
        aspect_ratio: Соотношение сторон (1:1, 16:9, 9:16, и т.д.)
        image_size: Размер изображения (1K, 2K, 4K)
        save_path: Путь для сохранения (если None, создастся автоматически)

    Returns:
        dict с результатами теста
    """

    result = {
        "success": False,
        "model": None,
        "prompt": prompt,
        "image_path": None,
        "generation_time": None,
        "error": None
    }

    try:
        # Проверка API-ключа
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("API-ключ не найден! Установите переменную GOOGLE_API_KEY")

        logger.info("=" * 50)
        logger.info(f"Начало теста Nano Banana API")
        logger.info(f"Модель: {model_type.upper()}")
        logger.info(f"Промпт: {prompt}")
        logger.info(f"Параметры: {aspect_ratio}, {image_size}")

        # Выбор модели
        if model_type.lower() == "basic":    #  'pro'
            model_name = "gemini-3-pro-image-preview"
        else:
            model_name = "gemini-2.5-flash-image"

        result["model"] = model_name
        logger.info(f"Используется модель: {model_name}")

        # Инициализация клиента
        client = genai.Client(api_key=api_key)
        logger.info("Клиент инициализирован")

        # Засекаем время
        start_time = datetime.now()
        logger.info("Отправка запроса на генерацию...")

        # Генерация изображения
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size
                ),
            )
        )

        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        result["generation_time"] = generation_time

        logger.info(f"Изображение сгенерировано за {generation_time:.2f} секунд")

        # Обработка ответа
        image_saved = False
        for part in response.parts:
            if part.text is not None:
                logger.info(f"Текстовый ответ: {part.text}")

            elif part.inline_data is not None:
                # Сохранение изображения
                if save_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = f"nano_banana_{model_type}_{timestamp}.png"

                image = part.as_image()
                image.save(save_path)
                result["image_path"] = save_path
                image_saved = True
                logger.info(f"Изображение сохранено: {save_path}")
                logger.info(f"Размер изображения: {image.size}")

        if image_saved:
            result["success"] = True
            logger.info("✓ Тест успешно пройден!")
        else:
            logger.warning("⚠ Изображение не было получено в ответе")
            result["error"] = "No image in response"

    except Exception as e:
        logger.error(f"✗ Ошибка при тестировании: {str(e)}")
        logger.exception("Полная информация об ошибке:")
        result["error"] = str(e)

    finally:
        logger.info("=" * 50)

    return result


def run_comparison_test(prompt: str):
    """
    Запуск сравнительного теста обеих моделей
    """
    logger.info("\n" + "=" * 70)
    logger.info("СРАВНИТЕЛЬНЫЙ ТЕСТ: Nano Banana Basic vs Pro")
    logger.info("=" * 70)

    results = {}

    # Тест базовой модели
    logger.info("\n>>> Тест Nano Banana BASIC")
    results["basic"] = test_nano_banana_api(
        prompt=prompt,
        model_type="basic",
        aspect_ratio="1:1",
        image_size="1K"
    )

    # Тест PRO модели
    logger.info("\n>>> Тест Nano Banana PRO")
    results["pro"] = test_nano_banana_api(
        prompt=prompt,
        model_type="pro",
        aspect_ratio="1:1",
        image_size="1K"
    )

    # Итоговая статистика
    logger.info("\n" + "=" * 70)
    logger.info("ИТОГОВАЯ СТАТИСТИКА")
    logger.info("=" * 70)

    for model_type, result in results.items():
        logger.info(f"\n{model_type.upper()}:")
        logger.info(f"  Успех: {result['success']}")
        logger.info(
            f"  Время генерации: {result['generation_time']:.2f}s" if result['generation_time'] else "  Время: N/A")
        logger.info(f"  Путь: {result['image_path']}" if result['image_path'] else "  Изображение не сохранено")
        if result['error']:
            logger.info(f"  Ошибка: {result['error']}")

    return results


# Пример использования:
if __name__ == "__main__":
    # Установите API-ключ перед запуском:
    # export GOOGLE_API_KEY="your_api_key_here"

    # Простой тест одной модели
    test_prompt = "Современный интерьер гостиной в скандинавском стиле с большими окнами"

    result = test_nano_banana_api(
        prompt=test_prompt,
        model_type="pro",
        aspect_ratio="16:9",
        image_size="2K"
    )

    print(f"\nРезультат: {result}")

    # Или сравнительный тест
    # comparison_results = run_comparison_test(test_prompt)
