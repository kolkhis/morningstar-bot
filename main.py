import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot import Bot, LEVEL_THRESHOLDS, EVENT_ROLE_ID, EVENT_REQUIRED_LEVEL
import json

import datetime as dt
import locale
locale.setlocale(locale.LC_TIME, 'C') # use English month names

# Monday, Tue, Wed, Thursday guild party will be at 19:00
# The rest of days, guild party will be at 15:00
# - Guild party can be changed from 19:00 to 15:00 and still run the next day,
#   but aura injected at the 19:00 party will count towards the subsequent one.
# - TODO(check): See if party can seamlessly change between 15:00 and 19:00 for
#   next-day.  
# Friday, Breaking Army will be at 19:00
# Friday, Showdown will be at 20:00
GUILD_EVENTS: dict[str, dict[str, str]] = {
    "Guild Party": {
        "Monday": "19:00",
        "Tuesday": "19:00",
        "Wednesday": "19:00",
        "Thursday": "15:00",
        "Friday": "15:00",
        "Saturday": "15:00",
        "Sunday": "15:00",
        },
    "Breaking Army": {
        "Friday": "19:30",
        "Saturday": "14:00",
        },
    "Showdown": {
        "Friday": "20:00",
        "Saturday": "14:30",
        },
    "Guild War": {
        "Saturday": "14:30",
        "Sunday": "14:30"
        },
    "Guild Hero Realm": {
        "Saturday": "15:10",
        "Sunday": "17:00",
        },
}


DAY_TO_WEEKDAY = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


MORNINSTAR_ROLE_ID:int = 1467564680401785090
GUILD_NOTIFICATION_CHANNEL_ID:int = 1467566735535378432
GUILD_ADMINS_CHANNEL_ID:int = 0

BOT_TOKEN: str = os.environ.get('BOT_TOKEN', 'empty')
if BOT_TOKEN == 'empty':
    sys.stderr.write('[ERROR]: BOT_TOKEN environment variable is unset! Set in venv/bin/activate\n')
    sys.exit(1)

bot: Bot = Bot()

