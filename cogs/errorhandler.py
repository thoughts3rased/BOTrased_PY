import asyncio
import itertools
import functools
import math
import re
from attr import __description__
import discord
import os
from discord import user
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
from osuapi import OsuApi, AHConnector

errorNameDict = {
    "100":"Leaderboard Not Initialised",


    "200":"No Profile",
    "201":"Database Unavailable",
    "202":"Bad Request",


    "300":"Bot Missing Permissions",


    "400":"Bad Argument",
    "401":"User Missing Permissions",
    "402":"Invalid Target",
    "403":"Missing Argument",
    "404":"Target Not Found",
    "405":"Item Not Owned",
    "406":"Insufficient Credits",
    "407":"Daily Already Claimed",
    "408":"Item Not Found",
    "409":"Already Own Item",
    "418":"I'm a teapot",

    "500":"Weather Data Not Found",
    "501":"Osu Profile Not Found",
    "502":"Recent Play Unobtainable"
}

errorMessageDict = {
    "100":"BOTrased cannot show the leaderboard due to the fact that it has not initialised it yet.",


    "200":"BOTrased cannot perform this request due to the fact that you do not have a user profile. You should have one by now, so you should get in touch with the developer.",
    "201":"BOTrased cannot perform this request due to the fact that the database is currently unreachable.",
    "202":"BOTrased was not able to query the database correctly due to the request being invalid.",


    "300":"BOTrased cannot perform this request due to the fact that it is missing the appropriate permissions.",


    "400":"One or more arguments you provided for this command are invalid.",
    "401":"BOTrased will not perform this request due to the fact that the user that initiated the command is lacking the appropriate permissions.",
    "402":"The target selected is not valid.",
    "403":"BOTrased cannot carry out this request due to the fact that a required argument is missing.",
    "404":"The target user does not have a profile in the database",
    "405":"The target user does not own this item.",
    "406":"You do not have enough credits to perform this action.",
    "407":"You have already claimed your daily too recently",
    "408":"That item is invalid.",
    "409":"You already own that item.",
    "418":"Sorry, I refuse to execute your request to brew coffee because I am in fact permanently a teapot.",

    "500":"Weather data for that location could not be found.",
    "501":"The specified Osu profile could not be found.",
    "502":"BOTrased couldn't get the most recent play for that user."
}

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance (error, commands.BadArgument):
            await ctx.send("**ERROR 400 - " + errorNameDict["400"] +"\n" + errorMessageDict["400"])
        if isinstance(error, self.bot.BOTrasedError):
            customErrorMessage = False
            if len(error.args[0]) > 3:
                customErrorMessage = True
            if customErrorMessage == False:
                await ctx.send("**ERROR "+ str(error.args[0]) +" - "+ errorNameDict[error.args[0]] +"**\n"+errorMessageDict[error.args[0]])
            else:
                await ctx.send("**ERROR "+ str(error.args[0][0:3]) +" - "+ errorNameDict[error.args[0][0:3]] +"**\n" + error.args[0][4:len(error.args[0])])


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))