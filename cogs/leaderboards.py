import asyncio
import itertools
import functools
import math
import re
from attr import __description__
import discord
import os
from discord.ext import tasks, commands
from discord.ext.commands.errors import MissingPermissions
from discord.user import Profile
from discord.utils import get
from dns.message import Message
import aiomysql
import random
import pyowm
import threading
import time
import datetime
import dbl


class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name = "topcredit",
                    description = "Displays the top 100 users globally with the most credits on BOTrased.",
                    brief = "Displays the top 100 users in terms of credits.")
    async def topcredit(self, ctx):
        pages = self.bot.creditLeaderboardPages
        if pages == None:
            raise self.bot.BOTrasedError("100")
            return
        await self.bot.sendEmbedPages(ctx, pages)


    @commands.command(name = "topexp",
                    description = "Displays the top 100 users globally with the most experience points on BOTrased.",
                    brief = "Displays the top 100 users in terms of experience.")
    async def topexp(self, ctx):
        pages = self.bot.expLeaderboardPages
        if pages == None:
            raise self.bot.BOTrasedError("100")
            return
        await self.bot.sendEmbedPages(ctx, pages)

    
def setup(bot):
    bot.add_cog(Leaderboards(bot))