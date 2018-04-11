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

        await ctx.send(get_conversions(_normalize_input(num)))

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


def _normalize_input(in_str: str):
    """

    >>> _normalize_input('')
    -1
    >>> _normalize_input('____')
    -1
    >>> _normalize_input('0b1_0_1')
    5
    >>> _normalize_input('0xA')
    10
    >>> _normalize_input('0XF_F')
    255
    >>> _normalize_input('0o7')
    7
    >>> _normalize_input('123123')
    123123
    >>> _normalize_input('123_123')
    123123
    >>> _normalize_input('-123_123')
    -123123

    Accepts the user input and converts it to several forms
    """

    num = -1

    # trim the string, remove underscores and to lower
    in_str = in_str.strip().replace('_', '').lower()

    # convert numbers that are binary
    if in_str.startswith('0b'):
        num = int(in_str, 2)
    elif in_str.startswith('0x') or in_str.startswith('$'):
        num = int(in_str.replace('$', ''), 16)
    elif in_str.startswith('0o'):
        num = int(in_str, 8)
    else:
        num = int(in_str.replace('#', ''))
    return num

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
