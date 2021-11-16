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

class Owner(commands.Cog, name = "Owner Commands", command_attrs = dict(hidden = True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = "showservers",
                    brief = "Gives a list of all the servers that the bot is currently in.")
    @commands.is_owner()
    async def showservers(self, ctx):
        messagestring = ""
        for guild in self.bot.guilds:
            messagestring = messagestring + str(guild.name) + "\n"
        await ctx.send(messagestring)
    
    @commands.command(name = "botentrypurge",
                    brief = "Removes all entries in the database of bot users.")
    @commands.is_owner()
    async def botEntryPurge(self, ctx):
        await self.bot.wait_until_ready()
        connection = await self.bot.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute("SELECT * from users")
        result = await cursor.fetchall()
        count = 0
        failCount = 0
        for i in range(0, len(result)):
            try:
                currentUser = await self.bot.fetch_user(int(result[i][0]))
            except:
                await cursor.execute("DELETE FROM users WHERE userID = '"+str(result[i][0])+"'")
                count += 1
            try:
                if currentUser.bot:
                    try:
                        await cursor.execute("DELETE FROM users WHERE userID = '"+str(result[i][0])+"'")
                        count += 1
                    except:
                        failCount += 1
            except:
                pass
            await asyncio.sleep(0.5)
        await ctx.send("Successfully removed **"+str(count)+"** bad entries from the database, with **"+str(failCount)+"** failed removals.")
    
    @commands.command(name = "fullreload",
                    brief = "Reloads all the cogs in the cogs directory, and also looks for any new cogs.")
    @commands.is_owner()
    async def fullreload(self, ctx):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    self.bot.unload_extension(f'cogs.{filename[:-3]}')
                except:
                    await ctx.send("Error unloading "+ f'cogs.{filename[:-3]}')
                try:
                    self.bot.load_extension(f'cogs.{filename[:-3]}')
                except:
                    await ctx.send("Error reloading "+ f'cogs.{filename[:-3]}')
        await ctx.send("Reload complete.")
    

def setup(bot):
    bot.add_cog(Owner(bot))