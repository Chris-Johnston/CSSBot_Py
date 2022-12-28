# enforces use of the :kirbutt: emote
# based the owner or owners of a No Fuckin' ziTi for the emote
import discord
from discord.ext import commands
import logging
import configparser
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class NoFuckinZiti(commands.Cog):
    """
    Enforces use of an emote based on the owners of it.
    """

    def __init__(self, bot):
        self.bot = bot

        self.owners = [ ]
        self.emoji_name = "kirbutt"

        config = configparser.ConfigParser()
        with open('config.ini') as config_file:
            config.read_file(config_file)

        try:
            if config.has_option(section="NoFuckinZiti", option="owners"):
                self.owners = json.loads(config.get(section="NoFuckinZiti", option="owners"))
            else:
                logger.warn("No owners listed in config for the No Fuckin Ziti")

            if config.has_option(section="NoFuckinZiti", option="emoji_name"):
                self.emoji_name = config.get(section="NoFuckinZiti", option="emoji_name")
        except Exception as e:
            logger.warn(f"Failed to find owners of the No Fuckin Ziti {e}")

        self.search_pattern = f"<:{self.emoji_name}:"

    async def handle_message(self, message):
        if message.author.id in self.owners:
            # allowed to use it
            return
        if self.search_pattern not in message:
            return
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to remove message {message.id} for containing the No Fuckin ziTi")        

    @commands.Cog.listener()
    async def on_message_edit(self, _, message):
        # don't care about what happens if it isn't in the cache, this is probably good enough
        await self.handle_message(message)

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.handle_message(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name != self.emoji_name:
            # not a match
            return
        if payload.user_id in self.owners:
            # user is allowed to use this reaction
            return
        # remove the reaction
        try:
            # guild = self.bot.get_guild(payload.guild_id)
            # not going to deal with threads because nobody uses them
            channel = self.bot.get_partial_messageable(payload.channel_id, guild_id=payload.guild_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)            
        except Exception as e:
            logger.error(f"Failed to remove reaction from {payload.user_id} on {payload.guild_id}/{payload.channel_id}/{payload.message_id}")


def setup(bot):
    bot.add_cog(NoFuckinZiti(bot))