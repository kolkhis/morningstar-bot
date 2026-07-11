import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

from tremendous_client import TremendousClient

# TODO: Finish this.
# This provides a way for users to claim a monthly coffee fund reward via
# Tremendous API (using ./tremendous_client.py).

# TODO(feat): Add more commands to create/update profile, check claim status, etc.
# - /coffee setup
# - /coffee status
# - /coffee profile
# - /coffee claim

COFFEE_AMOUNT_USD = float(os.environ.get("COFFEE_AMOUNT_USD", "5"))
TREMENDOUS_PRODUCT_IDS = os.environ.get("TREMENDOUS_PRODUCT_IDS", "").split(",")


class CoffeeFund(commands.GroupCog, name="coffee"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tremendous = TremendousClient()
        self.init_db()

    def init_db(self):
        cursor = self.bot.db.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS coffee_profiles (
            user_id INTEGER PRIMARY KEY,
            recipient_name TEXT NOT NULL,
            recipient_email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS coffee_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            claim_month TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            currency_code TEXT NOT NULL,
            tremendous_order_id TEXT,
            tremendous_reward_id TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, claim_month)
        );
        """)

        self.bot.db.commit()

    @app_commands.command(name="claim", description="Claim this month's coffee fund reward")
    async def claim_cmd(self, ita: discord.Interaction):
        await ita.response.defer(ephemeral=True)

        # 1. get/create profile
        # 2. check/create monthly claim
        # 3. call tremendous
        # 4. update claim
        # 5. respond

