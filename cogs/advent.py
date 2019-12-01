"""
Advent of Code Leaderboard
"""

import discord
from discord.ext import commands
import requests
import datetime
import configparser

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class AdventUser():
    def __init__(self):
        self.stars = 0
        self.id = None
        self.name = None
        self.local_score = None # leaderboard score
        self.last_star_ts = None # as a datetime
        # could add completion day level

def get_members(advent_json: str) -> list:
    members = []
    for key in advent_json["members"]:
        mem = advent_json["members"][key]
        m = AdventUser()
        m.stars = mem["stars"]
        m.id = mem["id"]
        m.name = mem["name"]
        m.local_score = mem["local_score"]
        if "last_star_ts" in mem:
            ts = int(mem["last_star_ts"])
            if ts == 0:
                m.last_star_ts = None
            else:
                m.last_star_ts = datetime.datetime.utcfromtimestamp(ts) - datetime.timedelta(hours=8)
        else:
            m.last_star_ts = None
        members.append(m)
    return members

class AdventOfCodeCog(commands.Cog):
    """
    Pulls the leaderboard info for the advent of code
    """
    def __init__(self, bot):
        self.bot = bot

        # get the path to the database
        config = configparser.ConfigParser()
        with open('config.ini') as config_file:
            config.read_file(config_file)

        self.leaderboard_id = None
        self.leaderboard_join_code = None
        self.session_cookie = None
        self.last_request_time = None
        self.last_request = None
        self.whitelist_guild = None

        if config.has_option(section='Configuration',
                             option='advent_leaderboard_id'):
            self.leaderboard_id = config.get(section='Configuration',
                              option='advent_leaderboard_id')
        else:
            logger.warning("Advent leaderboard ID is not set, exiting.")
            return
        if config.has_option(section='Configuration',
                             option='advent_join_code'):
            self.leaderboard_join_code = config.get(section='Configuration',
                              option='advent_join_code')
        if config.has_option(section='Configuration',
                             option='advent_cookie'):
            self.session_cookie = config.get(section='Configuration',
                              option='advent_cookie')
        if config.has_option(section='Configuration',
                             option='advent_guild'):
            self.whitelist_guild = config.get(section='Configuration',
                              option='advent_guild')

    def get_request_url(self) -> str:
        return f"https://adventofcode.com/2019/leaderboard/private/view/{self.leaderboard_id}.json"

    def request(self):
        """
        makes the request to the advent of code api
        """
        cookies = {
            "session": self.session_cookie
        }
        url = self.get_request_url()

        r = requests.get(url, cookies=cookies)
        return r.json()

    def cache_request(self):
        if self.last_request_time is None:
            logger.debug("Advent payload timer not set.")
            self.last_request = self.request()
            self.last_request_time = datetime.datetime.now()
        elif self.last_request_time < (datetime.datetime.now() - datetime.timedelta(minutes=15)):
            logger.debug("Advent payload older than 15 minutes.")
            # older than 15 min
            self.last_request = self.request()
            self.last_request_time = datetime.datetime.now()
        else:
            logger.debug("Using cached advent payload.")
        return self.last_request

    def get_emote_for_index(self, index):
        emotes = {
            0: "🥇",
            1: "🥈",
            2: "🥉",
        }
        if index in emotes:
            return emotes[index]
        return " "

    # @commands.command("advent")
    # @commands.cooldown(3, 900, commands.BucketType.user)
    @commands.guild_only()
    @commands.command("advent")
    async def leaderboard(self, ctx):
        if self.leaderboard_id is None:
            logger.warning("Leaderboard ID is not set from config.")
            return
        if ctx.guild is None:
            logger.debug("Guild not in context.")
            return
        guild_id = ctx.guild.id
        if guild_id != int(self.whitelist_guild):
            logger.debug(f"Guild ID ({guild_id}) did not match the whitelist guild ID ({self.whitelist_guild}).")
            return

        advent_json = self.cache_request()
        members = get_members(advent_json)
        members.sort(key=lambda x: x.local_score, reverse=True)

        if members is None or len(members) == 0:
            await ctx.send("Failed to get the list of members.")
            return

        leaderboard_embed = discord.Embed()
        total_stars = 0
        description = ""
        for idx, val in enumerate(members):
            total_stars += val.stars
            if idx < 20:
                date = ""
                if val.last_star_ts is not None:
                    date = val.last_star_ts.strftime("%b %d %-I:%M %p")

                emote = self.get_emote_for_index(idx)
                description += f"{emote} **{val.local_score}** {val.name} **{val.stars}** ⭐ {date}\n"

        description += f"\n**{len(members)}** users with a total of **{total_stars}** ⭐"

        leaderboard_embed.title = f"Advent of Code {advent_json['event']} Leaderboard"
        if self.leaderboard_join_code is not None:
            leaderboard_embed.set_footer(text=f"Join the leaderboard with the code {self.leaderboard_join_code}")
        leaderboard_embed.description = description
        url = f"https://adventofcode.com/{advent_json['event']}/leaderboard/private/view/{self.leaderboard_id}"
        leaderboard_embed.url = url
        leaderboard_embed.color = discord.Color.dark_green()

        await ctx.send(embed=leaderboard_embed)

def setup(bot):
    bot.add_cog(AdventOfCodeCog(bot))