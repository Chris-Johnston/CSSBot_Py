"""
CAWW

CAWW CAWWW CAAAWW CAAAAW
"""
import discord
from discord.ext import commands
import re #eeeeee
import random

CAWW = u"\U0001F426"

# https://github.com/Chris-Johnston/CROBBER/blob/master/src/post.py
def translate_message(input: str) -> str:
    """
    Translate a sentence into CRAW speak
    >>> translate_message("Y'all ever just YEET?")
    'CAAWW CAAW CAAW CAAW?'
    """
    # handles punctuation... somewhat
    return re.sub(r'([a-zA-Z\']+)', translate_match, input, flags=re.IGNORECASE)

def translate_match(match):
    return translate_word(match.group(0))

def translate_word(input: str) -> str:
    """
    Translate a word into CAW speak
    >>> translate_word("tests")
    'CAAWW'
    >>> translate_word("test")
    'CAAW'
    >>> translate_word("")
    ''
    >>> translate_word("a")
    'CA'
    >>> translate_word("ab")
    'CAW'
    >>> translate_word("abc")
    'CAW'
    """
    random.seed("CAAAAAWWWWW")
    if len(input) == 0:
        return ''
    if len(input) == 1:
        return 'CA'
    if len(input) == 2 or len(input) == 3:
        return 'CAW'
    # subtract the starting C and the ending W
    x = len(input) - 2
    # must have at least one A
    num_a = random.randint(1, x)
    return 'C' + ('A'*num_a) + ('W'*(x - (num_a - 1)))

class CrobCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        CAWWW

        CAAAW CAAAWW CAW CA CAWWW
        """
        if not payload.guild_id:
            return
        user = await self.bot.fetch_user(payload.user_id)
        guild = await self.bot.fetch_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return        

        print(payload.emoji.name, type(payload.emoji.name), CAWW, user, user.bot, payload.emoji == CAWW)
        if user and not user.bot and payload.emoji.name == CAWW:
            message = await channel.fetch_message(payload.message_id)

            # check if already CAWWed
            for r in message.reactions:
                if r.emoji == CAWW and r.me:
                    return
            if isinstance(channel, discord.TextChannel):
                await channel.send(
                    f'Translation: `{translate_message(message.content)}`'
                )

def setup(bot):
    bot.add_cog(CrobCog(bot))

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
