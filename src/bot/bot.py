import logging
import signal
from datetime import UTC, datetime, tzinfo
from typing import cast
from zoneinfo import ZoneInfo

import telegram
from asyncpg import PostgresError
from bs_nats_updater import NatsConfig, create_updater
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    Updater,
    filters,
)

from bot.config import TelegramConfig
from bot.database import Database
from bot.meme import Meme, MemeKind, get_meme
from bot.model import Poll, PollAnswer, PollOption, User

_logger = logging.getLogger(__name__)

type Context = ContextTypes.DEFAULT_TYPE


class MoodBot:
    def __init__(
        self,
        config: TelegramConfig,
        nats_config: NatsConfig,
        database: Database,
    ) -> None:
        self.config = config
        self.db = database
        self.timezone: tzinfo = ZoneInfo(config.timezone_name)

        app = (
            ApplicationBuilder()
            .updater(create_updater(self.config.token, nats_config))
            .post_init(self.initialize)
            .post_shutdown(lambda _: self.close())
            .build()
        )
        app.add_handler(PollAnswerHandler(self._on_poll_answer))
        message_filter = (
            filters.PHOTO
            | filters.VIDEO
            | filters.ANIMATION
            | filters.AUDIO
            | filters.VOICE
        )
        app.add_handler(
            MessageHandler(
                filters=message_filter,
                callback=self._on_message,
            )
        )

        self.app = app
        self.bot: telegram.Bot = app.bot

    async def initialize(self, application: Application | None = None) -> None:
        try:
            await self.db.open()
        except PostgresError as e:
            _logger.error("Could not open database connection", exc_info=e)
            if application is not None:
                application.stop_running()

    async def close(self) -> None:
        await self.db.close()
        updater: Updater | None = self.app.updater
        if updater is not None and updater.running:
            await updater.stop()

    def _now(self) -> datetime:
        return datetime.now(tz=UTC).astimezone(self.timezone)

    async def _on_message(self, update: telegram.Update, _: Context) -> None:
        message = update.message
        if message is None:
            return

        if photos := message.photo:
            largest = max(photos, key=lambda p: p.file_size or 0)
            _logger.info("Received photo with file_id %s", largest.file_id)

        if video := message.video:
            _logger.info("Received video with file_id %s", video.file_id)

        if animation := message.animation:
            _logger.info("Received animation with file_id %s", animation.file_id)

        if voice := message.voice:
            _logger.info("Received voice with file_id %s", voice.file_id)

        if audio := message.audio:
            _logger.info("Received voice with file_id %s", audio.file_id)

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

        user = User.from_telegram(cast(telegram.User, poll_answer.user))
        answer = PollAnswer.from_telegram(poll_answer)
        _logger.info("Received poll answer from %s: %s", user, answer)

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
        meme = get_meme(now)

        if meme is not None:
            await self._send_meme(chat_id, meme)

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
            creation_time = poll.creation_time.astimezone(self.timezone)
            if creation_time.date() == close_time.date():
                _logger.debug("Skipping poll %s from today", poll.id)
                continue

            _logger.debug("Closing poll %s in group %d", poll.id, poll.group_id)
            await self.bot.stop_poll(
                chat_id=poll.group_id,
                message_id=poll.message_id,
            )
            await self.db.update_poll_close_time(poll.id, close_time)

    def run(self) -> None:
        self.app.run_polling(
            stop_signals=[signal.SIGINT, signal.SIGTERM],
        )

    async def _send_meme(self, chat_id: int, meme: Meme) -> None:
        bot = self.bot
        file_id = meme.file_id
        match meme.kind:
            case MemeKind.photo:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id,
                    disable_notification=True,
                )
            case MemeKind.video:
                await bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    disable_notification=True,
                )
            case MemeKind.animation:
                await bot.send_animation(
                    chat_id=chat_id,
                    animation=file_id,
                    disable_notification=True,
                )
