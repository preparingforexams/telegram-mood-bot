import logging
from collections.abc import Iterable
from datetime import datetime
from typing import cast

import asyncpg

from bot.config import DatabaseConfig
from bot.database import Database, NotFoundException, OperationalException
from bot.model import Poll, PollAnswer, User

_logger = logging.getLogger(__name__)


class PostgresDatabase(Database):
    def __init__(self, config: DatabaseConfig) -> None:
        self.__config = config
        self.__pool: asyncpg.Pool | None = None

    @property
    def _pool(self) -> asyncpg.Pool:
        pool = self.__pool
        if pool is None:
            raise ValueError("Database not initialized")

        return pool

    async def open(self) -> None:
        if self.__pool is not None:
            raise ValueError("Already initialized")

        _logger.info("Opening connection pool")
        config = self.__config
        try:
            self.__pool = await asyncpg.create_pool(
                database=config.name,
                user=config.username,
                password=config.password,
                host=config.host,
                min_size=1,
                max_size=4,
            )
        except asyncpg.PostgresConnectionError as e:
            raise OperationalException from e

    async def can_connect(self) -> bool:
        try:
            async with self._pool.acquire():
                return True
        except asyncpg.PostgresConnectionError as e:
            _logger.error("Connection unhealthy", exc_info=e)
            return False

    async def close(self) -> None:
        _logger.info("Closing connection pool")
        await self._pool.close()
        _logger.debug("Connection pool is closed")

    @staticmethod
    def _poll_from_row(row: asyncpg.Record) -> Poll:
        return Poll(
            id=row["id"],
            group_id=row["group_id"],
            message_id=row["message_id"],
            creation_time=row["creation_time"],
            close_time=row["close_time"],
        )

    async def get_poll(self, poll_id: str) -> Poll:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            row = await connection.fetchrow(
                """
                SELECT * FROM polls WHERE id = $1;
                """,
                poll_id,
            )

            if row is None:
                raise NotFoundException(poll_id)

            return self._poll_from_row(row)

    async def get_open_polls(self) -> Iterable[Poll]:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            records = await connection.fetch(
                """
                SELECT * FROM polls WHERE close_time is null;
                """
            )
            for row in records:
                yield self._poll_from_row(row)

    async def upsert_user(self, user: User) -> None:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            await connection.execute(
                """
                INSERT INTO users(id, first_name)
                VALUES ($1, $2)
                ON CONFLICT(id) DO UPDATE SET
                    first_name = $2;
                """,
                user.id,
                user.first_name,
            )

    async def add_to_group(self, *, user_id: int, group_id: int) -> None:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            await connection.execute(
                """
                INSERT INTO users_groups(user_id, group_id)
                VALUES ($1, $2)
                ON CONFLICT(user_id, group_id) DO NOTHING;
                """,
                user_id,
                group_id,
            )

    async def insert_poll(self, poll: Poll) -> None:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            await connection.execute(
                """
                INSERT INTO polls(id, group_id, message_id, creation_time, close_time)
                VALUES ($1, $2, $3, $4, $5);
                """,
                poll.id,
                poll.group_id,
                poll.message_id,
                poll.creation_time,
                poll.close_time,
            )

    async def update_poll_close_time(
        self,
        poll_id: str,
        close_time: datetime,
    ) -> None:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            await connection.execute(
                """
                UPDATE polls
                SET close_time = $2
                WHERE id = $1;
                """,
                poll_id,
                close_time,
            )

    async def upsert_answer(self, poll_answer: PollAnswer) -> None:
        async with self._pool.acquire() as connection:
            connection = cast(asyncpg.Connection, connection)
            await connection.execute(
                """
                INSERT INTO poll_answers(user_id, poll_id, time, option)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT(user_id, poll_id) DO UPDATE SET
                    time = $3,
                    option = $4
                """,
                poll_answer.user_id,
                poll_answer.poll_id,
                poll_answer.time,
                poll_answer.get_option_value(),
            )
