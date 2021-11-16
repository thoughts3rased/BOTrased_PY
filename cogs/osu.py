import asyncio
import itertools
import functools
import math
import re
from attr import __description__
import discord
import os
from discord import colour
from discord import enums
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
from osuapi import OsuMode, OsuMod
import aiohttp
import json

def convertToTimecount(time):
    day = time // (24 * 3600)
    time = time % (24 * 3600)
    hour = time // 3600
    time %= 3600
    minutes = time // 60
    return "%dd %dh %dm" % (day, hour, minutes)

rankEmotes = {"F":"<:F_:827968020374618202>",
            "D":"<:D_:827967073165639680>",
            "C":"<:C_:827967073253720114>",
            "B":"<:B_:827967073262764062>",
            "A":"<:A_:827967073035747328>",
            "S":"<:S_:827967072771375124>",
            "SH":"<:SH:827966843623964752>",
            "X":"<:X_:827966843665776711>",
            "XH":"<:XH:827966843532607498>"}

def getUserPicture(osuUser):
    return "http://a.ppy.sh/"+str(osuUser[0].user_id)

def createProfileEmbed(osuUser, title):
    embed = discord.Embed(title = title, colour = discord.Colour.from_rgb(255, 102, 170))
    embed.set_thumbnail(url = getUserPicture(osuUser))
    embed.add_field(name = "Global Rank", value = "#"+str(osuUser[0].pp_rank))
    embed.add_field(name = "Country Rank (" + osuUser[0].country+")", value = "#" + str(osuUser[0].pp_country_rank))
    embed.add_field(name = "PP Count", value = str(osuUser[0].pp_raw)+"pp")
    embed.add_field(name = "Level", value = str(osuUser[0].level))
    embed.add_field(name = "Map Play Count", value = str(osuUser[0].playcount))
    embed.add_field(name = "Playtime", value = convertToTimecount(osuUser[0].total_seconds_played))
    embed.add_field(name = "Total Score", value = f"{osuUser[0].total_score:,}")
    embed.add_field(name = "Accuracy", value = str(osuUser[0].accuracy)[0:5] + "%")
    return embed

async def createRecentEmbed(osuBeatmap, osuUser, osuPlay, mode):
    modeDict = {"std":"300 - " + str(osuPlay[0].count300) + "\n 100 - " + str(osuPlay[0].count100) + "\n 50 - " + str(osuPlay[0].count50) + "\n miss - " + str(osuPlay[0].countmiss),
                "taiko":"great - " + str(osuPlay[0].count300) + "\n good - " + str(osuPlay[0].count100) + "\n miss - " + str(osuPlay[0].countmiss),
                "mania":"300 - " + str(osuPlay[0].count300) + "\n 200 - " + str(osuPlay[0].count100) + "\n 50 - " + str(osuPlay[0].count50) + "\n miss - " + str(osuPlay[0].countmiss),
                "ctb":"fruit - " + str(osuPlay[0].count300) + "\n drops - " + str(osuPlay[0].count100) + "\n droplets - " + str(osuPlay[0].count50) + "\n miss - " + str(osuPlay[0].countmiss)}
    fcDict = {True:"Yes", False:"No"}
    embed = discord.Embed(title = osuUser[0].username + "'s recent play on " + osuBeatmap[0].title + " (" + osuBeatmap[0].version + ") [★" + str(round(osuBeatmap[0].difficultyrating, 2)) +"] " + osuPlay[0].enabled_mods.shortname, description = modeDict[mode], colour = discord.Colour.from_rgb(255, 102, 170))
    embed.set_thumbnail(url = getUserPicture(osuUser))
    embed.add_field(name = "Rank", value = rankEmotes[osuPlay[0].rank])
    embed.add_field(name = "Score", value = f"{osuPlay[0].score:,}")
    embed.add_field(name = "Max Combo", value = str(osuPlay[0].maxcombo) + "/" + str(osuBeatmap[0].max_combo))
    embed.add_field(name = "Full Combo", value = fcDict[osuPlay[0].perfect])
    embed.add_field(name = "Accuracy", value = str(round(osuPlay[0].accuracy(osuBeatmap[0].mode) * 100, 2))+"%")
    return embed

