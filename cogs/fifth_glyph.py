"""
Fifth glyph is bad, ban at all costs.
"""
import discord
from discord.ext import commands
import re
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# real channel ID
# fifth_glyph_channel_id = 820535744035553290

# testing channel ID
fifth_glyph_channel_id = 820549897501540424

glyphs = ['e', 'E', 'ꗋ', 'æ', 'Æ', 'œ', 'Œ', '€', '£', 'ⱻ', 'Ɇ', 'ɇ', 'Ə', 'ǝ', 'ⱸ', 'Ɛ', 'ℇ']

class FifthGlyphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.channel_id != fifth_glyph_channel_id:
            return
        logger.debug(f"edit for non cached message: {payload.message_id}")
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        await self.on_message(message)

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Audaciously cull the fifth glyph
        """
        if message.channel and isinstance(message.channel, discord.TextChannel) and message.channel.id == fifth_glyph_channel_id:
            for g in glyphs:
                if g in message.content or any([True for a in message.attachments if g in a.filename]):
                    logger.info(f"Deleted message {message.id}, contained verboten glyph '{g}', contents were '{message.content}'")
                    await message.delete()

def setup(bot):
    bot.add_cog(FifthGlyphCog(bot))

if __name__ == '__main__':
    import doctest
    doctest.testmod()

