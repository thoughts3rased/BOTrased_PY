import asyncio
from cogs.userprofile import UserProfile
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

class Shop(commands.Cog, name = "Shop"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name = "Shop",
                    description = "Show all items that are currently available in the shop.",
                    brief = "Browse the shop.")
    async def shop(self, ctx):
        if self.bot.SQLConnection == None:
            raise self.bot.BOTrasedError("201 Sorry, but I can't currently contact the database to access the shop.")
        shopData = await self.bot.fetchItemDatabase()
        shopData = [shopData[i:i + 10] for i in range(0, len(shopData), 10)]
        pages = []
        for i in range(0, len(shopData)):
            embed = discord.Embed(title = "BOTrased's Wares", colour = discord.Color.purple())
            for j in range (0, len(shopData[i])):
                if shopData[i][j]["purchasable"] == 1:
                    embed.add_field(name = "Item #" + str(shopData[i][j]["itemID"]) + " - "+ shopData[i][j]["name"] + " (" + (shopData[i][j]["type"]) + ")", value = "Price - " + str(shopData[i][j]["price"]) + " credits \n \"" + shopData[i][j]["description"] + "\"")
            
            pages.append(embed)
    
        await self.bot.sendEmbedPages(ctx, pages)
        
                    
    @commands.command(name = "Buy",
                        description = "Purchase an item from the shop using your credits.",
                        brief = "Purchase an item from the store.")
    async def buy(self, ctx, itemNo):
        try:
            int(itemNo)
        except:
            await ctx.send("That item ID is not valid.")
            return
        items = await self.bot.fetchItemDatabase()
        itemIndex = None
        for i in range(0, len(items)):
            if int(items[i]["itemID"]) == int(itemNo) and items[i]["purchasable"] == 1:
                itemIndex = i
                break
        if itemIndex == None:
            raise self.bot.BOTrasedError("408 That item ID is not valid.")
        profile = await self.bot.fetchUserProfile(ctx.message.author.id)
        if await self.bot.checkUserHasItem(ctx.message.author.id, itemNo) == True:
            raise self.bot.BOTrasedError("409")   
        if profile[3] > items[itemIndex]["price"]:
            profile[3] -= items[itemIndex]["price"]
            await self.bot.updateUserProfile(profile)
            await self.bot.updateUserInventory(False, ctx.message.author.id, itemNo)
            await ctx.send("You have successfully purchased **" +items[itemIndex]["name"]+"**")
        else:
            raise self.bot.BOTrasedError("406 You don't have enough credits to buy this.")
        


        


def setup(bot):
    bot.add_cog(Shop(bot))