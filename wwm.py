#!/usr/bin/env python3

import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

user_schema="""
CREATE TABLE IF NOT EXISTS wwm_profiles (
    user_id INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL,
    uid TEXT,
    name TEXT,
    mythic_rank TEXT,
    dps TEXT
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

    def set_uid(self, user_id: int, uid: str):
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

    def delete_profile(self, user_id: int):
        """delete a user's profile frome DB"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            DELETE FROM wwm_profiles
            WHERE user_id = ?
            """,
            (user_id,),
        )
        self.bot.db.commit()

    @app_commands.command(name="uid", description="Set your Where Winds Meet in-game UID")
    @app_commands.describe(uid="Your Where Winds Meet in-game UID (include only the 10-digit number)")
    async def uid_cmd(self, ita: discord.Interaction, uid: str):
        uid = uid.strip()
        if not uid:
            await ita.response.send_message("Please provide a valid UID.", ephemeral=True)
            return
        if not uid.isdigit():
            await ita.response.send_message("Your UID should only contain numbers.", ephemeral=True)
            return
        if len(uid) != 10:
            await ita.response.send_message("Your UID should be 10 digits long.", ephemeral=True)
            return

        self.set_uid(ita.user.id, uid)
        await ita.response.send_message(f"Your in-game UID has been saved as: {uid}.")
        


    @app_commands.command(name="lookup", description="Look up a member's Where Winds Meet profile")
    @app_commands.describe(member="The member whose profile you want to look up")
    async def lookup_cmd(self, ita: discord.Interaction, member: discord.Member):
        if not ita.user.guild_permissions.administrator:
            await ita.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return
        row = self.get_profile(member.id)

        if row is None:
            await ita.response.send_message(
                f"No **Where Winds Meet** profile found for {member.mention}.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"Morningstar Server: Where Winds Meet Profile Lookup",
            description=f"Profile for {member.mention}",
            color=discord.Color.blurple(),
        )

        for n, val in zip(
            ["UID", "Name", "Mythic Rank", "DPS"],
            [row["uid"], row["name"], row["mythic_rank"], row["dps"]],
        ):
            if val is not None:
                embed.add_field(name=n, value=val, inline=False)
            else:
                embed.add_field(name=n, value="Not set", inline=False)
        await ita.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(WWM(bot))



