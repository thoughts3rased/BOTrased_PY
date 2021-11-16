import asyncio
import aiohttp
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
from datetime import datetime
import dbl

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.changeStatusMessage.start(bot)
        if os.getenv("TEST_MODE") == "False":
            self.updateBotListCounts.start()
        self.updateExpLeaderboard.start(bot)
        self.updateCreditsLeaderboard.start(bot)

    def cog_unload(self):
        self.changeStatusMessage.cancel()
        self.updateExpLeaderboard.cancel()
        self.updateCreditsLeaderboard.cancel()
        self.updateBotListCounts.cancel()

    @tasks.loop(minutes = 30.0)
    async def changeStatusMessage(self, bot):   
        messages = ["Stuck? Use !help",
            "Currently serving "+str(len(bot.guilds))+" servers!",
            "bleep-bloop-blop",
            "I have a little brother called TESTrased!",
            "Change my prefix with !prefix",
            "I like... Rain.",
            "I used to roll the dice...",
            "Check the changelog with !changelog",
            "Have you remembered to use !daily today?",
            "Got any servers you'd like to add me to?"]
        if self.bot.SQLConnection != None:
            await self.bot.change_presence(status = discord.Status.online, activity = discord.Game(name = random.choice(messages)))
        else:
            while self.bot.SQLConnection == None:
                await self.bot.change_presence(status = discord.Status.idle, activity = discord.Game(name = "Limited functionality - Database is unreachable."))
                await asyncio.sleep(30.0)
            await self.bot.change_presence(status = discord.Status.online, activity = discord.Game(name = random.choice(messages)))
    
    @tasks.loop(minutes = 5.0)
    async def updateExpLeaderboard(self, bot):
        print("Initialising connection...")
        connection = await self.bot.SQLConnection.acquire()
        cursor = await connection.cursor()
        query = ("SELECT * from users ORDER BY exp DESC LIMIT 100;")
        await cursor.execute(query)
        result = await cursor.fetchall()
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S")
        leaderboard = []
        print("Formatting database result...")
        for i in range (0, len(result)):
            currentProfile = []
            currentProfile.append(result[i][0])
            currentProfile.append(result[i][1])
            leaderboard.append(currentProfile)
        
        leaderboard = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
        pages = []
        pagecount = len(leaderboard)
        boardPos = 1
        print("Creating pages...")
        for i in range(0, len(leaderboard)):
            leaderboardString = ""
            for j in range(0, len(leaderboard[i])):
                try:
                    user = self.bot.get_user(leaderboard[i][j][0])
                    if user == None:
                        user = await self.bot.fetch_user(leaderboard[i][j][0])
                    leaderboardString = leaderboardString + ("\n" + str(boardPos)+". "+ user.name + "#" + user.discriminator + " - " + str(leaderboard[i][j][1]))
                except:
                    leaderboardString = leaderboardString + ("\n" + str(boardPos)+". Invalid/Deleted User - " + str(leaderboard[i][j][1]))
                boardPos += 1
            embed = discord.Embed(title = "Top 100 users by amount of experience", description = leaderboardString)
            embed.set_footer(text = "Page " + str(i+1)+"/"+str(pagecount) +" - Updated at " + timestamp + "(GMT + 0:00)")
            pages.append(embed)
        await self.bot.SQLConnection.release(connection)
        self.bot.expLeaderboardPages = pages
        print("Experience leaderboard successfully updated.")

    @updateExpLeaderboard.before_loop
    async def beforeExpLeaderboard(self):
        await self.bot.wait_until_ready()
        while self.bot.SQLConnection == None:
            await asyncio.sleep(1.0)
        print("Experience Leaderboard ready to be updated.")
    
    @tasks.loop(minutes = 5.0)
    async def updateCreditsLeaderboard(self, bot):
        print("Initialising Connection...")
        connection = await self.bot.SQLConnection.acquire()
        cursor = await connection.cursor()
        query = ("SELECT * from users ORDER BY money DESC LIMIT 100;")
        await cursor.execute(query)
        result = await cursor.fetchall()
        leaderboard = []
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S")
        print("Formatting database result...")
        for i in range (0, len(result)):
            currentProfile = []
            currentProfile.append(result[i][0])
            currentProfile.append(result[i][3])
            leaderboard.append(currentProfile)
        
        leaderboard = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
        pages = []
        pagecount = len(leaderboard)
        boardPos = 1
        print("Creating pages...")
        for i in range(0, len(leaderboard)):
            leaderboardString = ""
            for j in range(0, len(leaderboard[i])):
                try:
                    user = self.bot.get_user(leaderboard[i][j][0])
                    if user == None:
                        user = await self.bot.fetch_user(leaderboard[i][j][0])
                    leaderboardString = leaderboardString + ("\n" + str(boardPos)+". "+ user.name + "#" + user.discriminator + " - " + str(leaderboard[i][j][1]))
                except:
                    leaderboardString = leaderboardString + ("\n" + str(boardPos)+". Invalid/Deleted User - " + str(leaderboard[i][j][1]))
                boardPos += 1
            embed = discord.Embed(title = "Top 100 users by amount of credits", description = leaderboardString)
            embed.set_footer(text = "Page " + str(i+1)+"/"+str(pagecount) + " - Updated at " + timestamp + "(GMT + 0:00)")
            pages.append(embed)
        await self.bot.SQLConnection.release(connection)
        self.bot.creditLeaderboardPages = pages
        print("Credits leaderboard successfully updated.")
    
    @updateCreditsLeaderboard.before_loop
    async def beforeCreditLeaderboard(self):
        await self.bot.wait_until_ready()
        while self.bot.SQLConnection == None:
            await asyncio.sleep(1.0)
        print("Credit Leaderboard ready to be updated.")
    
    @tasks.loop(minutes = 30.0)
    async def updateBotListCounts(self):
        if os.getenv("TEST_MODE") == "True":
            return
        async with aiohttp.ClientSession() as session:
            async with session.post("https://top.gg/api/bots/541373621873016866/stats", data = {
                "server_count":len(self.bot.guilds)
            }, headers = {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjU0MTM3MzYyMTg3MzAxNjg2NiIsImJvdCI6dHJ1ZSwiaWF0IjoxNjEzMzExMDI2fQ.9gwACxjL-fgh_4rQ0yyfmLbpC5T7G88ITd8OoaoZO8k"}) as response:
                if response.status == 200:
                    print("top.gg server count updated successfully.")
                else:
                    print(await response.text())
            
            #async with session.post("https://discordbotlist.com/api/v1/bots/541373621873016866/stats", 
            #                            data = {"guilds":len(self.bot.guilds)},
             #                           headers = {"Authorization":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoxLCJpZCI6IjU0MTM3MzYyMTg3MzAxNjg2NiIsImlhdCI6MTYxNTU5NzQyMX0.id3kE7wAGYxc3iY6q4CTcU2tlJ3obH_t5n4DhPcDCJY"}) as response:
              #  if response.status == 200:
               #     print("discordbotlist.com server count updated successfully.")
                #else:
                 #   print(await response.text())

def setup(bot):
    bot.add_cog(Loops(bot))