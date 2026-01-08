import asyncio
import logging
import html
import uuid
import time
import threading
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from database.db import db

from keyboards.inline import (
    get_room_choice_keyboard,
    get_choose_style_1_keyboard,
    get_choose_style_2_keyboard,
    get_post_generation_keyboard,
    get_payment_keyboard,
    get_main_menu_keyboard,
    get_uploading_photo_keyboard,
)

from services.api_fallback import smart_generate_interior

from states.fsm import CreationStates, WorkMode

from utils.texts import (
    ROOM_CHOICE_TEXT,
    CHOOSE_STYLE_TEXT,
    ERROR_INSUFFICIENT_BALANCE,
    ROOM_TYPES,
    STYLE_TYPES,
    UPLOADING_PHOTO_TEMPLATES,
)

from utils.helpers import add_balance_and_mode_to_text
from utils.navigation import edit_menu, show_main_menu

import aiohttp
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)
router = Router()

PHOTO_SEND_LOG = {}

# 🔍 ДИАГНОСТИКА
class DiagnosticTracker:
    """🔍 Отслеживание параллельных операций для выявления deadlock'ов"""
    def __init__(self):
        self.operations = {}  # {user_id: {'db_operations': 0, 'http_operations': 0, 'timestamp': ...}}
        self.lock = threading.Lock()
    
    def start_db_op(self, user_id: int, operation: str):
        with self.lock:
            if user_id not in self.operations:
                self.operations[user_id] = {
                    'db_operations': [],
                    'http_operations': [],
                    'started': datetime.now(),
                    'thread': threading.current_thread().name
                }
            self.operations[user_id]['db_operations'].append({
                'op': operation,
                'time': time.time(),
                'thread': threading.current_thread().name
            })
        logger.debug(f"🔄 [DB_START] user_id={user_id}, op={operation}, thread={threading.current_thread().name}")
    
    def end_db_op(self, user_id: int, operation: str):
        with self.lock:
            if user_id in self.operations:
                logger.debug(f"✅ [DB_END] user_id={user_id}, op={operation}")
    
    def start_http_op(self, user_id: int, operation: str):
        with self.lock:
            if user_id not in self.operations:
                self.operations[user_id] = {
                    'db_operations': [],
                    'http_operations': [],
                    'started': datetime.now(),
                    'thread': threading.current_thread().name
                }
            self.operations[user_id]['http_operations'].append({
                'op': operation,
                'time': time.time(),
                'thread': threading.current_thread().name
            })
        logger.debug(f"🌐 [HTTP_START] user_id={user_id}, op={operation}, thread={threading.current_thread().name}")
    
    def end_http_op(self, user_id: int, operation: str):
        with self.lock:
            if user_id in self.operations:
                logger.debug(f"✅ [HTTP_END] user_id={user_id}, op={operation}")
    
    def get_status(self, user_id: int) -> dict:
        with self.lock:
            if user_id in self.operations:
                return self.operations[user_id]
        return None

tracker = DiagnosticTracker()

def log_photo_send(user_id: int, method: str, message_id: int, request_id: str = None, operation: str = ""):
    """Логирует отправку фото для диагностики"""
    if user_id not in PHOTO_SEND_LOG:
        PHOTO_SEND_LOG[user_id] = []
    
    timestamp = datetime.now().isoformat()
    rid = request_id or str(uuid.uuid4())[:8]
    
    entry = {
        'timestamp': timestamp,
        'method': method,
        'message_id': message_id,
        'request_id': rid,
        'operation': operation
    }
    
    PHOTO_SEND_LOG[user_id].append(entry)
    
    logger.warning(
        f"📊 [PHOTO_LOG] user_id={user_id}, method={method}, msg_id={message_id}, "
        f"request_id={rid}, operation={operation}, timestamp={timestamp}"
    )


