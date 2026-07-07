import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot import Bot, LEVEL_THRESHOLDS

import datetime as dt
from zoneinfo import ZoneInfo
EASTERN_TZ = ZoneInfo("America/New_York")  # Eastern Time Zone

import locale
locale.setlocale(locale.LC_TIME, 'C') # use English month names

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
    "Guild War (GvG)": {
        "Saturday": "14:30",
        "Sunday": "14:30"
        },
    "Guild Hero's Realm": {
        "Saturday": "15:10",
        "Sunday": "17:00",
        },
    "Guild Tower (Skyward Bond)": {
        "Thursday": "14:00",
        "Friday": "14:00",
    },
    "Event Signup": {
        "Monday": "15:00",
    },
}

EVENT_NOTIFICATION_MESSAGES: dict[str, str] = {
    "Guild Party": """
{role_mention} Reminder: **{event_name}** is starting! Get ready!
Guild Party is today at {timestamp} ({relative_timestamp}), your local time. 
{event_name} ends about 10 minutes after it starts.

To participate:
Go to the guild base (open guild menu and hit space) and press K to inject aura. It's free and extends party duration!
""",

    "Breaking Army": """
{role_mention} Reminder: **{event_name}** is starting!
Breaking Army is today at {timestamp} ({relative_timestamp}), your local time.
{event_name} ends 2 hours after it starts.

To participate:
Go to the guild menu, select "Events", find Breaking Army and select it to teleport there.
""",

    "Showdown": """
{role_mention} Reminder: **{event_name}** is starting!
Showdown is today, weekly on {current_day}, at {timestamp} ({relative_timestamp}), your local time.
{event_name} ends 2 hours after it starts.

To participate:
Go to the guild base, turn left and find the arena right outside.
""",

    "Guild War": """
{role_mention} Reminder: **{event_name}** is starting!
Guild War is today, weekly on {current_day}, at {timestamp} ({relative_timestamp}).

Get ready to defend our honor!
""",

    "Guild Hero Realm": """
{role_mention} Reminder: **{event_name}** is starting!
Guild Hero Realm is today, weekly on {current_day} at {timestamp} ({relative_timestamp}).

Please check the messages from the Raid Helper in <#1467567050611495058> for
details on the events happening this week and sign up for the ones you want to 
participate in.
""",

    "Guild Tower (Skyward Bond)": """
{role_mention} Reminder: **{event_name}** is starting!
Guild Tower (Skyward Bond) is weekly on {current_day} at {timestamp} ({relative_timestamp}).

We do two runs per week:
- Thursday runs are when we take the highest DPS in guild to try and clear the highest floors we can.
- Friday runs are typically for learning and getting people through the lower floors.

Signups for Guild Tower and the rest of the weekly events are posted in <#1467567050611495058> every Monday.
Anyone can sign up to participate. If you are at all interested in doing Guild Tower, please sign up!

- If you'd like to be part of the main team, post your DPS in this thread: <#1514101741258543256>
- It also helps to set up your WWM profile through Kolbot. Use `/wwm profile` to do it. It's really quick.

""",
# > Use `/daily-guild-events` and `/weekly-guild-events` to check the schedule.

    "Event Signup": """
Reminder: Weekly **{event_name}** has started!
Event signups are posted weekly on {current_day} at {timestamp} by the RaidBot.

Check the messages from the Raid Bot in <#1467567050611495058> for details on the events happening this week and sign up for the ones you want to participate in.

Please check the times carefully and make sure you can make the events you sign up for.

> Use `/daily-guild-events` and `/weekly-guild-events` to check the schedule.
""",
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

from guild_roles import ROLE_BUTTONS
def get_event_role_mention(event_name: str) -> str:
    role_id = ROLE_BUTTONS.get(event_name)
    if role_id is not None:
        return f"<@&{role_id}>"
    return f"<@&{MORNINSTAR_ROLE_ID}>"

def build_event_notification_message(
    event_name: str,
    current_day: str,
    timestamp: str,
    relative_timestamp: str) -> str | None:
    template = EVENT_NOTIFICATION_MESSAGES.get(event_name)

    if template is None:
        return None

    role_mention = get_event_role_mention(event_name)

    message = template.format(
        role_mention=role_mention,
        event_name=event_name,
        current_day=current_day,
        timestamp=timestamp,
        relative_timestamp=relative_timestamp,
    )
    return message.strip()


BOT_TOKEN: str = os.environ.get('BOT_TOKEN', 'empty')
if BOT_TOKEN == 'empty':
    sys.stderr.write('[ERROR]: BOT_TOKEN environment variable is unset! Set in venv/bin/activate\n')
    sys.exit(1)

bot: Bot = Bot()

def build_daily_schedule_embed() -> discord.Embed:
    date_timestamp = discord.utils.format_dt(dt.datetime.now(), style="D")
    today = dt.date.today()
    embed = discord.Embed(
        title="Daily Guild Event Schedule",
        description=f"Below is today's **daily** schedule for **{today.strftime('%A')}**, {date_timestamp}.\nAll event times are localized.",
        color=discord.Color.green(),
    )
    for event_name, schedule in GUILD_EVENTS.items():
        lines: list[str] = []
        for day, time_str in schedule.items():
            event_time = dt.datetime.strptime(time_str, "%H:%M").time()
            target_weekday = DAY_TO_WEEKDAY[day]
            days_ahead = (target_weekday - today.weekday()) % 7
            target_date = today + dt.timedelta(days=days_ahead)
            event_dt = dt.datetime.combine(target_date, event_time)
            timestamp = discord.utils.format_dt(event_dt, style="t")
            relative_timestamp = discord.utils.format_dt(event_dt, style="R")
            if target_weekday == today.weekday():
                lines.append(f"- **{day}** at {timestamp} ({relative_timestamp})" + (" **(today)**" if target_weekday == today.weekday() else ""))

        value = "\n".join(lines)
        if value:
            embed.add_field(
                name=event_name,
                value=f"{value}\n━━━━━━━━━━━━━━━━━━━━",
                inline=False,
            )
    return embed

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

# TODO: Add removal functionality for old messages to prevent clutter, or have a pinned message that gets updated with the current events instead of posting new messages each time

###### WEEKLY GUILD EVENT SCHEDULE ######
# Command to display a Discord timestamp for times of the guild events
@bot.tree.command(name="weekly-guild-events", description="Show the schedule for guild events")
async def weekly_guild_events_cmd(ita: discord.Interaction):
    embed = discord.Embed(
        title="Weekly Guild Event Schedule",
        description="Below is the **weekly** schedule for our regular guild events.\nAll event times are localized.",
        color=discord.Color.green(),
    )
    today = dt.date.today()
    for event_name, schedule in GUILD_EVENTS.items():
        lines: list[str] = []
        for day, time_str in schedule.items():
            event_time = dt.datetime.strptime(time_str, "%H:%M").time()
            target_weekday = DAY_TO_WEEKDAY[day]
            days_ahead = (target_weekday - today.weekday()) % 7
            target_date = today + dt.timedelta(days=days_ahead)
            event_dt = dt.datetime.combine(target_date, event_time)
            timestamp = discord.utils.format_dt(event_dt, style="t")
            relative_timestamp = discord.utils.format_dt(event_dt, style="R")
            lines.append(f"- **{day}** at {timestamp} ({relative_timestamp})" + (" **(today)**" if target_weekday == today.weekday() else ""))
        # Join all day/time entries for this event
        value = "\n".join(lines)
        embed.add_field(
            name=event_name,
            value=f"{value}\n━━━━━━━━━━━━━━━━━━━━",
            inline=False,
        )
    await ita.response.send_message(embed=embed, ephemeral=True)
    return

###### DAILY GUILD EVENT SCHEDULE ######
# Command to display a Discord timestamp for times of the guild events
@bot.tree.command(name="daily-guild-events", description="Show the schedule for guild events")
async def daily_guild_events_cmd(ita: discord.Interaction):
    embed = build_daily_schedule_embed()
    await ita.response.send_message(embed=embed, ephemeral=True)
    return

@bot.tree.command(name="do-not-use", description="DM util")
async def dm_all_except_cmd(ita: discord.Interaction, excluded_member: discord.Member, message: str):
    kol = 103719303441825792
    if not ita.user.guild_permissions.administrator and not (ita.user.id == kol):
        await ita.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    if ita.guild is None:
        await ita.response.send_message("This command must be used in a server.",ephemeral=True)
        return

    await ita.response.defer(ephemeral=True)
    await ita.followup.send(f"Starting DM process. Excluding {excluded_member.mention}.", ephemeral=True)

    formatted_msg = message.replace("\\n", "\n") # allow newlines to be included in the message via \n

    # print(f"Formatted msg to send:\n{formatted_msg}")
    sent = 0
    skipped = 0
    failed = 0
    failed_users: list[str] = []

    for member in ita.guild.members:
        if member.bot or member.id == excluded_member.id:
            skipped += 1
            continue

        print(f"Attempting to DM {member.name}...")
        try:
            await member.send(formatted_msg)
            sent += 1
            await asyncio.sleep(0.2)
        except discord.Forbidden:
            failed += 1 # DMs disabled or they blocked the bot
            failed_users.append(member.name)
        except discord.HTTPException:
            sys.stderr.write(f"ERROR: HTTPException when trying to DM {member.name}. Skipping.\n")
            failed += 1 # Discord API failure
            failed_users.append(member.name)
        except Exception as e:
            sys.stderr.write(f"ERROR: Unexpected exception when trying to DM {member.name}: {e}\n")
            failed += 1 # catchall
            failed_users.append(member.name)

    await ita.followup.send(
        "DM broadcast complete.\n"
        f"Sent: **{sent}**\n"
        f"Skipped: **{skipped}**\n"
        f"Failed: **{failed}**",
        ephemeral=True
    )

@tasks.loop(minutes=1)
async def guild_event_notification_loop():
    guild_notification_channel = bot.get_channel(GUILD_NOTIFICATION_CHANNEL_ID)

    if guild_notification_channel is None:
        guild_notification_channel = await bot.fetch_channel(GUILD_NOTIFICATION_CHANNEL_ID)

    if not isinstance(guild_notification_channel, discord.TextChannel):
        return

    now = dt.datetime.now(EASTERN_TZ)
    current_day = now.strftime("%A")

    for event_name, schedule in GUILD_EVENTS.items():
        event_time_str = schedule.get(current_day)

        if event_time_str is None:
            continue

        event_time = dt.datetime.strptime(event_time_str, "%H:%M").time()

        if now.hour != event_time.hour or now.minute != event_time.minute:
            continue

        event_dt = dt.datetime.combine(
            now.date(),
            event_time,
            tzinfo=EASTERN_TZ,
        )

        timestamp = discord.utils.format_dt(event_dt, style="t")
        relative_timestamp = discord.utils.format_dt(event_dt, style="R")

        message = build_event_notification_message(
            event_name=event_name,
            current_day=current_day,
            timestamp=timestamp,
            relative_timestamp=relative_timestamp,
        )

        if message is None:
            continue

        await guild_notification_channel.send(message)
        return

@tasks.loop(time=dt.time(hour=0, minute=0, second=0, tzinfo=EASTERN_TZ))
async def daily_guild_schedule_post_loop():
    guild_notification_channel = bot.get_channel(GUILD_NOTIFICATION_CHANNEL_ID)
    if guild_notification_channel is None:
        guild_notification_channel = await bot.fetch_channel(GUILD_NOTIFICATION_CHANNEL_ID)
    if not isinstance(guild_notification_channel, discord.TextChannel):
        return
    embed = build_daily_schedule_embed()
    await guild_notification_channel.send(embed=embed)

@daily_guild_schedule_post_loop.before_loop
async def before_daily_guild_schedule_post_loop():
    await bot.wait_until_ready()

@guild_event_notification_loop.before_loop
async def before_event_notification_loop():
    await bot.wait_until_ready()

async def main() -> None:
    async with bot:
        print("Bot starting...")
        print("Loading extensions...")
        try:
            await bot.load_extension("faction_quiz")
            print ("Faction quiz extension loaded.")
            await bot.load_extension("wwm")
            print("WWM extension loaded.")
            await bot.load_extension("guild_roles")
            print("All extensions loaded.")
        except Exception as e:
            sys.stderr.write(f"Error loading extensions: {e}\n")
            raise
        if not guild_event_notification_loop.is_running():
            guild_event_notification_loop.start()
        if not daily_guild_schedule_post_loop.is_running():
            daily_guild_schedule_post_loop.start()

        await bot.start(BOT_TOKEN)
        print("Bot is done.")
        return

if __name__ == '__main__':
    asyncio.run(main())
