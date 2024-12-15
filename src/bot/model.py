from dataclasses import dataclass
from datetime import UTC, datetime
from enum import IntEnum
from typing import Self

import telegram


class PollOption(IntEnum):
    very_good = 0
    good = 1
    not_so_good = 2
    bad = 3

    def __str__(self) -> str:
        match self:
            case PollOption.very_good:
                return "🦦 Sehr gut"
            case PollOption.good:
                return "🙂 Gut"
            case PollOption.not_so_good:
                return "😪 Nicht so gut"
            case PollOption.bad:
                return "😞 Schlecht"


@dataclass(kw_only=True)
class Poll:
    id: str
    group_id: int
    message_id: int
    creation_time: datetime
    close_time: datetime | None


@dataclass(frozen=True, kw_only=True)
class User:
    id: int
    first_name: str

    @classmethod
    def from_telegram(cls, user: telegram.User) -> Self:
        return cls(
            id=user.id,
            first_name=user.first_name,
        )

    def __str__(self) -> str:
        return f"{self.first_name} ({self.id})"


@dataclass(frozen=True, kw_only=True)
class PollAnswer:
    time: datetime
    option: PollOption | None
    user_id: int
    poll_id: str

    @classmethod
    def from_telegram(cls, answer: telegram.PollAnswer) -> Self:
        options = answer.option_ids
        return cls(
            time=datetime.now(tz=UTC),
            option=PollOption(options[0]) if options else None,
            user_id=answer.user.id,
            poll_id=str(answer.poll_id),
        )

    def get_option_value(self) -> int | None:
        option = self.option
        if option is None:
            return None

        return option.value

    def __str__(self) -> str:
        option = self.option
        if option:
            return option.name
        else:
            return "<no answer>"
