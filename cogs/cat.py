import discord
from discord.ext import commands
import configparser
import random
import asyncio
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Cat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        config = configparser.ConfigParser()
        with open("config.ini") as config_file:
            config.read_file(config_file)

        self.cat_facts = []
        try:
            if config.has_option(section="Configuration", option="catfacts"):
                cat_facts_file = config.get(section="Configuration", option="catfacts")
                with open(cat_facts_file) as facts:
                    self.cat_facts = facts.readlines()
        except Exception as e:
            logger.warn(f"Failed to init cat facts {e}")

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(name='catfact')
    async def catfact(self, ctx):
        if self.cat_facts is None:
            return

        async with ctx.channel.typing():
            q = "?" * random.randrange(1, 6)
            await ctx.send(f"Did you know{q}")
            await asyncio.sleep(random.randrange(1, 3))
            await ctx.send(random.choice(self.cat_facts))
            wow = [ "Wow!", "Me-wow!", "Cool!", "Neat!", "huh", ":)" ]
            await asyncio.sleep(random.randrange(2, 3))
            await ctx.send(random.choice(wow))

def setup(bot):
    bot.add_cog(Cat(bot))

if __name__=='__main__':
    import doctest
    doctest.testmod()
