import discord
from discord.ext import commands

# sqlite
import sqlite3
import configparser
import datetime

# stuff that handles user analytics
# no commands are associated with this
class Analytics:
    """Set of handlers that log use analytics.

    """

    def __init__(self, bot):
        # open the config file in the parent directory
        config = configparser.ConfigParser()
        with open('config.ini') as config_file:
            config.read_file(config_file)

        self.bot = bot

        self.database_connection = None

        # if the database is specified
        if config.has_option(section='Configuration',
                             option='analytics_database'):
            path = config.get(section='Configuration',
                              option='analytics_database')
            # open the database
            self.database_connection = sqlite3.connect(path)

            # setup the tables of the database
            self._setup_tables()


        # no database specified will mean that the database
        # will be None

    def _setup_tables(self):
        """Sets up the tables of the database

        :return:
        """
        # connection 'cursor'
        c = self.database_connection.cursor()

        # user message table

        # Discord uses 64-bit unsigned IDs, so represent those
        # as UNSIGNED BIG INTs
        c.execute("""CREATE TABLE IF NOT EXISTS messages
                    (guildId UNSIGNED BIG INT,
                     channelId UNSIGNED BIG INT,
                     authorId UNSIGNED BIG INT,
                     messageId UNSIGNED BIG INT,
                     timestamp DATETIME,
                     contents TEXT)""")

        # member status table

        c.execute("""CREATE TABLE IF NOT EXISTS userStatus
                    (userId UNSIGNED BIG INT,
                    status TEXT,
                    game_name TEXT,
                    timestamp DATETIME)""")

        # reaction table
        c.execute("""CREATE TABLE IF NOT EXISTS reactions
                    (userId UNSIGNED BIG INT,
                    emojiname TEXT,
                    messageId UNSIGNED BIG INT,
                    channelId UNSIGNED BIG INT,
                    action TEXT,
                    timestamp DATETIME)""")
        # emojiname is emoji.name
        # action will be "ADD" for addition
        # and "REMOVE" for removed

        # metadata table
        # saves the user name
        # user nickname
        # guild Id (nicknames are on a server by server basis)
        # https://discordapp.com/developers/docs/resources/user#user-object
        c.execute("""CREATE TABLE IF NOT EXISTS userData
                    (userId UNSIGNED BIG INT,
                    username TEXT,
                    discriminator TEXT,
                    guildId UNSIGNED BIG INT,
                    nickname TEXT,
                    avatar TEXT,
                    bot BOOLEAN DEFAULT 0,
                    joinedAt DATETIME)
                    """)

        # commit changes when done
        self.database_connection.commit()

    def _log_guild_user(self, user):
        """
        Logs the metadata of a guild user into the table
        userData
        :param user:
        :return:
        """
        to_insert = (
            user.id, user.name, user.discriminator, user.guild.id,
            user.nick, user.avatar, user.bot, user.joined_at)

        if self.database_connection is not None:
            c = self.database_connection.cursor()
            c.execute("""
            INSERT INTO userData VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
                      to_insert)

    async def on_ready(self):
        """
        Populates the userData table with information for each user
        :return:
        """
        if self.database_connection is not None:
            # loop through all of the guilds
            for guild in self.bot.guilds:
                # loop through all the users
                for user in guild.members:
                    self._log_guild_user(user)
            # commit the changes when done
            self.database_connection.commit()

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        """
        Inserts an ADD into the table when reactions are added
        :param emoji:
        :param message_id:
        :param channel_id:
        :param user_id:
        :return:
        """
        if self.database_connection is not None:
            to_insert = (user_id, str(emoji.name), message_id, channel_id, "ADD", datetime.datetime.now())

            # insert it
            c = self.database_connection.cursor()
            c.execute("""INSERT INTO reactions VALUES (?, ?, ?, ?, ?, ?)""", to_insert)
            self.database_connection.commit()

    async def on_raw_reaction_remove(self, emoji, message_id, channel_id, user_id):
        """
        Inserts a REMOVE into the table when reactions are removed
        :param emoji:
        :param message_id:
        :param channel_id:
        :param user_id:
        :return:
        """
        if self.database_connection is not None:
            to_insert = (user_id, str(emoji.name), message_id, channel_id, "REMOVE", datetime.datetime.now())

            # insert it
            c = self.database_connection.cursor()
            c.execute("""INSERT INTO reactions VALUES (?, ?, ?, ?, ?, ?)""", to_insert)
            self.database_connection.commit()

    async def on_member_update(self, before, after):
        """Inserts into the user status table when the user status has changed
        :param before: the Member value before the updated their status
        :param after: the value after their status has changed
        :return:
        """

        if self.database_connection is not None:
            to_insert = (after.id, str(after.status), str(after.game or "None"), datetime.datetime.now())

            # log the after status
            c = self.database_connection.cursor()

            c.execute("""INSERT INTO userStatus VALUES (?, ?, ?, ?)""", to_insert)

            self.database_connection.commit()

    async def on_message(self, message):
        """Inserts a new row into the messages table when a message is sent.

        """
        # ensure that this is a guild message
        if self.database_connection is not None and message.guild is not None:
            # build the tuple that represents the data to insert
            # unforunately the library doesn't support inserting a dict

            to_insert = ( message.guild.id, message.id, message.author.id,
                          message.id, message.created_at, message.content)

            # get a connection cursor
            c = self.database_connection.cursor()

            # insert into the table
            # kinda just have to assume that the values are in the same order as
            # they were created in the database
            c.execute("""INSERT INTO messages VALUES (?,?,?,?,?,?)""",
                      to_insert)

            self.database_connection.commit()

def setup(bot):
    bot.add_cog(Analytics(bot))