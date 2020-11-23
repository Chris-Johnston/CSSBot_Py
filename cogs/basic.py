import discord
from discord.ext import commands
import time
import aiohttp
import urllib.parse
import logging
import requests
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# discord.py calls commands cogs
# so I'm just going to roll with it

# trust me, this contains a zero-width space
zero_width_space = '​'

def sanitize_ping(message: str) -> str:
    """
    Checks that a message is sanitized with a zero width space

    >>> sanitize_ping("@test")
    '@​test'
    >>> sanitize_ping("@ test")
    '@​ test'
    >>> sanitize_ping(None)

    """
    if message is None:
        return None
    return message.replace('@', '@' + zero_width_space)

def generate_claps(message: str, emoji: str) -> str:
    """
    Generates :clap: a :clap: message :clap: separated :clap:
    with :clap: emojis

    >>> generate_claps("test", "a") # Don't embed emoji in source code
    'test'
    >>> generate_claps("test message", "a")
    'test a message'
    >>> generate_claps("", "a")
    >>> generate_claps(None, "a")
    >>> generate_claps("test message", '')

    """
    if message is None or message.strip() == "" or emoji is None or emoji.strip() == "":
        return None

    # no pings!
    message = sanitize_ping(message)
    message = message.strip()
    # if there were no changes, then don't modify anything
    emoji = sanitize_ping(emoji)
    emoji = emoji.strip()
    if emoji is None or emoji == "":
        return message
    split = message.split()
    # no point when there's nothing to split
    if len(split) <= 1:
        return message
    ret = ''
    for word in split[:-1]:
        ret += f"{word} {emoji} "
    ret += split[-1]
    return ret

def _test_example():
    """
    Example of how to incorporate doctests
    
    >>> _test_example()
    'Pong!'

    :return: 'Pong!'
    """
    return 'Pong!'

# setup
class BasicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ping command
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def ping(self, ctx):
        logger.debug("Ping command")
        await ctx.send(_test_example())

    # echo command
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(name='echo')
    async def echo(self, ctx, *, message='_echo_'):
        await ctx.send(f'{ctx.author.mention} : {message}')

    # github command
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='github')
    async def github(self, ctx):
        await ctx.send(f'https://github.com/Chris-Johnston/CSSBot_Py')

    @commands.command(name='webcam')
    async def webcam(self, ctx):
        webcam_url = "http://69.91.192.220/nph-jpeg.cgi"
        message_content = f'<http://69.91.192.220/nph-jpeg.cgi?0&{time.time()}>'

        r = requests.get(webcam_url)
        f = discord.File(r.content)
        await ctx.send(content=message_content, file=f)
        
    @commands.command(name='405')
    async def i405(self, ctx):
        await ctx.send(f'https://images.wsdot.wa.gov/nw/405vc03022.jpg?t={time.time()}')

    @commands.command(name='xkcd')
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def get_xkcd(self, ctx, id: int=None):
        """
        Replies with a random xkcd comic URL.
        :return:
        """
        if not id or id < 1:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://c.xkcd.com/random/comic/') as resp:
                    logger.info(f"XKCD: {resp.url}")
                    await ctx.send(resp.url)
        else:
            logger.info(f"XKCD: {id}")
            await ctx.send(f'https://xkcd.com/{id}/')

    @commands.command(name='lmgtfy')
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def lmgtfy(self, ctx, *, search: str):
        """
        Generates a LMGTFY link for the given search query
        """
        encoded = urllib.parse.quote_plus(search)
        await ctx.send(f'Was that so hard? https://lmgtfy.com/?q={encoded}')

    @commands.command(name='g', aliases=["google", "search"])
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def google(self, ctx, *, search: str):
        """
        Generates a Google search link for the given search query
        """
        encoded = urllib.parse.quote_plus(search)
        await ctx.send(f'Really!? How lazy are you? https://www.google.com/search?q={encoded}')
    
    @commands.command(name=u"clap")
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clap(self, ctx, emoji, *, message):
        await ctx.send(generate_claps(message, emoji))

    @commands.command(name=u"\U0001F44F", hidden = True)
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clap_no_skin_tone(self, ctx, *, message):
        emoji = u"\U0001F44F"
        await ctx.send(generate_claps(message, u"\U0001F44F"))

    # hack to get around the issue of skin tone modifiers
    @commands.command(name=u"\U0001F44F\U0001F3FB", hidden = True)
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clap_skin_tone_1(self, ctx, *, message):
        await ctx.send(generate_claps(message, u"\U0001F44F\U0001F3FB"))
    
    @commands.command(name=u"\U0001F44F\U0001F3FC", hidden = True)
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clap_skin_tone_2(self, ctx, *, message):
        await ctx.send(generate_claps(message, u"\U0001F44F\U0001F3FC"))
    
    @commands.command(name=u"\U0001F44F\U0001F3FD", hidden = True)
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clap_skin_tone_3(self, ctx, *, message):
        await ctx.send(generate_claps(message, u"\U0001F44F\U0001F3FD"))

    @commands.command(name=u"\U0001F44F\U0001F3FE", hidden = True)
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clap_skin_tone_4(self, ctx, *, message):
        await ctx.send(generate_claps(message, u"\U0001F44F\U0001F3FE"))

    @commands.command(name=u"\U0001F44F\U0001F3FF", hidden = True)
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clap_skin_tone_5(self, ctx, *, message):
        await ctx.send(generate_claps(message, u"\U0001F44F\U0001F3FF"))

# add this cog to the bot
def setup(bot):
    bot.add_cog(BasicCog(bot))

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
