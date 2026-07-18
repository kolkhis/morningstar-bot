import os
import sys
import re
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from ext.tremendous_client import TremendousClient

# Lets eligible members claim a monthly coffee fund reward via the Tremendous
# API (see ./tremendous_client.py). Claims reset on the 1st of every month (UTC).

COFFEE_AMOUNT_USD: float = float(os.environ.get("COFFEE_AMOUNT_USD", "5"))

# the preset product IDs to use for Tremendous rewards. These should be comma-separated in the
# env var (e.g., "prod_123,prod_456"). 
# If empty, the Tremendous API will reject the order.
TREMENDOUS_PRODUCT_IDS: list[str] = [
    p.strip() for p in os.environ.get("TREMENDOUS_PRODUCT_IDS", "").split(",") if p.strip()
]

# Role required to claim the coffee fund. Defaults to the general Morningstar
# guild member role; override with COFFEE_ELIGIBLE_ROLE_ID to restrict further.
COFFEE_ELIGIBLE_ROLE_ID: int = int(os.environ.get("COFFEE_ELIGIBLE_ROLE_ID", "1467564680401785090"))

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def current_claim_month() -> str:
    """The current UTC claim period, e.g. '2026-07'. Claims reset on the 1st of each month (UTC)."""
    return discord.utils.utcnow().strftime("%Y-%m")


