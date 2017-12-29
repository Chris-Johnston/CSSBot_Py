import discord
from discord.ext import commands

# discord.py calls commands cogs
# so I'm just going to roll with it

# setup
class BasicCog:
    def __init__(self, bot):
        self.bot = bot

    # ping command
    @commands.command()
    async def ping(self, ctx):
        await ctx.send('Pong!')

    # echo command
    @commands.command(name='echo')
    async def echo(self, ctx, *, message='_echo_'):
        await ctx.send(f'{ctx.author.mention} : {message}')

    # github command
    @commands.command(name='github')
    async def github(self, ctx):
        await ctx.send(f'https://github.com/Chris-Johnston/CSSBot_Py')

# add this cog to the bot
def setup(bot):
    bot.add_cog(BasicCog(bot))