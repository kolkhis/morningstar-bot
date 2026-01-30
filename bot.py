import discord
import logging
import asyncio
from discord.ext import commands

PREFIXES = ";", "!", ">", "."
TIMEZONE_NAME: str = "America/New_York"
POST_HR: int = 9
POST_MIN: int = 0

class Bot(commands.Bot):
    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=PREFIXES, intents=intents)
        self.setup_logging()
        self.prefixes: tuple = PREFIXES

    def setup_logging(self) -> None:
        """
        Set up logging for the bot. 
        Uses a custom formatter to add colours to the logs.
        Passes in a custom formatter to `discord.utils.setup_logging` to 
        customize the format of the log string. 
        """
        logging.basicConfig(
            filename="logs/bot.log",
            level=logging.INFO,
            format="%(asctime)s:%(levelname)s:%(message)s",
        )
        handler: logging.StreamHandler = logging.StreamHandler()
        formatter: discord.utils._ColourFormatter = discord.utils._ColourFormatter()
        # Custom date formatting
        formatter.FORMATS = {
            level: logging.Formatter(
                f"\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s",
                "%m-%d-%Y %H:%M:%S",
            )
            for level, colour in formatter.LEVEL_COLOURS
        }
        discord.utils.setup_logging(
            level=logging.INFO,
            formatter=formatter,
            handler=handler,
        )
    
    async def setup_hook(self) -> None:
        await self.tree.sync()


