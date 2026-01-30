import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot import Bot

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


async def main() -> None:
    async with bot:
        await bot.start(BOT_TOKEN)


# Example parameter description, add `app_commands.describe` decorator:
# @bot.tree.command(name="setposttime", description="Set the daily post time (server timezone setting in code)")
# @app_commands.describe(hour="0-23", minute="0-59")

