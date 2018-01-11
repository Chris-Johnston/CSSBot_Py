"""
discord bot cog that is used for various number utility functions
"""
import discord
from discord.ext import commands

class BoolUtilsCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bool(self, ctx, exp):
        """
        """
        await ctx.send(get_bool_table(exp))

def setup(bot):
    """Sets up the cog"""
    bot.add_cog(NumberUtilsCog(bot))

def get_bool_table(exp):
    """Parses a boolean expression and creates a truth table"""
    boolean_exp = BooleanExpr(exp)
    return boolean_exp.get_truth_table()

