#!/usr/bin/env python3

import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

user_schema="""
CREATE TABLE IF NOT EXISTS wwm_profiles (
    discord_user_id INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL
    uid INTEGER NOT NULL,
    name TEXT,
    mythic_rank TEXT,
    dps TEXT,
);
"""

class WWM(commands.GroupCog, name="wwm"):
    """command suite for the Where Winds Meet utility"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.init_db()

    def init_db(self):
        """create table for WWM user info"""
        cursor = self.bot.db.cursor()
        cursor.execute(user_schema)
        self.bot.db.commit()

    def set_uid(self, discord_user_id: int, uid: int):
        """create or update a user's wwm UID"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            INSERT INTO wwm_profiles (discord_user_id, uid, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
                SET
                uid = excluded.uid,
                updated_at = excluded.updated_at
            """,
            (discord_user_id, uid, discord.utils.utcnow().isoformat()),
        )
        self.bot.db.commit()