class Osu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = "osu",
                    description = "Gets the Osu!STD profile of a specified player, and returns it as an embed.",
                    brief = "Returns the Osu!STD profile of a specified player.")
    async def osuProfile(self, ctx, *, username = None):
        try:
            osuUser = await self.bot.OsuConnection.get_user(str(username))
        except:
            raise self.bot.BOTrasedError("501")
        title = osuUser[0].username + "'s osu! Standard Profile"
        embed = createProfileEmbed(osuUser, title)
        await ctx.send(embed = embed)
    
    @commands.command(name = "ctb",
                    description = "Gets the Osu!Catch profile of a specified player, and returns it as an embed.",
                    brief = "Returns the Osu!Catch profile of a specified player.")
    async def catchProfile(self, ctx, *, username = None):
        try:
            osuUser = await self.bot.OsuConnection.get_user(str(username), mode = OsuMode.ctb)
        except:
            raise self.bot.BOTrasedError("501")
        title = osuUser[0].username + "'s osu!Catch Profile"
        embed = createProfileEmbed(osuUser, title)
        await ctx.send(embed = embed)

    @commands.command(name = "mania",
                        description = "Gets the Osu!Mania profile of a specified player, and returns it as an embed.",
                        brief = "Returns the Osu!Mania profile of a specified player.")
    async def maniaProfile(self, ctx, *, username = None):
        try:
            osuUser = await self.bot.OsuConnection.get_user(str(username), mode = OsuMode.mania)
        except:
            raise self.bot.BOTrasedError("501")
        title = osuUser[0].username + "'s osu!Mania Profile"
        embed = createProfileEmbed(osuUser, title)
        await ctx.send(embed = embed)
    
    @commands.command(name = "taiko",
                        description = "Gets the Osu!Taiko profile of a specified player, and returns it as an embed.",
                        brief = "Returns the Osu!Taiko profile of a specified player.")
    async def taikoProfile(self, ctx, *, username = None):
        try:
            osuUser = await self.bot.OsuConnection.get_user(str(username), mode = OsuMode.taiko)
        except:
            raise self.bot.BOTrasedError("501")
        title = osuUser[0].username + "'s osu!Taiko Profile"
        embed = createProfileEmbed(osuUser, title)
        await ctx.send(embed = embed)
    
    @commands.command(name = "osurecent",
                    description = "Gets the most recent osu!STD play for a specified player, and returns it as an embed.",
                    brief = "Gets the most recent osu!STD play for a player.")
    async def osuRecent(self, ctx, *, username = None):
        try:
            osuUser = await self.bot.OsuConnection.get_user(str(username))
            osuPlay = await self.bot.OsuConnection.get_user_recent(str(username))
            beatmap = await self.bot.OsuConnection.get_beatmaps(beatmap_id = osuPlay[0].beatmap_id)
        except:
            raise self.bot.BOTrasedError("502")
        embed = await createRecentEmbed(beatmap, osuUser, osuPlay, "std")

        await ctx.send(embed = embed)
    
    @commands.command(name = "ctbrecent",
                    description = "Gets the most recent osu!Catch play for a specified player, and returns it as an embed.",
                    brief = "Gets the most recent osu!Catch play for a player.")
    async def ctbRecent(self, ctx, *, username = None):
        try:
            osuUser = await self.bot.OsuConnection.get_user(str(username))
            osuPlay = await self.bot.OsuConnection.get_user_recent(str(username), mode = OsuMode.ctb)
            beatmap = await self.bot.OsuConnection.get_beatmaps(beatmap_id = osuPlay[0].beatmap_id)
        except:
            raise self.bot.BOTrasedError("502")
        embed = await createRecentEmbed(beatmap, osuUser, osuPlay, "ctb")
        await ctx.send(embed = embed)
    
    @commands.command(name = "maniarecent",
                    description = "Gets the most recent osu!STD play for a specified player, and returns it as an embed.",
                    brief = "Gets the most recent osu!STD for a player.")
    async def maniaRecent(self, ctx, *, username = None):
        try:
            osuUser = await self.bot.OsuConnection.get_user(str(username))
            osuPlay = await self.bot.OsuConnection.get_user_recent(str(username))
            beatmap = await self.bot.OsuConnection.get_beatmaps(beatmap_id = osuPlay[0].beatmap_id)
        except:
            raise self.bot.BOTrasedError("502")
        embed = await createRecentEmbed(beatmap, osuUser, osuPlay, "std")

        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(Osu(bot))