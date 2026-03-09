import discord
import random
import asyncio
from discord.ext import commands

TOKEN = "PUT_YOUR_TOKEN_HERE"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

gifts = [
    "1$ Skin",
    "5$ Skin",
    "10$ Battlepass"
]

@bot.command()
async def giveaway(ctx):

    msg = await ctx.send(
        "🎉 **Weekly Giveaway!**\n"
        "React with 🎉 to enter!\n"
        "⏳ Ends in 7 days."
    )

    await msg.add_reaction("🎉")

    await asyncio.sleep(604800)

    new_msg = await ctx.channel.fetch_message(msg.id)
    reaction = discord.utils.get(new_msg.reactions, emoji="🎉")

    if reaction is None:
        await ctx.send("No participants.")
        return

    users = [user async for user in reaction.users() if not user.bot]

    if len(users) == 0:
        await ctx.send("No participants.")
        return

    winner = random.choice(users)
    gift = random.choice(gifts)

    await ctx.send(f"🎉 Winner: {winner.mention}\n🎁 Prize: **{gift}**")

bot.run(TOKEN)
