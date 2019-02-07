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
    ("echo", 2)
    >>> parse("invalid -1")

    >>> parse("invalid aaa 123")

    >>> parse("invalid 0")

    >>> parse("invalid 9")
    
    >>> parse("invalid 10")

    >>> parse("echo(10)")
    """
    pattern = re.compile(parse_regex, flags=re.IGNORECASE)
    match = pattern.search

    name, section_number = pattern.group(1, 2)

    # default to 1
    if section_number is None:
        section_number = 1

    print('name', name, 'section #', section_number)

    try:
        if len(split) == 1:
            # only contains a single term
            name = split[0]
        elif len(split) == 2:
            name = split[0]
            section_number = int(section_number)
            if not (0 < section_number <= 8):
                return None
        return name, section_number
    except ValueError:
        return None
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
