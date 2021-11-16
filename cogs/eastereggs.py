import asyncio
import itertools
import functools
import math
import re
import typing
from attr import __description__, field
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

class EasterEggs(commands.Cog, command_attrs = dict(hidden = True)):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name = "brew")
    async def brew(self, ctx, *, argument):
        if argument.lower() == "tea":
            await ctx.send("I'm a little teapot short and stout, tip me over and pour me out.")
        
        if argument.lower() == "coffee":
            raise self.bot.BOTrasedError("418")


def setup(bot):
    bot.add_cog(EasterEggs(bot))