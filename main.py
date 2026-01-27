import os
import sys
import asyncio
from bot import Bot

BOT_TOKEN: str | None = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("[ERROR]: Bot token environment variable is unset! Set in venv/bin/activate")
    sys.exit(1)
    

bot = Bot()

async def main() -> None:
    async with bot:
        await bot.start(BOT_TOKEN)

