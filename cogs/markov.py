"""
Commands for mocking user's speech using markov chains
"""

import discord
from discord.ext import commands

import sqlite3
import configparser
import datetime
import numpy as np

def normalize_word(word: str) -> str:
    """
    Normalizes a word for use in the marov chain

    >>> normalize_word("Test")
    'test'
    
    >>> normalize_word("What!?!?!")
    'what'

    # does not trim existing whitespace
    >>> normalize_word("(u wot)")
    'u wot'

    """
    word = word.lower()
    # there's probably a much better way to do this
    word = word.replace(',', '')
    word = word.replace('.', '')
    word = word.replace('!', '')
    word = word.replace('?', '')
    word = word.replace("'", '')
    word = word.replace('"', '')
    word = word.replace('~', '')
    word = word.replace('`', '')
    word = word.replace('*', '')
    word = word.replace('_', '')
    word = word.replace('(', '')
    word = word.replace(')', '')
    return word

def make_word_pairs(words: list) -> tuple:
    """
    Makes an association of one word to another
    """
    for x in range(len(words) - 1):
        w1 = normalize_word(words[x])
        w2 = normalize_word(words[x + 1])
        yield (w1, w2)

class Markov:
    """
    Commands for mocking user's messages using Markov chains.
    """

    def __init__(self, bot):
        self.bot = bot

        # get the path to the database
        config = configparser.ConfigParser()
        with open('config.ini') as config_file:
            config.read_file(config_file)

        self.database = None
        self.database_path = None

        if config.has_option(section='Configuration',
                             option='analytics_database'):
            path = config.get(section='Configuration',
                              option='analytics_database')
            # open the database
            self.database_path = path
        else:
            print("database path not provided")

    def get_data(self, guild_id: int, user_id: int = None) -> list:
        """
        Gets a list of all messages, split by whitespace from that user,
        or everyone if user_id is None.
        """
        self.database = sqlite3.connect(self.database_path, timeout=15)
        self.c = self.database.cursor()

        if user_id is not None or user_id != 0:
            self.c.execute("SELECT contents FROM messages WHERE guildId = :guild", {"guild": guild_id})
        else:
            self.c.execute("SELECT contents FROM messages WHERE guildId = :guild AND authorId = :author", {"guild": guild_id, "author": user_id})
        words = []
        rows = self.c.fetchall()
        for r in rows:
            message = r[0]
            # append all words in this message to the list of words
            words.extend(message.split())
        return words

    def predict(self, num_words: int, guild_id: int, user_id: int = None, start_word: str = None) -> str:
        """
        Runs a markov prediction
        """
        # for now, just re-build the markov chain each time that this is run
        # unfortunate, but maybe I could do this nightly. data has to be up to date

        # restrict number of words to 20 if out of bounds
        if num_words < 1 or num_words > 50:
            num_words = 20

        # get all words in this server from this user (or all users)
        words = self.get_data(guild_id, user_id)
        if not words:
            return "No data found!"
        # holds list of associated words with each other
        word_dict = {}
        for word_1, word_2 in make_word_pairs(words):
            if word_1 in word_dict.keys():
                word_dict[word_1].append(word_2)
            else:
                word_dict[word_1] = [word_2]

        first_word = None
        if start_word:
            first_word = normalize_word(start_word)
        else:
            # pick a random starting word
            first_word = normalize_word(np.random.choice(words))

        chain = [first_word]
        try:
            # loop until we got everything
            for x in range(num_words):
                w = word_dict[chain[-1]]
                chain.append(np.random.choice(w))
        except KeyError:
            return "Error, starting word was not in set of existing words."
        result = ' '.join(chain)
        if result:
            return result
        return None

    @commands.command("markov_user")
    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.guild_only()
    async def markov_user(self, ctx, user: discord.User, words: int = 20):
        """
        Replies with a predicted phrase from the specified user.
        """
        await ctx.send(self.predict(words, ctx.guild.id, user.id))

    @commands.command("markov")
    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.guild_only()
    async def markov(self, ctx, words: int = 20):
        """
        Replies with a predicted phrase from all known users.
        """
        await ctx.send(self.predict(words, ctx.guild.id))

    @commands.command("markov_hint_user")
    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.guild_only()
    async def markov_user_hint(self, ctx, user: discord.User, start_word: str, words: int = 20):
        """
        Replies with a predicted phrase from the specified user, starting with a given word.
        """
        await ctx.send(self.predict(words, ctx.guild.id, user.id, start_word))

    @commands.command("markov_hint")
    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.guild_only()
    async def markov_hint(self, ctx, start_word: str, words: int = 20):
        """
        Replies with a predicted phrase starting with a given word.
        """
        await ctx.send(self.predict(words, ctx.guild.id, None, start_word))

def setup(bot):
    bot.add_cog(Markov(bot))

if __name__ == '__main__':
    import doctest
    doctest.testmod()