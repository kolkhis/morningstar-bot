import os
import sys
import asyncio
import discord
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

async def main() -> None:
    async with bot:
        await bot.start(BOT_TOKEN)

