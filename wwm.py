#!/usr/bin/env python3

import sqlite3
import discord
import re
from discord import app_commands
from discord.ext import commands

user_schema="""
CREATE TABLE IF NOT EXISTS wwm_profiles (
    user_id INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL,
    uid TEXT,
    name TEXT,
    mythic_rank TEXT,
    dps TEXT,
    build TEXT
);
"""

FIELD_NAMES: dict[str, str] = {
    "UID": "uid",
    "Name": "name",
    "Build": "build",
    "Mythic Rank": "mythic_rank",
    "DPS": "dps",
}

WWM_BUILD_OPTIONS = { 
    "Bamboocut Wind": "DPS",
    "Bamboocut Dust": "DPS",
    "Bellstrike Splendor": "DPS",
    "Bellstrike Umbra": "DPS",
    "Stonesplit Might": "Tank", 
    "Stonesplit Strength": "DPS",
    "Silkbind Jade": "DPS",
    "Silkbind Deluge": "Healer",
}


class WWM(commands.GroupCog, name="wwm"):
    """command suite for the Where Winds Meet utility"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.init_db()

    def init_db(self):
        """create table for WWM user info"""
        cursor = self.bot.db.cursor()
        cursor.execute(user_schema)
        self.bot.db.commit()
        # TODO: Comment out after schema update
        # self.ensure_column_exists("wwm_profiles", "build", "TEXT")

    def ensure_column_exists(self, table_name: str, column_name: str, column_type: str):
        """add a column to a table if it doesn't already exist"""
        cursor = self.bot.db.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row["name"] for row in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
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

    def set_build(self, user_id: int, build: str):
        """create or update the user's WWM build"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            INSERT INTO wwm_profiles (user_id, build, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
                SET
                build = excluded.build,
                updated_at = excluded.updated_at
            """,
            (user_id, build, discord.utils.utcnow().isoformat()),
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

    @app_commands.command(name="set-uid", description="Set your Where Winds Meet in-game UID")
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
        

    @app_commands.command(name="set-name", description="Set your Where Winds Meet in-game name")
    @app_commands.describe(name="Your Where Winds Meet in-game name")
    async def name_cmd(self, ita: discord.Interaction, name: str):
        name = name.strip()
        if not name:
            await ita.response.send_message("Please provide a valid name.", ephemeral=True)
            return
        self.set_name(ita.user.id, name)
        await ita.response.send_message(f"Your in-game name has been saved as: {name}.")

    @app_commands.command(name="set-dps", description="Set your Where Winds Meet in-game dps")
    @app_commands.describe(dps="Your Where Winds Meet in-game DPS (from a 1 minute test in the training dummy)")
    async def set_dps_cmd(self, ita: discord.Interaction, dps: str):
        dps = dps.strip()
        if not dps:
            await ita.response.send_message("Please provide valid DPS. (e.g., 41.1k)", ephemeral=True)
            return
        if not re.match(r"^\d+(\.?\d+)?[kK]?$", dps):
            await ita.response.send_message("Please provide valid DPS. (e.g., 41.1k)", ephemeral=True)
            return
        self.set_dps(ita.user.id, dps)
        await ita.response.send_message(f"Your in-game DPS has been saved as: {dps}.")

    @app_commands.command(name="set-mythic-rank", description="Set your Where Winds Meet in-game Mythic PVP rank")
    @app_commands.describe(mythic_rank="Your Where Winds Meet in-game Mythic PVP rank points (e.g., `2000`))")
    async def dps_mythic_rank(self, ita: discord.Interaction, mythic_rank: str):
        mythic_rank = mythic_rank.strip()
        if not mythic_rank:
            await ita.response.send_message("Please provide valid mythic points rank. (e.g., 1000)", ephemeral=True)
            return
        # if not re.match(r"^\d{3,5}", mythic_rank):
        #     await ita.response.send_message("Please provide valid mythic points rank. (e.g., 1000)", ephemeral=True)
        #     return
        self.set_mythic_rank(ita.user.id, mythic_rank)
        await ita.response.send_message(f"Your in-game DPS has been saved as: {mythic_rank}.")

    @app_commands.command(name="set-build", description="Set your Where Winds Meet build")
    async def set_build_cmd(self, ita: discord.Interaction):
        embed = discord.Embed(
            title="Select Your Build",
            description="Please select your Where Winds Meet build from the dropdown menu below.",
            color=discord.Color.blurple(),
        )
        await ita.response.send_message(embed=embed, view=WWMBuildView(self, ita.user.id), ephemeral=True)

    @app_commands.command(name="lookup", description="Look up a member's Where Winds Meet profile")
    @app_commands.describe(member="The member whose profile you want to look up")
    async def lookup_cmd(self, ita: discord.Interaction, member: discord.Member):
        await ita.response.defer(ephemeral=True)
        if not ita.user.guild_permissions.administrator:
            await ita.followup.send(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return
        row = self.get_profile(member.id)

        if row is None:
            await ita.followup.send(
                f"No **Where Winds Meet** profile found for {member.mention}.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"Morningstar Server: Where Winds Meet Profile Lookup",
            description=f"Profile for {member.mention}",
            color=discord.Color.blurple(),
        )

        for n, val in FIELD_NAMES.items():
            if val is not None:
                embed.add_field(name=n, value=row[val], inline=False)
            else:
                embed.add_field(name=n, value="Not set", inline=False)
        await ita.followup.send(embed=embed, ephemeral=True)


class WWMBuildSelect(discord.ui.Select):
    def __init__(self, cog: "WWM", user_id: int):
        self.cog = cog
        self.user_id = user_id

        options = [
            discord.SelectOption(label=build, value=build)
            for build in WWM_BUILD_OPTIONS
        ]

        super().__init__(
            placeholder="Choose your Where Winds Meet build.",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This build selector is not for you.",
                ephemeral=True,
            )
            return

        selected_build = self.values[0]
        self.cog.set_build(interaction.user.id, selected_build)

        embed = discord.Embed(
            title="Build Saved",
            description=f"Your Where Winds Meet build has been saved as:\n\n**{selected_build}**",
            color=discord.Color.green(),
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None,
        )


    # async def set_profile_field(self, user_id: int, field: str, value: str):
    #     """helper function to set a specific field in the user's profile"""
    #     if field == "build":
    #         self.cog.set_build(user_id, value)
    #     elif field == "dps":
    #         self.cog.set_dps(user_id, value)
    #     elif field == "mythic_rank":
    #         self.cog.set_mythic_rank(user_id, value)
    #     elif field == "name":
    #         self.cog.set_name(user_id, value)
    #     elif field == "uid":
    #         self.cog.set_uid(user_id, value)


# class WWMBuildView(discord.ui.View):
#     def __init__(self, cog: "WWM", user_id: int):
#         super().__init__(timeout=300)
#         self.add_item(WWMBuildSelect(cog, user_id))

class WWMProfileView(discord.ui.View):
    def __init__(self, cog: "WWM", user_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.add_item(WWMBuildSelect(cog, user_id))

async def setup(bot: commands.Bot):
    await bot.add_cog(WWM(bot))



