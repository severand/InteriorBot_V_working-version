# bot/loader.py
# --- СОЗДАН: 2025-12-10 12:09 - Глобальный объект bot для вебхуков ---

"""Глобальный объект бота для использования в вебхуках"""

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import config

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
