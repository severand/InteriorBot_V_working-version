"""
╔════════════════════════════════════════════════════════════════════════════════╗
║           ОБРАБОТЧИК ВНЕШНЭГО/ВНУТРЕННЕГО ОФОРМЛЕНИЯ             ║
║           (Creation Exterior/Interior - Old System Handlers)            ║
╚════════════════════════════════════════════════════════════════════════════════╝

📋 НАЗНАЧЕНИЕ МОДУЛЯ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Этот модуль сохраняет исторические обработчики для дизайна внешнего и внутреннего оформления.

📋 СТАТУС:
  🔲 IN PROGRESS - Модуль пока зарезервирован (все обработчики комментированы)
  🎫 В В3 архитектуре эти процессы обработаны другими модулями

📂 ТО ЧТО БЫЛО В ФАЙЛЕ (ОВ В3):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 ФУНКЦИЯ:
  • "Что в фото?" (what_is_in_photo) 
    → Определение: экстерьер или интерьер

  📸 ТОПО: выбор комнаты или типа фасада
    → room_choice, exterior_choice

  🎪 СТИЛЬ: выбор стиля оформления
    → style_choice

  🧰 ОЧИСТКА: Очистить поля
    → clear_space_confirm

  🎜 ГЕНЕРАЦИЯ: Отправка огпрашивания
    → Получение результата от API

  📄 ПОСЛЕ ГЕНЕРАЦИИ: Меню выбора действия
    → Данных но ничего по НОВОЙ архитектуре V3

═════════════════════════════════════════════════════════════════════════════

📄 ОЧЕРЕДНОСТЬ МИГРАЦИИ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ [V3 STRUCTURE] Новая архитектура:
  ├─ creation_main.py
  │  └─ Основной модуль (выбор режима → загружение фото)
  ├─ creation_new_design.py
  │  └─ Новые дизайны (комната → генерация)
  ├─ creation_extras.py
  │  └─ Отфильтрование неожиданных файлов
  └─ creation_exterior_interior.py ← (КОЭФФИЦИЕНТ НО ОСТАЛЯСЬ)
     └─ Очистить до ебитя

❌ [ОТМЕНЕНО] Обработчики что были в этом файле:
  • HANDLER: what_is_in_photo
  • HANDLER: select_room_or_exterior
  • HANDLER: select_style
  • HANDLER: clear_space_confirm
  • HANDLER: generate (style_choice → generation)
  • HANDLER: post_generation_menu
  
  Причина: В V3 архитектуре выборы режимов обработаны в 
  creation_main.py, creation_new_design.py и другие модули.

🎭 КОГДА ВОсстанавливать:
  Если нужны старые функции → копиэ историю репитория с датой этого коммита.

═════════════════════════════════════════════════════════════════════════════
"""

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
    get_uploading_photo_keyboard,
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


# ══════════════════════════════════════════════════════════════════════════════════
# 💰 [КОСТАВКА МОДУЛЯ] ЗАРЕЗЕРВОВАН НА ОЧИСТКУ
# ══════════════════════════════════════════════════════════════════════════════════
#
# 💰 ТЕКУЩИЙ СТАТУС:
#   🔲 IN PROGRESS - Все обработчики закомментированы
#   🎫 В В3 архитектуре эти трансформации обработаны другими модулями
#   ✅ При нужде - можно воссостановить с гита истории
#

logger.warning(
    """[DEPRECATED] creation_exterior_interior.py остаутся но не используется в В3. 
    Обработка распределена между:
    - creation_main.py
    - creation_new_design.py
    - другие модули
    """
)
