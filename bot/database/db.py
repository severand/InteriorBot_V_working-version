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

# ===== ТАБЛИЦЫ ДЛЯ ПРОВЕРКИ ЦЕЛОСТНОСТИ =====
REQUIRED_TABLES = {
    'users': ['user_id', 'balance', 'referral_code', 'created_at'],
    'payments': ['id', 'user_id', 'yookassa_payment_id', 'status', 'created_at'],
    'generations': ['id', 'user_id', 'room_type', 'success', 'created_at'],
    'user_photos': ['user_id', 'photo_id', 'sample_photo_id'],
    'settings': ['key', 'value'],
    'user_activity': ['id', 'user_id', 'action_type', 'created_at'],
    'chat_menus': ['chat_id', 'user_id', 'menu_message_id'],
}

class DatabaseError(Exception):
    """Кастомная ошибка БД"""
    pass

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.pool = None
        self._initialized = False
        self._failed_operations: List[Dict[str, Any]] = []
        self._startup_errors: List[str] = []

    async def init_pool(self) -> None:
        """🔧 Инициализация пула (одно соединение на весь бот)"""
        if self.pool is not None:
            logger.warning("⚠️  Пул уже инициализирован, пропускаю")
            return

        try:
            self.pool = await aiosqlite.connect(self.db_path)
            await self.pool.execute("PRAGMA journal_mode=WAL")
            await self.pool.execute("PRAGMA busy_timeout=5000")
            await self.pool.execute("PRAGMA foreign_keys=ON")
            await self.pool.commit()
            logger.info(f"✅ Пул соединений создан (БД: {self.db_path})")
        except Exception as e:
            logger.error(f"❌ КРИТИЧНАЯ ОШИБКА при создании пула: {e}", exc_info=True)
            raise DatabaseError(f"Failed to initialize connection pool: {e}")

    async def close_pool(self) -> None:
        """🔧 Закрытие пула при выключении бота"""
        if self.pool:
            try:
                await self.pool.close()
                self.pool = None
                logger.info("✅ Пул соединений закрыт")
            except Exception as e:
                logger.error(f"❌ Ошибка при закрытии пула: {e}", exc_info=True)

    async def _get_db(self) -> aiosqlite.Connection:
        """🔧 Получить соединение (инициализируем если нужно)"""
        if self.pool is None:
            await self.init_pool()
        return self.pool

    async def init_db(self) -> bool:
        """
        🚀 ИНИЦИАЛИЗАЦИЯ БД С ПОЛНОЙ ВАЛИДАЦИЕЙ
        
        Этапы:
        1. Создание всех таблиц
        2. Инициализация дефолтных настроек
        3. Валидация целостности структуры
        4. Статистика БД
        5. Проверка критических индексов
        """
        db = await self._get_db()
        self._startup_errors = []  # Очищаем список ошибок
        
        try:
            logger.info("=" * 70)
            logger.info("🚀 ИНИЦИАЛИЗАЦИЯ БД НАЧАЛО")
            logger.info("=" * 70)
            
            # ===== ШАГ 1: СОЗДАНИЕ ТАБЛИЦ =====
            logger.info("\n📝 ШАГ 1: Создание таблиц...")
            tables_info = [
                ('users', CREATE_USERS_TABLE),
                ('payments', CREATE_PAYMENTS_TABLE),
                ('generations', CREATE_GENERATIONS_TABLE),
                ('user_activity', CREATE_USER_ACTIVITY_TABLE),
                ('admin_notifications', CREATE_ADMIN_NOTIFICATIONS_TABLE),
                ('user_sources', CREATE_USER_SOURCES_TABLE),
                ('chat_menus', CREATE_CHAT_MENUS_TABLE),
                ('user_photos', CREATE_USER_PHOTOS_TABLE),
                ('user_session_modes', CREATE_USER_SESSION_MODES_TABLE),
                ('referral_earnings', CREATE_REFERRAL_EARNINGS_TABLE),
                ('referral_exchanges', CREATE_REFERRAL_EXCHANGES_TABLE),
                ('referral_payouts', CREATE_REFERRAL_PAYOUTS_TABLE),
                ('settings', CREATE_SETTINGS_TABLE),
            ]
            
            created_count = 0
            for table_name, create_sql in tables_info:
                try:
                    await db.execute(create_sql)
                    created_count += 1
                    logger.debug(f"  ✓ Таблица '{table_name}' создана/проверена")
                except Exception as e:
                    error_msg = f"ОШИБКА создания таблицы '{table_name}': {e}"
                    logger.error(f"  ✗ {error_msg}")
                    self._startup_errors.append(error_msg)
            
            await db.commit()
            logger.info(f"✅ Таблицы: {created_count}/{len(tables_info)} успешно")
            
            # ===== ШАГ 2: ДЕФОЛТНЫЕ НАСТРОЙКИ =====
            logger.info("\n⚙️  ШАГ 2: Инициализация дефолтных настроек...")
            settings_added = 0
            for key, value in DEFAULT_SETTINGS.items():
                try:
                    await db.execute(
                        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                        (key, value)
                    )
                    settings_added += 1
                except Exception as e:
                    error_msg = f"ОШИБКА при добавлении настройки '{key}': {e}"
                    logger.error(f"  ✗ {error_msg}")
                    self._startup_errors.append(error_msg)
            
            await db.commit()
            logger.info(f"✅ Настройки: {settings_added}/{len(DEFAULT_SETTINGS)} добавлены")
            
            # ===== ШАГ 3: ВАЛИДАЦИЯ ЦЕЛОСТНОСТИ =====
            logger.info("\n🔍 ШАГ 3: Проверка целостности структуры...")
            integrity_ok = await self._validate_db_structure(db)
            if not integrity_ok:
                error_msg = "❌ КРИТИЧНО: Целостность БД нарушена!"
                logger.error(error_msg)
                self._startup_errors.append(error_msg)
                raise DatabaseError("Database structure integrity check failed")
            
            logger.info("✅ Целостность подтверждена")
            
            # ===== ШАГ 4: СТАТИСТИКА БД =====
            logger.info("\n📊 ШАГ 4: Статистика БД...")
            await self._log_db_stats(db)
            
            # ===== ШАГ 5: КРИТИЧЕСКИЕ ИНДЕКСЫ =====
            logger.info("\n📈 ШАГ 5: Проверка критических индексов...")
            await self._ensure_critical_indexes(db)
            
            logger.info("\n" + "=" * 70)
            logger.info("✅✅✅ БД УСПЕШНО ИНИЦИАЛИЗИРОВАНА ✅✅✅")
            logger.info("=" * 70)
            
            self._initialized = True
            return True
            
        except Exception as e:
            error_msg = f"❌ КРИТИЧНАЯ ОШИБКА ИНИЦИАЛИЗАЦИИ БД: {e}"
            logger.error(error_msg, exc_info=True)
            self._startup_errors.append(error_msg)
            self._initialized = False
            
            logger.error("\n" + "=" * 70)
            logger.error("❌❌❌ БД НЕ ИНИЦИАЛИЗИРОВАНА ❌❌❌")
            logger.error("Все ошибки:")
            for err in self._startup_errors:
                logger.error(f"  • {err}")
            logger.error("=" * 70)
            
            raise DatabaseError(f"Database initialization failed: {e}")

    async def _validate_db_structure(self, db: aiosqlite.Connection) -> bool:
        """
        🔍 ВАЛИДАЦИЯ СТРУКТУРЫ БД
        
        Проверяет:
        - Наличие всех таблиц
        - Наличие критических колонок
        - Типы данных
        """
        try:
            for table_name, required_columns in REQUIRED_TABLES.items():
                # Получаем информацию о таблице
                async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
                    rows = await cursor.fetchall()
                
                if not rows:
                    logger.error(f"  ✗ Таблица '{table_name}' НЕ СУЩЕСТВУЕТ!")
                    self._startup_errors.append(f"Missing table: {table_name}")
                    return False
                
                # Проверяем наличие требуемых колонок
                existing_columns = {row[1] for row in rows}
                missing_columns = set(required_columns) - existing_columns
                
                if missing_columns:
                    error_msg = f"Таблица '{table_name}' потеряла колонки: {', '.join(missing_columns)}"
                    logger.error(f"  ✗ {error_msg}")
                    self._startup_errors.append(error_msg)
                    return False
                
                logger.debug(f"  ✓ Таблица '{table_name}': все колонки на месте")
            
            logger.info("✅ Все таблицы и колонки присутствуют")
            return True
            
        except Exception as e:
            error_msg = f"Ошибка при валидации: {e}"
            logger.error(error_msg, exc_info=True)
            self._startup_errors.append(error_msg)
            return False

    async def _log_db_stats(self, db: aiosqlite.Connection) -> None:
        """
        📊 СТАТИСТИКА БД
        
        Выводит количество записей в ключевых таблицах
        """
        try:
            stats = {}
            for table_name in ['users', 'payments', 'generations', 'user_activity', 'user_photos']:
                try:
                    async with db.execute(f"SELECT COUNT(*) FROM {table_name}") as cursor:
                        count = (await cursor.fetchone())[0]
                        stats[table_name] = count
                except Exception as e:
                    logger.warning(f"  ⚠️  Не удалось подсчитать {table_name}: {e}")
                    stats[table_name] = "?"
            
            logger.info("  📋 Статистика таблиц:")
            for table_name, count in stats.items():
                if isinstance(count, int):
                    logger.info(f"     • {table_name:20s}: {count:>8,} записей")
                else:
                    logger.info(f"     • {table_name:20s}: {count}")
                    
        except Exception as e:
            logger.warning(f"⚠️  Ошибка при сборе статистики: {e}")

    async def _ensure_critical_indexes(self, db: aiosqlite.Connection) -> None:
        """
        📈 СОЗДАНИЕ КРИТИЧЕСКИХ ИНДЕКСОВ
        
        Ускоряет часто выполняемые запросы
        """
        try:
            indexes = [
                ("idx_users_referral_code", "CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)"),
                ("idx_payments_user_id", "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)"),
                ("idx_payments_status", "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)"),
                ("idx_generations_user_id", "CREATE INDEX IF NOT EXISTS idx_generations_user_id ON generations(user_id)"),
                ("idx_user_activity_user_id", "CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id)"),
            ]
            
            created = 0
            for idx_name, idx_sql in indexes:
                try:
                    await db.execute(idx_sql)
                    created += 1
                    logger.debug(f"  ✓ Индекс '{idx_name}' создан/проверен")
                except Exception as e:
                    logger.debug(f"  ⚠️  Индекс '{idx_name}': {e}")
            
            await db.commit()
            logger.info(f"✅ Индексы: {created}/{len(indexes)} оптимизированы")
            
        except Exception as e:
            logger.warning(f"⚠️  Ошибка при создании индексов: {e}")

    # ===== 📸 МЕТОДЫ ДЛЯ ФОТО С ПОЛНЫМ ЛОГИРОВАНИЕМ =====

    async def save_main_photo(self, user_id: int, photo_id: str) -> bool:
        """
        📷 Сохранить ОСНОВНОЕ фото пользователя (SCREEN 2)
        
        Возвращает:
        - True если успешно
        - False при ошибке (ошибка логируется)
        """
        db = await self._get_db()
        try:
            logger.debug(f"📷 [SAVE_MAIN_PHOTO] user_id={user_id}")
            logger.debug(f"   photo_id: {photo_id[:30]}..." if len(photo_id) > 30 else f"   photo_id: {photo_id}")
            
            await db.execute(SAVE_USER_PHOTO, (user_id, photo_id))
            await db.commit()
            
            logger.info(f"✅ [SAVE_MAIN_PHOTO] Основное фото сохранено для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SAVE_MAIN_PHOTO] user_id={user_id}: {e}", exc_info=True)
            self._failed_operations.append({
                'timestamp': datetime.now().isoformat(),
                'operation': 'save_main_photo',
                'user_id': user_id,
                'error': str(e)
            })
            return False

    async def save_sample_photo(self, user_id: int, photo_id: str) -> bool:
        """
        🎨 Сохранить ОБРАЗЕЦ фото пользователя (SCREEN 10)
        
        Возвращает:
        - True если успешно
        - False при ошибке
        """
        db = await self._get_db()
        try:
            logger.debug(f"🎨 [SAVE_SAMPLE_PHOTO] user_id={user_id}")
            logger.debug(f"   photo_id: {photo_id[:30]}..." if len(photo_id) > 30 else f"   photo_id: {photo_id}")
            
            # Проверяем существует ли запись
            async with db.execute(GET_USER_PHOTOS, (user_id,)) as cursor:
                existing = await cursor.fetchone()
            
            if not existing:
                logger.debug(f"   ➡️  Запись НЕ существует, создаём новую")
                await db.execute(
                    "INSERT INTO user_photos (user_id, sample_photo_id, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (user_id, photo_id)
                )
            else:
                logger.debug(f"   ➡️  Запись СУЩЕСТВУЕТ, обновляем")
                await db.execute(
                    "UPDATE user_photos SET sample_photo_id = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (photo_id, user_id)
                )
            
            await db.commit()
            logger.info(f"✅ [SAVE_SAMPLE_PHOTO] Образец сохранён для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SAVE_SAMPLE_PHOTO] user_id={user_id}: {e}", exc_info=True)
            self._failed_operations.append({
                'timestamp': datetime.now().isoformat(),
                'operation': 'save_sample_photo',
                'user_id': user_id,
                'error': str(e)
            })
            return False

    async def get_user_photos(self, user_id: int) -> Dict[str, Optional[str]]:
        """
        📸 Получить ОБА фото пользователя сразу
        
        Возвращает:
        - {'main_photo_id': '...', 'sample_photo_id': '...'}
        - В полях None если фото не загружено
        """
        db = await self._get_db()
        try:
            logger.debug(f"📸 [GET_USER_PHOTOS] user_id={user_id}")
            
            async with db.execute(GET_USER_PHOTOS, (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            if row:
                result = {
                    'main_photo_id': row[0],
                    'sample_photo_id': row[1]
                }
                logger.debug(f"✅ [GET_USER_PHOTOS] Найдены для user_id={user_id}")
                logger.debug(f"   main: {row[0][:20]}..." if row[0] and len(str(row[0])) > 20 else f"   main: {row[0]}")
                logger.debug(f"   sample: {row[1][:20]}..." if row[1] and len(str(row[1])) > 20 else f"   sample: {row[1]}")
                return result
            
            logger.debug(f"⚠️  [GET_USER_PHOTOS] НЕ найдены для user_id={user_id}")
            return {'main_photo_id': None, 'sample_photo_id': None}
            
        except Exception as e:
            logger.error(f"❌ [GET_USER_PHOTOS] user_id={user_id}: {e}", exc_info=True)
            return {'main_photo_id': None, 'sample_photo_id': None}

    async def save_user_photo(self, user_id: int, photo_id: str) -> bool:
        """📄 Сохранить фото (совместимость)"""
        db = await self._get_db()
        try:
            await db.execute(SAVE_USER_PHOTO, (user_id, photo_id))
            await db.commit()
            logger.info(f"✅ [SAVE_USER_PHOTO] Фото сохранена для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ [SAVE_USER_PHOTO] user_id={user_id}: {e}", exc_info=True)
            return False

    async def get_last_user_photo(self, user_id: int) -> Optional[str]:
        """📄 Получить последнюю фото (совместимость)"""
        db = await self._get_db()
        try:
            async with db.execute(GET_LAST_USER_PHOTO, (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            if row:
                logger.debug(f"✅ [GET_LAST_USER_PHOTO] Найдена для user_id={user_id}")
                return row[0]
            
            logger.debug(f"⚠️  [GET_LAST_USER_PHOTO] НЕ найдена для user_id={user_id}")
            return None
        except Exception as e:
            logger.error(f"❌ [GET_LAST_USER_PHOTO] user_id={user_id}: {e}", exc_info=True)
            return None

    # ===== PRO MODE =====

    async def get_user_pro_settings(self, user_id: int) -> Dict[str, Any]:
        """🔧 Получить параметры PRO режима"""
        db = await self._get_db()
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER_PRO_SETTINGS, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'pro_mode': bool(row['pro_mode']),
                        'pro_aspect_ratio': row['pro_aspect_ratio'],
                        'pro_resolution': row['pro_resolution'],
                        'pro_mode_changed_at': row['pro_mode_changed_at']
                    }
                return {
                    'pro_mode': False,
                    'pro_aspect_ratio': '16:9',
                    'pro_resolution': '1K',
                    'pro_mode_changed_at': None
                }
        except Exception as e:
            logger.error(f"❌ get_user_pro_settings(user_id={user_id}): {e}", exc_info=True)
            return {
                'pro_mode': False,
                'pro_aspect_ratio': '16:9',
                'pro_resolution': '1K',
                'pro_mode_changed_at': None
            }

    async def set_user_pro_mode(self, user_id: int, mode: bool) -> bool:
        db = await self._get_db()
        try:
            await db.execute(SET_USER_PRO_MODE, (1 if mode else 0, user_id))
            await db.commit()
            mode_name = "PRO 🔧" if mode else "СТАНДАРТ 📋"
            logger.info(f"✅ Режим изменён на {mode_name} для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ set_user_pro_mode(user_id={user_id}): {e}", exc_info=True)
            return False

    async def set_pro_aspect_ratio(self, user_id: int, ratio: str) -> bool:
        valid_ratios = ['16:9', '4:3', '1:1', '9:16']
        if ratio not in valid_ratios:
            logger.warning(f"❌ Неверное соотношение {ratio}. Допустимые: {valid_ratios}")
            return False
        db = await self._get_db()
        try:
            await db.execute(SET_PRO_ASPECT_RATIO, (ratio, user_id))
            await db.commit()
            logger.info(f"✅ Соотношение {ratio} установлено для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ set_pro_aspect_ratio(user_id={user_id}): {e}", exc_info=True)
            return False

    async def set_pro_resolution(self, user_id: int, resolution: str) -> bool:
        valid_resolutions = ['1K', '2K', '4K']
        if resolution not in valid_resolutions:
            logger.warning(f"❌ Неверное разрешение {resolution}. Допустимые: {valid_resolutions}")
            return False
        db = await self._get_db()
        try:
            await db.execute(SET_PRO_RESOLUTION, (resolution, user_id))
            await db.commit()
            logger.info(f"✅ Разрешение {resolution} установлено для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ set_pro_resolution(user_id={user_id}): {e}", exc_info=True)
            return False

    # ===== CHAT MENUS =====

    async def save_chat_menu(self, chat_id: int, user_id: int, menu_message_id: int,
                             screen_code: str = 'main_menu') -> bool:
        db = await self._get_db()
        try:
            await db.execute(SAVE_CHAT_MENU, (chat_id, user_id, menu_message_id, screen_code))
            await db.commit()
            logger.debug(f"📃 Menu сохранено: chat={chat_id}, msgid={menu_message_id}")
            return True
        except Exception as e:
            logger.error(f"❌ save_chat_menu(chat_id={chat_id}): {e}", exc_info=True)
            return False

    async def get_chat_menu(self, chat_id: int) -> Optional[Dict[str, Any]]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute(GET_CHAT_MENU, (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ get_chat_menu(chat_id={chat_id}): {e}", exc_info=True)
            return None

    async def delete_chat_menu(self, chat_id: int) -> bool:
        db = await self._get_db()
        try:
            await db.execute(DELETE_CHAT_MENU, (chat_id,))
            await db.commit()
            logger.debug(f"🗑️  Menu удалено для chat={chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ delete_chat_menu(chat_id={chat_id}): {e}", exc_info=True)
            return False

    async def edit_old_menu_if_exists(self, chat_id: int, user_id: int, new_text: str, new_keyboard, bot) -> Optional[int]:
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
                    logger.info(f"✏️  Menu отредактировано для chat={chat_id}")
                    await self.save_chat_menu(chat_id, user_id, old_message_id, 'main_menu')
                    return old_message_id
                except Exception as e:
                    logger.warning(f"⚠️  Не удалось отредактировать menu: {e}")
                    return None
            return None
        except Exception as e:
            logger.error(f"❌ edit_old_menu_if_exists(chat_id={chat_id}): {e}", exc_info=True)
            return None

    async def delete_old_menu_if_exists(self, chat_id: int, bot) -> bool:
        try:
            menu_data = await self.get_chat_menu(chat_id)
            if menu_data and menu_data.get('menu_message_id'):
                old_menu_id = menu_data['menu_message_id']
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=old_menu_id)
                    logger.info(f"✅ Menu удалено для chat={chat_id}")
                except Exception as e:
                    logger.debug(f"⚠️  Не удалось удалить menu: {e}")
                await self.delete_chat_menu(chat_id)
            return True
        except Exception as e:
            logger.error(f"❌ delete_old_menu_if_exists(chat_id={chat_id}): {e}", exc_info=True)
            return False

    # ===== ПОЛЬЗОВАТЕЛИ =====

    async def create_user(self, user_id: int, username: str = None, referrer_code: str = None) -> bool:
        db = await self._get_db()
        try:
            async with db.execute(GET_USER, (user_id,)) as cursor:
                existing = await cursor.fetchone()
                if existing:
                    logger.warning(f"⚠️  user_id={user_id} уже существует")
                    return False

            ref_code = secrets.token_urlsafe(8)
            initial_balance = int(await self.get_setting('welcome_bonus') or '3')
            await db.execute(CREATE_USER, (user_id, username, initial_balance, ref_code))

            if referrer_code:
                await self._process_referral(db, user_id, referrer_code)

            await db.commit()
            logger.info(f"✅ user_id={user_id} создан (баланс: {initial_balance})")
            return True
        except Exception as e:
            logger.error(f"❌ create_user(user_id={user_id}): {e}", exc_info=True)
            return False

    async def _process_referral(self, db: aiosqlite.Connection, user_id: int, referrer_code: str):
        try:
            async with db.execute(GET_USER_BY_REFERRAL_CODE, (referrer_code,)) as cursor:
                referrer = await cursor.fetchone()
                if not referrer:
                    logger.warning(f"⚠️  Реферрер с кодом '{referrer_code}' не найден")
                    return

            referrer_id = referrer[0]
            await db.execute(UPDATE_REFERRED_BY, (referrer_id, user_id))
            await db.execute(INCREMENT_REFERRALS_COUNT, (referrer_id,))

            inviter_bonus = int(await self.get_setting('referral_bonus_inviter') or '2')
            invited_bonus = int(await self.get_setting('referral_bonus_invited') or '2')

            await db.execute(UPDATE_BALANCE, (inviter_bonus, referrer_id))
            await db.execute(UPDATE_BALANCE, (invited_bonus, user_id))
            logger.info(f"✅ Реферал: {referrer_id} -> {user_id}")
        except Exception as e:
            logger.error(f"❌ _process_referral(user_id={user_id}): {e}", exc_info=True)

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute(GET_USER, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ get_user_data(user_id={user_id}): {e}", exc_info=True)
            return None

    async def get_balance(self, user_id: int) -> int:
        db = await self._get_db()
        try:
            async with db.execute(GET_BALANCE, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"❌ get_balance(user_id={user_id}): {e}", exc_info=True)
            return 0

    async def decrease_balance(self, user_id: int) -> bool:
        db = await self._get_db()
        try:
            async with db.execute(GET_BALANCE, (user_id,)) as cursor:
                row = await cursor.fetchone()
                current = row[0] if row else 0
            
            if current <= 0:
                logger.warning(f"⚠️  user_id={user_id} недостаточно баланса ({current})")
                return False
            
            await db.execute(DECREASE_BALANCE, (user_id,))
            await db.commit()
            logger.info(f"✅ Баланс уменьшен для user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ decrease_balance(user_id={user_id}): {e}", exc_info=True)
            return False

    async def increase_balance(self, user_id: int, tokens: int) -> bool:
        db = await self._get_db()
        try:
            await db.execute(UPDATE_BALANCE, (tokens, user_id))
            await db.commit()
            logger.info(f"✅ Баланс пополнен: user_id={user_id}, +{tokens}")
            return True
        except Exception as e:
            logger.error(f"❌ increase_balance(user_id={user_id}): {e}", exc_info=True)
            return False

    async def add_tokens(self, user_id: int, tokens: int) -> bool:
        db = await self._get_db()
        try:
            await db.execute(UPDATE_BALANCE, (tokens, user_id))
            await db.commit()
            logger.info(f"✅ Добавлено {tokens} токенов user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ add_tokens(user_id={user_id}): {e}", exc_info=True)
            return False

    # ===== ПЛАТЕЖИ =====

    async def create_payment(self, payment_id: str, user_id: int, amount: int, tokens: int) -> bool:
        db = await self._get_db()
        try:
            await db.execute(CREATE_PAYMENT, (user_id, payment_id, amount, tokens, 'pending'))
            await db.commit()
            logger.info(f"✅ Платеж создан: id={payment_id}, user={user_id}, amount={amount}")
            return True
        except Exception as e:
            logger.error(f"❌ create_payment(payment_id={payment_id}): {e}", exc_info=True)
            return False

    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        db = await self._get_db()
        try:
            await db.execute(UPDATE_PAYMENT_STATUS, (status, payment_id))
            await db.commit()
            logger.info(f"✅ Статус платежа обновлен: {payment_id} -> {status}")
            return True
        except Exception as e:
            logger.error(f"❌ update_payment_status(payment_id={payment_id}): {e}", exc_info=True)
            return False

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute("SELECT * FROM payments WHERE yookassa_payment_id = ?", (payment_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ get_payment(payment_id={payment_id}): {e}", exc_info=True)
            return None

    async def get_last_pending_payment(self, user_id: int) -> Optional[Dict[str, Any]]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute(GET_PENDING_PAYMENT, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ get_last_pending_payment(user_id={user_id}): {e}", exc_info=True)
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
            status = "✓" if success else "✗"
            logger.info(f"{status} Генерация: user={user_id}, room={room_type}, style={style_type}")
            return True
        except Exception as e:
            logger.error(f"❌ log_generation(user_id={user_id}): {e}", exc_info=True)
            return False

    async def get_total_generations(self) -> int:
        db = await self._get_db()
        try:
            async with db.execute("SELECT COUNT(*) FROM generations") as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_total_generations(): {e}", exc_info=True)
            return 0

    async def get_generations_count(self, days: int = 1) -> int:
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT COUNT(*) FROM generations WHERE created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_generations_count(days={days}): {e}", exc_info=True)
            return 0

    async def get_failed_generations_count(self, days: int = 1) -> int:
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT COUNT(*) FROM generations WHERE success = 0 AND created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_failed_generations_count(days={days}): {e}", exc_info=True)
            return 0

    async def get_conversion_rate(self) -> float:
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT AVG(total_generations) FROM users WHERE total_generations > 0"
            ) as cursor:
                row = await cursor.fetchone()
                return round(row[0], 2) if row and row[0] else 0.0
        except Exception as e:
            logger.error(f"❌ get_conversion_rate(): {e}", exc_info=True)
            return 0.0

    async def get_popular_rooms(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT room_type, COUNT(*) as count FROM generations GROUP BY room_type ORDER BY count DESC LIMIT ?",
                    (limit,)
            ) as cursor:
                return [{'room_type': row[0], 'count': row[1]} for row in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ get_popular_rooms(limit={limit}): {e}", exc_info=True)
            return []

    async def get_popular_styles(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT style_type, COUNT(*) as count FROM generations GROUP BY style_type ORDER BY count DESC LIMIT ?",
                    (limit,)
            ) as cursor:
                return [{'style_type': row[0], 'count': row[1]} for row in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ get_popular_styles(limit={limit}): {e}", exc_info=True)
            return []

    # ===== АКТИВНОСТЬ =====

    async def log_activity(self, user_id: int, action_type: str) -> bool:
        db = await self._get_db()
        try:
            await db.execute(LOG_USER_ACTIVITY, (user_id, action_type))
            await db.execute(UPDATE_LAST_ACTIVITY, (user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"❌ log_activity(user_id={user_id}): {e}", exc_info=True)
            return False

    async def get_active_users_count(self, days: int = 1) -> int:
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_active_users_count(days={days}): {e}", exc_info=True)
            return 0

    # ===== ДОПОЛНИТЕЛЬНЫЕ =====

    async def get_total_users_count(self) -> int:
        db = await self._get_db()
        try:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_total_users_count(): {e}", exc_info=True)
            return 0

    async def get_setting(self, key: str) -> Optional[str]:
        db = await self._get_db()
        try:
            async with db.execute(GET_SETTING, (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"❌ get_setting(key={key}): {e}", exc_info=True)
            return None

    async def set_setting(self, key: str, value: str) -> bool:
        db = await self._get_db()
        try:
            await db.execute(SET_SETTING, (key, value))
            await db.commit()
            logger.info(f"✅ Настройка установлена: {key}={value}")
            return True
        except Exception as e:
            logger.error(f"❌ set_setting(key={key}): {e}", exc_info=True)
            return False

    async def get_all_settings(self) -> Dict[str, str]:
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute(GET_ALL_SETTINGS) as cursor:
                return {row['key']: row['value'] for row in await cursor.fetchall()}
        except Exception as e:
            logger.error(f"❌ get_all_settings(): {e}", exc_info=True)
            return {}

    # ===== АНАЛИТИКА =====

    async def get_total_revenue(self) -> int:
        """💰 Общая выручка"""
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_total_revenue(): {e}", exc_info=True)
            return 0

    async def get_new_users_count(self, days: int = 1) -> int:
        """👥 Новые пользователи"""
        date_threshold = datetime.now() - timedelta(days=days)
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT COUNT(*) FROM users WHERE created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_new_users_count(days={days}): {e}", exc_info=True)
            return 0

    async def get_successful_payments_count(self) -> int:
        """💳 Успешные платежи"""
        db = await self._get_db()
        try:
            async with db.execute(
                    "SELECT COUNT(*) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                return (await cursor.fetchone())[0] or 0
        except Exception as e:
            logger.error(f"❌ get_successful_payments_count(): {e}", exc_info=True)
            return 0

    def get_startup_errors(self) -> List[str]:
        """📋 Получить ошибки инициализации"""
        return self._startup_errors

    def get_failed_operations(self) -> List[Dict[str, Any]]:
        """❌ Получить ошибки операций"""
        return self._failed_operations

    def is_initialized(self) -> bool:
        """🔍 Проверить инициализирована ли БД"""
        return self._initialized


# 🌍 Глобальный экземпляр
db = Database()
