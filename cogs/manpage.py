import discord
from discord.ext import commands
import re

parse_regex = r"^\s*([A-Za-z0-9\_\-]+)(?:(?:\s*\(?)([1-8])\)?)?\s*$"

def parse(query: str) -> tuple:
    """
    Parses an input into a pair of the (name, section number)

    Assumes that the default section number is 1.

    If an input is not valid, returns None.

    Does not handle non numeric categories.

    >>> parse("echo(1)")
    ('echo', 1)
    >>> parse("echo")
    ('echo', 1)
    >>> parse("     echo    ")
    ('echo', 1)
    >>> parse("     echo    2")
    ('echo', 2)
    >>> parse("   aaaa    8")
    ('aaaa', 8)
    >>> parse("invalid -1")

    >>> parse("invalid aaa 123")

    >>> parse("invalid 0")

    >>> parse("invalid 9")
    
    >>> parse("invalid 10")

    >>> parse("echo(10)")

    """
    pattern = re.compile(parse_regex, flags=re.I)
    match = pattern.search(query)
    if match:
        name, section_number = match.groups()
        # default to 1
        if section_number:
            section_number = int(section_number)
        else:
            section_number = 1
        return name, section_number
    return None

# setup
class ManPageCog:
    def __init__(self, bot):
        self.bot = bot

    # ping command
    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.command('man', aliases=["manpage"])
    async def man(self, ctx, *, query: str):
        """
        Tries to look up a manpage on 
        https://linux.die.net/
        and replies with the link
        """
        # try to parse the query
        parsed = parse(query)
        if parsed:
            await ctx.send(f"https://linux.die.net/man/{parsed[1]}/{parsed[0]}")
        else:
            await ctx.send("Couldn't parse that input. Try something like `echo(1)`, or `ping 8`. The default section number is 1.")

# add this cog to the bot
def setup(bot):
    bot.add_cog(ManPageCog(bot))

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
