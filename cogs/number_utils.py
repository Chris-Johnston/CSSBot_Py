"""
discord bot cog that is used for various number utility functions
"""
import discord
from discord.ext import commands

class NumberUtilsCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.command()
    async def convert(self, ctx, num):
        """Convert command
        Converts the supplied number to various bases
        This assumes decimal for no prefix given,
        if there is a prefix given it will use the
        supplied prefix."""
        if isinstance(num, str):
            if str(num).lower().startswith('0b'):
                num = int(num, 2)
            elif str(num).lower().startswith('0x'):
                num = int(num, 16)
            elif str(num).lower().startswith('0o'):
                num = int(num, 8)
            else:
                num = int(num)

        await ctx.send(get_conversions(num))

    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.command()
    async def from_hex(self, ctx, num: str):
        """Converts the supplied hexadecimal number"""
        await ctx.send(get_conversions(int(num, 16)))

    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.command()
    async def from_bin(self, ctx, num: str):
        """Converts the supplied binary number"""
        await ctx.send(get_conversions(int(num, 2)))

def setup(bot):
    """Sets up the cog"""
    bot.add_cog(NumberUtilsCog(bot))

def get_conversions(number: int):
    r"""Gets a string for output that has all of the conversions.

    convert newlines so that they can be tested properly
    >>> get_conversions(1).replace('\n', ' ')
    '``` Dec:    1 Hex:    0x1 Bin:    0b1 Oct:    0o1```'

    """
    ret = f"```\nDec:    {number}\n" +\
          f"Hex:    {hex(number)}\n" +\
          f"Bin:    {bin(number)}\n" +\
          f"Oct:    {oct(number)}```"
    return ret

if __name__ == '__main__':
    import doctest
    doctest.testmod()