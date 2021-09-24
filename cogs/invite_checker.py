import discord
from discord.ext import commands
import configparser
import random
import re
import asyncio
import logging
import requests
from typing import List
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

invite_re = re.compile(r"https?:\/\/discord.gg\/([a-zA-Z0-9]+)", re.IGNORECASE)

def get_invites(message: str) -> List[str]:
    """
    >>> get_invites("http://discord.gg/abcabcabc http://discord.gg/123123")
    ['abcabcabc', '123123']
    """
    return invite_re.findall(message)

def is_invite_permanent(invite_code: str):
    url = f'https://discord.com/api/v9/invites/{invite_code}?with_counts=false&with_expiration=true'
    response = requests.get(url)

    # this should? handle expired invites
    if not response.ok():
        return False

    content = response.json()
    return content["expires_at"] is None

class InviteChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        config = configparser.ConfigParser()
        with open("config.ini") as config_file:
            config.read_file(config_file)

        # channels where any discord invites must be permanent links
        self.invite_channels = []
        try:
            if config.has_option(section="Configuration", option="invite_channels"):
                self.invite_channels = config.get(section="Configuration", option="invite_channels")
        except Exception as e:
            logger.warn(f"Failed to init invite channels {e}")

    async def handle_message(self, message):
        if message.channel.id not in self.invite_channels:
            return
        
        invites = get_invites(message.content)
        bad_invites = []
        
        for inv in invites:
            perm = is_invite_permanent(inv)
            if not perm:
                bad_invites.append(inv)
        
        if len(bad_invites) > 0:
            msg = f"Hey {message.author.mention}, the invite(s) {' '.join(bad_invites)} are not permanent. Please provide a permanent link."
            await message.channel.send(msg)

    @commands.Cog.listener()
    async def on_message_edit(self, _, message):
        # don't care about what happens if it isn't in the cache, this is probably good enough
        await self.handle_message(message)

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.handle_message(message)

def setup(bot):
    bot.add_cog(InviteChecker(bot))

if __name__=='__main__':
    import doctest
    doctest.testmod()
