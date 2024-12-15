import logging
import signal
from datetime import tzinfo, datetime, UTC
from typing import cast
from zoneinfo import ZoneInfo

import telegram
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    PollAnswerHandler,
)

from bot.config import TelegramConfig
from bot.database import Database
from bot.model import User, PollAnswer, PollOption, Poll

_logger = logging.getLogger(__name__)

type Context = ContextTypes.DEFAULT_TYPE


class MoodBot:
    def __init__(self, config: TelegramConfig, database: Database) -> None:
        self.config = config
        self.db = database
        self.timezone: tzinfo = ZoneInfo(config.timezone_name)

        app = (
            ApplicationBuilder()
            .token(self.config.token)
            .post_init(lambda _: self.initialize())
            .post_shutdown(lambda _: self.close())
            .build()
        )
        app.add_handler(PollAnswerHandler(self._on_poll_answer))

        self.app = app
        self.bot: telegram.Bot = app.bot

    async def initialize(self) -> None:
        await self.db.open()

    async def close(self) -> None:
        await self.db.close()

    def _now(self) -> datetime:
        return datetime.now(tz=UTC).astimezone(self.timezone)

    @staticmethod
    def _get_day_description(at_time: datetime) -> str:
        day_names = [
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
            "Sonntag",
        ]
        day_name = day_names[at_time.weekday()]
        date = at_time.strftime(r"%d.%m.%Y")
        return f"{day_name} {date}"

    async def _on_poll_answer(self, update: telegram.Update, _: Context) -> None:
        poll_answer = update.poll_answer
        if poll_answer is None:
            raise ValueError("Poll answer was None")

        user = User.from_telegram(poll_answer.user)
        answer = PollAnswer.from_telegram(poll_answer)
        _logger.info(f"Received poll answer from {user}: {answer}")

        await self.db.upsert_user(user)
        await self.db.upsert_answer(answer)

        poll = await self.db.get_poll(answer.poll_id)
        await self.db.add_to_group(user_id=user.id, group_id=poll.group_id)

    async def send_poll(self, chat_id: int) -> None:
        if not await self.db.can_connect():
            _logger.error("Could not connect to database")
            return

        now = self._now()
        day_of_week = self._get_day_description(now)

        # TODO: meme

        message = await self.bot.send_poll(
            chat_id=chat_id,
            question=f"Heute, {day_of_week}, geht es mir",
            options=[str(option) for option in PollOption],
            is_anonymous=False,
            allows_multiple_answers=False,
        )
        telegram_poll = cast(telegram.Poll, message.poll)
        poll = Poll(
            id=telegram_poll.id,
            group_id=chat_id,
            message_id=message.message_id,
            creation_time=now,
            close_time=None,
        )
        await self.db.insert_poll(poll)

    async def close_open_polls(self) -> None:
        close_time = self._now()
        async for poll in self.db.get_open_polls():
            _logger.debug(f"Closing poll {poll.id} in group {poll.group_id}")
            await self.bot.stop_poll(
                chat_id=poll.group_id,
                message_id=poll.message_id,
            )
            await self.db.update_poll_close_time(poll.id, close_time)

    def run(self) -> None:
        self.app.run_polling(
            stop_signals=[signal.SIGINT, signal.SIGTERM],
        )
