# bot/database/db.py
# --- ОБНОВЛЕНО: 2026-01-09 01:25 - КРИТИЧНО: ДОБАВЛЕНЫ ДЕТАЛЬНЫЕ ЛОГИ ДЛЯ ФОТО И ФИКСЫ БД ---
# --- ОБНОВЛЕНО: 2026-01-09 01:09 - CRITICAL FIX: Удалены вложенные функции из init_db, исправлен lifecycle пула ---
# --- ОБНОВЛЕНО: 2026-01-03 18:56 - CLEAN: Убрано все миграции, таблица со всеми полями авто с начала ---
# --- ОБНОВЛЕНО: 2026-01-03 17:51 - КРИТИЧНО: Добавлены методы save_sample_photo и get_user_photos ---
# --- ОБНОВЛЕНО: 2026-01-02 22:42 - НОВОЕ: edit_old_menu_if_exists() - редактирование вместо удаления ---
# --- ОБНОВЛЕНО: 2026-01-02 21:40 - ОТКАТЫВАЕМ НЕПРАВИЛЬНЫЙ FIX - вернуть delete_message с правильной обработкой ошибок ---
# --- ОБНОВЛЕНО: 2026-01-02 11:53 - НОВОЕ: Добавлены методы save_user_photo/get_last_user_photo ---
# --- ОБНОВЛЕНО: 2025-12-30 23:59 - Добавлена функция increase_balance() для возврата баланса ---
# --- ОБНОВЛЕНО: 2025-12-24 20:25 - Добавлены методы get_setting/set_setting ---
# --- ОБНОВЛЕНО: 2025-12-24 12:35 - Добавлены методы для PRO MODE функционала ---
# --- ОБНОВЛЕНО: 2025-12-04 11:36 - Добавлены методы для уведомлений и источников трафика ---
# Добавлены методы get_user_recent_payments и get_referrer_info для расширенного поиска

