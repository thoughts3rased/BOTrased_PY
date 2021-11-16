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

class ServerSettings(commands.Cog, name = "Server Settings"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = "svtogglemessage",
                    description = "Toggles the level up message for all members in the server, regardless as to what they have set themselves. This does not change it for them in other servers.",
                    brief = "Toggles the level up message for all members in the server.")
    @commands.has_guild_permissions(manage_guild = True)
    @commands.guild_only()
    async def servertogglemessage(self, ctx):
        if self.bot.SQLConnection == False:
            raise self.bot.BOTrasedError("201")
        server = await self.bot.fetchServerEntry(ctx.message.guild.id)
        if server[2] == 1:
            server[2] = 0
            await ctx.send("Level up messages toggled **OFF** for all server members.")
        else:
            server[2] = 1
            await ctx.send("Level up messages toggled **ON** for members with it turned on.")
        await self.bot.updateServerEntry(server)

    @servertogglemessage.error
    async def serverToggleMessageError(self, ctx, exc):
        if isinstance(exc, commands.MissingPermissions):
            raise self.bot.BOTrasedError("401")
    
    @commands.command(name = "prefix",
                    description = "Changes the server's prefix that BOTrased will to respond to. The maximum amount of characters is 2.",
                    brief = "Changes the server's prefix.")
    @commands.has_guild_permissions(manage_guild = True)
    @commands.guild_only()
    async def changeprefix(self, ctx, prefix = None):
        if prefix == None:
            raise self.bot.BOTrasedError("400 You haven't specified a prefix.")
        if len(prefix) > 2:
            raise self.bot.BOTrasedError("400 That prefix is too long. Make sure it's 2 characters or less, and try again.")
        server = await self.bot.fetchServerEntry(ctx.message.guild.id)
        server[1] = str(prefix)
        try:
            await self.bot.updateServerEntry(server)
            await ctx.send("The server's prefix is now: "+str(prefix))
        except:
            raise self.bot.BOTrasedError("202 BOTrased had a problem updating your prefix. Please let the developer know. (hint: use !info to find contact information)")
    
    @changeprefix.error
    async def changePrefixError(self, ctx, exc):
        if isinstance(exc, commands.MissingPermissions):
            raise self.bot.BOTrasedError("401 You are not authorised to use this command.")
    
    @commands.command(name = "svsettings",
                    description = "Displays all of the settings that are currently applied to this server.",
                    brief = "Displays server settings.")
    @commands.guild_only()
    async def svsettings(self, ctx):
        server = await self.bot.fetchServerEntry(ctx.message.guild.id)
        embed = discord.Embed(title = "Settings for "+ ctx.message.guild.name)
        embed.set_thumbnail(url = ctx.message.guild.icon_url)
        embed.add_field(name = "Prefix:", value = str(server[1]))
        if server[2] == 1:
            embed.add_field(name = "Level up messages:", value = "Enabled for those with it turned on.")
        else:
            embed.add_field(name = "Level up messages:", value = "Disabled server-wide.")
        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(ServerSettings(bot))