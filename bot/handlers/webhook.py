# bot/handlers/webhook.py
# --- ОБНОВЛЕН: 2025-12-10 - Полная интеграция с YooKassa вебхуками ---

"""
Обработчик вебхуков от YooKassa для автоматического зачисления токенов.

Функционал:
- Приём уведомлений о успешных платежах
- Валидация подписей от YooKassa
- Автоматическое начисление токенов
- Реферальные начисления
- Уведомления администраторов
"""

import logging
from aiogram import Router
from aiohttp import web
from services.payment_api import validate_webhook_signature
from database.db import db

logger = logging.getLogger(__name__)
router = Router()


async def _process_referral_commission(user_id: int, payment_id: str, amount: int, tokens: int):
    """
    Начисление реферальной комиссии при успешной оплате.

    Дублирует логику из payment.py для вебхука.
    """
    try:
        # 1. Проверяем включена ли реферальная программа
        enabled = await db.get_setting('referral_enabled')
        if str(enabled) != '1':
            logger.debug(f"[WEBHOOK][REFERRAL] Реферальная программа отключена")
            return

        # 2. Находим реферера
        user_data = await db.get_user_data(user_id)
        if not user_data:
            logger.debug(f"[WEBHOOK][REFERRAL] Данные пользователя {user_id} не найдены")
            return

        referrer_id = user_data.get('referred_by')
        if not referrer_id:
            logger.debug(f"[WEBHOOK][REFERRAL] Пользователь {user_id} не имеет реферера")
            return

        # 3. Рассчитываем комиссию
        commission_percent = int(await db.get_setting('referral_commission_percent') or '10')
        earnings = int(amount * commission_percent / 100)

        logger.info(
            f"[WEBHOOK][REFERRAL] Расчет: {amount} руб * {commission_percent}% = {earnings} руб"
        )

        # 4. Начисляем рубли на реферальный баланс
        await db.add_referral_balance(referrer_id, earnings)
        logger.info(
            f"[WEBHOOK][REFERRAL] Начислено {earnings} руб на реф. баланс реферера {referrer_id}"
        )

        # 5. Конвертируем в генерации и начисляем на основной баланс
        exchange_rate = int(await db.get_setting('referral_exchange_rate') or '29')
        tokens_to_give = earnings // exchange_rate

        logger.info(
            f"[WEBHOOK][REFERRAL] Конвертация: {earnings} руб = {tokens_to_give} генераций"
        )

        if tokens_to_give > 0:
            await db.add_tokens(referrer_id, tokens_to_give)
            logger.info(
                f"[WEBHOOK][REFERRAL] Начислено {tokens_to_give} генераций рефереру {referrer_id}"
            )

        # 6. Логируем операцию
        await db.log_referral_earning(
            referrer_id=referrer_id,
            referred_id=user_id,
            payment_id=payment_id,
            amount=amount,
            commission_percent=commission_percent,
            earnings=earnings,
            tokens=tokens_to_give
        )
        logger.info(f"[WEBHOOK][REFERRAL] ✅ Запись в referral_earnings создана")

    except Exception as e:
        logger.error(f"[WEBHOOK][REFERRAL] ❌ Ошибка обработки комиссии: {e}", exc_info=True)


async def yookassa_webhook_handler(request: web.Request) -> web.Response:
    """
    Обработчик вебхука от YooKassa.

    Принимает уведомления о успешных платежах и автоматически
    начисляет токены пользователям.

    URL: POST /webhook/yookassa
    """
    try:
        # 1. Получаем тело запроса
        request_body = await request.json()

        logger.info(f"[WEBHOOK] Получен запрос от YooKassa")
        logger.debug(f"[WEBHOOK] Данные: {request_body}")

        # 2. Валидируем подпись и парсим данные
        validated_data = validate_webhook_signature(request_body)

        if not validated_data:
            logger.warning("[WEBHOOK] ⚠️ Валидация вебхука не прошла!")
            return web.json_response(
                {"error": "Invalid signature"},
                status=400
            )

        payment_id = validated_data['payment_id']
        status = validated_data['status']
        user_id = validated_data['user_id']
        tokens = validated_data['tokens']
        amount = validated_data['amount']

        # 3. Проверяем что платёж успешен
        if status != 'succeeded':
            logger.info(f"[WEBHOOK] Платёж {payment_id} в статусе {status}, пропускаем")
            return web.json_response({"status": "ok"})

        # 4. Проверяем что платёж ещё не обработан
        existing_payment = await db.get_payment_by_yookassa_id(payment_id)

        if existing_payment and existing_payment.get('status') == 'succeeded':
            logger.warning(f"[WEBHOOK] Платёж {payment_id} уже обработан, пропускаем")
            return web.json_response({"status": "already_processed"})

        # 5. Обновляем статус платежа в БД
        await db.set_payment_success(payment_id)
        logger.info(f"[WEBHOOK] Статус платежа {payment_id} обновлён на 'succeeded'")

        # 6. Начисляем токены покупателю
        await db.add_tokens(user_id, tokens)
        logger.info(f"[WEBHOOK] ✅ Начислено {tokens} токенов пользователю {user_id}")

        # 7. Обрабатываем реферальную комиссию
        await _process_referral_commission(
            user_id=user_id,
            payment_id=payment_id,
            amount=amount,
            tokens=tokens
        )

        # 8. Уведомляем администраторов
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_new_payments")

            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        f"💳 **Новая оплата (webhook)**\n\n"
                        f"Пользователь: `{user_id}`\n"
                        f"Сумма: {amount} руб.\n"
                        f"Токенов: {tokens}\n"
                        f"ID платежа: `{payment_id}`",
                        parse_mode="Markdown"
                    )
                    logger.info(f"[WEBHOOK] Уведомление отправлено админу {admin_id}")
                except Exception as e:
                    logger.error(
                        f"[WEBHOOK] Ошибка отправки уведомления админу {admin_id}: {e}"
                    )
        except Exception as e:
            logger.error(f"[WEBHOOK] Ошибка при отправке уведомлений админам: {e}")

        # 9. Уведомляем пользователя о зачислении
        try:
            from loader import bot
            balance = await db.get_balance(user_id)

            await bot.send_message(
                user_id,
                f"✅ **Оплата успешна!**\n\n"
                f"Начислено: {tokens} генераций\n"
                f"Ваш баланс: {balance} генераций",
                parse_mode="Markdown"
            )
            logger.info(f"[WEBHOOK] Уведомление о зачислении отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(
                f"[WEBHOOK] Ошибка отправки уведомления пользователю {user_id}: {e}"
            )

        logger.info(f"[WEBHOOK] ✅ Платёж {payment_id} успешно обработан")

        return web.json_response({"status": "ok"})

    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ Критическая ошибка обработки вебхука: {e}", exc_info=True)
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


# Регистрация маршрута вебхука
def setup_webhook_routes(app: web.Application):
    """
    Регистрация маршрутов для вебхуков.

    Вызывается при инициализации веб-сервера.
    """
    app.router.add_post('/webhook/yookassa', yookassa_webhook_handler)
    logger.info("✅ Маршрут вебхука YooKassa зарегистрирован: POST /webhook/yookassa")
