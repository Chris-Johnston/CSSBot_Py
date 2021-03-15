import discord
from discord.ext import commands
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class HentaiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # do not respond to bots
        if message.author.bot:
            return
        if message.channel and isinstance(message.channel, discord.TextChannel):
            if 'hentai' in message.content.lower():
                logger.info("Ruh roh, hentai mention detected from user {message.author.id}.")
                # Consider: persisting a dict of { Author: count } and 
                #   "welcome" individuals who are not in an entry.
                #   Like, "Please welcome @Conner to the Hentai Hall of Shame. :thinkclap:"
                #   Could also respond with "count: XX" and 
                #   "level up" that user when they pass 10, 20, etc.
                # Consider: editing the message and search & replace the 
                #   "hentai" part with :blobstop: or something. Consider 
                #   doing this only after 25+ usages (if combined with 
                #   previous suggestion).
                await message.add_reaction('\U0001F378') # U+1F378

def setup(bot):
    bot.add_cog(HentaiCog(bot))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
