import os
import sys
import time
import logging
import random
import asyncio
import discord
from discord.ext import commands
from typing import Optional, Sequence
import datetime as dt
import sqlite3

# A Discord bot to facilitate weekly giveaways for a guild in an MMO. 
# The bot should have the capability of keeping track of people's levels (e.g., we keep track of their message count and level them up as they talk, max level of 10 at 500 messages)
# There will be a weekly giveaway post, and users who react with a specific emoji will be entered into the drawing pool **only if** they are level 10.
# The post will be automated weekly, and will select from a list of 3 rewards randomly and randomly select a winner.

PREFIXES = ";", "!", ">", "."
REWARDS: list = [
    "$1 Skin",
    "$5 Skin",
    "$10 Battle Pass",
]
GIVEAWAY_EMOJI: str = "🎉"
REQUIRED_ROLE_ID: int = 1481044257916850361 
BOT_CHANNEL_ID: int = 1482014535966654565
REQUIRED_LEVEL: int = 3

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

        self.guild_id: int = GUILD_ID if GUILD_ID is not None \
            else int(os.environ.get('GUILD_ID', '0'))
        self.giveaway_channel_id: int = GIVEAWAY_CHANNEL_ID if GIVEAWAY_CHANNEL_ID is not None \
            else int(os.environ.get('GIVEAWAY_CHANNEL_ID', '0'))

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
        # Add table for leveling system
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            message_count INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 0
        );
        """)
        # Add table for giveaways
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            reward TEXT NOT NULL,
            emoji TEXT NOT NULL,
            created_at TEXT NOT NULL,
            ended INTEGER NOT NULL DEFAULT 0
        );
        """)
        self.db.commit()

    ################ BOT EVENT HANDLERS ################
    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} (id={self.user.id})")
        print(f"Ready and waiting for events...")

    async def setup_hook(self) -> None:
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"Slash commands synced to guild {guild}")

    ############## LEVELING SYSTEM METHODS #############
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
        row = cursor.fetchone()
        if row is not None:
            return row
        if row is None:
            self.create_user_stats(user_id)
            row = self.get_user_stats(user_id)
            return row

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

    def get_next_level_info(self, message_count: int, level: int) -> tuple[Optional[int], Optional[int]]:
        """
        Return the next level and its threshold.

        Returns:
            tuple[Optional[int], Optional[int]]:
                (next_level, next_threshold)

            If the user is already max level, returns (None, None).
        """
        if level >= max(LEVEL_THRESHOLDS):
            return None, None

        next_level = level + 1
        next_threshold = LEVEL_THRESHOLDS[next_level]
        return next_level, next_threshold

    def build_progress_bar(self, current: int, total: int, width: int = 10) -> str:
        """Return an ASCII text progress bar for the user's level progress."""
        if total <= 0:
            return "[----------] 0%"
        ratio = current / total
        filled = int(ratio * width)
        empty = width - filled
        percent = int(ratio * 100)

        return f"[{'█' * filled}{'░' * empty}] {percent}%"

    # Bot event handler for tracking messages and leveling up users
    async def on_message(self, message: discord.Message) -> None:
        """Bot event handler, track user messages for the leveling system"""
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
            channel = self.get_channel(BOT_CHANNEL_ID)
            if channel is None:
                channel = await self.fetch_channel(BOT_CHANNEL_ID)
            await channel.send(
                f"{message.author.mention} leveled up! You're now level "
                f"**{new_level}**! Use `/level` to check your stats!"
            )

        await self.process_commands(message)

    ############## GIVEAWAYS METHODS ##############
    async def get_giveaway_channel(self) -> Optional[discord.TextChannel]:
        channel = self.get_channel(GIVEAWAY_CHANNEL_ID)
        if channel is not None:
            return channel
        try:
            channel = await self.fetch_channel(GIVEAWAY_CHANNEL_ID)
            return channel
        except discord.NotFound:
            sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m Giveaway channel with ID {GIVEAWAY_CHANNEL_ID} not found.\n")
            return None

    def create_giveaway_record(self, 
                                     guild_id: int,
                                     channel_id: int,
                                     message_id: int,
                                     reward: str,
                                     emoji: str,
                                     created_at: str,
                                     ) -> None:
        cursor = self.db.cursor() 
        cursor.execute(
            """
            INSERT INTO giveaways (
                guild_id, channel_id, message_id, reward, emoji, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, channel_id, message_id, reward, emoji, created_at)
        )
        self.db.commit()

    def get_active_giveaway(self) -> Optional[sqlite3.Row]:
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT id, guild_id, channel_id, message_id, reward, emoji, created_at, ended
            FROM giveaways
            WHERE guild_id = ? AND ended = 0
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (self.guild_id,)
        )
        row = cursor.fetchone()
        return row

    def close_giveaway(self, giveaway_id: int) -> None:
        cursor = self.db.cursor()
        cursor.execute(
            """
            UPDATE giveaways
            SET ended = 1
            WHERE id = ?
            """,
            (giveaway_id,)
        )
        self.db.commit()

    def is_giveaway_eligible(self, member: discord.Member) -> bool:
        if member.bot:
            return False

        has_giveaway_role = any(role.id == REQUIRED_ROLE_ID for role in member.roles)
        if not has_giveaway_role:
            return False

        row = self.get_user_stats(member.id)
        if row is None:
            return False

        return row["level"] >= REQUIRED_LEVEL

    async def post_giveaway(self) -> Optional[discord.Message]:
        channel = await self.get_giveaway_channel()
        if channel is None:
            sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m Giveaway channel with ID \
                              {GIVEAWAY_CHANNEL_ID} not found. Cannot post giveaway.\n")
            return None

        active = self.get_active_giveaway()
        if active is not None:
            sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m An active \
                               giveaway already exists with message ID {active['message_id']}. \
                               Cannot post new giveaway until the active one is closed.\n")
            return None
        
        reward = random.choice(REWARDS)
        content = (
            f"# WEEKLY GIVEAWAY! 🎉\n\n"
            f"Reward for this week: **{reward}**\n\n"
            f"React to this message with {GIVEAWAY_EMOJI} to enter the giveaway!\n"
            f"## Eligibility requirements:\n\n" 
            f"- Must have the @{REQUIRED_ROLE_ID} role.  \n"
            f"- Must be level {REQUIRED_LEVEL} (use `/level` to check your stats in #kolbot).  \n\n"
            f"Winners will be randomly selected from the pool of eligible entrants who react to this message."
        )

        msg = await channel.send(content)
        await msg.add_reaction(GIVEAWAY_EMOJI)

        self.create_giveaway_record(
            guild_id=self.guild_id,
            channel_id=channel.id,
            message_id=msg.id,
            reward=reward,
            emoji=GIVEAWAY_EMOJI,
            created_at=dt.datetime.utcnow().isoformat(),  # TODO(fix): Refactor to non-deprecated method
        )
        return msg
        

    async def draw_giveaway_winner(self) -> Optional[discord.Member]:
        giveaway = self.get_active_giveaway()
        if giveaway is None:
            sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m No active giveaway found for guild ID {self.guild_id}. Cannot draw winner.\n")
            return None

        channel = self.get_channel(giveaway["channel_id"])
        if channel is None:
            try:
                channel = await self.fetch_channel(giveaway["channel_id"])
            except discord.DiscordException:
                pass
                sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m Giveaway channel with ID \
                                  {giveaway['channel_id']} not found. Cannot draw winner.\n")
            return None

        if not isinstance(channel, discord.TextChannel):
            sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m Giveaway channel with ID \
                              {giveaway['channel_id']} is not a text channel. Cannot draw winner.\n")
            return None
    
        try:
            giveaway_msg = await channel.fetch_message(giveaway["message_id"])
        except discord.DiscordException:
            sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m Giveaway message with ID " \
                             f"{giveaway['message_id']} not found in channel {channel.id}. " \
                             "Cannot draw winner.\n")
            return None

        valid_members: list[discord.Member] = []
        for reaction in giveaway_msg.reactions:
            if str(reaction.emoji) != giveaway["emoji"]:
                continue

            async for user in reaction.users():
                if user.bot:
                    continue
                member = channel.guild.get_member(user.id)
                if member is None:
                    try:
                        member = await channel.guild.fetch_member(user.id)
                    except discord.DiscordException:
                        sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m User with ID {user.id} " \
                                         "reacted to giveaway message but is not a member of the guild. " \
                                         "Skipping user.\n")
                        continue

                if self.is_giveaway_eligible(member):
                    valid_members.append(member)

        self.close_giveaway(giveaway["id"])
        if not valid_members:
            sys.stderr.write(f"\x1b[31m[GIVEAWAY ERROR]:\x1b[0m No eligible entrants found for giveaway " \
                             f"with message ID {giveaway['message_id']}. Cannot draw winner.\n")
            return None
        winner = random.choice(valid_members)
        await channel.send(f"Congratulations to {winner.mention}! They won this " \
                           f"week's giveaway for **{giveaway['reward']}**! 🎉")
        return winner

