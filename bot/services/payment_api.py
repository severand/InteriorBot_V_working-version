# bot/services/payment_api.py
# --- СОЗДАН: 2025-12-10 - Полная интеграция YooKassa с официальным SDK ---

"""
Модуль для работы с платежами через YooKassa API.

Функционал:
- Создание платежей с метаданными для вебхуков
- Проверка статуса платежей
- Валидация вебхуков от YooKassa
- Обработка ошибок и логирование

Требования:
- pip install yookassa
- Переменные окружения: YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

Документация: https://yookassa.ru/developers/using-api/using-sdks
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

try:
    from yookassa import Payment, Configuration
    from yookassa.domain.notification import (
        WebhookNotificationEventType,
        WebhookNotificationFactory
    )

    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    logging.warning(
        "⚠️ Библиотека yookassa не установлена! "
        "Установите: pip install yookassa"
    )
BOT_LINK = os.getenv('BOT_LINK', 'Interior_Bot1_bot')

load_dotenv()
logger = logging.getLogger(__name__)

# Настройка YooKassa
if YOOKASSA_AVAILABLE:
    YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
    YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

    if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        logger.info("✅ YooKassa конфигурация загружена")
    else:
        logger.error(
            "❌ Отсутствуют YOOKASSA_SHOP_ID или YOOKASSA_SECRET_KEY в .env! "
            "Платежи работать НЕ будут!"
        )


def create_payment_yookassa(
    amount: int,
    user_id: int,
    tokens: int,
    description: str = "Покупка токенов",
    return_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Создание платежа в YooKassa.

    Args:
        amount: Сумма в рублях (целое число)
        user_id: ID пользователя Telegram
        tokens: Количество генераций для начисления
        description: Описание платежа
        return_url: URL возврата после оплаты (опционально)

    Returns:
        dict: Данные о платеже или None при ошибке
    """
    if not YOOKASSA_AVAILABLE:
        logger.error("❌ YooKassa SDK не установлен!")
        return None

    if amount <= 0 or tokens <= 0:
        raise ValueError(f"Некорректные параметры: amount={amount}, tokens={tokens}")

    try:
        # Формируем данные платежа
        payment_data = {
            "amount": {
                "value": f"{amount}.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/Interior_Bot1_bot?start=payment_success"

            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id),
                "tokens": str(tokens),
                "bot": "InteriorBot"
            },
            # ✅ ДОБАВЛЯЕМ ЧЕК (обязательно для 54-ФЗ)
            "receipt": {
                "customer": {
                    "email": f"user{user_id}@telegram.user"  # Фиктивный email
                },
                "items": [
                    {
                        "description": f"Генерации для дизайна интерьера ({tokens} шт.)",
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount}.00",
                            "currency": "RUB"
                        },
                        "vat_code": 1,  # НДС не облагается
                        "payment_mode": "full_payment",
                        "payment_subject": "service"
                    }
                ]
            }
        }

        logger.info(f"[YOOKASSA] Создание платежа: user_id={user_id}, amount={amount}₽, tokens={tokens}")

        # Создаем платеж через YooKassa SDK
        payment = Payment.create(payment_data)

        logger.info(f"[YOOKASSA] ✅ Платёж создан: {payment.id}, статус: {payment.status}")

        return {
            'id': payment.id,
            'amount': amount,
            'tokens': tokens,
            'confirmation_url': payment.confirmation.confirmation_url,
            'status': payment.status
        }

    except Exception as e:
        logger.error(f"[YOOKASSA] ❌ Ошибка создания платежа: {e}", exc_info=True)
        return None


