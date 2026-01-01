"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                   ОБРАБОТЧИК ДОПОЛНИТЕЛЬНЫХ ФАЙЛОВ                            ║
║                    (Creation Extras - Extra Files Handler)                     ║
╚════════════════════════════════════════════════════════════════════════════════╝

📋 НАЗНАЧЕНИЕ МОДУЛЯ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Этот модуль отвечает за обработку и фильтрацию файлов в неправильных FSM-состояниях.

🎯 ОСНОВНАЯ ЗАДАЧА:
  1. Позволить обработку файлов только в нужных состояниях (uploading_photo, 
     uploading_furniture, loading_facade_sample, text_input)
  2. Автоматически удалять файлы, отправленные пользователем в неправильные состояния
  3. Предотвращать лишние сообщения об ошибках - просто удалять файлы молча

🔍 КАК ЭТО РАБОТАЕТ:
  - Если пользователь в состоянии uploading_photo → его фото обработаются creation_main.py
  - Если пользователь отправит фото в другом состоянии → фото автоматически удалится
  - Тоже самое с текстом, видео, документами, аудио и т.д.

📂 СТРУКТУРА:
  ├─ VALID STATES (✅ Разрешённые): Pass-through обработчики
  │   └─ Здесь фото/текст передаются нужным обработчикам
  │
  └─ INVALID STATES (❌ Запрещённые): Silent delete обработчики  
      └─ Здесь файлы удаляются без сообщений об ошибке

⚙️ ПРИОРИТЕТ МАРШРУТИЗАЦИИ:
  Айограм обрабатывает маршруты в порядке регистрации, поэтому:
  1️⃣  Сначала идут VALID STATES (разрешённые)
  2️⃣  Потом идут INVALID STATES (запрещённые)
  Если состояние разрешено → функция pass и обработка идёт в creation_main.py
  Если состояние запрещено → файл удаляется молча
