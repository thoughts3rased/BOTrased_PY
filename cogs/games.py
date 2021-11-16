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


class Games(commands.Cog, name = "Games"):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command(name = "slots",
                        description = "A slot machine, for gambling away your hard-earned credits.",
                        brief = "A slot machine. Different fruit gain you different prizes!")
        async def Slots(self, ctx, bet = str(5)):
            if self.bot.SQLConnection == None:
                raise self.bot.BOTrasedError("201")
            if await self.bot.checkUserExists(ctx.message.author.id) == False:
                raise self.bot.BOTrasedError("200")
            #Validate bet amount
            if bet == "help":
                embed = discord.Embed(title = "About !slots", colour = 0xf4013e)
                embed.add_field(name = "The fruit table:", value = ":watermelon: :watermelon: :watermelon: - 100 times your bet amount \n :grapes: :grapes: :grapes: - 15 times your bet amount \n :banana: :banana: :banana: - 8 times your bet amount \n :pineapple: :pineapple: :pineapple: - 5 times your bet amount \n :skull: :skull: :skull: - you LOSE twice the amount you bet \n Matching the first two fruit will win you your money back.")
                await ctx.send(embed = embed)
                return
            try:
                bet = int(bet)
            except:
                raise self.bot.BOTrasedError("400 Please enter an integer and try again.")
            user = await self.bot.fetchUserProfile(ctx.message.author.id)
            #Does the user have enough money to play with their specified bet?
            if user[3] < bet:
                raise self.bot.BOTrasedError("406")
            #Display an easter egg if the bet amount is 0
            if bet == 0:
                await ctx.send("Freeloader mode activated.")
            #Error out if the bet amount is below zero    
            if bet < 0:
                raise self.bot.BOTrasedError("400 Sorry, I can't give credit. Come back when you're a little hmmmmmm... richer!")
            user[3] = user[3]-bet
            await self.bot.updateUserProfile(user)
            fruits = [":watermelon:", ":grapes:", ":grapes:",  ":banana:", ":banana:", ":banana:",  ":pineapple:", ":pineapple:", ":pineapple:", ":pineapple:",  ":skull:", ":skull:"]
            results = []
            possibleCombos = [[":watermelon:", 100],
                            [":grapes:", 15],
                            [":banana:", 8],
                            [":pineapple:", 5],
                            [":skull:", -2]]
            for i in range(0,3):
                results.append(random.choice(fruits))
            #Try to mimick a slot machine with sleeps and message edits
            message = await ctx.send(":grey_question::grey_question::grey_question:")
            await asyncio.sleep(3.0)
            await message.edit(content = results[0]+":grey_question::grey_question:")
            await asyncio.sleep(1.0)
            await message.edit(content = results[0]+results[1]+":grey_question:")
            await asyncio.sleep(0.3)
            await message.edit(content = results[0]+results[1]+results[2])
            if results[0] == results[1] and results[1] != results[2]:
                user[3] += bet
                await message.edit(content = results[0]+results[1]+results[2]+ "\n"+"That's alright "+ctx.message.author.mention+", you won your money back!")
            elif results[0] == results[1] and results [1] == results[2]:
                index = None
                for i in range(0, 5):
                    if possibleCombos[i][0] == results[0]:
                        index = i
                        break
                user[3] += bet * possibleCombos[index][1]
                winnings = bet * possibleCombos[index][1]
                if results[0] == ":watermelon:":
                    await message.edit(content = results[0]+results[1]+results[2]+ "\n"+"WOW "+ctx.message.author.mention+ ", YOU HIT THE JACKPOT! You won "+str(winnings)+" credits!")
                elif results[0] == ":skull:":
                    await message.edit(content = results[0]+results[1]+results[2]+ "\n"+"Oh dear... You lost an additional "+str(bet*2)+" credits...")
                else:
                    await message.edit(content = results[0]+results[1]+results[2]+ "\n"+"Well done! You won "+str(winnings)+" credits!")
            else:
                await message.edit(content = results[0]+results[1]+results[2]+ "\n"+"Sorry, you didn't win this time.")
            await self.bot.updateUserProfile(user)
    
        @commands.command(name = "daily",
                        description = "Awards a random amount of credits every 24 hours. This is based on the system's date, so timezones are not taken into account.",
                        brief = "Awards you a random amount of credits once per day.")
        async def daily(self, ctx):
            if self.bot.SQLConnection == None:
                raise self.bot.BOTrasedError("201")
            if await self.bot.checkUserExists(ctx.message.author.id) == False:
                raise self.bot.BOTrasedError("200")
            else:
                awardDaily = False
                user = await self.bot.fetchUserProfile(ctx.message.author.id)
                if user[6] == None:
                    awardDaily = True
                else:
                    if user[6] < (int(time.time()) - 86400):
                        awardDaily = True
                if awardDaily == True:
                    bracketDetermine = random.randint(1, 100)
                    if bracketDetermine < 97:
                        awardAmount = random.randint(100, 250)
                        user[3] += awardAmount
                        await ctx.send("Your daily handout comes to "+str(awardAmount)+" credits.")
                    else:
                        awardAmount = random.randint(1000, 1500)
                        user[3] += awardAmount
                        await ctx.send("Lucky you! Your daily handout comes to "+str(awardAmount)+" credits!")
                    user[6] = int(time.time())
                    await self.bot.updateUserProfile(user)
                else:
                    timeRemainingString = await self.bot.grabDailyTimer(user)
                    raise self.bot.BOTrasedError("407 You've claimed your daily too recently. Time remaining: **"+timeRemainingString+"**")
        
        @commands.command(name = "jankenpon",
                        description = "Challenge another user to a game of rock paper scissors. Have your decision made before the countdown finishes to ensure that you don't time out.",
                        brief = "A game of rock paper scissors against another player.",
                        aliases = ["jkp", "rockpaperscissors", "rps"])
        async def jankenpon(self, ctx, opponent: discord.User = None):
            if opponent == None:
                raise self.bot.BOTrasedError("403 You haven't selected an opponent.")
            if opponent == ctx.author:
                raise self.bot.BOTrasedError("400 You cannot challenge yourself.")
                return
            await ctx.send(opponent.mention + ", " + ctx.message.author.mention + " has challenged you to a game of rock paper scissors. Do you accept?")
            tempOpponent = opponent
            timeout = 20.0
            def checkChoice(message):
                return message.content.lower() in ["yes", "y", "accept", "no", "n", "decline"] and message.author == opponent
            req = None
            try:
                req = await self.bot.wait_for("message", check = checkChoice, timeout = timeout)
            except:
                await ctx.send(opponent.mention + " didn't respond in time, and therefore declined the match.")
            if req.content.lower() in ["no", "n", "decline"]:
                await ctx.send(opponent.mention + " declined the match.")           
            else:
                await ctx.send("When I say \"NOW\", send either \"rock\", \"paper\" or \"scissors\"")
                exit = False
                loopCounter = 0
                while not exit:                    
                    message = await ctx.send("On your marks...")
                    await asyncio.sleep(1.0)
                    await ctx.send("Rock")
                    await asyncio.sleep(1.0)
                    await ctx.send("Paper")
                    await asyncio.sleep(1.0)
                    await ctx.send("Scissors")
                    await asyncio.sleep(1.0)
                    await ctx.send("**NOW**")
                    def p1rock(message):
                        return message.content.lower() in ["rock", "paper", "scissors"] and message.author == ctx.message.author
                    def p2rock(message):
                        return message.content.lower() in ["rock", "paper", "scissors"] and message.author == opponent
                    timeout = 1.0
                    ret = await asyncio.gather(
                        self.bot.wait_for("message", timeout = timeout, check = p1rock),
                        self.bot.wait_for("message", timeout = timeout, check = p2rock),
                        return_exceptions = True
                    )
                    authorResult = ret[0].content.lower()
                    opponentResult = ret[1].content.lower()
                    messages = [ctx.message.author.mention + " won this round.", opponent.mention + " won this round."]
                    if authorResult == opponentResult and authorResult != None and opponentResult != None:
                        await ctx.send("That's a **tie**.")
                        break
                    elif authorResult == "rock" and opponentResult == "scissors":
                        await ctx.send(messages[0])
                        break
                    elif authorResult == "scissors" and opponentResult == "rock":
                        await ctx.send(messages[1])
                        break
                    elif authorResult == "rock" and opponentResult == "paper":
                        await ctx.send(messages[1])
                        break
                    elif authorResult == "paper" and opponentResult == "rock":
                        await ctx.send(messages[0])
                        break
                    elif authorResult == "scissors" and opponentResult == "paper":
                        await ctx.send(messages[0])
                        break
                    elif authorResult == "paper" and opponentResult == "scissors":
                        await ctx.send(messages[1])
                        break
                    else:
                        loopCounter += 1
                        if loopCounter == 3:
                            await ctx.send("Players have failed to respond in time too many times, closing match...")
                            break
                        elif authorResult == opponentResult:
                            await ctx.send("Both of you failed to type in time, let's try that again.")
                        elif authorResult == None:
                            await ctx.send(ctx.message.author.mention + " failed to type in time, let's try that again.")
                        else:
                            await ctx.send(opponent.mention + " failed to type in time, let's try that again.")

def setup(bot):
    bot.add_cog(Games(bot))