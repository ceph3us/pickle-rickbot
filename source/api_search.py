import discord
from discord.ext import commands


# ********************************************** #
# LANGUAGE API SEARCH COMMANDS ***************** #
# ********************************************** #

class APISearch:
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(APISearch(bot))
