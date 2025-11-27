from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from bs_nats_updater import NatsConfig

if TYPE_CHECKING:
    from bs_config import Env


@dataclass(frozen=True, kw_only=True)
class SentryConfig:
    dsn: str
    release: str

    @classmethod
    def from_env(cls, env: Env) -> Self | None:
        dsn = env.get_string("sentry-dsn")

        if not dsn:
            return None

        return cls(
            dsn=dsn,
            release=env.get_string("app-version", default="debug"),
        )


@dataclass(frozen=True, kw_only=True)
class TelegramConfig:
    token: str
    timezone_name: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            token=env.get_string("token", required=True),
            timezone_name=env.get_string("timezone", default="Etc/UTC"),
        )


@dataclass(frozen=True, kw_only=True)
class DatabaseConfig:
    host: str
    name: str
    username: str
    password: str

    def to_connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}/{self.name}"

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            host=env.get_string("host", default="localhost"),
            name=env.get_string("name", required=True),
            username=env.get_string("username", required=True),
            password=env.get_string("password", required=True),
        )


@dataclass(frozen=True, kw_only=True)
class Config:
    active_chats: list[int]
    database: DatabaseConfig
    nats: NatsConfig
    sentry: SentryConfig | None
    telegram: TelegramConfig

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            active_chats=env.get_int_list("active-chats", required=True),
            database=DatabaseConfig.from_env(env / "database"),
            nats=NatsConfig.from_env(env / "nats"),
            sentry=SentryConfig.from_env(env),
            telegram=TelegramConfig.from_env(env / "telegram"),
        )