"""

import logging
import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from states.fsm import CreationStates

logger = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════════════════════════════════════════
# ✅ [РАЗРЕШЁННЫЕ СОСТОЯНИЯ] Фото/текст в нужном месте - пропускаем дальше
# ══════════════════════════════════════════════════════════════════════════════════
# 
# ЛОГИКА:
#   Если пользователь в одном из этих состояний и отправляет нужный тип файла →
#   мы НЕ обрабатываем здесь, а пропускаем (pass) дальше в другие обработчики.
#   Это нужно, чтобы предотвратить удаление файлов в INVALID STATES обработчиках.
#

@router.message(StateFilter(CreationStates.uploading_photo), F.photo)
async def handle_photo_in_uploading_photo_state(message: Message, state: FSMContext):
    """
    ✅ [SCREEN 2] Пользователь загружает фото в состоянии uploading_photo
    
    📌 КОГДА СРАБАТЫВАЕТ:
       Пользователь отправил фото, а его FSM-состояние = uploading_photo
    
    🎯 ЧТО ДЕЛАЕТ:
       Пропускает (pass) фото дальше - его обработает handler в creation_main.py
    
    💡 ПОЧЕМУ ВАЖНО:
       Без этого обработчика фото удалился бы в handle_unexpected_files().
       Так мы защищаем нужные файлы от удаления.
    """
    pass


@router.message(StateFilter(CreationStates.uploading_furniture), F.photo)
async def handle_photo_in_uploading_furniture_state(message: Message, state: FSMContext):
    """
    ✅ [SCREEN X] Пользователь загружает фото в состоянии uploading_furniture
    
    📌 КОГДА СРАБАТЫВАЕТ:
       Пользователь отправил фото для расстановки мебели
    
    🎯 ЧТО ДЕЛАЕТ:
       Пропускает фото дальше - его обработает специализированный handler
    
    💡 ПОЧЕМУ ВАЖНО:
       Режим "Расстановка мебели" использует свой обработчик фото.
    """
    pass


@router.message(StateFilter(CreationStates.loading_facade_sample), F.photo)
async def handle_photo_in_loading_facade_sample_state(message: Message, state: FSMContext):
    """
    ✅ [SCREEN X] Пользователь загружает фото в состоянии loading_facade_sample
    
    📌 КОГДА СРАБАТЫВАЕТ:
       Пользователь отправил фото для дизайна фасада
    
    🎯 ЧТО ДЕЛАЕТ:
       Пропускает фото дальше - его обработает специализированный handler
    
    💡 ПОЧЕМУ ВАЖНО:
       Режим "Дизайн фасада" использует свой обработчик фото.
    """
    pass


@router.message(StateFilter(CreationStates.text_input), F.text)
async def handle_text_in_text_input_state(message: Message, state: FSMContext):
    """
    ✅ [SCREEN X] Пользователь вводит текст в состоянии text_input
    
    📌 КОГДА СРАБАТЫВАЕТ:
       Пользователь отправил текстовое сообщение, а его FSM-состояние = text_input
    
    🎯 ЧТО ДЕЛАЕТ:
       Пропускает текст дальше - его обработает специализированный handler
    
    💡 ПОЧЕМУ ВАЖНО:
       Текстовый ввод (например, для промптов) требует специальной обработки.
       Без защиты текст был бы удалён в handle_unexpected_text().
    """
    pass


# ══════════════════════════════════════════════════════════════════════════════════
# ❌ [ЗАПРЕЩЁННЫЕ СОСТОЯНИЯ] Неожиданные файлы - МОЛЧА УДАЛЯЕМ
# ══════════════════════════════════════════════════════════════════════════════════
# 
# ЛОГИКА:
#   Если пользователь отправит файл в состоянии, где его обработать нельзя →
#   мы удаляем файл молча (без сообщений об ошибке).
#   Это сохраняет чат чистым и предотвращает спам.
#

@router.message(
    ~StateFilter(CreationStates.uploading_photo),
    ~StateFilter(CreationStates.uploading_furniture),
    ~StateFilter(CreationStates.loading_facade_sample),
    F.photo,
    F.media_group_id
)
async def handle_unexpected_media_group(message: Message, state: FSMContext):
    """
    ❌ [CLEANUP] Пользователь отправил АЛЬБОМ (группу фото) в неправильном состоянии
    
    📌 КОГДА СРАБАТЫВАЕТ:
       1. Пользователь отправил несколько фото сразу (альбом)
       2. Его текущее состояние НЕ uploading_photo, uploading_furniture или 
          loading_facade_sample
    
    🎯 ЧТО ДЕЛАЕТ:
       Удаляет все фото из альбома молча (без сообщений)
    
    💡 ЗАЧЕМ:
       - Альбомы могут заспамить чат мусорными сообщениями
       - Пользователь случайно отправил фото не в нужное время
       - Нет смысла показывать ошибку - просто удаляем
    
    ⚡ БЕЗОПАСНОСТЬ:
       Try-except ловит TelegramBadRequest если фото уже удалено
    """
    try:
        await message.delete()
        logger.info(f"🗑️ [ALBUM_DELETED] user={message.from_user.id}, "
                   f"state={await state.get_state()}")
    except TelegramBadRequest:
        # Фото уже удалено или бот не имеет прав
        pass
    except Exception as e:
        logger.error(f"❌ [ALBUM_DELETE_ERROR] {e}")


@router.message(
    ~StateFilter(CreationStates.uploading_photo),
    ~StateFilter(CreationStates.uploading_furniture),
    ~StateFilter(CreationStates.loading_facade_sample),
    F.photo | F.document | F.video | F.video_note | F.audio | F.voice | F.animation,
    ~F.media_group_id
)
async def handle_unexpected_files(message: Message, state: FSMContext):
    """
    ❌ [CLEANUP] Пользователь отправил ОДИНОЧНЫЙ ФАЙЛ в неправильном состоянии
    
    📌 КОГДА СРАБАТЫВАЕТ:
       1. Пользователь отправил файл (фото, видео, документ, аудио и т.д.)
       2. Это НЕ альбом (не media_group_id)
       3. Его текущее состояние НЕ uploading_photo, uploading_furniture или 
          loading_facade_sample
    
    🎯 ЧТО ДЕЛАЕТ:
       Удаляет файл молча (без сообщений об ошибке)
    
    💡 ЗАЧЕМ:
       - Пользователь случайно отправил файл
       - Файл не может быть обработан в текущем состоянии
       - Лучше удалить молча, чем показать ошибку
    
    📂 УДАЛЯЕМЫЕ ТИПЫ:
       • 🖼️  Фото (photo)
       • 📄 Документы (document)
       • 🎬 Видео (video)
       • 🎵 Аудио (audio, voice)
       • 🎞️  Анимация/GIF (animation)
       • 📹 Видеосообщение (video_note)
    
    ⚡ БЕЗОПАСНОСТЬ:
       Try-except ловит исключения при удалении
    """
    try:
        await message.delete()
        logger.info(f"🗑️ [FILE_DELETED] user={message.from_user.id}, "
                   f"state={await state.get_state()}")
    except TelegramBadRequest:
        # Файл уже удалён или бот не имеет прав
        pass
    except Exception as e:
        logger.error(f"❌ [FILE_DELETE_ERROR] {e}")


@router.message(
    ~StateFilter(CreationStates.text_input),
    F.text
)
async def handle_unexpected_text(message: Message, state: FSMContext):
    """
    ❌ [CLEANUP] Пользователь отправил ТЕКСТ в неправильном состоянии
    
    📌 КОГДА СРАБАТЫВАЕТ:
       1. Пользователь отправил текстовое сообщение
       2. Его FSM-состояние НЕ text_input
       3. Это текстовое сообщение не обработано выше
    
    🎯 ЧТО ДЕЛАЕТ:
       Удаляет текст молча
    
    💡 ЗАЧЕМ:
       - Текстовый ввод разрешен только в состоянии text_input
       - В других состояниях используются кнопки (callback queries)
       - Текст в неправильное время = ошибка пользователя → удаляем
    
    📝 ПРИМЕРЫ КОГДА СРАБАТЫВАЕТ:
       ❌ Пользователь написал сообщение вместо клика по кнопке
       ❌ Пользователь отправил текст на экране выбора комнаты
       ❌ Пользователь отправил сообщение в меню
    
    ⚡ БЕЗОПАСНОСТЬ:
       Try-except ловит исключения при удалении
    """
    try:
        await message.delete()
        logger.info(f"🗑️ [TEXT_DELETED] user={message.from_user.id}, "
                   f"state={await state.get_state()}")
    except TelegramBadRequest:
        # Текст уже удалён или бот не имеет прав
        pass
    except Exception as e:
        logger.error(f"❌ [TEXT_DELETE_ERROR] {e}")
