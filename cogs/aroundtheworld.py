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
    async def on_raw_message_edit(self, payload):
        """
        edit handler, oops
        """
        if payload.cached_message is not None:
            await self.on_message(payload.cached_message)
        else if payload.channel_id == around_the_world_channel_id:
            channel = await self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            await self.on_message(message)


    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Around the world
        """
        if message.channel and isinstance(message.channel, discord.TextChannel) and message.channel.id == around_the_world_channel_id:
            if not "".join(message.content.split()).lower() == "aroundtheworld":
                logger.info(f"Deleted message {message.id}, did not match 'around the world'")
                await message.delete()

def setup(bot):
    bot.add_cog(AroundTheWorldCog(bot))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