import aiosqlite
import logging
import secrets
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from database.models import (
    # Таблицы
    CREATE_USERS_TABLE, CREATE_PAYMENTS_TABLE,
    CREATE_REFERRAL_EARNINGS_TABLE, CREATE_REFERRAL_EXCHANGES_TABLE,
    CREATE_REFERRAL_PAYOUTS_TABLE, CREATE_SETTINGS_TABLE,
    CREATE_GENERATIONS_TABLE, CREATE_USER_ACTIVITY_TABLE,
    CREATE_ADMIN_NOTIFICATIONS_TABLE, CREATE_USER_SOURCES_TABLE,
    CREATE_CHAT_MENUS_TABLE,
    CREATE_USER_PHOTOS_TABLE,
    CREATE_USER_SESSION_MODES_TABLE,
    DEFAULT_SETTINGS,
    # Пользователи
    GET_USER, CREATE_USER, UPDATE_BALANCE, DECREASE_BALANCE, GET_BALANCE, UPDATE_LAST_ACTIVITY,
    # Реферальные коды
    UPDATE_REFERRAL_CODE, GET_USER_BY_REFERRAL_CODE, UPDATE_REFERRED_BY, INCREMENT_REFERRALS_COUNT,
    # Платежи
    CREATE_PAYMENT, GET_PENDING_PAYMENT, UPDATE_PAYMENT_STATUS,
    # Генерации
    CREATE_GENERATION, INCREMENT_TOTAL_GENERATIONS,
    # Активность
    LOG_USER_ACTIVITY,
    # Реферальный баланс
    GET_REFERRAL_BALANCE, ADD_REFERRAL_BALANCE, DECREASE_REFERRAL_BALANCE, UPDATE_TOTAL_PAID,
    # Реферальные начисления
    CREATE_REFERRAL_EARNING, GET_USER_REFERRAL_EARNINGS,
    # Обмены
    CREATE_REFERRAL_EXCHANGE, GET_USER_EXCHANGES,
    # Выплаты
    CREATE_PAYOUT_REQUEST, GET_USER_PAYOUTS, GET_PENDING_PAYOUTS, UPDATE_PAYOUT_STATUS,
    # Реквизиты
    SET_PAYMENT_DETAILS, GET_PAYMENT_DETAILS,
    # Настройки
    GET_SETTING, SET_SETTING, GET_ALL_SETTINGS,
    # Единое меню
    SAVE_CHAT_MENU, GET_CHAT_MENU, DELETE_CHAT_MENU,
    # ФОТО
    SAVE_USER_PHOTO, GET_LAST_USER_PHOTO, SAVE_SAMPLE_PHOTO, GET_USER_PHOTOS,
    # PRO MODE
    GET_USER_PRO_SETTINGS, SET_USER_PRO_MODE, SET_PRO_ASPECT_RATIO, SET_PRO_RESOLUTION
)

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.pool = None

    async def init_pool(self) -> None:
        """🔧 Инициализация пула (1 соединение на весь бот)"""
        if self.pool is None:
            self.pool = await aiosqlite.connect(self.db_path)
            await self.pool.execute("PRAGMA journal_mode=WAL")
            await self.pool.execute("PRAGMA busy_timeout=5000")
            await self.pool.commit()
            logger.info("✅ Пул соединений создан")

    async def close_pool(self) -> None:
        """🔧 Закрытие пула при выключении бота"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("✅ Пул соединений закрыт")

    async def _get_db(self) -> aiosqlite.Connection:
        """🔧 Получить соединение (не закрывать его!)"""
        if self.pool is None:
            await self.init_pool()
        return self.pool

    async def init_db(self):
        """Инициализация таблиц БД"""
        db = await self._get_db()
        # Создаем все таблицы
        await db.execute(CREATE_USERS_TABLE)
        await db.execute(CREATE_PAYMENTS_TABLE)
        await db.execute(CREATE_GENERATIONS_TABLE)
        await db.execute(CREATE_USER_ACTIVITY_TABLE)
        await db.execute(CREATE_ADMIN_NOTIFICATIONS_TABLE)
        await db.execute(CREATE_USER_SOURCES_TABLE)
        await db.execute(CREATE_CHAT_MENUS_TABLE)
        await db.execute(CREATE_USER_PHOTOS_TABLE)  # Тут уже со всеми полями!
        await db.execute(CREATE_USER_SESSION_MODES_TABLE)
        await db.execute(CREATE_REFERRAL_EARNINGS_TABLE)
        await db.execute(CREATE_REFERRAL_EXCHANGES_TABLE)
        await db.execute(CREATE_REFERRAL_PAYOUTS_TABLE)
        await db.execute(CREATE_SETTINGS_TABLE)

        # Инициализируем дефолтные настройки
        for key, value in DEFAULT_SETTINGS.items():
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

        await db.commit()
        logger.info("✅ База данных инициализирована")

    # ===== 📸 МЕТОДЫ ДЛЯ ФОТО С ПОЛНЫМ ЛОГИРОВАНИЕМ (2026-01-09) =====

    async def save_main_photo(self, user_id: int, photo_id: str) -> bool:
        """
        📷 Сохранить ОСНОВНОЕ фото пользователя в БД (SCREEN 2).

        ⚠️ ВНИМАНИЕ: Основное фото считается постоянным!

        Параметры:
        - user_id: ID пользователя
        - photo_id: Telegram file_id фото

        Возвращает:
        - True если успешно сохранено, False при ошибке
        """
        db = await self._get_db()
        try:
            logger.debug(f"📷 [SAVE_MAIN] Начало сохранения основного фото для user_id={user_id}")
            logger.debug(f"   photo_id: {photo_id[:25]}..." if len(photo_id) > 25 else f"   photo_id: {photo_id}")
            
            await db.execute(SAVE_USER_PHOTO, (user_id, photo_id))
            await db.commit()
            
            logger.info(f"✅ [SAVE_MAIN] УСПЕШНО: Основное фото сохранено для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SAVE_MAIN] ОШИБКА save_main_photo user_id={user_id}: {e}", exc_info=True)
            return False

    async def save_sample_photo(self, user_id: int, photo_id: str) -> bool:
        """
        🎨 Сохранить ОБРАЗЕЦ фото пользователя в БД (SCREEN 10).

        ⚠️ ВАЖНО: Образец может быть заменен многократно для примерки!

        Параметры:
        - user_id: ID пользователя
        - photo_id: Telegram file_id фото

        Возвращает:
        - True если успешно сохранено, False при ошибке
        """
        db = await self._get_db()
        try:
            logger.debug(f"🎨 [SAVE_SAMPLE] Начало сохранения образца фото для user_id={user_id}")
            logger.debug(f"   photo_id: {photo_id[:25]}..." if len(photo_id) > 25 else f"   photo_id: {photo_id}")
            
            # ⚠️ КРИТИЧНЫЙ ФИХ [2026-01-09]: Проверяем и создаём запись если нужно
            async with db.execute(GET_USER_PHOTOS, (user_id,)) as cursor:
                existing_row = await cursor.fetchone()
            
            if not existing_row:
                logger.debug(f"   ➡️  Запись НЕ существует, создаём новую с sample_photo_id")
                # Создаём новую запись с sample_photo_id
                await db.execute(
                    "INSERT INTO user_photos (user_id, sample_photo_id, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (user_id, photo_id)
                )
            else:
                logger.debug(f"   ➡️  Запись СУЩЕСТВУЕТ, обновляем sample_photo_id")
                # Обновляем существующую запись
                await db.execute(
                    "UPDATE user_photos SET sample_photo_id = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (photo_id, user_id)
                )
            
            await db.commit()
            logger.info(f"✅ [SAVE_SAMPLE] УСПЕШНО: Образец фото сохранён для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SAVE_SAMPLE] ОШИБКА save_sample_photo user_id={user_id}: {e}", exc_info=True)
            return False

    async def get_user_photos(self, user_id: int) -> Dict[str, Optional[str]]:
        """
        📸 Получить ОБА фото пользователя одновременно!

        Возвращает:
        {
            'main_photo_id': 'file_id или None',
            'sample_photo_id': 'file_id или None'
        }
        """
        db = await self._get_db()
        try:
            logger.debug(f"📸 [GET_PHOTOS] Запрос обоих фото для user_id={user_id}")
            
            async with db.execute(GET_USER_PHOTOS, (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            if row:
                result = {
                    'main_photo_id': row[0],
                    'sample_photo_id': row[1]
                }
                logger.debug(f"✅ [GET_PHOTOS] Найдены оба фото для user_id={user_id}:")
                logger.debug(f"   main_photo_id: {row[0][:25] if row[0] else 'None'}..." if row[0] and len(row[0]) > 25 else f"   main_photo_id: {row[0]}")
                logger.debug(f"   sample_photo_id: {row[1][:25] if row[1] else 'None'}..." if row[1] and len(row[1]) > 25 else f"   sample_photo_id: {row[1]}")
                return result
            else:
                logger.warning(f"⚠️  [GET_PHOTOS] Фото НЕ НАЙДЕНЫ для user_id={user_id}, возвращаем None")
                return {
                    'main_photo_id': None,
                    'sample_photo_id': None
                }
        except Exception as e:
            logger.error(f"❌ [GET_PHOTOS] ОШИБКА get_user_photos user_id={user_id}: {e}", exc_info=True)
            return {
                'main_photo_id': None,
                'sample_photo_id': None
            }

    async def save_user_photo(self, user_id: int, photo_id: str) -> bool:
        """📄 Сохранить фото (скомонат для обратной совместимости)"""
        db = await self._get_db()
        try:
            logger.debug(f"📄 [SAVE_USER_PHOTO] Сохранение для user_id={user_id}")
            await db.execute(SAVE_USER_PHOTO, (user_id, photo_id))
            await db.commit()
            logger.info(f"✅ [SAVE_USER_PHOTO] УСПЕШНО: Фото сохранена для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SAVE_USER_PHOTO] ОШИБКА user_id={user_id}: {e}", exc_info=True)
            return False

    async def get_last_user_photo(self, user_id: int) -> Optional[str]:
        """📄 Получить последнюю фото (скомонат для обратной совместимости)"""
        db = await self._get_db()
        try:
            logger.debug(f"📄 [GET_LAST_PHOTO] Запрос для user_id={user_id}")
            
            async with db.execute(GET_LAST_USER_PHOTO, (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            if row:
                photo_id = row[0]
                logger.info(f"✅ [GET_LAST_PHOTO] Найдена фото для user_id={user_id}")
                logger.debug(f"   photo_id: {photo_id[:25]}..." if photo_id and len(photo_id) > 25 else f"   photo_id: {photo_id}")
                return photo_id
            else:
                logger.warning(f"⚠️  [GET_LAST_PHOTO] Фото НЕ НАЙДЕНА для user_id={user_id}")
                return None
        except Exception as e:
            logger.error(f"❌ [GET_LAST_PHOTO] ОШИБКА user_id={user_id}: {e}", exc_info=True)
            return None

    # ===== PRO MODE FUNCTIONS =====

    async def get_user_pro_settings(self, user_id: int) -> Dict[str, Any]:
        """Получить все параметры PRO режима пользователя"""
        db = await self._get_db()
        try:
            logger.debug(f"🔧 [PRO_SETTINGS] Запрос параметров PRO для user_id={user_id}")
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER_PRO_SETTINGS, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    result = {
                        'pro_mode': bool(row['pro_mode']),
                        'pro_aspect_ratio': row['pro_aspect_ratio'],
                        'pro_resolution': row['pro_resolution'],
                        'pro_mode_changed_at': row['pro_mode_changed_at']
                    }
                    logger.debug(f"✅ [PRO_SETTINGS] Найдены: mode={result['pro_mode']}, ratio={result['pro_aspect_ratio']}, res={result['pro_resolution']}")
                    return result
                logger.warning(f"⚠️  [PRO_SETTINGS] Нет записи PRO для user_id={user_id}, возвращаем дефолты")
                return {
                    'pro_mode': False,
                    'pro_aspect_ratio': '16:9',
                    'pro_resolution': '1K',
                    'pro_mode_changed_at': None
                }
        except Exception as e:
            logger.error(f"❌ [PRO_SETTINGS] ОШИБКА user_id={user_id}: {e}", exc_info=True)
            return {
                'pro_mode': False,
                'pro_aspect_ratio': '16:9',
                'pro_resolution': '1K',
                'pro_mode_changed_at': None
            }

    async def set_user_pro_mode(self, user_id: int, mode: bool) -> bool:
        """Установить режим (True = PRO, False = СТАНДАРТ)"""
        db = await self._get_db()
        try:
            mode_name = "PRO 🔧" if mode else "СТАНДАРТ 📋"
            logger.debug(f"🔧 [SET_PRO_MODE] Установка режима {mode_name} для user_id={user_id}")
            
            await db.execute(SET_USER_PRO_MODE, (1 if mode else 0, user_id))
            await db.commit()
            
            logger.info(f"✅ [SET_PRO_MODE] УСПЕШНО: Режим изменён на {mode_name} для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SET_PRO_MODE] ОШИБКА user_id={user_id}: {e}", exc_info=True)
            return False

    async def set_pro_aspect_ratio(self, user_id: int, ratio: str) -> bool:
        """Установить соотношение сторон для PRO режима"""
        valid_ratios = ['16:9', '4:3', '1:1', '9:16']
        if ratio not in valid_ratios:
            logger.warning(f"❌ [SET_ASPECT] Неверное соотношение {ratio} для user_id={user_id}. Допустимые: {valid_ratios}")
            return False

        db = await self._get_db()
        try:
            logger.debug(f"📐 [SET_ASPECT] Установка соотношения {ratio} для user_id={user_id}")
            await db.execute(SET_PRO_ASPECT_RATIO, (ratio, user_id))
            await db.commit()
            logger.info(f"✅ [SET_ASPECT] УСПЕШНО: Соотношение {ratio} установлено для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SET_ASPECT] ОШИБКА user_id={user_id}: {e}", exc_info=True)
            return False

    async def set_pro_resolution(self, user_id: int, resolution: str) -> bool:
        """Установить разрешение для PRO режима"""
        valid_resolutions = ['1K', '2K', '4K']
        if resolution not in valid_resolutions:
            logger.warning(f"❌ [SET_RES] Неверное разрешение {resolution} для user_id={user_id}. Допустимые: {valid_resolutions}")
            return False

        db = await self._get_db()
        try:
            logger.debug(f"📺 [SET_RES] Установка разрешения {resolution} для user_id={user_id}")
            await db.execute(SET_PRO_RESOLUTION, (resolution, user_id))
            await db.commit()
            logger.info(f"✅ [SET_RES] УСПЕШНО: Разрешение {resolution} установлено для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SET_RES] ОШИБКА user_id={user_id}: {e}", exc_info=True)
            return False

    # ===== CHAT MENUS =====

    async def save_chat_menu(self, chat_id: int, user_id: int, menu_message_id: int,
                             screen_code: str = 'main_menu') -> bool:
        """Сохранить/обновить menu"""
        db = await self._get_db()
        try:
            await db.execute(SAVE_CHAT_MENU,
                             (chat_id, user_id, menu_message_id, screen_code))
            await db.commit()
            logger.debug(f"📃 Saved menu: chat={chat_id}, msgid={menu_message_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка save_chat_menu: {e}")
            return False

    async def get_chat_menu(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные меню"""
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        async with db.execute(GET_CHAT_MENU, (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def delete_chat_menu(self, chat_id: int) -> bool:
        """Удалить запись о меню"""
        db = await self._get_db()
        try:
            await db.execute(DELETE_CHAT_MENU, (chat_id,))
            await db.commit()
            logger.debug(f"🗑️ Deleted menu")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка delete_chat_menu: {e}")
            return False

    async def edit_old_menu_if_exists(self, chat_id: int, user_id: int, new_text: str, new_keyboard, bot) -> Optional[
        int]:
        """✏️ Редактируем старое меню вместо удаления"""
        try:
            menu_data = await self.get_chat_menu(chat_id)
            if menu_data and menu_data.get('menu_message_id'):
                old_message_id = menu_data['menu_message_id']
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=old_message_id,
                        text=new_text,
                        reply_markup=new_keyboard
                    )
                    logger.info(f"✏️ Отредактировано")
                    await self.save_chat_menu(chat_id, user_id, old_message_id, 'main_menu')
                    return old_message_id
                except Exception as edit_error:
                    logger.warning(f"⚠️ Не удалось отредактировать: {edit_error}")
                    return None
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка в edit_old_menu_if_exists: {e}")
            return None

    async def delete_old_menu_if_exists(self, chat_id: int, bot) -> bool:
        """🗑️ Удалить старое меню"""
        try:
            menu_data = await self.get_chat_menu(chat_id)
            if menu_data and menu_data.get('menu_message_id'):
                old_menu_id = menu_data['menu_message_id']
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=old_menu_id)
                    logger.info(f"✅ Удалено")
                except Exception as e:
                    logger.debug(f"⚠️ Не удалось: {e}")
                await self.delete_chat_menu(chat_id)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False

    # ===== ПОЛЬЗОВАТЕЛИ =====

    async def create_user(self, user_id: int, username: str = None, referrer_code: str = None) -> bool:
        db = await self._get_db()
        try:
            async with db.execute(GET_USER, (user_id,)) as cursor:
                existing = await cursor.fetchone()
                if existing:
                    return False

            ref_code = secrets.token_urlsafe(8)
            initial_balance = int(await self.get_setting('welcome_bonus') or '3')
            await db.execute(CREATE_USER, (user_id, username, initial_balance, ref_code))

            if referrer_code:
                await self._process_referral(db, user_id, referrer_code)

            await db.commit()
            logger.info(f"Пользователь {user_id} создан")
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def _process_referral(self, db: aiosqlite.Connection, user_id: int, referrer_code: str):
        try:
            async with db.execute(GET_USER_BY_REFERRAL_CODE, (referrer_code,)) as cursor:
                referrer = await cursor.fetchone()
                if not referrer:
                    return

            referrer_id = referrer[0]
            await db.execute(UPDATE_REFERRED_BY, (referrer_id, user_id))
            await db.execute(INCREMENT_REFERRALS_COUNT, (referrer_id,))

            inviter_bonus = int(await self.get_setting('referral_bonus_inviter') or '2')
            invited_bonus = int(await self.get_setting('referral_bonus_invited') or '2')

            await db.execute(UPDATE_BALANCE, (inviter_bonus, referrer_id))
            await db.execute(UPDATE_BALANCE, (invited_bonus, user_id))
            logger.info(f"Реферал: {referrer_id} -> {user_id}")
        except Exception as e:
            logger.error(f"Ошибка: {e}")

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        async with db.execute(GET_USER, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def get_balance(self, user_id: int) -> int:
        db = await self._get_db()
        async with db.execute(GET_BALANCE, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def decrease_balance(self, user_id: int) -> bool:
        db = await self._get_db()
        try:
            await db.execute(DECREASE_BALANCE, (user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def increase_balance(self, user_id: int, tokens: int) -> bool:
        """Увеличить баланс на N токенов"""
        db = await self._get_db()
        try:
            await db.execute(UPDATE_BALANCE, (tokens, user_id))
            await db.commit()
            logger.info(f"✅ Возвращено {tokens}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False

    async def add_tokens(self, user_id: int, tokens: int) -> bool:
        db = await self._get_db()
        try:
            await db.execute(UPDATE_BALANCE, (tokens, user_id))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    # ===== ПЛАТЕЖИ =====

    async def create_payment(self, payment_id: str, user_id: int, amount: int, tokens: int) -> bool:
        db = await self._get_db()
        try:
            await db.execute(CREATE_PAYMENT, (user_id, payment_id, amount, tokens, 'pending'))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        db = await self._get_db()
        try:
            await db.execute(UPDATE_PAYMENT_STATUS, (status, payment_id))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE yookassa_payment_id = ?", (payment_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def get_last_pending_payment(self, user_id: int) -> Optional[Dict[str, Any]]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        async with db.execute(GET_PENDING_PAYMENT, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def set_payment_success(self, payment_id: str) -> bool:
        return await self.update_payment_status(payment_id, 'succeeded')

    # ===== ГЕНЕРАЦИИ =====

    async def log_generation(self, user_id: int, room_type: str, style_type: str,
                             operation_type: str = 'design', success: bool = True) -> bool:
        db = await self._get_db()
        try:
            await db.execute(CREATE_GENERATION, (user_id, room_type, style_type, operation_type, success))
            await db.execute(INCREMENT_TOTAL_GENERATIONS, (user_id,))
            await db.execute(UPDATE_LAST_ACTIVITY, (user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def get_total_generations(self) -> int:
        db = await self._get_db()
        async with db.execute("SELECT COUNT(*) FROM generations") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_generations_count(self, days: int = 1) -> int:
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        async with db.execute(
                "SELECT COUNT(*) FROM generations WHERE created_at >= ?",
                (date_threshold.isoformat(),)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_failed_generations_count(self, days: int = 1) -> int:
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        async with db.execute(
                "SELECT COUNT(*) FROM generations WHERE success = 0 AND created_at >= ?",
                (date_threshold.isoformat(),)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_conversion_rate(self) -> float:
        db = await self._get_db()
        async with db.execute(
                "SELECT AVG(total_generations) FROM users WHERE total_generations > 0"
        ) as cursor:
            row = await cursor.fetchone()
            return round(row[0], 2) if row and row[0] else 0.0

    async def get_popular_rooms(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = await self._get_db()
        async with db.execute(
                "SELECT room_type, COUNT(*) as count FROM generations GROUP BY room_type ORDER BY count DESC LIMIT ?",
                (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{'room_type': row[0], 'count': row[1]} for row in rows]

    async def get_popular_styles(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = await self._get_db()
        async with db.execute(
                "SELECT style_type, COUNT(*) as count FROM generations GROUP BY style_type ORDER BY count DESC LIMIT ?",
                (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{'style_type': row[0], 'count': row[1]} for row in rows]

    # ===== АКТИВНОСТЬ =====

    async def log_activity(self, user_id: int, action_type: str) -> bool:
        db = await self._get_db()
        try:
            await db.execute(LOG_USER_ACTIVITY, (user_id, action_type))
            await db.execute(UPDATE_LAST_ACTIVITY, (user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def get_active_users_count(self, days: int = 1) -> int:
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE created_at >= ?",
                (date_threshold.isoformat(),)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    # ===== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ =====

    async def get_total_users_count(self) -> int:
        db = await self._get_db()
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_setting(self, key: str) -> Optional[str]:
        db = await self._get_db()
        async with db.execute(GET_SETTING, (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def set_setting(self, key: str, value: str) -> bool:
        db = await self._get_db()
        try:
            await db.execute(SET_SETTING, (key, value))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def get_all_settings(self) -> Dict[str, str]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        async with db.execute(GET_ALL_SETTINGS) as cursor:
            rows = await cursor.fetchall()
            return {row['key']: row['value'] for row in rows}


# 💰 Получить общую выручку из успешных платежей
#===============================================
    async def get_total_revenue(self) -> int:

        db = await self._get_db()
        async with db.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded'"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# Количество новых пользователей за последние N дней
#========================================================
    async def get_new_users_count(self, days: int = 1) -> int:
        """👥 Количество новых пользователей за последние N дней"""
        from datetime import datetime, timedelta
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        async with db.execute(
                "SELECT COUNT(*) FROM users WHERE created_at >= ?",
                (date_threshold.isoformat(),)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


#Количество успешных платежей
#===============================
    async def get_successful_payments_count(self) -> int:
        """💳 Количество успешных платежей"""
        db = await self._get_db()
        async with db.execute(
                "SELECT COUNT(*) FROM payments WHERE status = 'succeeded'"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# Объект
db = Database()
