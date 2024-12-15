import abc
from collections.abc import AsyncIterable
from datetime import datetime

from bot.model import Poll, PollAnswer, User


class DatabaseException(abc.ABC, Exception):
    pass


class OperationalException(DatabaseException):
    pass


class NotFoundException(DatabaseException):
    def __init__(self, entity_id: str) -> None:
        super().__init__(f"Lookup by ID failed: {entity_id}")


class ConstraintException(DatabaseException):
    pass


class DuplicateException(ConstraintException):
    pass


class Database(abc.ABC):
    @abc.abstractmethod
    async def open(self) -> None:
        pass

    @abc.abstractmethod
    async def get_poll(self, poll_id: str) -> Poll:
        pass

    @abc.abstractmethod
    def get_open_polls(self) -> AsyncIterable[Poll]:
        pass

    @abc.abstractmethod
    async def upsert_user(self, user: User) -> None:
        pass

    @abc.abstractmethod
    async def add_to_group(self, *, user_id: int, group_id: int) -> None:
        pass

    @abc.abstractmethod
    async def insert_poll(self, poll: Poll) -> None:
        pass

    @abc.abstractmethod
    async def update_poll_close_time(
        self,
        poll_id: str,
        close_time: datetime,
    ) -> None:
        pass

    @abc.abstractmethod
    async def upsert_answer(self, poll_answer: PollAnswer) -> None:
        pass

    @abc.abstractmethod
    async def can_connect(self) -> bool:
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        pass
