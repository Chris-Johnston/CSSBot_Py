import discord
from discord.ext import commands
import re

parse_regex = """^\s*([A-Za-z0-9\_\-]+)(?:(?:\w*\(*)([1-8])(?:[\s]*\)*))?\s*$"""

def parse(query: str) -> tuple:
    """
    Parses an input into a pair of the (name, section number)

    Assumes that the default section number is 1.

    If an input is not valid, returns None.

    Does not handle non numeric categories.

    >>> parse("echo(1)")
    ("echo", 1)
    >>> parse("echo")
    ("echo", 1)
    >>> parse("     echo    ")
    ("echo", 1)
    >>> parse("     echo    2")
    ("echo", 2)
    >>> parse("   aaaa    8")
    ("aaaa", 8)
    >>> parse("invalid -1")

    >>> parse("invalid aaa 123")

    >>> parse("invalid 0")

    >>> parse("invalid 9")
    
    >>> parse("invalid 10")

    >>> parse("echo(10)")
    """
    pattern = re.compile(parse_regex, flags=re.IGNORECASE)
    match = pattern.search(query)

    if match is not None:
        name, section_number = pattern.group(1, 2)

        # default to 1
        if section_number is None:
            section_number = 1
        else:
            section_number = int(section_number)
        return name, section_number
    return None

# setup
class ManPageCog:
    def __init__(self, bot):
        self.bot = bot

    # ping command
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command('man', aliases=["manpage"])
    async def man(self, ctx, *, query: str):
        """
        Tries to look up a manpage on 
        https://linux.die.net/
        and replies with the link
        """
        await ctx.send("todo")

# add this cog to the bot
def setup(bot):
    bot.add_cog(ManPageCog(bot))

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
