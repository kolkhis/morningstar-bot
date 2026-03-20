import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot import Bot, LEVEL_THRESHOLDS
import json

import datetime as dt
import locale
locale.setlocale(locale.LC_TIME, 'C') # use English month names

POST_HOUR: int = 9
POST_MIN: int = 0
POST_DAY: str = "Saturday"

BOT_TOKEN: str = os.environ.get('BOT_TOKEN', 'empty')

if BOT_TOKEN == 'empty':
    sys.stderr.write('[ERROR]: Bot token environment variable is unset! Set in venv/bin/activate\n')
    sys.exit(1)

bot: Bot = Bot()

@bot.tree.command(name="test", description="Test command to start")
async def testcmd(ita: discord.Interaction):
    await ita.response.send_message("Test command successfully executed")
    return

@bot.tree.command(name="testparams", description="Test command with parameter descriptions")
@app_commands.describe(hour="0-23", minute="0-59")
async def testparams(ita: discord.Interaction, hour: int, minute: int):
    await ita.response.send_message("Test command successfully executed. "\
                                    f"Arguments received: Hour: {hour}, Minute: {minute}")
    return

################### USER/LEVEL COMMANDS #################
@bot.tree.command(name="check_level", description="Check your current message count and level")
@app_commands.describe(user_id="The ID of the user to check the level for")
async def check_level_cmd(ita: discord.Interaction, user_id: str):
    """Check the level of a specific user by their ID."""
    try:
        user_id_int = int(user_id)
    except ValueError:
        await ita.response.send_message("Invalid user ID. Please provide a numeric ID.", ephemeral=True)
        return

    row = bot.get_user_stats(user_id_int)
    if row is None:
        await ita.response.send_message("User not found in the database.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Level Stats",
        description=f"Stats for <@{user_id_int}>",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Level", value=str(row["level"]), inline=True)
    embed.add_field(name="Messages", value=str(row["message_count"]), inline=True)

    if ita.user.display_avatar:
        embed.set_thumbnail(url=ita.user.display_avatar.url)
    embed.set_footer(text="Keep being involved to level up!")
    await ita.response.send_message(embed=embed)
    return

@bot.tree.command(name="level", description="Check your current message count and level")
async def level_cmd(ita: discord.Interaction):
    row = bot.get_user_stats(ita.user.id)
    embed = discord.Embed(
        title="Level Stats",
        description=f"Stats for {ita.user.mention}",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Level", value=str(row["level"]), inline=True)
    embed.add_field(name="Messages", value=str(row["message_count"]), inline=True)

    # # Include progress to next level if not max level
    level = row["level"]
    message_count = row["message_count"]

    next_level, next_threshold = bot.get_next_level_info(level)
    progress_text: str | None = None
    progress_bar: str | None = None
    if next_level is None or next_threshold is None:
        progress_text = "Max level reached!"
        progress_bar = "[██████████] 100%"
    elif level == 0:
        next_threshold = LEVEL_THRESHOLDS[1]
        progress = message_count / next_threshold * 100
        progress_text = f"{progress:.2f}% to level {next_level}"
        progress_bar = bot.build_progress_bar(message_count, next_threshold)
    elif row["level"] < max(LEVEL_THRESHOLDS.keys()):
        next_threshold = LEVEL_THRESHOLDS[level + 1]
        progress = (message_count - LEVEL_THRESHOLDS[level]) / (next_threshold - LEVEL_THRESHOLDS[level]) * 100
        progress_text = f"{progress:.2f}% to Level {next_level}"
        progress_bar = bot.build_progress_bar(message_count - LEVEL_THRESHOLDS[level], next_threshold - LEVEL_THRESHOLDS[level])
        # remaining = next_threshold - row["message_count"]

    if progress_text is not None and progress_bar is not None:
        embed.add_field(name="Progress:", value=progress_text, inline=False)
        embed.add_field(name="", value=progress_bar, inline=False)

    if ita.user.display_avatar:
        embed.set_thumbnail(url=ita.user.display_avatar.url)
    embed.set_footer(text="Keep being involved to level up!")
    await ita.response.send_message(embed=embed)
    return

################# GIVEAWAY ADMIN COMMANDS #################
@bot.tree.command(name="post_giveaway", description="Post a new giveaway")
async def post_giveaway_cmd(ita: discord.Interaction):
    if not ita.user.guild_permissions.administrator:
        await ita.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    msg = await bot.post_giveaway()
    if msg is None:
        await ita.response.send_message("Could not post giveaway. There may already be an active one.", ephemeral=True)
        return

    await ita.response.send_message(f"Giveaway posted in {msg.channel.mention}.", ephemeral=True)

@bot.tree.command(name="draw_giveaway", description="Draw the current giveaway winner")
async def draw_giveaway_cmd(ita: discord.Interaction):
    if not ita.user.guild_permissions.administrator:
        await ita.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    winner = await bot.draw_giveaway_winner()
    if winner is None:
        await ita.response.send_message("Giveaway draw completed, but no valid winner was found.", ephemeral=True)
        return

    await ita.response.send_message(f"Winner drawn: {winner.mention}", ephemeral=True)

@bot.tree.command(name="giveaway_status", description="Show current giveaway status")
async def giveaway_status_cmd(ita: discord.Interaction):
    giveaway = bot.get_active_giveaway()

    if giveaway is None:
        await ita.response.send_message("There is no active giveaway.", ephemeral=True)
        return

    await ita.response.send_message(
        f"Active giveaway message ID: `{giveaway['message_id']}`\n"
        f"Reward: **{giveaway['reward']}**\n"
        f"Emoji: {giveaway['emoji']}",
        ephemeral=True
    )

async def main() -> None:
    async with bot:
        print("Bot starting...")
        await bot.start(BOT_TOKEN)
        print("Bot is done.")
        return

if __name__ == '__main__':
    asyncio.run(main())

