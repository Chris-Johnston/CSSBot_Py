"""
discord bot cog that is used for creating truth tables
"""
import discord
from discord.ext import commands
from lib.src.boolean_expr_parser import BooleanExpr

class BoolUtilsCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(3, 30, commands.BucketType.user)
    @commands.command()
    async def bool(self, ctx, *, exp):
        """Creates truth table from expression using !,*,^,+

        Wrap expression in "quotes" to include spaces in your expression.
        If there are spaces in your expression and it is not properly wrapped,
        then it will not process correctly, if at all.

        Single chars are variables, more than one char in a row is invalid.
        More than one ! in a row is invalid... fight me.
        More than 5 variables is invalid, otherwise the messages would be long.
        """
        await ctx.send(get_bool_table(exp))

def setup(bot):
    """Sets up the cog"""
    bot.add_cog(BoolUtilsCog(bot))

def get_bool_table(exp):
    """Parses a boolean expression and creates a truth table"""
    boolean_exp = BooleanExpr(exp)
    return "```" + boolean_exp.get_truth_table() + "```"
