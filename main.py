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

GUILD_EVENTS: dict[str, str] = {
    "Guild Party": "15:00",
    "Breaking Army": "14:00",
    "Showdown": "14:30",
    "Guild War": "16:30",
}

MORNINSTAR_ROLE_ID:int = 1467564680401785090
GUILD_NOTIFICATION_CHANNEL_ID:int = 1467566735535378432

BOT_TOKEN: str = os.environ.get('BOT_TOKEN', 'empty')
if BOT_TOKEN == 'empty':
    sys.stderr.write('[ERROR]: Bot token environment variable is unset! Set in venv/bin/activate\n')
    sys.exit(1)

bot: Bot = Bot()

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
    if row is None:
        await ita.response.send_message(f"User {ita.user.name} not found in the database.", ephemeral=True)
        return
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
# TODO(feat): Add command to end giveaway early
# TODO(feat): Add command to reroll giveaway winner
# TODO(feat): Add command to see past giveaways and winners
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

###### GUILD EVENT NOTIFICATIONS ######
# Command to display a Discord timestamp for times of the guild events
@bot.tree.command(name="guild_events", description="Show the schedule for guild events")
async def guild_events_cmd(ita: discord.Interaction):
    embed = discord.Embed(
        title="Guild Event Schedule",
        description="Here are the scheduled times for our regular guild events:",
        color=discord.Color.green(),
    )
    for event_name, event_time_str in GUILD_EVENTS.items():
        event_time = dt.datetime.strptime(event_time_str, "%H:%M").time()
        timestamp = discord.utils.format_dt(
            dt.datetime.combine(dt.date.today(), event_time), style="t"
        )
        if event_name == "Guild Party":
            embed.add_field(name=event_name, value=f"Daily at {timestamp} (your local time)", inline=False)
        elif event_name == "Guild War":
            embed.add_field(name=event_name, value=f"Every Saturday and Sunday at {timestamp} (your local time)", inline=False)
        else:
            embed.add_field(name=event_name, value=f"Every Friday and Saturday at {timestamp} (your local time)", inline=False)

    await ita.response.send_message(embed=embed)
    return

# Add loop to send notification for guild party, breaking army, and showdown
@tasks.loop(minutes=1)
async def guild_event_notification_loop():
    guild_notification_channel = bot.get_channel(GUILD_NOTIFICATION_CHANNEL_ID)
    if guild_notification_channel is None:
        guild_notification_channel = await bot.fetch_channel(GUILD_NOTIFICATION_CHANNEL_ID)

    now = dt.datetime.now()
    timestamp = discord.utils.format_dt(discord.utils.utcnow(), style="t")
    
    for event_name, event_time_str in GUILD_EVENTS.items():
        event_time = dt.datetime.strptime(event_time_str, "%H:%M").time()
        if (
            event_name == "Guild Party" 
            and now.time().hour == event_time.hour 
            and now.time().minute == event_time.minute
        ):
            await guild_notification_channel.send(f"<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting! Get ready! (daily at {timestamp}, your local time)")
        elif (
            event_name in ["Breaking Army", "Showdown"] \
            and now.strftime("%A") in ["Friday", "Saturday"] \
            and now.time().hour == event_time.hour \
            and now.time().minute == event_time.minute
        ):
        # 1467564680401785090
            if event_name == "Breaking Army":
                await guild_notification_channel.send(f"""
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting! Schedule for
BA is every Friday and Saturday at {timestamp}, your local time.

To participate:
Go to the guild menu, select "Events", find Breaking Army and select it to teleport there!"""
                )
            elif event_name == "Showdown":
                await guild_notification_channel.send(f"""{msg}
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting! Schedule for
Showdown is every Friday and Saturday at {timestamp}, your local time.

To participate:
Go to the guild base, turn left and find the arena right outside."""
                )
        elif event_name == "Guild War":
            if (
                now.strftime("%A") == "Saturday" or now.strftime("%A") == "Sunday"
                and now.time().hour == event_time.hour
                and now.time().minute == event_time.minute
                ):
                    await guild_notification_channel.send(f"""
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting!
Schedule for Guild War is every Saturday and Sunday at {timestamp}.
Get ready to defend our honor!""")
    return

@guild_event_notification_loop.before_loop
async def before_event_notification_loop():
    await bot.wait_until_ready()

async def main() -> None:
    async with bot:
        print("Bot starting...")
        if not guild_event_notification_loop.is_running():
            guild_event_notification_loop.start()

        await bot.start(BOT_TOKEN)
        print("Bot is done.")
        return

if __name__ == '__main__':
    asyncio.run(main())

