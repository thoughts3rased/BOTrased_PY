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

class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name = "warn",
                    description = "Warns a user with a reason. This will send them a DM notifying them that they have been warned with the reason, server and who warned them. Requires \"Kick Members\" permission.",
                    brief = "Warns a user with a reason. Requires \"Kick Members\" permission.")
    #Does the user have the permissions required to kick members? If not, raise MissingPermissions and handle the error in the ErrorHandler cog.                
    @commands.has_guild_permissions(kick_members = True)
    async def warn(self, ctx, user: discord.Member = None, *, reason = "No reason given."):
            #Has the user failed to pass an argument?
            if user == None:
                await ctx.send("You have not specified a user. Please @mention a user or provide their user ID.")
            #Has the user tried to warn themselves?
            elif user.id == ctx.message.author.id:
                await ctx.send("You cannot warn yourself.")
            #Has the user tried to warn the bot?
            elif user.id == self.bot.user.id:
                await ctx.send("Sorry "+ctx.author.mention+", I'm afraid I can't let you do that.")
            #If they've passed both of these checks, then the command and its arguments must be valid
            else:
                embed = discord.Embed(title = "You have been warned!", description = "Reason: " + reason, colour = discord.Colour.gold())
                embed.add_field(name = "Server:", value = ctx.message.guild.name)
                embed.add_field(name = "Warned by:", value = ctx.message.author.display_name+"#"+ctx.message.author.discriminator, inline = False)
                embed.set_thumbnail(url = "https://i.imgur.com/w5CDAw7.png")
                #Send the embed in the target's DMs
                await user.send(embed = embed)
            if reason == "No reason given.":
                reason = "NULL"
            try:
                log = {"server": ctx.message.guild.id,
                        "admin": ctx.message.author.id,
                        "target": user.id,
                        "type": "warn",
                        "reason": reason,
                        "bot": 1,
                        "time": int(time.time())}
                logID = await self.bot.createAdminLogEntry(log)
                await ctx.send("Warn entry created with case number " + str(logID))
            except:
                await ctx.send("Error logging to database, case not recorded.")

    @warn.error
    async def warnError(self, ctx, exc):
        if isinstance(exc, commands.BadArgument):
            await ctx.send("Invalid user selected.")
        elif isinstance(exc, commands.MissingPermissions):
            await ctx.send("You are not authorised to use this command.")

    @commands.command(name = "kick",
                    description = "Temporarily kicks a user from the server with a reason, and notifies them via a DM. Requires \"Kick Members\" permission.",
                    brief = "Kicks a user from the server. Requires \"Kick Members\" permission.")
    @commands.has_guild_permissions(kick_members = True)
    async def kick(self, ctx, user: discord.Member = None, *, reason = "No reason given."):
        kicked = False
        #Has the user failed to pass an argument?
        if user == None:
            await ctx.send("You have not specified a user. Please @mention a user or provide their user ID.")
        #Has the user tried to kick themselves?
        elif user.id == ctx.message.author.id:
            await ctx.send("You cannot kick yourself.")
        #If they've passed both of these checks, then the command and its arguments must be valid
        else:
            #Try kicking the user and if this is successful set the flag to True
            try:
                await user.kick(reason = reason)
                kicked = True
            #If this fails, send a message back into the channel notifying the user of the issue
            except:
                await ctx.send("I had an issue kicking that member, make sure to check the position of my roles on the hierarchy if you need to kick someone higher up than me.")
            if kicked:
                embed = discord.Embed(title = "You have been kicked!", description = "Reason: " + reason, colour = discord.Colour.orange())
                embed.set_thumbnail(url = "https://i.imgur.com/XpWbrhp.png")
                embed.add_field(name = "Server:", value = ctx.message.guild.name)
                embed.add_field(name = "Kicked by:", value = ctx.message.author.display_name+"#"+ctx.message.author.discriminator, inline = False)
                #Try sending the target user the embed in their DMs
                try:
                    await user.send(embed = embed)
                #If there's an issue doing this, throw an error
                except:
                    await ctx.send("There was an issue sending the user their kick message. They may have server private messages turned off, or they may have blocked me.")
                try:
                    log = {"server": ctx.message.guild.id,
                        "admin": ctx.message.author.id,
                        "target": user.id,
                        "type": "kick",
                        "reason": reason,
                        "bot": 1,
                        "time": int(time.time())}
                    logID = await self.bot.createAdminLogEntry(log)
                    await ctx.send("Kick entry created with case number " + str(logID))
                except:
                    await ctx.send("Error logging to database, case not recorded.")
    
    @kick.error
    async def kickError(self, ctx, exc):
        if isinstance(exc, commands.BadArgument):
            await ctx.send("Invalid user selected.")
        elif isinstance(exc, commands.MissingPermissions):
            await ctx.send("You are not authorised to use this command.")

    @commands.command(name = "ban",
                    description = "Bans a user from the server with a reason and sends them a DM with the reason for their ban. Requires “Ban Members” permission.",
                    brief = "Bans a user from the server. Requires “Ban Members” permission.",
                    aliases = ["kill"])
    @commands.has_guild_permissions(ban_members = True)
    async def ban(self, ctx, user: discord.Member = None, *, reason = "No reason given."):
        banned = False
        #Has the user failed to pass an argument?
        if user == None:
            await ctx.send("You have not specified a user. Please @mention a user or provide their user ID.")
        #Has the user tried to ban themselves?
        elif user.id == ctx.message.author.id:
            await ctx.send("You cannot ban yourself.")
        #If they've passed both of these checks, then the command and its arguments must be valid
        else:
            #Try banning the user and if this is successful set the flag to True
            try:
                await user.ban(reason = reason, delete_message_days=0)
                banned = True
            #If this fails, send a message back into the channel notifying the user of the issue
            except:
                await ctx.send("I had an issue banning that member, make sure to check the position of my roles on the hierarchy if you need to ban someone higher up than me.")
            if banned:
                embed = discord.Embed(title = "You have been permanently banned from "+ ctx.message.guild.name + "!", description = "Reason: " + reason, colour = discord.Colour.red())
                embed.set_thumbnail(url = "https://i.imgur.com/HBYFM4H.png")
                embed.add_field(name = "Banned by:", value = ctx.message.author.display_name+"#"+ctx.message.author.discriminator, inline = False)
                #Try sending the target user the embed in their DMs
                try:
                    await user.send(embed = embed)
                #If there's an issue doing this, throw an error
                except:
                    await ctx.send("There was an issue sending the user their ban message. They may have server private messages turned off, or they may have blocked me.")
                try:
                    log = {"server": ctx.message.guild.id,
                        "admin": ctx.message.author.id,
                        "target": user.id,
                        "type": "ban",
                        "reason": reason,
                        "bot": 1,
                        "time": int(time.time())}
                    logID = await self.bot.createAdminLogEntry(log)
                    await ctx.send("Ban entry created with case number " + str(logID))
                except:
                    await ctx.send("Error logging to database, case not recorded.")

    @ban.error
    async def banError(self, ctx, exc):
        if isinstance(exc, commands.BadArgument):
            await ctx.send("Invalid user selected.")
        elif isinstance(exc, commands.MissingPermissions):
            await ctx.send("You are not authorised to use this command.")
        else:
            await ctx.send("Sorry, an unspecified error occurred.")
    
    @commands.command(name = "clear",
                    description = "Clears a specified number of messages from the chat one by one. If no amount is specified, the default amount is set to 50. Requires \"Manage Messages\" permission.",
                    brief = "Clears messages. Requires \"Manage Messages\" permission.")
    @commands.has_guild_permissions(manage_messages = True)
    async def clear(self, ctx, amount = 50):
        #Try casting amount as an integer
        try:
            amount = int(amount)
        #If this fails, send an error message and break out of the command
        except:
            await ctx.send("That value was not an integer. Please enter an integer number and try again.")
            return
        #Try clearing the messages
        try:
            await ctx.channel.purge(limit = amount)
            #If this succeeds, send a success message into the chat
            message1 = await ctx.send("Successfully cleared "+str(amount)+" messages.")
        #If this fails, send an error message into the chat
        except:
            await ctx.send("Sorry, there has been a problem with clearing those messages. Make sure I have the correct permissions to do this, and try again.")
        try:
            log = {"server": ctx.message.guild.id,
                        "admin": ctx.message.author.id,
                        "target": ctx.message.channel.id,
                        "type": "clear",
                        "reason": str(amount),
                        "bot": 1,
                        "time": int(time.time())}
            logID = await self.bot.createAdminLogEntry(log)
            message2 = await ctx.send("Clear entry created with case number " + str(logID))
        except:
            await ctx.send("Error logging to database, case not recorded.")        
        await asyncio.sleep(5.0)
        if message1:
            await message1.delete()
        if message2:
            await message2.delete()
        

    @clear.error
    async def clearError(self, ctx, exc):
        if isinstance(exc, commands.MissingPermissions):
            await ctx.send("You are missing permissions to perform this command.")
        
        elif isinstance(exc, commands.BotMissingPermissions):
            await ctx.send("I do not have the required permissions to perform this command.")

    @commands.command(name = "nickname",
                    description = "Changes the nickname of a target member to any name under 32 characters in length. Requires \"Manage Nicknames\" permission.",
                    brief = "Change a member's nickname.")
    @commands.has_guild_permissions(manage_nicknames = True)
    async def nickname(self, ctx, target:discord.Member, *, nickname):
        if len(nickname) > 32:
            await ctx.send("Nicknames cannot be longer than 32 characters in length.")
            return
        await target.edit(nick = nickname)
        try:
            log = {"server": ctx.message.guild.id,
                        "admin": ctx.message.author.id,
                        "target": target.id,
                        "type": "name",
                        "reason": "NULL",
                        "bot": 1,
                        "time": int(time.time())}
            logID = await self.bot.createAdminLogEntry(log)
            await ctx.send("Nickname entry created with case number " + str(logID))
        except:
            await ctx.send("Error logging to database, case not recorded.")

    @nickname.error
    async def nicknameError(self, ctx, exc):
        if isinstance(exc, commands.BadArgument):
            await ctx.send("Invalid user selected.")
        elif isinstance(exc, commands.MissingPermissions):
            await ctx.send("You are not authorised to use this command.")
    
    @commands.command(name = "modlog",
                    description = "View the past 100 entries in the modlog. You may search by adding the type after the command, or you may view a specific case by typing the case number after the command.",
                    brief = "View the past 100 entries in the modlog.",
                    aliases = ["adminlog"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild = True)
    async def modlog(self, ctx, type = None):
        query = "select * from adminLogs where serverID = '" + str(ctx.message.guild.id) + "'"
        #Try to determine if the user is trying to find a specific case
        try:
            async with ctx.typing():
                int(type)
                query = query + "and logID = " + str(type)
                result = await self.bot.queryDatabase(query)
                if not result:
                    await ctx.send("An entry for this server with that case number was not found.")
                    return
                data = []
                for i in range(0, 8):
                    data.append(result[0][i])
                icons = {"warn":"https://i.imgur.com/w5CDAw7.png",
                        "kick":"https://i.imgur.com/XpWbrhp.png",
                        "ban":"https://i.imgur.com/HBYFM4H.png",
                        "clear":"https://static.thenounproject.com/png/492682-200.png",
                        "nickname":"https://assets.onlinelabels.com/Images/Predesign/00000002/1117/Red-Name-Tag.png"}
                embed = discord.Embed(title = "Case No. "+str(data[0]), description = "Entry created at " + str(datetime.datetime.fromtimestamp(data[6]).strftime('%Y-%m-%d %H:%M:%S')) + "(UTC+0:00)")
                admin = await self.bot.fetch_user(data[3])
                recipient = None
                text = None
                #This is if/else hell and I really wish I could do it in another way
                if data[4] == "name":
                    data[4] = "nickname"
                if data[4] == "clear":
                    text = await self.bot.fetch_channel(data[2])
                else:
                    recipient = await self.bot.fetch_user(data[2])
                try:
                    embed.set_thumbnail(url = icons[str(data[4])])
                except:
                    pass
                embed.add_field(name = "Type", value = str(data[4]).title(), inline = False)
                if data[4] == "clear":
                    embed.add_field(name = "Channel", value = str(text))
                else:
                    embed.add_field(name = "Recipient", value = str(recipient.name)+"#"+str(recipient.discriminator), inline = False)
                embed.add_field(name = "Administrator", value = str(admin.name) + "#" + str(admin.discriminator), inline = False)
                if data[4] == "clear":
                    embed.add_field(name = "Amount of messages cleared", value = str(data[5]))
                elif data[4] == "nickname":
                    pass
                elif data[5] == None or data[5] == "NULL":
                    embed.add_field(name = "Reason", value = "No reason given.", inline = False)
                else:
                    embed.add_field(name = "Reason", value = data[5])
                await ctx.send(embed = embed)

        except:             
            async with ctx.typing():
                if type != None:
                    if type.lower() == "nickname":
                        type = "name"
                    query = query + "and type = '" + type.lower() +"'"
                query = query + " ORDER BY logID DESC LIMIT 100"
                pages = []
                records = await self.bot.queryDatabase(query)
                if len(records) == 0:
                    await ctx.send("No moderator logs were found for this server.")
                    return
                processedData = [records[i:i + 5] for i in range(0, len(records), 5)]
                pageCount = len(processedData)
                valueSearched = type
                if valueSearched == None:
                    valueSearched = "All types"
                if valueSearched == "name":
                    valueSearched = "Nickname"
                for i in range (0, pageCount):
                    embed = discord.Embed(title = "Modlog for " + ctx.message.guild.name, description = "Type of action searched for: " + valueSearched.title())
                    for j in range(0, len(processedData[i])):
                        if processedData[i][j][4] != "name":
                            fieldText = "Type - " + processedData[i][j][4].title() + "\n"
                        else:
                            fieldText = "Type - Nickname\n"
                        admin = await self.bot.fetch_user(processedData[i][j][3])
                        if admin != None:
                            fieldText += "Administrator - " + admin.name+"#"+admin.discriminator+"\n"
                        else:
                            fieldText += "Administator - Invalid user\n"
                        if processedData[i][j][4] == "clear":
                            try:
                                channel = await self.bot.fetch_channel(processedData[i][j][2])
                                if channel != None:
                                    fieldText += "Channel - #" + str(channel) + "\n"
                                else:
                                    fieldText += "Channel - #invalid-channel\n"
                            except:
                                fieldText += "Channel - #invalid-channel\n"
                            fieldText += "Amount cleared - " + str(processedData[i][j][5]) + "\n"
                        else:
                            try:
                                recipient = await self.bot.fetch_user(processedData[i][j][2])
                                if recipient != None:
                                    fieldText += "Recipient - " + recipient.name + "#" + recipient.discriminator +"\n"
                                else:
                                    fieldText += "Recipient - Invalid User\n"
                            except:
                                fieldText += "Recipient - Invalid User\n"
                            if processedData[i][j][4] != "name":
                                reason = processedData[i][j][5]
                                if reason == None or reason == "NULL":
                                    reason = "No reason given."
                                fieldText += "Reason - " + reason
                        embed.add_field(name = "Case " + str(processedData[i][j][0]), value = fieldText, inline = False)
                        embed.set_footer(text = "Page " + str(i + 1) + "/" + str(pageCount))
                    pages.append(embed)
                await self.bot.sendEmbedPages(ctx, pages)

    
    @modlog.error
    async def modlogError(self, ctx, exc):
        if isinstance(exc, commands.MissingPermissions):
            await ctx.send("You are not authorised to use this command.")      

def setup(bot):
    bot.add_cog(Administration(bot))