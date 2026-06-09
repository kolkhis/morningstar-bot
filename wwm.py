#!/usr/bin/env python3

import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

user_schema="""
CREATE TABLE IF NOT EXISTS wwm_profiles (
    discord_user_id INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL
    uid TEXT NOT NULL,
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

        
