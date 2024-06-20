'''
poke

pretend like it's 2004
'''

import discord
from discord.ext import commands
import logging
import json
import configparser
import os
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from dataclasses import dataclass

@dataclass
class PokeState():
    # one poke state per user
    # key is recipient of the poke
    # value is when they were last poked
    poke_timers: dict

class Poke(commands.Cog):
    """
    Pretend like it's 2004.
    """

    def __init__(self, bot):
        self.bot = bot
        self.poke_state = {}

    @commands.command("poke")
    @commands.cooldown(3, 60, commands.BucketType.user)
    async def poke(self, ctx, user: discord.User):
        """
        Poke.
        """
        src_user_id = ctx.author.id
        dst_user_id = user.id

        # new state in case src user has not done this yet
        src_user_poke_state = PokeState()
        src_user_poke_state.poke_timers = {}

        # check to see if they have done this too recently
        if src_user_id in self.poke_state:
            if dst_user_id in self.poke_state[src_user_id]:
                # going to let cssbot py just restart every day
                # as it currently does, and so this will just reset at 4 am
                # every day
                poke_timestamp = self.poke_state[src_user_id]

                if poke_timestamp > (datetime.datetime.now() - datetime.timedelta(days=1)):
                    # too frequent
                    await ctx.send("You've already done that in the last 24 hours.")

            # src usr has sent at least one poke
            src_user_poke_state = self.poke_state[src_user_id]

        # poke!
        await user.send(f"{ctx.author.display_name} poked you!")
        await ctx.send("👉")

        # this probably has a race condition, I do not care.
        src_user_poke_state.poke_timers[dst_user_id] = datetime.datetime.now()
        self.poke_state[src_user_id] = src_user_poke_state

def setup(bot):
    bot.add_cog(Poke(bot))
