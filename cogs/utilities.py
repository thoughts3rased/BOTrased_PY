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

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = "alive",
                    description = "A simple check for bot responsiveness. If you get no response, there may be an issue with permissions or the bot itself.",
                    brief = "A simple check for bot responsiveness.",
                    aliases = ["hb", "heartbeat"])
    async def alive(self, ctx): 
        await ctx.send(ctx.message.author.mention + " I'm alive")
    
    @commands.command(name = "id",
                    description = "Returns the User ID of a specified user when @mentioned. If no user is @mentioned, it returns your ID.",
                    brief = "Returns the User ID of a specified user.")
    async def id(self, ctx, user: discord.User  = None):
        #Has the user presented an argument, or have they passed an @mention of themselves as an argument?
        if user == None or user.id == ctx.message.author.id:
            #Send the user a message presenting their ID that addresses them directly.
            await ctx.send(ctx.message.author.mention + ", your User ID is: "+ str(ctx.message.author.id))
        #In this case, the user must have passed something other than a reference to themselves
        else:
            #Try to get the ID of that argument, and send it to the channel
            try:
                await ctx.send(user.display_name+"'s ID is: "+ str(user.id))
            #If there's an issue doing this, send an error message in the chat.
            except:
                raise self.bot.BOTrasedError("402 Sorry, there was an issue getting that user's ID. Check that the account of the user you are obtaining the ID of hasn't deleted their account. Please note that only @mentions will be taken as valid arguments, and that @role mentions will not work.")
    
    @commands.command(name = "info",
                    description = "Displays information about BOTrased including the name, a description, server count and the creator of the bot.",
                    brief = "Displays information about BOTrased.",
                    aliases = ["i"])
    async def info(self, ctx):
        #Fetch my user profile using my ID
        ownerProfile = await self.bot.fetch_user(int(self.bot.ownerID))
        #Initialise the embed object and assign it to a local variable called "embed". Set the title and description and set the colour for the sidebar.
        embed = discord.Embed(title = "BOTrased", description = "A Discord Bot written entirely in Python.", colour = discord.Colour.dark_purple())
        #Set the content of the embed to an image type and pass the URL of my user profile
        embed.set_image(url = str(ownerProfile.avatar_url))
        #Set the content of the thumbnail (the image displayed in the top right corner of the embed) and pass the URL of the bot's user profile
        embed.set_thumbnail(url = str(self.bot.user.avatar_url))
        #Add a field which will display the server count of the bot
        embed.add_field(name = "Currently serving:", value = str(len(self.bot.guilds)) + " servers", inline = False)
        #Add a field which will provide an invite link to add the bot to other servers
        embed.add_field(name="Invite Bot", value="[Invite link](https://discord.com/oauth2/authorize?client_id=541373621873016866&scope=bot&permissions=439610486)")
        embed.add_field(name = "Support Server", value  = "[Server Invite](https://discord.gg/KUSWws6XAA)")
        embed.add_field(name = "Vote", value = "[Vote for BOTrased](https://top.gg/bot/541373621873016866/vote)")
        embed.add_field(name = "Creator", value = ownerProfile.display_name+"#"+ownerProfile.discriminator, inline = False)
        #Send the embed object as an embed type message into the channel
        await ctx.send(embed = embed)
    
    @commands.command(name = "weather",
                    description = "Gets the weather for a specified location and displays it as an embed.",
                    brief = "Check the weather for a specified location.")
    async def weather(self, ctx, *, location = None):
        if location == None:
            raise self.bot.BOTrasedError("403")
        try:
            weather = self.bot.mgr.weather_at_place(location)
        except:
            raise self.bot.BOTrasedError("500")
        data = weather.weather
        distance = int(data.visibility_distance)/1000
        embed = discord.Embed(title = "Weather for " + location.title())
        embed.set_thumbnail(url = data.weather_icon_url(size = '4x'))
        embed.add_field(name = (data.detailed_status.title()), value = "\u200b", inline = False)
        embed.add_field(name = "Temperature:", value = str(data.temperature(unit = 'celsius')['temp']) + "°C", inline = False)
        embed.add_field(name = "Humidity:", value = str(data.humidity)+"%", inline=False)
        embed.add_field(name = "Wind Speed:", value = str(data.wind()['speed'])+"m/s", inline = False)
        embed.add_field(name = "Cloud Cover:", value = str(data.clouds)+"%", inline = False)
        embed.add_field(name = "Pressure:", value = str(data.pressure['press'])+"hPa", inline = False)
        embed.add_field(name = "Visibility Distance:", value = str(distance)+"KM", inline = False)
        await ctx.send(embed = embed)
        
    @commands.command(name = "flip",
                    description = "Flips a coin and returns heads or tails.",
                    brief = "Flips a coin and returns heads or tails.",
                    aliases = ["coin"])
    async def flip(self, ctx):
        if random.randint(1,2) == 1:
            await ctx.send("<:heads:809568187707817994>")
            await asyncio.sleep(0.3)
            await ctx.send(ctx.message.author.mention+", you got **heads**.")
        else:
            await ctx.send("<:tails:809568669029236766>")
            await asyncio.sleep(0.3)
            await ctx.send(ctx.message.author.mention+", you got **tails**.")
    
    @commands.command(name = "changelog",
                    description = "View all the changes made to BOTrased since the last update.",
                    brief = "View the changelog.")
    async def changelog(self, ctx):
        async with ctx.typing():
            changeLog = open("changelog.txt", "r")
            changeLogBody = ""
            changeLogLines = []
            for line in changeLog:
                changeLogLines.append(line)
            for i in range(1, len(changeLogLines)):
                changeLogBody += changeLogLines[i]
            embed = discord.Embed(title = changeLogLines[0], description = changeLogBody, colour = discord.Colour.dark_purple())
            embed.set_footer(text = "Note: \"Silent changes\" are changes that should not impact user experience, and instead only code stability or maintainability.")
            changeLog.close()
            await ctx.send(embed = embed)
    
    @commands.command(name = "randomint",
                    description = "Generates a random integer within a given range",
                    brief = "Generates a random integer within a given range")
    async def randomInt(self, ctx, val1 = None, val2 = None):
        if val1 == None:
            raise self.bot.BOTrasedError("403")
        try:
            int(val1)
            if val2 != None:
                int(val2)
                assert int(val1) < int(val2)
        except:
            raise self.bot.BOTrasedError("400")
        if val2 == None:
            await ctx.send("Your number is " + str(random.randint(0, int(val1))))
        else:
            await ctx.send("Your number is " + str(random.randint(int(val1), int(val2))))

def setup(bot):
    bot.add_cog(Utilities(bot))