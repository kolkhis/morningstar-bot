import os
import sys
import logging
import asyncio
import discord
from discord.ext import commands
from typing import Optional, Sequence

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

        self.guild_id=os.environ.get('GUILD_ID', '')
        self.forum_channel_id=os.environ.get('FORUM_CHANNEL', '')
        if not self.guild_id or not self.forum_channel_id:
            sys.stderr.write("[ERROR]: The GUILD_ID or FORUM_CHANNEL environment " \
                             "variables are unset!\n")
            sys.exit(1)

    def setup_logging(self) -> None:
        """
        Set up logging for the bot. 
        Uses a custom formatter to add colours to the logs.
        Passes in a custom formatter to `discord.utils.setup_logging` to 
        customize the format of the log string. 
        """
        if not os.path.isdir("./logs"):
            os.makedirs("logs", exist_ok=True)
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

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} (id={self.user.id})")
        print(f"Ready and waiting for events...")

    async def setup_hook(self) -> None:
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"Slash commands synced to guild {guild}")


    async def add_forum_post(self,
                             title: str,
                             body: str,
                             forum_channel_id: int = self.forum_channel_id,
                             tags: Optional[Sequence[str]] = None,
                             ) -> discord.Thread:
        channel = self.get_channel(self.forum_channel_id)
        if not channel:
           channel = await self.fetch_channel(self.forum_channel_id)
        if not isinstance(channel, discord.ForumChannel):
            raise TypeError(f"Channel {self.forum_channel_id} is not a " \
                            f"ForumChannel. Got {type(channel)} instead.")
        thread = await channel.create_thread(
            name=title,
            content=body,
            # tags=[],
        )

        return thread