# 🔥 [SCREEN 4-5→6] ГЕНЕРАЦИЯ ДИЗАЙНА - ГЛАВНАЯ ФУНКЦИЯ
@router.callback_query(
    StateFilter(CreationStates.choose_style_1, CreationStates.choose_style_2),
    F.data.startswith("style_")
)
async def style_choice_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """
    🔥 [SCREEN 4-5→6] ГЕНЕРИРУЕТ ДИЗАЙН
    
    🔍 ДИАГНОСТИКА: Добавлено тщательное логирование всех этапов для выявления 
    истинной причины taim таймаута семафора (WinError 121)
    """
    style = callback.data.replace("style_", "", 1)
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    menu_message_id = callback.message.message_id
    request_id = str(uuid.uuid4())[:8]
    
    timestamp_start = time.time()

    logger.warning(f"🔍 [SCREEN 6] START: request_id={request_id}, user_id={user_id}, style={style}, thread={threading.current_thread().name}")

    await db.log_activity(user_id, f'style_{style}')

    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('selected_room')
    work_mode = data.get('work_mode')

    if not photo_id or not room:
        await callback.answer(
            "⚠️ Сессия устарела. Загрузите фото заново.",
            show_alert=True
        )
        await state.clear()
        await show_main_menu(callback, state, admins)
        return

    is_admin = user_id in admins
    if not is_admin:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await edit_menu(
                callback=callback,
                state=state,
                text=ERROR_INSUFFICIENT_BALANCE,
                keyboard=get_payment_keyboard(),
                show_balance=False,
                screen_code='no_balance'
            )
            return

    if not is_admin:
        logger.warning(f"🔍 [SCREEN 6] BEFORE decrease_balance - elapsed: {time.time() - timestamp_start:.2f}s")
        tracker.start_db_op(user_id, "decrease_balance")
        await db.decrease_balance(user_id)
        tracker.end_db_op(user_id, "decrease_balance")
        logger.warning(f"🔍 [SCREEN 6] AFTER decrease_balance - elapsed: {time.time() - timestamp_start:.2f}s")

    progress_msg = None
    current_msg = callback.message
    balance_text = await add_balance_and_mode_to_text(
        f"⚡ Генерирую {style} дизайн для {room}. Это может занять до 3 минут...",
        user_id,
        work_mode
    )
    
    try:
        if current_msg.photo:
            await callback.message.delete()
            logger.warning(f"📊 [SCREEN 6] Deleted media msg")
            
            progress_msg = await callback.message.answer(
                text=balance_text,
                parse_mode="HTML"
            )
            logger.warning(f"📊 [SCREEN 6] Progress msg sent")
            
        else:
            progress_msg = await callback.message.edit_text(
                text=balance_text,
                parse_mode="HTML"
            )
            logger.warning(f"📊 [SCREEN 6] Edited text menu to progress")
        
    except Exception as e:
        logger.warning(f"⚠️ [SCREEN 6] Failed to show progress: {e}")
        progress_msg = None
    
    await callback.answer()

    pro_settings = await db.get_user_pro_settings(user_id)
    use_pro = pro_settings.get('pro_mode', False)
    logger.info(f"🔧 PRO MODE для user_id={user_id}: {use_pro}")

    logger.warning(f"🔍 [SCREEN 6] BEFORE generate - elapsed: {time.time() - timestamp_start:.2f}s")
    tracker.start_http_op(user_id, "generate_interior")
    try:
        result_image_url = await smart_generate_interior(
            photo_id, room, style, bot_token, use_pro=use_pro
        )
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"[ERROR] Критическая ошибка генерации: {e}")
        result_image_url = None
        success = False
    tracker.end_http_op(user_id, "generate_interior")
    logger.warning(f"🔍 [SCREEN 6] AFTER generate - elapsed: {time.time() - timestamp_start:.2f}s")

    logger.warning(f"🔍 [SCREEN 6] BEFORE log_generation - elapsed: {time.time() - timestamp_start:.2f}s")
    tracker.start_db_op(user_id, "log_generation")
    await db.log_generation(
        user_id=user_id,
        room_type=room,
        style_type=style,
        operation_type='design',
        success=success
    )
    tracker.end_db_op(user_id, "log_generation")
    logger.warning(f"🔍 [SCREEN 6] AFTER log_generation - elapsed: {time.time() - timestamp_start:.2f}s")

    if result_image_url:
        balance = await db.get_balance(user_id)
        
        room_display = ROOM_TYPES.get(room, room.replace('_', ' ').title())
        style_display = STYLE_TYPES.get(style, style.replace('_', ' ').title())
        
        design_caption = f"""✨ <b>Идея для дизайна {room_display} в стиле {style_display} готова!</b>
        """
        
        menu_caption = f"""🎨 <b>Что дальше?
Есть 20 готовых стилей!</b>

Выберите действие:
🔄 Создать другой стиль.
🏠 Выбрать режим работы.

📊 Баланс: <b>{balance}</b> генераций | 🔧 Режим: <b>{work_mode}</b>"""
        
        photo_sent = False

        # ПОПЫТКА 1: Прямая отправка
        try:
            logger.warning(f"📊 [SCREEN 6] ATTEMPT 1: answer_photo - elapsed: {time.time() - timestamp_start:.2f}s")
            tracker.start_http_op(user_id, "answer_photo")
            
            photo_msg = await callback.message.answer_photo(
                photo=result_image_url,
                caption=design_caption,
                parse_mode="HTML",
            )
            
            tracker.end_http_op(user_id, "answer_photo")
            photo_sent = True
            logger.warning(f"📊 [SCREEN 6] SUCCESS: answer_photo - elapsed: {time.time() - timestamp_start:.2f}s")
            log_photo_send(user_id, "answer_photo", photo_msg.message_id, request_id, "style_choice")
            
            logger.warning(f"🔍 [SCREEN 6] BEFORE save_chat_menu (photo) - elapsed: {time.time() - timestamp_start:.2f}s")
            tracker.start_db_op(user_id, "save_chat_menu_photo")
            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
            tracker.end_db_op(user_id, "save_chat_menu_photo")
            logger.warning(f"🔍 [SCREEN 6] AFTER save_chat_menu (photo) - elapsed: {time.time() - timestamp_start:.2f}s")
            
            # 🔍 ДИАГНОСТИКА: Отправка меню
            try:
                logger.warning(f"🔍 [SCREEN 6] BEFORE answer (menu) - elapsed: {time.time() - timestamp_start:.2f}s")
                logger.warning(f"🔍 [SCREEN 6] Current thread: {threading.current_thread().name}, operations: {tracker.get_status(user_id)}")
                
                tracker.start_http_op(user_id, "answer_menu")
                menu_send_start = time.time()
                
                menu_msg = await callback.message.answer(
                    text=menu_caption,
                    parse_mode="HTML",
                    reply_markup=get_post_generation_keyboard()
                )
                
                menu_send_time = time.time() - menu_send_start
                tracker.end_http_op(user_id, "answer_menu")
                logger.warning(f"✅ [SCREEN 6] MENU SENT in {menu_send_time:.2f}s - elapsed: {time.time() - timestamp_start:.2f}s")
                
                logger.warning(f"🔍 [SCREEN 6] BEFORE save_chat_menu (menu) - elapsed: {time.time() - timestamp_start:.2f}s")
                tracker.start_db_op(user_id, "save_chat_menu_menu")
                await state.update_data(
                    photo_message_id=photo_msg.message_id, 
                    menu_message_id=menu_msg.message_id
                )
                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                tracker.end_db_op(user_id, "save_chat_menu_menu")
                logger.warning(f"🔍 [SCREEN 6] AFTER save_chat_menu (menu) - elapsed: {time.time() - timestamp_start:.2f}s")
                
            except Exception as menu_error:
                logger.error(f"⚠️ [SCREEN 6] Failed to send menu: {type(menu_error).__name__}: {menu_error}", exc_info=True)
                logger.warning(f"🔍 [SCREEN 6] Diagnostic - Operations status: {tracker.get_status(user_id)}")
            
            # Удаляем прогресс (независимо от результата меню)
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception:
                    pass

        except Exception as url_error:
            logger.warning(f"📊 [SCREEN 6] FAILED ATTEMPT 1: {url_error}")

            # ПОПЫТКА 2: Загрузка локально
            try:
                logger.warning(f"📊 [SCREEN 6] ATTEMPT 2: BufferedInputFile")

                async with aiohttp.ClientSession() as session:
                    async with session.get(result_image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()

                            photo_msg = await callback.message.answer_photo(
                                photo=BufferedInputFile(photo_data, filename="design.jpg"),
                                caption=design_caption,
                                parse_mode="HTML",
                            )
                            
                            photo_sent = True
                            logger.warning(f"📊 [SCREEN 6] SUCCESS: BufferedInputFile")
                            log_photo_send(user_id, "answer_photo_buffered", photo_msg.message_id, request_id, "style_choice")
                            
                            await db.save_chat_menu(chat_id, user_id, photo_msg.message_id, 'post_generation')
                            
                            # 🔍 ДИАГНОСТИКА: Отправка меню (attempt 2)
                            try:
                                logger.warning(f"🔍 [SCREEN 6] BEFORE answer (menu attempt 2) - elapsed: {time.time() - timestamp_start:.2f}s")
                                
                                tracker.start_http_op(user_id, "answer_menu_2")
                                menu_send_start = time.time()
                                
                                menu_msg = await callback.message.answer(
                                    text=menu_caption,
                                    parse_mode="HTML",
                                    reply_markup=get_post_generation_keyboard()
                                )
                                
                                menu_send_time = time.time() - menu_send_start
                                tracker.end_http_op(user_id, "answer_menu_2")
                                logger.warning(f"✅ [SCREEN 6] MENU SENT (attempt 2) in {menu_send_time:.2f}s")
                                
                                await state.update_data(
                                    photo_message_id=photo_msg.message_id, 
                                    menu_message_id=menu_msg.message_id
                                )
                                await db.save_chat_menu(chat_id, user_id, menu_msg.message_id, 'post_generation_menu')
                                
                            except Exception as menu_error:
                                logger.error(f"⚠️ [SCREEN 6] Failed to send menu (attempt 2): {type(menu_error).__name__}: {menu_error}", exc_info=True)
                                logger.warning(f"🔍 [SCREEN 6] Diagnostic - Operations status: {tracker.get_status(user_id)}")
                            
                            # Удаляем прогресс
                            if progress_msg:
                                try:
                                    await progress_msg.delete()
                                except Exception:
                                    pass

            except Exception as buffer_error:
                logger.error(f"📊 [SCREEN 6] FAILED ATTEMPT 2: {buffer_error}")

        # FALLBACK: Все попытки не сработали
        if not photo_sent:
            if not is_admin:
                await db.increase_balance(user_id, 1)
            
            logger.error(f"📊 [SCREEN 6] ALL ATTEMPTS FAILED")
            
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception:
                    pass
            
            await callback.message.answer(
                text="❌ Ошибка при отправке изображения. Баланс возвращен. Попробуйте ещё раз.",
                parse_mode="Markdown"
            )
            return

        # Переход на SCREEN 6
        await state.set_state(CreationStates.post_generation)

        logger.warning(f"📊 [SCREEN 6] GENERATION SUCCESS - total elapsed: {time.time() - timestamp_start:.2f}s")
        logger.info(f"[SCREEN 6] Generated for {room}/{style}, user_id={user_id}")

    else:
        # ОШИБКА ГЕНЕРАЦИИ
        if not is_admin:
            await db.increase_balance(user_id, 1)
        
        logger.error(f"📊 [SCREEN 6] GENERATION_FAILED")
        
        if progress_msg:
            try:
                await progress_msg.delete()
            except Exception:
                pass
        
        await callback.message.answer(
            text="❌ Ошибка генерации. Баланс возвращен. Попробуйте ещё раз.",
            parse_mode="Markdown"
        )
