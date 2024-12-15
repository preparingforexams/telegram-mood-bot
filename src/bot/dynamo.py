from __future__ import annotations

import typing
from collections.abc import AsyncIterable
from dataclasses import dataclass
from datetime import UTC, datetime

import aioboto3

from bot.config import AwsConfig
from bot.model import PollAnswer, PollOption, User


@dataclass(frozen=True)
class ImportedPollAnswer:
    answer: PollAnswer
    group_id: int


class DynamoClient:
    def __init__(self, config: AwsConfig) -> None:
        self._config = config
        self._session = aioboto3.Session(
            region_name="eu-central-1",
            aws_access_key_id=self._config.access_key,
            aws_secret_access_key=self._config.secret_key,
        )

    @staticmethod
    def _build_user(item: dict[str, typing.Any]) -> User:
        return User(
            id=int(item["user_id"]),
            first_name=item["first_name"],
        )

    async def list_users(self) -> AsyncIterable[User]:
        async with self._session.resource("dynamodb") as resource:
            table = await resource.Table("mischebot-users")
            response = await table.scan()
            for item in response.get("Items"):
                yield self._build_user(item)

            while last_key := response.get("LastEvaluatedKey"):
                response = await table.scan(ExclusiveStartKey=last_key)
                for item in response.get("Items"):
                    yield self._build_user(item)

    async def list_user_groups(self) -> AsyncIterable[tuple[int, int]]:
        async with self._session.resource("dynamodb") as resource:
            table = await resource.Table("mischebot-groups")
            response = await table.scan()
            for item in response.get("Items"):
                yield int(item["user_id"]), int(item["group_id"])

            while last_key := response.get("LastEvaluatedKey"):
                response = await table.scan(ExclusiveStartKey=last_key)
                for item in response.get("Items"):
                    yield int(item["user_id"]), int(item["group_id"])

    @staticmethod
    def _build_answer(item: dict[str, typing.Any]) -> ImportedPollAnswer:
        answer = PollAnswer(
            time=datetime.fromtimestamp(int(item["time"]), tz=UTC),
            option=PollOption(int(item["option"])),
            user_id=int(item["user_id"]),
            poll_id=str(item["poll_id"]),
        )

        return ImportedPollAnswer(answer=answer, group_id=int(item["group_id"]))

    async def list_answers(self) -> AsyncIterable[ImportedPollAnswer]:
        async with self._session.resource("dynamodb") as resource:
            table = await resource.Table("mischebot-results2")
            response = await table.scan()
            for item in response.get("Items"):
                yield self._build_answer(item)

            while last_key := response.get("LastEvaluatedKey"):
                response = await table.scan(ExclusiveStartKey=last_key)
                for item in response.get("Items"):
                    yield self._build_answer(item)
