from dataclasses import dataclass
from typing import Self

from bs_config import Env


@dataclass(frozen=True, kw_only=True)
class SentryConfig:
    dsn: str
    release: str

    @classmethod
    def from_env(cls, env: Env) -> Self | None:
        dsn = env.get_string("SENTRY_DSN")

        if not dsn:
            return None

        return cls(
            dsn=dsn,
            release=env.get_string("APP_VERSION", default="debug"),
        )


@dataclass(frozen=True, kw_only=True)
class TelegramConfig:
    token: str
    target_chat: int
    timezone_name: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            token=env.get_string("TELEGRAM_TOKEN", required=True),
            target_chat=env.get_int("TELEGRAM_TARGET_CHAT", default=133399998),
            timezone_name=env.get_string("TELEGRAM_TIMEZONE", default="Etc/UTC"),
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
            host=env.get_string("HOST", default="localhost"),
            name=env.get_string("NAME", required=True),
            username=env.get_string("USERNAME", required=True),
            password=env.get_string("PASSWORD", required=True),
        )


@dataclass(frozen=True, kw_only=True)
class Config:
    active_chats: list[int]
    database: DatabaseConfig
    sentry: SentryConfig | None
    telegram: TelegramConfig

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            active_chats=env.get_int_list("ACTIVE_CHATS", required=True),
            database=DatabaseConfig.from_env(env.scoped("DATABASE_")),
            sentry=SentryConfig.from_env(env),
            telegram=TelegramConfig.from_env(env),
        )
