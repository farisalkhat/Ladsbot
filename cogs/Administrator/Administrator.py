import discord
from discord.ext import commands
import tokens
import getpass
import time


class Administrator(commands.Cog):
    def __init__(self,bot):
        self.bot=bot

    @commands.command(name="restart",aliases=["r"]) 
    @commands.has_permissions(administrator=True)
    async def restart(self,ctx): 
        await self.bot.close()
        time.sleep(3.0)
        await self.bot.connect()

