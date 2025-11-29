# database/db.py

import aiosqlite
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Payments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    amount INTEGER,
                    tokens INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            await db.commit()
            logger.info("Database initialized successfully")

    async def create_user(self, user_id: int, username: str = None) -> bool:
        """Create new user if doesn't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                return False

    async def get_balance(self, user_id: int) -> int:
        """Get user balance"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT balance FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_user_data(self, user_id: int) -> Optional[dict]:
        """Получить данные пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT user_id, username, balance, created_at FROM users WHERE user_id = ?",
                    (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'balance': row[2],
                        'created_at': row[3]
                    }
                return None

    async def decrease_balance(self, user_id: int) -> bool:
        """Decrease user balance by 1"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE users SET balance = balance - 1 WHERE user_id = ? AND balance > 0",
                    (user_id,)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error decreasing balance: {e}")
                return False

    async def add_tokens(self, user_id: int, tokens: int) -> bool:
        """Add tokens to user balance"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                    (tokens, user_id)
                )
                await db.commit()
                logger.info(f"Added {tokens} tokens to user {user_id}")
                return True
            except Exception as e:
                logger.error(f"Error adding tokens: {e}")
                return False

    async def create_payment(
        self, payment_id: str, user_id: int, amount: int, tokens: int
    ) -> bool:
        """Create payment record"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO payments (payment_id, user_id, amount, tokens) VALUES (?, ?, ?, ?)",
                    (payment_id, user_id, amount, tokens)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating payment: {e}")
                return False

    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Update payment status"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE payments SET status = ? WHERE payment_id = ?",
                    (status, payment_id)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error updating payment status: {e}")
                return False

    async def get_payment(self, payment_id: str) -> Optional[dict]:
        """Get payment by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT payment_id, user_id, amount, tokens, status FROM payments WHERE payment_id = ?",
                    (payment_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'payment_id': row[0],
                        'user_id': row[1],
                        'amount': row[2],
                        'tokens': row[3],
                        'status': row[4]
                    }
                return None

    async def get_recent_users(self, limit: int = 10) -> list:
        """Получить последних пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT user_id, username, balance, created_at FROM users ORDER BY created_at DESC LIMIT ?",
                    (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'user_id': row[0],
                        'username': row[1] if row[1] else 'Не указано',
                        'balance': row[2],
                        'created_at': row[3]
                    }
                    for row in rows
                ]

    # ===== НОВЫЕ МЕТОДЫ ДЛЯ СТАТИСТИКИ АДМИН-ПАНЕЛИ =====

    async def get_total_users_count(self) -> int:
        """Получить общее количество пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_new_users_count(self, days: int = 1) -> int:
        """Получить количество новых пользователей за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT COUNT(*) FROM users WHERE created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_total_revenue(self) -> int:
        """Получить общую выручку (только успешные платежи)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT SUM(amount) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else 0

    async def get_revenue_by_period(self, days: int = 1) -> int:
        """Получить выручку за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT SUM(amount) FROM payments WHERE status = 'succeeded' AND created_at >= ?",
                    (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else 0

    async def get_successful_payments_count(self) -> int:
        """Получить количество успешных платежей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT COUNT(*) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_average_payment(self) -> float:
        """Получить средний чек"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT AVG(amount) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return round(row[0], 2) if row and row[0] else 0.0

    async def get_all_users_paginated(self, page: int = 1, per_page: int = 10) -> tuple[list, int]:
        """
        Получить список всех пользователей с пагинацией
        Возвращает (список пользователей, общее количество страниц)
        """
        offset = (page - 1) * per_page

        async with aiosqlite.connect(self.db_path) as db:
            # Получаем общее количество
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total_row = await cursor.fetchone()
                total_count = total_row[0] if total_row else 0

            # Вычисляем количество страниц
            total_pages = (total_count + per_page - 1) // per_page

            # Получаем пользователей для текущей страницы
            async with db.execute(
                    "SELECT user_id, username, balance, created_at FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (per_page, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                users = [
                    {
                        'user_id': row[0],
                        'username': row[1] if row[1] else 'Не указано',
                        'balance': row[2],
                        'created_at': row[3]
                    }
                    for row in rows
                ]

            return users, total_pages

    async def get_all_payments(self, limit: int = 20) -> list:
        """Получить последние платежи"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    """
                    SELECT p.payment_id, p.user_id, u.username, p.amount, p.tokens, p.status, p.created_at
                    FROM payments p
                    LEFT JOIN users u ON p.user_id = u.user_id
                    ORDER BY p.created_at DESC
                    LIMIT ?
                    """,
                    (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'payment_id': row[0],
                        'user_id': row[1],
                        'username': row[2] if row[2] else 'Не указано',
                        'amount': row[3],
                        'tokens': row[4],
                        'status': row[5],
                        'created_at': row[6]
                    }
                    for row in rows
                ]


# Create global database instance
db = Database()
