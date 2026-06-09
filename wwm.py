#!/usr/bin/env python3

import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

class WWM(commands.GroupCog, name="wwm"):
    """command suite for the Where Winds Meet utility"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
