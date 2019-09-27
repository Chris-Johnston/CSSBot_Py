"""
Hyphen

Converts messages that are hyphenated
based on the "Hyphen" xkcd comic

https://xkcd.com/37/
"""
import discord
from discord.ext import commands
import re

# this is probably the best regex I've ever made
hyphen_regex = r"(\w+)-(ass) (\w+)"
hyphen_pattern = re.compile(hyphen_regex, flags=re.I)
zero_width_space = '​'

def sanitize(input: str) -> str:
    """
    Removes all special characters and formatting from
    a message.
    """
    for c in ['*', '~', '|', '-', '`', '\\']:
        input = input.replace('*', f"\\{c}")
    input = input.replace('@', f'@{zero_width_space}')
    return input

def replace(input: str) -> bool:
    """
    Checks to see if the given message contains the regex
    and if it does, returns the fixed version, which is bolded.

    >>> replace("Man, that's a sweet-ass car.")
    "Man, that's a **sweet ass-car**."

    >>> replace("sweet-ass car")
    '**sweet ass-car**'

    >>> replace("aaa-ass aaa")
    '**aaa ass-aaa**'

    >>> replace("Man, that's a sweet ass car.")
    
    >>> replace("Man, that's a sweet ass-car.")

    """
    input = sanitize(input)
    match = hyphen_pattern.search(input)
    if match:
        adjective = match.group(1)
        ass = match.group(2)
        noun = match.group(3)

        start_index = match.start()
        end_index = match.end()
        return input[0:start_index] + f'**{adjective} {ass}-{noun}**' + input[end_index:]
    return None

class HyphenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("hyphen")
    async def hyphen(self, ctx):
        await ctx.send("https://xkcd.com/37/")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Checks to see if a message contains a hyphen
        and if it matches the pattern,
        replies with the edited version of the original message.
        """
        # do not respond to bots (including this one)
        if message.author.bot:
            return
        if message.channel and isinstance(message.channel, discord.TextChannel):
            result = replace(message.content)
            if result:
                async with message.channel.typing():
                    await message.channel.send(result)

def setup(bot):
    bot.add_cog(HyphenCog(bot))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