class CoffeeFund(commands.GroupCog, name="coffee"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tremendous = TremendousClient()
        self.init_db()
        if not TREMENDOUS_PRODUCT_IDS:
            sys.stderr.write(
                "[WARN]: TREMENDOUS_PRODUCT_IDS is unset/empty. Tremendous orders "
                "may be rejected without at least one product ID.\n"
            )

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

    ################ PROFILE HELPERS ################
    def get_profile(self, user_id: int) -> Optional[sqlite3.Row]:
        cursor = self.bot.db.cursor()
        cursor.execute(
            "SELECT * FROM coffee_profiles WHERE user_id = ?",
            (user_id,),
        )
        return cursor.fetchone()

    def upsert_profile(self, user_id: int, recipient_name: str, recipient_email: str) -> None:
        now = discord.utils.utcnow().isoformat()
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            INSERT INTO coffee_profiles (user_id, recipient_name, recipient_email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                recipient_name = excluded.recipient_name,
                recipient_email = excluded.recipient_email,
                updated_at = excluded.updated_at
            """,
            (user_id, recipient_name, recipient_email, now, now),
        )
        self.bot.db.commit()

    ################ CLAIM HELPERS ################
    def get_claim(self, user_id: int, claim_month: str) -> Optional[sqlite3.Row]:
        cursor = self.bot.db.cursor()
        cursor.execute(
            "SELECT * FROM coffee_claims WHERE user_id = ? AND claim_month = ?",
            (user_id, claim_month),
        )
        return cursor.fetchone()

    def try_reserve_claim(
        self,
        user_id: int,
        claim_month: str,
        amount_cents: int,
        currency_code: str,
    ) -> Optional[int]:
        """
        Atomically reserve this month's claim slot for a user.

        The UNIQUE(user_id, claim_month) constraint is the actual guardrail against
        double-claiming (including double-submits/races); this only decides whether
        a `failed` claim from earlier this month can be retried.

        Returns the claim id on success, or None if a claim already exists this
        month (pending or successful).
        """
        now = discord.utils.utcnow().isoformat()
        cursor = self.bot.db.cursor()

        cursor.execute(
            """
            UPDATE coffee_claims
            SET status = 'pending', amount_cents = ?, currency_code = ?, created_at = ?
            WHERE user_id = ? AND claim_month = ? AND status = 'failed'
            """,
            (amount_cents, currency_code, now, user_id, claim_month),
        )
        if cursor.rowcount > 0:
            self.bot.db.commit()
            row = self.get_claim(user_id, claim_month)
            return row["id"] if row else None

        try:
            cursor.execute(
                """
                INSERT INTO coffee_claims (user_id, claim_month, amount_cents, currency_code, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (user_id, claim_month, amount_cents, currency_code, now),
            )
            self.bot.db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            self.bot.db.rollback()
            return None

    def mark_claim_success(self, claim_id: int, order_id: Optional[str], reward_id: Optional[str]) -> None:
        cursor = self.bot.db.cursor()
        cursor.execute(
            """
            UPDATE coffee_claims
            SET status = 'success', tremendous_order_id = ?, tremendous_reward_id = ?
            WHERE id = ?
            """,
            (order_id, reward_id, claim_id),
        )
        self.bot.db.commit()

    def mark_claim_failed(self, claim_id: int) -> None:
        cursor = self.bot.db.cursor()
        cursor.execute(
            "UPDATE coffee_claims SET status = 'failed' WHERE id = ?",
            (claim_id,),
        )
        self.bot.db.commit()

    def is_eligible(self, member: discord.Member) -> bool:
        if not COFFEE_ELIGIBLE_ROLE_ID:
            return True
        return any(role.id == COFFEE_ELIGIBLE_ROLE_ID for role in member.roles)

    ################ COMMANDS ################
    @app_commands.command(name="setup", description="Set up or update your coffee fund recipient info")
    @app_commands.describe(
        name="Your full name, as it should appear on the reward",
        email="The email address that should receive your reward",
    )
    async def setup_cmd(self, ita: discord.Interaction, name: str, email: str):
        name = name.strip()
        email = email.strip()

        if not name:
            await ita.response.send_message("Please provide a valid name.", ephemeral=True)
            return
        if not EMAIL_RE.match(email):
            await ita.response.send_message("Please provide a valid email address.", ephemeral=True)
            return

        self.upsert_profile(ita.user.id, name, email)
        await ita.response.send_message(
            f"Coffee fund profile saved. Rewards will be sent to **{email}**.",
            ephemeral=True,
        )

    @app_commands.command(name="status", description="Check your coffee fund profile and this month's claim status")
    async def status_cmd(self, ita: discord.Interaction):
        profile = self.get_profile(ita.user.id)
        claim_month = current_claim_month()
        claim = self.get_claim(ita.user.id, claim_month)

        embed = discord.Embed(
            title="Coffee Fund Status",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Profile",
            value=f"Name: {profile['recipient_name']}\nEmail: {profile['recipient_email']}" if profile else "Not set up. Use `/coffee setup`.",
            inline=False,
        )

        if claim is None:
            claim_status = "Not claimed yet this month."
        elif claim["status"] == "success":
            claim_status = f"Claimed for **{claim_month}**. Enjoy your coffee!"
        elif claim["status"] == "pending":
            claim_status = "A claim is currently being processed."
        else:
            claim_status = "Last attempt failed. You can try `/coffee claim` again."

        embed.add_field(name=f"This Month ({claim_month})", value=claim_status, inline=False)
        embed.set_footer(text="Claims reset on the 1st of each month (UTC).")

        await ita.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="claim", description="Claim this month's coffee fund reward")
    async def claim_cmd(self, ita: discord.Interaction):
        await ita.response.defer(ephemeral=True)

        if ita.guild is None:
            await ita.followup.send("This command must be used in the server.", ephemeral=True)
            return

        member = ita.guild.get_member(ita.user.id)
        if member is None:
            try:
                member = await ita.guild.fetch_member(ita.user.id)
            except discord.DiscordException:
                await ita.followup.send("Could not verify your server membership. Please try again.", ephemeral=True)
                return

        if not self.is_eligible(member):
            await ita.followup.send(
                "You don't have the role required to claim the coffee fund.",
                ephemeral=True,
            )
            return

        profile = self.get_profile(ita.user.id)
        if profile is None:
            await ita.followup.send(
                "You need to set up your coffee fund profile first. Use `/coffee setup` to input your name and email.",
                ephemeral=True,
            )
            return

        claim_month = current_claim_month()
        existing = self.get_claim(ita.user.id, claim_month)
        if existing is not None and existing["status"] == "success":
            await ita.followup.send(
                f"You've already claimed your coffee fund reward for **{claim_month}**. "
                "Come back after the 1st of next month!",
                ephemeral=True,
            )
            return

        if existing is not None and existing["status"] == "pending":
            await ita.followup.send(
                "A claim is already being processed for you this month. Check `/coffee status` shortly.",
                ephemeral=True,
            )
            return

        amount_cents = round(COFFEE_AMOUNT_USD * 100)
        claim_id = self.try_reserve_claim(ita.user.id, claim_month, amount_cents, "USD")
        if claim_id is None:
            # Lost a race against a concurrent claim; the other request owns this month's slot
            await ita.followup.send(
                "You've already claimed (or are claiming) this month's reward.",
                ephemeral=True,
            )
            return

        try:
            result = await self.tremendous.create_email_reward(
                recipient_name=profile["recipient_name"],
                recipient_email=profile["recipient_email"],
                amount_usd=COFFEE_AMOUNT_USD,
                product_ids=TREMENDOUS_PRODUCT_IDS,
            )
        except Exception as e:
            self.mark_claim_failed(claim_id)
            sys.stderr.write(f"[ERROR]: Tremendous claim failed for user {ita.user.id}: {e}\n")
            await ita.followup.send(
                "Something went wrong sending your reward. Please try `/coffee claim` again in a moment.",
                ephemeral=True,
            )
            return

        order = result.get("order") or {}
        rewards = order.get("rewards") or [{}]
        reward = rewards[0] if rewards else {}
        self.mark_claim_success(claim_id, order.get("id"), reward.get("id"))

        await ita.followup.send(
            f"Sent **${COFFEE_AMOUNT_USD:.2f}** to **{profile['recipient_email']}**.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CoffeeFund(bot))
