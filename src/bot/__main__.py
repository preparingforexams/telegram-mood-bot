import asyncio
import logging
import sys
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from bot.bot import MoodBot
from bot.database import Database
from bot.dynamo import DynamoClient
from bot.init import initialize
from bot.model import Poll

_logger = logging.getLogger(__package__)


async def _send_polls(bot: MoodBot, active_chats: list[int]) -> None:
    await bot.initialize()
    try:
        for chat_id in active_chats:
            await bot.send_poll(chat_id)
    finally:
        await bot.close()


async def _close_polls(bot: MoodBot) -> None:
    await bot.initialize()
    try:
        await bot.close_open_polls()
    finally:
        await bot.close()


async def _import_users(dynamo: DynamoClient, database: Database) -> None:
    await database.open()
    try:
        async for user in dynamo.list_users():
            _logger.info("Upserting user %s", user)
            await database.upsert_user(user)
    finally:
        await database.close()


async def _import_user_groups(dynamo: DynamoClient, database: Database) -> None:
    await database.open()
    try:
        async for user_id, group_id in dynamo.list_user_groups():
            _logger.info("Linking user %d to group %d", user_id, group_id)
            await database.add_to_group(user_id=user_id, group_id=group_id)
    finally:
        await database.close()


def _build_poll(*, poll_id: str, group_id: int, answer_time: datetime) -> Poll:
    if answer_time.hour != 0:
        raise ValueError(f"Unexcected answer time: {answer_time}")

    tz = ZoneInfo("Europe/Berlin")
    date = answer_time.date()
    creation_time = datetime.combine(date, time(13), tzinfo=tz)
    close_time = datetime.combine(date + timedelta(days=1), time(1), tzinfo=UTC)
    return Poll(
        id=poll_id,
        group_id=group_id,
        message_id=0,
        creation_time=creation_time,
        close_time=close_time,
    )


async def _import_results(dynamo: DynamoClient, database: Database) -> None:
    await database.open()
    tz = ZoneInfo("Europe/Berlin")
    try:
        async for imported in dynamo.list_answers():
            answer = imported.answer
            plausible_time = datetime.combine(
                answer.time.date(),
                time(14),
                tzinfo=tz,
            )
            answer = replace(answer, time=plausible_time)
            await database.upsert_answer(answer)
    finally:
        await database.close()


def main() -> None:
    config, database = initialize()

    bot = MoodBot(config.telegram, database)

    args = sys.argv[1:]
    if len(args) != 1:
        _logger.error("Must specify operation mode")
        return

    match args[0]:
        case "handle-updates":
            _logger.info("Running bot")
            bot.run()
        case "send-polls":
            _logger.info("Sending out polls")
            asyncio.run(_send_polls(bot, config.active_chats))
        case "close-polls":
            _logger.info("Closing polls")
            asyncio.run(_close_polls(bot))
        case "import-users":
            _logger.info("Importing users")
            asyncio.run(_import_users(DynamoClient(config.aws), database))
        case "import-user-groups":
            _logger.info("Importing user groups")
            asyncio.run(_import_user_groups(DynamoClient(config.aws), database))
        case "import-results":
            _logger.info("Importing results")
            asyncio.run(_import_results(DynamoClient(config.aws), database))
        case other:
            _logger.error("Unknown operation mode: %s", other)
            sys.exit(1)


if __name__ == "__main__":
    main()
