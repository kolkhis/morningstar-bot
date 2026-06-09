#!/usr/bin/env python3

import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

user_schema="""
CREATE TABLE IF NOT EXISTS wwm_profiles (
    user_id INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL
    uid TEXT,
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

    def get_profile(self, user_id: int):
        """return a user's WWM profile (DB row for that user)"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            SELECT *
            FROM wwm_profiles
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return cursor.fetchone()

    def set_uid(self, user_id: int, uid: int):
        """create or update a user's wwm UID"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            INSERT INTO wwm_profiles (user_id, uid, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
                SET
                uid = excluded.uid,
                updated_at = excluded.updated_at
            """,
            (user_id, uid, discord.utils.utcnow().isoformat()),
        )
        self.bot.db.commit()

    def set_mythic_rank(self, user_id: int, rank: str):
        """create or update the user's WWM mythic rank"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            INSERT INTO wwm_profiles (user_id, mythic_rank, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
                SET
                mythic_rank = excluded.mythic_rank,
                updated_at = excluded.updated_at
            """,
            (user_id, rank, discord.utils.utcnow().isoformat()),
        )
        self.bot.db.commit()

    def set_name(self, user_id: int, name: str):
        """create or update the user's WWM name"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            INSERT INTO wwm_profiles (user_id, name, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
                SET
                name = excluded.name,
                updated_at = excluded.updated_at
            """,
            (user_id, name, discord.utils.utcnow().isoformat()),
        )
        self.bot.db.commit()

    def set_dps(self, user_id: int, dps: str):
        """create or update the user's WWM dps"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            INSERT INTO wwm_profiles (user_id, dps, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
                SET
                dps = excluded.dps,
                updated_at = excluded.updated_at
            """,
            (user_id, dps, discord.utils.utcnow().isoformat()),
        )
        self.bot.db.commit()







