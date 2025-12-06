from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

import asyncpg

from src.config import config
from src.logconf import opt_logger as log
from src.models.payment_models import Payment

logger = log.setup_logger("database")


# = КЛАСС ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ =
class DatabaseService:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool | None] = None
        self.initialized: bool = False

    async def connect(self):
        """Инициализация пула соединений и создание таблиц"""
        try:
            # Создаем пул соединений
            self._pool = await asyncpg.create_pool(
                config.database.url,
                min_size=config.database.min_size,
                max_size=config.database.max_size,
                timeout=config.database.timeout
            )

            # Создаем таблицы
            await self.__create_payment_status_info()
            await self.__create_transaction_history()
            await self.__create_payment_methods()

            self.initialized = True

            logger.debug("Database pool initialized successfully")
            return self

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def __create_payment_status_info(self):
        async with self.acquire_connection() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_status_info (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                amount NUMERIC NOT NULL,
                currency VARCHAR(10) NULL,
                period TEXT NULL,
                trial BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE, 
                until TIMESTAMP DEFAULT NOW()
                ); """
            )

    async def __create_transaction_history(self):
        async with self.acquire_connection() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transaction_history (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                amount NUMERIC NOT NULL,
                currency VARCHAR(10) NOT NULL,
                payment_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (user_id, payment_id)
                ); 
                """
            )

    async def __create_payment_methods(self):
        async with self.acquire_connection() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_methods (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                payment_method_id TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
                );
                """
            )

    # Контекстный менеджер для работы с соединениями
    @asynccontextmanager
    async def acquire_connection(self):
        """Асинхронный контекстный менеджер для работы с соединениями"""
        conn = await self._pool.acquire()
        try:
            yield conn

        except Exception as e:
            raise logger.warning(f"Connection error occurred, not releasing invalid connection: {e}")

        finally:
            if conn and not conn.is_closed():
                await self._pool.release(conn)


    async def create_payment(self, payment_data: Payment) -> None:
        async with self.acquire_connection() as conn:
            try:

                logger.debug(
                    f"Parameters for payment_status_info: "
                    f"user_id={payment_data.user_id} (type: {type(payment_data.user_id)}), "
                    f"period={payment_data.period} (type: {type(payment_data.period)}), "
                    f"amount={payment_data.amount} (type: {type(payment_data.amount)}), "
                    f"currency={payment_data.currency} (type: {type(payment_data.currency)}), "
                    f"trial={payment_data.trial} (type: {type(payment_data.trial)}), "
                    f"until={payment_data.until} (type: {type(payment_data.until)})"
                )

                # Convert datetime to naive for database storage
                until_naive = payment_data.until.replace(
                    tzinfo=None) if payment_data.until.tzinfo else payment_data.until

                await conn.execute(
                    """
                    INSERT INTO payment_status_info (user_id, period, amount, currency, trial, untill) 
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    payment_data.user_id,
                    payment_data.period,
                    payment_data.amount,
                    payment_data.currency,
                    payment_data.trial,
                    until_naive,
                )

                # Проверка на реальный платеж
                if payment_data.payment_id:
                    created_at = datetime.now(tz=config.tz_info).replace(tzinfo=None)

                    await conn.execute(
                        """
                        INSERT INTO transaction_history (user_id, amount, currency, payment_id, created_at) VALUES ($1, $2, $3, $4, $5)
                        """, payment_data.user_id, payment_data.amount, payment_data.currency, payment_data.payment_id,
                        created_at
                    )

            except Exception as e:
                return logger.error(f"Error creating payment for user {payment_data.user_id}: {e}")

            finally:
                return logger.info(f"Payment successfully created for user {payment_data.user_id}")

    async def save_payment_method(self, user_id: int, payment_method_id: str) -> None:
        """Сохранение payment_method_id для автоматических списаний"""
        async with self.acquire_connection() as conn:
            try:
                new_updated_at = datetime.now(tz=config.tz_info).replace(tzinfo=None)
                await conn.execute(
                    """
                    INSERT INTO payment_methods (user_id, payment_method_id, updated_at) 
                    VALUES ($1, $2, $3) 
                    """,
                    user_id, payment_method_id, new_updated_at
                )
            except Exception as e:
                return logger.error(f"Error in saving method_payment_id for user %s: {e}", user_id)

            finally:
                return logger.info(f"Payment method successfully saved for user %s", user_id)

    async def get_active_subs(self, limit, offset) -> List[dict]:
        async with self.acquire_connection() as conn:
            rows = await conn.execute(
                """
                SELECT user_id, amount, until
                FROM payment_status_info
                WHERE is_active = true
                LIMIT $1 OFFSET $2
                """, limit, offset
            )
            return [
                {
                    "user_id": row["user_id"],
                    "amount": row["amount"],
                    "until": row["until"]
                } for row in rows
            ]

    async def get_user_payment_method(self, user_id: int):
        async with self.acquire_connection() as conn:
            return await conn.fetchval(
                """
                SELECT payment_method_id 
                FROM payment_methods
                WHERE user_id = $1 
                LIMIT 1
                """, user_id
            )

    async def get_users_due_to(self, user_id: int) -> datetime:
        """ Отправляет данные о времени следующей оплаты, если пользователь активен """
        async with self.acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT until
                FROM payment_status_info
                WHERE user_id = $1
                """,
                user_id,
            )
            return row["until"] if row else None

    async def deactivate_subscription(self, user_id: int):
        async with self.acquire_connection() as conn:
            await conn.execute(
                "DELETE FROM payment_methods WHERE user_id = $1", user_id
            )
            await conn.execute(
                "UPDATE users SET is_active = false WHERE user_id = $1", user_id
            )

    async def activate_subscription(self, user_id: int):
        async with self.acquire_connection() as conn:
            try:
                await conn.execute(
                    "UPDATE users SET is_active = true WHERE user_id = $1", user_id
                )

            except Exception as e:
                return logger.error(f"Error in activate_subscription: {e}")

            finally:
                return logger.info("User %s marked as active successfully", user_id)



database_service = DatabaseService()