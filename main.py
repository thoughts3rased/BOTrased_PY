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

ownerID = "273140563971145729"
SQLConnection = None
homeDir = os.path.dirname(os.path.realpath(__file__))
disabled = []
#Determine whether the bot should boot in test mode or not
if os.getenv("TEST_MODE") == "False":
    print("TEST_MODE ENV variable set to FALSE. Running in NORMAL MODE. If this isn't meant to happen, this is a bug!")
else:
    print("TEST_MODE ENV variable set to TRUE. Running in TEST MODE. If this isn't meant to happen, this is a bug!")
if os.getenv("APIKEY") == None or os.getenv("TOKEN") == None:
    raise Exception("One or more required Environment Variables not found.")

class BOTrased(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SQLConnection = None
        self.OpenWMap = pyowm.OWM(str(os.getenv("APIKEY")))
        self.mgr = self.OpenWMap.weather_manager()
        self.ownerID = 273140563971145729
        self.expLeaderboardPages = None
        self.creditLeaderboardPages = None
        self.OsuConnection = OsuApi("", connector = AHConnector())

    class BOTrasedError(commands.CommandError):
        pass

    async def create_SQL_connection(self):
        global disabled
        connection = None
        #Attempt to connect to the database
        if os.getenv("TEST_MODE") == "False":
            connection = await aiomysql.create_pool(
                        host= '',
                        port = 1273,
                        user=os.getenv("DATABASE_USERNAME"),
                        password=os.getenv("DATABASE_PASSWORD"),
                        db = os.getenv("DATABASE_SCHEMA"),
                        autocommit = True)
        else:
            connection = await aiomysql.create_pool(
                        host = '',
                        port = 1273,
                        user = '',
                        password = '',
                        db = 'botrased_test',
                        autocommit = True
            ) 
        if connection != None:
            disabled = []
        else:
            if "database" not in disabled:
                disabled.append("database")
        self.SQLConnection = connection

    async def createUserProfile(self, ID):
        query = "INSERT into users VALUES ('"+str(ID)+"', 0, 0, 1000, NULL, 1, NULL)"
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute(query)
        await self.SQLConnection.release(connection)

    async def checkUserExists(self, ID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute(("SELECT * from users WHERE userID = '" +str(ID))+"'")
        result = await cursor.fetchall()
        await self.SQLConnection.release(connection)
        if not result: #In other words, is the returned array empty?
            #Yes, it is empty, meaning no users with that ID exist in the database
            return False
        else:
            #No, it isn't empty, meaning that at least one user with that ID exists
            return True

    async def fetchUserProfile(self, ID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute(("SELECT * from users WHERE userID = '" +str(ID))+"';")
        result = await cursor.fetchall()
        profile = []
        for i in range (0, 8):
            profile.append(result[0][i])
        await self.SQLConnection.release(connection)
        return profile

    async def updateUserProfile(self, profile):
        if profile[3] < 0:
            profile[3] = 0
        if profile[6] == None:
            profile[6] = "NULL"
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        query = ("UPDATE users SET exp = "+str(profile[1])+", level = "+str(profile[2])+", money = "+str(profile[3])+", message = \""+str(profile[4])+"\", levelUpMessage = "+str(profile[5]) + ", lastdaily = "+str(profile[6]) + ", embedColour = '" + str(profile[7]) + "' WHERE userID = \""+profile[0]+"\";")
        await cursor.execute(query)
        await self.SQLConnection.release(connection)

    async def grabDailyTimer(self, user):
        nextDaily = user[6] + 86400
        timeRemainingSecs = nextDaily - int(time.time())
        timeRemainingString = time.strftime("%H:%M:%S", time.gmtime(timeRemainingSecs))
        return timeRemainingString

    async def checkServerExists(self, ID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute(("SELECT * from servers WHERE serverID = '" +str(ID))+"'")
        result = await cursor.fetchall()
        await self.SQLConnection.release(connection)
        if not result: #In other words, is the returned array empty?
            #Yes, it is empty, meaning no servers with that ID exist in the database
            return False
        else:
            #No, it isn't empty, meaning that at least one server with that ID exists
            return True

    async def updateServerEntry(self, server):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        query = ("UPDATE servers SET prefix = '"+str(server[1])+"', levelupmessage = "+str(server[2])+" WHERE serverID = \""+server[0]+"\";")
        await cursor.execute(query)
        await bot.SQLConnection.release(connection)

    async def createServerEntry(self, serverID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        query = "INSERT into servers VALUES ('"+str(serverID)+"', '!', 1)"
        await cursor.execute(query)
        await bot.SQLConnection.release(connection)

    async def createAdminLogEntry(self, log):
        try:
            print(log)
            connection = await self.SQLConnection.acquire()
            cursor = await connection.cursor()
            query = "INSERT into adminLogs VALUES (NULL, '"+str(log["server"])+"', '"+str(log["target"])+"', '"+ str(log["admin"])+"', '"+ str(log["type"]) + "', '" + str(log["reason"]) +"', "+str(log["time"]) + ", " + str(log["bot"])+")"
            await cursor.execute(query)
            query = "SELECT logID FROM adminLogs where serverID = '"+str(log["server"])+"' ORDER BY logID DESC LIMIT 1"
            await cursor.execute(query)
            logID = await cursor.fetchall()
            await bot.SQLConnection.release(connection)
            return logID[0][0]
        except:
            raise

    async def fetchServerEntry(self, ID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute("SELECT * from servers WHERE serverID = '" +str(ID)+"';")
        result = await cursor.fetchall()
        profile = []
        for i in range (0, 3):
            profile.append(result[0][i])
        await self.SQLConnection.release(connection)
        return profile
    
    async def queryDatabase(self, query):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute(query)
        result = await cursor.fetchall()
        resultArray = []
        for i in range (0, len(result)):
            record = []
            for j in range(0, len(result[i])):
                record.append(result[i][j])
            resultArray.append(record)
        return resultArray
    
    async def fetchItemDatabase(self):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute("SELECT * from items")
        dataArray = []
        result = await cursor.fetchall()
        for i in range (0, len(result)):
            tempDict = {}
            tempDict = {"itemID":result[i][0],
                        "type":result[i][1],
                        "name":result[i][2],
                        "emojiString":result[i][3],
                        "price":result[i][4],
                        "description":result[i][5],
                        "purchasable":result[i][6]}
            dataArray.append(tempDict)
        await self.SQLConnection.release(connection)
        return dataArray
    
    async def userInventoryLookup(self, userID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute("SELECT inventory.userID, inventory.itemID, inventory.showOnProfile, items.name, items.type, items.emojiString, items.price, items.description, items.purchasable FROM inventory INNER JOIN items ON inventory.itemID = items.itemID WHERE userID = \""+ str(userID) + "\";")
        result = await cursor.fetchall()
        dataArray = []
        for i in range (0, len(result)):
            tempDict = {}
            tempDict = {"userID":result[i][0],
                        "itemID":result[i][1],
                        "showOnProfile":result[i][2],
                        "name":result[i][3],
                        "type":result[i][4],
                        "emojiString":result[i][5],
                        "price":result[i][6],
                        "description":result[i][7],
                        "purchasable":result[i][8]}
            dataArray.append(tempDict)
        await self.SQLConnection.release(connection)
        return dataArray

    async def checkUserHasItem(self, userID, itemID):
        userInventory = await self.userInventoryLookup(userID)
        if len(userInventory) == 0:
            return False
        for i in range(0, len(userInventory)):
            if int(userInventory[i]["itemID"]) == int(itemID):
                return True
        return False
    
    async def fetchSingleItem(self, itemID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute("SELECT * from items WHERE itemID = " + str(itemID) + ";")
        result = await cursor.fetchall()
        resultDict = {
            "itemID":result[0][0],
            "type":result[0][1],
            "name":result[0][2],
            "emojiString":result[0][3],
            "price":result[0][4],
            "description":result[0][5],
            "purchasable":result[0][6]
        }
        await self.SQLConnection.release(connection)
        return resultDict

    async def fetchSingleInventoryEntry(self, userID, itemID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute("SELECT * FROM inventory WHERE userID = \"" + str(userID) + "\" AND itemID = " + str(itemID) + ";")
        result = await cursor.fetchall()
        resultDict = {
            "userID":result[0][0],
            "itemID":result[0][1],
            "showOnProfile":result[0][2]
        }
        await self.SQLConnection.release(connection)
        return resultDict
    
    async def fetchAllVisibleBadges(self, userID):
        connection = await self.SQLConnection.acquire()
        cursor = await connection.cursor()
        await cursor.execute("SELECT * FROM inventory WHERE userID = \"" + str(userID) + "\" AND showOnProfile = 1;")
        result = await cursor.fetchall()
        resultArray = []
        
        for i in range(0, (len(result))):
            if i == 10:
                break
            resultArray.append({
                "userID":result[i][0],
                "itemID":result[i][1],
                "showOnProfile":1
            })
        await self.SQLConnection.release(connection)
        return resultArray

    async def checkItemType(self, itemID, typeArg):
        item = await self.fetchSingleItem(itemID)
        if item["type"].lower() != typeArg:
            return False
        return True

    async def updateUserInventory(self, modify: bool, userID, itemID, showOnProfile: int = 0):
        if not modify:
            connection = await self.SQLConnection.acquire()
            cursor = await connection.cursor()
            await cursor.execute("INSERT INTO inventory VALUES(" +str(userID)+", " +str(itemID)+ ", " + str(showOnProfile) + ")")
            await self.SQLConnection.release(connection)
        if modify:
            connection = await self.SQLConnection.acquire()
            cursor = await connection.cursor()
            await cursor.execute("UPDATE inventory SET showOnProfile = " + str(showOnProfile) + " WHERE userID = \"" + str(userID) + "\" AND itemID = " + str(itemID) + ";")
    
    async def sendEmbedPages(self, ctx, pages):
        message = await ctx.send(embed = pages[0])
        if len(pages) != 1:    
            await message.add_reaction('⏮')
            await message.add_reaction('⏭')
            i = 0
            emoji = ''
            while True:
                if emoji == '⏮':
                    if i == 0:
                        i = len(pages) - 1
                    else:
                        i -= 1
                    await message.edit(embed = pages[i])
                elif emoji == '⏭':
                    if i == len(pages) - 1:
                        i = 0
                    else:
                        i += 1
                    await message.edit(embed= pages[i])
                
                def reactionCheck(reaction, user):
                    return reaction.message == message and user == ctx.message.author and reaction.emoji in ['⏮', '⏭']

                try:
                    reaction, user = await self.wait_for("reaction_add", check = reactionCheck, timeout = 30.0)
                    emoji = str(reaction.emoji)
                    await message.remove_reaction(emoji = str(reaction), member = ctx.message.author)

                except:
                    await message.clear_reactions()
                    return



async def getPrefix(bot, message):
    guild = message.guild
    if guild and ("database" not in disabled):
        server = await bot.fetchServerEntry(message.guild.id)
        serverPrefix = server[1]
        return commands.when_mentioned_or(str(server[1]))(bot, message)
    else:
        return commands.when_mentioned_or("!")

if os.getenv("TEST_MODE") == "False":
    bot = BOTrased(command_prefix= getPrefix, owner_id = int(ownerID), case_insensitive = True)
else:
    bot = BOTrased(command_prefix= commands.when_mentioned_or("\\"), owner_id = int(ownerID), case_insensitive = True)
bot.SQLConnection = None

@bot.event
async def on_guild_join(guild):
    if await bot.checkServerExists(guild.id) == False:
        await bot.createServerEntry(guild.id)

@bot.event
async def on_message(message):
    if bot.SQLConnection != None:
        if message.author == bot.user:
            return
        
        if message.author.bot:
            return
        
        if "database" not in disabled:
            if await bot.checkServerExists(message.guild.id) == False:
                await bot.createServerEntry(message.guild.id)
            
            if await bot.checkUserExists(str(message.author.id)) == False:
                await bot.createUserProfile(str(message.author.id))
            
            user = await bot.fetchUserProfile(str(message.author.id))
            server = await bot.fetchServerEntry(message.guild.id)
            user[1] += random.randint(1, 6)
            if user[1] // 100 != user[2]:
                user[2] = user[1] //100
                if user[5] == 1 and server[2] == 1:
                    try:
                        await message.channel.send("Congratulations "+message.author.mention+", you just levelled up to level "+str(user[2])+"!")
                    except:
                        pass
            user[3] += random.randint(1, 3)
            await bot.updateUserProfile(user)
            await bot.process_commands(message)
        else:
            await bot.process_commands(message)
    
    else:
        await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name}')
    print(f'With ID: {bot.user.id}')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')
    await bot.create_SQL_connection()

bot.run(os.getenv("TOKEN"))
