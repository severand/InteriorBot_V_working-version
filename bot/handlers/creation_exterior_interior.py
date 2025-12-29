# bot/handlers/creation_exterior_interior.py
# ===== PHASE 3: EXTERIOR/INTERIOR + OLD SYSTEM =====
# [2025-12-29] НОВЫЙ ФАЙЛ: Часть 3 рефакторинга creation.py
# Содержит: Старая система (what_is_in_photo -> room_choice -> style_choice -> generation)
# + Clear Space, room_chosen, style_chosen

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message

from database.db import db

from keyboards.inline import (
    get_what_is_in_photo_keyboard,
    get_upload_photo_keyboard,
    get_room_keyboard,
    get_style_keyboard,
    get_payment_keyboard,
    get_post_generation_keyboard,
    get_clear_space_confirm_keyboard,
    get_main_menu_keyboard,
)

from services.api_fallback import smart_generate_with_text, smart_clear_space, smart_generate_interior

from states.fsm import CreationStates

from utils.texts import (
    WHAT_IS_IN_PHOTO_TEXT,
    ERROR_INSUFFICIENT_BALANCE,
    TOO_MANY_PHOTOS_TEXT,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()


# ===== OLD SYSTEM: PLACEHOLDER =====
# Настоящий файл ныне сконструян в минимальную версию
# для использования V3 роутеров