def find_payment(payment_id: str) -> Optional[Dict[str, Any]]:
    """
    Получение информации о платеже из YooKassa.

    Args:
        payment_id: ID платежа в YooKassa

    Returns:
        dict: Данные о платеже или None при ошибке
            {
                'id': str - ID платежа,
                'status': str - Статус (pending/succeeded/canceled),
                'amount': int - Сумма в рублях,
                'metadata': dict - Метаданные (user_id, tokens)
            }
    """
    if not YOOKASSA_AVAILABLE:
        logger.error("❌ YooKassa SDK не установлен!")
        return None

    if not payment_id:
        logger.error("[YOOKASSA] payment_id не указан!")
        return None

    try:
        logger.info(f"[YOOKASSA] Проверка платежа: {payment_id}")

        # Получаем данные платежа
        payment = Payment.find_one(payment_id)

        if not payment:
            logger.warning(f"[YOOKASSA] Платёж {payment_id} не найден")
            return None

        logger.info(f"[YOOKASSA] Платёж {payment_id}: статус={payment.status}")

        return {
            'id': payment.id,
            'status': payment.status,
            'amount': int(float(payment.amount.value)),
            'metadata': payment.metadata or {}
        }

    except Exception as e:
        logger.error(f"[YOOKASSA] ❌ Ошибка получения платежа {payment_id}: {e}", exc_info=True)
        return None


def is_payment_successful(payment_id: str) -> bool:
    """
    Проверка успешности платежа.

    Args:
        payment_id: ID платежа в YooKassa

    Returns:
        bool: True если платёж успешен, False в противном случае
    """
    if not YOOKASSA_AVAILABLE:
        logger.error("❌ YooKassa SDK не установлен!")
        return False

    payment_data = find_payment(payment_id)

    if not payment_data:
        return False

    is_success = payment_data['status'] == "succeeded"

    if is_success:
        logger.info(f"[YOOKASSA] ✅ Платёж {payment_id} успешен")
    else:
        logger.info(f"[YOOKASSA] ⏳ Платёж {payment_id} в статусе: {payment_data['status']}")

    return is_success


def validate_webhook_signature(request_body: dict, notification_type: str = None) -> Optional[Dict[str, Any]]:
    """
    Валидация вебхука от YooKassa.

    Проверяет подпись уведомления и парсит данные платежа.
    Используется для защиты от поддельных вебхуков.

    Args:
        request_body: Тело HTTP-запроса от YooKassa (JSON)
        notification_type: Тип уведомления (опционально)

    Returns:
        dict: Данные платежа или None если валидация не прошла
            {
                'payment_id': str,
                'status': str,
                'user_id': int,
                'tokens': int,
                'amount': int
            }
    """
    if not YOOKASSA_AVAILABLE:
        logger.error("❌ YooKassa SDK не установлен!")
        return None

    try:
        # Парсим уведомление через фабрику YooKassa
        notification = WebhookNotificationFactory().create(request_body)

        # Получаем объект платежа
        payment = notification.object

        if notification.event != WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            logger.info(f"[WEBHOOK] Игнорируем событие: {notification.event}")
            return None

        # Извлекаем метаданные
        metadata = payment.metadata or {}

        result = {
            'payment_id': payment.id,
            'status': payment.status,
            'user_id': int(metadata.get('user_id', 0)),
            'tokens': int(metadata.get('tokens', 0)),
            'amount': int(float(payment.amount.value))
        }

        logger.info(
            f"[WEBHOOK] ✅ Валидация успешна: "
            f"payment_id={result['payment_id']}, "
            f"user_id={result['user_id']}, "
            f"amount={result['amount']}₽"
        )

        return result

    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ Ошибка валидации вебхука: {e}", exc_info=True)
        return None

# ============================================
# ИНСТРУКЦИЯ ПО НАСТРОЙКЕ
# ============================================
#
# 1. Установить библиотеку:
#    pip install yookassa
#
# 2. Добавить в .env:
#    YOOKASSA_SHOP_ID=ваш_shop_id
#    YOOKASSA_SECRET_KEY=ваш_secret_key
#
# 3. Настроить вебхук в личном кабинете YooKassa:
#    URL: https://your-domain.com/webhook/yookassa
#    События: payment.succeeded
#
# 4. Обновить return_url на реальный URL вашего бота
#
# 5. Протестировать на тестовых платежах:
#    https://yookassa.ru/developers/using-api/testing-and-going-live
#
# ============================================
