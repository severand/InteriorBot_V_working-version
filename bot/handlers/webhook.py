# webhook

import logging
from aiogram import Router, F
from aiogram.types import Update

from database.db import db

logger = logging.getLogger(__name__)
router = Router()


async def handle_yookassa_webhook(update: dict):
    """
    Обработчик webhook от YooKassa
    Вызывается из main.py при получении POST-запроса
    """
    try:
        # Парсим данные платежа
        payment_data = update.get('object', {})
        payment_id = payment_data.get('id')
        status = payment_data.get('status')
        metadata = payment_data.get('metadata', {})

        logger.info(f"Webhook получен: payment_id={payment_id}, status={status}")

        # Обрабатываем только успешные платежи
        if status == 'succeeded':
            user_id = int(metadata.get('user_id', 0))
            tokens = int(metadata.get('tokens', 0))

            if user_id and tokens:
                # Обновляем статус платежа в БД
                await db.update_payment_status(payment_id, 'succeeded')

                # Добавляем токены пользователю
                await db.add_tokens(user_id, tokens)

                logger.info(f"✅ Платеж обработан: user_id={user_id}, tokens={tokens}")
            else:
                logger.warning(f"⚠️ Некорректные метаданные: user_id={user_id}, tokens={tokens}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return {"status": "error", "message": str(e)}
