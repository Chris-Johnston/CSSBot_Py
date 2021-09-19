"""
Starboard

Posts quotes of starred messages to the #starboard channel if it exists.
"""

import discord
from discord.ext import commands
import re
import datetime
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# sqlite
import sqlite3
import configparser

# star emoji used to update the starboard
STAR = u"\u2B50"
# require x or more stars to be posted on the starboard
STAR_THRESHOLD = 3

# does not care about stuff before or after the link
MESSAGE_LINK_REGEX = re.compile(r'.*https:\/\/discordapp.com\/channels\/(\d+)\/(\d+)\/(\d+).*', flags=re.RegexFlag.I)

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
    result = MESSAGE_LINK_REGEX.search(input)
    if result:
        return tuple([int(x) for x in result.groups()])
    return None

def merge_unique(a: list, b: list) -> set:
    """
    merges all of the unique values of each list into a new set

    >>> merge_unique([1, 2, 3], [3, 4, 5])
    {1, 2, 3, 4, 5}

    """
    ret = set()
    a.extend(b)
    for element in a:
        ret.add(element)
    return ret

class StarboardCog(commands.Cog):
    def __init__(self, bot):
        # open the config file in the parent directory
        config = configparser.ConfigParser()
        with open('config.ini') as config_file:
            config.read_file(config_file)

        self.bot = bot

        self.database_path = None

        # if the database is specified
        if config.has_option(section='Configuration',
                             option='starboard_database'):
            path = config.get(section='Configuration',
                              option='starboard_database')

            # open the database
            self.database_path = path
            connection = sqlite3.connect(path, timeout=15)

            # setup the tables of the database
            self._setup_tables(connection)
            connection.close()
        else:
            logger.warn("Starboard database setting missing; starboard will use a transient internal dict instead.")
            self.star_posts = {}

        # No database specified will mean that the database will be None

    def _setup_tables(self, connection):
        """Set up the tables of the database

        :return:"""

        # connection 'cursor'
        c = connection.cursor()

        # Singular message table
        c.execute("""CREATE TABLE IF NOT EXISTS messages
                    (messageId UNSIGNED BIG INT,
                     sentMessageId UNSIGNED BIG INT,
                     channelId UNSIGNED BIG INT)""")

        connection.commit()

    def _get_star_post(self, message_id):
        """Get information of the starred post if it exists.
        :param message_id: the id of the starred message
        :return: either a tuple containing the sent message id, and channel id, or none."""
        if self.database_path is not None:
            database_connection = sqlite3.connect(self.database_path)
            to_query = (message_id,)

            c = database_connection.cursor()

            c.execute("SELECT (sentMessageId, channelId) FROM messages WHERE messageId=?", to_query)
            result = c.fetchone()
            database_connection.close()
            return result
        elif message_id in self.star_posts:
            return self.star_posts[message_id]
        else:
            return None

    def _insert_star_post(self, message_id, sent_message_id, channel_id):
        """Remember starboard information for the future.
        :param message_id: the id of the starred message.
        :param sent_message_id: the id of the message sent to the starboard channel
        :param channel_id: the starboard channel's id
        :return:"""
        to_insert = (sent_message_id, channel_id)

        if self.database_path is not None:
            database_connection = sqlite3.connect(self.database_path)
            c = database_connection.cursor()
            c.execute("""
            INSERT OR REPLACE INTO messages VALUES (?, ?, ?)""",
                      to_insert)
            database_connection.close()
        else:
            self.star_posts[message_id] = to_insert

    def _delete_star_post(self, message_id):
        """Delete the starboard post from memory.
        :param message_id: the id of the starred message."""
        if self.database_path is not None:
            database_connection = sqlite3.connect(self.database_path)
            c = database_connection.cursor()
            c.execute("""
            DELETE FROM messages WHERE message_id = ?""",
                      (message_id,))
            # commit the changes when done
            database_connection.commit()
            database_connection.close()

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

    async def get_starred_users(self, guild_id, channel_id, message_id) -> list:
        """
        Gets the list of all users who starred the given message.
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return []
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return []
        message = await channel.fetch_message(message_id)
        if not message:
            return []
        star_react = filter(lambda x: x.emoji == STAR, message.reactions)
        if star_react:
            # need to instead return the set of all
            users_iter = next(star_react, None)
            if users_iter:
                users = await users_iter.users().flatten()
                return [u.id for u in users]
        return []

    async def get_message_stars(self, guild_id, channel_id, message_id, starboard_channel_id) -> int:
        """
        Gets the number of stars for a message.
        Returns None if there is an error.
        Message id should be for the original post
        """
        original_stars = await self.get_starred_users(guild_id, channel_id, message_id)
        star_post = self._get_star_post(message_id)
        if star_post is not None:
            sent_message_id, _ = star_post
            # need to also get stars from the starboard
            starboard_stars = await self.get_starred_users(guild_id, starboard_channel_id, sent_message_id)
            if starboard_stars:
                # merge the two lists
                return len(merge_unique(original_stars, starboard_stars))
        return len(original_stars)

    async def update_starboard(self, starboard_channel, guild_id, channel_id, message_id):
        """
        Updates an existing starboard post with a new count of stars.
        """
        # get the url of the original message from the starboard post contents
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        if channel_id == starboard_channel.id:
            starboard_message = await starboard_channel.fetch_message(message_id)
            if not starboard_message:
                return # fetched starboard message was null
            # parse the message link
            original_message_values = parse_message_link(starboard_message.content)
            if original_message_values:
                original_guild, original_channel, original_message = original_message_values
            else:
                # no url, so probably not a legit starboard post, skip
                return
        else:
            star_post = self._get_star_post(message_id)
            if star_post is not None:
                starboard_message_id, _ = star_post
                starboard_message = await starboard_channel.fetch_message(starboard_message_id)
                if not starboard_message:
                    return # fetched starboard message null
                original_guild, original_channel, original_message = guild_id, channel_id, message_id
        # sanity check to prevent going across guilds
        assert guild_id == original_guild

        # get the new number of stars
        stars = await self.get_message_stars(guild_id, original_channel, original_message, starboard_channel.id)
        if stars >= STAR_THRESHOLD:
            message, embed = await self.generate_message(guild_id, original_channel, original_message, stars)
            if message and embed:
                # edit existing starboard message
                await starboard_message.edit(content = message, embed = embed)
        else:
            # under threshold, delete and remove from star posts
            await starboard_message.delete()
            self._delete_star_post(original_message)

    async def post_starboard(self, starboard_channel, guild_id, channel_id, message_id):
        """
        Posts a new message on starboard if there are enough stars
        """
        stars = await self.get_message_stars(guild_id, channel_id, message_id, starboard_channel.id)
        if stars >= STAR_THRESHOLD:
            message, embed = await self.generate_message(guild_id, channel_id, message_id, stars)
            if message and embed:
                sent_message = await starboard_channel.send(content = message, embed = embed)
                # register this in the dict of messages to their starboard posts
                self._insert_star_post(message_id, sent_message.id, channel_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Reaction removed handler
        """
        logger.debug("Reaction removed.")
        await self.update_reaction(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload): # consider doing reaction removed as well?
        """
        Reaction added handler
        """
        logger.debug("Reaction added.")
        await self.update_reaction(payload)

    async def update_reaction(self, payload):
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
            await self.update_starboard(starboard_channel, payload.guild_id, payload.channel_id, payload.message_id)
        else:
            # reaction added to a message not in starboard
            # check the number of stars on the message
            star_post = self._get_star_post(payload.message_id)
            if star_post is not None:
                # another reaction was added to the starred message, update the starboard post if the resulting # of stars has changed
                await self.update_starboard(starboard_channel, payload.guild_id, payload.channel_id, payload.message_id)
            else:
                # a message was starred that is not in this dict
                # means that either the bot was restarted, or this message hasn't been posted to the starboard yet
                await self.post_starboard(starboard_channel, payload.guild_id, payload.channel_id, payload.message_id)

def setup(bot):
    bot.add_cog(StarboardCog(bot))

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
