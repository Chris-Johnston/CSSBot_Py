# discord bot cog that is used for various number utility functions
import discord
from discord.ext import commands

class NumberUtilsCog:
    def __init__(self, bot):
        self.bot = bot

    # convert command
    # converts the supplied number to various bases
    # this assumes decimal, unless it is a string that has
    # a prefix of 0x 0b or 0o
    @commands.command()
    async def convert(self, ctx, num):
        if isinstance(num, str):
            if(str(num).lower().startswith('0b')):
                num = int(num, 2)
            elif (str(num).lower().startswith('0x')):
                num = int(num, 16)
            elif (str(num).lower().startswith('0o')):
                num = int(num, 8)
            else:
                num = int(num)

        await ctx.send(get_conversions(num))

    @commands.command()
    async def from_hex(self, ctx, num: str):
        # from hexadecimal
        await ctx.send(get_conversions(int(num, 16)))

    @commands.command()
    async def from_bin(self, ctx, num: str):
        # from binary
        await ctx.send(get_conversions(int(num, 2)))

def setup(bot):
    bot.add_cog(NumberUtilsCog(bot))

def get_conversions(number: int):
    return f"```\nDec:    {number}\n" + f"Hex:    {hex(number)}\n" + f"Bin:    {bin(number)}\n" + f"Oct:    {oct(number)}```"