from __future__ import annotations

import typing
from collections.abc import AsyncIterable

import aioboto3

from bot.config import AwsConfig
from bot.model import User

if typing.TYPE_CHECKING:
    pass


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
