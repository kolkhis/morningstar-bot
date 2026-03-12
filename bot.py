import os
import sys
import time
import logging
import asyncio
import discord
from discord.ext import commands
from typing import Optional, Sequence
import datetime as dt
import sqlite3

PREFIXES = ";", "!", ">", "."

# A Discord bot to facilitate weekly giveaways for a guild in an MMO. 
# The bot should have the capability of keeping track of people's levels (e.g., we keep track of their message count and level them up as they talk, max level of 10 at 500 messages)
# There will be a weekly giveaway post, and users who react with a specific emoji will be entered into the drawing pool **only if** they are level 10.
# The post will be automated weekly, and will select from a list of 3 rewards randomly and randomly select a winner.

REWARDS: list = [
    "$1 Skin",
    "$5 Skin",
    "$10 Battle Pass",
]
GIVEAWAY_EMOJI: str = "🎉"
REQUIRED_ROLE_ID: int = 1481044257916850361 

GUILD_ID: int = int(os.getenv('GUILD_ID', '0'))
GIVEAWAY_CHANNEL_ID: int = int(os.getenv('GIVEAWAY_CHANNEL_ID', '0'))
if not GUILD_ID or not GIVEAWAY_CHANNEL_ID:
    sys.stderr.write("[ERROR]: One of the GUILD_ID or GIVEAWAY_CHANNEL_ID environment " \
                     "variables are unset!\n")
    sys.exit(1)

# Leveling system
LEVEL_THRESHOLDS = {
    1: 50,
    2: 100,
    3: 150,
    4: 200,
    5: 250,
    6: 300,
    7: 350,
    8: 400,
    9: 450,
    10: 500,
}
MESSAGE_COOLDOWN: int = 1 # seconds
def calculate_level(message_count: int) -> int:
    level = 0
    for lvl, threshold in LEVEL_THRESHOLDS.items():
        if message_count >= threshold:
            level = lvl
    return level


class Bot(commands.Bot):

    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        intents.members = True

        super().__init__(command_prefix=PREFIXES, intents=intents)
        self.setup_logging()
        self.prefixes: tuple = PREFIXES

        self.guild_id: int = int(os.environ.get('GUILD_ID', '0'))
        self.giveaway_channel_id: int = int(os.environ.get('GIVEAWAY_CHANNEL_ID', '0'))

        if not self.guild_id or not self.giveaway_channel_id:
            sys.stderr.write("[ERROR]: One of the GUILD_ID or GIVEAWAY_CHANNEL_ID environment " \
                             "variables are unset!\n")
            sys.exit(1)

        self.db: sqlite3.Connection = sqlite3.connect("guildbot.db")
        self.db.row_factory = sqlite3.Row
        self.last_message_times: dict[int, float] = {}

        self.init_db()

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

    def init_db(self) -> None:
        cursor = self.db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            message_count INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 0
        )
        """)
        self.db.commit()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} (id={self.user.id})")
        print(f"Ready and waiting for events...")

    async def setup_hook(self) -> None:
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"Slash commands synced to guild {guild}")

    # Leveling system methods
    def get_user_stats(self, user_id: int) -> Optional[sqlite3.Row]:
        """Return a user's stats row from the database, or None if missing."""
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT user_id, message_count, level
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )
        return cursor.fetchone()

    def create_user_stats(self, user_id: int) -> None:
        """Create a new stats row for a user."""
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, message_count, level)
            VALUES (?, 0, 0)
            """,
            (user_id,)
        )
        self.db.commit()

    def update_user_stats(self, user_id: int, message_count: int, level: int) -> None:
        """Update a user's message count and level."""
        cursor = self.db.cursor()
        cursor.execute(
            """
            UPDATE users
            SET message_count = ?, level = ?
            WHERE user_id = ?
            """,
            (message_count, level, user_id)
        )
        self.db.commit()

    def increment_user_message_count(self, user_id: int) -> tuple[int, int, int]:
        """
        Increment a user's message count by one.

        Returns:
            tuple[int, int, int]:
                (message_count, old_level, new_level)
        """
        row = self.get_user_stats(user_id)

        if row is None:
            self.create_user_stats(user_id)
            row = self.get_user_stats(user_id)

        old_level: int = row["level"]
        message_count: int = row["message_count"] + 1
        new_level: int = calculate_level(message_count)

        self.update_user_stats(user_id, message_count, new_level)
        return message_count, old_level, new_level

    def ensure_user_exists(self, user_id: int) -> sqlite3.Row:
        """Ensure a user exists in the database and return their row."""
        row = self.get_user_stats(user_id)
        if row is None:
            self.create_user_stats(user_id)
            row = self.get_user_stats(user_id)
        return row

    async def on_message(self, message: discord.Message) -> None:
        """Track user messages for the leveling system"""
        if message.author.bot:
            return

        if message.guild is None:
            return

        content: str = message.content.strip()

        # Ignore empty messages
        if not content:
            await self.process_commands(message)
            return

        now: float = time.time()
        last_time: float = self.last_message_times.get(message.author.id, 0.0)

        if now - last_time < MESSAGE_COOLDOWN:
            await self.process_commands(message)
            return

        self.last_message_times[message.author.id] = now

        message_count, old_level, new_level = self.increment_user_message_count(message.author.id)

        if new_level != old_level:
            await message.channel.send(
                f"{message.author.mention} leveled up! You're now level "
                f"**{new_level}**! (Message count: {message_count})"
            )
        await self.process_commands(message)

