import asyncio
import logging
import sys

from bot.bot import MoodBot
from bot.database import Database
from bot.dynamo import DynamoClient
from bot.init import initialize

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
        case other:
            _logger.error("Unknown operation mode: %s", other)
            sys.exit(1)


if __name__ == "__main__":
    main()
