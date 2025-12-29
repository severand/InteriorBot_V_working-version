# --- ОБНОВЛЕНО: 2025-12-29 - Рефакторинг creation.py на 4 модуля ---
# --- ОБНОВЛЕНО: 2025-12-24 14:15 - Добавлена регистрация pro_mode router ---
# --- ОБНОВЛЕНО: 2025-12-10 12:03 - Добавлен веб-сервер для вебхуков YooKassa ---
# [2025-12-10 12:03] Добавлен запуск aiohttp веб-сервера для обработки вебхуков YooKassa
# [2025-12-07 10:43] Добавлен вызов миграции chat_menus при старте
# [2025-12-07 10:43] Добавлен await db.migrate_add_chat_menus_table() для создания таблицы единого меню
# [2025-11-22 11:35] Исправление: Уровень логирования изменен на DEBUG
# [2025-12-03] Добавлен роутер referral для реферальной системы

import asyncio
import logging
import aiosqlite  # В начало файла

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
#from aiohttp import web
from config import ADMIN_IDS
from config import config
from database.db import Database
from handlers import user_start, payment, referral, admin
from handlers import (
    router_main,
    router_new_design,
    router_exterior,
    router_extras,
)
from handlers.pro_mode import pro_mode_router
#from handlers.webhook import yookassa_webhook_handler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализируем базу данных
db = Database(db_path=config.DB_PATH)

# Initialize bot
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)


async def main():
    """Основная функция бота"""
    # Initialize database
    await db.init_db()
    logger.info("База данных инициализирована")

    # Initialize dispatcher
    dp = Dispatcher()

    # Register routers
    # Ордер регистрации вАЖНО!
    # 1. Админ
    # 2. Пользовательские команды
    # 3. Платежи
    # 4. Подтвердитель PRO режима
    # 5. Рефералы
    # 6. Основные сценарии создания дизайна
    # 7. ПОСЛЕДНО: Фаловые обработчики (катч-элс для всего остального)
    dp.include_routers(
        admin.router,  # ✅ АДМИН ПЕРВЫМ!
        user_start.router,
        payment.router,
        pro_mode_router,  # ✅ PRO MODE ROUTER (PHASE 3)
        referral.router,
        router_main,  # ✅ ОСНОВНОЕ (выбор режима + загрузка фото)
        router_new_design,  # ✅ NEW_DESIGN (режим срежим)
        router_exterior,  # ✅ EXTERIOR + ОЛД СИСТЕМА
        router_extras,  # ✅ ПОСЛЕДНЮЩИМ! Фаловые обработчики
    )

    # Передаем ADMIN_IDS и BOT_TOKEN в контекст
    dp["admins"] = ADMIN_IDS
    dp["bot_token"] = config.BOT_TOKEN

    # Настройка веб-сервера для вебхуков YooKassa
    #app = web.Application()
   # app.router.add_post('/webhook/yookassa', yookassa_webhook_handler)
    #runner = web.AppRunner(app)
    #await runner.setup()
    #site = web.TCPSite(runner, '0.0.0.0', 8080)
    #await site.start()
    #logger.info("Веб-сервер для вебхуков запущен на порту 8080")

    logger.info("Бот запущен")

    try:
        # Get bot info
        me = await bot.get_me()
        logger.info(f"Run polling for bot @{me.username} id={me.id} - '{me.first_name}'")

        # Start polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
