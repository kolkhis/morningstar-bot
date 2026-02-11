import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot import Bot
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

async def title_to_datetime(date: str):
    """
    Take in a date and return a datetime object. The strftime format for the forum
    posts' titles is '%B %d, %Y'. This function will take in the date as a
    string and return a datetime object using that format.
    """
    return dt.datetime.strptime(date, '%B %d, %Y')

async def load_last_post_date() -> str | None:
    """Fetch and return the value of "last_post_date" in the bot's questions file"""
    if not os.path.exists(bot.question_file):
        sys.stderr.write(f'[ERROR]: The questions file ({bot.question_file}) was not found!\n')
        return None
    with open(bot.question_file, "r", encoding="utf-8") as f:
        return json.load(f).get("last_post_date")

async def save_last_post_date(date: str) -> None:
    """Update the value of "last_post_date" in the bot's questions file"""
    with open(bot.question_file, "r", encoding="utf-8") as f:
        json.dump({"last_post_date": date}, f)


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

@bot.tree.command(name="addpost", description="Command to manually add a post to the forum channel")
@app_commands.describe(title="Title of the forum post", body="The contents of the forum post")
async def addpost(ita: discord.Interaction, title: str, body: str):
    print(f"Attempting to add forum post with the title \"{title}\" and " \
          f"content:\n {body}")
    now = dt.datetime.now()
    title = now.strftime('%B %d, %Y')
    if not title or not body:
        await ita.response.send_message("ERROR: Either a body or title was not provided!")
        return
    post = await bot.add_forum_post(title=title, body=body)
    await ita.response.send_message(f"Thread was successfully created: {post.mention}")
    return

@bot.tree.command(name="addquestion", description="Add a question to the bot's "\
                  "database. It will be posted for Days of Giving later")
async def addquestion(ita: discord.Interaction, question: str):
    # TODO(security): Add user role validation
    if not question:
        await ita.response.send_message("ERROR! No question was provided to " \
                                        "/addquestion")
    await bot.add_question(new_question=question,
                           added_by=ita.user.name, 
                           date_added=dt.datetime.now())

@tasks.loop(minutes=5)
async def days_of_giving_post_loop() -> None:
    """Post once per week on Saturday"""
    now = dt.datetime.now()

    if now.strftime('%A') == POST_DAY and now.hour >= POST_HOUR and now.minute >= POST_MIN:
        # It's posting day, check last post date
        last_post_date = load_last_post_date()
        if last_post_date is None:
            sys.stderr.write('[ERROR]: Could not determine last post date\n')
            return
        with open(bot.question_file, 'r') as f:
            pass

            # Check last post date and determine if it's time to add a new one
        await bot.add_forum_post(
            title=now.strftime('%B %d, %Y'),
            body="TODO: Add question",
        )
    pass


async def main() -> None:
    async with bot:
        print("Bot starting...")
        await bot.start(BOT_TOKEN)
        print("Bot is done.")
        return

if __name__ == '__main__':
    asyncio.run(main())

# Example parameter description, add `app_commands.describe` decorator:
# @bot.tree.command(name="setposttime", description="Set the daily post time (server timezone setting in code)")
# @app_commands.describe(hour="0-23", minute="0-59")
