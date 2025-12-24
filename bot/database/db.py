# bot/database/db.py
# --- ОБНОВЛЕН: 2025-12-24 12:35 - Добавлены методы для PRO MODE функционала ---
# --- ОБНОВЛЕН: 2025-12-04 11:36 - Добавлены методы для уведомлений и источников трафика ---
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
    CREATE_CHAT_MENUS_TABLE,  # ← НОВАЯ СТРОКА
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
    # Единое меню (НОВОЕ)
    SAVE_CHAT_MENU, GET_CHAT_MENU, DELETE_CHAT_MENU,  # ← НОВАЯ СТРОКА
    # PRO MODE (НОВОЕ)
    GET_USER_PRO_SETTINGS, SET_USER_PRO_MODE, SET_PRO_ASPECT_RATIO, SET_PRO_RESOLUTION  # ← НОВАЯ СТРОКА
)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация таблиц БД"""
        async with aiosqlite.connect(self.db_path) as db:
            # Создаем все таблицы
            await db.execute(CREATE_USERS_TABLE)
            await db.execute(CREATE_PAYMENTS_TABLE)
            await db.execute(CREATE_GENERATIONS_TABLE)
            await db.execute(CREATE_USER_ACTIVITY_TABLE)
            await db.execute(CREATE_ADMIN_NOTIFICATIONS_TABLE)
            await db.execute(CREATE_USER_SOURCES_TABLE)
            await db.execute(CREATE_CHAT_MENUS_TABLE)  # ← НОВАЯ ТАБЛИЦА
            await db.execute(CREATE_REFERRAL_EARNINGS_TABLE)
            await db.execute(CREATE_REFERRAL_EXCHANGES_TABLE)
            await db.execute(CREATE_REFERRAL_PAYOUTS_TABLE)
            await db.execute(CREATE_SETTINGS_TABLE)

            # Инициализируем дефолтные настройки
            for key, value in DEFAULT_SETTINGS.items():
                await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

            await db.commit()
            logger.info("База данных инициализирована")

    # ===== PRO MODE FUNCTIONS (НОВОЕ) =====

    async def get_user_pro_settings(self, user_id: int) -> Dict[str, Any]:
        """
        Получить все параметры PRO режима пользователя.

        Возвращает:
        - {'pro_mode': bool, 'pro_aspect_ratio': str, 'pro_resolution': str, 'pro_mode_changed_at': str}
        - Если пользователя нет, возвращает дефолтные значения
        """
        async with aiosqlite.connect(self.db_path) as db:
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
                    # Дефолтные значения если пользователя нет
                    return {
                        'pro_mode': False,
                        'pro_aspect_ratio': '16:9',
                        'pro_resolution': '1K',
                        'pro_mode_changed_at': None
                    }
            except Exception as e:
                logger.error(f"❌ Ошибка get_user_pro_settings для user_id={user_id}: {e}")
                return {
                    'pro_mode': False,
                    'pro_aspect_ratio': '16:9',
                    'pro_resolution': '1K',
                    'pro_mode_changed_at': None
                }

    async def set_user_pro_mode(self, user_id: int, mode: bool) -> bool:
        """
        Установить режим (True = PRO, False = СТАНДАРТ).

        Параметры:
        - user_id: ID пользователя
        - mode: True для PRO, False для СТАНДАРТ

        Возвращает:
        - True если успешно обновлено, False при ошибке
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(SET_USER_PRO_MODE, (1 if mode else 0, user_id))
                await db.commit()
                mode_name = "PRO 🔧" if mode else "СТАНДАРТ 📋"
                logger.info(f"✅ Режим изменён на {mode_name} для user_id={user_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка set_user_pro_mode для user_id={user_id}: {e}")
                return False

    async def set_pro_aspect_ratio(self, user_id: int, ratio: str) -> bool:
        """
        Установить соотношение сторон для PRO режима.

        Параметры:
        - user_id: ID пользователя
        - ratio: '16:9', '4:3', '1:1', '9:16'

        Возвращает:
        - True если успешно обновлено, False при ошибке
        """
        # Валидируем значение
        valid_ratios = ['16:9', '4:3', '1:1', '9:16']
        if ratio not in valid_ratios:
            logger.warning(f"❌ Неверное соотношение: {ratio}. Допустимые: {valid_ratios}")
            return False

        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(SET_PRO_ASPECT_RATIO, (ratio, user_id))
                await db.commit()
                logger.info(f"✅ Соотношение сторон установлено {ratio} для user_id={user_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка set_pro_aspect_ratio для user_id={user_id}: {e}")
                return False

    async def set_pro_resolution(self, user_id: int, resolution: str) -> bool:
        """
        Установить разрешение для PRO режима.

        Параметры:
        - user_id: ID пользователя
        - resolution: '1K', '2K', '4K'

        Возвращает:
        - True если успешно обновлено, False при ошибке
        """
        # Валидируем значение
        valid_resolutions = ['1K', '2K', '4K']
        if resolution not in valid_resolutions:
            logger.warning(f"❌ Неверное разрешение: {resolution}. Допустимые: {valid_resolutions}")
            return False

        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(SET_PRO_RESOLUTION, (resolution, user_id))
                await db.commit()
                logger.info(f"✅ Разрешение установлено {resolution} для user_id={user_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка set_pro_resolution для user_id={user_id}: {e}")
                return False

    # ===== CHAT MENUS =====

    async def save_chat_menu(self, chat_id: int, user_id: int, menu_message_id: int,
                             screen_code: str = 'main_menu') -> bool:
        """Сохранить/обновить menu_message_id и screen_code для чата"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(SAVE_CHAT_MENU,
                                 (chat_id, user_id, menu_message_id, screen_code))
                await db.commit()
                logger.debug(f"💾 Saved menu: chat={chat_id}, msgid={menu_message_id}, screen={screen_code}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка save_chat_menu: {e}")
                return False

    async def get_chat_menu(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные меню для чата"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_CHAT_MENU, (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def delete_chat_menu(self, chat_id: int) -> bool:
        """Удалить запись о меню для чата"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(DELETE_CHAT_MENU, (chat_id,))
                await db.commit()
                logger.debug(f"🗑️ Deleted menu record for chat {chat_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка delete_chat_menu: {e}")
                return False

    async def delete_old_menu_if_exists(self, chat_id: int, bot) -> bool:
        """Удалить старое меню из чата, если оно есть в БД"""
        try:
            menu_data = await self.get_chat_menu(chat_id)
            if menu_data and menu_data.get('menu_message_id'):
                old_menu_id = menu_data['menu_message_id']
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=old_menu_id)
                    logger.debug(f"🗑️ Удалено старое меню: chat={chat_id}, message_id={old_menu_id}")
                except Exception as e:
                    logger.debug(f"⚠️ Не удалось удалить старое меню: {e}")

                await self.delete_chat_menu(chat_id)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка delete_old_menu_if_exists: {e}")
            return False

    # ===== ПОЛЬЗОВАТЕЛИ =====

    async def create_user(self, user_id: int, username: str = None, referrer_code: str = None) -> bool:
        """Создать нового пользователя с реферальным кодом"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Проверяем, есть ли уже пользователь
                async with db.execute(GET_USER, (user_id,)) as cursor:
                    existing = await cursor.fetchone()
                    if existing:
                        return False

                # Генерируем уникальный реферальный код
                ref_code = secrets.token_urlsafe(8)

                # Получаем начальный бонус
                initial_balance = int(await self.get_setting('welcome_bonus') or '3')

                # Создаем пользователя
                await db.execute(CREATE_USER, (user_id, username, initial_balance, ref_code))

                # Обрабатываем реферальную систему
                if referrer_code:
                    await self._process_referral(db, user_id, referrer_code)

                await db.commit()
                logger.info(f"Пользователь {user_id} создан с реф. кодом {ref_code}")
                return True
            except Exception as e:
                logger.error(f"Ошибка создания пользователя: {e}")
                return False

    async def _process_referral(self, db: aiosqlite.Connection, user_id: int, referrer_code: str):
        """Обработка реферальной системы при регистрации"""
        try:
            # Находим реферера
            async with db.execute(GET_USER_BY_REFERRAL_CODE, (referrer_code,)) as cursor:
                referrer = await cursor.fetchone()
                if not referrer:
                    return

            referrer_id = referrer[0]

            # Связываем пользователя с реферером
            await db.execute(UPDATE_REFERRED_BY, (referrer_id, user_id))

            # Увеличиваем счетчик рефералов
            await db.execute(INCREMENT_REFERRALS_COUNT, (referrer_id,))

            # Начисляем бонусы
            inviter_bonus = int(await self.get_setting('referral_bonus_inviter') or '2')
            invited_bonus = int(await self.get_setting('referral_bonus_invited') or '2')

            await db.execute(UPDATE_BALANCE, (inviter_bonus, referrer_id))
            await db.execute(UPDATE_BALANCE, (invited_bonus, user_id))

            logger.info(f"Реферал: {referrer_id} пригласил {user_id}")
        except Exception as e:
            logger.error(f"Ошибка обработки реферала: {e}")

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def get_balance(self, user_id: int) -> int:
        """Получить баланс генераций"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(GET_BALANCE, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def decrease_balance(self, user_id: int) -> bool:
        """Уменьшить баланс на 1"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(DECREASE_BALANCE, (user_id,))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка уменьшения баланса: {e}")
                return False

    async def add_tokens(self, user_id: int, tokens: int) -> bool:
        """Добавить генерации"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(UPDATE_BALANCE, (tokens, user_id))
                await db.commit()
                logger.info(f"Добавлено {tokens} генераций пользователю {user_id}")
                return True
            except Exception as e:
                logger.error(f"Ошибка добавления токенов: {e}")
                return False

    # ===== ПЛАТЕЖИ =====

    async def create_payment(self, payment_id: str, user_id: int, amount: int, tokens: int) -> bool:
        """Создать запись о платеже"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(CREATE_PAYMENT, (user_id, payment_id, amount, tokens, 'pending'))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка создания платежа: {e}")
                return False

    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновить статус платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(UPDATE_PAYMENT_STATUS, (status, payment_id))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка обновления статуса платежа: {e}")
                return False

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о платеже"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM payments WHERE yookassa_payment_id = ?", (payment_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def get_last_pending_payment(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить последний ожидающий платеж"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_PENDING_PAYMENT, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def set_payment_success(self, payment_id: str) -> bool:
        """Отметить платеж как успешный"""
        return await self.update_payment_status(payment_id, 'succeeded')

    # ===== ГЕНЕРАЦИИ =====

    async def log_generation(self, user_id: int, room_type: str, style_type: str,
                             operation_type: str = 'design', success: bool = True) -> bool:
        """
        Залогировать генерацию.
        Параметры:
        - user_id: ID пользователя
        - room_type: тип комнаты (напр. 'гостиная', 'кухня')
        - style_type: стиль (напр. 'минимализм', 'лофт')
        - operation_type: тип операции ('design' или др.)
        - success: успешность генерации
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Логируем в таблицу generations
                await db.execute(CREATE_GENERATION, (user_id, room_type, style_type, operation_type, success))

                # Увеличиваем счетчик в таблице users
                await db.execute(INCREMENT_TOTAL_GENERATIONS, (user_id,))

                # Обновляем время последней активности
                await db.execute(UPDATE_LAST_ACTIVITY, (user_id,))

                await db.commit()
                logger.info(f"Генерация: user={user_id}, room={room_type}, style={style_type}")
                return True
            except Exception as e:
                logger.error(f"Ошибка логирования генерации: {e}")
                return False

    async def get_total_generations(self) -> int:
        """Общее количество генераций"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM generations") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_generations_count(self, days: int = 1) -> int:
        """Количество генераций за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT COUNT(*) FROM generations WHERE created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_failed_generations_count(self, days: int = 1) -> int:
        """
        Количество неудачных генераций за период.
        Параметры:
        - days: количество дней назад (1 = за сегодня, 7 = за неделю)
        """
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT COUNT(*) FROM generations WHERE success = 0 AND created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_conversion_rate(self) -> float:
        """
        Рассчитать конверсию (генераций на пользователя).
        Возвращает среднее количество генераций на пользователя.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT AVG(total_generations) FROM users WHERE total_generations > 0"
            ) as cursor:
                row = await cursor.fetchone()
                return round(row[0], 2) if row and row[0] else 0.0

    async def get_popular_rooms(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить популярные типы комнат"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """
                    SELECT room_type, COUNT(*) as count
                    FROM generations
                    GROUP BY room_type
                    ORDER BY count DESC
                    LIMIT ?
                    """,
                    (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{'room_type': row[0], 'count': row[1]} for row in rows]

    async def get_popular_styles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить популярные стили"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """
                    SELECT style_type, COUNT(*) as count
                    FROM generations
                    GROUP BY style_type
                    ORDER BY count DESC
                    LIMIT ?
                    """,
                    (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{'style_type': row[0], 'count': row[1]} for row in rows]

    # ===== АКТИВНОСТЬ =====

    async def log_activity(self, user_id: int, action_type: str) -> bool:
        """
        Залогировать активность пользователя.
        Параметры:
        - user_id: ID пользователя
        - action_type: тип действия (напр. 'start', 'generation', 'payment', 'referral')
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(LOG_USER_ACTIVITY, (user_id, action_type))
                await db.execute(UPDATE_LAST_ACTIVITY, (user_id,))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка логирования активности: {e}")
                return False

    async def get_active_users_count(self, days: int = 1) -> int:
        """
        Количество активных пользователей за период.
        Активным считается пользователь, который совершил любое действие.
        """
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ===== СТАТИСТИКА =====

    async def get_total_users_count(self) -> int:
        """Общее количество пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_new_users_count(self, days: int = 1) -> int:
        """Количество новых пользователей за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT COUNT(*) FROM users WHERE created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_total_revenue(self) -> int:
        """Общая выручка"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT SUM(amount) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else 0

    async def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Последние пользователи"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT ?",
                    (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def search_user(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Поиск пользователя по ID, username или реферальному коду.
        Возвращает полную информацию о пользователе.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Пробуем поиск по ID (если запрос - цифры)
            if query.isdigit():
                user_id = int(query)
                async with db.execute(GET_USER, (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return dict(row)

            # Поиск по username (убираем @ если есть)
            username_query = query.replace('@', '')
            async with db.execute(
                    "SELECT * FROM users WHERE username = ? OR username = ?",
                    (username_query, f"@{username_query}")
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)

            # Поиск по реферальному коду
            async with db.execute(GET_USER_BY_REFERRAL_CODE, (query,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)

            return None

    async def get_all_users_paginated(self, page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Получить всех пользователей с пагинацией.
        Возвращает ([пользователи], всего_страниц)
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Подсчитываем общее количество
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total = (await cursor.fetchone())[0]

            total_pages = (total + per_page - 1) // per_page
            offset = (page - 1) * per_page

            # Получаем пользователей для страницы
            async with db.execute(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (per_page, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                users = [dict(row) for row in rows]

            return users, total_pages

    async def get_revenue_by_period(self, days: int = 1) -> int:
        """Выручка за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT SUM(amount) FROM payments WHERE status = 'succeeded' AND created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else 0

    async def get_successful_payments_count(self) -> int:
        """Количество успешных платежей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT COUNT(*) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_average_payment(self) -> int:
        """Средний чек"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT AVG(amount) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row and row[0] else 0

    async def get_all_payments(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить все платежи"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    """
                    SELECT p.*, u.username 
                    FROM payments p
                    LEFT JOIN users u ON p.user_id = u.user_id
                    ORDER BY p.created_at DESC
                    LIMIT ?
                    """,
                    (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


# Создаем глобальный экземпляр
db = Database()
