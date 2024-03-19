'''
no freakin tutors

anti-spam measures to track down which invite link was used to invite
a given user

then a command to ban users by ID
'''

import discord
from discord.ext import commands
import logging
import json
import configparser
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

invite_filename = "invite_tracking.json"
# hyper-specific for a single guild
target_guild = 297485054836342786

class NoFreakinTutors(commands.Cog):
    """
    Anti-spam stuff.
    """

    def __init__(self, bot):
        self.bot = bot

        if os.path.exists(invite_filename):
            logger.warn("invite tracking json doesn't exist, creating it")
            self.invite_source = {}
        else:
            try:
                with open(invite_filename, 'rt') as f:
                    # dictionary where key is user id, value is invite link, both
                    # are strings
                    self.invite_source = json.loads(f.read())
            except Exception as e:
                logger.warn(f"Failed to open invite tracking json file {e}")

        # dictionary of invite links, key is link, value is the count of used
        # this is fetched on guild available, and checked when new users join
        self.invite_links = {}
    
    def update_tracking_file(self):
        logger.debug("Updating invite tracking json")

        with open(invite_filename, 'wt') as f:
            f.write(json.dumps(self.invite_source))

    @commands.Cog.listener()
    async def on_guild_available(self, guild):
        if guild.id != target_guild:
            return

        invites = await guild.invites()
        logger.info(f"guild currently has {len(invites)} invites")
        for inv in invites:
            invite_id = inv.id
            uses = inv.uses or 0
            owner = inv.inviter.id
            self.invite_links[invite_id] = f"{uses},{owner}"

    # this does not seem to fire ever
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        logger.info("guild invite create")
        if invite.guild is None:
            logger.info("guild is none")
            return
        if invite.guild.id != target_guild:
            logger.info("wrong guild")
            return
        
        invite_id = invite.id
        owner = invite.inviter.id
        logger.info(f"new invite {invite_id} created by user {owner}")
        self.invite_links[invite_id] = f"0,{owner}"

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != target_guild:
            return

        joined_id = member.id

        # actually not sure if this is necessary
        old_invite_states = self.invite_links

        probably_used_invite_id = None

        # fetch new invite state for comparison
        invites = await member.guild.invites()
        for inv in invites:
            invite_id = inv.id
            uses = inv.uses or 0
            owner = inv.inviter.id
            val = f"{uses},{owner}"
            # self.invite_links[invite_id] = f"{uses},{owner}"

            if invite_id in old_invite_states:
                # compare value
                if old_invite_states[invite_id] != val:
                    # val changed
                    probably_used_invite_id = invite_id
                    self.invite_links[invite_id] = val

                    self.invite_source[f"{owner}"] = invite_id
                    self.update_tracking_file()
            else:
                # new invite which did not exist before
                if uses > 0:
                    logger.warn(f"probably joined from a new to me invite {invite_id}")
                    probably_used_invite_id = invite_id

                    self.invite_source[f"{owner}"] = invite_id
                    self.update_tracking_file()

                # this is now known
                self.invite_links[invite_id] = val
        
        logger.info(f"user {joined_id} joined, probably from invite id {probably_used_invite_id}")

# TODO add a ban command for admins
def setup(bot):
    bot.add_cog(NoFreakinTutors(bot))