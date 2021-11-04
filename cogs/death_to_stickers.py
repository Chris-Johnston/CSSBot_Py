import discord
from discord.ext import commands
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import configparser
import datetime
import json

# stuff that handles user analytics
# no commands are associated with this
class DeathToStickers(commands.Cog):
    """
    Stickers are bad and they should feel bad
    """

    def __init__(self, bot):
        # open the config file in the parent directory
        config = configparser.ConfigParser()
        with open('config.ini') as config_file:
            config.read_file(config_file)

        self.bot = bot

        self.no_stickers = []
        # if the database is specified
        if config.has_option(section='Configuration',
                             option='death_to_stickers'):
            self.no_stickers = json.loads(config.get(section='Configuration',
                              option='death_to_stickers'))
        else:
            logger.warn("Sticker channel denylist is not specified in the config.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Inserts a new row into the messages table when a message is sent.

        """
        logger.debug(f"on message, channel id is {message.channel.id}")
        if message.channel.id in self.no_stickers:
            if len(message.stickers) > 0:
                logger.info(f"deleting message {message.id} in channel {message.channel.id} because it had stickers")
                # bah-deleted
                await message.delete()

def setup(bot):
    bot.add_cog(DeathToStickers(bot))
