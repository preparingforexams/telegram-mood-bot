import asyncio
import logging
import sys

from bot.init import initialize
from bot.bot import MoodBot

_logger = logging.getLogger(__package__)


async def _send_polls(bot: MoodBot, active_chats: list[int])->None:
    await bot.initialize()
    try:
        for chat_id in active_chats:
            await bot.send_poll(chat_id)
    finally:
        await bot.close()

async def _close_polls(bot: MoodBot) ->None:
    await bot.initialize()
    try:
        await bot.close_open_polls()
    finally:
        await bot.close()

def main()->None:
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
        case other:
            _logger.error(f"Unknown operation mode: {other}")
            sys.exit(1)


if __name__ == "__main__":
    main()
