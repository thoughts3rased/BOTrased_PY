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


class UserProfile(commands.Cog, name = "Profile Commands"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name = "user",
                        description = "Gathers information about a profile (yours by default) and displays the information in an embed.",
                        brief = "Displays your user profile.",
                        aliases = ["profile"])
    async def User(self, ctx, user: discord.User = None):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        #Has the user mentioned someone else?
        if user == None: 
            #If they haven't, change the target user to the author of the message
            user = ctx.message.author
        #Is the target user in the database?
        if await self.bot.checkUserExists(user.id) == False:
            #If not, give back a message depending on who the target is
            if user.id == ctx.message.author.id:
                raise self.bot.BOTrasedError("200")
            else:
                raise self.bot.BOTrasedError("404 This user does not have a profile.")
            #Return to processing other commands
            return
        #Fetch the target's profile
        userProfile = await self.bot.fetchUserProfile(user.id)
        #Does the target have a set message?
        if userProfile[4] == "None": #Note: SQL library returns NULL entries as None in a string
            #If they don't, set it to a default message
            userProfile[4] = "Welcome to my profile!"
        #Set up colour variable
        colour = None
        if user.id == self.bot.ownerID:
            colour = discord.Color.purple()
        #Check target's level against colour brackets
        elif userProfile[2] < 100:
            colour = discord.Colour.light_grey()
        elif userProfile[2] < 200:
            colour = discord.Colour.from_rgb(166, 121, 18)
        elif userProfile[2] < 400:
            colour = discord.Colour.from_rgb(104, 105, 104)
        else:
            colour = discord.Colour. from_rgb(221, 224, 0)
        #Embed logic    
        embed = discord.Embed(title = user.display_name, description = str(userProfile[4]), colour = colour)
        embed.set_thumbnail(url = str(user.avatar_url))
        embed.add_field(name = "Experience:", value = str(userProfile[1]), inline = False)
        embed.add_field(name = "Level:", value = "Level " + str(userProfile[2]), inline = False)
        embed.add_field(name = "Credits:", value = str(userProfile[3]) + " credits", inline = False)
        try:
            if (userProfile[6] + 86400) < int(time.time()):
                raise ValueError()
            embed.add_field(name = "Time until daily reset:", value = await self.bot.grabDailyTimer(userProfile), inline = False)
        except:
            embed.add_field(name = "Time until daily reset:", value = "Daily is available!", inline = False)
        
        badges = await self.bot.fetchAllVisibleBadges(ctx.message.author.id)
        if len(badges) != 0:
            footerText = ""
            for i in range(0, len(badges)):
                 badge = await self.bot.fetchSingleItem(badges[i]["itemID"])
                 footerText += badge["emojiString"]
            embed.add_field(name = footerText, value = "​")

        #Send the embed into the channel
        await ctx.send(embed = embed)
    
    @commands.command(name = "gift",
                        description = "Gift credits to another user by @mentioning them. Takes member then integer as arguments.",
                        brief = "Gift credits to another user.")
    async def Gift(self, ctx, target: discord.User = None, amount = None):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        if target == None:
            raise self.bot.BOTrasedError("403 You haven't specified a user. @mention a user and try again.")
        if target.id == ctx.author.id:
            raise self.bot.BOTrasedError("402 You cannot gift credits to yourself.") 
        if amount <= 0:
                raise self.bot.BOTrasedError("400 Amount cannot be a negative number.") 
        try:
            amount = int(amount)
        except:
            raise self.bot.BOTrasedError("400 Please enter a positive integer and try again.")
        if await self.bot.checkUserExists(target.id) == False:
            raise self.bot.BOTrasedError("404 The target user is not in the database.")
        elif await self.bot.checkUserExists(ctx.message.author.id) == False:
            raise self.bot.BOTrasedError("200")
        sendingUser = await self.bot.fetchUserProfile(ctx.message.author.id)
        receivingUser = await self.bot.fetchUserProfile(target.id)
        if sendingUser[3] < amount:
            raise self.bot.BOTrasedError("406 You do not have sufficient credits to gift this amount.")
        sendingUser[3] += -amount
        receivingUser[3] += amount
        await self.bot.updateUserProfile(sendingUser)
        await self.bot.updateUserProfile(receivingUser)
        await ctx.send(target.mention+", you've been gifted "+str(amount)+" credits by "+ ctx.message.author.mention+"!")
    
    @commands.command(name = "inventory",
                    description = "Displays all of the items in your inventory, by order of itemID.",
                    brief = "Displays your inventory.")
    async def inventory(self, ctx, target: discord.User = None):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        if target == None:
            target = ctx.message.author
        userInventory = await self.bot.userInventoryLookup(target.id)
        if len(userInventory) == 0:
            await ctx.send(target.name + "'s inventory is empty.")
        else:
            pages = []
            processedData = [userInventory[i:i + 10] for i in range(0, len(userInventory), 5)]
            pageCount = len(processedData)
            for i in range(0, pageCount):
                embed = discord.Embed(title = target.name + "'s Inventory")
                for j in range (0, len(processedData[i])):
                    statusEmoji = ""
                    if processedData[i][j]["type"] == "badge" and processedData[i][j]["showOnProfile"] == 1:
                        statusEmoji = ":eye:"
                    embed.add_field(name = "Item #" + str(processedData[i][j]["itemID"]) + "- " + processedData[i][j]["name"] + " " + statusEmoji,
                    value = processedData[i][j]["description"])
                pages.append(embed)
            await self.bot.sendEmbedPages(ctx, pages)
    
    @commands.command(name = "showbadge",
                    description = "Toggles whether a badge appears on your profile or not when !profile is used.",
                    brief = "Toggles whether a badge is shown on your profile.")
    async def showBadge(self, ctx, badgeID: int):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201")
        if await self.bot.checkUserHasItem(ctx.message.author.id, badgeID) == False:
            raise self.bot.BOTrasedError("405 You do not have that badge.")
        if await self.bot.checkItemType(badgeID, "badge") == False:
            raise self.bot.BOTrasedError("402 That is not a badge.")
        showOnProfile = 0
        inventoryEntry = await self.bot.fetchSingleInventoryEntry(ctx.message.author.id, badgeID)
        if inventoryEntry["showOnProfile"] == 0:
            showOnProfile = 1
        await self.bot.updateUserInventory(True, ctx.message.author.id, badgeID , showOnProfile)

def setup(bot):
    bot.add_cog(UserProfile(bot))