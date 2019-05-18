"""
Starboard

Posts quotes of starred messages to the #starboard channel if it exists.
"""

import discord
from discord.ext import commands
import re
import datetime

# star emoji used to update the starboard
STAR = u"\u2B50"
# require 3 or more stars to be posted on the starboard
STAR_THRESHOLD = 3

# does not care about stuff before or after the link
MESSAGE_LINK_REGEX = re.compile(r'https:\/\/discordapp.com\/channels\/(\d+)\/(\d+)\/(\d+)', flags=re.RegexFlag.I)

def message_link(guild_id, channel_id, message_id) -> str:
    """
    Generates a message link from the given Ids

    >>> message_link(1, 2, 3)
    'https://discordapp.com/channels/1/2/3'

    """
    return f'https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}'

def parse_message_link(input: str) -> (int, int, int):
    """
    Parses a message link into it's parts

    >>> parse_message_link('https://discordapp.com/channels/1/2/3')
    (1, 2, 3)

    >>> parse_message_link('dont care about https://discordapp.com/channels/111/222/333 stuff before or after')
    (111, 222, 333)

    """
    result = MESSAGE_LINK_REGEX.match(input)
    if result:
        return [int(x) for x in result.groups()]
    return None

class StarboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_starboard_channel(self, guild_id) -> discord.TextChannel:
        """
        Gets the #starboard channel, if there is one.
        Must be named #starboard, case insensitive.
        Returns none if client cannot access the guild or find a matching channel.
        """
        assert self.bot is not None

        # get the guild
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return
        
        # get channel with matching name, if any
        channel_iterator = filter(lambda x: x.name.lower() == "starboard", guild.channels)
        if channel_iterator is None:
            return
        return next(channel_iterator)

    async def generate_message(self, guild_id, channel_id, message_id, stars):
        """
        Generates the message text and the embed
        to post or update for a message on the starboard
        """
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return None, None
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return None, None
        message = await channel.fetch_message(message_id)

        msg_link = message_link(guild_id, channel_id, message_id)
        # the message to post
        send_message = f'{stars} {STAR} {msg_link}'

        # generate the embed
        send_embed = discord.Embed()\
            .set_author(name = message.author.display_name, icon_url = message.author.avatar_url)
        send_embed.colour = discord.Color.gold()
        send_embed.description = message.content
        send_embed.timestamp = datetime.datetime.now()

        if message.attachments:
            # just use the first attachment
            attach = message.attachments[0]
            if attach and attach.proxy_url:
                send_embed.set_image(url = attach.proxy_url)
        return send_message, send_embed

    async def get_message_stars(self, guild_id, channel_id, message_id, user_id = None):
        """
        Gets the number of stars for a message.
        if user_id is supplied, will return True or False if they have already starred this message
        """
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        message = await channel.fetch_message(message_id)

        star_react = filter(lambda x: x.emoji == STAR, message.reactions)
        if star_react:
            users = await next(star_react).users().flatten()
            if user_id:
                if filter(lambda u: u.id == user_id, users):
                    return len(users), True                    
            return len(users), False
        return None, False
    
    async def update_starboard(self, starboard_channel, message_id):
        """
        Updates an existing starboard post with a new count of stars.
        """
        pass

    async def post_starboard(self, starboard_channel, guild_id, channel_id, message_id):
        """
        Posts a new message on starboard if there are enough stars
        """
        stars, starred_already = await self.get_message_stars(guild_id, channel_id, message_id)
        if stars >= STAR_THRESHOLD or True:
            message, embed = await self.generate_message(guild_id, channel_id, message_id, stars)
            if message and embed:
                await starboard_channel.send(content = message, embed = embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload): # consider doing reaction removed as well?
        """
        Reaction added handler
        """
        # only respond to stars
        if payload.emoji.name != STAR:
            return
        # fetch the starboard channel in this guild, if any
        # if there isn't, then just do nothing
        starboard_channel = self.get_starboard_channel(payload.guild_id)
        if starboard_channel is None:
            return
        
        if payload.channel_id == starboard_channel.id:
            # reaction added to a message in starboard,
            # check that this person hasn't already starred the original message
            # just update the starboard message with a higher number
            await self.update_starboard(starboard_channel, payload.message_id)
        else:
            # reaction added to a message not in starboard
            # check the number of stars on the message
            # TODO: probably need to set up a db to link messages to their posts on the starboard, or just be lazy and use a dict
            # if higher, post to the starboard
            await self.post_starboard(starboard_channel, payload.guild_id, payload.channel_id, payload.message_id)

def setup(bot):
    bot.add_cog(StarboardCog(bot))

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
