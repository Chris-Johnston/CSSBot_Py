"""
Around the world
"""
import discord
from discord.ext import commands
import re
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

around_the_world_channel_id = 810607632330260480

class AroundTheWorldCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Around the world
        """
        if message.author.id == 85614143951892480: # allow ub3r bot because it is funny
            return
        if message.channel and isinstance(message.channel, discord.TextChannel) and message.channel.id == around_the_world_channel_id:
            if not "".join(message.content.split()).lower() == "aroundtheworld":
                logger.info(f"Deleted message {message.id}, did not match 'around the world'")
                await message.delete()

def setup(bot):
    bot.add_cog(AroundTheWorldCog(bot))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
