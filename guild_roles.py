# Extensions for role selection within a Discord guild (server) using discord.py library.
#!/usr/bin/env python3

import discord
from discord import app_commands
from discord.ext import commands

ROLE_BUTTONS: dict[str, int] = {
    "Breaking Army": 1523825464135647353,
    "Showdown": 1523825591181381773,
    "Guild Tower (Skyward Bond)": 1523825690020020234,
    "Guild War (GvG)": 1523825823566659648,
    "Guild Hero's Realm": 1523826004295159878,
    "Guild Party": 1523827362922238122,
}

class GuildRoles(commands.GroupCog, name="guild"):
    """utility command group for role self-assignment."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roles", description="Choose your guild roles")
    async def roles_cmd(self, ita: discord.Interaction):
        embed = discord.Embed(
            title="Guild Role Selector",
            description=(
                "Use the buttons below to add or remove guild roles.\n\n"
                "If you already have a role, clicking its button will remove it.\n\n"
                "Note that selecting a role here will determine when you get pinged for guild events and announcements."
            ),
            color=discord.Color.blurple(),
        )

        for label, role_id in ROLE_BUTTONS.items():
            embed.add_field(
                name=label,
                value=f"<@&{role_id}>",
                inline=True,
            )

        await ita.response.send_message(
            embed=embed,
            view=GuildRoleView(),
            ephemeral=True,
        )


class GuildRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

        for label, role_id in ROLE_BUTTONS.items():
            self.add_item(GuildRoleButton(label=label, role_id=role_id))
        self.add_item(AssignAllButton())

class AssignAllButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Assign All Roles",
            style=discord.ButtonStyle.success,
        )

    async def callback(self, ita: discord.Interaction):
        if ita.guild is None:
            await ita.response.send_message(
                "This can only be used in the server.",
                ephemeral=True,
            )
            return

        member = ita.guild.get_member(ita.user.id)

        if member is None:
            try:
                member = await ita.guild.fetch_member(ita.user.id)
            except discord.DiscordException:
                await ita.response.send_message(
                    "Could not find your server membership. Try again.",
                    ephemeral=True,
                )
                return

        roles_to_add = []
        for role_id in ROLE_BUTTONS.values():
            role = ita.guild.get_role(role_id)
            if role and role not in member.roles:
                roles_to_add.append(role)

        if not roles_to_add:
            await ita.response.send_message(
                "You already have all the guild roles.",
                ephemeral=True,
            )
            return

        try:
            await member.add_roles(
                *roles_to_add,
                reason="Guild role selector",
            )
            added_roles_mentions = ", ".join(role.mention for role in roles_to_add)
            await ita.response.send_message(
                f"Added roles: {added_roles_mentions}",
                ephemeral=True,
            )
        except discord.Forbidden:
            await ita.response.send_message(
                (
                    "I do not have permission to manage some of those roles.\n\n"
                    "Make sure my bot role is above the roles I am trying to assign."
                ),
                ephemeral=True,
            )
        except discord.HTTPException:
            await ita.response.send_message(
                "Discord returned an error while updating your roles. Please try again.",
                ephemeral=True,
            )

class GuildRoleButton(discord.ui.Button):
    def __init__(self, label: str, role_id: int):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
        )
        self.role_id = role_id

    async def callback(self, ita: discord.Interaction):
        if ita.guild is None:
            await ita.response.send_message(
                "This can only be used in the server.",
                ephemeral=True,
            )
            return

        member = ita.guild.get_member(ita.user.id)

        if member is None:
            try:
                member = await ita.guild.fetch_member(ita.user.id)
            except discord.DiscordException:
                await ita.response.send_message(
                    "Could not find your server membership. Try again.",
                    ephemeral=True,
                )
                return

        role = ita.guild.get_role(self.role_id)

        if role is None:
            await ita.response.send_message(
                "That role could not be found. Please contact an administrator.",
                ephemeral=True,
            )
            return

        try:
            if role in member.roles:
                await member.remove_roles(
                    role,
                    reason="Guild role selector",
                )

                await ita.response.send_message(
                    f"Removed role: {role.mention}",
                    ephemeral=True,
                )
            else:
                await member.add_roles(
                    role,
                    reason="Guild role selector",
                )

                await ita.response.send_message(
                    f"Added role: {role.mention}",
                    ephemeral=True,
                )

        except discord.Forbidden:
            await ita.response.send_message(
                (
                    "I do not have permission to manage that role.\n\n"
                    "Make sure my bot role is above the role I am trying to assign."
                ),
                ephemeral=True,
            )

        except discord.HTTPException:
            await ita.response.send_message(
                "Discord returned an error while updating your role. Please try again.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildRoles(bot))