################### USER/LEVEL COMMANDS #################
@bot.tree.command(name="check-level", description="Fetch the stats for a specific user")
@app_commands.describe(user="The user to fetch stats for")
async def fetch_stats_cmd(ita: discord.Interaction, user: discord.User):
    row = bot.get_user_stats(user.id)
    if row is None:
        await ita.response.send_message("User not found in the database.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Level Stats",
        description=f"Stats for {user.mention}",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Level", value=str(row["level"]), inline=True)
    embed.add_field(name="Messages", value=str(row["message_count"]), inline=True)

    if user.display_avatar:
        embed.set_thumbnail(url=user.display_avatar.url)
    await ita.response.send_message(embed=embed, ephemeral=True)
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


@bot.tree.command(name="users_by_level", description="Get a list of all users of a specified level")
@app_commands.describe(level="The level to filter users by")
async def users_by_level(ita: discord.Interaction, level: int):
    if level < 0 or level > max(LEVEL_THRESHOLDS.keys()):
        await ita.response.send_message(f"Invalid level. Please provide a level between 0 and {max(LEVEL_THRESHOLDS.keys())}.", ephemeral=True)
        return
    rows = bot.get_users_by_level(level)
    if not rows:
        await ita.response.send_message(f"No users found at level {level}.", ephemeral=True)
        return
    lines = []

    for idx, row in enumerate(rows, start=1):
        lines.append(f"{idx:>2}. <@{row['user_id']}> - {row['message_count']} messages")
    await ita.response.send_message(f"# Users at level {level}:\n" + "\n".join(lines), ephemeral=True)
    # user_mentions = [f"<@{user['user_id']}>" for user in lines]
    # mentions_str = "\n".join(user_mentions)
    # await ita.response.send_message(f"Users at level {level}:\n{mentions_str}", ephemeral=True)


@bot.tree.command(name="count_users_over_level", description="Get count of all users of a specified level and above")
@app_commands.describe(level="The level to filter users by")
async def count_users_over_level(ita: discord.Interaction, level: int):
    if level < 0 or level > max(LEVEL_THRESHOLDS.keys()):
        await ita.response.send_message(f"Invalid level. Please provide a level between 0 and {max(LEVEL_THRESHOLDS.keys())}.", ephemeral=True)
        return
    count = bot.count_users_above_level(level)
    if not count:
        await ita.response.send_message(f"No users found above level {level}.", ephemeral=True)
        return
    await ita.response.send_message(f"Number of users level {level} and above: {count}")


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

    today = dt.date.today()
    for event_name, schedule in GUILD_EVENTS.items():
        lines: list[str] = []

        for day, time_str in schedule.items():
            event_time = dt.datetime.strptime(time_str, "%H:%M").time()
            # target_weekday = dt.datetime.strptime(day, "%A").weekday()
            target_weekday = DAY_TO_WEEKDAY[day]
            days_ahead = (target_weekday - today.weekday()) % 7
            target_date = today + dt.timedelta(days=days_ahead)
            event_dt = dt.datetime.combine(target_date, event_time)
            timestamp = discord.utils.format_dt(event_dt, style="t")
            lines.append(f"**{day}** at {timestamp}" + (" **(today)**" if target_weekday == today.weekday() else ""))

        # Join all day/time entries for this event
        value = "\n".join(lines)
        embed.add_field(
            name=event_name,
            value=f"{value}\n*(your local time)*",
            inline=False,
        )
    await ita.response.send_message(embed=embed)
    return

@tasks.loop(minutes=1)
async def guild_event_notification_loop():
    guild_notification_channel = bot.get_channel(GUILD_NOTIFICATION_CHANNEL_ID)
    if guild_notification_channel is None:
        guild_notification_channel = await bot.fetch_channel(GUILD_NOTIFICATION_CHANNEL_ID)

    if not isinstance(guild_notification_channel, discord.TextChannel):
        return

    now = dt.datetime.now()
    current_day = now.strftime("%A")

    for event_name, schedule in GUILD_EVENTS.items():
        event_time_str = schedule.get(current_day)
        if event_time_str is None:
            continue

        event_time = dt.datetime.strptime(event_time_str, "%H:%M").time()

        if now.hour != event_time.hour or now.minute != event_time.minute:
            continue

        timestamp = discord.utils.format_dt(
            dt.datetime.combine(dt.date.today(), event_time),
            style="t",
        )


        if event_name == "Guild Party":
            await guild_notification_channel.send(f"""
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting! Get ready!
Guild Party is today at {timestamp}, your local time.

To participate:
Go to the guild base (open guild menu and hit space) and press K to inject aura (it's free and extends party duration!).
""")

        elif event_name == "Breaking Army":
            await guild_notification_channel.send(f"""
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting!
Breaking Army is today at {timestamp}, your local time.

To participate:
Go to the guild menu, select "Events", find Breaking Army and select it to teleport there!
""")

        elif event_name == "Showdown":
            await guild_notification_channel.send(f"""
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting!
Showdown is today, weekly on {current_day}, at {timestamp}, your local time.

To participate:
Go to the guild base, turn left and find the arena right outside.
""")

        elif event_name == "Guild War":
            await guild_notification_channel.send(f"""
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting!
Guild War is today, weekly on {current_day}, at {timestamp}.
Get ready to defend our honor!
""")

        elif event_name == "Guild Hero Realm":
            await guild_notification_channel.send(f"""
<@&{MORNINSTAR_ROLE_ID}> Reminder: **{event_name}** is starting!
Guild Hero Realm is today, weekly at {current_day} at {timestamp}.

To participate:
Log in and send a message in the guild chat for an invite!
""")
    return

@guild_event_notification_loop.before_loop
async def before_event_notification_loop():
    await bot.wait_until_ready()

async def main() -> None:
    async with bot:
        print("Bot starting...")
        await bot.load_extension("faction_quiz")

        if not guild_event_notification_loop.is_running():
            guild_event_notification_loop.start()

        await bot.start(BOT_TOKEN)
        print("Bot is done.")
        return

if __name__ == '__main__':
    asyncio.run(main())

