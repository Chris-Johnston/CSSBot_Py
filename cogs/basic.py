import discord
from discord.ext import commands
import time
import aiohttp

# discord.py calls commands cogs
# so I'm just going to roll with it

# setup
class BasicCog:
    def __init__(self, bot):
        self.bot = bot

    # ping command
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def ping(self, ctx):
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
        await ctx.send(f'http://69.91.192.220/nph-jpeg.cgi?0&{time.time()}')
        
    @commands.command(name='405')
    async def i405(self, ctx):
        await ctx.send(f'https://images.wsdot.wa.gov/nw/405vc03022.jpg?t={time.time()}')

    @commands.command(name='xkcd')
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def get_xkcd(self, ctx, id: int=None):
        """
        Replies with a random xkcd comic URL.
        :param ctx:
        :return:
        """
        if not id or id < 1:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://c.xkcd.com/random/comic/') as resp:
                    await ctx.send(resp.url)
        else:
            await ctx.send(f'https://xkcd.com/{id}/')


# add this cog to the bot
def setup(bot):
    bot.add_cog(BasicCog(bot))


def _test_example():
    """
    Example of how to incorporate doctests
    
    >>> _test_example()
    'Pong!'

    :return: 'Pong!'
    """

    return 'Pong!'

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
