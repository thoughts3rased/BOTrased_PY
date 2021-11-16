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

class UserSettings(commands.Cog, name = "User Settings"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name = "setmessage",
                        description = "Change the message that appears on your user profile. This has a limit of 144 characters, and quotes must be escaped with a backslash before them.",
                        brief = "Change the message that appears on your user profile.")
    async def setMessage(self, ctx, *, message):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        illegalCharacters = ['"']
        if await self.bot.checkUserExists(ctx.message.author.id) == False:
            raise self.bot.BOTrasedError("200")
        user = await self.bot.fetchUserProfile(ctx.message.author.id)
        if len(str(message)) > 144:
                    raise self.bot.BOTrasedError("400 Sorry, that user message is too long. Please shorten it and try again.")
        for character in illegalCharacters:
            if character in str(message):
                raise self.bot.BOTrasedError("400 Sorry, but the message you have entered contains illegal characters. Please remove them and try again.")
        else:
            user[4] = str(message)
            try:
                await self.bot.updateUserProfile(user)
                await ctx.send("User message changed successfully.")
            except:
                raise self.bot.BOTrasedError("202")
    
    @commands.command(name = "togglelevelmessage",
                    description = "Toggles the message that will display in chat when you level up. Disabling it is global and affects every server.",
                    brief = "Toggles the level up message.")
    async def toggleLevelMessage(self, ctx):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        if await self.bot.checkUserExists(ctx.message.author.id) == False:
            raise self.bot.BOTrasedError("200")
        user = await self.bot.fetchUserProfile(ctx.message.author.id)
        if user[5] == 1:
            user[5] = 0
        else:
            user[5] = 1
        try:
            await self.bot.updateUserProfile(user)
            if user[5] == 1:
                await ctx.send("Level up message toggled **ON**.")
            else:
                await ctx.send("Level up message toggled **OFF**.")      
        except:
            raise self.bot.BOTrasedError("202")
    
    @commands.command(name = "settings",
                    description = "Shows all of your settings that apply to you globally. Does not take into account server settings.",
                    brief = "Shows your settings configuration.")
    async def settings(self, ctx):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        user = await self.bot.fetchUserProfile(ctx.message.author.id)
        embed = discord.Embed(title = "User settings for "+ctx.message.author.name)
        embed.set_thumbnail(url = ctx.message.author.avatar_url)
        if user[5] == 1:
            embed.add_field(name = "Level Up Messages:", value = "Enabled")
        else:
            embed.add_field(name = "Level Up Messages:", value = "Disabled")
        
        await ctx.send(embed = embed)
    
    @commands.command(name = "profilecolour",
                    description = "Changes your !profile embed colour to a hex code of your choosing. Requires the Profile Colour Change item.",
                    brief = "Changes your !profile embed colour.",
                    aliases = ["profilecolor"])
    async def changeProfileColour(self, ctx, colour):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        if await self.bot.checkUserExists(ctx.message.author.id) == False:
            raise self.bot.BOTrasedError("200")
        if await self.bot.checkUserHasItem(ctx.message.author.id, 3) == False:
            raise self.bot.BOTrasedError("405 You require the Profile Colour Change to use this setting. (Use !buy 4)")
        user = await self.bot.fetchUserProfile(ctx.message.author.id)
        try:
            rgbColour = tuple(int(colour[i:i+2], 16) for i in (0, 2, 4))
            newColour = discord.Colour.from_rgb(rgbColour)
        except:
            raise self.bot.BOTrasedError("400 That colour is invalid. Ensure it's formatted with hex and that you don't include the # or any spaces.")
        await ctx.send("Profile colour successfully updated.")



def setup(bot):
    bot.add_cog(UserSettings(bot))